"""
Tests for custom permission classes.
"""
import pytest
from unittest.mock import Mock, MagicMock
from rest_framework.test import APIRequestFactory

from apps.users.models import User, Role, Permission
from apps.users.permissions import (
    HasPermission,
    HasModulePermission,
    CanAccessBranch,
    IsOwnerOrAdmin,
    IsSameUserOrAdmin
)


@pytest.fixture
def request_factory():
    """API request factory."""
    return APIRequestFactory()


@pytest.fixture
def test_permission(db):
    """Create a test permission."""
    return Permission.objects.create(
        code='test:view',
        name='Test View',
        module='test',
        action='view'
    )


@pytest.fixture
def test_role(db, test_permission):
    """Create a test role with permission."""
    role = Role.objects.create(name='Test Role', role_type='viewer')
    role.permissions.add(test_permission)
    return role


@pytest.fixture
def regular_user(db, test_role):
    """Create a regular user with test role."""
    return User.objects.create_user(
        email='regular@test.com',
        password='testpass123',
        first_name='Regular',
        last_name='User',
        role=test_role
    )


@pytest.fixture
def superuser(db):
    """Create a superuser."""
    return User.objects.create_superuser(
        email='super@test.com',
        password='testpass123',
        first_name='Super',
        last_name='User'
    )


class TestHasPermission:
    """Tests for the HasPermission class."""

    def test_unauthenticated_user_denied(self, request_factory):
        """Test that unauthenticated users are denied."""
        request = request_factory.get('/')
        request.user = None

        permission = HasPermission()
        view = Mock(required_permission='test:view')

        assert permission.has_permission(request, view) is False

    def test_superuser_always_allowed(self, request_factory, superuser):
        """Test that superusers always have permission."""
        request = request_factory.get('/')
        request.user = superuser

        permission = HasPermission()
        view = Mock(required_permission='any:permission')

        assert permission.has_permission(request, view) is True

    def test_user_with_permission_allowed(self, request_factory, regular_user):
        """Test that user with required permission is allowed."""
        request = request_factory.get('/')
        request.user = regular_user

        permission = HasPermission()
        view = Mock(required_permission='test:view')

        assert permission.has_permission(request, view) is True

    def test_user_without_permission_denied(self, request_factory, regular_user):
        """Test that user without required permission is denied."""
        request = request_factory.get('/')
        request.user = regular_user

        permission = HasPermission()
        view = Mock(required_permission='other:permission')

        assert permission.has_permission(request, view) is False

    def test_no_required_permission_allows_all(self, request_factory, regular_user):
        """Test that when no permission is required, all authenticated users pass."""
        request = request_factory.get('/')
        request.user = regular_user

        permission = HasPermission()
        view = Mock(spec=[])  # No required_permission attribute

        assert permission.has_permission(request, view) is True

    def test_factory_pattern_usage(self, request_factory, regular_user):
        """Test using HasPermission with factory pattern."""
        request = request_factory.get('/')
        request.user = regular_user

        permission = HasPermission('test:view')
        view = Mock()

        assert permission.has_permission(request, view) is True

    def test_callable_returns_self(self):
        """Test that calling HasPermission returns self for DRF compatibility."""
        permission = HasPermission('test:view')
        assert permission() is permission


class TestHasModulePermission:
    """Tests for the HasModulePermission class."""

    def test_unauthenticated_user_denied(self, request_factory):
        """Test that unauthenticated users are denied."""
        request = request_factory.get('/')
        request.user = None

        permission = HasModulePermission()
        view = Mock(required_module='test')

        assert permission.has_permission(request, view) is False

    def test_superuser_always_allowed(self, request_factory, superuser):
        """Test that superusers always have module permission."""
        request = request_factory.get('/')
        request.user = superuser

        permission = HasModulePermission()
        view = Mock(required_module='any_module')

        assert permission.has_permission(request, view) is True

    def test_user_with_module_permission_allowed(self, request_factory, regular_user):
        """Test that user with any permission in module is allowed."""
        request = request_factory.get('/')
        request.user = regular_user

        permission = HasModulePermission()
        view = Mock(required_module='test')

        assert permission.has_permission(request, view) is True

    def test_user_without_module_permission_denied(self, request_factory, regular_user):
        """Test that user without any permission in module is denied."""
        request = request_factory.get('/')
        request.user = regular_user

        permission = HasModulePermission()
        view = Mock(required_module='other_module')

        assert permission.has_permission(request, view) is False

    def test_no_required_module_allows_all(self, request_factory, regular_user):
        """Test that when no module is required, all authenticated users pass."""
        request = request_factory.get('/')
        request.user = regular_user

        permission = HasModulePermission()
        view = Mock(spec=[])  # No required_module attribute

        assert permission.has_permission(request, view) is True


class TestCanAccessBranch:
    """Tests for the CanAccessBranch class."""

    @pytest.fixture
    def branch(self, db):
        """Create a test branch."""
        from apps.branches.models import Branch
        return Branch.objects.create(
            name='Test Branch',
            code='TST',
            address='Test Address',
            city='Test City',
            state='Test State',
            is_active=True
        )

    @pytest.fixture
    def user_with_branch(self, db, branch, test_role):
        """Create a user with branch access."""
        user = User.objects.create_user(
            email='branch@test.com',
            password='testpass123',
            first_name='Branch',
            last_name='User',
            role=test_role
        )
        user.allowed_branches.add(branch)
        return user

    def test_unauthenticated_user_denied(self, request_factory):
        """Test that unauthenticated users are denied."""
        request = request_factory.get('/')
        request.user = None
        request.query_params = {}
        request.data = {}

        permission = CanAccessBranch()
        view = Mock(kwargs={})

        assert permission.has_permission(request, view) is False

    def test_superuser_always_allowed(self, request_factory, superuser, branch):
        """Test that superusers can access any branch."""
        request = request_factory.get('/')
        request.user = superuser
        request.query_params = {'branch': str(branch.id)}
        request.data = {}

        permission = CanAccessBranch()
        view = Mock(kwargs={})

        assert permission.has_permission(request, view) is True

    def test_user_with_branch_access_allowed(self, request_factory, user_with_branch, branch):
        """Test that user can access their allowed branch."""
        request = request_factory.get('/')
        request.user = user_with_branch
        request.query_params = {}
        request.data = {'branch_id': branch.id}

        permission = CanAccessBranch()
        view = Mock(kwargs={})

        assert permission.has_permission(request, view) is True

    def test_user_without_branch_access_denied(self, request_factory, regular_user, branch):
        """Test that user cannot access branch not in their list."""
        request = request_factory.get('/')
        request.user = regular_user
        request.query_params = {}
        request.data = {'branch_id': branch.id}

        permission = CanAccessBranch()
        view = Mock(kwargs={})

        assert permission.has_permission(request, view) is False

    def test_branch_from_url_kwargs(self, request_factory, user_with_branch, branch):
        """Test getting branch_id from URL kwargs."""
        request = request_factory.get('/')
        request.user = user_with_branch
        request.query_params = {}
        request.data = {}

        permission = CanAccessBranch()
        view = Mock(kwargs={'branch_id': branch.id})

        assert permission.has_permission(request, view) is True

    def test_branch_from_query_params(self, request_factory, user_with_branch, branch):
        """Test getting branch from query params."""
        request = request_factory.get('/')
        request.user = user_with_branch
        request.query_params = {'branch': str(branch.id)}
        request.data = {}

        permission = CanAccessBranch()
        view = Mock(kwargs={})

        assert permission.has_permission(request, view) is True

    def test_no_branch_specified_allowed(self, request_factory, regular_user):
        """Test that when no branch is specified, access is allowed."""
        request = request_factory.get('/')
        request.user = regular_user
        request.query_params = {}
        request.data = {}

        permission = CanAccessBranch()
        view = Mock(kwargs={})

        assert permission.has_permission(request, view) is True

    def test_invalid_branch_id_denied(self, request_factory, regular_user):
        """Test that invalid branch_id format is denied."""
        request = request_factory.get('/')
        request.user = regular_user
        request.query_params = {'branch': 'invalid'}
        request.data = {}

        permission = CanAccessBranch()
        view = Mock(kwargs={})

        assert permission.has_permission(request, view) is False


class TestIsOwnerOrAdmin:
    """Tests for the IsOwnerOrAdmin class."""

    def test_superuser_always_allowed(self, superuser):
        """Test that superusers can access any object."""
        request = Mock(user=superuser)
        obj = Mock(user=Mock())  # Object owned by someone else

        permission = IsOwnerOrAdmin()

        assert permission.has_object_permission(request, Mock(), obj) is True

    def test_owner_allowed_via_user_field(self, regular_user):
        """Test that owner can access object via user field."""
        request = Mock(user=regular_user)
        obj = Mock(user=regular_user)

        permission = IsOwnerOrAdmin()

        assert permission.has_object_permission(request, Mock(), obj) is True

    def test_owner_allowed_via_created_by_field(self, regular_user):
        """Test that owner can access object via created_by field."""
        request = Mock(user=regular_user)
        obj = Mock(spec=['created_by'], created_by=regular_user)

        permission = IsOwnerOrAdmin()

        assert permission.has_object_permission(request, Mock(), obj) is True

    def test_non_owner_denied(self, regular_user, db):
        """Test that non-owner cannot access object."""
        other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )

        request = Mock(user=regular_user)
        obj = Mock(user=other_user)

        permission = IsOwnerOrAdmin()

        assert permission.has_object_permission(request, Mock(), obj) is False

    def test_object_without_user_fields_denied(self, regular_user):
        """Test that object without user/created_by fields denies access."""
        request = Mock(user=regular_user)
        obj = Mock(spec=[])  # No user or created_by attribute

        permission = IsOwnerOrAdmin()

        assert permission.has_object_permission(request, Mock(), obj) is False


class TestIsSameUserOrAdmin:
    """Tests for the IsSameUserOrAdmin class."""

    def test_superuser_always_allowed(self, superuser, regular_user):
        """Test that superusers can access any user's data."""
        request = Mock(user=superuser)

        permission = IsSameUserOrAdmin()

        assert permission.has_object_permission(request, Mock(), regular_user) is True

    def test_same_user_allowed(self, regular_user):
        """Test that user can access their own data."""
        request = Mock(user=regular_user)

        permission = IsSameUserOrAdmin()

        assert permission.has_object_permission(request, Mock(), regular_user) is True

    def test_different_user_denied(self, regular_user, db):
        """Test that user cannot access another user's data."""
        other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )

        request = Mock(user=regular_user)

        permission = IsSameUserOrAdmin()

        assert permission.has_object_permission(request, Mock(), other_user) is False
