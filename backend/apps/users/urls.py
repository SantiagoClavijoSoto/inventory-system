"""
URL configuration for users app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    LoginView,
    LogoutView,
    CustomTokenRefreshView,
    MeView,
    ChangePasswordView,
    VerifyEmailView,
    ResendVerificationView,
    UserViewSet,
    RoleViewSet,
    PermissionListView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')

urlpatterns = [
    # Authentication endpoints
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),

    # Email verification
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend_verification'),

    # Permissions
    path('permissions/', PermissionListView.as_view(), name='permission_list'),

    # Router URLs (users and roles CRUD)
    path('', include(router.urls)),
]
