"""
Business logic services for Employee module.
"""
from decimal import Decimal
from datetime import date, timedelta
from django.db import transaction
from django.db.models import Sum, Count, Avg
from django.utils import timezone

from apps.users.models import User, Role
from apps.branches.models import Branch
from apps.sales.models import Sale
from .models import Employee, Shift


class EmployeeService:
    """Service for managing employees."""

    @classmethod
    @transaction.atomic
    def create_employee(
        cls,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        branch: Branch,
        position: str,
        hire_date: date,
        phone: str = '',
        role: Role = None,
        department: str = '',
        employment_type: str = 'full_time',
        salary: Decimal = Decimal('0.00'),
        hourly_rate: Decimal = Decimal('0.00'),
        **extra_fields
    ) -> Employee:
        """
        Create a new employee with associated user account.

        Args:
            email: User email (login)
            password: Initial password
            first_name: Employee first name
            last_name: Employee last name
            branch: Primary branch assignment
            position: Job position title
            hire_date: Employment start date
            phone: Contact phone (optional)
            role: User role for permissions (optional)
            department: Department name (optional)
            employment_type: Type of employment
            salary: Monthly salary
            hourly_rate: Hourly rate for overtime
            **extra_fields: Additional employee fields

        Returns:
            Created Employee instance
        """
        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role,
            default_branch=branch,
        )

        # Add branch to allowed branches
        user.allowed_branches.add(branch)

        # Generate employee code
        employee_code = Employee.generate_employee_code(branch.code)

        # Create employee profile
        employee = Employee.objects.create(
            user=user,
            employee_code=employee_code,
            branch=branch,
            position=position,
            department=department,
            employment_type=employment_type,
            hire_date=hire_date,
            salary=salary,
            hourly_rate=hourly_rate,
            **extra_fields
        )

        return employee

    @classmethod
    @transaction.atomic
    def terminate_employee(
        cls,
        employee: Employee,
        termination_date: date = None,
        reason: str = ''
    ) -> Employee:
        """
        Terminate an employee.

        Args:
            employee: Employee to terminate
            termination_date: Last day of work (defaults to today)
            reason: Reason for termination (stored in notes)

        Returns:
            Updated Employee instance
        """
        if employee.status == 'terminated':
            raise ValueError(f"El empleado {employee.full_name} ya está terminado")

        # Close any open shifts
        current_shift = employee.get_current_shift()
        if current_shift:
            Shift.clock_out_employee(employee, notes="Terminación de empleo")

        # Update employee
        employee.status = 'terminated'
        employee.termination_date = termination_date or date.today()
        if reason:
            employee.notes = f"{employee.notes}\nTerminación: {reason}".strip()
        employee.save()

        # Deactivate user account
        employee.user.is_active = False
        employee.user.save()

        return employee

    @classmethod
    def get_employee_stats(
        cls,
        employee: Employee,
        date_from: date = None,
        date_to: date = None
    ) -> dict:
        """
        Get statistics for an employee.

        Args:
            employee: Employee to get stats for
            date_from: Start date for period (defaults to 30 days ago)
            date_to: End date for period (defaults to today)

        Returns:
            Dictionary with employee statistics
        """
        if not date_to:
            date_to = timezone.localdate()
        if not date_from:
            date_from = date_to - timedelta(days=30)

        # Shift statistics
        shifts = Shift.objects.filter(
            employee=employee,
            clock_in__date__gte=date_from,
            clock_in__date__lte=date_to,
            clock_out__isnull=False
        )

        shift_stats = shifts.aggregate(
            total_shifts=Count('id'),
            total_hours=Sum('worked_hours')
        )

        # Sales statistics (if user is a cashier)
        sales = Sale.objects.filter(
            cashier=employee.user,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
            status='completed'
        )

        sales_stats = sales.aggregate(
            total_sales=Count('id'),
            total_revenue=Sum('total'),
            average_sale=Avg('total')
        )

        return {
            'total_shifts': shift_stats['total_shifts'] or 0,
            'total_hours': shift_stats['total_hours'] or Decimal('0.00'),
            'total_sales': sales_stats['total_sales'] or 0,
            'total_revenue': sales_stats['total_revenue'] or Decimal('0.00'),
            'average_sale': sales_stats['average_sale'] or Decimal('0.00'),
            'period_start': date_from,
            'period_end': date_to,
        }

    @classmethod
    def get_employees_by_branch(cls, branch: Branch, include_inactive: bool = False):
        """
        Get all employees for a branch.

        Args:
            branch: Branch to filter by
            include_inactive: Whether to include inactive employees

        Returns:
            QuerySet of employees
        """
        if include_inactive:
            queryset = Employee.objects.filter(branch=branch)
        else:
            queryset = Employee.active_objects.filter(branch=branch, status='active')

        return queryset.select_related('user', 'branch')


class ShiftService:
    """Service for managing shifts."""

    @classmethod
    def clock_in(cls, employee: Employee, branch: Branch = None) -> Shift:
        """
        Clock in an employee.

        Args:
            employee: Employee to clock in
            branch: Branch to clock in at (defaults to employee's branch)

        Returns:
            Created Shift instance
        """
        return Shift.clock_in_employee(employee, branch)

    @classmethod
    def clock_out(cls, employee: Employee, notes: str = '') -> Shift:
        """
        Clock out an employee.

        Args:
            employee: Employee to clock out
            notes: Optional notes for the shift

        Returns:
            Updated Shift instance
        """
        return Shift.clock_out_employee(employee, notes)

    @classmethod
    def start_break(cls, employee: Employee) -> Shift:
        """
        Start a break for the current shift.

        Args:
            employee: Employee starting break

        Returns:
            Updated Shift instance
        """
        current_shift = employee.get_current_shift()

        if not current_shift:
            raise ValueError(f"El empleado {employee.full_name} no tiene un turno abierto")

        if current_shift.break_start and not current_shift.break_end:
            raise ValueError("El empleado ya está en descanso")

        current_shift.break_start = timezone.now()
        current_shift.save()

        return current_shift

    @classmethod
    def end_break(cls, employee: Employee) -> Shift:
        """
        End a break for the current shift.

        Args:
            employee: Employee ending break

        Returns:
            Updated Shift instance
        """
        current_shift = employee.get_current_shift()

        if not current_shift:
            raise ValueError(f"El empleado {employee.full_name} no tiene un turno abierto")

        if not current_shift.break_start:
            raise ValueError("El empleado no ha iniciado descanso")

        if current_shift.break_end:
            raise ValueError("El empleado ya terminó su descanso")

        current_shift.break_end = timezone.now()
        current_shift.save()

        return current_shift

    @classmethod
    def get_daily_summary(cls, branch: Branch, target_date: date = None) -> dict:
        """
        Get shift summary for a branch on a specific date.

        Args:
            branch: Branch to get summary for
            target_date: Date to summarize (defaults to today)

        Returns:
            Dictionary with shift summary
        """
        if not target_date:
            target_date = timezone.localdate()

        shifts = Shift.objects.filter(
            branch=branch,
            clock_in__date=target_date
        )

        completed_shifts = shifts.filter(clock_out__isnull=False)

        stats = completed_shifts.aggregate(
            total_hours=Sum('worked_hours'),
            shifts_count=Count('id')
        )

        # Count unique employees
        total_employees = shifts.values('employee').distinct().count()

        return {
            'date': target_date,
            'total_employees': total_employees,
            'total_hours': stats['total_hours'] or Decimal('0.00'),
            'shifts_count': stats['shifts_count'] or 0,
        }

    @classmethod
    def get_employee_shifts(
        cls,
        employee: Employee,
        date_from: date = None,
        date_to: date = None
    ):
        """
        Get shifts for an employee in a date range.

        Args:
            employee: Employee to get shifts for
            date_from: Start date (optional)
            date_to: End date (optional)

        Returns:
            QuerySet of shifts
        """
        queryset = Shift.objects.filter(employee=employee)

        if date_from:
            queryset = queryset.filter(clock_in__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(clock_in__date__lte=date_to)

        return queryset.select_related('branch').order_by('-clock_in')

    @classmethod
    @transaction.atomic
    def create_manual_shift(
        cls,
        employee: Employee,
        branch: Branch,
        clock_in,
        clock_out,
        adjusted_by,
        break_start=None,
        break_end=None,
        notes: str = ''
    ) -> Shift:
        """
        Create a manual shift entry (for corrections).

        Args:
            employee: Employee for the shift
            branch: Branch where shift was worked
            clock_in: Start datetime
            clock_out: End datetime
            adjusted_by: User making the manual entry
            break_start: Break start time (optional)
            break_end: Break end time (optional)
            notes: Notes about the manual entry

        Returns:
            Created Shift instance
        """
        shift = Shift.objects.create(
            employee=employee,
            branch=branch,
            clock_in=clock_in,
            clock_out=clock_out,
            break_start=break_start,
            break_end=break_end,
            notes=notes,
            is_manual_entry=True,
            adjusted_by=adjusted_by
        )

        return shift
