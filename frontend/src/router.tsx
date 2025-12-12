import { createBrowserRouter } from 'react-router-dom'
import { MainLayout } from '@/components/layout'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'

// Auth Pages
import { Login } from '@/pages/auth/Login'

// Main Pages
import { Dashboard } from '@/pages/dashboard/Dashboard'
import { Products } from '@/pages/inventory/Products'
import { POS } from '@/pages/pos/POS'
import { Employees } from '@/pages/employees/Employees'
import { Suppliers } from '@/pages/suppliers/Suppliers'
import { Reports } from '@/pages/reports/Reports'
import { Alerts } from '@/pages/alerts/Alerts'
import { Branches } from '@/pages/branches/Branches'
import { Settings } from '@/pages/settings/Settings'
import { Clients } from '@/pages/clients/Clients'

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
        element: <Dashboard />,
      },
      {
        path: 'pos',
        element: (
          <ProtectedRoute requiredModule="sales">
            <POS />
          </ProtectedRoute>
        ),
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
