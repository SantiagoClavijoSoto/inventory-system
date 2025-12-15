import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { cn } from '@/utils/cn'
import { useAuthStore, useModulePermission, useIsPlatformAdmin } from '@/store/authStore'
import { useThemeStore } from '@/store/themeStore'
import {
  LayoutDashboard,
  Package,
  Users,
  Truck,
  FileText,
  Settings,
  Building2,
  Building,
  Bell,
  LogOut,
  CreditCard,
} from 'lucide-react'

interface NavItem {
  name: string
  href: string
  icon: React.ElementType
  module: string
}

// Navigation for regular company users (admins, employees)
const regularNavigation: NavItem[] = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, module: 'dashboard' },
  { name: 'Inventario', href: '/inventory', icon: Package, module: 'inventory' },
  { name: 'Empleados', href: '/employees', icon: Users, module: 'employees' },
  { name: 'Proveedores', href: '/suppliers', icon: Truck, module: 'suppliers' },
  { name: 'Reportes', href: '/reports', icon: FileText, module: 'reports' },
  { name: 'Alertas', href: '/alerts', icon: Bell, module: 'alerts' },
  { name: 'Sucursales', href: '/branches', icon: Building2, module: 'branches' },
  { name: 'Configuración', href: '/settings', icon: Settings, module: 'settings' },
]

// Navigation for platform superadmin (SaaS owner)
const superadminNavigation: NavItem[] = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, module: 'dashboard' },
  { name: 'Clientes', href: '/clients', icon: Building, module: 'companies' },
  { name: 'Suscripciones', href: '/subscriptions', icon: CreditCard, module: 'subscriptions' },
  { name: 'Alertas', href: '/alerts', icon: Bell, module: 'alerts' },
  { name: 'Configuración', href: '/settings', icon: Settings, module: 'settings' },
]

export function Sidebar() {
  const location = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user, logout } = useAuthStore()
  const { branding, clearBranding } = useThemeStore()
  const isPlatformAdmin = useIsPlatformAdmin()

  // Select navigation based on user role
  const navigation = isPlatformAdmin ? superadminNavigation : regularNavigation

  const handleLogout = async () => {
    // Clear all TanStack Query cache to prevent stale data between sessions
    queryClient.clear()
    // Reset branding/theme to defaults
    clearBranding()
    // Clear auth storage from localStorage
    localStorage.removeItem('auth-storage')
    // Perform logout
    await logout()
    // Navigate to login page without any state (forces redirect to dashboard on next login)
    navigate('/login', { replace: true, state: null })
  }

  // Get store name from branding or fallback
  const storeName = isPlatformAdmin
    ? 'Panel Administrador'
    : branding?.display_name || 'Sistema de Inventario'
  const logoUrl = isPlatformAdmin ? null : branding?.logo_url

  return (
    <aside className="fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-secondary-200 flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-secondary-200">
        <div className="flex items-center gap-3">
          {logoUrl ? (
            <img
              src={logoUrl}
              alt={storeName}
              className="w-8 h-8 rounded-lg object-contain"
            />
          ) : (
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <Package className="w-5 h-5 text-white" />
            </div>
          )}
          <span className="text-lg font-semibold text-secondary-900 truncate max-w-[160px]">
            {storeName}
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3">
        <ul className="space-y-1">
          {navigation.map((item) => {
            // Platform admins have access to all their navigation items
            // Regular users need module permission check
            const hasAccess = useModulePermission(item.module)
            if (!isPlatformAdmin && !hasAccess && user?.role?.role_type !== 'admin') return null

            const isActive =
              item.href === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(item.href)

            return (
              <li key={item.name}>
                <NavLink
                  to={item.href}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-secondary-600 hover:bg-secondary-100 hover:text-secondary-900'
                  )}
                >
                  <item.icon className="w-5 h-5" />
                  {item.name}
                </NavLink>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* User section */}
      <div className="border-t border-secondary-200 p-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
            <span className="text-primary-700 font-medium">
              {user?.first_name?.[0]}
              {user?.last_name?.[0]}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-secondary-900 truncate">
              {user?.full_name}
            </p>
            <p className="text-xs text-secondary-500 truncate">
              {user?.role?.name || 'Sin rol'}
            </p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 w-full px-3 py-2 text-sm text-secondary-600 hover:bg-secondary-100 rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Cerrar sesión
        </button>
      </div>
    </aside>
  )
}
