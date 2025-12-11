"""
Tests for Sales services.
"""
import pytest
from decimal import Decimal
from django.utils import timezone

from apps.sales.models import Sale, SaleItem, DailyCashRegister
from apps.sales.services import SaleService, CashRegisterService
from apps.inventory.models import BranchStock


@pytest.mark.django_db
class TestSaleService:
    """Tests for SaleService."""

    def test_create_sale_success(self, branch, cashier_user, product, branch_stock):
        """Test successful sale creation."""
        initial_stock = branch_stock.quantity

        items = [{
            'product_id': product.id,
            'quantity': 2,
        }]

        sale = SaleService.create_sale(
            branch=branch,
            cashier=cashier_user,
            items=items,
            payment_method='cash',
            amount_tendered=Decimal('300.00'),
        )

        assert sale.pk is not None
        assert sale.status == 'completed'
        assert sale.items.count() == 1

        # Verify stock was reduced
        branch_stock.refresh_from_db()
        assert branch_stock.quantity == initial_stock - 2

    def test_create_sale_insufficient_stock(self, branch, cashier_user, product, branch_stock):
        """Test sale fails with insufficient stock."""
        items = [{
            'product_id': product.id,
            'quantity': 999,  # More than available
        }]

        with pytest.raises(Exception) as exc_info:
            SaleService.create_sale(
                branch=branch,
                cashier=cashier_user,
                items=items,
                payment_method='cash',
            )

        assert 'stock' in str(exc_info.value).lower()

    def test_create_sale_with_discount_percent(
        self, branch, cashier_user, product, branch_stock
    ):
        """Test sale with percentage discount."""
        items = [{
            'product_id': product.id,
            'quantity': 1,
        }]

        sale = SaleService.create_sale(
            branch=branch,
            cashier=cashier_user,
            items=items,
            payment_method='cash',
            discount_percent=Decimal('10.00'),
            amount_tendered=Decimal('200.00'),
        )

        assert sale.discount_percent == Decimal('10.00')
        assert sale.discount_amount > 0

    def test_create_sale_with_customer_info(
        self, branch, cashier_user, product, branch_stock
    ):
        """Test sale with customer information."""
        items = [{
            'product_id': product.id,
            'quantity': 1,
        }]

        sale = SaleService.create_sale(
            branch=branch,
            cashier=cashier_user,
            items=items,
            payment_method='card',
            customer_name='Juan Pérez',
            customer_phone='555-1234',
            customer_email='juan@test.com',
            payment_reference='****1234',
        )

        assert sale.customer_name == 'Juan Pérez'
        assert sale.customer_phone == '555-1234'
        assert sale.customer_email == 'juan@test.com'
        assert sale.payment_reference == '****1234'

    def test_void_sale_success(self, branch, cashier_user, product, branch_stock):
        """Test voiding a sale."""
        initial_stock = branch_stock.quantity

        items = [{
            'product_id': product.id,
            'quantity': 2,
        }]

        sale = SaleService.create_sale(
            branch=branch,
            cashier=cashier_user,
            items=items,
            payment_method='cash',
            amount_tendered=Decimal('300.00'),
        )

        # Stock should be reduced after sale
        branch_stock.refresh_from_db()
        stock_after_sale = branch_stock.quantity

        # Void the sale
        voided_sale = SaleService.void_sale(
            sale=sale,
            user=cashier_user,
            reason='Test void'
        )

        assert voided_sale.status == 'voided'
        assert voided_sale.void_reason == 'Test void'
        assert voided_sale.voided_by == cashier_user
        assert voided_sale.voided_at is not None

        # Stock should be restored
        branch_stock.refresh_from_db()
        assert branch_stock.quantity == stock_after_sale + 2

    def test_void_already_voided_sale(self, branch, cashier_user, product, branch_stock):
        """Test that voiding an already voided sale fails."""
        items = [{
            'product_id': product.id,
            'quantity': 1,
        }]

        sale = SaleService.create_sale(
            branch=branch,
            cashier=cashier_user,
            items=items,
            payment_method='cash',
        )

        SaleService.void_sale(sale=sale, user=cashier_user, reason='First void')

        with pytest.raises(Exception) as exc_info:
            SaleService.void_sale(sale=sale, user=cashier_user, reason='Second void')

        assert 'anulada' in str(exc_info.value).lower() or 'voided' in str(exc_info.value).lower()

    def test_get_daily_summary(self, branch, cashier_user, product, branch_stock):
        """Test daily summary generation."""
        # Create some sales
        items = [{
            'product_id': product.id,
            'quantity': 1,
        }]

        SaleService.create_sale(
            branch=branch,
            cashier=cashier_user,
            items=items,
            payment_method='cash',
            amount_tendered=Decimal('200.00'),
        )

        SaleService.create_sale(
            branch=branch,
            cashier=cashier_user,
            items=items,
            payment_method='card',
        )

        summary = SaleService.get_daily_summary(branch)

        assert summary['total_sales'] >= 2
        assert summary['total_revenue'] > 0

    def test_multiple_items_sale(
        self, branch, cashier_user, product, second_product,
        branch_stock, second_branch_stock
    ):
        """Test sale with multiple different products."""
        items = [
            {'product_id': product.id, 'quantity': 1},
            {'product_id': second_product.id, 'quantity': 2},
        ]

        sale = SaleService.create_sale(
            branch=branch,
            cashier=cashier_user,
            items=items,
            payment_method='cash',
            amount_tendered=Decimal('500.00'),
        )

        assert sale.items.count() == 2
        assert sale.items_count == 2
        assert sale.total_quantity == 3  # 1 + 2


@pytest.mark.django_db
class TestCashRegisterService:
    """Tests for CashRegisterService."""

    def test_open_register_success(self, branch, cashier_user):
        """Test opening a cash register."""
        register = CashRegisterService.open_register(
            branch=branch,
            user=cashier_user,
            opening_amount=Decimal('1000.00')
        )

        assert register.pk is not None
        assert register.opening_amount == Decimal('1000.00')
        assert register.opened_by == cashier_user
        assert not register.is_closed

    def test_open_register_already_open(self, branch, cashier_user):
        """Test that opening a register when one is open fails."""
        CashRegisterService.open_register(
            branch=branch,
            user=cashier_user,
            opening_amount=Decimal('1000.00')
        )

        with pytest.raises(Exception) as exc_info:
            CashRegisterService.open_register(
                branch=branch,
                user=cashier_user,
                opening_amount=Decimal('500.00')
            )

        assert 'abierta' in str(exc_info.value).lower() or 'open' in str(exc_info.value).lower()

    def test_close_register_success(self, branch, cashier_user):
        """Test closing a cash register."""
        register = CashRegisterService.open_register(
            branch=branch,
            user=cashier_user,
            opening_amount=Decimal('1000.00')
        )

        closed_register = CashRegisterService.close_register(
            register=register,
            user=cashier_user,
            closing_amount=Decimal('2500.00'),
            notes='Cierre normal'
        )

        assert closed_register.is_closed
        assert closed_register.closing_amount == Decimal('2500.00')
        assert closed_register.closed_by == cashier_user
        assert closed_register.notes == 'Cierre normal'

    def test_close_already_closed_register(self, branch, cashier_user):
        """Test that closing an already closed register fails."""
        register = CashRegisterService.open_register(
            branch=branch,
            user=cashier_user,
            opening_amount=Decimal('1000.00')
        )

        CashRegisterService.close_register(
            register=register,
            user=cashier_user,
            closing_amount=Decimal('2500.00')
        )

        with pytest.raises(Exception) as exc_info:
            CashRegisterService.close_register(
                register=register,
                user=cashier_user,
                closing_amount=Decimal('3000.00')
            )

        assert 'cerrada' in str(exc_info.value).lower() or 'closed' in str(exc_info.value).lower()

    def test_get_current_register(self, branch, cashier_user):
        """Test getting current open register."""
        # No register yet
        assert CashRegisterService.get_current_register(branch) is None

        # Open a register
        register = CashRegisterService.open_register(
            branch=branch,
            user=cashier_user,
            opening_amount=Decimal('1000.00')
        )

        current = CashRegisterService.get_current_register(branch)
        assert current == register

        # Close it
        CashRegisterService.close_register(
            register=register,
            user=cashier_user,
            closing_amount=Decimal('1500.00')
        )

        # No current register
        assert CashRegisterService.get_current_register(branch) is None
