"""
Views for user authentication and management.
"""
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, extend_schema_view

from core.mixins import TenantQuerySetMixin
from .models import User, Role, Permission, EmailVerificationCode
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    LoginResponseSerializer,
    RoleSerializer,
    PermissionSerializer,
    TokenRefreshResponseSerializer,
    VerifyEmailSerializer,
    ResendVerificationSerializer,
)
from .permissions import HasPermission
from .tasks import trigger_verification_email


class LoginRateThrottle(AnonRateThrottle):
    """Throttle for login attempts - 5 per minute."""
    scope = 'login'


@extend_schema(tags=['Autenticación'])
class LoginView(APIView):
    """User login endpoint."""
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]
    serializer_class = LoginSerializer

    @extend_schema(
        request=LoginSerializer,
        responses={200: LoginResponseSerializer}
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })


@extend_schema(tags=['Autenticación'])
class LogoutView(APIView):
    """User logout - blacklists the refresh token."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={'type': 'object', 'properties': {'refresh': {'type': 'string'}}},
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Sesión cerrada exitosamente.'})
        except TokenError:
            return Response(
                {'error': 'Token inválido.'},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(tags=['Autenticación'])
class CustomTokenRefreshView(TokenRefreshView):
    """Custom token refresh view with extended schema."""

    @extend_schema(
        responses={200: TokenRefreshResponseSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@extend_schema(tags=['Autenticación'])
class MeView(generics.RetrieveUpdateAPIView):
    """Get or update current user profile."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer


@extend_schema(tags=['Autenticación'])
class ChangePasswordView(APIView):
    """Change password for current user."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.must_change_password = False  # Reset flag after password change
        user.save(update_fields=['password', 'must_change_password'])

        # Update session to prevent logout
        update_session_auth_hash(request, user)

        return Response({'message': 'Contraseña actualizada exitosamente.'})


class VerificationRateThrottle(AnonRateThrottle):
    """Throttle for verification attempts - 10 per minute."""
    scope = 'verification'


@extend_schema(tags=['Autenticación'])
class VerifyEmailView(APIView):
    """Verify user email with 6-digit code."""
    permission_classes = [AllowAny]
    throttle_classes = [VerificationRateThrottle]
    serializer_class = VerifyEmailSerializer

    @extend_schema(
        request=VerifyEmailSerializer,
        responses={
            200: {'type': 'object', 'properties': {
                'access': {'type': 'string'},
                'refresh': {'type': 'string'},
                'user': {'type': 'object'},
            }},
            400: {'type': 'object', 'properties': {'error': {'type': 'string'}}},
        }
    )
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        # Find user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.email_verified:
            return Response(
                {'error': 'El email ya ha sido verificado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find valid verification code
        verification = EmailVerificationCode.objects.filter(
            user=user,
            is_used=False
        ).order_by('-created_at').first()

        if not verification:
            return Response(
                {'error': 'No hay código de verificación activo. Solicita uno nuevo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not verification.is_valid:
            if verification.is_expired:
                return Response(
                    {'error': 'El código ha expirado. Solicita uno nuevo.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if verification.attempts >= EmailVerificationCode.MAX_ATTEMPTS:
                return Response(
                    {'error': 'Demasiados intentos fallidos. Solicita un nuevo código.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Check code
        if verification.code != code:
            verification.increment_attempts()
            remaining = EmailVerificationCode.MAX_ATTEMPTS - verification.attempts
            return Response(
                {'error': f'Código incorrecto. Te quedan {remaining} intentos.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Success - verify email and mark code as used
        verification.mark_as_used()
        user.email_verified = True
        user.save(update_fields=['email_verified'])

        # Generate JWT tokens for immediate login
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Email verificado exitosamente.',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })


@extend_schema(tags=['Autenticación'])
class ResendVerificationView(APIView):
    """Resend verification code to user email."""
    permission_classes = [AllowAny]
    throttle_classes = [VerificationRateThrottle]
    serializer_class = ResendVerificationSerializer

    @extend_schema(
        request=ResendVerificationSerializer,
        responses={
            200: {'type': 'object', 'properties': {'message': {'type': 'string'}}},
            400: {'type': 'object', 'properties': {'error': {'type': 'string'}}},
        }
    )
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if user exists
            return Response({'message': 'Si el email existe, se enviará un nuevo código.'})

        if user.email_verified:
            return Response(
                {'error': 'El email ya ha sido verificado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Send new verification email (sync in dev, async in prod)
        trigger_verification_email(user.id)

        return Response({'message': 'Si el email existe, se enviará un nuevo código.'})


@extend_schema_view(
    list=extend_schema(tags=['Usuarios']),
    create=extend_schema(tags=['Usuarios']),
    retrieve=extend_schema(tags=['Usuarios']),
    update=extend_schema(tags=['Usuarios']),
    partial_update=extend_schema(tags=['Usuarios']),
    destroy=extend_schema(tags=['Usuarios']),
)
class UserViewSet(TenantQuerySetMixin, viewsets.ModelViewSet):
    """ViewSet for user management (admin only).

    Multi-tenant: Users are filtered by company automatically via TenantQuerySetMixin.
    SuperAdmins can only see company administrators (not all users).
    """
    queryset = User.objects.select_related('role', 'company', 'default_branch').prefetch_related('allowed_branches')
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'settings:view'
    tenant_field = 'company'  # Filter users by their company
    filterset_fields = ['is_active', 'role', 'default_branch']
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['created_at', 'first_name', 'last_name']
    ordering = ['-created_at']

    def get_queryset(self):
        """Override to filter admins only for SuperAdmin."""
        queryset = super().get_queryset()

        # SuperAdmin only sees company administrators
        if self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(is_company_admin=True) | Q(role__role_type='admin'),
                company__isnull=False  # Only users assigned to a company
            )

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.required_permission = 'settings:edit'
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a user."""
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=['is_active'])
        return Response({'message': f'Usuario {user.email} activado.'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a user."""
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response({'message': f'Usuario {user.email} desactivado.'})

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Reset user password (admin action)."""
        user = self.get_object()
        new_password = request.data.get('new_password')
        if not new_password:
            return Response(
                {'error': 'new_password es requerido.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar fortaleza de contraseña
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response(
                {'error': list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()
        return Response({'message': f'Contraseña de {user.email} actualizada.'})


@extend_schema_view(
    list=extend_schema(tags=['Roles']),
    create=extend_schema(tags=['Roles']),
    retrieve=extend_schema(tags=['Roles']),
    update=extend_schema(tags=['Roles']),
    partial_update=extend_schema(tags=['Roles']),
    destroy=extend_schema(tags=['Roles']),
)
class RoleViewSet(TenantQuerySetMixin, viewsets.ModelViewSet):
    """ViewSet for role management.

    Multi-tenant: Roles are filtered by company automatically via TenantQuerySetMixin.
    SuperAdmins only see 'admin' type roles (to assign to company administrators).
    Company admins see all roles for their company.
    """
    queryset = Role.objects.select_related('company').prefetch_related('permissions')
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'settings:view'
    tenant_field = 'company'  # Filter roles by their company
    filterset_fields = ['is_active', 'role_type']
    search_fields = ['name', 'description']
    ordering = ['name']

    def get_queryset(self):
        """Override to filter only admin roles for SuperAdmin."""
        queryset = super().get_queryset()

        # SuperAdmin only sees admin-type roles (for assigning to company admins)
        if self.request.user.is_superuser:
            queryset = queryset.filter(role_type='admin')

        return queryset

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.required_permission = 'settings:edit'
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """Create a new role. Requires can_create_roles permission."""
        user = request.user

        # SuperAdmins can always create roles
        if not user.is_superuser:
            # Check if user has permission to create roles
            if not user.can_create_roles:
                return Response(
                    {'error': 'No tienes permiso para crear nuevos roles. Solo puedes editar roles existentes.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # SuperAdmin creates global admin roles (company=NULL, role_type='admin')
        if user.is_superuser:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(role_type='admin', company=None)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def setup_defaults(self, request):
        """Create default roles and permissions."""
        Permission.create_default_permissions()
        Role.create_default_roles()
        return Response({'message': 'Roles y permisos por defecto creados.'})


@extend_schema(tags=['Permisos'])
class PermissionListView(generics.ListAPIView):
    """List all available permissions."""
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'settings:view'
    filterset_fields = ['module', 'action']
    ordering = ['module', 'action']
    # Disable pagination - permissions are a small, fixed list that should all be returned
    pagination_class = None
