"""
Views for user authentication and management.
"""
from django.contrib.auth import update_session_auth_hash
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import User, Role, Permission
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
)
from .permissions import HasPermission


@extend_schema(tags=['Autenticación'])
class LoginView(APIView):
    """User login endpoint."""
    permission_classes = [AllowAny]
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
        user.save()

        # Update session to prevent logout
        update_session_auth_hash(request, user)

        return Response({'message': 'Contraseña actualizada exitosamente.'})


@extend_schema_view(
    list=extend_schema(tags=['Usuarios']),
    create=extend_schema(tags=['Usuarios']),
    retrieve=extend_schema(tags=['Usuarios']),
    update=extend_schema(tags=['Usuarios']),
    partial_update=extend_schema(tags=['Usuarios']),
    destroy=extend_schema(tags=['Usuarios']),
)
class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user management (admin only)."""
    queryset = User.objects.select_related('role').prefetch_related('allowed_branches')
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'settings:view'
    filterset_fields = ['is_active', 'role']
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['created_at', 'first_name', 'last_name']
    ordering = ['-created_at']

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
class RoleViewSet(viewsets.ModelViewSet):
    """ViewSet for role management."""
    queryset = Role.objects.prefetch_related('permissions')
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'settings:view'
    filterset_fields = ['is_active', 'role_type']
    search_fields = ['name', 'description']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.required_permission = 'settings:edit'
        return super().get_permissions()

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
