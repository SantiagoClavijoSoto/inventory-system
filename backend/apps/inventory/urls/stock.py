"""
URL configuration for Stock, Movements, and Alerts endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from ..views import StockViewSet, StockMovementViewSet, StockAlertViewSet

router = DefaultRouter()
router.register(r'', StockViewSet, basename='stock')
router.register(r'movements', StockMovementViewSet, basename='movement')
router.register(r'alerts', StockAlertViewSet, basename='alert')

urlpatterns = [
    path('', include(router.urls)),
]
