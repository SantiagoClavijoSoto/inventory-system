"""
CRUD tests for Supplier module.
Tests: Create, Read (list/detail), Update, Delete
"""
import pytest
from decimal import Decimal
from rest_framework import status

from apps.suppliers.models import Supplier
from apps.users.models import Permission


@pytest.fixture
def suppliers_permissions(db):
    """Create all supplier permissions."""
    perms = {
        'view': Permission.objects.create(code='suppliers:view', name='Ver', module='suppliers', action='view'),
        'create': Permission.objects.create(code='suppliers:create', name='Crear', module='suppliers', action='create'),
        'edit': Permission.objects.create(code='suppliers:edit', name='Editar', module='suppliers', action='edit'),
        'delete': Permission.objects.create(code='suppliers:delete', name='Eliminar', module='suppliers', action='delete'),
    }
    return perms


@pytest.fixture
def admin_role_with_supplier_perms(admin_role, suppliers_permissions):
    """Admin role with supplier permissions."""
    admin_role.permissions.add(*suppliers_permissions.values())
    return admin_role


@pytest.fixture
def authenticated_supplier_client(api_client, admin_user, admin_role_with_supplier_perms):
    """Authenticated client with supplier permissions."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def test_supplier(db, branch):
    """Create a test supplier."""
    return Supplier.objects.create(
        name='Proveedor Existente',
        code='PROV-EXIST-001',
        contact_name='Contacto Existente',
        email='existente@proveedor.com',
        phone='555-9999',
        city='Ciudad Existente',
        payment_terms=30,
        credit_limit=Decimal('5000.00'),
        company=branch.company if branch.company else None,
        is_active=True
    )


class TestSupplierCreate:
    """Tests for supplier creation."""

    def test_create_supplier_success(self, authenticated_supplier_client, branch):
        """Test creating a supplier successfully."""
        data = {
            'name': 'Proveedor Nuevo',
            'code': 'PROV-NEW-001',
            'contact_name': 'Juan Contacto',
            'email': 'contacto@nuevo.com',
            'phone': '555-1234',
            'city': 'Bogotá',
            'payment_terms': 30,
            'credit_limit': '10000.00',
            'is_active': True
        }

        response = authenticated_supplier_client.post('/api/v1/suppliers/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Proveedor Nuevo'
        assert response.data['code'] == 'PROV-NEW-001'

        # Verify supplier was created in database
        supplier = Supplier.objects.get(id=response.data['id'])
        assert supplier.name == 'Proveedor Nuevo'

    def test_create_supplier_assigns_company(self, authenticated_supplier_client, branch, admin_user):
        """Test that company is assigned from user on create."""
        # Set company on user
        from apps.companies.models import Company
        company = Company.objects.create(name='Test Co', slug='test-co', tax_id='123')
        branch.company = company
        branch.save()
        admin_user.company = company
        admin_user.save()

        data = {
            'name': 'Proveedor Con Company',
            'code': 'PROV-COMP-001',
            'payment_terms': 30,
            'credit_limit': '5000.00'
        }

        response = authenticated_supplier_client.post('/api/v1/suppliers/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED

        # Verify company was assigned
        supplier = Supplier.objects.get(id=response.data['id'])
        assert supplier.company == company

    def test_create_supplier_code_uppercase(self, authenticated_supplier_client):
        """Test that supplier code is converted to uppercase."""
        data = {
            'name': 'Proveedor Lowercase',
            'code': 'prov-lower-001',
            'payment_terms': 30,
            'credit_limit': '5000.00'
        }

        response = authenticated_supplier_client.post('/api/v1/suppliers/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['code'] == 'PROV-LOWER-001'


class TestSupplierRead:
    """Tests for reading suppliers."""

    def test_list_suppliers(self, authenticated_supplier_client, test_supplier):
        """Test listing suppliers."""
        response = authenticated_supplier_client.get('/api/v1/suppliers/')

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_list_serializer_fields(self, authenticated_supplier_client, test_supplier):
        """Test that list serializer has expected fields."""
        response = authenticated_supplier_client.get('/api/v1/suppliers/')

        assert response.status_code == status.HTTP_200_OK

        if response.data['results']:
            supplier_data = response.data['results'][0]
            # Fields that SHOULD be in list
            assert 'id' in supplier_data
            assert 'name' in supplier_data
            assert 'code' in supplier_data
            assert 'contact_name' in supplier_data
            assert 'email' in supplier_data
            assert 'phone' in supplier_data
            assert 'city' in supplier_data
            assert 'purchase_orders_count' in supplier_data

            # Field that IS NOT in list (only in detail)
            # This tests the bug: frontend expects total_purchases in list but it's not there
            has_total_purchases_in_list = 'total_purchases' in supplier_data
            print(f"total_purchases in list: {has_total_purchases_in_list}")

    def test_detail_supplier(self, authenticated_supplier_client, test_supplier):
        """Test getting supplier detail."""
        response = authenticated_supplier_client.get(f'/api/v1/suppliers/{test_supplier.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == test_supplier.name

    def test_detail_serializer_has_total_purchases(self, authenticated_supplier_client, test_supplier):
        """Test that detail serializer has total_purchases field."""
        response = authenticated_supplier_client.get(f'/api/v1/suppliers/{test_supplier.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert 'total_purchases' in response.data

    def test_search_suppliers(self, authenticated_supplier_client, test_supplier):
        """Test searching suppliers by name."""
        response = authenticated_supplier_client.get('/api/v1/suppliers/', {'search': 'Existente'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1


class TestSupplierUpdate:
    """Tests for updating suppliers."""

    def test_update_supplier_partial(self, authenticated_supplier_client, test_supplier):
        """Test partial update (PATCH) of supplier."""
        data = {
            'name': 'Proveedor Actualizado',
            'payment_terms': 45
        }

        response = authenticated_supplier_client.patch(
            f'/api/v1/suppliers/{test_supplier.id}/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Proveedor Actualizado'
        assert response.data['payment_terms'] == 45

        # Verify in database
        test_supplier.refresh_from_db()
        assert test_supplier.name == 'Proveedor Actualizado'
        assert test_supplier.payment_terms == 45

    def test_update_supplier_contact(self, authenticated_supplier_client, test_supplier):
        """Test updating supplier contact info."""
        data = {
            'contact_name': 'Nuevo Contacto',
            'email': 'nuevo@contacto.com',
            'phone': '555-0000'
        }

        response = authenticated_supplier_client.patch(
            f'/api/v1/suppliers/{test_supplier.id}/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['contact_name'] == 'Nuevo Contacto'


class TestSupplierDelete:
    """Tests for deleting suppliers."""

    def test_delete_supplier_soft_delete(self, authenticated_supplier_client, test_supplier):
        """Test that delete is a soft delete."""
        supplier_id = test_supplier.id

        response = authenticated_supplier_client.delete(f'/api/v1/suppliers/{supplier_id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify soft delete
        supplier = Supplier.objects.get(id=supplier_id)
        assert supplier.is_deleted is True
        assert supplier.deleted_at is not None

    def test_deleted_supplier_not_in_list(self, authenticated_supplier_client, test_supplier):
        """Test that deleted supplier doesn't appear in list."""
        supplier_id = test_supplier.id

        # Delete the supplier
        authenticated_supplier_client.delete(f'/api/v1/suppliers/{supplier_id}/')

        # Check list
        response = authenticated_supplier_client.get('/api/v1/suppliers/')

        assert response.status_code == status.HTTP_200_OK
        supplier_ids = [s['id'] for s in response.data['results']]
        assert supplier_id not in supplier_ids


class TestDataConsistency:
    """Tests for data consistency between list and detail views."""

    def test_total_purchases_in_both_list_and_detail(self, authenticated_supplier_client, test_supplier):
        """
        Verify that total_purchases is present in both list and detail serializers.
        """
        # Get list response
        list_response = authenticated_supplier_client.get('/api/v1/suppliers/')
        assert list_response.status_code == status.HTTP_200_OK

        # Get detail response
        detail_response = authenticated_supplier_client.get(f'/api/v1/suppliers/{test_supplier.id}/')
        assert detail_response.status_code == status.HTTP_200_OK

        # Check field presence
        list_data = list_response.data['results'][0] if list_response.data['results'] else {}
        detail_data = detail_response.data

        has_in_list = 'total_purchases' in list_data
        has_in_detail = 'total_purchases' in detail_data

        print(f"\ntotal_purchases in list: {has_in_list}")
        print(f"total_purchases in detail: {has_in_detail}")

        # Both should have total_purchases now
        assert has_in_detail is True, "total_purchases should be in detail"
        assert has_in_list is True, "total_purchases should now be in list serializer"
