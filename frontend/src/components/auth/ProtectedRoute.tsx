import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore, useIsPlatformAdmin } from '@/store/authStore'
import { Loader2 } from 'lucide-react'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredPermission?: string
  requiredModule?: string
}

export function ProtectedRoute({
  children,
  requiredPermission,
  requiredModule,
}: ProtectedRouteProps) {
  const location = useLocation()
  const { isAuthenticated, isLoading, hasPermission, hasModulePermission, user } =
    useAuthStore()
  const isPlatformAdmin = useIsPlatformAdmin()

  // Show loading spinner while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-secondary-50">
        <div className="text-center">
          <Loader2 className="w-10 h-10 animate-spin text-primary-600 mx-auto" />
          <p className="mt-4 text-secondary-600">Cargando...</p>
        </div>
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Platform admins bypass all permission checks
  if (isPlatformAdmin) {
    return <>{children}</>
  }

  // Check specific permission if required
  if (requiredPermission && !hasPermission(requiredPermission)) {
    // Admins bypass permission checks
    if (user?.role?.role_type !== 'admin') {
      return <Navigate to="/unauthorized" replace />
    }
  }

  // Check module access if required
  if (requiredModule && !hasModulePermission(requiredModule)) {
    // Admins bypass module checks
    if (user?.role?.role_type !== 'admin') {
      return <Navigate to="/unauthorized" replace />
    }
  }

  return <>{children}</>
}
