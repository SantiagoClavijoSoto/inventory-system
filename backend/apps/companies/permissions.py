"""
Permission classes for companies app.
"""
from rest_framework.permissions import BasePermission


class IsSuperUser(BasePermission):
    """
    Permission class that only allows platform superusers.
    Used for company management at the platform level.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser
        )


class IsCompanyAdmin(BasePermission):
    """
    Permission class that allows company administrators.
    Company admins can manage their own company's data.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # SuperUsers have all permissions
        if request.user.is_superuser:
            return True

        # Check if user is a company admin
        return getattr(request.user, 'is_company_admin', False)


class IsSameCompany(BasePermission):
    """
    Permission class that ensures users can only access
    resources from their own company.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        # Get user's company
        user_company = getattr(request.user, 'company', None)
        if not user_company:
            return False

        # Get object's company
        obj_company = getattr(obj, 'company', None)
        if not obj_company:
            return False

        return user_company.id == obj_company.id
