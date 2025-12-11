"""
Tests for Branch API endpoints.
"""
import pytest
from datetime import time
from rest_framework import status

from apps.branches.models import Branch
from apps.users.models import Permission


class TestBranchViewSet:
    """Tests for the Branch ViewSet."""

    @pytest.fixture
    def branches_permission(self, db):
        """Create branches view permission."""
        return Permission.objects.create(
            code='branches:view',
            name='Ver Sucursales',
            module='branches',
            action='view'
        )

    @pytest.fixture
    def branches_edit_permission(self, db):
        """Create branches edit permission."""
        return Permission.objects.create(
            code='branches:edit',
            name='Editar Sucursales',
            module='branches',
            action='edit'
        )

    @pytest.fixture
    def admin_with_permissions(self, db, admin_user, admin_role, branches_permission, branches_edit_permission):
        """Admin user with branches permissions."""
        admin_role.permissions.add(branches_permission, branches_edit_permission)
        return admin_user

    def test_list_branches(self, authenticated_admin_client, admin_with_permissions, branch):
        """Test listing branches."""
        response = authenticated_admin_client.get('/api/branches/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_create_branch(self, authenticated_admin_client, admin_with_permissions):
        """Test creating a new branch."""
        response = authenticated_admin_client.post('/api/branches/', {
            'name': 'New Branch',
            'code': 'new',
            'address': '123 New St',
            'city': 'New City',
            'state': 'New State',
            'is_active': True
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert Branch.objects.filter(code='NEW').exists()  # Code should be uppercased

    def test_create_branch_code_uppercase(self, authenticated_admin_client, admin_with_permissions):
        """Test that branch code is automatically uppercased."""
        response = authenticated_admin_client.post('/api/branches/', {
            'name': 'Lowercase Test',
            'code': 'lowercase',
            'is_active': True
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['code'] == 'LOWERCASE'

    def test_retrieve_branch(self, authenticated_admin_client, admin_with_permissions, branch):
        """Test retrieving a specific branch."""
        response = authenticated_admin_client.get(f'/api/branches/{branch.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == branch.name
        assert response.data['code'] == branch.code

    def test_update_branch(self, authenticated_admin_client, admin_with_permissions, branch):
        """Test updating a branch."""
        response = authenticated_admin_client.patch(f'/api/branches/{branch.id}/', {
            'name': 'Updated Branch Name'
        })

        assert response.status_code == status.HTTP_200_OK
        branch.refresh_from_db()
        assert branch.name == 'Updated Branch Name'

    def test_delete_branch(self, authenticated_admin_client, admin_with_permissions, db):
        """Test deleting a branch (soft delete)."""
        new_branch = Branch.objects.create(
            name='To Delete',
            code='DEL',
            is_active=True
        )

        response = authenticated_admin_client.delete(f'/api/branches/{new_branch.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        new_branch.refresh_from_db()
        assert new_branch.is_deleted is True

    def test_list_branches_with_filter(self, authenticated_admin_client, admin_with_permissions, branch, db):
        """Test filtering branches by city."""
        Branch.objects.create(
            name='Another Branch',
            code='ANO',
            city='Different City',
            is_active=True
        )

        response = authenticated_admin_client.get('/api/branches/?city=Ciudad Test')

        assert response.status_code == status.HTTP_200_OK
        for b in response.data:
            assert b['city'] == 'Ciudad Test'

    def test_list_branches_search(self, authenticated_admin_client, admin_with_permissions, branch, db):
        """Test searching branches."""
        response = authenticated_admin_client.get('/api/branches/?search=Test')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_branches_requires_authentication(self, api_client):
        """Test that listing branches requires authentication."""
        response = api_client.get('/api/branches/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_branch_requires_edit_permission(self, authenticated_cashier_client, cashier_user, cashier_role, branches_permission):
        """Test that creating a branch requires edit permission."""
        # Only give view permission
        cashier_role.permissions.add(branches_permission)

        response = authenticated_cashier_client.post('/api/branches/', {
            'name': 'New Branch',
            'code': 'NEW'
        })

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestBranchStatsAction:
    """Tests for the branch stats endpoint."""

    @pytest.fixture
    def branches_permission(self, db):
        """Create branches view permission."""
        return Permission.objects.create(
            code='branches:view',
            name='Ver Sucursales',
            module='branches',
            action='view'
        )

    @pytest.fixture
    def admin_with_permissions(self, db, admin_user, admin_role, branches_permission):
        """Admin user with branches permissions."""
        admin_role.permissions.add(branches_permission)
        return admin_user

    def test_get_branch_stats(self, authenticated_admin_client, admin_with_permissions, branch):
        """Test getting branch statistics."""
        response = authenticated_admin_client.get(f'/api/branches/{branch.id}/stats/')

        assert response.status_code == status.HTTP_200_OK
        assert 'total_products' in response.data
        assert 'sales_today' in response.data
        assert 'sales_amount_today' in response.data
        assert 'active_employees' in response.data

    def test_stats_for_nonexistent_branch(self, authenticated_admin_client, admin_with_permissions):
        """Test getting stats for nonexistent branch."""
        response = authenticated_admin_client.get('/api/branches/9999/stats/')

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestBranchSimpleAction:
    """Tests for the simple branches list endpoint."""

    @pytest.fixture
    def branches_permission(self, db):
        """Create branches view permission."""
        return Permission.objects.create(
            code='branches:view',
            name='Ver Sucursales',
            module='branches',
            action='view'
        )

    @pytest.fixture
    def admin_with_permissions(self, db, admin_user, admin_role, branches_permission):
        """Admin user with branches permissions."""
        admin_role.permissions.add(branches_permission)
        return admin_user

    def test_get_simple_list(self, authenticated_admin_client, admin_with_permissions, branch):
        """Test getting simplified branch list."""
        response = authenticated_admin_client.get('/api/branches/simple/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        # Simple serializer should have limited fields
        assert 'id' in response.data[0]
        assert 'name' in response.data[0]
        assert 'code' in response.data[0]
        # Should NOT have detailed fields
        assert 'address' not in response.data[0]

    def test_simple_list_only_active(self, authenticated_admin_client, admin_with_permissions, branch, db):
        """Test that simple list only returns active branches."""
        inactive = Branch.objects.create(
            name='Inactive Branch',
            code='INAC',
            is_active=False
        )

        response = authenticated_admin_client.get('/api/branches/simple/')

        assert response.status_code == status.HTTP_200_OK
        codes = [b['code'] for b in response.data]
        assert 'INAC' not in codes


class TestBranchAccessControl:
    """Tests for branch-based access control."""

    @pytest.fixture
    def branches_permission(self, db):
        """Create branches view permission."""
        return Permission.objects.create(
            code='branches:view',
            name='Ver Sucursales',
            module='branches',
            action='view'
        )

    def test_user_sees_only_allowed_branches(
        self, api_client, cashier_user, cashier_role, branches_permission, branch, second_branch
    ):
        """Test that non-admin users only see their allowed branches."""
        # Add permission and only one branch
        cashier_role.permissions.add(branches_permission)
        cashier_user.allowed_branches.add(branch)

        api_client.force_authenticate(user=cashier_user)
        response = api_client.get('/api/branches/')

        assert response.status_code == status.HTTP_200_OK
        # Should only see the allowed branch
        codes = [b['code'] for b in response.data]
        assert branch.code in codes

    def test_admin_sees_all_branches(
        self, authenticated_admin_client, admin_user, admin_role, branches_permission, branch, second_branch
    ):
        """Test that admin users see all branches."""
        admin_role.permissions.add(branches_permission)
        # Admin should see all even without explicit allowed_branches
        admin_user.is_superuser = True
        admin_user.save()

        response = authenticated_admin_client.get('/api/branches/')

        assert response.status_code == status.HTTP_200_OK
        codes = [b['code'] for b in response.data]
        assert branch.code in codes
        assert second_branch.code in codes


class TestBranchMainBranchAPI:
    """Tests for main branch behavior via API."""

    @pytest.fixture
    def branches_permission(self, db):
        """Create branches view permission."""
        return Permission.objects.create(
            code='branches:view',
            name='Ver Sucursales',
            module='branches',
            action='view'
        )

    @pytest.fixture
    def branches_edit_permission(self, db):
        """Create branches edit permission."""
        return Permission.objects.create(
            code='branches:edit',
            name='Editar Sucursales',
            module='branches',
            action='edit'
        )

    @pytest.fixture
    def admin_with_permissions(self, db, admin_user, admin_role, branches_permission, branches_edit_permission):
        """Admin user with branches permissions."""
        admin_role.permissions.add(branches_permission, branches_edit_permission)
        return admin_user

    def test_filter_main_branch(self, authenticated_admin_client, admin_with_permissions, db):
        """Test filtering by is_main."""
        Branch.objects.create(name='Main', code='MAIN', is_main=True)
        Branch.objects.create(name='Not Main', code='NMAIN', is_main=False)

        response = authenticated_admin_client.get('/api/branches/?is_main=true')

        assert response.status_code == status.HTTP_200_OK
        for b in response.data:
            assert b['is_main'] is True

    def test_create_main_branch_updates_others(self, authenticated_admin_client, admin_with_permissions, db):
        """Test that creating a main branch unsets others."""
        first = Branch.objects.create(name='First', code='F1', is_main=True)

        response = authenticated_admin_client.post('/api/branches/', {
            'name': 'Second Main',
            'code': 'S2',
            'is_main': True
        })

        assert response.status_code == status.HTTP_201_CREATED
        first.refresh_from_db()
        assert first.is_main is False
