"""
Integration tests for organization API endpoints.
"""
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, MemberRole


class TestGetMyOrganizationsEndpoint:
    """Test GET /api/v1/organizations/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_my_organizations_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization
    ):
        """Test successfully getting user's organizations."""
        response = await client.get(
            "/api/v1/organizations/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == str(test_organization.id)
        assert result[0]["name"] == test_organization.name
        assert result[0]["role"] == "owner"

    @pytest.mark.asyncio
    async def test_get_my_organizations_multiple(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
        test_organization: Organization
    ):
        """Test getting multiple organizations for user."""
        # Create second organization
        org2 = Organization(
            id=uuid4(),
            name="Second Organization",
            default_currency="EUR"
        )
        db_session.add(org2)
        await db_session.commit()

        # Add membership
        membership = OrganizationMember(
            id=uuid4(),
            organization_id=org2.id,
            user_id=test_user.id,
            role=MemberRole.ADMIN
        )
        db_session.add(membership)
        await db_session.commit()

        response = await client.get(
            "/api/v1/organizations/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        assert len(result) == 2
        org_names = {org["name"] for org in result}
        assert "Test Organization" in org_names
        assert "Second Organization" in org_names

    @pytest.mark.asyncio
    async def test_get_my_organizations_unauthorized(self, client: AsyncClient):
        """Test getting organizations without authentication."""
        response = await client.get("/api/v1/organizations/me")

        assert response.status_code == 401


class TestGetOrganizationEndpoint:
    """Test GET /api/v1/organizations/{org_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_organization_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization
    ):
        """Test successfully getting organization details."""
        response = await client.get(
            f"/api/v1/organizations/{test_organization.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        assert result["id"] == str(test_organization.id)
        assert result["name"] == test_organization.name
        assert result["default_currency"] == test_organization.default_currency
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_get_organization_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test getting non-existent organization."""
        fake_id = uuid4()
        response = await client.get(
            f"/api/v1/organizations/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_organization_unauthorized(
        self,
        client: AsyncClient,
        test_organization: Organization
    ):
        """Test getting organization without authentication."""
        response = await client.get(
            f"/api/v1/organizations/{test_organization.id}"
        )

        assert response.status_code == 401


class TestUpdateOrganizationEndpoint:
    """Test PATCH /api/v1/organizations/{org_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_organization_as_owner(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization
    ):
        """Test updating organization as OWNER."""
        update_data = {
            "name": "Updated Organization Name",
            "default_currency": "EUR"
        }

        response = await client.patch(
            f"/api/v1/organizations/{test_organization.id}",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        result = response.json()

        assert result["name"] == "Updated Organization Name"
        assert result["default_currency"] == "EUR"

    @pytest.mark.asyncio
    async def test_update_organization_as_admin(
        self,
        client: AsyncClient,
        admin_auth_headers: dict,
        test_organization: Organization
    ):
        """Test updating organization as ADMIN."""
        update_data = {
            "name": "Admin Updated Name"
        }

        response = await client.patch(
            f"/api/v1/organizations/{test_organization.id}",
            headers=admin_auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        result = response.json()

        assert result["name"] == "Admin Updated Name"

    @pytest.mark.asyncio
    async def test_update_organization_as_manager_forbidden(
        self,
        client: AsyncClient,
        manager_auth_headers: dict,
        test_organization: Organization
    ):
        """Test updating organization as MANAGER (should fail)."""
        update_data = {
            "name": "Should Not Update"
        }

        response = await client.patch(
            f"/api/v1/organizations/{test_organization.id}",
            headers=manager_auth_headers,
            json=update_data
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_organization_as_member_forbidden(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
        test_organization: Organization
    ):
        """Test updating organization as MEMBER (should fail)."""
        update_data = {
            "name": "Should Not Update"
        }

        response = await client.patch(
            f"/api/v1/organizations/{test_organization.id}",
            headers=member_auth_headers,
            json=update_data
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_organization_partial_update(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization
    ):
        """Test partial update (name only)."""
        update_data = {
            "name": "Only Name Updated"
        }

        response = await client.patch(
            f"/api/v1/organizations/{test_organization.id}",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        result = response.json()

        assert result["name"] == "Only Name Updated"
        assert result["default_currency"] == "USD"  # Unchanged


class TestListMembersEndpoint:
    """Test GET /api/v1/organizations/{org_id}/members endpoint."""

    @pytest.mark.asyncio
    async def test_list_members_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization,
        test_user: User
    ):
        """Test listing organization members."""
        response = await client.get(
            f"/api/v1/organizations/{test_organization.id}/members",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        assert "members" in result
        assert "total" in result
        assert result["total"] >= 1

        # Check owner is in the list
        member_emails = {member["email"] for member in result["members"]}
        assert test_user.email in member_emails

    @pytest.mark.asyncio
    async def test_list_members_multiple_roles(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization,
        test_user: User,
        test_admin_user: User,
        test_manager_user: User,
        test_member_user: User,
        test_admin_membership: OrganizationMember,
        test_manager_membership: OrganizationMember,
        test_member_membership: OrganizationMember
    ):
        """Test listing members with different roles."""
        response = await client.get(
            f"/api/v1/organizations/{test_organization.id}/members",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        assert result["total"] == 4  # owner, admin, manager, member

        # Check all roles are present
        roles = {member["role"] for member in result["members"]}
        assert "owner" in roles
        assert "admin" in roles
        assert "manager" in roles
        assert "member" in roles

    @pytest.mark.asyncio
    async def test_list_members_all_roles_can_view(
        self,
        client: AsyncClient,
        member_auth_headers: dict,
        test_organization: Organization
    ):
        """Test that even MEMBER role can list members."""
        response = await client.get(
            f"/api/v1/organizations/{test_organization.id}/members",
            headers=member_auth_headers
        )

        assert response.status_code == 200


class TestAddMemberEndpoint:
    """Test POST /api/v1/organizations/{org_id}/members endpoint."""

    @pytest.mark.asyncio
    async def test_add_member_as_owner(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization,
        db_session: AsyncSession
    ):
        """Test adding member as OWNER."""
        # Create user to invite
        from app.core.security import hash_password
        new_user = User(
            id=uuid4(),
            email="newmember@example.com",
            hashed_password=hash_password("Pass123"),
            name="New Member"
        )
        db_session.add(new_user)
        await db_session.commit()

        invite_data = {
            "user_email": "newmember@example.com",
            "role": "member"
        }

        response = await client.post(
            f"/api/v1/organizations/{test_organization.id}/members",
            headers=auth_headers,
            json=invite_data
        )

        assert response.status_code == 201
        result = response.json()

        assert result["email"] == "newmember@example.com"
        assert result["role"] == "member"
        assert "joined_at" in result

    @pytest.mark.asyncio
    async def test_add_admin_as_owner(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization,
        db_session: AsyncSession
    ):
        """Test adding ADMIN as OWNER."""
        from app.core.security import hash_password
        new_user = User(
            id=uuid4(),
            email="newadmin@example.com",
            hashed_password=hash_password("Pass123"),
            name="New Admin"
        )
        db_session.add(new_user)
        await db_session.commit()

        invite_data = {
            "user_email": "newadmin@example.com",
            "role": "admin"
        }

        response = await client.post(
            f"/api/v1/organizations/{test_organization.id}/members",
            headers=auth_headers,
            json=invite_data
        )

        assert response.status_code == 201
        result = response.json()

        assert result["role"] == "admin"

    @pytest.mark.asyncio
    async def test_add_owner_as_owner(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization,
        db_session: AsyncSession
    ):
        """Test adding another OWNER as OWNER."""
        from app.core.security import hash_password
        new_user = User(
            id=uuid4(),
            email="newowner@example.com",
            hashed_password=hash_password("Pass123"),
            name="New Owner"
        )
        db_session.add(new_user)
        await db_session.commit()

        invite_data = {
            "user_email": "newowner@example.com",
            "role": "owner"
        }

        response = await client.post(
            f"/api/v1/organizations/{test_organization.id}/members",
            headers=auth_headers,
            json=invite_data
        )

        assert response.status_code == 201
        result = response.json()

        assert result["role"] == "owner"

    @pytest.mark.asyncio
    async def test_add_member_as_admin(
        self,
        client: AsyncClient,
        admin_auth_headers: dict,
        test_organization: Organization,
        db_session: AsyncSession
    ):
        """Test adding member as ADMIN."""
        from app.core.security import hash_password
        new_user = User(
            id=uuid4(),
            email="member2@example.com",
            hashed_password=hash_password("Pass123"),
            name="Member Two"
        )
        db_session.add(new_user)
        await db_session.commit()

        invite_data = {
            "user_email": "member2@example.com",
            "role": "member"
        }

        response = await client.post(
            f"/api/v1/organizations/{test_organization.id}/members",
            headers=admin_auth_headers,
            json=invite_data
        )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_add_owner_as_admin_forbidden(
        self,
        client: AsyncClient,
        admin_auth_headers: dict,
        test_organization: Organization,
        db_session: AsyncSession
    ):
        """Test ADMIN cannot add OWNER."""
        from app.core.security import hash_password
        new_user = User(
            id=uuid4(),
            email="shouldnotbeowner@example.com",
            hashed_password=hash_password("Pass123"),
            name="Should Not Be Owner"
        )
        db_session.add(new_user)
        await db_session.commit()

        invite_data = {
            "user_email": "shouldnotbeowner@example.com",
            "role": "owner"
        }

        response = await client.post(
            f"/api/v1/organizations/{test_organization.id}/members",
            headers=admin_auth_headers,
            json=invite_data
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_add_member_as_manager_forbidden(
        self,
        client: AsyncClient,
        manager_auth_headers: dict,
        test_organization: Organization,
        db_session: AsyncSession
    ):
        """Test MANAGER cannot add members."""
        from app.core.security import hash_password
        new_user = User(
            id=uuid4(),
            email="shouldnotadd@example.com",
            hashed_password=hash_password("Pass123"),
            name="Should Not Add"
        )
        db_session.add(new_user)
        await db_session.commit()

        invite_data = {
            "user_email": "shouldnotadd@example.com",
            "role": "member"
        }

        response = await client.post(
            f"/api/v1/organizations/{test_organization.id}/members",
            headers=manager_auth_headers,
            json=invite_data
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_add_member_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization
    ):
        """Test adding non-existent user."""
        invite_data = {
            "user_email": "nonexistent@example.com",
            "role": "member"
        }

        response = await client.post(
            f"/api/v1/organizations/{test_organization.id}/members",
            headers=auth_headers,
            json=invite_data
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_existing_member(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization,
        test_admin_user: User,
        test_admin_membership: OrganizationMember
    ):
        """Test adding user who is already a member."""
        invite_data = {
            "user_email": test_admin_user.email,
            "role": "member"
        }

        response = await client.post(
            f"/api/v1/organizations/{test_organization.id}/members",
            headers=auth_headers,
            json=invite_data
        )

        assert response.status_code == 400


class TestRemoveMemberEndpoint:
    """Test DELETE /api/v1/organizations/{org_id}/members/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_remove_member_as_owner(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization,
        test_member_user: User,
        test_member_membership: OrganizationMember
    ):
        """Test removing member as OWNER."""
        response = await client.delete(
            f"/api/v1/organizations/{test_organization.id}/members/{test_member_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_remove_member_as_admin(
        self,
        client: AsyncClient,
        admin_auth_headers: dict,
        test_organization: Organization,
        test_member_user: User,
        test_member_membership: OrganizationMember
    ):
        """Test removing member as ADMIN."""
        response = await client.delete(
            f"/api/v1/organizations/{test_organization.id}/members/{test_member_user.id}",
            headers=admin_auth_headers
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_remove_admin_as_admin_forbidden(
        self,
        client: AsyncClient,
        admin_auth_headers: dict,
        test_organization: Organization,
        db_session: AsyncSession
    ):
        """Test ADMIN cannot remove another ADMIN."""
        # Create second admin
        from app.core.security import hash_password
        admin2 = User(
            id=uuid4(),
            email="admin2@example.com",
            hashed_password=hash_password("Pass123"),
            name="Admin Two"
        )
        db_session.add(admin2)
        await db_session.commit()

        membership = OrganizationMember(
            id=uuid4(),
            organization_id=test_organization.id,
            user_id=admin2.id,
            role=MemberRole.ADMIN
        )
        db_session.add(membership)
        await db_session.commit()

        response = await client.delete(
            f"/api/v1/organizations/{test_organization.id}/members/{admin2.id}",
            headers=admin_auth_headers
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_remove_owner_as_owner(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization,
        db_session: AsyncSession
    ):
        """Test OWNER can remove another OWNER if not the last one."""
        # Create second owner
        from app.core.security import hash_password
        owner2 = User(
            id=uuid4(),
            email="owner2@example.com",
            hashed_password=hash_password("Pass123"),
            name="Owner Two"
        )
        db_session.add(owner2)
        await db_session.commit()

        membership = OrganizationMember(
            id=uuid4(),
            organization_id=test_organization.id,
            user_id=owner2.id,
            role=MemberRole.OWNER
        )
        db_session.add(membership)
        await db_session.commit()

        response = await client.delete(
            f"/api/v1/organizations/{test_organization.id}/members/{owner2.id}",
            headers=auth_headers
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_remove_last_owner_forbidden(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization,
        test_user: User
    ):
        """Test cannot remove the last OWNER."""
        response = await client.delete(
            f"/api/v1/organizations/{test_organization.id}/members/{test_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_remove_member_as_manager_forbidden(
        self,
        client: AsyncClient,
        manager_auth_headers: dict,
        test_organization: Organization,
        test_member_user: User,
        test_member_membership: OrganizationMember
    ):
        """Test MANAGER cannot remove members."""
        response = await client.delete(
            f"/api/v1/organizations/{test_organization.id}/members/{test_member_user.id}",
            headers=manager_auth_headers
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_remove_nonexistent_member(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization
    ):
        """Test removing non-existent member."""
        fake_id = uuid4()
        response = await client.delete(
            f"/api/v1/organizations/{test_organization.id}/members/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404


class TestUpdateMemberRoleEndpoint:
    """Test PATCH /api/v1/organizations/{org_id}/members/{user_id}/role endpoint."""

    @pytest.mark.asyncio
    async def test_update_member_role_as_owner(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization,
        test_member_user: User,
        test_member_membership: OrganizationMember
    ):
        """Test updating member role as OWNER."""
        update_data = {
            "role": "manager"
        }

        response = await client.patch(
            f"/api/v1/organizations/{test_organization.id}/members/{test_member_user.id}/role",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        result = response.json()

        assert result["role"] == "manager"

    @pytest.mark.asyncio
    async def test_promote_to_admin(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization,
        test_member_user: User,
        test_member_membership: OrganizationMember
    ):
        """Test promoting member to ADMIN."""
        update_data = {
            "role": "admin"
        }

        response = await client.patch(
            f"/api/v1/organizations/{test_organization.id}/members/{test_member_user.id}/role",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        result = response.json()

        assert result["role"] == "admin"

    @pytest.mark.asyncio
    async def test_promote_to_owner(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization,
        test_member_user: User,
        test_member_membership: OrganizationMember
    ):
        """Test promoting member to OWNER."""
        update_data = {
            "role": "owner"
        }

        response = await client.patch(
            f"/api/v1/organizations/{test_organization.id}/members/{test_member_user.id}/role",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        result = response.json()

        assert result["role"] == "owner"

    @pytest.mark.asyncio
    async def test_demote_owner_to_admin(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization,
        db_session: AsyncSession
    ):
        """Test demoting OWNER to ADMIN (requires multiple owners)."""
        # Create second owner
        from app.core.security import hash_password
        owner2 = User(
            id=uuid4(),
            email="owner2@example.com",
            hashed_password=hash_password("Pass123"),
            name="Owner Two"
        )
        db_session.add(owner2)
        await db_session.commit()

        membership = OrganizationMember(
            id=uuid4(),
            organization_id=test_organization.id,
            user_id=owner2.id,
            role=MemberRole.OWNER
        )
        db_session.add(membership)
        await db_session.commit()

        update_data = {
            "role": "admin"
        }

        response = await client.patch(
            f"/api/v1/organizations/{test_organization.id}/members/{owner2.id}/role",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        result = response.json()

        assert result["role"] == "admin"

    @pytest.mark.asyncio
    async def test_demote_last_owner_forbidden(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization,
        test_user: User
    ):
        """Test cannot demote the last OWNER."""
        update_data = {
            "role": "admin"
        }

        response = await client.patch(
            f"/api/v1/organizations/{test_organization.id}/members/{test_user.id}/role",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_role_as_admin_forbidden(
        self,
        client: AsyncClient,
        admin_auth_headers: dict,
        test_organization: Organization,
        test_member_user: User,
        test_member_membership: OrganizationMember
    ):
        """Test ADMIN cannot update roles (only OWNER can)."""
        update_data = {
            "role": "manager"
        }

        response = await client.patch(
            f"/api/v1/organizations/{test_organization.id}/members/{test_member_user.id}/role",
            headers=admin_auth_headers,
            json=update_data
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_role_as_manager_forbidden(
        self,
        client: AsyncClient,
        manager_auth_headers: dict,
        test_organization: Organization,
        test_member_user: User,
        test_member_membership: OrganizationMember
    ):
        """Test MANAGER cannot update roles."""
        update_data = {
            "role": "admin"
        }

        response = await client.patch(
            f"/api/v1/organizations/{test_organization.id}/members/{test_member_user.id}/role",
            headers=manager_auth_headers,
            json=update_data
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_nonexistent_member_role(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization: Organization
    ):
        """Test updating role for non-existent member."""
        fake_id = uuid4()
        update_data = {
            "role": "admin"
        }

        response = await client.patch(
            f"/api/v1/organizations/{test_organization.id}/members/{fake_id}/role",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 404
