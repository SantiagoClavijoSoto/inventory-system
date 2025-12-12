"""
Pytest configuration and fixtures for the inventory system.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

from apps.users.models import User, Role, Permission
from apps.branches.models import Branch
from apps.inventory.models import Category, Product, BranchStock
from apps.employees.models import Employee, Shift


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
def admin_user(db, admin_role, branch):
    """Create an admin user for testing."""
    user = User.objects.create_user(
        email='admin@test.com',
        password='testpass123',
        first_name='Admin',
        last_name='User',
        role=admin_role,
        default_branch=branch,
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
        quantity=100
    )


@pytest.fixture
def second_branch_stock(db, branch, second_product):
    """Create stock for second product in branch."""
    return BranchStock.objects.create(
        branch=branch,
        product=second_product,
        quantity=50
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


# Employee fixtures
@pytest.fixture
def employee_user(db, cashier_role, branch):
    """Create a user for an employee."""
    user = User.objects.create_user(
        email='employee@test.com',
        password='testpass123',
        first_name='Juan',
        last_name='Empleado',
        role=cashier_role,
        default_branch=branch,
        is_active=True
    )
    return user


@pytest.fixture
def employee(db, employee_user, branch):
    """Create a test employee."""
    return Employee.objects.create(
        user=employee_user,
        employee_code='EMP-TST-0001',
        branch=branch,
        position='Cajero',
        department='Ventas',
        employment_type='full_time',
        hire_date=date.today() - timedelta(days=365),
        salary=Decimal('15000.00'),
        hourly_rate=Decimal('100.00'),
        status='active'
    )


@pytest.fixture
def second_employee_user(db, cashier_role, branch):
    """Create a second user for employee testing."""
    user = User.objects.create_user(
        email='employee2@test.com',
        password='testpass123',
        first_name='Maria',
        last_name='Trabajadora',
        role=cashier_role,
        default_branch=branch,
        is_active=True
    )
    return user


@pytest.fixture
def second_employee(db, second_employee_user, branch):
    """Create a second test employee."""
    return Employee.objects.create(
        user=second_employee_user,
        employee_code='EMP-TST-0002',
        branch=branch,
        position='Supervisor',
        department='Ventas',
        employment_type='full_time',
        hire_date=date.today() - timedelta(days=730),
        salary=Decimal('20000.00'),
        hourly_rate=Decimal('125.00'),
        status='active'
    )


@pytest.fixture
def shift(db, employee, branch):
    """Create a completed shift for testing."""
    clock_in = timezone.now() - timedelta(hours=8)
    clock_out = timezone.now()
    shift = Shift.objects.create(
        employee=employee,
        branch=branch,
        clock_in=clock_in,
        clock_out=clock_out,
    )
    return shift


@pytest.fixture
def open_shift(db, employee, branch):
    """Create an open (ongoing) shift for testing."""
    return Shift.objects.create(
        employee=employee,
        branch=branch,
        clock_in=timezone.now() - timedelta(hours=2),
    )


# Permission fixtures for employees module
@pytest.fixture
def employees_view_permission(db):
    """Create employees view permission."""
    return Permission.objects.create(
        code='employees:view',
        name='Ver Empleados',
        module='employees',
        action='view'
    )


@pytest.fixture
def employees_create_permission(db):
    """Create employees create permission."""
    return Permission.objects.create(
        code='employees:create',
        name='Crear Empleados',
        module='employees',
        action='create'
    )


@pytest.fixture
def employees_edit_permission(db):
    """Create employees edit permission."""
    return Permission.objects.create(
        code='employees:edit',
        name='Editar Empleados',
        module='employees',
        action='edit'
    )


@pytest.fixture
def employees_delete_permission(db):
    """Create employees delete permission."""
    return Permission.objects.create(
        code='employees:delete',
        name='Eliminar Empleados',
        module='employees',
        action='delete'
    )


@pytest.fixture
def admin_role_with_employees_permissions(
    admin_role,
    employees_view_permission,
    employees_create_permission,
    employees_edit_permission,
    employees_delete_permission
):
    """Admin role with all employees permissions."""
    admin_role.permissions.add(
        employees_view_permission,
        employees_create_permission,
        employees_edit_permission,
        employees_delete_permission
    )
    return admin_role


# API client aliases for test readability
@pytest.fixture
def authenticated_client(api_client, admin_user, admin_role_with_employees_permissions):
    """Authenticated admin client with employees permissions."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user, admin_role_with_employees_permissions):
    """Authenticated admin client with full admin permissions."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def employee_client(api_client, employee):
    """Create an authenticated API client for the employee user."""
    api_client.force_authenticate(user=employee.user)
    return api_client
