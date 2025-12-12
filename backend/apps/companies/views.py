"""
Views for companies app.
SuperAdmin only - platform-level company management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Company
from .serializers import (
    CompanySerializer,
    CompanyListSerializer,
    CompanyCreateSerializer,
    CompanySimpleSerializer,
)
from .permissions import IsSuperUser


@extend_schema_view(
    list=extend_schema(tags=['Empresas (Admin)']),
    create=extend_schema(tags=['Empresas (Admin)']),
    retrieve=extend_schema(tags=['Empresas (Admin)']),
    update=extend_schema(tags=['Empresas (Admin)']),
    partial_update=extend_schema(tags=['Empresas (Admin)']),
    destroy=extend_schema(tags=['Empresas (Admin)']),
)
class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for platform-level company management.
    Only accessible by SuperAdmins (platform administrators).
    """
    queryset = Company.active_objects.all()
    permission_classes = [IsAuthenticated, IsSuperUser]
    filterset_fields = ['plan', 'is_active']
    search_fields = ['name', 'slug', 'email', 'legal_name']
    ordering_fields = ['name', 'created_at', 'plan']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'create':
            return CompanyCreateSerializer
        if self.action == 'list':
            return CompanyListSerializer
        return CompanySerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Include inactive if requested
        if self.request.query_params.get('include_inactive') == 'true':
            queryset = Company.objects.filter(is_deleted=False)

        return queryset

    def perform_destroy(self, instance):
        """Soft delete the company."""
        instance.soft_delete(user=self.request.user)

    @extend_schema(
        tags=['Empresas (Admin)'],
        responses={200: CompanySerializer}
    )
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a company."""
        company = self.get_object()
        company.is_active = True
        company.save(update_fields=['is_active'])
        serializer = CompanySerializer(company)
        return Response(serializer.data)

    @extend_schema(
        tags=['Empresas (Admin)'],
        responses={200: CompanySerializer}
    )
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a company (keeps data but blocks access)."""
        company = self.get_object()
        company.is_active = False
        company.save(update_fields=['is_active'])
        serializer = CompanySerializer(company)
        return Response(serializer.data)

    @extend_schema(tags=['Empresas (Admin)'])
    @action(detail=False, methods=['get'])
    def simple(self, request):
        """Get simple list of companies for dropdowns."""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = CompanySimpleSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(tags=['Empresas (Admin)'])
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get detailed statistics for a company."""
        company = self.get_object()

        stats = {
            'company': CompanySerializer(company).data,
            'limits': company.get_plan_limits(),
            'usage': {
                'branches_used': company.branch_count,
                'branches_remaining': company.max_branches - company.branch_count,
                'users_used': company.user_count,
                'users_remaining': company.max_users - company.user_count,
                'products_used': company.product_count,
                'products_remaining': company.max_products - company.product_count,
            },
            'can_add': {
                'branch': company.can_add_branch(),
                'user': company.can_add_user(),
                'product': company.can_add_product(),
            }
        }

        return Response(stats)
