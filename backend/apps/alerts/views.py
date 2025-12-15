"""
Alert views - API endpoints for alert management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from apps.users.permissions import HasPermission
from .models import Alert, AlertConfiguration, UserAlertPreference
from .services import AlertService, AlertGeneratorService, AlertConfigurationService
from .serializers import (
    AlertSerializer,
    AlertListSerializer,
    AlertConfigurationSerializer,
    UserAlertPreferenceSerializer,
    AlertActionSerializer,
    BulkAlertActionSerializer,
    AlertFilterSerializer,
    AlertCountResponseSerializer
)


class AlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing alerts.
    Multi-tenant: only shows alerts for user's company.
    """
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'alerts:view'
    serializer_class = AlertSerializer
    queryset = Alert.objects.all()

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
