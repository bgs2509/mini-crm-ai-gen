"""
Deal stage manager for handling stage transitions.

This module implements stage transition logic following the Open/Closed Principle,
making it easy to add new stages without modifying existing code.
"""
from typing import Dict, List, Optional, Tuple

from app.models.deal import DealStage
from app.models.organization_member import MemberRole


class StageTransitionRule:
    """
    Represents a rule for stage transitions.

    Encapsulates the logic for determining if a stage transition is valid.
    """

    def __init__(
        self,
        from_stage: DealStage,
        to_stage: DealStage,
        is_backward: bool = False,
        requires_role: Optional[MemberRole] = None
    ):
        """
        Initialize stage transition rule.

        Args:
            from_stage: Starting stage
            to_stage: Target stage
            is_backward: Whether this is a backward transition
            requires_role: Minimum role required (if any)
        """
        self.from_stage = from_stage
        self.to_stage = to_stage
        self.is_backward = is_backward
        self.requires_role = requires_role


class DealStageManager:
    """
    Manager for deal stage transitions.

    Implements stage transition logic following the Open/Closed Principle.
    New stages can be added by extending the configuration without
    modifying existing code.
    """

    def __init__(self):
        """Initialize deal stage manager with stage order and transitions."""
        # Define stage order (lower number = earlier stage)
        self._stage_order: Dict[DealStage, int] = {
            DealStage.QUALIFICATION: 1,
            DealStage.PROPOSAL: 2,
            DealStage.NEGOTIATION: 3,
            DealStage.CLOSED: 4
        }

        # Define allowed forward transitions
        self._forward_transitions: Dict[DealStage, List[DealStage]] = {
            DealStage.QUALIFICATION: [DealStage.PROPOSAL, DealStage.NEGOTIATION, DealStage.CLOSED],
            DealStage.PROPOSAL: [DealStage.NEGOTIATION, DealStage.CLOSED],
            DealStage.NEGOTIATION: [DealStage.CLOSED],
            DealStage.CLOSED: []  # Terminal stage
        }

    def get_stage_order(self, stage: DealStage) -> int:
        """
        Get the order number for a stage.

        Args:
            stage: Deal stage

        Returns:
            Order number (lower = earlier)
        """
        return self._stage_order.get(stage, 0)

    def is_backward_transition(self, from_stage: DealStage, to_stage: DealStage) -> bool:
        """
        Check if transition is backward (moving to earlier stage).

        Args:
            from_stage: Current stage
            to_stage: Target stage

        Returns:
            True if moving backward
        """
        return self.get_stage_order(to_stage) < self.get_stage_order(from_stage)

    def is_forward_transition(self, from_stage: DealStage, to_stage: DealStage) -> bool:
        """
        Check if transition is forward (moving to later stage).

        Args:
            from_stage: Current stage
            to_stage: Target stage

        Returns:
            True if moving forward
        """
        return self.get_stage_order(to_stage) > self.get_stage_order(from_stage)

    def is_valid_transition(self, from_stage: DealStage, to_stage: DealStage) -> bool:
        """
        Check if transition between stages is valid (ignoring role permissions).

        Args:
            from_stage: Current stage
            to_stage: Target stage

        Returns:
            True if transition is allowed
        """
        # Same stage is always valid
        if from_stage == to_stage:
            return True

        # Check if target stage is in allowed transitions
        allowed_stages = self._forward_transitions.get(from_stage, [])
        if to_stage in allowed_stages:
            return True

        # Backward transitions are valid but may require special permissions
        if self.is_backward_transition(from_stage, to_stage):
            # Check if we can go back (all stages except CLOSED can go back)
            return from_stage != DealStage.CLOSED

        return False

    def can_transition(
        self,
        from_stage: DealStage,
        to_stage: DealStage,
        user_role: MemberRole
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user can perform stage transition.

        Args:
            from_stage: Current stage
            to_stage: Target stage
            user_role: User's role

        Returns:
            Tuple of (can_transition, error_message)
        """
        # Check if same stage
        if from_stage == to_stage:
            return True, None

        # Check if transition is valid
        if not self.is_valid_transition(from_stage, to_stage):
            return False, f"Invalid stage transition from {from_stage.value} to {to_stage.value}"

        # Check if backward transition requires special permissions
        if self.is_backward_transition(from_stage, to_stage):
            if user_role not in (MemberRole.ADMIN, MemberRole.OWNER):
                return False, "Only admins and owners can move deal stage backward"

        return True, None

    def get_next_stages(self, current_stage: DealStage) -> List[DealStage]:
        """
        Get list of possible next stages from current stage.

        Args:
            current_stage: Current deal stage

        Returns:
            List of possible next stages
        """
        return self._forward_transitions.get(current_stage, [])

    def get_all_stages_in_order(self) -> List[DealStage]:
        """
        Get all stages in order.

        Returns:
            List of stages sorted by order
        """
        return sorted(self._stage_order.keys(), key=lambda s: self._stage_order[s])

    def is_terminal_stage(self, stage: DealStage) -> bool:
        """
        Check if stage is terminal (no forward transitions).

        Args:
            stage: Deal stage

        Returns:
            True if terminal stage
        """
        return len(self._forward_transitions.get(stage, [])) == 0


# Global instance
deal_stage_manager = DealStageManager()
