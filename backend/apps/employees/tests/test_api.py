"""
Tests for Employee API endpoints - EmployeeViewSet and ShiftViewSet.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.employees.models import Employee, Shift
from apps.users.models import User, Role
from apps.branches.models import Branch


class TestEmployeeViewSetList:
    """Tests for EmployeeViewSet.list action."""

    def test_list_employees_success(self, authenticated_client, employee):
        """Test listing employees."""
        response = authenticated_client.get('/api/v1/employees/')

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list) or 'results' in response.data

    def test_list_employees_filter_by_branch(self, authenticated_client, employee, branch):
        """Test filtering employees by branch."""
        response = authenticated_client.get(f'/api/v1/employees/?branch={branch.id}')

        assert response.status_code == status.HTTP_200_OK

    def test_list_employees_filter_by_status(self, authenticated_client, employee):
        """Test filtering employees by status."""
        response = authenticated_client.get('/api/v1/employees/?status=active')

        assert response.status_code == status.HTTP_200_OK

    def test_list_employees_filter_by_employment_type(self, authenticated_client, employee):
        """Test filtering employees by employment type."""
        response = authenticated_client.get('/api/v1/employees/?employment_type=full_time')

        assert response.status_code == status.HTTP_200_OK

    def test_list_employees_search(self, authenticated_client, employee):
        """Test searching employees."""
        response = authenticated_client.get('/api/v1/employees/?search=test')

        assert response.status_code == status.HTTP_200_OK

    def test_list_employees_unauthenticated(self, db):
        """Test that unauthenticated request is rejected."""
        client = APIClient()
        response = client.get('/api/v1/employees/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestEmployeeViewSetRetrieve:
    """Tests for EmployeeViewSet.retrieve action."""

    def test_retrieve_employee_success(self, authenticated_client, employee):
        """Test retrieving a single employee."""
        response = authenticated_client.get(f'/api/v1/employees/{employee.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == employee.id
        assert 'employee_code' in response.data
        assert 'user' in response.data

    def test_retrieve_employee_includes_current_shift(self, authenticated_client, open_shift):
        """Test that employee detail includes current shift info."""
        employee = open_shift.employee
        response = authenticated_client.get(f'/api/v1/employees/{employee.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert 'current_shift' in response.data
        assert 'is_clocked_in' in response.data

    def test_retrieve_employee_not_found(self, authenticated_client, db):
        """Test retrieving non-existent employee."""
        response = authenticated_client.get('/api/v1/employees/99999/')

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestEmployeeViewSetCreate:
    """Tests for EmployeeViewSet.create action."""

    @pytest.fixture
    def valid_employee_data(self, branch, cashier_role):
        """Valid data for creating an employee."""
        return {
            'email': 'newemployee@test.com',
            'password': 'securepass123',
            'first_name': 'New',
            'last_name': 'Employee',
            'branch_id': branch.id,
            'position': 'Cajero',
            'hire_date': str(date.today()),
            'role_id': cashier_role.id,
        }

    @pytest.fixture
    def cashier_role(self, db):
        """Create a cashier role."""
        return Role.objects.create(
            name='Cajero Test',
            role_type='cashier',
            is_active=True
        )

    def test_create_employee_success(self, admin_client, valid_employee_data):
        """Test creating an employee."""
        response = admin_client.post('/api/v1/employees/', valid_employee_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['user']['email'] == 'newemployee@test.com'
        assert 'employee_code' in response.data

    def test_create_employee_with_all_fields(self, admin_client, valid_employee_data):
        """Test creating employee with all optional fields."""
        valid_employee_data.update({
            'phone': '555-1234',
            'department': 'Ventas',
            'employment_type': 'part_time',
            'salary': '15000.00',
            'hourly_rate': '100.00',
            'emergency_contact_name': 'Contact Person',
            'emergency_contact_phone': '555-5678',
            'address': '123 Main St',
            'tax_id': 'RFC123456789',
            'notes': 'New hire',
        })

        response = admin_client.post('/api/v1/employees/', valid_employee_data)

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_employee_duplicate_email(self, admin_client, valid_employee_data, employee):
        """Test creating employee with duplicate email fails."""
        valid_employee_data['email'] = employee.user.email

        response = admin_client.post('/api/v1/employees/', valid_employee_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_create_employee_invalid_branch(self, admin_client, valid_employee_data):
        """Test creating employee with invalid branch fails."""
        valid_employee_data['branch_id'] = 99999

        response = admin_client.post('/api/v1/employees/', valid_employee_data)

        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

    def test_create_employee_missing_required_fields(self, admin_client, branch):
        """Test creating employee without required fields fails."""
        data = {'email': 'incomplete@test.com'}

        response = admin_client.post('/api/v1/employees/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestEmployeeViewSetUpdate:
    """Tests for EmployeeViewSet.update action."""

    def test_update_employee_success(self, admin_client, employee):
        """Test updating an employee."""
        data = {'position': 'Senior Cajero', 'department': 'Ventas'}

        response = admin_client.patch(f'/api/v1/employees/{employee.id}/', data)

        assert response.status_code == status.HTTP_200_OK
        employee.refresh_from_db()
        assert employee.position == 'Senior Cajero'

    def test_update_employee_user_fields(self, admin_client, employee):
        """Test updating employee's user fields."""
        data = {'first_name': 'Updated', 'last_name': 'Name', 'phone': '555-9999'}

        response = admin_client.patch(f'/api/v1/employees/{employee.id}/', data)

        assert response.status_code == status.HTTP_200_OK
        employee.user.refresh_from_db()
        assert employee.user.first_name == 'Updated'


class TestEmployeeViewSetDelete:
    """Tests for EmployeeViewSet.destroy action."""

    def test_delete_employee_soft_deletes(self, admin_client, employee):
        """Test deleting an employee performs soft delete."""
        response = admin_client.delete(f'/api/v1/employees/{employee.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        employee.refresh_from_db()
        assert employee.is_deleted is True


class TestEmployeeViewSetTerminate:
    """Tests for EmployeeViewSet.terminate action."""

    def test_terminate_employee_success(self, admin_client, employee):
        """Test terminating an employee."""
        data = {
            'termination_date': str(date.today()),
            'reason': 'Voluntary resignation'
        }

        response = admin_client.post(f'/api/v1/employees/{employee.id}/terminate/', data)

        assert response.status_code == status.HTTP_200_OK
        employee.refresh_from_db()
        assert employee.status == 'terminated'

    def test_terminate_employee_default_date(self, admin_client, employee):
        """Test terminating without date uses today."""
        response = admin_client.post(f'/api/v1/employees/{employee.id}/terminate/', {'reason': 'Test'})

        assert response.status_code == status.HTTP_200_OK
        employee.refresh_from_db()
        assert employee.termination_date == date.today()

    def test_terminate_already_terminated(self, admin_client, employee):
        """Test terminating already terminated employee fails."""
        employee.status = 'terminated'
        employee.save()

        response = admin_client.post(f'/api/v1/employees/{employee.id}/terminate/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestEmployeeViewSetStats:
    """Tests for EmployeeViewSet.stats action."""

    def test_get_employee_stats(self, authenticated_client, employee, branch):
        """Test getting employee statistics."""
        # Create a completed shift
        clock_in = timezone.now() - timedelta(hours=8)
        clock_out = timezone.now()
        Shift.objects.create(
            employee=employee,
            branch=branch,
            clock_in=clock_in,
            clock_out=clock_out,
        )

        response = authenticated_client.get(f'/api/v1/employees/{employee.id}/stats/')

        assert response.status_code == status.HTTP_200_OK
        assert 'total_shifts' in response.data
        assert 'total_hours' in response.data

    def test_get_employee_stats_with_date_range(self, authenticated_client, employee):
        """Test getting stats with date filter."""
        today = date.today()
        date_from = today - timedelta(days=30)

        response = authenticated_client.get(
            f'/api/v1/employees/{employee.id}/stats/?date_from={date_from}&date_to={today}'
        )

        assert response.status_code == status.HTTP_200_OK


class TestEmployeeViewSetShifts:
    """Tests for EmployeeViewSet.shifts action."""

    def test_get_employee_shifts(self, authenticated_client, employee, branch):
        """Test getting employee's shift history."""
        # Create shifts
        Shift.objects.create(
            employee=employee,
            branch=branch,
            clock_in=timezone.now() - timedelta(hours=8),
            clock_out=timezone.now(),
        )

        response = authenticated_client.get(f'/api/v1/employees/{employee.id}/shifts/')

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


class TestShiftViewSetList:
    """Tests for ShiftViewSet.list action."""

    def test_list_shifts_success(self, authenticated_client, open_shift):
        """Test listing shifts."""
        response = authenticated_client.get('/api/v1/shifts/')

        assert response.status_code == status.HTTP_200_OK

    def test_list_shifts_filter_by_branch(self, authenticated_client, open_shift, branch):
        """Test filtering shifts by branch."""
        response = authenticated_client.get(f'/api/v1/shifts/?branch={branch.id}')

        assert response.status_code == status.HTTP_200_OK

    def test_list_shifts_filter_by_employee(self, authenticated_client, open_shift):
        """Test filtering shifts by employee."""
        response = authenticated_client.get(f'/api/v1/shifts/?employee={open_shift.employee.id}')

        assert response.status_code == status.HTTP_200_OK

    def test_list_shifts_filter_by_date(self, authenticated_client, open_shift):
        """Test filtering shifts by date range."""
        today = date.today()
        response = authenticated_client.get(f'/api/v1/shifts/?date_from={today}&date_to={today}')

        assert response.status_code == status.HTTP_200_OK

    def test_list_shifts_filter_complete(self, authenticated_client, open_shift):
        """Test filtering by complete status."""
        response = authenticated_client.get('/api/v1/shifts/?is_complete=false')

        assert response.status_code == status.HTTP_200_OK


class TestShiftViewSetCreate:
    """Tests for ShiftViewSet.create (manual shift)."""

    def test_create_manual_shift(self, admin_client, employee, branch):
        """Test creating a manual shift entry."""
        clock_in = timezone.now() - timedelta(hours=8)
        clock_out = timezone.now()

        data = {
            'employee': employee.id,
            'branch': branch.id,
            'clock_in': clock_in.isoformat(),
            'clock_out': clock_out.isoformat(),
            'notes': 'Manual entry'
        }

        response = admin_client.post('/api/v1/shifts/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['is_manual_entry'] is True


class TestShiftViewSetClockIn:
    """Tests for ShiftViewSet.clock_in action."""

    def test_clock_in_success(self, employee_client, employee):
        """Test clocking in successfully."""
        response = employee_client.post('/api/v1/shifts/clock_in/', {})

        assert response.status_code == status.HTTP_201_CREATED
        assert 'clock_in' in response.data
        assert response.data['clock_out'] is None

    def test_clock_in_at_specific_branch(self, employee_client, employee, second_branch):
        """Test clocking in at a specific branch."""
        response = employee_client.post('/api/v1/shifts/clock_in/', {'branch_id': second_branch.id})

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['branch'] == second_branch.id

    def test_clock_in_already_clocked_in(self, employee_client, open_shift):
        """Test clocking in when already clocked in fails."""
        response = employee_client.post('/api/v1/shifts/clock_in/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_clock_in_no_employee_profile(self, authenticated_client, db):
        """Test clock in without employee profile fails."""
        response = authenticated_client.post('/api/v1/shifts/clock_in/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data


class TestShiftViewSetClockOut:
    """Tests for ShiftViewSet.clock_out action."""

    def test_clock_out_success(self, employee_client, open_shift):
        """Test clocking out successfully."""
        response = employee_client.post('/api/v1/shifts/clock_out/', {'notes': 'End of shift'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['clock_out'] is not None
        assert response.data['notes'] == 'End of shift'

    def test_clock_out_not_clocked_in(self, employee_client, employee):
        """Test clocking out when not clocked in fails."""
        response = employee_client.post('/api/v1/shifts/clock_out/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_clock_out_no_employee_profile(self, authenticated_client, db):
        """Test clock out without employee profile fails."""
        response = authenticated_client.post('/api/v1/shifts/clock_out/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestShiftViewSetBreaks:
    """Tests for ShiftViewSet break actions."""

    def test_start_break_success(self, employee_client, open_shift):
        """Test starting a break successfully."""
        response = employee_client.post('/api/v1/shifts/start_break/', {})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['break_start'] is not None

    def test_start_break_no_shift(self, employee_client, employee):
        """Test starting break without shift fails."""
        response = employee_client.post('/api/v1/shifts/start_break/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_start_break_already_on_break(self, employee_client, open_shift):
        """Test starting break when already on break fails."""
        open_shift.break_start = timezone.now()
        open_shift.save()

        response = employee_client.post('/api/v1/shifts/start_break/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_end_break_success(self, employee_client, open_shift):
        """Test ending a break successfully."""
        open_shift.break_start = timezone.now() - timedelta(minutes=30)
        open_shift.save()

        response = employee_client.post('/api/v1/shifts/end_break/', {})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['break_end'] is not None

    def test_end_break_not_on_break(self, employee_client, open_shift):
        """Test ending break when not on break fails."""
        response = employee_client.post('/api/v1/shifts/end_break/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestShiftViewSetCurrent:
    """Tests for ShiftViewSet.current action."""

    def test_get_current_shift(self, employee_client, open_shift):
        """Test getting current shift."""
        response = employee_client.get('/api/v1/shifts/current/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == open_shift.id

    def test_get_current_shift_none(self, employee_client, employee):
        """Test getting current shift when none exists."""
        response = employee_client.get('/api/v1/shifts/current/')

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'message' in response.data


class TestShiftViewSetDailySummary:
    """Tests for ShiftViewSet.daily_summary action."""

    def test_get_daily_summary(self, authenticated_client, branch, employee):
        """Test getting daily summary."""
        # Create a shift for today
        Shift.objects.create(
            employee=employee,
            branch=branch,
            clock_in=timezone.now() - timedelta(hours=4),
            clock_out=timezone.now(),
        )

        response = authenticated_client.get(f'/api/v1/shifts/daily_summary/?branch={branch.id}')

        assert response.status_code == status.HTTP_200_OK
        assert 'date' in response.data
        assert 'total_employees' in response.data
        assert 'total_hours' in response.data
        assert 'shifts_count' in response.data

    def test_get_daily_summary_specific_date(self, authenticated_client, branch):
        """Test getting daily summary for specific date."""
        yesterday = date.today() - timedelta(days=1)

        response = authenticated_client.get(
            f'/api/v1/shifts/daily_summary/?branch={branch.id}&date={yesterday}'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['date'] == str(yesterday)

    def test_get_daily_summary_no_branch(self, api_client, db, admin_role_with_employees_permissions):
        """Test daily summary without branch fails."""
        # Create a user without default branch
        user = User.objects.create_user(
            email='nobranch@test.com',
            password='testpass123',
            first_name='No',
            last_name='Branch',
            role=admin_role_with_employees_permissions,
            default_branch=None,
            is_active=True
        )
        api_client.force_authenticate(user=user)

        response = api_client.get('/api/v1/shifts/daily_summary/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
