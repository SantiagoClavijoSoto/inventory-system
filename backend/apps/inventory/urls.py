from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    ProductViewSet,
    StockViewSet,
    StockMovementViewSet,
    StockAlertViewSet,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'stock', StockViewSet, basename='stock')
router.register(r'movements', StockMovementViewSet, basename='movement')
router.register(r'alerts', StockAlertViewSet, basename='alert')

urlpatterns = [
    path('', include(router.urls)),
]
