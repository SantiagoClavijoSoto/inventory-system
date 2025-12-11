"""
URL configuration for Alerts app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AlertViewSet,
    AlertConfigurationViewSet,
    UserAlertPreferenceViewSet
)

router = DefaultRouter()
router.register(r'', AlertViewSet, basename='alert')
router.register(r'configurations', AlertConfigurationViewSet, basename='alert-configuration')
router.register(r'preferences', UserAlertPreferenceViewSet, basename='alert-preference')

urlpatterns = [
    path('', include(router.urls)),
]
