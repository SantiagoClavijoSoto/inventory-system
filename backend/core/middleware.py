"""
Middleware for multi-tenant architecture.
"""


class TenantMiddleware:
    """
    Middleware that attaches company context to the request.

    For authenticated users:
    - SuperAdmin (is_superuser=True): request.company = None, is_platform_admin = True
    - Regular users: request.company = user.company, is_platform_admin = False

    This allows ViewSets using TenantQuerySetMixin to automatically
    filter data by company.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set defaults
        request.company = None
        request.is_platform_admin = False

        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.is_superuser:
                # SuperAdmin de plataforma - puede ver todo
                request.company = None
                request.is_platform_admin = True
            else:
                # Usuario normal - filtrar por su empresa
                request.company = getattr(request.user, 'company', None)
                request.is_platform_admin = False

        response = self.get_response(request)
        return response
