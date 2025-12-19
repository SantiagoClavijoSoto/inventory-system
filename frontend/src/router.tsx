import { createBrowserRouter, Navigate } from 'react-router-dom'
import { MainLayout } from '@/components/layout'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { useAuthStore, useIsPlatformAdmin } from '@/store/authStore'

// Auth Pages
import { Login } from '@/pages/auth/Login'

// Main Pages
import { Dashboard } from '@/pages/dashboard/Dashboard'

// Home redirect component - sends users to appropriate page based on permissions
function HomeRedirect() {
  const { hasModulePermission } = useAuthStore()
  const isPlatformAdmin = useIsPlatformAdmin()

  // Platform admins and users with dashboard permission go to Dashboard
  if (isPlatformAdmin || hasModulePermission('dashboard')) {
    return <Dashboard />
  }

  // Users without dashboard permission go to Schedule (clock in/out)
  return <Navigate to="/schedule" replace />
}
import { Products } from '@/pages/inventory/Products'
import { Employees } from '@/pages/employees/Employees'
import { Schedule } from '@/pages/schedule/Schedule'
import { Suppliers } from '@/pages/suppliers/Suppliers'
import { Reports } from '@/pages/reports/Reports'
import { Alerts } from '@/pages/alerts/Alerts'
import { Branches } from '@/pages/branches/Branches'
import { Settings } from '@/pages/settings/Settings'
import { Clients } from '@/pages/clients/Clients'
import { Subscriptions } from '@/pages/subscriptions/Subscriptions'

// Error Pages
import { NotFound } from '@/pages/errors/NotFound'
import { Unauthorized } from '@/pages/errors/Unauthorized'

// Placeholder components for pages not yet implemented
function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="flex items-center justify-center h-96">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-secondary-900 mb-2">{title}</h2>
        <p className="text-secondary-500">Esta página está en desarrollo</p>
      </div>
    </div>
  )
}

export const router = createBrowserRouter([
  // Public routes
  {
    path: '/login',
    element: <Login />,
  },

  // Protected routes with MainLayout
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <MainLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <HomeRedirect />,
      },
      {
        path: 'inventory',
        element: (
          <ProtectedRoute requiredModule="inventory">
            <Products />
          </ProtectedRoute>
        ),
      },
      {
        path: 'inventory/products',
        element: (
          <ProtectedRoute requiredModule="inventory">
            <Products />
          </ProtectedRoute>
        ),
      },
      {
        path: 'inventory/categories',
        element: (
          <ProtectedRoute requiredModule="inventory">
            <PlaceholderPage title="Categorías" />
          </ProtectedRoute>
        ),
      },
      {
        path: 'inventory/movements',
        element: (
          <ProtectedRoute requiredModule="inventory">
            <PlaceholderPage title="Movimientos de Stock" />
          </ProtectedRoute>
        ),
      },
      {
        path: 'employees',
        element: (
          <ProtectedRoute requiredModule="employees">
            <Employees />
          </ProtectedRoute>
        ),
      },
      {
        path: 'employees/:id',
        element: (
          <ProtectedRoute requiredModule="employees">
            <PlaceholderPage title="Detalle de Empleado" />
          </ProtectedRoute>
        ),
      },
      {
        path: 'schedule',
        // No requiredModule - Schedule is accessible to ALL authenticated users
        // Every employee needs to clock in/out regardless of role
        element: <Schedule />,
      },
      {
        path: 'suppliers',
        element: (
          <ProtectedRoute requiredModule="suppliers">
            <Suppliers />
          </ProtectedRoute>
        ),
      },
      {
        path: 'reports',
        element: (
          <ProtectedRoute requiredModule="reports">
            <Reports />
          </ProtectedRoute>
        ),
      },
      {
        path: 'alerts',
        element: (
          <ProtectedRoute requiredModule="alerts">
            <Alerts />
          </ProtectedRoute>
        ),
      },
      {
        path: 'branches',
        element: (
          <ProtectedRoute requiredModule="branches">
            <Branches />
          </ProtectedRoute>
        ),
      },
      {
        path: 'clients',
        element: (
          <ProtectedRoute requiredModule="companies">
            <Clients />
          </ProtectedRoute>
        ),
      },
      {
        path: 'subscriptions',
        element: (
          <ProtectedRoute requiredModule="subscriptions">
            <Subscriptions />
          </ProtectedRoute>
        ),
      },
      {
        path: 'settings',
        element: (
          <ProtectedRoute requiredModule="settings">
            <Settings />
          </ProtectedRoute>
        ),
      },
    ],
  },

  // Error routes
  {
    path: '/unauthorized',
    element: <Unauthorized />,
  },
  {
    path: '*',
    element: <NotFound />,
  },
])
