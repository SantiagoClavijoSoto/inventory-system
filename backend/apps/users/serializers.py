"""
Serializers for user authentication and management.
"""
from datetime import date
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Role, Permission
from apps.companies.models import Company
from apps.employees.models import Employee
from apps.branches.models import Branch


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for Permission model."""

    class Meta:
        model = Permission
        fields = ['id', 'code', 'name', 'module', 'action', 'description']


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        write_only=True,
        source='permissions',
        required=False
    )

    class Meta:
        model = Role
        fields = [
            'id', 'name', 'role_type', 'description',
            'permissions', 'permission_ids', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class RoleSimpleSerializer(serializers.ModelSerializer):
    """Simple serializer for Role (without permissions detail)."""

    class Meta:
        model = Role
        fields = ['id', 'name', 'role_type']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    role = RoleSimpleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.filter(is_active=True),
        write_only=True,
        source='role',
        required=False
    )
    role_name = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    full_name = serializers.CharField(read_only=True)
    is_platform_admin = serializers.SerializerMethodField()
    # Company info for SuperAdmin view
    company_id = serializers.IntegerField(source='company.id', read_only=True, allow_null=True)
    company_name = serializers.CharField(source='company.name', read_only=True, allow_null=True)
    is_company_admin = serializers.BooleanField(read_only=True)
    # Branch info
    default_branch_name = serializers.SerializerMethodField()

    # Permission flags
    can_create_roles = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'avatar', 'role', 'role_id', 'role_name', 'permissions',
            'default_branch', 'default_branch_name', 'allowed_branches', 'is_active',
            'is_platform_admin', 'is_company_admin', 'can_create_roles',
            'must_change_password',
            'company_id', 'company_name',
            'created_at', 'updated_at', 'last_login'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_login']
        extra_kwargs = {
            'allowed_branches': {'required': False}
        }

    def get_role_name(self, obj):
        return obj.role.name if obj.role else None

    def get_default_branch_name(self, obj):
        return obj.default_branch.name if obj.default_branch else None

    def get_permissions(self, obj):
        return obj.get_permissions()

    def get_is_platform_admin(self, obj):
        """Return True if user is a platform superadmin (no company assigned)."""
        return obj.is_superuser and obj.company_id is None


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users.

    SuperAdmin can specify company_id to assign the user to a company.
    Regular admins create users within their own company (handled by mixin).
    Optionally creates an Employee profile if is_employee=True.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.filter(is_active=True),
        write_only=True,
        source='role',
        required=False
    )
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.active_objects.all(),
        write_only=True,
        source='company',
        required=False,
        help_text='Company ID (only for SuperAdmin)'
    )
    # Employee fields (optional)
    is_employee = serializers.BooleanField(
        write_only=True,
        required=False,
        default=False,
        help_text='Si es True, crea un perfil de empleado asociado'
    )
    employee_position = serializers.CharField(
        write_only=True,
        required=False,
        max_length=100,
        help_text='Puesto del empleado (requerido si is_employee=True)'
    )
    employee_branch_id = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.filter(is_active=True),
        write_only=True,
        required=False,
        help_text='Sucursal del empleado (requerido si is_employee=True)'
    )
    employment_type = serializers.ChoiceField(
        choices=Employee.EMPLOYMENT_TYPE_CHOICES,
        write_only=True,
        required=False,
        default='full_time',
        help_text='Tipo de empleo'
    )
    hire_date = serializers.DateField(
        write_only=True,
        required=False,
        help_text='Fecha de contratación (default: hoy)'
    )

    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone',
            'role_id', 'default_branch', 'allowed_branches',
            'company_id',
            # Employee fields
            'is_employee', 'employee_position', 'employee_branch_id',
            'employment_type', 'hire_date',
        ]

    def validate(self, attrs):
        if attrs.get('password') != attrs.pop('password_confirm', None):
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden.'
            })

        # If SuperAdmin is creating, company_id is required
        request = self.context.get('request')
        if request and request.user.is_superuser:
            if not attrs.get('company'):
                raise serializers.ValidationError({
                    'company_id': 'Debe especificar una empresa para el usuario.'
                })

        # Validate employee fields if is_employee=True
        if attrs.get('is_employee'):
            if not attrs.get('employee_position'):
                raise serializers.ValidationError({
                    'employee_position': 'El puesto es requerido para empleados.'
                })
            # Branch is optional - employee will be created without it if not provided

            # Validate branch belongs to user's company (if provided)
            branch = attrs.get('employee_branch_id')
            if branch:
                company = attrs.get('company')
                if request and not request.user.is_superuser:
                    company = request.user.company

                if company and branch.company_id != company.id:
                    raise serializers.ValidationError({
                        'employee_branch_id': 'La sucursal no pertenece a la empresa del usuario.'
                    })

        return attrs

    def create(self, validated_data):
        allowed_branches = validated_data.pop('allowed_branches', [])
        password = validated_data.pop('password')

        # Extract employee fields
        is_employee = validated_data.pop('is_employee', False)
        employee_position = validated_data.pop('employee_position', None)
        employee_branch = validated_data.pop('employee_branch_id', None)
        employment_type = validated_data.pop('employment_type', 'full_time')
        hire_date = validated_data.pop('hire_date', None) or date.today()

        # Check if SuperAdmin is creating this user
        request = self.context.get('request')
        is_superadmin_creating = request and request.user.is_superuser

        user = User(**validated_data)
        user.set_password(password)

        # If SuperAdmin creates user with company, mark as company admin
        if is_superadmin_creating and user.company_id:
            user.is_company_admin = True

        # Force password change on first login
        user.must_change_password = True

        user.save()
        if allowed_branches:
            user.allowed_branches.set(allowed_branches)

        # Create Employee profile if requested
        if is_employee and employee_position:
            # Generate employee code - use branch code if available, else company or default
            if employee_branch:
                employee_code = Employee.generate_employee_code(employee_branch.code)
            else:
                # Use company slug or default prefix for employees without branch
                company = validated_data.get('company')
                if not company and request and not request.user.is_superuser:
                    company = request.user.company
                prefix = company.slug[:3].upper() if company else 'EMP'
                employee_code = Employee.generate_employee_code(prefix)

            Employee.objects.create(
                user=user,
                employee_code=employee_code,
                position=employee_position,
                branch=employee_branch,  # Can be None - will be assigned later
                employment_type=employment_type,
                hire_date=hire_date,
                status='active',
            )

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users."""
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.filter(is_active=True),
        write_only=True,
        source='role',
        required=False
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'avatar',
            'role_id', 'default_branch', 'allowed_branches', 'is_active'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    current_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('La contraseña actual es incorrecta.')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Las contraseñas no coinciden.'
            })
        return attrs


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            email=email,
            password=password
        )

        if not user:
            raise serializers.ValidationError(
                'Credenciales inválidas.',
                code='authorization'
            )

        if not user.is_active:
            raise serializers.ValidationError(
                'Esta cuenta está desactivada.',
                code='authorization'
            )

        attrs['user'] = user
        return attrs


class LoginResponseSerializer(serializers.Serializer):
    """Serializer for login response."""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class TokenRefreshResponseSerializer(serializers.Serializer):
    """Serializer for token refresh response."""
    access = serializers.CharField()
