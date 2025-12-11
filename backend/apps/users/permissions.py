"""
Custom permission classes for the API.
"""
from rest_framework.permissions import BasePermission


class HasPermission(BasePermission):
    """
    Custom permission class that checks for specific permissions.

    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, HasPermission]
            required_permission = 'module:action'
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers have all permissions
        if request.user.is_superuser:
            return True

        # Get required permission from view
        required_permission = getattr(view, 'required_permission', None)
        if not required_permission:
            return True  # No specific permission required

        return request.user.has_permission(required_permission)


class HasModulePermission(BasePermission):
    """
    Permission class that checks for any permission in a module.

    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, HasModulePermission]
            required_module = 'inventory'
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        required_module = getattr(view, 'required_module', None)
        if not required_module:
            return True

        return request.user.has_module_permission(required_module)


class CanAccessBranch(BasePermission):
    """
    Permission class that checks if user can access the requested branch.

    Looks for branch_id in:
    1. URL kwargs (branch_id or branch_pk)
    2. Query parameters (branch)
    3. Request data (branch_id or branch)
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        # Try to get branch_id from various sources
        branch_id = (
            view.kwargs.get('branch_id') or
            view.kwargs.get('branch_pk') or
            request.query_params.get('branch') or
            request.data.get('branch_id') or
            request.data.get('branch')
        )

        if not branch_id:
            # If no branch specified, use user's default branch
            return True

        try:
            branch_id = int(branch_id)
        except (TypeError, ValueError):
            return False

        return request.user.can_access_branch(branch_id)


class IsOwnerOrAdmin(BasePermission):
    """
    Permission that allows access only to owner or admin.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        # Check if obj has a user field
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user

        return False


class IsSameUserOrAdmin(BasePermission):
    """
    Permission that allows users to access only their own data or admins.
    Used for user profile endpoints.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj == request.user
