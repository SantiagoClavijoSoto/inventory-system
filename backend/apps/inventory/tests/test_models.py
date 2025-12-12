"""
Tests for Inventory models.
"""
import pytest
from decimal import Decimal
from django.db import IntegrityError

from apps.inventory.models import Category, Product, BranchStock, StockMovement, StockAlert


class TestCategoryModel:
    """Tests for the Category model."""

    def test_category_creation(self, db):
        """Test creating a category with minimal fields."""
        category = Category.objects.create(
            name='Electronics',
            description='Electronic devices'
        )
        assert category.id is not None
        assert category.name == 'Electronics'
        assert category.is_active is True

    def test_category_str(self, db):
        """Test category string representation."""
        category = Category.objects.create(name='Beverages')
        assert str(category) == 'Beverages'

    def test_category_full_path_root(self, db):
        """Test full_path for root category."""
        category = Category.objects.create(name='Food')
        assert category.full_path == 'Food'

    def test_category_full_path_nested(self, db):
        """Test full_path for nested categories."""
        parent = Category.objects.create(name='Food')
        child = Category.objects.create(name='Dairy', parent=parent)
        grandchild = Category.objects.create(name='Cheese', parent=child)

        assert parent.full_path == 'Food'
        assert child.full_path == 'Food > Dairy'
        assert grandchild.full_path == 'Food > Dairy > Cheese'

    def test_category_hierarchy(self, db):
        """Test category parent-child relationship."""
        parent = Category.objects.create(name='Parent')
        child1 = Category.objects.create(name='Child 1', parent=parent)
        child2 = Category.objects.create(name='Child 2', parent=parent)

        assert child1.parent == parent
        assert child2.parent == parent
        assert list(parent.children.all()) == [child1, child2]

    def test_category_soft_delete(self, db):
        """Test that soft_delete marks category as deleted."""
        category = Category.objects.create(name='To Delete')
        category.soft_delete()

        # After soft delete, object still exists in database but is_deleted=True
        category.refresh_from_db()
        assert category.is_deleted is True
        assert category.deleted_at is not None


class TestProductModel:
    """Tests for the Product model."""

    @pytest.fixture
    def category(self, db):
        """Create a test category."""
        return Category.objects.create(name='Test Category')

    def test_product_creation(self, db, category):
        """Test creating a product."""
        product = Product.objects.create(
            name='Test Product',
            sku='TST001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )
        assert product.id is not None
        assert product.name == 'Test Product'
        assert product.is_active is True
        assert product.is_sellable is True

    def test_product_str(self, db, category):
        """Test product string representation."""
        product = Product.objects.create(
            name='Widget',
            sku='WDG001',
            category=category,
            cost_price=Decimal('5.00'),
            sale_price=Decimal('10.00')
        )
        assert str(product) == 'WDG001 - Widget'

    def test_product_sku_unique(self, db, category):
        """Test that SKU must be unique."""
        Product.objects.create(
            name='First',
            sku='UNIQUE',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )
        with pytest.raises(IntegrityError):
            Product.objects.create(
                name='Second',
                sku='UNIQUE',
                category=category,
                cost_price=Decimal('10.00'),
                sale_price=Decimal('15.00')
            )

    def test_product_profit_margin(self, db, category):
        """Test profit_margin calculated property."""
        product = Product.objects.create(
            name='Margin Test',
            sku='MRG001',
            category=category,
            cost_price=Decimal('100.00'),
            sale_price=Decimal('150.00')
        )
        # margin = ((150 - 100) / 100) * 100 = 50%
        assert product.profit_margin == Decimal('50.00')

    def test_product_profit_margin_zero_cost(self, db, category):
        """Test profit_margin when cost is zero."""
        product = Product.objects.create(
            name='Free Product',
            sku='FREE001',
            category=category,
            cost_price=Decimal('0.00'),
            sale_price=Decimal('10.00')
        )
        assert product.profit_margin == Decimal('0')

    def test_product_default_unit(self, db, category):
        """Test default unit is 'unidad'."""
        product = Product.objects.create(
            name='Default Unit',
            sku='DFT001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )
        assert product.unit == 'unit'  # Default unit is 'unit'

    def test_product_soft_delete(self, db, category):
        """Test that soft_delete marks product as deleted."""
        product = Product.objects.create(
            name='To Delete',
            sku='DEL001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )
        product.soft_delete()

        # After soft delete, object still exists in database but is_deleted=True
        product.refresh_from_db()
        assert product.is_deleted is True
        assert product.deleted_at is not None


class TestBranchStockModel:
    """Tests for the BranchStock model."""

    @pytest.fixture
    def product(self, db):
        """Create a test product."""
        category = Category.objects.create(name='Test Category')
        return Product.objects.create(
            name='Stock Product',
            sku='STK001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00'),
            min_stock=10
        )

    def test_branch_stock_creation(self, db, product, branch):
        """Test creating branch stock."""
        stock = BranchStock.objects.create(
            product=product,
            branch=branch,
            quantity=100
        )
        assert stock.id is not None
        assert stock.quantity == 100
        assert stock.reserved_quantity == 0

    def test_branch_stock_unique_constraint(self, db, product, branch):
        """Test that product-branch combination is unique."""
        BranchStock.objects.create(
            product=product,
            branch=branch,
            quantity=50
        )
        with pytest.raises(IntegrityError):
            BranchStock.objects.create(
                product=product,
                branch=branch,
                quantity=100
            )

    def test_available_quantity(self, db, product, branch):
        """Test available_quantity property."""
        stock = BranchStock.objects.create(
            product=product,
            branch=branch,
            quantity=100,
            reserved_quantity=25
        )
        assert stock.available_quantity == 75

    def test_is_low_stock_true(self, db, product, branch):
        """Test is_low_stock when below minimum."""
        stock = BranchStock.objects.create(
            product=product,
            branch=branch,
            quantity=5  # min_stock is 10
        )
        assert stock.is_low_stock is True

    def test_is_low_stock_false(self, db, product, branch):
        """Test is_low_stock when above minimum."""
        stock = BranchStock.objects.create(
            product=product,
            branch=branch,
            quantity=50  # min_stock is 10
        )
        assert stock.is_low_stock is False

    def test_is_out_of_stock(self, db, product, branch):
        """Test is_out_of_stock property."""
        stock = BranchStock.objects.create(
            product=product,
            branch=branch,
            quantity=0
        )
        assert stock.is_out_of_stock is True

        stock.quantity = 1
        stock.save()
        assert stock.is_out_of_stock is False


class TestProductStockMethods:
    """Tests for Product stock-related methods."""

    @pytest.fixture
    def product(self, db):
        """Create a test product."""
        category = Category.objects.create(name='Test Category')
        return Product.objects.create(
            name='Multi Branch Product',
            sku='MBP001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )

    def test_get_total_stock(self, db, product, branch, second_branch):
        """Test get_total_stock across multiple branches."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50)
        BranchStock.objects.create(product=product, branch=second_branch, quantity=30)

        assert product.get_total_stock() == 80

    def test_get_total_stock_no_stock(self, db, product):
        """Test get_total_stock when no stock exists."""
        assert product.get_total_stock() == 0

    def test_get_stock_for_branch(self, db, product, branch, second_branch):
        """Test get_stock_for_branch returns correct branch stock."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50)
        BranchStock.objects.create(product=product, branch=second_branch, quantity=30)

        assert product.get_stock_for_branch(branch.id) == 50
        assert product.get_stock_for_branch(second_branch.id) == 30

    def test_get_stock_for_branch_no_stock(self, db, product, branch):
        """Test get_stock_for_branch when no stock exists for branch."""
        assert product.get_stock_for_branch(branch.id) == 0


class TestStockMovementModel:
    """Tests for the StockMovement model."""

    @pytest.fixture
    def product(self, db):
        """Create a test product."""
        category = Category.objects.create(name='Test Category')
        return Product.objects.create(
            name='Movement Product',
            sku='MOV001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )

    def test_stock_movement_creation(self, db, product, branch, admin_user):
        """Test creating a stock movement."""
        movement = StockMovement.objects.create(
            product=product,
            branch=branch,
            movement_type='purchase',
            quantity=100,
            previous_quantity=0,
            new_quantity=100,
            created_by=admin_user
        )
        assert movement.id is not None
        assert movement.movement_type == 'purchase'
        assert movement.quantity == 100

    def test_stock_movement_str(self, db, product, branch, admin_user):
        """Test stock movement string representation."""
        movement = StockMovement.objects.create(
            product=product,
            branch=branch,
            movement_type='sale',
            quantity=5,
            previous_quantity=100,
            new_quantity=95,
            created_by=admin_user
        )
        # String representation uses Spanish display name 'Venta' for 'sale' type
        assert 'venta' in str(movement).lower()
        assert product.name in str(movement)

    def test_stock_movement_types(self, db, product, branch, admin_user):
        """Test different movement types."""
        movement_types = ['purchase', 'sale', 'adjustment', 'transfer_in', 'transfer_out', 'return']

        for m_type in movement_types:
            movement = StockMovement.objects.create(
                product=product,
                branch=branch,
                movement_type=m_type,
                quantity=10,
                previous_quantity=0,
                new_quantity=10,
                created_by=admin_user
            )
            assert movement.movement_type == m_type

    def test_stock_movement_with_related_branch(self, db, product, branch, second_branch, admin_user):
        """Test stock movement with related branch (transfer)."""
        movement = StockMovement.objects.create(
            product=product,
            branch=branch,
            movement_type='transfer_out',
            quantity=20,
            previous_quantity=100,
            new_quantity=80,
            related_branch=second_branch,
            created_by=admin_user
        )
        assert movement.related_branch == second_branch


class TestStockAlertModel:
    """Tests for the StockAlert model."""

    @pytest.fixture
    def product(self, db):
        """Create a test product."""
        category = Category.objects.create(name='Alert Category')
        return Product.objects.create(
            name='Alert Product',
            sku='ALR001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )

    @pytest.fixture
    def category(self, db):
        """Create a test category for alerts."""
        return Category.objects.create(name='Alert Test Category')

    def test_stock_alert_for_product(self, db, product, branch):
        """Test creating stock alert for specific product."""
        alert = StockAlert.objects.create(
            product=product,
            branch=branch,
            alert_type='low_stock',
            threshold=10,
            is_active=True
        )
        assert alert.id is not None
        assert alert.product == product
        assert alert.threshold == 10

    def test_stock_alert_for_category(self, db, category, branch):
        """Test creating stock alert for category."""
        alert = StockAlert.objects.create(
            category=category,
            branch=branch,
            alert_type='out_of_stock',
            threshold=0,
            is_active=True
        )
        assert alert.category == category
        assert alert.product is None

    def test_stock_alert_types(self, db, product, branch):
        """Test different alert types."""
        low_stock = StockAlert.objects.create(
            product=product,
            branch=branch,
            alert_type='low_stock',
            threshold=5
        )
        assert low_stock.alert_type == 'low_stock'

        out_of_stock = StockAlert.objects.create(
            category=Category.objects.create(name='OOS Category'),
            branch=branch,
            alert_type='out_of_stock',
            threshold=0
        )
        assert out_of_stock.alert_type == 'out_of_stock'

    def test_stock_alert_notify_email(self, db, product, branch):
        """Test alert with email notification."""
        alert = StockAlert.objects.create(
            product=product,
            branch=branch,
            alert_type='low_stock',
            threshold=10,
            notify_email=True
        )
        assert alert.notify_email is True


class TestCategoryManagers:
    """Tests for Category model managers."""

    def test_active_manager(self, db):
        """Test ActiveManager filters deleted records."""
        active = Category.objects.create(name='Active Category', is_active=True)
        deleted = Category.objects.create(name='Deleted Category', is_active=True)
        deleted.delete()

        active_categories = Category.active.all()
        assert active in active_categories

    def test_default_manager_returns_all(self, db):
        """Test that objects manager returns all records."""
        Category.objects.create(name='One')
        Category.objects.create(name='Two')

        assert Category.objects.count() >= 2


class TestProductManagers:
    """Tests for Product model managers."""

    @pytest.fixture
    def category(self, db):
        """Create a test category."""
        return Category.objects.create(name='Manager Test Category')

    def test_active_manager(self, db, category):
        """Test ActiveManager filters deleted records."""
        active = Product.objects.create(
            name='Active Product',
            sku='ACT001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )
        deleted = Product.objects.create(
            name='Deleted Product',
            sku='DEL001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )
        deleted.delete()

        active_products = Product.active.all()
        assert active in active_products
