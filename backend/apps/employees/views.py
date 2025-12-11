"""
API Views for Employee module.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from datetime import datetime

from apps.users.permissions import HasPermission
from apps.branches.models import Branch
from .models import Employee, Shift
from .serializers import (
    EmployeeListSerializer,
    EmployeeDetailSerializer,
    CreateEmployeeSerializer,
    UpdateEmployeeSerializer,
    ShiftSerializer,
    ClockInSerializer,
    ClockOutSerializer,
    ManualShiftSerializer,
    EmployeeStatsSerializer,
    ShiftSummarySerializer,
)
from .services import EmployeeService, ShiftService


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing employees.

    list: Get all employees (filtered by branch)
    retrieve: Get employee details with current shift info
    create: Create new employee with user account
    update: Update employee information
    destroy: Soft delete employee
    terminate: Terminate employment
    stats: Get employee statistics
    sales: Get employee's sales history
    """
    queryset = Employee.objects.select_related('user', 'branch').filter(is_deleted=False)
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        elif self.action == 'create':
            return CreateEmployeeSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateEmployeeSerializer
        return EmployeeDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Filter by branch if not admin
        if user.role and user.role.role_type != 'admin':
            if user.allowed_branches.exists():
                queryset = queryset.filter(branch__in=user.allowed_branches.all())
            elif user.default_branch:
                queryset = queryset.filter(branch=user.default_branch)

        # Apply filters
        branch_id = self.request.query_params.get('branch')
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        employment_type = self.request.query_params.get('employment_type')
        if employment_type:
            queryset = queryset.filter(employment_type=employment_type)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(employee_code__icontains=search) |
                Q(position__icontains=search)
            )

        return queryset.order_by('user__first_name', 'user__last_name')

    def get_permissions(self):
        if self.action in ['create', 'terminate']:
            self.permission_classes = [IsAuthenticated, HasPermission('employees:create')]
        elif self.action in ['update', 'partial_update']:
            self.permission_classes = [IsAuthenticated, HasPermission('employees:edit')]
        elif self.action == 'destroy':
            self.permission_classes = [IsAuthenticated, HasPermission('employees:delete')]
        elif self.action in ['list', 'retrieve', 'stats', 'sales']:
            self.permission_classes = [IsAuthenticated, HasPermission('employees:view')]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """Create a new employee with user account."""
        serializer = CreateEmployeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        branch = get_object_or_404(Branch, id=data['branch_id'], is_active=True)

        # Get role if provided
        role = None
        if data.get('role_id'):
            from apps.users.models import Role
            role = get_object_or_404(Role, id=data['role_id'], is_active=True)

        try:
            employee = EmployeeService.create_employee(
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone=data.get('phone', ''),
                role=role,
                branch=branch,
                position=data['position'],
                department=data.get('department', ''),
                employment_type=data.get('employment_type', 'full_time'),
                hire_date=data['hire_date'],
                salary=data.get('salary', 0),
                hourly_rate=data.get('hourly_rate', 0),
                emergency_contact_name=data.get('emergency_contact_name', ''),
                emergency_contact_phone=data.get('emergency_contact_phone', ''),
                address=data.get('address', ''),
                tax_id=data.get('tax_id', ''),
                social_security_number=data.get('social_security_number', ''),
                notes=data.get('notes', ''),
            )

            return Response(
                EmployeeDetailSerializer(employee).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        """Soft delete an employee."""
        employee = self.get_object()
        employee.soft_delete(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        """Terminate an employee."""
        employee = self.get_object()

        termination_date = request.data.get('termination_date')
        if termination_date:
            termination_date = datetime.strptime(termination_date, '%Y-%m-%d').date()

        reason = request.data.get('reason', '')

        try:
            employee = EmployeeService.terminate_employee(
                employee=employee,
                termination_date=termination_date,
                reason=reason
            )
            return Response(EmployeeDetailSerializer(employee).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get employee statistics."""
        employee = self.get_object()

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()

        stats = EmployeeService.get_employee_stats(
            employee=employee,
            date_from=date_from,
            date_to=date_to
        )

        serializer = EmployeeStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def sales(self, request, pk=None):
        """Get employee's sales history."""
        employee = self.get_object()

        from apps.sales.models import Sale
        from apps.sales.serializers import SaleSerializer

        sales = Sale.objects.filter(
            cashier=employee.user
        ).select_related('branch').prefetch_related('items')

        # Apply date filters
        date_from = request.query_params.get('date_from')
        if date_from:
            sales = sales.filter(created_at__date__gte=date_from)

        date_to = request.query_params.get('date_to')
        if date_to:
            sales = sales.filter(created_at__date__lte=date_to)

        sales = sales.order_by('-created_at')[:50]  # Limit to 50 most recent

        serializer = SaleSerializer(sales, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def shifts(self, request, pk=None):
        """Get employee's shift history."""
        employee = self.get_object()

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()

        shifts = ShiftService.get_employee_shifts(
            employee=employee,
            date_from=date_from,
            date_to=date_to
        )[:50]  # Limit to 50 most recent

        serializer = ShiftSerializer(shifts, many=True)
        return Response(serializer.data)


class ShiftViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing shifts.

    list: Get all shifts (filtered)
    retrieve: Get shift details
    create: Create manual shift entry
    clock_in: Clock in current user
    clock_out: Clock out current user
    start_break: Start break
    end_break: End break
    daily_summary: Get daily shift summary
    """
    queryset = Shift.objects.select_related('employee', 'employee__user', 'branch')
    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Filter by branch if not admin
        if user.role and user.role.role_type != 'admin':
            if user.allowed_branches.exists():
                queryset = queryset.filter(branch__in=user.allowed_branches.all())
            elif user.default_branch:
                queryset = queryset.filter(branch=user.default_branch)

        # Apply filters
        branch_id = self.request.query_params.get('branch')
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        employee_id = self.request.query_params.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(clock_in__date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(clock_in__date__lte=date_to)

        is_complete = self.request.query_params.get('is_complete')
        if is_complete is not None:
            if is_complete.lower() in ['true', '1']:
                queryset = queryset.filter(clock_out__isnull=False)
            else:
                queryset = queryset.filter(clock_out__isnull=True)

        return queryset.order_by('-clock_in')

    def create(self, request, *args, **kwargs):
        """Create a manual shift entry."""
        serializer = ManualShiftSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        shift = serializer.save()
        return Response(
            ShiftSerializer(shift).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['post'])
    def clock_in(self, request):
        """Clock in the current user."""
        # Get employee profile for current user
        try:
            employee = request.user.employee_profile
        except Employee.DoesNotExist:
            return Response(
                {'error': 'No tiene perfil de empleado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ClockInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        branch_id = serializer.validated_data.get('branch_id')
        branch = None
        if branch_id:
            branch = get_object_or_404(Branch, id=branch_id, is_active=True)

        try:
            shift = ShiftService.clock_in(employee=employee, branch=branch)
            return Response(
                ShiftSerializer(shift).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def clock_out(self, request):
        """Clock out the current user."""
        try:
            employee = request.user.employee_profile
        except Employee.DoesNotExist:
            return Response(
                {'error': 'No tiene perfil de empleado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ClockOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            shift = ShiftService.clock_out(
                employee=employee,
                notes=serializer.validated_data.get('notes', '')
            )
            return Response(ShiftSerializer(shift).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def start_break(self, request):
        """Start a break for the current user."""
        try:
            employee = request.user.employee_profile
        except Employee.DoesNotExist:
            return Response(
                {'error': 'No tiene perfil de empleado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            shift = ShiftService.start_break(employee=employee)
            return Response(ShiftSerializer(shift).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def end_break(self, request):
        """End a break for the current user."""
        try:
            employee = request.user.employee_profile
        except Employee.DoesNotExist:
            return Response(
                {'error': 'No tiene perfil de empleado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            shift = ShiftService.end_break(employee=employee)
            return Response(ShiftSerializer(shift).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current user's active shift."""
        try:
            employee = request.user.employee_profile
        except Employee.DoesNotExist:
            return Response(
                {'error': 'No tiene perfil de empleado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        current_shift = employee.get_current_shift()

        if current_shift:
            return Response(ShiftSerializer(current_shift).data)
        return Response(
            {'message': 'No tiene turno activo'},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=False, methods=['get'])
    def daily_summary(self, request):
        """Get daily shift summary for a branch."""
        branch_id = request.query_params.get('branch') or request.user.default_branch_id
        if not branch_id:
            return Response(
                {'error': 'No se especificó una sucursal'},
                status=status.HTTP_400_BAD_REQUEST
            )

        branch = get_object_or_404(Branch, id=branch_id)

        date_str = request.query_params.get('date')
        target_date = None
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        summary = ShiftService.get_daily_summary(branch, target_date)
        serializer = ShiftSummarySerializer(summary)
        return Response(serializer.data)
