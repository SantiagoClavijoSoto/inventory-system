"""
Reusable model mixins for audit trails and common functionality.
"""
from django.db import models
from django.conf import settings


class TimestampMixin(models.Model):
    """Adds created_at and updated_at timestamps to models."""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        abstract = True


class AuditMixin(TimestampMixin):
    """Adds audit fields including user who created/updated the record."""
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name='Creado por'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name='Actualizado por'
    )

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """Adds soft delete capability to models."""
    is_deleted = models.BooleanField(default=False, verbose_name='Eliminado')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de eliminación')
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deleted',
        verbose_name='Eliminado por'
    )

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        """Soft delete the instance."""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        """Restore a soft-deleted instance."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


class ActiveManager(models.Manager):
    """Manager that returns only non-deleted objects."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class TenantQuerySetMixin:
    """
    ViewSet mixin that automatically filters querysets by company.

    Usage:
        # Direct company FK
        class ProductViewSet(TenantQuerySetMixin, viewsets.ModelViewSet):
            queryset = Product.objects.all()
            # Queryset will be auto-filtered by user's company

        # Indirect company FK (through related model)
        class EmployeeViewSet(TenantQuerySetMixin, viewsets.ModelViewSet):
            queryset = Employee.objects.all()
            tenant_field = 'branch__company'  # Filter through branch

    The mixin gets the company directly from the authenticated user
    (works with DRF's authentication which happens at view time, not middleware).

    SuperAdmins (is_superuser=True) see all data across companies.

    Attributes:
        tenant_field: Optional path to company field. Defaults to 'company'.
                     Use '__' for related fields (e.g., 'branch__company').
    """

    # Configurable field path to company (default: direct 'company' FK)
    tenant_field = 'company'

    def _get_tenant_company(self):
        """Get the company from the authenticated user."""
        if not hasattr(self, 'request') or not self.request:
            return None, False

        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:
            return None, False

        # SuperAdmin (platform owner) sees all data
        if user.is_superuser:
            return None, True  # (company=None, is_platform_admin=True)

        # Regular user - return their company
        return getattr(user, 'company', None), False

    def get_queryset(self):
        queryset = super().get_queryset()

        company, is_platform_admin = self._get_tenant_company()

        # SuperAdmin sees all data
        if is_platform_admin:
            return queryset

        # Filter by user's company
        if company:
            # Use configured tenant_field for filtering
            tenant_field = getattr(self, 'tenant_field', 'company')

            # Check if model has the field (for direct FK) or allow related lookups
            model = queryset.model
            field_name = tenant_field.split('__')[0]  # Get base field name
            if hasattr(model, field_name):
                return queryset.filter(**{tenant_field: company})

        return queryset

    def perform_create(self, serializer):
        """Auto-assign company on create if not specified."""
        company, _ = self._get_tenant_company()
        if company and hasattr(serializer.Meta.model, 'company'):
            serializer.save(company=company)
        else:
            serializer.save()
