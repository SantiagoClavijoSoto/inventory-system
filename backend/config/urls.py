"""
URL configuration for inventory project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# Import shifts patterns
from apps.employees.urls import shifts_urlpatterns
from apps.suppliers.urls import orders_urlpatterns

# API v1 URL patterns
api_v1_patterns = [
    # Auth
    path('auth/', include('apps.users.urls')),
    # Platform Management (SuperAdmin only)
    path('companies/', include('apps.companies.urls')),
    # Core modules
    path('branches/', include('apps.branches.urls')),
    path('employees/', include('apps.employees.urls')),
    path('shifts/', include(shifts_urlpatterns)),
    # Inventory
    path('categories/', include('apps.inventory.urls.categories')),
    path('products/', include('apps.inventory.urls.products')),
    path('stock/', include('apps.inventory.urls.stock')),
    # Sales
    path('sales/', include('apps.sales.urls.sales')),
    path('registers/', include('apps.sales.urls.registers')),
    # Suppliers
    path('suppliers/', include('apps.suppliers.urls')),
    path('purchase-orders/', include(orders_urlpatterns)),
    # Reports & Alerts
    path('reports/', include('apps.reports.urls')),
    path('alerts/', include('apps.alerts.urls')),
]

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API v1
    path('api/v1/', include(api_v1_patterns)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
