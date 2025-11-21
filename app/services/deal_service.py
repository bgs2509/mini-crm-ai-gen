"""
Deal service for deal management and business logic.
"""
from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError, BusinessLogicError, NotFoundError
from app.core.config import settings
from app.repositories.deal_repository import DealRepository
from app.repositories.contact_repository import ContactRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.protocols import (
    IDealRepository,
    IContactRepository,
    IOrganizationRepository,
    IActivityRepository
)
from app.models.deal import Deal, DealStatus, DealStage
from app.models.activity import ActivityType
from app.models.organization_member import MemberRole
from app.services.deal_stage_manager import deal_stage_manager
from app.core.permissions.resource_permissions import ResourcePermissionChecker


class DealService:
    """Service for deal operations with dependency inversion."""

    def __init__(
        self,
        db: AsyncSession,
        deal_repo: Optional[IDealRepository] = None,
        contact_repo: Optional[IContactRepository] = None,
        org_repo: Optional[IOrganizationRepository] = None,
        activity_repo: Optional[IActivityRepository] = None
    ):
        """
        Initialize deal service.

        Args:
            db: Database session
            deal_repo: Deal repository (uses default if None)
            contact_repo: Contact repository (uses default if None)
            org_repo: Organization repository (uses default if None)
            activity_repo: Activity repository (uses default if None)
        """
        self.db = db
        self.deal_repo = deal_repo or DealRepository(db)
        self.contact_repo = contact_repo or ContactRepository(db)
        self.org_repo = org_repo or OrganizationRepository(db)
        self.activity_repo = activity_repo or ActivityRepository(db)
        self.permission_checker = ResourcePermissionChecker()

    async def create_deal(
        self,
        organization_id: UUID,
        contact_id: UUID,
        owner_id: UUID,
        title: str,
        amount: Decimal,
        currency: Optional[str] = None
    ) -> Deal:
        """
        Create new deal.

        Args:
            organization_id: Organization UUID
            contact_id: Contact UUID
            owner_id: Owner user UUID
            title: Deal title
            amount: Deal amount
            currency: Currency code (uses org default or app default if None)

        Returns:
            Created deal

        Raises:
            NotFoundError: If contact not found
            ValidationError: If contact belongs to different organization
        """
        # Verify contact exists and belongs to organization
        contact = await self.contact_repo.get_by_id(contact_id)
        if not contact:
            raise NotFoundError("Contact", contact_id)

        if contact.organization_id != organization_id:
            raise ValidationError(
                "Contact does not belong to this organization",
                field="contact_id"
            )

        # Determine currency
        if not currency:
            # Get organization default currency
            org = await self.org_repo.get_by_id(organization_id)
            if org and org.default_currency:
                currency = org.default_currency
            else:
                currency = settings.default_currency

        # Validate currency
        if currency.upper() not in settings.supported_currencies:
            raise ValidationError(
                f"Currency '{currency}' is not supported",
                field="currency"
            )

        # Create deal
        deal = await self.deal_repo.create(
            organization_id=organization_id,
            contact_id=contact_id,
            owner_id=owner_id,
            title=title,
            amount=amount,
            currency=currency.upper(),
            status=DealStatus.NEW,
            stage=DealStage.QUALIFICATION
        )

        # Create system activity
        await self.activity_repo.create_activity(
            deal_id=deal.id,
            activity_type=ActivityType.SYSTEM,
            payload={
                'message': 'Deal created',
                'amount': str(amount),
                'currency': currency.upper()
            }
        )

        await self.db.commit()
        return deal

    async def update_deal_status(
        self,
        deal_id: UUID,
        new_status: DealStatus,
        user_id: UUID,
        user_role: MemberRole
    ) -> Deal:
        """
        Update deal status with validation.

        Args:
            deal_id: Deal UUID
            new_status: New status
            user_id: User making the change
            user_role: User's role

        Returns:
            Updated deal

        Raises:
            BusinessLogicError: If status transition is invalid
        """
        deal = await self.deal_repo.get_by_id_or_404(deal_id)
        old_status = deal.status

        # Check ownership permission using new permission checker
        self.permission_checker.check_resource_ownership(
            user_id,
            deal.owner_id,
            user_role,
            "Deal",
            str(deal_id)
        )

        # Validate status transition
        if old_status == new_status:
            return deal

        # Can't change from terminal status
        if old_status.is_terminal:
            raise BusinessLogicError(
                f"Cannot change status from terminal state '{old_status.value}'"
            )

        # Can't mark as won with zero or negative amount
        if new_status == DealStatus.WON and deal.amount <= 0:
            raise BusinessLogicError(
                f"Cannot mark deal as won with amount {deal.amount}. Amount must be greater than 0."
            )

        # Auto-set stage to closed when won/lost
        updates: Dict[str, Any] = {'status': new_status}
        if new_status.is_terminal:
            updates['stage'] = DealStage.CLOSED

        # Update deal
        deal = await self.deal_repo.update(deal_id, **updates)

        # Log activity
        await self.activity_repo.create_activity(
            deal_id=deal_id,
            activity_type=ActivityType.STATUS_CHANGED,
            payload={
                'old_status': old_status.value,
                'new_status': new_status.value
            },
            author_id=user_id
        )

        await self.db.commit()
        return deal

    async def update_deal_stage(
        self,
        deal_id: UUID,
        new_stage: DealStage,
        user_id: UUID,
        user_role: MemberRole
    ) -> Deal:
        """
        Update deal stage with role validation using DealStageManager.

        Args:
            deal_id: Deal UUID
            new_stage: New stage
            user_id: User making the change
            user_role: User's role

        Returns:
            Updated deal

        Raises:
            BusinessLogicError: If stage change is not allowed
        """
        deal = await self.deal_repo.get_by_id_or_404(deal_id)
        old_stage = deal.stage

        # Check ownership permission using new permission checker
        self.permission_checker.check_resource_ownership(
            user_id,
            deal.owner_id,
            user_role,
            "Deal",
            str(deal_id)
        )

        if old_stage == new_stage:
            return deal

        # Use DealStageManager to validate transition
        can_transition, error_message = deal_stage_manager.can_transition(
            from_stage=old_stage,
            to_stage=new_stage,
            user_role=user_role
        )

        if not can_transition:
            raise BusinessLogicError(error_message or "Stage transition not allowed")

        # Update deal
        deal = await self.deal_repo.update(deal_id, stage=new_stage)

        # Log activity
        await self.activity_repo.create_activity(
            deal_id=deal_id,
            activity_type=ActivityType.STAGE_CHANGED,
            payload={
                'old_stage': old_stage.value,
                'new_stage': new_stage.value
            },
            author_id=user_id
        )

        await self.db.commit()
        return deal

    async def delete_deal(self, deal_id: UUID) -> bool:
        """
        Delete deal and all related data.

        Args:
            deal_id: Deal UUID

        Returns:
            True if deleted
        """
        result = await self.deal_repo.delete(deal_id)
        await self.db.commit()
        return result
