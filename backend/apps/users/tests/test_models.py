"""
Tests for User, Role, and Permission models.
"""
import pytest
from django.db import IntegrityError

from apps.users.models import User, Role, Permission


class TestPermissionModel:
    """Tests for the Permission model."""

    def test_permission_creation(self, db):
        """Test creating a permission."""
        permission = Permission.objects.create(
            code='inventory:view',
            name='Ver Inventario',
            module='inventory',
            action='view',
            description='Permite ver el inventario'
        )
        assert permission.id is not None
        assert permission.code == 'inventory:view'
        assert str(permission) == 'inventory:view'

    def test_permission_unique_code(self, db):
        """Test that permission code must be unique."""
        Permission.objects.create(
            code='test:action',
            name='Test Action',
            module='inventory',
            action='view'
        )
        with pytest.raises(IntegrityError):
            Permission.objects.create(
                code='test:action',
                name='Test Action 2',
                module='inventory',
                action='create'
            )

    def test_create_default_permissions(self, db):
        """Test creating default permissions for all module/action combinations."""
        Permission.create_default_permissions()

        # Should create permissions for all module/action combinations
        expected_count = len(Permission.MODULES) * len(Permission.ACTIONS)
        assert Permission.objects.count() == expected_count

        # Verify some specific permissions exist
        assert Permission.objects.filter(code='inventory:view').exists()
        assert Permission.objects.filter(code='sales:create').exists()
        assert Permission.objects.filter(code='employees:edit').exists()

    def test_permission_ordering(self, db):
        """Test that permissions are ordered by module then action."""
        Permission.objects.create(code='z:z', name='Z', module='settings', action='view')
        Permission.objects.create(code='a:a', name='A', module='dashboard', action='create')
        Permission.objects.create(code='a:b', name='B', module='dashboard', action='view')

        permissions = list(Permission.objects.all())
        # dashboard comes before settings alphabetically
        assert permissions[0].module == 'dashboard'


class TestRoleModel:
    """Tests for the Role model."""

    def test_role_creation(self, db):
        """Test creating a role."""
        role = Role.objects.create(
            name='Test Role',
            role_type='viewer',
            description='A test role',
            is_active=True
        )
        assert role.id is not None
        assert role.name == 'Test Role'
        assert str(role) == 'Test Role'

    def test_role_unique_name(self, db):
        """Test that role name must be unique."""
        Role.objects.create(name='Unique Role', role_type='viewer')
        with pytest.raises(IntegrityError):
            Role.objects.create(name='Unique Role', role_type='admin')

    def test_role_permissions_relationship(self, db):
        """Test that role can have multiple permissions."""
        role = Role.objects.create(name='Multi Perm Role', role_type='viewer')
        perm1 = Permission.objects.create(code='test:view', name='View', module='inventory', action='view')
        perm2 = Permission.objects.create(code='test:create', name='Create', module='inventory', action='create')

        role.permissions.add(perm1, perm2)

        assert role.permissions.count() == 2
        assert perm1 in role.permissions.all()
        assert perm2 in role.permissions.all()

    def test_role_default_type(self, db):
        """Test that default role_type is 'viewer'."""
        role = Role.objects.create(name='Default Type Role')
        assert role.role_type == 'viewer'

    def test_create_default_roles(self, db):
        """Test creating default roles."""
        # First create permissions
        Permission.create_default_permissions()
        # Then create roles
        Role.create_default_roles()

        # Should create 5 default roles
        assert Role.objects.count() == 5

        # Check that admin has all permissions
        admin = Role.objects.get(role_type='admin')
        assert admin.permissions.count() == Permission.objects.count()

        # Check that viewer only has view permissions
        viewer = Role.objects.get(role_type='viewer')
        assert all(p.action == 'view' for p in viewer.permissions.all())


class TestUserModel:
    """Tests for the User model."""

    def test_user_creation(self, db):
        """Test creating a user with email as username."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        assert user.id is not None
        assert user.email == 'test@example.com'
        assert user.username is None  # username field is removed
        assert user.check_password('testpass123')

    def test_user_str(self, db):
        """Test user string representation."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        assert str(user) == 'John Doe'

    def test_user_full_name_property(self, db):
        """Test full_name property."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith'
        )
        assert user.full_name == 'Jane Smith'

    def test_user_email_required(self, db):
        """Test that email is required."""
        with pytest.raises(ValueError, match='El email es obligatorio'):
            User.objects.create_user(
                email='',
                password='testpass123',
                first_name='Test',
                last_name='User'
            )

    def test_user_email_unique(self, db):
        """Test that email must be unique."""
        User.objects.create_user(
            email='unique@example.com',
            password='testpass123',
            first_name='First',
            last_name='User'
        )
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email='unique@example.com',
                password='testpass123',
                first_name='Second',
                last_name='User'
            )

    def test_create_superuser(self, db):
        """Test creating a superuser."""
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='Super'
        )
        assert superuser.is_staff is True
        assert superuser.is_superuser is True

    def test_superuser_requires_is_staff(self, db):
        """Test that superuser must have is_staff=True."""
        with pytest.raises(ValueError, match='Superuser debe tener is_staff=True'):
            User.objects.create_superuser(
                email='admin@example.com',
                password='adminpass123',
                first_name='Admin',
                last_name='Super',
                is_staff=False
            )

    def test_superuser_requires_is_superuser(self, db):
        """Test that superuser must have is_superuser=True."""
        with pytest.raises(ValueError, match='Superuser debe tener is_superuser=True'):
            User.objects.create_superuser(
                email='admin@example.com',
                password='adminpass123',
                first_name='Admin',
                last_name='Super',
                is_superuser=False
            )


class TestUserPermissions:
    """Tests for user permission checking."""

    @pytest.fixture
    def permission(self, db):
        """Create a test permission."""
        return Permission.objects.create(
            code='inventory:view',
            name='Ver Inventario',
            module='inventory',
            action='view'
        )

    @pytest.fixture
    def role_with_permission(self, db, permission):
        """Create a role with one permission."""
        role = Role.objects.create(name='Test Role', role_type='viewer')
        role.permissions.add(permission)
        return role

    def test_superuser_has_all_permissions(self, db):
        """Test that superuser has all permissions."""
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='Super'
        )
        assert superuser.has_permission('any:permission') is True
        assert superuser.has_permission('nonexistent:perm') is True

    def test_user_without_role_has_no_permissions(self, db):
        """Test that user without role has no permissions."""
        user = User.objects.create_user(
            email='norole@example.com',
            password='testpass123',
            first_name='No',
            last_name='Role'
        )
        assert user.has_permission('inventory:view') is False

    def test_user_has_permission_via_role(self, db, permission, role_with_permission):
        """Test that user has permission through their role."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role=role_with_permission
        )
        assert user.has_permission('inventory:view') is True
        assert user.has_permission('inventory:create') is False

    def test_has_module_permission(self, db, permission, role_with_permission):
        """Test checking module-level permissions."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role=role_with_permission
        )
        assert user.has_module_permission('inventory') is True
        assert user.has_module_permission('sales') is False

    def test_superuser_has_all_module_permissions(self, db):
        """Test that superuser has all module permissions."""
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='Super'
        )
        assert superuser.has_module_permission('any_module') is True

    def test_get_permissions(self, db, permission, role_with_permission):
        """Test getting list of permission codes."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role=role_with_permission
        )
        permissions = user.get_permissions()
        assert 'inventory:view' in permissions
        assert len(permissions) == 1

    def test_get_permissions_superuser(self, db):
        """Test that superuser gets all permissions."""
        Permission.create_default_permissions()
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='Super'
        )
        permissions = superuser.get_permissions()
        assert len(permissions) == Permission.objects.count()


class TestUserBranchAccess:
    """Tests for user branch access."""

    @pytest.fixture
    def test_branch(self, db):
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

    def test_superuser_can_access_any_branch(self, db, test_branch):
        """Test that superuser can access any branch."""
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='Super'
        )
        assert superuser.can_access_branch(test_branch.id) is True
        assert superuser.can_access_branch(9999) is True  # Even nonexistent

    def test_user_can_access_allowed_branch(self, db, test_branch):
        """Test that user can access branches in their allowed list."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        user.allowed_branches.add(test_branch)

        assert user.can_access_branch(test_branch.id) is True

    def test_user_cannot_access_non_allowed_branch(self, db, test_branch):
        """Test that user cannot access branches not in their allowed list."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        # Don't add any branches to allowed_branches

        assert user.can_access_branch(test_branch.id) is False
