"""
Alert views - API endpoints for alert management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from apps.users.permissions import HasPermission
from .models import Alert, AlertConfiguration, UserAlertPreference, ActivityLog
from .services import AlertService, AlertGeneratorService, AlertConfigurationService, ActivityLogService
from .serializers import (
    AlertSerializer,
    AlertListSerializer,
    AlertConfigurationSerializer,
    UserAlertPreferenceSerializer,
    AlertActionSerializer,
    BulkAlertActionSerializer,
    AlertFilterSerializer,
    AlertCountResponseSerializer,
    ActivityLogSerializer,
    ActivityLogListSerializer,
    ActivityLogFilterSerializer,
)


class AlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing alerts.
    Multi-tenant: only shows alerts for user's company.

    Permission logic:
    - alerts:view: Access to all alert types
    - inventory:view: Access to stock-related alerts (low_stock, out_of_stock)
    - SuperAdmin: Access to platform alerts
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AlertSerializer
    queryset = Alert.objects.all()

    # Stock-related alert types that inventory users can see
    STOCK_ALERT_TYPES = ['low_stock', 'out_of_stock']

    def check_permissions(self, request):
        """
        Override to allow access based on alert type permissions.
        Users with inventory:view can access stock alerts.
        Users with alerts:view can access all alerts.
        """
        super().check_permissions(request)

        user = request.user

        # SuperAdmins can access everything
        if user.is_superuser:
            return

        # Check if user has alerts:view (full access)
        if user.has_permission('alerts:view'):
            return

        # Check if user has inventory:view (stock alerts only)
        if user.has_permission('inventory:view'):
            # Will be filtered in get_queryset to only show stock alerts
            return

        # No permission - raise 403
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("No tiene permiso para ver alertas.")

    def get_serializer_class(self):
        if self.action == 'list':
            return AlertListSerializer
        return AlertSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Multi-tenant filter: only show alerts for user's company
        user = self.request.user
        if hasattr(user, 'company_id') and user.company_id:
            queryset = queryset.filter(company_id=user.company_id)

        # Permission-based filtering:
        # Users with only inventory:view see only stock alerts
        if not user.is_superuser and not user.has_permission('alerts:view'):
            if user.has_permission('inventory:view'):
                queryset = queryset.filter(alert_type__in=self.STOCK_ALERT_TYPES)
            else:
                # No alerts permission at all - empty queryset
                queryset = queryset.none()

        return queryset.select_related(
            'branch', 'product', 'employee', 'read_by', 'resolved_by'
        ).order_by('-created_at')

    @extend_schema(
        summary="List alerts",
        description="Get a list of alerts with optional filtering.",
        parameters=[
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('alert_type', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('status', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('severity', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('is_read', OpenApiTypes.BOOL, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('limit', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: AlertListSerializer(many=True)}
    )
    def list(self, request):
        """List alerts with filtering."""
        serializer = AlertFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        alerts = AlertService.get_alerts(
            user=request.user,
            **serializer.validated_data
        )

        output_serializer = AlertListSerializer(alerts, many=True)
        return Response(output_serializer.data)

    @extend_schema(
        summary="Get unread alert counts",
        description="Get count of unread alerts grouped by severity.",
        parameters=[
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: AlertCountResponseSerializer}
    )
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """Get unread alert counts by severity."""
        branch_id = request.query_params.get('branch_id')
        if branch_id:
            branch_id = int(branch_id)

        counts = AlertService.get_unread_count(
            user=request.user,
            branch_id=branch_id
        )
        return Response(counts)

    @extend_schema(
        summary="Mark alert as read",
        description="Mark a single alert as read.",
        responses={200: AlertSerializer}
    )
    @action(detail=True, methods=['post'], url_path='read')
    def mark_read(self, request, pk=None):
        """Mark alert as read."""
        alert = AlertService.mark_as_read(
            alert_id=pk,
            user=request.user
        )
        serializer = AlertSerializer(alert)
        return Response(serializer.data)

    @extend_schema(
        summary="Mark all alerts as read",
        description="Mark all unread alerts as read.",
        parameters=[
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: {'type': 'object', 'properties': {'count': {'type': 'integer'}}}}
    )
    @action(detail=False, methods=['post'], url_path='read-all')
    def mark_all_read(self, request):
        """Mark all alerts as read."""
        branch_id = request.query_params.get('branch_id')
        if branch_id:
            branch_id = int(branch_id)

        count = AlertService.mark_all_as_read(
            user=request.user,
            branch_id=branch_id
        )
        return Response({'count': count})

    @extend_schema(
        summary="Acknowledge alert",
        description="Acknowledge an alert without resolving it.",
        responses={200: AlertSerializer}
    )
    @action(detail=True, methods=['post'], url_path='acknowledge')
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert."""
        alert = AlertService.acknowledge_alert(
            alert_id=pk,
            user=request.user
        )
        serializer = AlertSerializer(alert)
        return Response(serializer.data)

    @extend_schema(
        summary="Resolve alert",
        description="Resolve an alert with optional notes.",
        request=AlertActionSerializer,
        responses={200: AlertSerializer}
    )
    @action(detail=True, methods=['post'], url_path='resolve')
    def resolve(self, request, pk=None):
        """Resolve an alert."""
        serializer = AlertActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        alert = AlertService.resolve_alert(
            alert_id=pk,
            user=request.user,
            notes=serializer.validated_data.get('notes', '')
        )
        output_serializer = AlertSerializer(alert)
        return Response(output_serializer.data)

    @extend_schema(
        summary="Dismiss alert",
        description="Dismiss an alert without resolving.",
        responses={200: AlertSerializer}
    )
    @action(detail=True, methods=['post'], url_path='dismiss')
    def dismiss(self, request, pk=None):
        """Dismiss an alert."""
        alert = AlertService.dismiss_alert(
            alert_id=pk,
            user=request.user
        )
        serializer = AlertSerializer(alert)
        return Response(serializer.data)

    @extend_schema(
        summary="Bulk resolve alerts",
        description="Resolve multiple alerts at once.",
        request=BulkAlertActionSerializer,
        responses={200: {'type': 'object', 'properties': {'count': {'type': 'integer'}}}}
    )
    @action(detail=False, methods=['post'], url_path='bulk-resolve')
    def bulk_resolve(self, request):
        """Resolve multiple alerts."""
        serializer = BulkAlertActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        count = AlertService.bulk_resolve(
            alert_ids=serializer.validated_data['alert_ids'],
            user=request.user,
            notes=serializer.validated_data.get('notes', '')
        )
        return Response({'count': count})

    @extend_schema(
        summary="Generate alerts manually",
        description="Trigger alert generation (admin only).",
        responses={200: {'type': 'object', 'properties': {'alerts_created': {'type': 'integer'}}}}
    )
    @action(detail=False, methods=['post'], url_path='generate')
    def generate(self, request):
        """Manually trigger alert generation."""
        # Check for admin permission
        if not request.user.has_permission('alerts:create'):
            return Response(
                {'error': 'No tiene permiso para generar alertas'},
                status=status.HTTP_403_FORBIDDEN
            )

        alerts = AlertGeneratorService.generate_all_alerts()
        return Response({'alerts_created': len(alerts)})


class AlertConfigurationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing alert configurations.
    Multi-tenant: only shows configurations for user's company.
    """
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'settings:edit'
    serializer_class = AlertConfigurationSerializer
    queryset = AlertConfiguration.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()

        # Multi-tenant filter: only show configurations for user's company
        user = self.request.user
        if hasattr(user, 'company_id') and user.company_id:
            queryset = queryset.filter(company_id=user.company_id)

        return queryset.select_related('branch', 'category')

    @extend_schema(
        summary="Get global configuration",
        description="Get the global alert configuration.",
        responses={200: AlertConfigurationSerializer}
    )
    @action(detail=False, methods=['get'], url_path='global')
    def global_config(self, request):
        """Get global configuration."""
        config = AlertConfigurationService.get_configuration(scope='global')
        if config:
            serializer = AlertConfigurationSerializer(config)
            return Response(serializer.data)
        return Response({'message': 'No global configuration found'}, status=404)

    @extend_schema(
        summary="Get branch configuration",
        description="Get alert configuration for a specific branch.",
        parameters=[
            OpenApiParameter('branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=True),
        ],
        responses={200: AlertConfigurationSerializer}
    )
    @action(detail=False, methods=['get'], url_path='branch')
    def branch_config(self, request):
        """Get branch-specific configuration."""
        branch_id = request.query_params.get('branch_id')
        if not branch_id:
            return Response(
                {'error': 'branch_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        config = AlertConfigurationService.get_configuration(
            scope='branch',
            branch_id=int(branch_id)
        )
        if config:
            serializer = AlertConfigurationSerializer(config)
            return Response(serializer.data)
        return Response({'message': 'No configuration found for this branch'}, status=404)


class UserAlertPreferenceViewSet(viewsets.ViewSet):
    """
    ViewSet for managing user alert preferences.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get my preferences",
        description="Get current user's alert preferences.",
        responses={200: UserAlertPreferenceSerializer}
    )
    def list(self, request):
        """Get current user's alert preferences."""
        prefs = AlertConfigurationService.get_user_preferences(request.user)
        serializer = UserAlertPreferenceSerializer(prefs)
        return Response(serializer.data)

    @extend_schema(
        summary="Update my preferences",
        description="Update current user's alert preferences.",
        request=UserAlertPreferenceSerializer,
        responses={200: UserAlertPreferenceSerializer}
    )
    @action(detail=False, methods=['put', 'patch'], url_path='me')
    def me(self, request):
        """Update current user's alert preferences."""
        serializer = UserAlertPreferenceSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        prefs = AlertConfigurationService.update_user_preferences(
            request.user,
            **serializer.validated_data
        )
        output_serializer = UserAlertPreferenceSerializer(prefs)
        return Response(output_serializer.data)

    @extend_schema(
        summary="Update my preferences",
        description="Update current user's alert preferences.",
        request=UserAlertPreferenceSerializer,
        responses={200: UserAlertPreferenceSerializer}
    )
    def update(self, request, pk=None):
        """Update user's alert preferences."""
        serializer = UserAlertPreferenceSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        prefs = AlertConfigurationService.update_user_preferences(
            request.user,
            **serializer.validated_data
        )
        output_serializer = UserAlertPreferenceSerializer(prefs)
        return Response(output_serializer.data)

    @extend_schema(
        summary="Update my preferences (partial)",
        description="Partially update current user's alert preferences.",
        request=UserAlertPreferenceSerializer,
        responses={200: UserAlertPreferenceSerializer}
    )
    def partial_update(self, request, pk=None):
        """Partially update user's alert preferences."""
        return self.update(request, pk)


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing activity logs.
    Read-only - activity logs are created through the ActivityLogMixin.
    Multi-tenant: only shows logs for user's company.

    Access restricted to users with alerts:view permission (typically admins).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ActivityLogSerializer
    queryset = ActivityLog.objects.all()

    def get_permissions(self):
        """Only admins with alerts:view can see activity logs."""
        return [IsAuthenticated(), HasPermission('alerts:view')]

    def get_serializer_class(self):
        if self.action == 'list':
            return ActivityLogListSerializer
        return ActivityLogSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Multi-tenant filter: only show logs for user's company
        user = self.request.user
        if hasattr(user, 'company_id') and user.company_id:
            queryset = queryset.filter(company_id=user.company_id)
        else:
            # SuperAdmin without company sees nothing (or could see all)
            queryset = queryset.none()

        return queryset.select_related(
            'user', 'branch', 'read_by'
        ).order_by('-created_at')

    @extend_schema(
        summary="List activity logs",
        description="Get activity logs with optional filtering by module, action, or user.",
        parameters=[
            OpenApiParameter('module', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('action', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('user_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('is_read', OpenApiTypes.BOOL, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('limit', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('offset', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: ActivityLogListSerializer(many=True)}
    )
    def list(self, request):
        """List activity logs with filtering."""
        serializer = ActivityLogFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        user = request.user
        company = user.company if hasattr(user, 'company') else None

        if not company:
            return Response([])

        logs = ActivityLogService.get_activities(
            company=company,
            user=serializer.validated_data.get('user_id'),
            module=serializer.validated_data.get('module'),
            is_read=serializer.validated_data.get('is_read'),
            limit=serializer.validated_data.get('limit', 50),
            offset=serializer.validated_data.get('offset', 0)
        )

        output_serializer = ActivityLogListSerializer(logs, many=True)
        return Response(output_serializer.data)

    @extend_schema(
        summary="Get unread activity count",
        description="Get count of unread activity logs.",
        responses={200: {'type': 'object', 'properties': {'count': {'type': 'integer'}}}}
    )
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """Get unread activity log count."""
        user = request.user
        company = user.company if hasattr(user, 'company') else None

        if not company:
            return Response({'count': 0})

        count = ActivityLogService.get_unread_count(company)
        return Response({'count': count})

    @extend_schema(
        summary="Mark activity as read",
        description="Mark a single activity log as read.",
        responses={200: ActivityLogSerializer}
    )
    @action(detail=True, methods=['post'], url_path='read')
    def mark_read(self, request, pk=None):
        """Mark activity log as read."""
        success = ActivityLogService.mark_as_read(
            activity_id=pk,
            user=request.user
        )
        if success:
            activity = ActivityLog.objects.get(pk=pk)
            serializer = ActivityLogSerializer(activity)
            return Response(serializer.data)
        return Response(
            {'error': 'No se pudo marcar como leído'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        summary="Mark all activities as read",
        description="Mark all unread activity logs as read.",
        responses={200: {'type': 'object', 'properties': {'count': {'type': 'integer'}}}}
    )
    @action(detail=False, methods=['post'], url_path='read-all')
    def mark_all_read(self, request):
        """Mark all activity logs as read."""
        user = request.user
        company = user.company if hasattr(user, 'company') else None

        if not company:
            return Response({'count': 0})

        count = ActivityLogService.mark_all_as_read(company, user)
        return Response({'count': count})
