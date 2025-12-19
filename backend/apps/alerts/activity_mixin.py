"""
Activity logging mixin for Django REST Framework ViewSets.
Automatically logs CRUD operations to ActivityLog.
"""
from apps.alerts.services import ActivityLogService


class ActivityLogMixin:
    """
    Mixin para ViewSets que registra automáticamente las operaciones CRUD.

    Uso:
        class ProductViewSet(ActivityLogMixin, TenantQuerySetMixin, viewsets.ModelViewSet):
            activity_model_name = 'Producto'  # Nombre legible del modelo
            activity_name_field = 'name'  # Campo para obtener el nombre del objeto

    Configurable:
        activity_model_name: str - Nombre del modelo para el log (default: nombre del modelo)
        activity_name_field: str - Campo del modelo para obtener nombre descriptivo (default: 'name')
        activity_log_create: bool - Registrar creación (default: True)
        activity_log_update: bool - Registrar actualización (default: True)
        activity_log_delete: bool - Registrar eliminación (default: True)
    """

    activity_model_name = None
    activity_name_field = 'name'
    activity_log_create = True
    activity_log_update = True
    activity_log_delete = True

    def _get_model_name(self):
        """Obtiene el nombre del modelo para el log."""
        if self.activity_model_name:
            return self.activity_model_name
        if hasattr(self, 'queryset') and self.queryset is not None:
            return self.queryset.model.__name__
        return 'Objeto'

    def _get_object_name(self, obj):
        """Obtiene el nombre descriptivo del objeto."""
        if hasattr(obj, self.activity_name_field):
            return str(getattr(obj, self.activity_name_field, ''))
        if hasattr(obj, 'name'):
            return str(obj.name)
        if hasattr(obj, '__str__'):
            return str(obj)[:100]
        return f"#{obj.pk}"

    def _get_company(self, obj=None):
        """Obtiene la empresa del usuario o del objeto."""
        user = self.request.user
        if hasattr(user, 'company') and user.company:
            return user.company
        if obj and hasattr(obj, 'company'):
            return obj.company
        if obj and hasattr(obj, 'branch') and obj.branch:
            return obj.branch.company
        return None

    def _get_branch(self, obj=None):
        """Obtiene la sucursal del contexto o del objeto."""
        # Primero intenta obtener del request
        branch_id = self.request.query_params.get('branch') or self.request.data.get('branch')
        if branch_id:
            from apps.branches.models import Branch
            try:
                return Branch.objects.get(pk=branch_id)
            except Branch.DoesNotExist:
                pass

        # Luego del objeto
        if obj and hasattr(obj, 'branch'):
            return obj.branch

        return None

    def _get_action_type(self, action_name: str) -> str:
        """Determina el tipo de acción basado en el modelo y la operación."""
        model_name = self._get_model_name().lower()

        # Mapeo de modelo a prefijo de acción
        action_mapping = {
            'producto': 'product',
            'product': 'product',
            'venta': 'sale',
            'sale': 'sale',
            'empleado': 'employee',
            'employee': 'employee',
            'sucursal': 'branch',
            'branch': 'branch',
            'usuario': 'user',
            'user': 'user',
            'proveedor': 'supplier',
            'supplier': 'supplier',
            'orden de compra': 'purchase_order',
            'purchaseorder': 'purchase_order',
            'caja': 'cash_register',
            'cashregister': 'cash_register',
            'dailycashregister': 'cash_register',
            'turno': 'shift',
            'shift': 'shift',
        }

        prefix = action_mapping.get(model_name, model_name)

        if action_name == 'create':
            return f'{prefix}_created'
        elif action_name == 'update':
            return f'{prefix}_updated'
        elif action_name == 'delete':
            return f'{prefix}_deleted'

        return f'{prefix}_{action_name}'

    def _log_activity(self, action_name: str, obj, old_data: dict = None):
        """Registra la actividad en el log."""
        user = self.request.user
        company = self._get_company(obj)

        if not company:
            return

        model_name = self._get_model_name()
        object_name = self._get_object_name(obj)
        action_type = self._get_action_type(action_name)

        # Construir descripción
        user_display = f"{user.first_name} {user.last_name}".strip() or user.email
        if action_name == 'create':
            description = f"{user_display} creó {model_name.lower()}: {object_name}"
        elif action_name == 'update':
            description = f"{user_display} modificó {model_name.lower()}: {object_name}"
        elif action_name == 'delete':
            description = f"{user_display} eliminó {model_name.lower()}: {object_name}"
        else:
            description = f"{user_display} realizó {action_name} en {model_name.lower()}: {object_name}"

        # Metadata con cambios
        metadata = {}
        if old_data and action_name == 'update':
            changes = {}
            for field, old_value in old_data.items():
                new_value = getattr(obj, field, None)
                if old_value != new_value:
                    changes[field] = {'old': str(old_value), 'new': str(new_value)}
            if changes:
                metadata['changes'] = changes

        try:
            ActivityLogService.log(
                action=action_type,
                user=user,
                company=company,
                description=description,
                branch=self._get_branch(obj),
                target_type=obj.__class__.__name__,
                target_id=obj.pk,
                target_name=object_name,
                metadata=metadata
            )
        except Exception:
            # No interrumpir la operación principal si falla el log
            pass

    def perform_create(self, serializer):
        """Override para registrar creación."""
        super().perform_create(serializer)
        if self.activity_log_create:
            self._log_activity('create', serializer.instance)

    def perform_update(self, serializer):
        """Override para registrar actualización con cambios."""
        # Capturar datos antes del update
        old_data = {}
        if self.activity_log_update and serializer.instance:
            for field in serializer.validated_data.keys():
                if hasattr(serializer.instance, field):
                    old_data[field] = getattr(serializer.instance, field)

        super().perform_update(serializer)

        if self.activity_log_update:
            self._log_activity('update', serializer.instance, old_data)

    def perform_destroy(self, instance):
        """Override para registrar eliminación."""
        if self.activity_log_delete:
            # Registrar antes de eliminar para tener acceso al objeto
            self._log_activity('delete', instance)
        super().perform_destroy(instance)
