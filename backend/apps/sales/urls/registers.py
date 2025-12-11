"""
URL configuration for Cash Register endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from ..views import CashRegisterViewSet

router = DefaultRouter()
router.register(r'', CashRegisterViewSet, basename='register')

urlpatterns = [
    path('', include(router.urls)),
]
