"""
Custom User model with role-based permissions.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from core.mixins import TimestampMixin


class Permission(models.Model):
    """Granular permissions for the system."""
    MODULES = [
        ('dashboard', 'Dashboard'),
        ('inventory', 'Inventario'),
        ('sales', 'Ventas'),
        ('employees', 'Empleados'),
        ('suppliers', 'Proveedores'),
        ('reports', 'Reportes'),
        ('settings', 'Configuración'),
        ('branches', 'Sucursales'),
        ('alerts', 'Alertas'),
    ]

    ACTIONS = [
        ('view', 'Ver'),
        ('create', 'Crear'),
        ('edit', 'Editar'),
        ('delete', 'Eliminar'),
        ('export', 'Exportar'),
        ('void', 'Anular'),
        ('transfer', 'Transferir'),
    ]

    code = models.CharField(max_length=100, unique=True, verbose_name='Código')
    name = models.CharField(max_length=100, verbose_name='Nombre')
    module = models.CharField(max_length=50, choices=MODULES, verbose_name='Módulo')
    action = models.CharField(max_length=50, choices=ACTIONS, verbose_name='Acción')
    description = models.TextField(blank=True, verbose_name='Descripción')

    class Meta:
        db_table = 'permissions'
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'
        ordering = ['module', 'action']

    def __str__(self):
        return f"{self.module}:{self.action}"

    @classmethod
    def create_default_permissions(cls):
        """Create default permissions for all modules and actions."""
        for module_code, module_name in cls.MODULES:
            for action_code, action_name in cls.ACTIONS:
                code = f"{module_code}:{action_code}"
                name = f"{action_name} {module_name}"
                cls.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'module': module_code,
                        'action': action_code,
                    }
                )


class Role(TimestampMixin):
    """User roles with associated permissions."""
    ROLE_TYPES = [
        ('admin', 'Administrador'),
        ('supervisor', 'Supervisor'),
        ('cashier', 'Cajero'),
        ('warehouse', 'Almacenista'),
        ('viewer', 'Solo Lectura'),
    ]

    name = models.CharField(max_length=50, unique=True, verbose_name='Nombre')
    role_type = models.CharField(
        max_length=20,
        choices=ROLE_TYPES,
        default='viewer',
        verbose_name='Tipo de rol'
    )
    description = models.TextField(blank=True, verbose_name='Descripción')
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='roles',
        verbose_name='Permisos'
    )
    is_active = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        db_table = 'roles'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['name']

    def __str__(self):
        return self.name

    @classmethod
    def create_default_roles(cls):
        """Create default roles with appropriate permissions."""
        # Admin - all permissions
        admin, _ = cls.objects.get_or_create(
            role_type='admin',
            defaults={
                'name': 'Administrador',
                'description': 'Acceso completo al sistema'
            }
        )
        admin.permissions.set(Permission.objects.all())

        # Supervisor - most permissions except settings
        supervisor, _ = cls.objects.get_or_create(
            role_type='supervisor',
            defaults={
                'name': 'Supervisor',
                'description': 'Gestión de operaciones diarias'
            }
        )
        supervisor.permissions.set(
            Permission.objects.exclude(module='settings').exclude(action='delete')
        )

        # Cashier - sales and inventory view
        cashier, _ = cls.objects.get_or_create(
            role_type='cashier',
            defaults={
                'name': 'Cajero',
                'description': 'Operaciones de punto de venta'
            }
        )
        cashier.permissions.set(
            Permission.objects.filter(
                models.Q(module='sales') |
                models.Q(module='inventory', action='view') |
                models.Q(module='dashboard', action='view')
            )
        )

        # Warehouse - inventory management
        warehouse, _ = cls.objects.get_or_create(
            role_type='warehouse',
            defaults={
                'name': 'Almacenista',
                'description': 'Gestión de inventario'
            }
        )
        warehouse.permissions.set(
            Permission.objects.filter(
                models.Q(module='inventory') |
                models.Q(module='suppliers', action='view') |
                models.Q(module='dashboard', action='view')
            )
        )

        # Viewer - read-only access
        viewer, _ = cls.objects.get_or_create(
            role_type='viewer',
            defaults={
                'name': 'Solo Lectura',
                'description': 'Acceso de solo lectura'
            }
        )
        viewer.permissions.set(
            Permission.objects.filter(action='view')
        )


class UserManager(BaseUserManager):
    """Custom user manager."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, TimestampMixin):
    """Custom User model with email as username."""

    username = None  # Remove username field
    email = models.EmailField(unique=True, verbose_name='Email')
    first_name = models.CharField(max_length=150, verbose_name='Nombre')
    last_name = models.CharField(max_length=150, verbose_name='Apellido')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Avatar'
    )

    # Multi-tenant: company association
    # NULL company = SuperAdmin de plataforma
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Empresa',
        help_text='NULL para SuperAdmin de plataforma'
    )
    is_company_admin = models.BooleanField(
        default=False,
        verbose_name='Admin de empresa',
        help_text='Puede gestionar toda su empresa'
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Rol'
    )
    default_branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_users',
        verbose_name='Sucursal por defecto'
    )
    allowed_branches = models.ManyToManyField(
        'branches.Branch',
        blank=True,
        related_name='allowed_users',
        verbose_name='Sucursales permitidas'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def has_permission(self, permission_code: str) -> bool:
        """Check if user has a specific permission."""
        if self.is_superuser:
            return True
        if not self.role:
            return False
        return self.role.permissions.filter(code=permission_code).exists()

    def has_module_permission(self, module: str) -> bool:
        """Check if user has any permission for a module."""
        if self.is_superuser:
            return True
        if not self.role:
            return False
        return self.role.permissions.filter(module=module).exists()

    def get_permissions(self) -> list:
        """Get list of permission codes for the user."""
        if self.is_superuser:
            return list(Permission.objects.values_list('code', flat=True))
        if not self.role:
            return []
        return list(self.role.permissions.values_list('code', flat=True))

    def can_access_branch(self, branch_id: int) -> bool:
        """Check if user can access a specific branch."""
        if self.is_superuser:
            return True
        return self.allowed_branches.filter(id=branch_id).exists()
