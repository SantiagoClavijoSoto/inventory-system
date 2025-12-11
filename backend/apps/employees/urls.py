"""
URL configuration for Employees app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import EmployeeViewSet, ShiftViewSet

router = DefaultRouter()
router.register(r'', EmployeeViewSet, basename='employee')

urlpatterns = [
    path('', include(router.urls)),
]

# Shifts router - to be included separately in main urls
shifts_router = DefaultRouter()
shifts_router.register(r'', ShiftViewSet, basename='shift')

shifts_urlpatterns = [
    path('', include(shifts_router.urls)),
]
