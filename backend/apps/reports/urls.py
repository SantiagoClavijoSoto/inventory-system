"""
URL configuration for Reports app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DashboardViewSet,
    SalesReportViewSet,
    InventoryReportViewSet,
    EmployeeReportViewSet,
    BranchReportViewSet
)

router = DefaultRouter()
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'sales', SalesReportViewSet, basename='sales-report')
router.register(r'inventory', InventoryReportViewSet, basename='inventory-report')
router.register(r'employees', EmployeeReportViewSet, basename='employee-report')
router.register(r'branches', BranchReportViewSet, basename='branch-report')

urlpatterns = [
    path('', include(router.urls)),
]
