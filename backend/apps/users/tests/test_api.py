"""
Tests for User/Auth API endpoints.
"""
import pytest
from django.urls import reverse
from rest_framework import status

from apps.users.models import User, Role, Permission


class TestLoginEndpoint:
    """Tests for the login endpoint."""

    def test_login_success(self, api_client, admin_user):
        """Test successful login."""
        response = api_client.post('/api/v1/auth/login/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data
        assert response.data['user']['email'] == 'admin@test.com'

    def test_login_invalid_password(self, api_client, admin_user):
        """Test login with wrong password."""
        response = api_client.post('/api/v1/auth/login/', {
            'email': 'admin@test.com',
            'password': 'wrongpassword'
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_invalid_email(self, api_client, db):
        """Test login with non-existent email."""
        response = api_client.post('/api/v1/auth/login/', {
            'email': 'nonexistent@test.com',
            'password': 'testpass123'
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_inactive_user(self, api_client, db, admin_role):
        """Test login with inactive user."""
        user = User.objects.create_user(
            email='inactive@test.com',
            password='testpass123',
            first_name='Inactive',
            last_name='User',
            role=admin_role,
            is_active=False
        )

        response = api_client.post('/api/v1/auth/login/', {
            'email': 'inactive@test.com',
            'password': 'testpass123'
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_missing_fields(self, api_client):
        """Test login with missing fields."""
        response = api_client.post('/api/v1/auth/login/', {
            'email': 'test@test.com'
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestLogoutEndpoint:
    """Tests for the logout endpoint."""

    def test_logout_success(self, authenticated_admin_client, admin_user, api_client):
        """Test successful logout."""
        # First login to get tokens
        login_response = api_client.post('/api/v1/auth/login/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })
        refresh_token = login_response.data['refresh']

        # Then logout
        response = authenticated_admin_client.post('/api/v1/auth/logout/', {
            'refresh': refresh_token
        })

        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data

    def test_logout_requires_authentication(self, api_client):
        """Test that logout requires authentication."""
        response = api_client.post('/api/v1/auth/logout/', {
            'refresh': 'some_token'
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_invalid_token(self, authenticated_admin_client):
        """Test logout with invalid token."""
        response = authenticated_admin_client.post('/api/v1/auth/logout/', {
            'refresh': 'invalid_token'
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestMeEndpoint:
    """Tests for the /me endpoint."""

    def test_get_current_user(self, authenticated_admin_client, admin_user):
        """Test getting current user profile."""
        response = authenticated_admin_client.get('/api/v1/auth/me/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'admin@test.com'
        assert response.data['first_name'] == 'Admin'
        assert response.data['last_name'] == 'User'

    def test_update_current_user(self, authenticated_admin_client, admin_user):
        """Test updating current user profile."""
        response = authenticated_admin_client.patch('/api/v1/auth/me/', {
            'first_name': 'Updated',
            'phone': '555-9999'
        })

        assert response.status_code == status.HTTP_200_OK
        admin_user.refresh_from_db()
        assert admin_user.first_name == 'Updated'
        assert admin_user.phone == '555-9999'

    def test_me_requires_authentication(self, api_client):
        """Test that /me requires authentication."""
        response = api_client.get('/api/v1/auth/me/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestChangePasswordEndpoint:
    """Tests for the change password endpoint."""

    def test_change_password_success(self, authenticated_admin_client, admin_user):
        """Test successful password change."""
        response = authenticated_admin_client.post('/api/v1/auth/change-password/', {
            'current_password': 'testpass123',
            'new_password': 'newpass456!',
            'new_password_confirm': 'newpass456!'
        })

        assert response.status_code == status.HTTP_200_OK
        admin_user.refresh_from_db()
        assert admin_user.check_password('newpass456!')

    def test_change_password_wrong_current(self, authenticated_admin_client):
        """Test change password with wrong current password."""
        response = authenticated_admin_client.post('/api/v1/auth/change-password/', {
            'current_password': 'wrongpassword',
            'new_password': 'newpass456!',
            'new_password_confirm': 'newpass456!'
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_mismatch(self, authenticated_admin_client):
        """Test change password with mismatched new passwords."""
        response = authenticated_admin_client.post('/api/v1/auth/change-password/', {
            'current_password': 'testpass123',
            'new_password': 'newpass456!',
            'new_password_confirm': 'different789!'
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_requires_authentication(self, api_client):
        """Test that change password requires authentication."""
        response = api_client.post('/api/v1/auth/change-password/', {
            'current_password': 'testpass123',
            'new_password': 'newpass456!',
            'new_password_confirm': 'newpass456!'
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUserViewSet:
    """Tests for the User ViewSet (admin user management)."""

    @pytest.fixture
    def settings_permission(self, db):
        """Create settings permission."""
        return Permission.objects.create(
            code='settings:view',
            name='Ver Configuración',
            module='settings',
            action='view'
        )

    @pytest.fixture
    def settings_edit_permission(self, db):
        """Create settings edit permission."""
        return Permission.objects.create(
            code='settings:edit',
            name='Editar Configuración',
            module='settings',
            action='edit'
        )

    @pytest.fixture
    def admin_with_permissions(self, db, admin_user, admin_role, settings_permission, settings_edit_permission):
        """Admin user with settings permissions."""
        admin_role.permissions.add(settings_permission, settings_edit_permission)
        return admin_user

    def test_list_users(self, authenticated_admin_client, admin_with_permissions):
        """Test listing users."""
        response = authenticated_admin_client.get('/api/v1/auth/users/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_create_user(self, authenticated_admin_client, admin_with_permissions, admin_role):
        """Test creating a new user."""
        response = authenticated_admin_client.post('/api/v1/auth/users/', {
            'email': 'newuser@test.com',
            'password': 'newpass123!',
            'password_confirm': 'newpass123!',
            'first_name': 'New',
            'last_name': 'User',
            'role_id': admin_role.id
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email='newuser@test.com').exists()

    def test_create_user_password_mismatch(self, authenticated_admin_client, admin_with_permissions):
        """Test creating user with mismatched passwords."""
        response = authenticated_admin_client.post('/api/v1/auth/users/', {
            'email': 'newuser@test.com',
            'password': 'newpass123!',
            'password_confirm': 'different123!',
            'first_name': 'New',
            'last_name': 'User'
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_user(self, authenticated_admin_client, admin_with_permissions, admin_user):
        """Test retrieving a specific user."""
        response = authenticated_admin_client.get(f'/api/v1/auth/users/{admin_user.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == admin_user.email

    def test_update_user(self, authenticated_admin_client, admin_with_permissions, admin_user):
        """Test updating a user."""
        response = authenticated_admin_client.patch(f'/api/v1/auth/users/{admin_user.id}/', {
            'first_name': 'Updated Name'
        })

        assert response.status_code == status.HTTP_200_OK
        admin_user.refresh_from_db()
        assert admin_user.first_name == 'Updated Name'

    def test_delete_user(self, authenticated_admin_client, admin_with_permissions, db, admin_role):
        """Test deleting a user."""
        user_to_delete = User.objects.create_user(
            email='todelete@test.com',
            password='testpass123',
            first_name='To',
            last_name='Delete',
            role=admin_role
        )

        response = authenticated_admin_client.delete(f'/api/v1/auth/users/{user_to_delete.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(email='todelete@test.com').exists()

    def test_activate_user(self, authenticated_admin_client, admin_with_permissions, db, admin_role):
        """Test activating a user."""
        inactive_user = User.objects.create_user(
            email='inactive@test.com',
            password='testpass123',
            first_name='Inactive',
            last_name='User',
            role=admin_role,
            is_active=False
        )

        response = authenticated_admin_client.post(f'/api/v1/auth/users/{inactive_user.id}/activate/')

        assert response.status_code == status.HTTP_200_OK
        inactive_user.refresh_from_db()
        assert inactive_user.is_active is True

    def test_deactivate_user(self, authenticated_admin_client, admin_with_permissions, db, admin_role):
        """Test deactivating a user."""
        active_user = User.objects.create_user(
            email='active@test.com',
            password='testpass123',
            first_name='Active',
            last_name='User',
            role=admin_role,
            is_active=True
        )

        response = authenticated_admin_client.post(f'/api/v1/auth/users/{active_user.id}/deactivate/')

        assert response.status_code == status.HTTP_200_OK
        active_user.refresh_from_db()
        assert active_user.is_active is False

    def test_reset_password(self, authenticated_admin_client, admin_with_permissions, db, admin_role):
        """Test admin resetting a user's password."""
        user = User.objects.create_user(
            email='resetme@test.com',
            password='oldpass123',
            first_name='Reset',
            last_name='Me',
            role=admin_role
        )

        response = authenticated_admin_client.post(f'/api/v1/auth/users/{user.id}/reset_password/', {
            'new_password': 'newpass456!'
        })

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password('newpass456!')

    def test_reset_password_missing_password(self, authenticated_admin_client, admin_with_permissions, admin_user):
        """Test reset password without providing new password."""
        response = authenticated_admin_client.post(f'/api/v1/auth/users/{admin_user.id}/reset_password/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestRoleViewSet:
    """Tests for the Role ViewSet."""

    @pytest.fixture
    def settings_permission(self, db):
        """Create settings permission."""
        return Permission.objects.create(
            code='settings:view',
            name='Ver Configuración',
            module='settings',
            action='view'
        )

    @pytest.fixture
    def settings_edit_permission(self, db):
        """Create settings edit permission."""
        return Permission.objects.create(
            code='settings:edit',
            name='Editar Configuración',
            module='settings',
            action='edit'
        )

    @pytest.fixture
    def admin_with_permissions(self, db, admin_user, admin_role, settings_permission, settings_edit_permission):
        """Admin user with settings permissions."""
        admin_role.permissions.add(settings_permission, settings_edit_permission)
        return admin_user

    def test_list_roles(self, authenticated_admin_client, admin_with_permissions, admin_role):
        """Test listing roles."""
        response = authenticated_admin_client.get('/api/v1/auth/roles/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_create_role(self, authenticated_admin_client, admin_with_permissions):
        """Test creating a new role."""
        response = authenticated_admin_client.post('/api/v1/auth/roles/', {
            'name': 'New Role',
            'role_type': 'viewer',
            'description': 'A new test role'
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert Role.objects.filter(name='New Role').exists()

    def test_create_role_with_permissions(self, authenticated_admin_client, admin_with_permissions, db):
        """Test creating a role with permissions."""
        perm = Permission.objects.create(
            code='test:view',
            name='Test View',
            module='inventory',
            action='view'
        )

        response = authenticated_admin_client.post('/api/v1/auth/roles/', {
            'name': 'Role With Perms',
            'role_type': 'viewer',
            'permission_ids': [perm.id]
        })

        assert response.status_code == status.HTTP_201_CREATED
        role = Role.objects.get(name='Role With Perms')
        assert perm in role.permissions.all()

    def test_retrieve_role(self, authenticated_admin_client, admin_with_permissions, admin_role):
        """Test retrieving a specific role."""
        response = authenticated_admin_client.get(f'/api/v1/auth/roles/{admin_role.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == admin_role.name

    def test_update_role(self, authenticated_admin_client, admin_with_permissions, admin_role):
        """Test updating a role."""
        response = authenticated_admin_client.patch(f'/api/v1/auth/roles/{admin_role.id}/', {
            'description': 'Updated description'
        })

        assert response.status_code == status.HTTP_200_OK
        admin_role.refresh_from_db()
        assert admin_role.description == 'Updated description'

    def test_delete_role(self, authenticated_admin_client, admin_with_permissions, db):
        """Test deleting a role."""
        role = Role.objects.create(name='To Delete', role_type='viewer')

        response = authenticated_admin_client.delete(f'/api/v1/auth/roles/{role.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Role.objects.filter(name='To Delete').exists()

    def test_setup_defaults(self, authenticated_admin_client, admin_with_permissions, db):
        """Test creating default roles and permissions."""
        response = authenticated_admin_client.post('/api/v1/auth/roles/setup_defaults/')

        assert response.status_code == status.HTTP_200_OK
        # Verify default roles were created
        assert Role.objects.filter(role_type='admin').exists()
        assert Role.objects.filter(role_type='supervisor').exists()
        assert Role.objects.filter(role_type='cashier').exists()


class TestPermissionListView:
    """Tests for the Permission List endpoint."""

    @pytest.fixture
    def settings_permission(self, db):
        """Create settings permission."""
        return Permission.objects.create(
            code='settings:view',
            name='Ver Configuración',
            module='settings',
            action='view'
        )

    @pytest.fixture
    def admin_with_permissions(self, db, admin_user, admin_role, settings_permission):
        """Admin user with settings permissions."""
        admin_role.permissions.add(settings_permission)
        return admin_user

    def test_list_permissions(self, authenticated_admin_client, admin_with_permissions, db):
        """Test listing all permissions."""
        # Create some permissions
        Permission.objects.create(code='test:view', name='Test', module='inventory', action='view')
        Permission.objects.create(code='test:create', name='Test 2', module='inventory', action='create')

        response = authenticated_admin_client.get('/api/v1/auth/permissions/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2

    def test_list_permissions_filter_by_module(self, authenticated_admin_client, admin_with_permissions, db):
        """Test filtering permissions by module."""
        Permission.objects.create(code='inv:view', name='Inv', module='inventory', action='view')
        Permission.objects.create(code='sales:view', name='Sales', module='sales', action='view')

        response = authenticated_admin_client.get('/api/v1/auth/permissions/?module=inventory')

        assert response.status_code == status.HTTP_200_OK
        # Response is paginated, so access results list
        results = response.data.get('results', response.data)
        for perm in results:
            assert perm['module'] == 'inventory'

    def test_permissions_requires_authentication(self, api_client):
        """Test that permissions list requires authentication."""
        response = api_client.get('/api/v1/auth/permissions/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestTokenRefresh:
    """Tests for the token refresh endpoint."""

    def test_refresh_token(self, api_client, admin_user):
        """Test refreshing access token."""
        # First login to get tokens
        login_response = api_client.post('/api/v1/auth/login/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })
        refresh_token = login_response.data['refresh']

        # Refresh the token
        response = api_client.post('/api/v1/auth/refresh/', {
            'refresh': refresh_token
        })

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_refresh_invalid_token(self, api_client):
        """Test refresh with invalid token."""
        response = api_client.post('/api/v1/auth/refresh/', {
            'refresh': 'invalid_token'
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
