"""
Tests for Suppliers models.
"""
import pytest
from decimal import Decimal
from django.db import IntegrityError
from datetime import date

from apps.suppliers.models import Supplier, PurchaseOrder, PurchaseOrderItem
from apps.inventory.models import Category, Product


class TestSupplierModel:
    """Tests for the Supplier model."""

    def test_supplier_creation(self, db):
        """Test creating a supplier with minimal fields."""
        supplier = Supplier.objects.create(
            name='Test Supplier',
            code='SUP001'
        )
        assert supplier.id is not None
        assert supplier.name == 'Test Supplier'
        assert supplier.code == 'SUP001'
        assert supplier.is_active is True

    def test_supplier_str(self, db):
        """Test supplier string representation."""
        supplier = Supplier.objects.create(
            name='Main Supplier',
            code='MAIN'
        )
        assert str(supplier) == 'MAIN - Main Supplier'

    def test_supplier_code_unique(self, db):
        """Test that supplier code must be unique."""
        Supplier.objects.create(name='First', code='UNIQUE')
        with pytest.raises(IntegrityError):
            Supplier.objects.create(name='Second', code='UNIQUE')

    def test_supplier_full_address(self, db):
        """Test full_address property."""
        supplier = Supplier.objects.create(
            name='Full Address Supplier',
            code='FAS',
            address='123 Main St',
            city='Mexico City',
            state='CDMX',
            postal_code='06600',
            country='México'
        )
        expected = '123 Main St, Mexico City, CDMX, 06600, México'
        assert supplier.full_address == expected

    def test_supplier_full_address_partial(self, db):
        """Test full_address with some fields missing."""
        supplier = Supplier.objects.create(
            name='Partial',
            code='PAR',
            city='Guadalajara',
            state='Jalisco'
        )
        expected = 'Guadalajara, Jalisco, México'
        assert supplier.full_address == expected

    def test_supplier_default_country(self, db):
        """Test that default country is México."""
        supplier = Supplier.objects.create(name='Default Country', code='DEF')
        assert supplier.country == 'México'

    def test_supplier_default_payment_terms(self, db):
        """Test that default payment terms is 30 days."""
        supplier = Supplier.objects.create(name='Default Terms', code='DFT')
        assert supplier.payment_terms == 30

    def test_supplier_default_credit_limit(self, db):
        """Test that default credit limit is 0."""
        supplier = Supplier.objects.create(name='Default Credit', code='DFC')
        assert supplier.credit_limit == Decimal('0.00')

    def test_supplier_with_contact_info(self, db):
        """Test supplier with contact information."""
        supplier = Supplier.objects.create(
            name='Contact Supplier',
            code='CNT',
            contact_name='John Doe',
            email='john@supplier.com',
            phone='555-1234',
            mobile='555-5678'
        )
        assert supplier.contact_name == 'John Doe'
        assert supplier.email == 'john@supplier.com'
        assert supplier.phone == '555-1234'
        assert supplier.mobile == '555-5678'

    def test_supplier_with_business_info(self, db):
        """Test supplier with business information."""
        supplier = Supplier.objects.create(
            name='Business Supplier',
            code='BUS',
            tax_id='RFC123456789',
            website='https://supplier.com',
            notes='Important supplier'
        )
        assert supplier.tax_id == 'RFC123456789'
        assert supplier.website == 'https://supplier.com'
        assert supplier.notes == 'Important supplier'

    def test_supplier_soft_delete(self, db):
        """Test that deleting a supplier soft deletes it."""
        supplier = Supplier.objects.create(name='To Delete', code='DEL')
        supplier.delete()

        assert Supplier.objects.filter(code='DEL').exists()
        supplier.refresh_from_db()
        assert supplier.is_deleted is True


class TestPurchaseOrderModel:
    """Tests for the PurchaseOrder model."""

    @pytest.fixture
    def supplier(self, db):
        """Create a test supplier."""
        return Supplier.objects.create(name='Test Supplier', code='TST')

    def test_purchase_order_creation(self, db, supplier, branch, admin_user):
        """Test creating a purchase order."""
        po = PurchaseOrder.objects.create(
            order_number='PO-001',
            supplier=supplier,
            branch=branch,
            created_by=admin_user
        )
        assert po.id is not None
        assert po.order_number == 'PO-001'
        assert po.status == 'draft'

    def test_purchase_order_str(self, db, supplier, branch, admin_user):
        """Test purchase order string representation."""
        po = PurchaseOrder.objects.create(
            order_number='PO-002',
            supplier=supplier,
            branch=branch,
            created_by=admin_user
        )
        assert 'PO-002' in str(po)
        assert supplier.name in str(po)

    def test_purchase_order_number_unique(self, db, supplier, branch, admin_user):
        """Test that order number must be unique."""
        PurchaseOrder.objects.create(
            order_number='UNIQUE-PO',
            supplier=supplier,
            branch=branch,
            created_by=admin_user
        )
        with pytest.raises(IntegrityError):
            PurchaseOrder.objects.create(
                order_number='UNIQUE-PO',
                supplier=supplier,
                branch=branch,
                created_by=admin_user
            )

    def test_purchase_order_status_choices(self, db, supplier, branch, admin_user):
        """Test different status values."""
        statuses = ['draft', 'pending', 'approved', 'ordered', 'partial', 'received', 'cancelled']

        for i, status in enumerate(statuses):
            po = PurchaseOrder.objects.create(
                order_number=f'PO-STATUS-{i}',
                supplier=supplier,
                branch=branch,
                status=status,
                created_by=admin_user
            )
            assert po.status == status

    def test_purchase_order_default_totals(self, db, supplier, branch, admin_user):
        """Test default totals are zero."""
        po = PurchaseOrder.objects.create(
            order_number='PO-TOTALS',
            supplier=supplier,
            branch=branch,
            created_by=admin_user
        )
        assert po.subtotal == Decimal('0.00')
        assert po.tax == Decimal('0.00')
        assert po.total == Decimal('0.00')

    def test_purchase_order_with_dates(self, db, supplier, branch, admin_user):
        """Test purchase order with dates."""
        po = PurchaseOrder.objects.create(
            order_number='PO-DATES',
            supplier=supplier,
            branch=branch,
            order_date=date(2025, 1, 15),
            expected_date=date(2025, 1, 25),
            created_by=admin_user
        )
        assert po.order_date == date(2025, 1, 15)
        assert po.expected_date == date(2025, 1, 25)

    def test_purchase_order_audit_fields(self, db, supplier, branch, admin_user, cashier_user):
        """Test purchase order audit fields."""
        po = PurchaseOrder.objects.create(
            order_number='PO-AUDIT',
            supplier=supplier,
            branch=branch,
            created_by=admin_user,
            approved_by=cashier_user
        )
        assert po.created_by == admin_user
        assert po.approved_by == cashier_user
        assert po.received_by is None


class TestPurchaseOrderItemModel:
    """Tests for the PurchaseOrderItem model."""

    @pytest.fixture
    def supplier(self, db):
        """Create a test supplier."""
        return Supplier.objects.create(name='Test Supplier', code='TST')

    @pytest.fixture
    def category(self, db):
        """Create a test category."""
        return Category.objects.create(name='PO Item Category')

    @pytest.fixture
    def product(self, db, category):
        """Create a test product."""
        return Product.objects.create(
            name='PO Test Product',
            sku='POI001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )

    @pytest.fixture
    def purchase_order(self, db, supplier, branch, admin_user):
        """Create a test purchase order."""
        return PurchaseOrder.objects.create(
            order_number='PO-ITEMS',
            supplier=supplier,
            branch=branch,
            created_by=admin_user
        )

    def test_purchase_order_item_creation(self, db, purchase_order, product):
        """Test creating a purchase order item."""
        item = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=product,
            quantity_ordered=100,
            unit_price=Decimal('10.00')
        )
        assert item.id is not None
        assert item.quantity_ordered == 100
        assert item.quantity_received == 0

    def test_purchase_order_item_str(self, db, purchase_order, product):
        """Test purchase order item string representation."""
        item = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=product,
            quantity_ordered=50,
            unit_price=Decimal('10.00')
        )
        assert product.name in str(item)
        assert '50' in str(item)

    def test_purchase_order_item_subtotal_calculation(self, db, purchase_order, product):
        """Test that subtotal is calculated on save."""
        item = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=product,
            quantity_ordered=10,
            unit_price=Decimal('25.00')
        )
        assert item.subtotal == Decimal('250.00')

    def test_purchase_order_item_is_fully_received_false(self, db, purchase_order, product):
        """Test is_fully_received when not all received."""
        item = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=product,
            quantity_ordered=100,
            quantity_received=50,
            unit_price=Decimal('10.00')
        )
        assert item.is_fully_received is False

    def test_purchase_order_item_is_fully_received_true(self, db, purchase_order, product):
        """Test is_fully_received when all received."""
        item = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=product,
            quantity_ordered=100,
            quantity_received=100,
            unit_price=Decimal('10.00')
        )
        assert item.is_fully_received is True

    def test_purchase_order_item_is_fully_received_over(self, db, purchase_order, product):
        """Test is_fully_received when received more than ordered."""
        item = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=product,
            quantity_ordered=100,
            quantity_received=120,
            unit_price=Decimal('10.00')
        )
        assert item.is_fully_received is True

    def test_purchase_order_item_pending_quantity(self, db, purchase_order, product):
        """Test pending_quantity property."""
        item = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=product,
            quantity_ordered=100,
            quantity_received=30,
            unit_price=Decimal('10.00')
        )
        assert item.pending_quantity == 70

    def test_purchase_order_item_pending_quantity_zero(self, db, purchase_order, product):
        """Test pending_quantity when fully received."""
        item = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=product,
            quantity_ordered=100,
            quantity_received=100,
            unit_price=Decimal('10.00')
        )
        assert item.pending_quantity == 0

    def test_purchase_order_item_pending_quantity_over_received(self, db, purchase_order, product):
        """Test pending_quantity doesn't go negative."""
        item = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=product,
            quantity_ordered=100,
            quantity_received=150,
            unit_price=Decimal('10.00')
        )
        assert item.pending_quantity == 0


class TestPurchaseOrderCalculations:
    """Tests for PurchaseOrder calculation methods."""

    @pytest.fixture
    def supplier(self, db):
        """Create a test supplier."""
        return Supplier.objects.create(name='Calc Supplier', code='CALC')

    @pytest.fixture
    def category(self, db):
        """Create a test category."""
        return Category.objects.create(name='Calc Category')

    @pytest.fixture
    def products(self, db, category):
        """Create test products."""
        return [
            Product.objects.create(
                name=f'Product {i}',
                sku=f'PROD{i}',
                category=category,
                cost_price=Decimal('10.00'),
                sale_price=Decimal('15.00')
            )
            for i in range(3)
        ]

    @pytest.fixture
    def purchase_order(self, db, supplier, branch, admin_user):
        """Create a test purchase order."""
        return PurchaseOrder.objects.create(
            order_number='PO-CALC',
            supplier=supplier,
            branch=branch,
            created_by=admin_user
        )

    def test_calculate_totals(self, db, purchase_order, products):
        """Test calculate_totals method."""
        # Add items
        PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=products[0],
            quantity_ordered=10,
            unit_price=Decimal('100.00')  # subtotal = 1000
        )
        PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=products[1],
            quantity_ordered=5,
            unit_price=Decimal('200.00')  # subtotal = 1000
        )

        purchase_order.calculate_totals()

        assert purchase_order.subtotal == Decimal('2000.00')
        assert purchase_order.tax == Decimal('320.00')  # 16% IVA
        assert purchase_order.total == Decimal('2320.00')

    def test_calculate_totals_empty_order(self, db, purchase_order):
        """Test calculate_totals with no items."""
        purchase_order.calculate_totals()

        assert purchase_order.subtotal == Decimal('0.00')
        assert purchase_order.tax == Decimal('0.00')
        assert purchase_order.total == Decimal('0.00')

    def test_calculate_totals_updates_on_item_change(self, db, purchase_order, products):
        """Test that totals update when items change."""
        item = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            product=products[0],
            quantity_ordered=10,
            unit_price=Decimal('100.00')
        )

        purchase_order.calculate_totals()
        assert purchase_order.subtotal == Decimal('1000.00')

        # Update item
        item.quantity_ordered = 20
        item.save()

        purchase_order.calculate_totals()
        assert purchase_order.subtotal == Decimal('2000.00')
