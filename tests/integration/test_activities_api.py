"""
Integration tests for activity/timeline API endpoints.
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
async def test_deal(
    db_session: AsyncSession,
    test_organization: Organization,
    test_user: User,
    test_contact: Contact
) -> Deal:
    """Create test deal."""
    deal = Deal(
        id=uuid4(),
        organization_id=test_organization.id,
        contact_id=test_contact.id,
        owner_id=test_user.id,
        title="Test Deal",
        amount=5000.0,
        currency="USD",
        status=DealStatus.IN_PROGRESS,
        stage=DealStage.QUALIFICATION
    )
    db_session.add(deal)
    await db_session.commit()
    await db_session.refresh(deal)
    return deal


class TestGetDealTimeline:
    """Test GET /api/v1/deals/{deal_id}/activities endpoint."""

    @pytest.mark.asyncio
    async def test_get_timeline_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deal: Deal
    ):
        """Test getting empty timeline."""
        response = await client.get(
            f"/api/v1/deals/{test_deal.id}/activities",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        assert "items" in result
        assert "total" in result
        assert result["items"] == []
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_get_timeline_with_activities(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deal: Deal
    ):
        """Test getting timeline with activities."""
        # Add 3 comments
        for i in range(3):
            await client.post(
                f"/api/v1/deals/{test_deal.id}/activities",
                headers=auth_headers,
                json={"text": f"Comment {i+1}"}
            )

        response = await client.get(
            f"/api/v1/deals/{test_deal.id}/activities",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        assert len(result["items"]) == 3
        assert result["total"] == 3

    @pytest.mark.asyncio
    async def test_get_timeline_with_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deal: Deal
    ):
        """Test timeline pagination."""
        # Add 5 comments
        for i in range(5):
            await client.post(
                f"/api/v1/deals/{test_deal.id}/activities",
                headers=auth_headers,
                json={"text": f"Comment {i+1}"}
            )

        # Get first page (2 items)
        response = await client.get(
            f"/api/v1/deals/{test_deal.id}/activities?skip=0&limit=2",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        assert len(result["items"]) == 2
        assert result["total"] == 5
        assert result["skip"] == 0
        assert result["limit"] == 2
        assert result["has_more"] is True

        # Get second page
        response = await client.get(
            f"/api/v1/deals/{test_deal.id}/activities?skip=2&limit=2",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        assert len(result["items"]) == 2
        assert result["total"] == 5
        assert result["skip"] == 2
        assert result["has_more"] is True

        # Get last page
        response = await client.get(
            f"/api/v1/deals/{test_deal.id}/activities?skip=4&limit=2",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        assert len(result["items"]) == 1
        assert result["total"] == 5
        assert result["has_more"] is False

    @pytest.mark.asyncio
    async def test_get_timeline_nonexistent_deal(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test getting timeline for non-existent deal."""
        fake_deal_id = uuid4()

        response = await client.get(
            f"/api/v1/deals/{fake_deal_id}/activities",
            headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_timeline_unauthorized(
        self,
        client: AsyncClient,
        test_deal: Deal
    ):
        """Test getting timeline without authentication."""
        response = await client.get(
            f"/api/v1/deals/{test_deal.id}/activities"
        )

        assert response.status_code == 401


class TestAddComment:
    """Test POST /api/v1/deals/{deal_id}/activities endpoint."""

    @pytest.mark.asyncio
    async def test_add_comment_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deal: Deal,
        test_user: User
    ):
        """Test adding comment to deal."""
        comment_data = {
            "text": "This is a test comment"
        }

        response = await client.post(
            f"/api/v1/deals/{test_deal.id}/activities",
            headers=auth_headers,
            json=comment_data
        )

        assert response.status_code == 201
        result = response.json()

        assert result["type"] == "comment"
        assert result["deal_id"] == str(test_deal.id)
        assert result["author_id"] == str(test_user.id)
        assert "payload" in result
        assert result["payload"]["text"] == comment_data["text"]
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_add_comment_long_text(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deal: Deal
    ):
        """Test adding comment with long text."""
        long_text = "A" * 1000
        comment_data = {
            "text": long_text
        }

        response = await client.post(
            f"/api/v1/deals/{test_deal.id}/activities",
            headers=auth_headers,
            json=comment_data
        )

        assert response.status_code == 201
        result = response.json()

        assert result["payload"]["text"] == long_text

    @pytest.mark.asyncio
    async def test_add_comment_empty_text_fails(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deal: Deal
    ):
        """Test adding comment with empty text fails."""
        comment_data = {
            "text": ""
        }

        response = await client.post(
            f"/api/v1/deals/{test_deal.id}/activities",
            headers=auth_headers,
            json=comment_data
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_add_comment_missing_text_fails(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deal: Deal
    ):
        """Test adding comment without text fails."""
        comment_data = {}

        response = await client.post(
            f"/api/v1/deals/{test_deal.id}/activities",
            headers=auth_headers,
            json=comment_data
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_add_comment_nonexistent_deal(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test adding comment to non-existent deal."""
        fake_deal_id = uuid4()
        comment_data = {
            "text": "Comment for nonexistent deal"
        }

        response = await client.post(
            f"/api/v1/deals/{fake_deal_id}/activities",
            headers=auth_headers,
            json=comment_data
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_comment_unauthorized(
        self,
        client: AsyncClient,
        test_deal: Deal
    ):
        """Test adding comment without authentication."""
        comment_data = {
            "text": "Unauthorized comment"
        }

        response = await client.post(
            f"/api/v1/deals/{test_deal.id}/activities",
            json=comment_data
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_add_multiple_comments(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deal: Deal
    ):
        """Test adding multiple comments in sequence."""
        comments = [
            "First comment",
            "Second comment",
            "Third comment"
        ]

        activity_ids = []
        for comment_text in comments:
            response = await client.post(
                f"/api/v1/deals/{test_deal.id}/activities",
                headers=auth_headers,
                json={"text": comment_text}
            )
            assert response.status_code == 201
            activity_ids.append(response.json()["id"])

        # Verify all comments are in timeline
        timeline_response = await client.get(
            f"/api/v1/deals/{test_deal.id}/activities",
            headers=auth_headers
        )

        assert timeline_response.status_code == 200
        timeline = timeline_response.json()

        assert timeline["total"] == 3
        assert len(timeline["items"]) == 3

        # Verify comments are in reverse chronological order (newest first)
        timeline_texts = [item["payload"]["text"] for item in timeline["items"]]
        assert timeline_texts == list(reversed(comments))


class TestSystemActivities:
    """Test system-generated activities (status changes, etc.)."""

    @pytest.mark.asyncio
    async def test_status_change_creates_activity(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deal: Deal
    ):
        """Test that changing deal status creates activity."""
        # Update deal status to won
        update_data = {
            "status": "won",
            "stage": "closed"
        }

        response = await client.patch(
            f"/api/v1/deals/{test_deal.id}",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200

        # Check timeline for status_changed activity
        timeline_response = await client.get(
            f"/api/v1/deals/{test_deal.id}/activities",
            headers=auth_headers
        )

        assert timeline_response.status_code == 200
        timeline = timeline_response.json()

        # Should have at least one activity
        assert timeline["total"] >= 1

        # Find status_changed activity
        status_activities = [
            item for item in timeline["items"]
            if item["type"] == "status_changed"
        ]

        assert len(status_activities) >= 1

        # Verify activity has correct payload
        status_activity = status_activities[0]
        assert "old_status" in status_activity["payload"]
        assert "new_status" in status_activity["payload"]
        assert status_activity["payload"]["new_status"] == "won"

    @pytest.mark.asyncio
    async def test_stage_change_creates_activity(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deal: Deal
    ):
        """Test that changing deal stage creates activity."""
        # Update deal stage
        update_data = {
            "stage": "proposal"
        }

        response = await client.patch(
            f"/api/v1/deals/{test_deal.id}",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200

        # Check timeline for stage_changed activity
        timeline_response = await client.get(
            f"/api/v1/deals/{test_deal.id}/activities",
            headers=auth_headers
        )

        assert timeline_response.status_code == 200
        timeline = timeline_response.json()

        # Find stage_changed activity
        stage_activities = [
            item for item in timeline["items"]
            if item["type"] == "stage_changed"
        ]

        assert len(stage_activities) >= 1

        # Verify activity has correct payload
        stage_activity = stage_activities[0]
        assert "old_stage" in stage_activity["payload"]
        assert "new_stage" in stage_activity["payload"]
        assert stage_activity["payload"]["new_stage"] == "proposal"

    @pytest.mark.asyncio
    async def test_mixed_activities_order(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_deal: Deal
    ):
        """Test that user comments and system activities are ordered correctly."""
        # Add comment
        await client.post(
            f"/api/v1/deals/{test_deal.id}/activities",
            headers=auth_headers,
            json={"text": "Comment before status change"}
        )

        # Change status
        await client.patch(
            f"/api/v1/deals/{test_deal.id}",
            headers=auth_headers,
            json={"status": "won", "stage": "closed"}
        )

        # Add another comment
        await client.post(
            f"/api/v1/deals/{test_deal.id}/activities",
            headers=auth_headers,
            json={"text": "Comment after status change"}
        )

        # Get timeline
        timeline_response = await client.get(
            f"/api/v1/deals/{test_deal.id}/activities",
            headers=auth_headers
        )

        assert timeline_response.status_code == 200
        timeline = timeline_response.json()

        # Should have at least 3 activities
        assert timeline["total"] >= 3

        # Activities should be in reverse chronological order
        # Most recent first
        assert timeline["items"][0]["payload"]["text"] == "Comment after status change"
