"""
Pytest configuration and fixtures for the inventory system.
"""
import pytest
from decimal import Decimal
from django.utils import timezone

from apps.users.models import User, Role, Permission
from apps.branches.models import Branch
from apps.inventory.models import Category, Product, BranchStock


@pytest.fixture
def admin_role(db):
    """Create an admin role with all permissions."""
    role = Role.objects.create(
        name='Admin Test',
        role_type='admin',
        description='Admin role for testing',
        is_active=True
    )
    return role


@pytest.fixture
def cashier_role(db):
    """Create a cashier role with sales permissions."""
    role = Role.objects.create(
        name='Cajero Test',
        role_type='cashier',
        description='Cashier role for testing',
        is_active=True
    )
    return role


@pytest.fixture
def admin_user(db, admin_role):
    """Create an admin user for testing."""
    user = User.objects.create_user(
        email='admin@test.com',
        password='testpass123',
        first_name='Admin',
        last_name='User',
        role=admin_role,
        is_active=True
    )
    return user


@pytest.fixture
def cashier_user(db, cashier_role, branch):
    """Create a cashier user for testing."""
    user = User.objects.create_user(
        email='cashier@test.com',
        password='testpass123',
        first_name='Cajero',
        last_name='Test',
        role=cashier_role,
        default_branch=branch,
        is_active=True
    )
    return user


@pytest.fixture
def branch(db):
    """Create a test branch."""
    return Branch.objects.create(
        name='Sucursal Test',
        code='TST',
        address='Calle Test 123',
        city='Ciudad Test',
        state='Estado Test',
        phone='555-1234',
        is_active=True
    )


@pytest.fixture
def second_branch(db):
    """Create a second test branch for transfers."""
    return Branch.objects.create(
        name='Sucursal Dos',
        code='DOS',
        address='Avenida Dos 456',
        city='Ciudad Dos',
        state='Estado Dos',
        phone='555-5678',
        is_active=True
    )


@pytest.fixture
def category(db):
    """Create a test category."""
    return Category.objects.create(
        name='Categoría Test',
        code='CAT-TEST',
        description='Categoría para tests',
        is_active=True
    )


@pytest.fixture
def product(db, category):
    """Create a test product."""
    return Product.objects.create(
        name='Producto Test',
        sku='PRD-TEST-001',
        barcode='7501234567890',
        description='Producto para testing',
        category=category,
        cost_price=Decimal('50.00'),
        sale_price=Decimal('100.00'),
        min_stock=10,
        is_active=True
    )


@pytest.fixture
def second_product(db, category):
    """Create a second test product."""
    return Product.objects.create(
        name='Producto Dos',
        sku='PRD-TEST-002',
        barcode='7501234567891',
        description='Segundo producto para testing',
        category=category,
        cost_price=Decimal('25.00'),
        sale_price=Decimal('50.00'),
        min_stock=5,
        is_active=True
    )


@pytest.fixture
def branch_stock(db, branch, product):
    """Create stock for product in branch."""
    return BranchStock.objects.create(
        branch=branch,
        product=product,
        quantity=100,
        min_stock=10,
        max_stock=500
    )


@pytest.fixture
def second_branch_stock(db, branch, second_product):
    """Create stock for second product in branch."""
    return BranchStock.objects.create(
        branch=branch,
        product=second_product,
        quantity=50,
        min_stock=5,
        max_stock=200
    )


@pytest.fixture
def api_client():
    """Create a DRF test client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    """Create an authenticated API client with admin user."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def authenticated_cashier_client(api_client, cashier_user):
    """Create an authenticated API client with cashier user."""
    api_client.force_authenticate(user=cashier_user)
    return api_client
