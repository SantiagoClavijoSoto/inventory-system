"""
Tests for Sales models.
"""
import pytest
from decimal import Decimal
from django.utils import timezone

from apps.sales.models import Sale, SaleItem, DailyCashRegister


@pytest.mark.django_db
class TestSaleModel:
    """Tests for the Sale model."""

    def test_sale_creation(self, branch, cashier_user):
        """Test creating a sale."""
        sale = Sale.objects.create(
            sale_number='TST-20241211-0001',
            branch=branch,
            cashier=cashier_user,
            subtotal=Decimal('100.00'),
            tax_amount=Decimal('16.00'),
            total=Decimal('116.00'),
            payment_method='cash',
            amount_tendered=Decimal('150.00'),
            change_amount=Decimal('34.00'),
        )
        assert sale.pk is not None
        assert sale.status == 'completed'
        assert str(sale) == f"Venta #{sale.sale_number} - ${sale.total}"

    def test_sale_number_generation(self, branch):
        """Test automatic sale number generation."""
        sale_number = Sale.generate_sale_number(branch.code)

        today = timezone.now().date()
        expected_prefix = f"{branch.code}-{today.strftime('%Y%m%d')}"

        assert sale_number.startswith(expected_prefix)
        assert sale_number.endswith('-0001')

    def test_sequential_sale_numbers(self, branch, cashier_user):
        """Test that sale numbers increment correctly."""
        # Create first sale
        sale1_number = Sale.generate_sale_number(branch.code)
        Sale.objects.create(
            sale_number=sale1_number,
            branch=branch,
            cashier=cashier_user,
            total=Decimal('100.00'),
        )

        # Generate second sale number
        sale2_number = Sale.generate_sale_number(branch.code)

        assert sale2_number.endswith('-0002')

    def test_calculate_totals(self, branch, cashier_user, product):
        """Test sale totals calculation."""
        sale = Sale.objects.create(
            sale_number='TST-20241211-0001',
            branch=branch,
            cashier=cashier_user,
        )

        # Add an item
        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=2,
            unit_price=Decimal('100.00'),
            cost_price=Decimal('50.00'),
            product_name=product.name,
            product_sku=product.sku,
        )

        sale.calculate_totals()

        assert sale.subtotal == Decimal('200.00')
        assert sale.tax_amount == Decimal('32.00')  # 16% of 200
        assert sale.total == Decimal('232.00')

    def test_calculate_totals_with_discount(self, branch, cashier_user, product):
        """Test sale totals calculation with discount."""
        sale = Sale.objects.create(
            sale_number='TST-20241211-0001',
            branch=branch,
            cashier=cashier_user,
            discount_percent=Decimal('10.00'),  # 10% discount
        )

        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=1,
            unit_price=Decimal('100.00'),
            cost_price=Decimal('50.00'),
            product_name=product.name,
            product_sku=product.sku,
        )

        sale.calculate_totals()

        assert sale.subtotal == Decimal('100.00')
        assert sale.discount_amount == Decimal('10.00')  # 10% of 100
        # Tax on (100 - 10) = 90 * 0.16 = 14.40
        assert sale.tax_amount == Decimal('14.40')
        # Total = 90 + 14.40 = 104.40
        assert sale.total == Decimal('104.40')

    def test_is_voided_property(self, branch, cashier_user):
        """Test is_voided property."""
        sale = Sale.objects.create(
            sale_number='TST-20241211-0001',
            branch=branch,
            cashier=cashier_user,
            total=Decimal('100.00'),
        )

        assert not sale.is_voided

        sale.status = 'voided'
        sale.save()

        assert sale.is_voided


@pytest.mark.django_db
class TestSaleItemModel:
    """Tests for the SaleItem model."""

    def test_sale_item_creation(self, branch, cashier_user, product):
        """Test creating a sale item."""
        sale = Sale.objects.create(
            sale_number='TST-20241211-0001',
            branch=branch,
            cashier=cashier_user,
        )

        item = SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=3,
            unit_price=Decimal('100.00'),
            cost_price=Decimal('50.00'),
            product_name=product.name,
            product_sku=product.sku,
        )

        assert item.pk is not None
        # Subtotal = 3 * 100 = 300
        assert item.subtotal == Decimal('300.00')

    def test_sale_item_profit(self, branch, cashier_user, product):
        """Test profit calculation for sale item."""
        sale = Sale.objects.create(
            sale_number='TST-20241211-0001',
            branch=branch,
            cashier=cashier_user,
        )

        item = SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=2,
            unit_price=Decimal('100.00'),
            cost_price=Decimal('50.00'),
            product_name=product.name,
            product_sku=product.sku,
        )

        # Profit = (100 - 50) * 2 = 100
        assert item.profit == Decimal('100.00')

    def test_sale_item_profit_margin(self, branch, cashier_user, product):
        """Test profit margin calculation."""
        sale = Sale.objects.create(
            sale_number='TST-20241211-0001',
            branch=branch,
            cashier=cashier_user,
        )

        item = SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=1,
            unit_price=Decimal('100.00'),
            cost_price=Decimal('50.00'),
            product_name=product.name,
            product_sku=product.sku,
        )

        # Margin = ((100 - 50) / 50) * 100 = 100%
        assert item.profit_margin == Decimal('100')

    def test_sale_item_with_discount(self, branch, cashier_user, product):
        """Test sale item with item-level discount."""
        sale = Sale.objects.create(
            sale_number='TST-20241211-0001',
            branch=branch,
            cashier=cashier_user,
        )

        item = SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=2,
            unit_price=Decimal('100.00'),
            cost_price=Decimal('50.00'),
            discount_amount=Decimal('20.00'),
            product_name=product.name,
            product_sku=product.sku,
        )

        # Subtotal = (100 * 2) - 20 = 180
        assert item.subtotal == Decimal('180.00')


@pytest.mark.django_db
class TestDailyCashRegisterModel:
    """Tests for the DailyCashRegister model."""

    def test_cash_register_creation(self, branch, cashier_user):
        """Test creating a cash register."""
        register = DailyCashRegister.objects.create(
            branch=branch,
            date=timezone.now().date(),
            opening_amount=Decimal('1000.00'),
            opened_by=cashier_user,
            opened_at=timezone.now(),
        )

        assert register.pk is not None
        assert not register.is_closed
        assert "Abierta" in str(register)

    def test_cash_register_closure(self, branch, cashier_user):
        """Test closing a cash register."""
        register = DailyCashRegister.objects.create(
            branch=branch,
            date=timezone.now().date(),
            opening_amount=Decimal('1000.00'),
            opened_by=cashier_user,
            opened_at=timezone.now(),
        )

        register.closing_amount = Decimal('2500.00')
        register.closed_by = cashier_user
        register.closed_at = timezone.now()
        register.is_closed = True
        register.save()

        assert register.is_closed
        assert "Cerrada" in str(register)

    def test_cash_register_unique_per_day(self, branch, cashier_user):
        """Test that only one register per branch per day is allowed."""
        today = timezone.now().date()

        DailyCashRegister.objects.create(
            branch=branch,
            date=today,
            opening_amount=Decimal('1000.00'),
            opened_by=cashier_user,
            opened_at=timezone.now(),
        )

        with pytest.raises(Exception):  # IntegrityError
            DailyCashRegister.objects.create(
                branch=branch,
                date=today,
                opening_amount=Decimal('500.00'),
                opened_by=cashier_user,
                opened_at=timezone.now(),
            )
