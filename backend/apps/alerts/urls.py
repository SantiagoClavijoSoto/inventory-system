"""
URL configuration for Alerts app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AlertViewSet,
    AlertConfigurationViewSet,
    UserAlertPreferenceViewSet,
    ActivityLogViewSet,
)

router = DefaultRouter()
router.register(r'activities', ActivityLogViewSet, basename='activity-log')
router.register(r'configurations', AlertConfigurationViewSet, basename='alert-configuration')
router.register(r'', AlertViewSet, basename='alert')

# Create preference viewset instance for manual URL registration
preference_viewset = UserAlertPreferenceViewSet.as_view({
    'get': 'list',
})
preference_me_viewset = UserAlertPreferenceViewSet.as_view({
    'get': 'list',
    'put': 'me',
    'patch': 'me',
})

urlpatterns = [
    # User alert preferences (manual registration for ViewSet)
    path('preferences/', preference_viewset, name='alert-preference-list'),
    path('preferences/me/', preference_me_viewset, name='alert-preference-me'),
    # Router URLs
    path('', include(router.urls)),
]
