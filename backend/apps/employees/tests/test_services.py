"""
Tests for Employee services - EmployeeService and ShiftService.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

from apps.employees.models import Employee, Shift
from apps.employees.services import EmployeeService, ShiftService
from apps.users.models import Role


class TestEmployeeServiceCreate:
    """Tests for EmployeeService.create_employee method."""

    @pytest.fixture
    def cashier_role(self, db):
        """Create a cashier role."""
        return Role.objects.create(
            name='Cajero',
            role_type='cashier',
            is_active=True
        )

    def test_create_employee_success(self, db, branch, cashier_role):
        """Test successful employee creation."""
        employee = EmployeeService.create_employee(
            email='newemp@test.com',
            password='testpass123',
            first_name='New',
            last_name='Employee',
            branch=branch,
            position='Cajero',
            hire_date=date.today(),
            role=cashier_role
        )

        assert employee.id is not None
        assert employee.employee_code.startswith(f'EMP-{branch.code}-')
        assert employee.user.email == 'newemp@test.com'
        assert employee.position == 'Cajero'
        assert employee.branch == branch

    def test_create_employee_with_all_fields(self, db, branch, cashier_role):
        """Test creating employee with all optional fields."""
        employee = EmployeeService.create_employee(
            email='fullemp@test.com',
            password='testpass123',
            first_name='Full',
            last_name='Employee',
            phone='555-1234',
            branch=branch,
            position='Vendedor',
            department='Ventas',
            employment_type='part_time',
            hire_date=date.today(),
            salary=Decimal('15000.00'),
            hourly_rate=Decimal('100.00'),
            role=cashier_role,
            emergency_contact_name='Emergency Person',
            emergency_contact_phone='555-5678',
            address='123 Main St',
            tax_id='RFC123456789',
            social_security_number='IMSS123456',
            notes='New hire'
        )

        assert employee.department == 'Ventas'
        assert employee.employment_type == 'part_time'
        assert employee.salary == Decimal('15000.00')
        assert employee.hourly_rate == Decimal('100.00')
        assert employee.emergency_contact_name == 'Emergency Person'

    def test_create_employee_user_linked(self, db, branch):
        """Test that user is properly linked to employee."""
        employee = EmployeeService.create_employee(
            email='linked@test.com',
            password='testpass123',
            first_name='Linked',
            last_name='User',
            branch=branch,
            position='Test',
            hire_date=date.today()
        )

        assert employee.user is not None
        assert employee.user.first_name == 'Linked'
        assert employee.user.last_name == 'User'
        assert employee.user.default_branch == branch
        assert branch in employee.user.allowed_branches.all()


class TestEmployeeServiceTerminate:
    """Tests for EmployeeService.terminate_employee method."""

    def test_terminate_employee_success(self, db, employee):
        """Test successful employee termination."""
        terminated = EmployeeService.terminate_employee(
            employee=employee,
            termination_date=date.today(),
            reason='Voluntary resignation'
        )

        assert terminated.status == 'terminated'
        assert terminated.termination_date == date.today()
        assert 'Voluntary resignation' in terminated.notes
        assert terminated.user.is_active is False

    def test_terminate_employee_closes_open_shift(self, db, open_shift):
        """Test that termination closes any open shift."""
        employee = open_shift.employee

        EmployeeService.terminate_employee(
            employee=employee,
            reason='Test termination'
        )

        # Refresh shift from DB
        open_shift.refresh_from_db()
        assert open_shift.clock_out is not None

    def test_terminate_already_terminated_employee(self, db, employee):
        """Test terminating already terminated employee raises error."""
        employee.status = 'terminated'
        employee.save()

        with pytest.raises(ValueError, match='ya está terminado'):
            EmployeeService.terminate_employee(employee=employee)

    def test_terminate_employee_default_date(self, db, employee):
        """Test termination with default date (today)."""
        terminated = EmployeeService.terminate_employee(employee=employee)

        assert terminated.termination_date == date.today()


class TestEmployeeServiceStats:
    """Tests for EmployeeService.get_employee_stats method."""

    def test_get_employee_stats(self, db, employee, branch):
        """Test getting employee statistics."""
        # Create some completed shifts
        clock_in = timezone.now() - timedelta(hours=8)
        clock_out = timezone.now()

        for i in range(3):
            Shift.objects.create(
                employee=employee,
                branch=branch,
                clock_in=clock_in - timedelta(days=i),
                clock_out=clock_out - timedelta(days=i),
            )

        stats = EmployeeService.get_employee_stats(employee=employee)

        assert stats['total_shifts'] == 3
        assert stats['total_hours'] is not None
        assert stats['total_hours'] >= Decimal('21.0')  # ~8 hours * 3 shifts

    def test_get_employee_stats_date_range(self, db, employee, branch):
        """Test getting stats with specific date range."""
        # Create shifts across different dates
        today = date.today()
        clock_in = timezone.now() - timedelta(hours=8)
        clock_out = timezone.now()

        # Shift within range
        Shift.objects.create(
            employee=employee,
            branch=branch,
            clock_in=clock_in,
            clock_out=clock_out,
        )

        # Shift outside range (60 days ago)
        old_clock_in = clock_in - timedelta(days=60)
        old_clock_out = clock_out - timedelta(days=60)
        Shift.objects.create(
            employee=employee,
            branch=branch,
            clock_in=old_clock_in,
            clock_out=old_clock_out,
        )

        stats = EmployeeService.get_employee_stats(
            employee=employee,
            date_from=today - timedelta(days=30),
            date_to=today
        )

        assert stats['total_shifts'] == 1  # Only the recent one

    def test_get_employee_stats_empty(self, db, employee):
        """Test getting stats for employee with no shifts."""
        stats = EmployeeService.get_employee_stats(employee=employee)

        assert stats['total_shifts'] == 0
        assert stats['total_hours'] == Decimal('0.00')


class TestEmployeeServiceGetByBranch:
    """Tests for EmployeeService.get_employees_by_branch method."""

    def test_get_employees_by_branch(self, db, employee, branch):
        """Test getting employees for a branch."""
        employees = EmployeeService.get_employees_by_branch(branch=branch)

        assert employee in employees

    def test_get_employees_excludes_inactive(self, db, employee, branch):
        """Test that inactive employees are excluded by default."""
        employee.status = 'inactive'
        employee.save()

        employees = EmployeeService.get_employees_by_branch(branch=branch)

        assert employee not in employees

    def test_get_employees_include_inactive(self, db, employee, branch):
        """Test including inactive employees."""
        employee.status = 'inactive'
        employee.save()

        employees = EmployeeService.get_employees_by_branch(
            branch=branch,
            include_inactive=True
        )

        assert employee in employees


class TestShiftServiceClockInOut:
    """Tests for ShiftService clock_in and clock_out methods."""

    def test_clock_in_success(self, db, employee):
        """Test successful clock in."""
        shift = ShiftService.clock_in(employee=employee)

        assert shift.id is not None
        assert shift.employee == employee
        assert shift.clock_in is not None
        assert shift.clock_out is None

    def test_clock_in_at_different_branch(self, db, employee, second_branch):
        """Test clocking in at different branch."""
        shift = ShiftService.clock_in(employee=employee, branch=second_branch)

        assert shift.branch == second_branch

    def test_clock_out_success(self, db, open_shift):
        """Test successful clock out."""
        employee = open_shift.employee

        shift = ShiftService.clock_out(employee=employee, notes='Good shift')

        assert shift.clock_out is not None
        assert shift.notes == 'Good shift'
        assert shift.worked_hours is not None


class TestShiftServiceBreaks:
    """Tests for ShiftService break methods."""

    def test_start_break_success(self, db, open_shift):
        """Test starting a break."""
        shift = ShiftService.start_break(employee=open_shift.employee)

        assert shift.break_start is not None
        assert shift.break_end is None

    def test_start_break_no_shift(self, db, employee):
        """Test starting break without open shift."""
        with pytest.raises(ValueError, match='no tiene un turno abierto'):
            ShiftService.start_break(employee=employee)

    def test_start_break_already_on_break(self, db, open_shift):
        """Test starting break when already on break."""
        open_shift.break_start = timezone.now()
        open_shift.save()

        with pytest.raises(ValueError, match='ya está en descanso'):
            ShiftService.start_break(employee=open_shift.employee)

    def test_end_break_success(self, db, open_shift):
        """Test ending a break."""
        open_shift.break_start = timezone.now() - timedelta(hours=1)
        open_shift.save()

        shift = ShiftService.end_break(employee=open_shift.employee)

        assert shift.break_end is not None

    def test_end_break_no_shift(self, db, employee):
        """Test ending break without open shift."""
        with pytest.raises(ValueError, match='no tiene un turno abierto'):
            ShiftService.end_break(employee=employee)

    def test_end_break_not_started(self, db, open_shift):
        """Test ending break when not on break."""
        with pytest.raises(ValueError, match='no ha iniciado descanso'):
            ShiftService.end_break(employee=open_shift.employee)

    def test_end_break_already_ended(self, db, open_shift):
        """Test ending break when already ended."""
        open_shift.break_start = timezone.now() - timedelta(hours=1)
        open_shift.break_end = timezone.now() - timedelta(minutes=30)
        open_shift.save()

        with pytest.raises(ValueError, match='ya terminó su descanso'):
            ShiftService.end_break(employee=open_shift.employee)


class TestShiftServiceDailySummary:
    """Tests for ShiftService.get_daily_summary method."""

    def test_get_daily_summary(self, db, employee, branch):
        """Test getting daily shift summary."""
        # Create completed shifts for today
        clock_in = timezone.now() - timedelta(hours=8)
        clock_out = timezone.now()

        Shift.objects.create(
            employee=employee,
            branch=branch,
            clock_in=clock_in,
            clock_out=clock_out,
        )

        summary = ShiftService.get_daily_summary(branch=branch)

        assert summary['date'] == date.today()
        assert summary['total_employees'] >= 1
        assert summary['shifts_count'] >= 1
        assert summary['total_hours'] >= Decimal('7.0')

    def test_get_daily_summary_specific_date(self, db, employee, branch):
        """Test getting summary for specific date."""
        yesterday = date.today() - timedelta(days=1)
        clock_in = timezone.now() - timedelta(days=1, hours=8)
        clock_out = timezone.now() - timedelta(days=1)

        Shift.objects.create(
            employee=employee,
            branch=branch,
            clock_in=clock_in,
            clock_out=clock_out,
        )

        summary = ShiftService.get_daily_summary(branch=branch, target_date=yesterday)

        assert summary['date'] == yesterday

    def test_get_daily_summary_empty(self, db, branch):
        """Test summary for day with no shifts."""
        summary = ShiftService.get_daily_summary(branch=branch)

        assert summary['total_employees'] == 0
        assert summary['total_hours'] == Decimal('0.00')
        assert summary['shifts_count'] == 0


class TestShiftServiceGetShifts:
    """Tests for ShiftService.get_employee_shifts method."""

    def test_get_employee_shifts(self, db, employee, branch):
        """Test getting employee shifts."""
        clock_in = timezone.now() - timedelta(hours=8)
        clock_out = timezone.now()

        Shift.objects.create(
            employee=employee,
            branch=branch,
            clock_in=clock_in,
            clock_out=clock_out,
        )

        shifts = ShiftService.get_employee_shifts(employee=employee)

        assert len(shifts) >= 1

    def test_get_employee_shifts_date_filter(self, db, employee, branch):
        """Test getting shifts with date filter."""
        today = date.today()
        clock_in = timezone.now() - timedelta(hours=8)
        clock_out = timezone.now()

        Shift.objects.create(
            employee=employee,
            branch=branch,
            clock_in=clock_in,
            clock_out=clock_out,
        )

        shifts = ShiftService.get_employee_shifts(
            employee=employee,
            date_from=today,
            date_to=today
        )

        assert len(shifts) >= 1


class TestShiftServiceManualShift:
    """Tests for ShiftService.create_manual_shift method."""

    def test_create_manual_shift(self, db, employee, branch, admin_user):
        """Test creating a manual shift entry."""
        clock_in = timezone.now() - timedelta(days=1, hours=8)
        clock_out = timezone.now() - timedelta(days=1)

        shift = ShiftService.create_manual_shift(
            employee=employee,
            branch=branch,
            clock_in=clock_in,
            clock_out=clock_out,
            adjusted_by=admin_user,
            notes='Manual correction'
        )

        assert shift.id is not None
        assert shift.is_manual_entry is True
        assert shift.adjusted_by == admin_user
        assert shift.notes == 'Manual correction'

    def test_create_manual_shift_with_break(self, db, employee, branch, admin_user):
        """Test manual shift with break times."""
        clock_in = timezone.now() - timedelta(hours=9)
        clock_out = timezone.now()
        break_start = timezone.now() - timedelta(hours=5)
        break_end = timezone.now() - timedelta(hours=4)

        shift = ShiftService.create_manual_shift(
            employee=employee,
            branch=branch,
            clock_in=clock_in,
            clock_out=clock_out,
            adjusted_by=admin_user,
            break_start=break_start,
            break_end=break_end
        )

        assert shift.break_start is not None
        assert shift.break_end is not None
        assert shift.break_hours >= Decimal('0.9')
