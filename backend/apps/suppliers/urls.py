"""
URL configuration for Suppliers app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SupplierViewSet, PurchaseOrderViewSet

router = DefaultRouter()
router.register(r'', SupplierViewSet, basename='supplier')

# Purchase orders router - to be included separately
orders_router = DefaultRouter()
orders_router.register(r'', PurchaseOrderViewSet, basename='purchase-order')

urlpatterns = [
    path('', include(router.urls)),
]

# Purchase orders URLs
orders_urlpatterns = [
    path('', include(orders_router.urls)),
]
