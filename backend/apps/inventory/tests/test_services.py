"""
Tests for Inventory services - StockService.
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError

from apps.inventory.models import Category, Product, BranchStock, StockMovement
from apps.inventory.services import StockService


class TestStockServiceAdjustStock:
    """Tests for StockService.adjust_stock method."""

    @pytest.fixture
    def product(self, db):
        """Create a test product."""
        category = Category.objects.create(name='Service Test Category')
        return Product.objects.create(
            name='Adjustment Product',
            sku='ADJ001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00'),
            min_stock=5
        )

    def test_adjust_stock_creates_branch_stock(self, db, product, branch, admin_user):
        """Test that adjust_stock creates BranchStock if not exists."""
        assert not BranchStock.objects.filter(product=product, branch=branch).exists()

        StockService.adjust_stock(
            product=product,
            branch_id=branch.id,
            quantity_change=50,
            movement_type='purchase',
            user=admin_user
        )

        stock = BranchStock.objects.get(product=product, branch=branch)
        assert stock.quantity == 50

    def test_adjust_stock_increases_quantity(self, db, product, branch, admin_user):
        """Test increasing stock quantity."""
        BranchStock.objects.create(product=product, branch=branch, quantity=100)

        movement = StockService.adjust_stock(
            product=product,
            branch_id=branch.id,
            quantity_change=50,
            movement_type='purchase',
            user=admin_user
        )

        stock = BranchStock.objects.get(product=product, branch=branch)
        assert stock.quantity == 150
        assert movement.previous_quantity == 100
        assert movement.new_quantity == 150

    def test_adjust_stock_decreases_quantity(self, db, product, branch, admin_user):
        """Test decreasing stock quantity."""
        BranchStock.objects.create(product=product, branch=branch, quantity=100)

        movement = StockService.adjust_stock(
            product=product,
            branch_id=branch.id,
            quantity_change=-30,
            movement_type='sale',
            user=admin_user
        )

        stock = BranchStock.objects.get(product=product, branch=branch)
        assert stock.quantity == 70
        assert movement.quantity == 30  # Stored as positive

    def test_adjust_stock_creates_movement_record(self, db, product, branch, admin_user):
        """Test that a StockMovement is created."""
        BranchStock.objects.create(product=product, branch=branch, quantity=100)

        movement = StockService.adjust_stock(
            product=product,
            branch_id=branch.id,
            quantity_change=25,
            movement_type='purchase',
            user=admin_user,
            reference='PO-001',
            notes='Test purchase'
        )

        assert movement.product == product
        assert movement.branch == branch
        assert movement.movement_type == 'purchase'
        assert movement.reference == 'PO-001'
        assert movement.notes == 'Test purchase'
        assert movement.created_by == admin_user

    def test_adjust_stock_prevents_negative(self, db, product, branch, admin_user):
        """Test that stock cannot go negative."""
        BranchStock.objects.create(product=product, branch=branch, quantity=10)

        with pytest.raises(ValueError, match='Stock insuficiente'):
            StockService.adjust_stock(
                product=product,
                branch_id=branch.id,
                quantity_change=-20,  # More than available
                movement_type='sale',
                user=admin_user
            )


class TestStockServiceTransferStock:
    """Tests for StockService.transfer_stock method."""

    @pytest.fixture
    def product(self, db):
        """Create a test product."""
        category = Category.objects.create(name='Transfer Test Category')
        return Product.objects.create(
            name='Transfer Product',
            sku='TRF001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )

    def test_transfer_stock_success(self, db, product, branch, second_branch, admin_user):
        """Test successful stock transfer between branches."""
        BranchStock.objects.create(product=product, branch=branch, quantity=100)

        out_movement, in_movement = StockService.transfer_stock(
            product=product,
            from_branch_id=branch.id,
            to_branch_id=second_branch.id,
            quantity=30,
            user=admin_user
        )

        # Check source branch
        from_stock = BranchStock.objects.get(product=product, branch=branch)
        assert from_stock.quantity == 70

        # Check destination branch
        to_stock = BranchStock.objects.get(product=product, branch=second_branch)
        assert to_stock.quantity == 30

        # Check movements
        assert out_movement.movement_type == 'transfer_out'
        assert out_movement.quantity == 30
        assert out_movement.related_branch == second_branch

        assert in_movement.movement_type == 'transfer_in'
        assert in_movement.quantity == 30
        assert in_movement.related_branch == branch

    def test_transfer_stock_insufficient(self, db, product, branch, second_branch, admin_user):
        """Test transfer fails with insufficient stock."""
        BranchStock.objects.create(product=product, branch=branch, quantity=20)

        with pytest.raises(ValueError, match='Stock insuficiente'):
            StockService.transfer_stock(
                product=product,
                from_branch_id=branch.id,
                to_branch_id=second_branch.id,
                quantity=50,  # More than available
                user=admin_user
            )

    def test_transfer_creates_destination_stock(self, db, product, branch, second_branch, admin_user):
        """Test transfer creates BranchStock in destination if not exists."""
        BranchStock.objects.create(product=product, branch=branch, quantity=100)
        assert not BranchStock.objects.filter(product=product, branch=second_branch).exists()

        StockService.transfer_stock(
            product=product,
            from_branch_id=branch.id,
            to_branch_id=second_branch.id,
            quantity=25,
            user=admin_user
        )

        to_stock = BranchStock.objects.get(product=product, branch=second_branch)
        assert to_stock.quantity == 25


class TestStockServiceProcessSale:
    """Tests for StockService.process_sale method."""

    @pytest.fixture
    def product(self, db):
        """Create a test product."""
        category = Category.objects.create(name='Sale Test Category')
        return Product.objects.create(
            name='Sale Product',
            sku='SAL001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )

    def test_process_sale_success(self, db, product, branch, admin_user):
        """Test successful sale processing."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50)

        movement = StockService.process_sale(
            product=product,
            branch_id=branch.id,
            quantity=5,
            user=admin_user,
            sale_reference='SALE-001'
        )

        stock = BranchStock.objects.get(product=product, branch=branch)
        assert stock.quantity == 45

        assert movement.movement_type == 'sale'
        assert movement.quantity == 5
        assert movement.reference == 'SALE-001'

    def test_process_sale_insufficient_stock(self, db, product, branch, admin_user):
        """Test sale fails with insufficient stock."""
        BranchStock.objects.create(product=product, branch=branch, quantity=3)

        with pytest.raises(ValueError, match='Stock insuficiente'):
            StockService.process_sale(
                product=product,
                branch_id=branch.id,
                quantity=10,
                user=admin_user
            )


class TestStockServiceProcessPurchase:
    """Tests for StockService.process_purchase method."""

    @pytest.fixture
    def product(self, db):
        """Create a test product."""
        category = Category.objects.create(name='Purchase Test Category')
        return Product.objects.create(
            name='Purchase Product',
            sku='PUR001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )

    def test_process_purchase_success(self, db, product, branch, admin_user):
        """Test successful purchase processing."""
        movement = StockService.process_purchase(
            product=product,
            branch_id=branch.id,
            quantity=100,
            user=admin_user,
            purchase_reference='PO-001'
        )

        stock = BranchStock.objects.get(product=product, branch=branch)
        assert stock.quantity == 100

        assert movement.movement_type == 'purchase'
        assert movement.quantity == 100
        assert movement.reference == 'PO-001'

    def test_process_purchase_adds_to_existing(self, db, product, branch, admin_user):
        """Test purchase adds to existing stock."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50)

        StockService.process_purchase(
            product=product,
            branch_id=branch.id,
            quantity=30,
            user=admin_user
        )

        stock = BranchStock.objects.get(product=product, branch=branch)
        assert stock.quantity == 80


class TestStockServiceManualAdjustment:
    """Tests for StockService.manual_adjustment method."""

    @pytest.fixture
    def product(self, db):
        """Create a test product."""
        category = Category.objects.create(name='Manual Adjustment Category')
        return Product.objects.create(
            name='Manual Adjustment Product',
            sku='MAN001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )

    def test_manual_adjustment_add(self, db, product, branch, admin_user):
        """Test manual adjustment with add type."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50)

        movement = StockService.manual_adjustment(
            product=product,
            branch_id=branch.id,
            adjustment_type='add',
            quantity=20,
            user=admin_user,
            reason='Found extra inventory'
        )

        stock = BranchStock.objects.get(product=product, branch=branch)
        assert stock.quantity == 70
        assert movement.movement_type == 'adjustment'

    def test_manual_adjustment_subtract(self, db, product, branch, admin_user):
        """Test manual adjustment with subtract type."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50)

        movement = StockService.manual_adjustment(
            product=product,
            branch_id=branch.id,
            adjustment_type='subtract',
            quantity=15,
            user=admin_user,
            reason='Damaged inventory'
        )

        stock = BranchStock.objects.get(product=product, branch=branch)
        assert stock.quantity == 35

    def test_manual_adjustment_set(self, db, product, branch, admin_user):
        """Test manual adjustment with set type."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50)

        movement = StockService.manual_adjustment(
            product=product,
            branch_id=branch.id,
            adjustment_type='set',
            quantity=75,
            user=admin_user,
            reason='Physical inventory count'
        )

        stock = BranchStock.objects.get(product=product, branch=branch)
        assert stock.quantity == 75

    def test_manual_adjustment_set_lower(self, db, product, branch, admin_user):
        """Test manual adjustment set to lower value."""
        BranchStock.objects.create(product=product, branch=branch, quantity=100)

        StockService.manual_adjustment(
            product=product,
            branch_id=branch.id,
            adjustment_type='set',
            quantity=25,
            user=admin_user,
            reason='Inventory reconciliation'
        )

        stock = BranchStock.objects.get(product=product, branch=branch)
        assert stock.quantity == 25


class TestStockServiceReservations:
    """Tests for stock reservation methods."""

    @pytest.fixture
    def product(self, db):
        """Create a test product."""
        category = Category.objects.create(name='Reservation Test Category')
        return Product.objects.create(
            name='Reservation Product',
            sku='RES001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )

    def test_reserve_stock_success(self, db, product, branch, admin_user):
        """Test successful stock reservation."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50, reserved_quantity=0)

        StockService.reserve_stock(
            product=product,
            branch_id=branch.id,
            quantity=10
        )

        stock = BranchStock.objects.get(product=product, branch=branch)
        assert stock.reserved_quantity == 10
        assert stock.available_quantity == 40

    def test_reserve_stock_insufficient(self, db, product, branch, admin_user):
        """Test reservation fails with insufficient available stock."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50, reserved_quantity=45)

        with pytest.raises(ValueError, match='Stock disponible insuficiente'):
            StockService.reserve_stock(
                product=product,
                branch_id=branch.id,
                quantity=10  # Only 5 available
            )

    def test_release_reservation(self, db, product, branch, admin_user):
        """Test releasing reserved stock."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50, reserved_quantity=20)

        StockService.release_reservation(
            product=product,
            branch_id=branch.id,
            quantity=15
        )

        stock = BranchStock.objects.get(product=product, branch=branch)
        assert stock.reserved_quantity == 5
        assert stock.available_quantity == 45

    def test_release_more_than_reserved(self, db, product, branch, admin_user):
        """Test releasing more than reserved sets to zero."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50, reserved_quantity=10)

        StockService.release_reservation(
            product=product,
            branch_id=branch.id,
            quantity=50  # More than reserved
        )

        stock = BranchStock.objects.get(product=product, branch=branch)
        assert stock.reserved_quantity == 0


class TestStockServiceReturn:
    """Tests for StockService.record_return_customer method."""

    @pytest.fixture
    def product(self, db):
        """Create a test product."""
        category = Category.objects.create(name='Return Test Category')
        return Product.objects.create(
            name='Return Product',
            sku='RET001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )

    def test_record_return_customer(self, db, product, branch, admin_user):
        """Test recording a customer return."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50)

        movement = StockService.record_return_customer(
            product=product,
            branch_id=branch.id,
            quantity=5,
            user=admin_user,
            return_reference='RET-001'
        )

        stock = BranchStock.objects.get(product=product, branch=branch)
        assert stock.quantity == 55

        assert movement.movement_type == 'return'
        assert movement.quantity == 5
        assert movement.reference == 'RET-001'
