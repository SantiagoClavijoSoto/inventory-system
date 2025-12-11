"""
Tests for Employee models.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

from apps.employees.models import Employee, Shift


@pytest.mark.django_db
class TestEmployeeModel:
    """Tests for the Employee model."""

    def test_employee_creation(self, employee):
        """Test creating an employee."""
        assert employee.employee_code == 'EMP-TST-0001'
        assert employee.position == 'Cajero'
        assert employee.status == 'active'
        assert employee.employment_type == 'full_time'

    def test_employee_full_name(self, employee):
        """Test the full_name property."""
        assert employee.full_name == 'Juan Empleado'

    def test_employee_email(self, employee):
        """Test the email property."""
        assert employee.email == 'employee@test.com'

    def test_employee_is_active_property(self, employee):
        """Test the is_active property."""
        assert employee.is_active is True

        # Test when status is not active
        employee.status = 'inactive'
        employee.save()
        assert employee.is_active is False

    def test_employee_years_of_service(self, employee):
        """Test years of service calculation."""
        # Employee was hired 365 days ago
        assert employee.years_of_service == 1

    def test_employee_generate_code(self, db, branch):
        """Test employee code generation."""
        code = Employee.generate_employee_code(branch.code)
        assert code.startswith(f'EMP-{branch.code}-')
        assert len(code.split('-')[-1]) == 4  # Sequence is 4 digits

    def test_employee_str(self, employee):
        """Test string representation."""
        assert str(employee) == f"{employee.employee_code} - {employee.full_name}"

    def test_employee_is_clocked_in_false(self, employee):
        """Test is_clocked_in when no open shift."""
        assert employee.is_clocked_in() is False

    def test_employee_is_clocked_in_true(self, open_shift):
        """Test is_clocked_in when there is an open shift."""
        assert open_shift.employee.is_clocked_in() is True

    def test_employee_get_current_shift(self, open_shift):
        """Test getting current shift."""
        current_shift = open_shift.employee.get_current_shift()
        assert current_shift == open_shift


@pytest.mark.django_db
class TestShiftModel:
    """Tests for the Shift model."""

    def test_shift_creation(self, shift):
        """Test creating a shift."""
        assert shift.employee is not None
        assert shift.branch is not None
        assert shift.clock_in is not None
        assert shift.clock_out is not None

    def test_shift_is_complete(self, shift, open_shift):
        """Test is_complete property."""
        assert shift.is_complete is True
        assert open_shift.is_complete is False

    def test_shift_calculate_hours(self, employee, branch):
        """Test hours calculation."""
        clock_in = timezone.now() - timedelta(hours=8)
        clock_out = timezone.now()

        shift = Shift.objects.create(
            employee=employee,
            branch=branch,
            clock_in=clock_in,
            clock_out=clock_out,
        )

        # Hours should be calculated on save
        assert shift.total_hours is not None
        assert float(shift.total_hours) >= 7.9  # Approximately 8 hours
        assert float(shift.total_hours) <= 8.1

    def test_shift_calculate_hours_with_break(self, employee, branch):
        """Test hours calculation with break."""
        clock_in = timezone.now() - timedelta(hours=9)
        break_start = timezone.now() - timedelta(hours=5)
        break_end = timezone.now() - timedelta(hours=4)
        clock_out = timezone.now()

        shift = Shift.objects.create(
            employee=employee,
            branch=branch,
            clock_in=clock_in,
            clock_out=clock_out,
            break_start=break_start,
            break_end=break_end,
        )

        assert shift.total_hours is not None
        assert float(shift.break_hours) >= 0.9  # Approximately 1 hour break
        assert float(shift.break_hours) <= 1.1
        assert float(shift.worked_hours) >= 7.9  # 9 - 1 = 8 hours worked
        assert float(shift.worked_hours) <= 8.1

    def test_shift_clock_in_employee(self, employee, branch):
        """Test clocking in an employee."""
        shift = Shift.clock_in_employee(employee)

        assert shift is not None
        assert shift.employee == employee
        assert shift.branch == employee.branch
        assert shift.clock_in is not None
        assert shift.clock_out is None

    def test_shift_clock_in_already_clocked_in(self, open_shift):
        """Test clocking in when already clocked in."""
        with pytest.raises(ValueError) as exc:
            Shift.clock_in_employee(open_shift.employee)
        assert "ya tiene un turno abierto" in str(exc.value)

    def test_shift_clock_out_employee(self, open_shift):
        """Test clocking out an employee."""
        shift = Shift.clock_out_employee(open_shift.employee, notes='Test notes')

        assert shift.clock_out is not None
        assert shift.notes == 'Test notes'
        assert shift.worked_hours is not None

    def test_shift_clock_out_not_clocked_in(self, employee):
        """Test clocking out when not clocked in."""
        with pytest.raises(ValueError) as exc:
            Shift.clock_out_employee(employee)
        assert "no tiene un turno abierto" in str(exc.value)

    def test_shift_str(self, shift):
        """Test string representation."""
        str_repr = str(shift)
        assert shift.employee.full_name in str_repr

    def test_shift_duration_ongoing(self, open_shift):
        """Test duration calculation for ongoing shift."""
        duration = open_shift.duration
        # Should be approximately 2 hours
        assert duration.total_seconds() >= 7000  # ~1.9 hours
        assert duration.total_seconds() <= 7400  # ~2.1 hours

    def test_shift_manual_entry(self, employee, branch, admin_user):
        """Test creating a manual shift entry."""
        clock_in = timezone.now() - timedelta(days=1, hours=8)
        clock_out = timezone.now() - timedelta(days=1)

        shift = Shift.objects.create(
            employee=employee,
            branch=branch,
            clock_in=clock_in,
            clock_out=clock_out,
            is_manual_entry=True,
            adjusted_by=admin_user,
            notes='Manual correction',
        )

        assert shift.is_manual_entry is True
        assert shift.adjusted_by == admin_user
