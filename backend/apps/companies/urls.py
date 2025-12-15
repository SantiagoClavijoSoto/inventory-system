"""
URL configuration for companies app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, SubscriptionViewSet

router = DefaultRouter()
router.register(r'', CompanyViewSet, basename='company')

# Separate router for subscriptions
subscription_router = DefaultRouter()
subscription_router.register(r'', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
]

# Export subscriptions URLs to be included in main urls.py
subscriptions_urlpatterns = subscription_router.urls
