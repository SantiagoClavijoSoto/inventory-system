"""
Tests for Inventory API endpoints.
"""
import pytest
from decimal import Decimal
from rest_framework import status

from apps.inventory.models import Category, Product, BranchStock, StockMovement, StockAlert
from apps.users.models import Permission


class TestCategoryViewSet:
    """Tests for the Category ViewSet."""

    @pytest.fixture
    def inventory_view_permission(self, db):
        """Create inventory view permission."""
        return Permission.objects.create(
            code='inventory:view',
            name='Ver Inventario',
            module='inventory',
            action='view'
        )

    @pytest.fixture
    def inventory_manage_permission(self, db):
        """Create inventory manage permission."""
        return Permission.objects.create(
            code='inventory:manage',
            name='Gestionar Inventario',
            module='inventory',
            action='manage'
        )

    @pytest.fixture
    def admin_with_permissions(self, db, admin_user, admin_role, inventory_view_permission, inventory_manage_permission):
        """Admin user with inventory permissions."""
        admin_role.permissions.add(inventory_view_permission, inventory_manage_permission)
        return admin_user

    @pytest.fixture
    def category(self, db):
        """Create a test category."""
        return Category.objects.create(name='Test Category', description='Test description')

    def test_list_categories(self, authenticated_admin_client, admin_with_permissions, category):
        """Test listing categories."""
        response = authenticated_admin_client.get('/api/v1/categories/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_create_category(self, authenticated_admin_client, admin_with_permissions):
        """Test creating a new category."""
        response = authenticated_admin_client.post('/api/v1/categories/', {
            'name': 'New Category',
            'description': 'New category description'
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert Category.objects.filter(name='New Category').exists()

    def test_retrieve_category(self, authenticated_admin_client, admin_with_permissions, category):
        """Test retrieving a specific category."""
        response = authenticated_admin_client.get(f'/api/v1/categories/{category.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == category.name

    def test_update_category(self, authenticated_admin_client, admin_with_permissions, category):
        """Test updating a category."""
        response = authenticated_admin_client.patch(f'/api/v1/categories/{category.id}/', {
            'name': 'Updated Category Name'
        })

        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.name == 'Updated Category Name'

    def test_delete_category(self, authenticated_admin_client, admin_with_permissions, db):
        """Test deleting a category (soft delete)."""
        new_category = Category.objects.create(name='To Delete')

        response = authenticated_admin_client.delete(f'/api/v1/categories/{new_category.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        new_category.refresh_from_db()
        assert new_category.is_deleted is True

    def test_category_tree_action(self, authenticated_admin_client, admin_with_permissions, db):
        """Test tree action returns flat list for dropdowns."""
        Category.objects.create(name='Root Category', is_active=True)
        Category.objects.create(name='Another Category', is_active=True)

        response = authenticated_admin_client.get('/api/v1/categories/tree/')

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_category_root_action(self, authenticated_admin_client, admin_with_permissions, db):
        """Test root action returns only root categories."""
        parent = Category.objects.create(name='Parent', is_active=True)
        Category.objects.create(name='Child', parent=parent, is_active=True)

        response = authenticated_admin_client.get('/api/v1/categories/root/')

        assert response.status_code == status.HTTP_200_OK
        names = [c['name'] for c in response.data]
        assert 'Parent' in names
        assert 'Child' not in names

    def test_list_categories_requires_authentication(self, api_client):
        """Test that listing categories requires authentication."""
        response = api_client.get('/api/v1/categories/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestProductViewSet:
    """Tests for the Product ViewSet."""

    @pytest.fixture
    def inventory_view_permission(self, db):
        """Create inventory view permission."""
        return Permission.objects.create(
            code='inventory:view',
            name='Ver Inventario',
            module='inventory',
            action='view'
        )

    @pytest.fixture
    def inventory_manage_permission(self, db):
        """Create inventory manage permission."""
        return Permission.objects.create(
            code='inventory:manage',
            name='Gestionar Inventario',
            module='inventory',
            action='manage'
        )

    @pytest.fixture
    def admin_with_permissions(self, db, admin_user, admin_role, inventory_view_permission, inventory_manage_permission):
        """Admin user with inventory permissions."""
        admin_role.permissions.add(inventory_view_permission, inventory_manage_permission)
        return admin_user

    @pytest.fixture
    def category(self, db):
        """Create a test category."""
        return Category.objects.create(name='Product Test Category')

    @pytest.fixture
    def product(self, db, category):
        """Create a test product."""
        return Product.objects.create(
            name='Test Product',
            sku='TST001',
            barcode='1234567890123',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00'),
            min_stock=10,
            is_active=True
        )

    def test_list_products(self, authenticated_admin_client, admin_with_permissions, product):
        """Test listing products."""
        response = authenticated_admin_client.get('/api/v1/products/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_create_product(self, authenticated_admin_client, admin_with_permissions, category):
        """Test creating a new product."""
        response = authenticated_admin_client.post('/api/v1/products/', {
            'name': 'New Product',
            'sku': 'NEW001',
            'category': category.id,
            'cost_price': '20.00',
            'sale_price': '30.00'
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert Product.objects.filter(sku='NEW001').exists()

    def test_retrieve_product(self, authenticated_admin_client, admin_with_permissions, product):
        """Test retrieving a specific product."""
        response = authenticated_admin_client.get(f'/api/v1/products/{product.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == product.name
        assert response.data['sku'] == product.sku

    def test_update_product(self, authenticated_admin_client, admin_with_permissions, product):
        """Test updating a product."""
        response = authenticated_admin_client.patch(f'/api/v1/products/{product.id}/', {
            'name': 'Updated Product Name'
        })

        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.name == 'Updated Product Name'

    def test_delete_product(self, authenticated_admin_client, admin_with_permissions, category):
        """Test deleting a product (soft delete)."""
        new_product = Product.objects.create(
            name='To Delete',
            sku='DEL001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )

        response = authenticated_admin_client.delete(f'/api/v1/products/{new_product.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        new_product.refresh_from_db()
        assert new_product.is_deleted is True

    def test_product_by_barcode(self, authenticated_admin_client, admin_with_permissions, product, branch):
        """Test searching product by barcode."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50)

        response = authenticated_admin_client.get(
            f'/api/v1/products/barcode/{product.barcode}/?branch_id={branch.id}'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['product']['sku'] == product.sku
        assert response.data['stock_in_branch'] == 50

    def test_product_by_barcode_requires_branch(self, authenticated_admin_client, admin_with_permissions, product):
        """Test barcode search requires branch_id."""
        response = authenticated_admin_client.get(f'/api/v1/products/barcode/{product.barcode}/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_product_by_barcode_not_found(self, authenticated_admin_client, admin_with_permissions, branch):
        """Test barcode search with non-existent barcode."""
        response = authenticated_admin_client.get(f'/api/v1/products/barcode/9999999999999/?branch_id={branch.id}')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_product_stock_action(self, authenticated_admin_client, admin_with_permissions, product, branch, second_branch):
        """Test getting stock levels for a product."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50)
        BranchStock.objects.create(product=product, branch=second_branch, quantity=30)

        response = authenticated_admin_client.get(f'/api/v1/products/{product.id}/stock/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_product_movements_action(self, authenticated_admin_client, admin_with_permissions, product, branch, admin_user):
        """Test getting movement history for a product."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50)
        StockMovement.objects.create(
            product=product,
            branch=branch,
            movement_type='purchase',
            quantity=50,
            previous_quantity=0,
            new_quantity=50,
            created_by=admin_user
        )

        response = authenticated_admin_client.get(f'/api/v1/products/{product.id}/movements/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_product_low_stock_action(self, authenticated_admin_client, admin_with_permissions, category, branch):
        """Test getting products with low stock."""
        product = Product.objects.create(
            name='Low Stock Product',
            sku='LOW001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00'),
            min_stock=20,
            is_active=True
        )
        BranchStock.objects.create(product=product, branch=branch, quantity=5)

        response = authenticated_admin_client.get('/api/v1/products/low_stock/')

        assert response.status_code == status.HTTP_200_OK
        skus = [item['product_sku'] for item in response.data]
        assert 'LOW001' in skus

    def test_search_products(self, authenticated_admin_client, admin_with_permissions, product):
        """Test searching products."""
        response = authenticated_admin_client.get('/api/v1/products/?search=Test')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filter_products_by_category(self, authenticated_admin_client, admin_with_permissions, product, category):
        """Test filtering products by category."""
        response = authenticated_admin_client.get(f'/api/v1/products/?category={category.id}')

        assert response.status_code == status.HTTP_200_OK
        # Response is paginated, so access results list
        results = response.data.get('results', response.data)
        for p in results:
            assert p['category'] == category.id


class TestStockViewSet:
    """Tests for the Stock ViewSet."""

    @pytest.fixture
    def inventory_manage_permission(self, db):
        """Create inventory manage permission."""
        return Permission.objects.create(
            code='inventory:manage',
            name='Gestionar Inventario',
            module='inventory',
            action='manage'
        )

    @pytest.fixture
    def admin_with_permissions(self, db, admin_user, admin_role, inventory_manage_permission):
        """Admin user with inventory permissions."""
        admin_role.permissions.add(inventory_manage_permission)
        return admin_user

    @pytest.fixture
    def category(self, db):
        """Create a test category."""
        return Category.objects.create(name='Stock Test Category')

    @pytest.fixture
    def product(self, db, category):
        """Create a test product."""
        return Product.objects.create(
            name='Stock Test Product',
            sku='STK001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )

    def test_stock_adjustment_add(self, authenticated_admin_client, admin_with_permissions, product, branch):
        """Test manual stock adjustment - add."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50)

        response = authenticated_admin_client.post('/api/v1/stock/adjust/', {
            'product_id': product.id,
            'branch_id': branch.id,
            'adjustment_type': 'add',
            'quantity': 25,
            'reason': 'Found extra inventory'
        })

        assert response.status_code == status.HTTP_201_CREATED
        stock = BranchStock.objects.get(product=product, branch=branch)
        assert stock.quantity == 75

    def test_stock_adjustment_subtract(self, authenticated_admin_client, admin_with_permissions, product, branch):
        """Test manual stock adjustment - subtract."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50)

        response = authenticated_admin_client.post('/api/v1/stock/adjust/', {
            'product_id': product.id,
            'branch_id': branch.id,
            'adjustment_type': 'subtract',
            'quantity': 10,
            'reason': 'Damaged goods'
        })

        assert response.status_code == status.HTTP_201_CREATED
        stock = BranchStock.objects.get(product=product, branch=branch)
        assert stock.quantity == 40

    def test_stock_adjustment_set(self, authenticated_admin_client, admin_with_permissions, product, branch):
        """Test manual stock adjustment - set."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50)

        response = authenticated_admin_client.post('/api/v1/stock/adjust/', {
            'product_id': product.id,
            'branch_id': branch.id,
            'adjustment_type': 'set',
            'quantity': 100,
            'reason': 'Physical count'
        })

        assert response.status_code == status.HTTP_201_CREATED
        stock = BranchStock.objects.get(product=product, branch=branch)
        assert stock.quantity == 100

    def test_stock_transfer(self, authenticated_admin_client, admin_with_permissions, product, branch, second_branch):
        """Test stock transfer between branches."""
        BranchStock.objects.create(product=product, branch=branch, quantity=100)

        response = authenticated_admin_client.post('/api/v1/stock/transfer/', {
            'product_id': product.id,
            'from_branch_id': branch.id,
            'to_branch_id': second_branch.id,
            'quantity': 30
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert 'outgoing' in response.data
        assert 'incoming' in response.data

        from_stock = BranchStock.objects.get(product=product, branch=branch)
        to_stock = BranchStock.objects.get(product=product, branch=second_branch)
        assert from_stock.quantity == 70
        assert to_stock.quantity == 30

    def test_stock_transfer_same_branch_fails(self, authenticated_admin_client, admin_with_permissions, product, branch):
        """Test transfer to same branch fails."""
        BranchStock.objects.create(product=product, branch=branch, quantity=100)

        response = authenticated_admin_client.post('/api/v1/stock/transfer/', {
            'product_id': product.id,
            'from_branch_id': branch.id,
            'to_branch_id': branch.id,
            'quantity': 30
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_stock_by_branch(self, authenticated_admin_client, admin_with_permissions, product, branch):
        """Test getting all stock for a branch."""
        BranchStock.objects.create(product=product, branch=branch, quantity=50)

        response = authenticated_admin_client.get(f'/api/v1/stock/by_branch/?branch_id={branch.id}')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_stock_by_branch_requires_branch_id(self, authenticated_admin_client, admin_with_permissions):
        """Test by_branch requires branch_id parameter."""
        response = authenticated_admin_client.get('/api/v1/stock/by_branch/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestStockMovementViewSet:
    """Tests for the StockMovement ViewSet."""

    @pytest.fixture
    def inventory_view_permission(self, db):
        """Create inventory view permission."""
        return Permission.objects.create(
            code='inventory:view',
            name='Ver Inventario',
            module='inventory',
            action='view'
        )

    @pytest.fixture
    def admin_with_permissions(self, db, admin_user, admin_role, inventory_view_permission):
        """Admin user with inventory permissions."""
        admin_role.permissions.add(inventory_view_permission)
        return admin_user

    @pytest.fixture
    def category(self, db):
        """Create a test category."""
        return Category.objects.create(name='Movement Test Category')

    @pytest.fixture
    def product(self, db, category):
        """Create a test product."""
        return Product.objects.create(
            name='Movement Test Product',
            sku='MOV001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00')
        )

    def test_list_movements(self, authenticated_admin_client, admin_with_permissions, product, branch, admin_user):
        """Test listing stock movements."""
        StockMovement.objects.create(
            product=product,
            branch=branch,
            movement_type='purchase',
            quantity=100,
            previous_quantity=0,
            new_quantity=100,
            created_by=admin_user
        )

        response = authenticated_admin_client.get('/api/v1/stock/movements/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_retrieve_movement(self, authenticated_admin_client, admin_with_permissions, product, branch, admin_user):
        """Test retrieving a specific movement."""
        movement = StockMovement.objects.create(
            product=product,
            branch=branch,
            movement_type='sale',
            quantity=10,
            previous_quantity=100,
            new_quantity=90,
            created_by=admin_user
        )

        response = authenticated_admin_client.get(f'/api/v1/stock/movements/{movement.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['movement_type'] == 'sale'

    def test_movements_are_read_only(self, authenticated_admin_client, admin_with_permissions, product, branch, admin_user):
        """Test that movements cannot be created directly via API."""
        response = authenticated_admin_client.post('/api/v1/stock/movements/', {
            'product': product.id,
            'branch': branch.id,
            'movement_type': 'purchase',
            'quantity': 50
        })

        # ViewSet is read-only, so POST should be not allowed
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_filter_movements_by_product(self, authenticated_admin_client, admin_with_permissions, product, branch, admin_user):
        """Test filtering movements by product."""
        StockMovement.objects.create(
            product=product,
            branch=branch,
            movement_type='purchase',
            quantity=50,
            previous_quantity=0,
            new_quantity=50,
            created_by=admin_user
        )

        response = authenticated_admin_client.get(f'/api/v1/stock/movements/?product={product.id}')

        assert response.status_code == status.HTTP_200_OK
        # Response is paginated, so access results list
        results = response.data.get('results', response.data)
        for m in results:
            assert m['product'] == product.id


class TestStockAlertViewSet:
    """Tests for the StockAlert ViewSet."""

    @pytest.fixture
    def alerts_manage_permission(self, db):
        """Create alerts manage permission."""
        return Permission.objects.create(
            code='alerts:manage',
            name='Gestionar Alertas',
            module='alerts',
            action='manage'
        )

    @pytest.fixture
    def admin_with_permissions(self, db, admin_user, admin_role, alerts_manage_permission):
        """Admin user with alerts permissions."""
        admin_role.permissions.add(alerts_manage_permission)
        return admin_user

    @pytest.fixture
    def category(self, db):
        """Create a test category."""
        return Category.objects.create(name='Alert Test Category')

    @pytest.fixture
    def product(self, db, category):
        """Create a test product."""
        return Product.objects.create(
            name='Alert Test Product',
            sku='ALR001',
            category=category,
            cost_price=Decimal('10.00'),
            sale_price=Decimal('15.00'),
            min_stock=10
        )

    def test_list_stock_alerts(self, authenticated_admin_client, admin_with_permissions, product, branch):
        """Test listing stock alerts."""
        StockAlert.objects.create(
            product=product,
            branch=branch,
            alert_type='low_stock',
            threshold=5,
            is_active=True
        )

        response = authenticated_admin_client.get('/api/v1/stock/alerts/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_create_stock_alert(self, authenticated_admin_client, admin_with_permissions, product, branch):
        """Test creating a stock alert."""
        response = authenticated_admin_client.post('/api/v1/stock/alerts/', {
            'product': product.id,
            'branch': branch.id,
            'alert_type': 'low_stock',
            'threshold': 15,
            'is_active': True
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert StockAlert.objects.filter(product=product, branch=branch).exists()

    def test_active_alerts_action(self, authenticated_admin_client, admin_with_permissions, product, branch):
        """Test getting active alerts (products below threshold)."""
        BranchStock.objects.create(product=product, branch=branch, quantity=5)  # Below min_stock of 10

        response = authenticated_admin_client.get('/api/v1/stock/alerts/active/')

        assert response.status_code == status.HTTP_200_OK
        # Should find low stock alert
        alert_types = [a['alert_type'] for a in response.data]
        assert 'low_stock' in alert_types or 'out_of_stock' in alert_types

    def test_active_alerts_by_branch(self, authenticated_admin_client, admin_with_permissions, product, branch, second_branch):
        """Test getting active alerts filtered by branch."""
        BranchStock.objects.create(product=product, branch=branch, quantity=5)
        BranchStock.objects.create(product=product, branch=second_branch, quantity=100)

        response = authenticated_admin_client.get(f'/api/v1/stock/alerts/active/?branch_id={branch.id}')

        assert response.status_code == status.HTTP_200_OK
        for alert in response.data:
            assert alert['branch_id'] == branch.id
