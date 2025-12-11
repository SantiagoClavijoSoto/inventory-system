import { NavLink, useLocation } from 'react-router-dom'
import { cn } from '@/utils/cn'
import { useAuthStore, useModulePermission } from '@/store/authStore'
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  Users,
  Truck,
  FileText,
  Settings,
  Building2,
  Bell,
  LogOut,
} from 'lucide-react'

interface NavItem {
  name: string
  href: string
  icon: React.ElementType
  module: string
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, module: 'dashboard' },
  { name: 'Punto de Venta', href: '/pos', icon: ShoppingCart, module: 'sales' },
  { name: 'Inventario', href: '/inventory', icon: Package, module: 'inventory' },
  { name: 'Empleados', href: '/employees', icon: Users, module: 'employees' },
  { name: 'Proveedores', href: '/suppliers', icon: Truck, module: 'suppliers' },
  { name: 'Reportes', href: '/reports', icon: FileText, module: 'reports' },
  { name: 'Alertas', href: '/alerts', icon: Bell, module: 'alerts' },
  { name: 'Sucursales', href: '/branches', icon: Building2, module: 'branches' },
  { name: 'Configuración', href: '/settings', icon: Settings, module: 'settings' },
]

export function Sidebar() {
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const handleLogout = async () => {
    await logout()
  }

  return (
    <aside className="fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-secondary-200 flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-secondary-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <Package className="w-5 h-5 text-white" />
          </div>
          <span className="text-lg font-semibold text-secondary-900">Inventario</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3">
        <ul className="space-y-1">
          {navigation.map((item) => {
            const hasAccess = useModulePermission(item.module)
            if (!hasAccess && user?.role?.role_type !== 'admin') return null

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
