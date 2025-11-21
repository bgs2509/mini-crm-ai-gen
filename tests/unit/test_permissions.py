"""
Unit tests for RBAC permissions system.
"""
from uuid import uuid4

import pytest

from app.models.organization_member import MemberRole
from app.core.permissions import PermissionChecker
from app.core.exceptions import AuthorizationError


class TestRoleHierarchy:
    """Test role hierarchy comparisons."""

    def test_owner_is_highest_role(self):
        """Test that owner is the highest role."""
        assert MemberRole.OWNER > MemberRole.ADMIN
        assert MemberRole.OWNER > MemberRole.MANAGER
        assert MemberRole.OWNER > MemberRole.MEMBER

    def test_admin_hierarchy(self):
        """Test admin role hierarchy."""
        assert MemberRole.ADMIN < MemberRole.OWNER
        assert MemberRole.ADMIN > MemberRole.MANAGER
        assert MemberRole.ADMIN > MemberRole.MEMBER

    def test_manager_hierarchy(self):
        """Test manager role hierarchy."""
        assert MemberRole.MANAGER < MemberRole.OWNER
        assert MemberRole.MANAGER < MemberRole.ADMIN
        assert MemberRole.MANAGER > MemberRole.MEMBER

    def test_member_is_lowest_role(self):
        """Test that member is the lowest role."""
        assert MemberRole.MEMBER < MemberRole.OWNER
        assert MemberRole.MEMBER < MemberRole.ADMIN
        assert MemberRole.MEMBER < MemberRole.MANAGER

    def test_role_equality(self):
        """Test role equality comparisons."""
        assert MemberRole.OWNER == MemberRole.OWNER
        assert MemberRole.ADMIN == MemberRole.ADMIN
        assert MemberRole.MANAGER == MemberRole.MANAGER
        assert MemberRole.MEMBER == MemberRole.MEMBER


class TestCheckMinimumRole:
    """Test minimum role checking."""

    def test_exact_role_match(self):
        """Test that exact role match passes."""
        # Should not raise exception
        PermissionChecker.check_minimum_role(MemberRole.ADMIN, MemberRole.ADMIN)
        PermissionChecker.check_minimum_role(MemberRole.MANAGER, MemberRole.MANAGER)

    def test_higher_role_passes(self):
        """Test that higher role passes minimum check."""
        # Owner can access admin-only resources
        PermissionChecker.check_minimum_role(MemberRole.OWNER, MemberRole.ADMIN)
        # Admin can access manager-only resources
        PermissionChecker.check_minimum_role(MemberRole.ADMIN, MemberRole.MANAGER)
        # Manager can access member-only resources
        PermissionChecker.check_minimum_role(MemberRole.MANAGER, MemberRole.MEMBER)

    def test_lower_role_fails(self):
        """Test that lower role fails minimum check."""
        with pytest.raises(AuthorizationError, match="Requires admin role or higher"):
            PermissionChecker.check_minimum_role(MemberRole.MEMBER, MemberRole.ADMIN)

        with pytest.raises(AuthorizationError, match="Requires owner role or higher"):
            PermissionChecker.check_minimum_role(MemberRole.MANAGER, MemberRole.OWNER)

        with pytest.raises(AuthorizationError, match="Requires owner role or higher"):
            PermissionChecker.check_minimum_role(MemberRole.ADMIN, MemberRole.OWNER)

    def test_owner_can_access_all(self):
        """Test that owner can access all role levels."""
        # Should not raise exception
        PermissionChecker.check_minimum_role(MemberRole.OWNER, MemberRole.OWNER)
        PermissionChecker.check_minimum_role(MemberRole.OWNER, MemberRole.ADMIN)
        PermissionChecker.check_minimum_role(MemberRole.OWNER, MemberRole.MANAGER)
        PermissionChecker.check_minimum_role(MemberRole.OWNER, MemberRole.MEMBER)

    def test_member_can_only_access_member(self):
        """Test that member can only access member-level resources."""
        # Should not raise exception
        PermissionChecker.check_minimum_role(MemberRole.MEMBER, MemberRole.MEMBER)

        # All higher roles should fail
        with pytest.raises(AuthorizationError):
            PermissionChecker.check_minimum_role(MemberRole.MEMBER, MemberRole.MANAGER)

        with pytest.raises(AuthorizationError):
            PermissionChecker.check_minimum_role(MemberRole.MEMBER, MemberRole.ADMIN)

        with pytest.raises(AuthorizationError):
            PermissionChecker.check_minimum_role(MemberRole.MEMBER, MemberRole.OWNER)


class TestCanModifyResource:
    """Test resource modification permissions."""

    def test_owner_can_modify_any_resource(self):
        """Test that owner can modify any resource."""
        user_id = uuid4()
        resource_owner_id = uuid4()

        # Should return True
        assert PermissionChecker.can_modify_resource(
            MemberRole.OWNER, resource_owner_id, user_id
        ) is True

    def test_admin_can_modify_any_resource(self):
        """Test that admin can modify any resource."""
        user_id = uuid4()
        resource_owner_id = uuid4()

        # Should return True
        assert PermissionChecker.can_modify_resource(
            MemberRole.ADMIN, resource_owner_id, user_id
        ) is True

    def test_user_can_modify_own_resource(self):
        """Test that user can modify their own resource."""
        user_id = uuid4()

        # Manager can modify own resource
        assert PermissionChecker.can_modify_resource(
            MemberRole.MANAGER, user_id, user_id
        ) is True

        # Member can modify own resource
        assert PermissionChecker.can_modify_resource(
            MemberRole.MEMBER, user_id, user_id
        ) is True

    def test_manager_cannot_modify_other_resource(self):
        """Test that manager cannot modify other user's resource."""
        user_id = uuid4()
        resource_owner_id = uuid4()

        assert PermissionChecker.can_modify_resource(
            MemberRole.MANAGER, resource_owner_id, user_id
        ) is False

    def test_member_cannot_modify_other_resource(self):
        """Test that member cannot modify other user's resource."""
        user_id = uuid4()
        resource_owner_id = uuid4()

        assert PermissionChecker.can_modify_resource(
            MemberRole.MEMBER, resource_owner_id, user_id
        ) is False

    def test_none_resource_owner(self):
        """Test modification when resource has no owner."""
        user_id = uuid4()

        # When resource has no owner, only admin/owner can modify
        assert PermissionChecker.can_modify_resource(
            MemberRole.OWNER, None, user_id
        ) is True

        assert PermissionChecker.can_modify_resource(
            MemberRole.ADMIN, None, user_id
        ) is True

        assert PermissionChecker.can_modify_resource(
            MemberRole.MANAGER, None, user_id
        ) is False

        assert PermissionChecker.can_modify_resource(
            MemberRole.MEMBER, None, user_id
        ) is False


class TestDealStagePermissions:
    """Test deal stage change permissions."""

    def test_owner_can_change_stage_backward(self):
        """Test that owner can change deal stage backward."""
        assert PermissionChecker.can_change_deal_stage_backward(MemberRole.OWNER) is True

    def test_admin_can_change_stage_backward(self):
        """Test that admin can change deal stage backward."""
        assert PermissionChecker.can_change_deal_stage_backward(MemberRole.ADMIN) is True

    def test_manager_cannot_change_stage_backward(self):
        """Test that manager cannot change deal stage backward."""
        assert PermissionChecker.can_change_deal_stage_backward(MemberRole.MANAGER) is False

    def test_member_cannot_change_stage_backward(self):
        """Test that member cannot change deal stage backward."""
        assert PermissionChecker.can_change_deal_stage_backward(MemberRole.MEMBER) is False


class TestContactCreationPermissions:
    """Test contact creation permissions."""

    def test_all_roles_can_create_contacts(self):
        """Test that all roles can create contacts."""
        # All roles should be able to create contacts
        assert PermissionChecker.can_create_contact(MemberRole.OWNER) is True
        assert PermissionChecker.can_create_contact(MemberRole.ADMIN) is True
        assert PermissionChecker.can_create_contact(MemberRole.MANAGER) is True
        assert PermissionChecker.can_create_contact(MemberRole.MEMBER) is True


class TestDealCreationPermissions:
    """Test deal creation permissions."""

    def test_all_roles_can_create_deals(self):
        """Test that all roles can create deals."""
        # All roles should be able to create deals
        assert PermissionChecker.can_create_deal(MemberRole.OWNER) is True
        assert PermissionChecker.can_create_deal(MemberRole.ADMIN) is True
        assert PermissionChecker.can_create_deal(MemberRole.MANAGER) is True
        assert PermissionChecker.can_create_deal(MemberRole.MEMBER) is True


class TestMemberManagementPermissions:
    """Test organization member management permissions."""

    def test_owner_can_manage_members(self):
        """Test that owner can manage members."""
        assert PermissionChecker.can_manage_members(MemberRole.OWNER) is True

    def test_admin_can_manage_members(self):
        """Test that admin can manage members."""
        assert PermissionChecker.can_manage_members(MemberRole.ADMIN) is True

    def test_manager_cannot_manage_members(self):
        """Test that manager cannot manage members."""
        assert PermissionChecker.can_manage_members(MemberRole.MANAGER) is False

    def test_member_cannot_manage_members(self):
        """Test that member cannot manage members."""
        assert PermissionChecker.can_manage_members(MemberRole.MEMBER) is False
