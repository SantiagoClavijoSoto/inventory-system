"""
Tests for Sales API endpoints.
"""
import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status

from apps.sales.models import Sale, SaleItem, DailyCashRegister
from apps.sales.services import SaleService
from apps.users.models import Permission


@pytest.mark.django_db
class TestSaleViewSet:
    """Tests for Sale API endpoints."""

    @pytest.fixture
    def sales_view_permission(self, db):
        """Create sales view permission."""
        return Permission.objects.create(
            code='sales:view',
            name='Ver Ventas',
            module='sales',
            action='view'
        )

    @pytest.fixture
    def sales_create_permission(self, db):
        """Create sales create permission."""
        return Permission.objects.create(
            code='sales:create',
            name='Crear Ventas',
            module='sales',
            action='create'
        )

    @pytest.fixture
    def sales_void_permission(self, db):
        """Create sales void permission."""
        return Permission.objects.create(
            code='sales:void',
            name='Anular Ventas',
            module='sales',
            action='void'
        )

    @pytest.fixture
    def admin_with_sales_permissions(
        self, db, admin_user, admin_role,
        sales_view_permission, sales_create_permission, sales_void_permission
    ):
        """Admin user with sales permissions."""
        admin_role.permissions.add(
            sales_view_permission,
            sales_create_permission,
            sales_void_permission
        )
        return admin_user

    @pytest.fixture
    def cashier_with_sales_permissions(
        self, db, cashier_user, cashier_role,
        sales_view_permission, sales_create_permission
    ):
        """Cashier user with sales permissions."""
        cashier_role.permissions.add(sales_view_permission, sales_create_permission)
        return cashier_user

    def test_list_sales_authenticated(
        self, authenticated_admin_client, admin_with_sales_permissions,
        branch, cashier_user, product, branch_stock
    ):
        """Test listing sales requires authentication."""
        # Create a sale first
        items = [{'product_id': product.id, 'quantity': 1}]
        SaleService.create_sale(
            branch=branch,
            cashier=cashier_user,
            items=items,
            payment_method='cash',
            amount_tendered=Decimal('200.00'),
        )

        url = '/api/v1/sales/'
        response = authenticated_admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data or isinstance(response.data, list)

    def test_list_sales_unauthenticated(self, api_client):
        """Test listing sales without auth fails."""
        url = '/api/v1/sales/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_sale_success(
        self, authenticated_cashier_client, cashier_with_sales_permissions,
        branch, product, branch_stock
    ):
        """Test creating a sale via API."""
        url = '/api/v1/sales/'
        data = {
            'branch_id': branch.id,
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ],
            'payment_method': 'cash',
            'amount_tendered': '300.00',
        }

        response = authenticated_cashier_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'sale_number' in response.data
        assert response.data['payment_method'] == 'cash'

    def test_create_sale_with_customer(
        self, authenticated_cashier_client, cashier_with_sales_permissions,
        branch, product, branch_stock
    ):
        """Test creating a sale with customer info."""
        url = '/api/v1/sales/'
        data = {
            'branch_id': branch.id,
            'items': [
                {'product_id': product.id, 'quantity': 1}
            ],
            'payment_method': 'card',
            'customer_name': 'Test Customer',
            'customer_phone': '555-0000',
            'customer_email': 'customer@test.com',
            'payment_reference': '****9999',
        }

        response = authenticated_cashier_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['customer_name'] == 'Test Customer'

    def test_retrieve_sale(
        self, authenticated_admin_client, admin_with_sales_permissions,
        branch, cashier_user, product, branch_stock
    ):
        """Test retrieving a single sale."""
        # Create a sale first
        items = [{'product_id': product.id, 'quantity': 1}]
        sale = SaleService.create_sale(
            branch=branch,
            cashier=cashier_user,
            items=items,
            payment_method='cash',
            amount_tendered=Decimal('200.00'),
        )

        url = f'/api/v1/sales/{sale.pk}/'
        response = authenticated_admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == sale.pk
        assert response.data['sale_number'] == sale.sale_number

    def test_void_sale(
        self, authenticated_admin_client, admin_with_sales_permissions,
        branch, cashier_user, product, branch_stock
    ):
        """Test voiding a sale via API."""
        items = [{'product_id': product.id, 'quantity': 1}]
        sale = SaleService.create_sale(
            branch=branch,
            cashier=cashier_user,
            items=items,
            payment_method='cash',
            amount_tendered=Decimal('200.00'),
        )

        url = f'/api/v1/sales/{sale.pk}/void/'
        data = {'reason': 'Customer changed mind'}

        response = authenticated_admin_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'voided'

    def test_get_receipt_json(
        self, authenticated_admin_client, admin_with_sales_permissions,
        branch, cashier_user, product, branch_stock
    ):
        """Test getting receipt data as JSON."""
        items = [{'product_id': product.id, 'quantity': 1}]
        sale = SaleService.create_sale(
            branch=branch,
            cashier=cashier_user,
            items=items,
            payment_method='cash',
            amount_tendered=Decimal('200.00'),
        )

        url = f'/api/v1/sales/{sale.pk}/receipt/'
        response = authenticated_admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'sale_number' in response.data
        assert 'branch' in response.data
        assert 'items' in response.data
        assert 'total' in response.data

    def test_get_receipt_pdf(
        self, authenticated_admin_client, admin_with_sales_permissions,
        branch, cashier_user, product, branch_stock
    ):
        """Test downloading receipt as PDF."""
        items = [{'product_id': product.id, 'quantity': 1}]
        sale = SaleService.create_sale(
            branch=branch,
            cashier=cashier_user,
            items=items,
            payment_method='cash',
            amount_tendered=Decimal('200.00'),
        )

        url = f'/api/v1/sales/{sale.pk}/receipt_pdf/'
        response = authenticated_admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'application/pdf'
        assert 'recibo_' in response['Content-Disposition']
        assert response.content[:4] == b'%PDF'

    def test_daily_summary(
        self, authenticated_admin_client, admin_with_sales_permissions,
        branch, cashier_user, product, branch_stock
    ):
        """Test getting daily summary."""
        # Create a sale
        items = [{'product_id': product.id, 'quantity': 1}]
        SaleService.create_sale(
            branch=branch,
            cashier=cashier_user,
            items=items,
            payment_method='cash',
            amount_tendered=Decimal('200.00'),
        )

        url = f'/api/v1/sales/daily_summary/?branch={branch.id}'
        response = authenticated_admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'sale_count' in response.data  # DailySummarySerializer uses sale_count
        assert 'total_sales' in response.data

    def test_top_products(
        self, authenticated_admin_client, admin_with_sales_permissions,
        branch, cashier_user, product, branch_stock
    ):
        """Test getting top products."""
        # Create sales
        items = [{'product_id': product.id, 'quantity': 3}]
        SaleService.create_sale(
            branch=branch,
            cashier=cashier_user,
            items=items,
            payment_method='cash',
            amount_tendered=Decimal('400.00'),
        )

        url = f'/api/v1/sales/top_products/?branch={branch.id}'
        response = authenticated_admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_filter_sales_by_status(
        self, authenticated_admin_client, admin_with_sales_permissions,
        branch, cashier_user, product, branch_stock
    ):
        """Test filtering sales by status."""
        # Create sales
        items = [{'product_id': product.id, 'quantity': 1}]
        sale = SaleService.create_sale(
            branch=branch,
            cashier=cashier_user,
            items=items,
            payment_method='cash',
            amount_tendered=Decimal('200.00'),
        )
        SaleService.void_sale(sale=sale, user=cashier_user, reason='Test')

        # Filter voided
        url = '/api/v1/sales/?status=voided'
        response = authenticated_admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_filter_sales_by_payment_method(
        self, authenticated_admin_client, admin_with_sales_permissions,
        branch, cashier_user, product, branch_stock
    ):
        """Test filtering sales by payment method."""
        items = [{'product_id': product.id, 'quantity': 1}]
        SaleService.create_sale(
            branch=branch,
            cashier=cashier_user,
            items=items,
            payment_method='card',
        )

        url = '/api/v1/sales/?payment_method=card'
        response = authenticated_admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestCashRegisterViewSet:
    """Tests for Cash Register API endpoints."""

    @pytest.fixture
    def register_permission(self, db):
        """Create register permission."""
        return Permission.objects.create(
            code='sales:register',
            name='Gestión de Caja',
            module='sales',
            action='register'
        )

    @pytest.fixture
    def cashier_with_register_permission(self, db, cashier_user, cashier_role, register_permission):
        """Cashier user with register permission."""
        cashier_role.permissions.add(register_permission)
        return cashier_user

    @pytest.fixture
    def admin_with_register_permission(self, db, admin_user, admin_role, register_permission):
        """Admin user with register permission."""
        admin_role.permissions.add(register_permission)
        return admin_user

    def test_open_register(
        self, authenticated_cashier_client, cashier_with_register_permission, branch
    ):
        """Test opening a cash register."""
        url = '/api/v1/registers/open/'
        data = {
            'branch_id': branch.id,
            'opening_amount': '1000.00',
        }

        response = authenticated_cashier_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['opening_amount'] == '1000.00'
        assert response.data['is_closed'] is False

    def test_close_register(
        self, authenticated_cashier_client, cashier_with_register_permission, cashier_user, branch
    ):
        """Test closing a cash register."""
        # First open a register
        from apps.sales.services import CashRegisterService
        register = CashRegisterService.open_register(
            branch=branch,
            user=cashier_user,
            opening_amount=Decimal('1000.00')
        )

        url = f'/api/v1/registers/{register.pk}/close/'
        data = {
            'closing_amount': '2500.00',
            'notes': 'Normal closing',
        }

        response = authenticated_cashier_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_closed'] is True
        assert response.data['closing_amount'] == '2500.00'

    def test_get_current_register(
        self, authenticated_cashier_client, cashier_with_register_permission, cashier_user, branch
    ):
        """Test getting current open register."""
        # Open a register first
        from apps.sales.services import CashRegisterService
        CashRegisterService.open_register(
            branch=branch,
            user=cashier_user,
            opening_amount=Decimal('1000.00')
        )

        url = f'/api/v1/registers/current/?branch={branch.id}'
        response = authenticated_cashier_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_closed'] is False

    def test_get_current_register_none(
        self, authenticated_cashier_client, cashier_with_register_permission, branch
    ):
        """Test getting current register when none is open."""
        url = f'/api/v1/registers/current/?branch={branch.id}'
        response = authenticated_cashier_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_registers(
        self, authenticated_admin_client, admin_with_register_permission, cashier_user, branch
    ):
        """Test listing cash registers."""
        from apps.sales.services import CashRegisterService
        CashRegisterService.open_register(
            branch=branch,
            user=cashier_user,
            opening_amount=Decimal('1000.00')
        )

        url = '/api/v1/registers/'
        response = authenticated_admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
