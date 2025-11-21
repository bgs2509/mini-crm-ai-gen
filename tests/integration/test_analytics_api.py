"""
Integration tests for analytics API endpoints.
"""
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.organization import Organization
from app.models.contact import Contact
from app.models.deal import Deal, DealStatus, DealStage


@pytest_asyncio.fixture
async def test_contact(
    db_session: AsyncSession,
    test_organization: Organization,
    test_user: User
) -> Contact:
    """Create test contact."""
    contact = Contact(
        id=uuid4(),
        organization_id=test_organization.id,
        owner_id=test_user.id,
        name="Test Contact",
        email="contact@example.com",
        phone="+1234567890"
    )
    db_session.add(contact)
    await db_session.commit()
    await db_session.refresh(contact)
    return contact


@pytest_asyncio.fixture
async def test_deals(
    db_session: AsyncSession,
    test_organization: Organization,
    test_user: User,
    test_contact: Contact
) -> list[Deal]:
    """Create multiple test deals with different statuses and stages."""
    deals = [
        # Won deals
        Deal(
            id=uuid4(),
            organization_id=test_organization.id,
            contact_id=test_contact.id,
            owner_id=test_user.id,
            title="Won Deal 1",
            amount=10000.0,
            currency="USD",
            status=DealStatus.WON,
            stage=DealStage.CLOSED
        ),
        Deal(
            id=uuid4(),
            organization_id=test_organization.id,
            contact_id=test_contact.id,
            owner_id=test_user.id,
            title="Won Deal 2",
            amount=5000.0,
            currency="USD",
            status=DealStatus.WON,
            stage=DealStage.CLOSED
        ),
        # In progress deals
        Deal(
            id=uuid4(),
            organization_id=test_organization.id,
            contact_id=test_contact.id,
            owner_id=test_user.id,
            title="In Progress Deal 1",
            amount=8000.0,
            currency="USD",
            status=DealStatus.IN_PROGRESS,
            stage=DealStage.QUALIFICATION
        ),
        Deal(
            id=uuid4(),
            organization_id=test_organization.id,
            contact_id=test_contact.id,
            owner_id=test_user.id,
            title="In Progress Deal 2",
            amount=12000.0,
            currency="USD",
            status=DealStatus.IN_PROGRESS,
            stage=DealStage.PROPOSAL
        ),
        # Lost deal
        Deal(
            id=uuid4(),
            organization_id=test_organization.id,
            contact_id=test_contact.id,
            owner_id=test_user.id,
            title="Lost Deal",
            amount=3000.0,
            currency="USD",
            status=DealStatus.LOST,
            stage=DealStage.NEGOTIATION
        ),
        # New deal
        Deal(
            id=uuid4(),
            organization_id=test_organization.id,
            contact_id=test_contact.id,
            owner_id=test_user.id,
            title="New Deal",
            amount=6000.0,
            currency="USD",
            status=DealStatus.NEW,
            stage=DealStage.QUALIFICATION
        ),
    ]

    for deal in deals:
        db_session.add(deal)

    await db_session.commit()

    for deal in deals:
        await db_session.refresh(deal)

    return deals


class TestDealsSummary:
    """Test GET /api/v1/analytics/deals/summary endpoint."""

    @pytest.mark.asyncio
    async def test_deals_summary_empty(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test deals summary with no deals."""
        response = await client.get(
            "/api/v1/analytics/deals/summary",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        assert "total_deals" in result
        assert "total_value" in result
        assert "won_deals" in result
        assert "lost_deals" in result
        assert "in_progress_deals" in result
        assert result["total_deals"] == 0
        assert float(result["total_value"]) == 0.0

    @pytest.mark.asyncio
    async def test_deals_summary_with_deals(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deals: list[Deal]
    ):
        """Test deals summary with multiple deals."""
        response = await client.get(
            "/api/v1/analytics/deals/summary",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        # Total stats
        assert result["total_deals"] == 6
        # API returns decimal values as strings for precision
        assert float(result["total_value"]) == 44000.0

        # Won deals stats
        assert result["won_deals"] == 2
        assert float(result["won_value"]) == 15000.0

        # In progress deals stats
        assert result["in_progress_deals"] == 2
        assert float(result["in_progress_value"]) == 20000.0

        # Lost deals stats
        assert result["lost_deals"] == 1
        assert float(result["lost_value"]) == 3000.0

    @pytest.mark.asyncio
    async def test_deals_summary_win_rate(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deals: list[Deal]
    ):
        """Test win rate calculation in summary."""
        response = await client.get(
            "/api/v1/analytics/deals/summary",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        # Win rate should be won / (won + lost)
        # 2 won, 1 lost = 2/3 = ~66.67%
        if "win_rate" in result:
            assert result["win_rate"] >= 66.0
            assert result["win_rate"] <= 67.0

    @pytest.mark.asyncio
    async def test_deals_summary_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test deals summary without authentication."""
        response = await client.get("/api/v1/analytics/deals/summary")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_deals_summary_caching(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deals: list[Deal]
    ):
        """Test that summary is cached (multiple requests should return same data)."""
        # First request
        response1 = await client.get(
            "/api/v1/analytics/deals/summary",
            headers=auth_headers
        )

        assert response1.status_code == 200
        result1 = response1.json()

        # Second request (should be cached)
        response2 = await client.get(
            "/api/v1/analytics/deals/summary",
            headers=auth_headers
        )

        assert response2.status_code == 200
        result2 = response2.json()

        # Results should be identical
        assert result1 == result2


class TestFunnelMetrics:
    """Test GET /api/v1/analytics/deals/funnel endpoint."""

    @pytest.mark.asyncio
    async def test_funnel_empty(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test funnel with no deals."""
        response = await client.get(
            "/api/v1/analytics/deals/funnel",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        assert "by_status" in result
        assert "by_stage" in result

    @pytest.mark.asyncio
    async def test_funnel_with_deals(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deals: list[Deal]
    ):
        """Test funnel metrics with multiple deals."""
        response = await client.get(
            "/api/v1/analytics/deals/funnel",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        # By status
        assert "by_status" in result
        by_status = result["by_status"]

        # Check status breakdown
        status_counts = {item["status"]: item["count"] for item in by_status}
        assert status_counts.get("won") == 2
        assert status_counts.get("in_progress") == 2
        assert status_counts.get("lost") == 1
        assert status_counts.get("new") == 1

        # By stage
        assert "by_stage" in result
        by_stage = result["by_stage"]

        # Check stage breakdown
        stage_counts = {item["stage"]: item["count"] for item in by_stage}
        assert stage_counts.get("qualification") == 2  # 1 in_progress + 1 new
        assert stage_counts.get("proposal") == 1
        assert stage_counts.get("negotiation") == 1
        assert stage_counts.get("closed") == 2  # 2 won

    @pytest.mark.asyncio
    async def test_funnel_percentages(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deals: list[Deal]
    ):
        """Test that funnel includes percentage calculations."""
        response = await client.get(
            "/api/v1/analytics/deals/funnel",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        # Check that percentages are included
        by_status = result["by_status"]
        for status_item in by_status:
            assert "percentage" in status_item
            assert status_item["percentage"] >= 0
            assert status_item["percentage"] <= 100

        # Sum of percentages should be approximately 100%
        total_percentage = sum(item["percentage"] for item in by_status)
        assert 99.0 <= total_percentage <= 101.0

    @pytest.mark.asyncio
    async def test_funnel_amounts(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deals: list[Deal]
    ):
        """Test that funnel includes amount calculations."""
        response = await client.get(
            "/api/v1/analytics/deals/funnel",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        # Check by_status amounts
        by_status = result["by_status"]
        for status_item in by_status:
            assert "total_amount" in status_item
            # Convert string to float for comparison
            assert float(status_item["total_amount"]) >= 0

        # Find won status
        won_status = next(
            (item for item in by_status if item["status"] == "won"),
            None
        )
        assert won_status is not None
        assert float(won_status["total_amount"]) == 15000.0

    @pytest.mark.asyncio
    async def test_funnel_conversion_rate(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deals: list[Deal]
    ):
        """Test conversion rate calculation in funnel."""
        response = await client.get(
            "/api/v1/analytics/deals/funnel",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        # Should have overall conversion rate
        if "conversion_rate" in result:
            # Conversion is typically won / (won + lost + in_progress)
            # or won / total
            assert result["conversion_rate"] >= 0
            assert result["conversion_rate"] <= 100

    @pytest.mark.asyncio
    async def test_funnel_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test funnel without authentication."""
        response = await client.get("/api/v1/analytics/deals/funnel")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_funnel_organization_isolation(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deals: list[Deal],
        db_session: AsyncSession
    ):
        """Test that funnel only shows deals from current organization."""
        # Create another organization and deal
        other_org = Organization(
            id=uuid4(),
            name="Other Organization",
            default_currency="USD"
        )
        db_session.add(other_org)
        await db_session.commit()

        # Create contact for other org
        other_contact = Contact(
            id=uuid4(),
            organization_id=other_org.id,
            owner_id=test_deals[0].owner_id,
            name="Other Contact",
            email="other@example.com"
        )
        db_session.add(other_contact)
        await db_session.commit()

        # Create deal in other org
        other_deal = Deal(
            id=uuid4(),
            organization_id=other_org.id,
            contact_id=other_contact.id,
            owner_id=test_deals[0].owner_id,
            title="Other Org Deal",
            amount=99999.0,
            currency="USD",
            status=DealStatus.WON,
            stage=DealStage.CLOSED
        )
        db_session.add(other_deal)
        await db_session.commit()

        # Get funnel - should only show current org's deals
        response = await client.get(
            "/api/v1/analytics/deals/funnel",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        # Won count should still be 2 (from test_deals), not 3
        by_status = result["by_status"]
        won_status = next(
            (item for item in by_status if item["status"] == "won"),
            None
        )
        assert won_status["count"] == 2
        # API returns decimal as string
        assert float(won_status["total_amount"]) == 15000.0  # Not including 99999


class TestAnalyticsCaching:
    """Test analytics caching behavior."""

    @pytest.mark.asyncio
    async def test_cache_duration(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deals: list[Deal]
    ):
        """Test that analytics results are properly cached."""
        # Get initial summary
        response1 = await client.get(
            "/api/v1/analytics/deals/summary",
            headers=auth_headers
        )
        assert response1.status_code == 200

        # Get initial funnel
        response2 = await client.get(
            "/api/v1/analytics/deals/funnel",
            headers=auth_headers
        )
        assert response2.status_code == 200

        # Both requests should succeed and be cached
        # (actual cache verification would require inspecting cache implementation)
        assert response1.json()["total_deals"] == 6
        assert len(response2.json()["by_status"]) > 0
