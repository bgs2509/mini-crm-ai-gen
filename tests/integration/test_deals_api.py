"""
Integration tests for deals API endpoints.
"""
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.deal import Deal, DealStatus, DealStage


class TestListDealsEndpoint:
    """Test listing deals endpoint."""

    @pytest.mark.asyncio
    async def test_list_deals_empty(self, client: AsyncClient, auth_headers):
        """Test listing deals when none exist."""
        response = await client.get("/api/v1/deals", headers=auth_headers)

        assert response.status_code == 200
        result = response.json()

        assert "items" in result
        assert len(result["items"]) == 0
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_list_deals_with_data(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_organization,
        test_user
    ):
        """Test listing deals with existing data."""
        # Create test contact
        contact = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="Test Contact",
            email="contact@example.com"
        )
        db_session.add(contact)
        await db_session.commit()

        # Create test deals
        deal1 = Deal(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            contact_id=contact.id,
            title="Deal 1",
            amount=Decimal("1000.00"),
            currency="USD"
        )
        deal2 = Deal(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            contact_id=contact.id,
            title="Deal 2",
            amount=Decimal("2000.00"),
            currency="USD"
        )

        db_session.add(deal1)
        db_session.add(deal2)
        await db_session.commit()

        response = await client.get("/api/v1/deals", headers=auth_headers)

        assert response.status_code == 200
        result = response.json()

        assert len(result["items"]) == 2
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_list_deals_filter_by_status(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_organization,
        test_user
    ):
        """Test filtering deals by status."""
        # Create test contact
        contact = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="Test Contact",
            email="contact@example.com"
        )
        db_session.add(contact)
        await db_session.commit()

        # Create deals with different statuses
        deal1 = Deal(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            contact_id=contact.id,
            title="New Deal",
            amount=Decimal("1000.00"),
            currency="USD",
            status=DealStatus.NEW
        )
        deal2 = Deal(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            contact_id=contact.id,
            title="Won Deal",
            amount=Decimal("2000.00"),
            currency="USD",
            status=DealStatus.WON
        )

        db_session.add(deal1)
        db_session.add(deal2)
        await db_session.commit()

        response = await client.get(
            "/api/v1/deals?status=won",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        assert len(result["items"]) == 1
        assert result["items"][0]["status"] == "won"

    @pytest.mark.asyncio
    async def test_list_deals_filter_by_stage(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_organization,
        test_user
    ):
        """Test filtering deals by stage."""
        # Create test contact
        contact = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="Test Contact",
            email="contact@example.com"
        )
        db_session.add(contact)
        await db_session.commit()

        # Create deals with different stages
        deal1 = Deal(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            contact_id=contact.id,
            title="Qualification Deal",
            amount=Decimal("1000.00"),
            currency="USD",
            stage=DealStage.QUALIFICATION
        )
        deal2 = Deal(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            contact_id=contact.id,
            title="Negotiation Deal",
            amount=Decimal("2000.00"),
            currency="USD",
            stage=DealStage.NEGOTIATION
        )

        db_session.add(deal1)
        db_session.add(deal2)
        await db_session.commit()

        response = await client.get(
            "/api/v1/deals?stage=negotiation",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        assert len(result["items"]) == 1
        assert result["items"][0]["stage"] == "negotiation"


class TestCreateDealEndpoint:
    """Test creating deal endpoint."""

    @pytest.mark.asyncio
    async def test_create_deal_success(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_organization,
        test_user
    ):
        """Test successful deal creation."""
        # Create test contact
        contact = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="Test Contact",
            email="contact@example.com"
        )
        db_session.add(contact)
        await db_session.commit()

        data = {
            "contact_id": str(contact.id),
            "title": "New Deal",
            "amount": 5000.00,
            "currency": "USD"
        }

        response = await client.post("/api/v1/deals", headers=auth_headers, json=data)

        assert response.status_code == 201
        result = response.json()

        assert result["title"] == data["title"]
        assert float(result["amount"]) == data["amount"]
        assert result["currency"] == data["currency"]
        assert result["status"] == "new"
        assert result["stage"] == "qualification"

    @pytest.mark.asyncio
    async def test_create_deal_minimal_data(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_organization,
        test_user
    ):
        """Test creating deal with minimal required data."""
        # Create test contact
        contact = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="Test Contact",
            email="contact@example.com"
        )
        db_session.add(contact)
        await db_session.commit()

        data = {
            "contact_id": str(contact.id),
            "title": "Minimal Deal",
            "amount": 1000.00
        }

        response = await client.post("/api/v1/deals", headers=auth_headers, json=data)

        assert response.status_code == 201
        result = response.json()

        assert result["title"] == data["title"]
        # Should use organization default currency
        assert result["currency"] == "USD"

    @pytest.mark.asyncio
    async def test_create_deal_invalid_contact(self, client: AsyncClient, auth_headers):
        """Test creating deal with invalid contact ID."""
        data = {
            "contact_id": str(uuid4()),
            "title": "Invalid Contact Deal",
            "amount": 1000.00
        }

        response = await client.post("/api/v1/deals", headers=auth_headers, json=data)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_deal_negative_amount(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_organization,
        test_user
    ):
        """Test creating deal with negative amount fails."""
        # Create test contact
        contact = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="Test Contact",
            email="contact@example.com"
        )
        db_session.add(contact)
        await db_session.commit()

        data = {
            "contact_id": str(contact.id),
            "title": "Negative Deal",
            "amount": -1000.00
        }

        response = await client.post("/api/v1/deals", headers=auth_headers, json=data)

        assert response.status_code == 422


class TestGetDealEndpoint:
    """Test getting single deal endpoint."""

    @pytest.mark.asyncio
    async def test_get_deal_success(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_organization,
        test_user
    ):
        """Test getting deal by ID."""
        # Create test contact
        contact = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="Test Contact",
            email="contact@example.com"
        )
        db_session.add(contact)
        await db_session.commit()

        # Create test deal
        deal = Deal(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            contact_id=contact.id,
            title="Test Deal",
            amount=Decimal("5000.00"),
            currency="USD"
        )
        db_session.add(deal)
        await db_session.commit()

        response = await client.get(f"/api/v1/deals/{deal.id}", headers=auth_headers)

        assert response.status_code == 200
        result = response.json()

        assert result["id"] == str(deal.id)
        assert result["title"] == deal.title
        assert float(result["amount"]) == float(deal.amount)

    @pytest.mark.asyncio
    async def test_get_deal_not_found(self, client: AsyncClient, auth_headers):
        """Test getting nonexistent deal."""
        fake_id = uuid4()

        response = await client.get(f"/api/v1/deals/{fake_id}", headers=auth_headers)

        assert response.status_code == 404


class TestUpdateDealEndpoint:
    """Test updating deal endpoint."""

    @pytest.mark.asyncio
    async def test_update_deal_success(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_organization,
        test_user
    ):
        """Test successful deal update."""
        # Create test contact
        contact = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="Test Contact",
            email="contact@example.com"
        )
        db_session.add(contact)
        await db_session.commit()

        # Create test deal
        deal = Deal(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            contact_id=contact.id,
            title="Original Title",
            amount=Decimal("1000.00"),
            currency="USD"
        )
        db_session.add(deal)
        await db_session.commit()

        # Update deal
        update_data = {
            "title": "Updated Title",
            "amount": 2000.00
        }

        response = await client.patch(
            f"/api/v1/deals/{deal.id}",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        result = response.json()

        assert result["title"] == update_data["title"]
        assert float(result["amount"]) == update_data["amount"]

    @pytest.mark.asyncio
    async def test_update_deal_status(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_organization,
        test_user
    ):
        """Test updating deal status."""
        # Create test contact
        contact = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="Test Contact",
            email="contact@example.com"
        )
        db_session.add(contact)
        await db_session.commit()

        # Create test deal
        deal = Deal(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            contact_id=contact.id,
            title="Test Deal",
            amount=Decimal("1000.00"),
            currency="USD",
            status=DealStatus.NEW
        )
        db_session.add(deal)
        await db_session.commit()

        # Update status
        update_data = {
            "status": "in_progress"
        }

        response = await client.patch(
            f"/api/v1/deals/{deal.id}",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        result = response.json()

        assert result["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_update_deal_stage(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_organization,
        test_user
    ):
        """Test updating deal stage."""
        # Create test contact
        contact = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="Test Contact",
            email="contact@example.com"
        )
        db_session.add(contact)
        await db_session.commit()

        # Create test deal
        deal = Deal(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            contact_id=contact.id,
            title="Test Deal",
            amount=Decimal("1000.00"),
            currency="USD",
            stage=DealStage.QUALIFICATION
        )
        db_session.add(deal)
        await db_session.commit()

        # Update stage
        update_data = {
            "stage": "proposal"
        }

        response = await client.patch(
            f"/api/v1/deals/{deal.id}",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        result = response.json()

        assert result["stage"] == "proposal"


class TestDeleteDealEndpoint:
    """Test deleting deal endpoint."""

    @pytest.mark.asyncio
    async def test_delete_deal_success(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_organization,
        test_user
    ):
        """Test successful deal deletion."""
        # Create test contact
        contact = Contact(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            name="Test Contact",
            email="contact@example.com"
        )
        db_session.add(contact)
        await db_session.commit()

        # Create test deal
        deal = Deal(
            id=uuid4(),
            organization_id=test_organization.id,
            owner_id=test_user.id,
            contact_id=contact.id,
            title="To Delete",
            amount=Decimal("1000.00"),
            currency="USD"
        )
        db_session.add(deal)
        await db_session.commit()

        response = await client.delete(f"/api/v1/deals/{deal.id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(f"/api/v1/deals/{deal.id}", headers=auth_headers)
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_deal_not_found(self, client: AsyncClient, auth_headers):
        """Test deleting nonexistent deal."""
        fake_id = uuid4()

        response = await client.delete(f"/api/v1/deals/{fake_id}", headers=auth_headers)

        assert response.status_code == 404
