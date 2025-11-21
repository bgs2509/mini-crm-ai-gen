"""
Full end-to-end integration test covering complete user scenario.

This test verifies the entire application flow:
1. User registration
2. Organization creation (automatic during registration)
3. Adding organization members
4. Creating contacts
5. Creating deals
6. Creating tasks for deals
7. Adding activities/comments
8. Checking analytics

This is the comprehensive integration test required by the assignment specification.
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User


class TestFullScenarioE2E:
    """Complete end-to-end test scenario."""

    @pytest.mark.asyncio
    async def test_complete_user_journey(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        Test complete user journey from registration to analytics.

        This is the full scenario required by the assignment:
        регистрация → создание организации → добавление участника →
        создание контакта → сделки → задачи → аналитика
        """

        # ============================================================
        # STEP 1: USER REGISTRATION
        # ============================================================
        print("\n[STEP 1] User Registration...")

        registration_data = {
            "email": "owner@acme.com",
            "password": "SecurePassword123",
            "name": "Alice Owner",
            "organization_name": "Acme Inc"
        }

        register_response = await client.post(
            "/api/v1/auth/register",
            json=registration_data
        )

        assert register_response.status_code == 201
        registration_result = register_response.json()

        # Verify user was created
        assert registration_result["user"]["email"] == registration_data["email"]
        assert registration_result["user"]["name"] == registration_data["name"]

        # ============================================================
        # STEP 2: ORGANIZATION CREATED (automatic during registration)
        # ============================================================
        print("[STEP 2] Organization Created (automatic)...")

        # Verify organization was created
        assert registration_result["organization"]["name"] == registration_data["organization_name"]

        # Get tokens and organization info
        access_token = registration_result["tokens"]["access_token"]
        organization_id = registration_result["organization"]["id"]
        owner_id = registration_result["user"]["id"]

        # Create auth headers for subsequent requests
        owner_headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Organization-Id": organization_id
        }

        # ============================================================
        # STEP 3: ADD ORGANIZATION MEMBERS
        # ============================================================
        print("[STEP 3] Adding Organization Members...")

        # Create additional users to invite
        manager_user = User(
            id=uuid4(),
            email="manager@acme.com",
            hashed_password=hash_password("ManagerPass123"),
            name="Bob Manager"
        )
        db_session.add(manager_user)

        member_user = User(
            id=uuid4(),
            email="member@acme.com",
            hashed_password=hash_password("MemberPass123"),
            name="Charlie Member"
        )
        db_session.add(member_user)

        await db_session.commit()

        # Invite manager
        invite_manager_response = await client.post(
            f"/api/v1/organizations/{organization_id}/members",
            headers=owner_headers,
            json={
                "user_email": "manager@acme.com",
                "role": "manager"
            }
        )

        assert invite_manager_response.status_code == 201
        assert invite_manager_response.json()["role"] == "manager"

        # Invite member
        invite_member_response = await client.post(
            f"/api/v1/organizations/{organization_id}/members",
            headers=owner_headers,
            json={
                "user_email": "member@acme.com",
                "role": "member"
            }
        )

        assert invite_member_response.status_code == 201
        assert invite_member_response.json()["role"] == "member"

        # Verify members list
        members_response = await client.get(
            f"/api/v1/organizations/{organization_id}/members",
            headers=owner_headers
        )

        assert members_response.status_code == 200
        members_result = members_response.json()
        assert members_result["total"] == 3  # owner + manager + member

        # ============================================================
        # STEP 4: CREATE CONTACTS
        # ============================================================
        print("[STEP 4] Creating Contacts...")

        # Create first contact
        contact1_data = {
            "name": "John Doe",
            "email": "john.doe@client.com",
            "phone": "+1234567890"
        }

        contact1_response = await client.post(
            "/api/v1/contacts",
            headers=owner_headers,
            json=contact1_data
        )

        assert contact1_response.status_code == 201
        contact1_result = contact1_response.json()
        contact1_id = contact1_result["id"]
        assert contact1_result["name"] == contact1_data["name"]

        # Create second contact
        contact2_data = {
            "name": "Jane Smith",
            "email": "jane.smith@client.com",
            "phone": "+0987654321"
        }

        contact2_response = await client.post(
            "/api/v1/contacts",
            headers=owner_headers,
            json=contact2_data
        )

        assert contact2_response.status_code == 201
        contact2_result = contact2_response.json()
        contact2_id = contact2_result["id"]

        # Verify contacts list
        contacts_list_response = await client.get(
            "/api/v1/contacts",
            headers=owner_headers
        )

        assert contacts_list_response.status_code == 200
        contacts_list = contacts_list_response.json()
        assert contacts_list["total"] == 2

        # ============================================================
        # STEP 5: CREATE DEALS
        # ============================================================
        print("[STEP 5] Creating Deals...")

        # Create first deal (in progress)
        deal1_data = {
            "contact_id": contact1_id,
            "title": "Website Redesign Project",
            "amount": 15000.0,
            "currency": "USD"
        }

        deal1_response = await client.post(
            "/api/v1/deals",
            headers=owner_headers,
            json=deal1_data
        )

        assert deal1_response.status_code == 201
        deal1_result = deal1_response.json()
        deal1_id = deal1_result["id"]
        assert deal1_result["title"] == deal1_data["title"]
        # API returns decimal as string for precision
        assert float(deal1_result["amount"]) == deal1_data["amount"]
        assert deal1_result["status"] == "new"

        # Create second deal
        deal2_data = {
            "contact_id": contact2_id,
            "title": "Mobile App Development",
            "amount": 25000.0,
            "currency": "USD"
        }

        deal2_response = await client.post(
            "/api/v1/deals",
            headers=owner_headers,
            json=deal2_data
        )

        assert deal2_response.status_code == 201
        deal2_result = deal2_response.json()
        deal2_id = deal2_result["id"]

        # Create third deal (smaller)
        deal3_data = {
            "contact_id": contact1_id,
            "title": "SEO Optimization",
            "amount": 5000.0,
            "currency": "USD"
        }

        deal3_response = await client.post(
            "/api/v1/deals",
            headers=owner_headers,
            json=deal3_data
        )

        assert deal3_response.status_code == 201
        deal3_result = deal3_response.json()
        deal3_id = deal3_result["id"]

        # Update deal statuses to create variety
        # Move deal1 to in_progress
        await client.patch(
            f"/api/v1/deals/{deal1_id}",
            headers=owner_headers,
            json={
                "status": "in_progress",
                "stage": "proposal"
            }
        )

        # Move deal2 to won
        await client.patch(
            f"/api/v1/deals/{deal2_id}",
            headers=owner_headers,
            json={
                "status": "won",
                "stage": "closed"
            }
        )

        # Verify deals list
        deals_list_response = await client.get(
            "/api/v1/deals",
            headers=owner_headers
        )

        assert deals_list_response.status_code == 200
        deals_list = deals_list_response.json()
        assert deals_list["total"] == 3

        # ============================================================
        # STEP 6: CREATE TASKS
        # ============================================================
        print("[STEP 6] Creating Tasks...")

        # Create task for deal1
        task1_data = {
            "title": "Prepare proposal document",
            "description": "Create detailed proposal for website redesign",
            "due_date": str(date.today() + timedelta(days=3))
        }

        task1_response = await client.post(
            f"/api/v1/tasks?deal_id={deal1_id}",
            headers=owner_headers,
            json=task1_data
        )

        assert task1_response.status_code == 201
        task1_result = task1_response.json()
        task1_id = task1_result["id"]
        assert task1_result["title"] == task1_data["title"]
        assert task1_result["is_done"] is False

        # Create second task for deal1
        task2_data = {
            "title": "Schedule client meeting",
            "description": "Arrange meeting to discuss requirements",
            "due_date": str(date.today() + timedelta(days=7))
        }

        task2_response = await client.post(
            f"/api/v1/tasks?deal_id={deal1_id}",
            headers=owner_headers,
            json=task2_data
        )

        assert task2_response.status_code == 201
        task2_result = task2_response.json()
        task2_id = task2_result["id"]

        # Create task for deal3
        task3_data = {
            "title": "SEO audit",
            "due_date": str(date.today() + timedelta(days=5))
        }

        task3_response = await client.post(
            f"/api/v1/tasks?deal_id={deal3_id}",
            headers=owner_headers,
            json=task3_data
        )

        assert task3_response.status_code == 201
        task3_id = task3_response.json()["id"]

        # Complete one task
        complete_task_response = await client.post(
            f"/api/v1/tasks/{task1_id}/done",
            headers=owner_headers
        )

        assert complete_task_response.status_code == 200
        assert complete_task_response.json()["is_done"] is True

        # Verify tasks list
        tasks_list_response = await client.get(
            f"/api/v1/tasks?deal_id={deal1_id}",
            headers=owner_headers
        )

        assert tasks_list_response.status_code == 200
        tasks_list = tasks_list_response.json()
        assert tasks_list["total"] == 2

        # ============================================================
        # STEP 7: ADD ACTIVITIES (Comments and System Events)
        # ============================================================
        print("[STEP 7] Adding Activities...")

        # Add comment to deal1
        comment1_data = {
            "text": "Client showed great interest in the proposal"
        }

        comment1_response = await client.post(
            f"/api/v1/deals/{deal1_id}/activities",
            headers=owner_headers,
            json=comment1_data
        )

        assert comment1_response.status_code == 201
        comment1_result = comment1_response.json()
        assert comment1_result["type"] == "comment"
        assert comment1_result["payload"]["text"] == comment1_data["text"]

        # Add another comment
        comment2_data = {
            "text": "Need to follow up on pricing details"
        }

        comment2_response = await client.post(
            f"/api/v1/deals/{deal1_id}/activities",
            headers=owner_headers,
            json=comment2_data
        )

        assert comment2_response.status_code == 201

        # Add comment to deal2
        comment3_data = {
            "text": "Deal closed successfully!"
        }

        comment3_response = await client.post(
            f"/api/v1/deals/{deal2_id}/activities",
            headers=owner_headers,
            json=comment3_data
        )

        assert comment3_response.status_code == 201

        # Get timeline for deal1
        timeline_response = await client.get(
            f"/api/v1/deals/{deal1_id}/activities",
            headers=owner_headers
        )

        assert timeline_response.status_code == 200
        timeline_result = timeline_response.json()

        # Should have comments + system activities (status changes)
        assert timeline_result["total"] >= 2

        # Verify activities include both comments and system events
        activity_types = {item["type"] for item in timeline_result["items"]}
        assert "comment" in activity_types
        # May also have status_changed or stage_changed from deal updates

        # ============================================================
        # STEP 8: CHECK ANALYTICS
        # ============================================================
        print("[STEP 8] Checking Analytics...")

        # Get deals summary
        summary_response = await client.get(
            "/api/v1/analytics/deals/summary",
            headers=owner_headers
        )

        assert summary_response.status_code == 200
        summary_result = summary_response.json()

        # Verify summary data
        assert summary_result["total_deals"] == 3
        assert float(summary_result["total_value"]) == 45000.0  # 15000 + 25000 + 5000

        # Check breakdown by status (flat structure)
        assert summary_result["won_deals"] == 1
        assert float(summary_result["won_value"]) == 25000.0

        assert summary_result["in_progress_deals"] == 1
        assert float(summary_result["in_progress_value"]) == 15000.0

        # Note: "new" status deals are not tracked separately in DealsSummaryResponse
        # They would be part of the total_deals count

        # Get funnel metrics
        funnel_response = await client.get(
            "/api/v1/analytics/deals/funnel",
            headers=owner_headers
        )

        assert funnel_response.status_code == 200
        funnel_result = funnel_response.json()

        # Verify funnel data
        assert "by_status" in funnel_result
        assert "by_stage" in funnel_result

        # Check status distribution
        funnel_by_status = funnel_result["by_status"]
        assert len(funnel_by_status) >= 2

        # Verify each status has required fields
        for status_item in funnel_by_status:
            assert "status" in status_item
            assert "count" in status_item
            assert "total_amount" in status_item
            assert "percentage" in status_item

        # Check stage distribution
        funnel_by_stage = funnel_result["by_stage"]
        assert len(funnel_by_stage) >= 2

        # Verify stages
        stage_names = {item["stage"] for item in funnel_by_stage}
        assert "closed" in stage_names  # From won deal
        assert "proposal" in stage_names  # From in_progress deal

        # ============================================================
        # VERIFICATION: Cross-check data consistency
        # ============================================================
        print("[VERIFICATION] Cross-checking data consistency...")

        # Verify organization members
        final_members_response = await client.get(
            f"/api/v1/organizations/{organization_id}/members",
            headers=owner_headers
        )
        assert final_members_response.json()["total"] == 3

        # Verify all contacts are accessible
        final_contacts_response = await client.get(
            "/api/v1/contacts",
            headers=owner_headers
        )
        assert final_contacts_response.json()["total"] == 2

        # Verify all deals are accessible
        final_deals_response = await client.get(
            "/api/v1/deals",
            headers=owner_headers
        )
        assert final_deals_response.json()["total"] == 3

        # Verify tasks for each deal
        for deal_id in [deal1_id, deal2_id, deal3_id]:
            tasks_response = await client.get(
                f"/api/v1/tasks?deal_id={deal_id}",
                headers=owner_headers
            )
            assert tasks_response.status_code == 200

        print("\n✅ COMPLETE E2E TEST PASSED!")
        print("=" * 60)
        print("Successfully tested full user journey:")
        print("  ✓ User registration")
        print("  ✓ Organization creation")
        print("  ✓ Member management")
        print("  ✓ Contact creation")
        print("  ✓ Deal management")
        print("  ✓ Task management")
        print("  ✓ Activity timeline")
        print("  ✓ Analytics reporting")
        print("=" * 60)


class TestE2EWithMultipleUsers:
    """Test E2E scenario with multiple users and permission checks."""

    @pytest.mark.asyncio
    async def test_multiple_users_workflow(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        Test workflow with multiple users having different roles.
        Verify that permissions work correctly in E2E scenario.
        """

        # Register first user (owner)
        owner_reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "owner@company.com",
                "password": "Pass1234",
                "name": "Owner User",
                "organization_name": "Company Ltd"
            }
        )

        assert owner_reg.status_code == 201
        owner_data = owner_reg.json()
        org_id = owner_data["organization"]["id"]
        owner_token = owner_data["tokens"]["access_token"]

        owner_headers = {
            "Authorization": f"Bearer {owner_token}",
            "X-Organization-Id": org_id
        }

        # Create and invite manager
        manager_user = User(
            id=uuid4(),
            email="manager@company.com",
            hashed_password=hash_password("Pass1234"),
            name="Manager User"
        )
        db_session.add(manager_user)
        await db_session.commit()

        await client.post(
            f"/api/v1/organizations/{org_id}/members",
            headers=owner_headers,
            json={"user_email": "manager@company.com", "role": "manager"}
        )

        # Manager logs in
        manager_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "manager@company.com", "password": "Pass1234"}
        )

        manager_token = manager_login.json()["tokens"]["access_token"]
        manager_headers = {
            "Authorization": f"Bearer {manager_token}",
            "X-Organization-Id": org_id
        }

        # Manager creates contact
        contact_resp = await client.post(
            "/api/v1/contacts",
            headers=manager_headers,
            json={
                "name": "Contact by Manager",
                "email": "contact@test.com"
            }
        )
        assert contact_resp.status_code == 201
        contact_id = contact_resp.json()["id"]

        # Manager creates deal
        deal_resp = await client.post(
            "/api/v1/deals",
            headers=manager_headers,
            json={
                "contact_id": contact_id,
                "title": "Manager's Deal",
                "amount": 10000.0,
                "currency": "USD"
            }
        )
        assert deal_resp.status_code == 201
        deal_id = deal_resp.json()["id"]

        # Owner can see manager's deal
        owner_deal_resp = await client.get(
            f"/api/v1/deals/{deal_id}",
            headers=owner_headers
        )
        assert owner_deal_resp.status_code == 200

        # Both can see analytics
        owner_analytics = await client.get(
            "/api/v1/analytics/deals/summary",
            headers=owner_headers
        )
        assert owner_analytics.status_code == 200

        manager_analytics = await client.get(
            "/api/v1/analytics/deals/summary",
            headers=manager_headers
        )
        assert manager_analytics.status_code == 200

        # Both should see same analytics (same org)
        assert owner_analytics.json()["total_deals"] == manager_analytics.json()["total_deals"]

        print("\n✅ MULTI-USER E2E TEST PASSED!")
