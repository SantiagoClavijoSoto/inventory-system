"""
URL configuration for Sales app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SaleViewSet, CashRegisterViewSet

router = DefaultRouter()
router.register(r'sales', SaleViewSet, basename='sale')
router.register(r'cash-register', CashRegisterViewSet, basename='cash-register')

urlpatterns = [
    path('', include(router.urls)),
]
