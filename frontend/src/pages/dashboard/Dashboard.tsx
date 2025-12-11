import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { useAuthStore } from '@/store/authStore'
import {
  DollarSign,
  Package,
  ShoppingCart,
  TrendingUp,
  AlertTriangle,
} from 'lucide-react'

// Placeholder data - will be fetched from API
const stats = [
  {
    name: 'Ventas del Día',
    value: '$12,450',
    change: '+12%',
    changeType: 'positive' as const,
    icon: DollarSign,
  },
  {
    name: 'Productos Vendidos',
    value: '156',
    change: '+8%',
    changeType: 'positive' as const,
    icon: ShoppingCart,
  },
  {
    name: 'Productos en Stock',
    value: '2,340',
    change: '-2%',
    changeType: 'negative' as const,
    icon: Package,
  },
  {
    name: 'Ganancias del Mes',
    value: '$45,230',
    change: '+18%',
    changeType: 'positive' as const,
    icon: TrendingUp,
  },
]

export function Dashboard() {
  const { user, currentBranch } = useAuthStore()

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">
          ¡Bienvenido, {user?.first_name}!
        </h1>
        <p className="text-secondary-500">
          {currentBranch ? `${currentBranch.name}` : 'Selecciona una sucursal'} •{' '}
          {new Date().toLocaleDateString('es-ES', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <Card key={stat.name}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-secondary-500">
                    {stat.name}
                  </p>
                  <p className="text-2xl font-bold text-secondary-900 mt-1">
                    {stat.value}
                  </p>
                  <p
                    className={`text-sm mt-1 ${
                      stat.changeType === 'positive'
                        ? 'text-success-600'
                        : 'text-danger-600'
                    }`}
                  >
                    {stat.change} vs ayer
                  </p>
                </div>
                <div
                  className={`p-3 rounded-lg ${
                    stat.changeType === 'positive'
                      ? 'bg-success-100'
                      : 'bg-danger-100'
                  }`}
                >
                  <stat.icon
                    className={`w-6 h-6 ${
                      stat.changeType === 'positive'
                        ? 'text-success-600'
                        : 'text-danger-600'
                    }`}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Alerts Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-warning-500" />
            Alertas de Stock Bajo
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-secondary-500">
            <Package className="w-12 h-12 mx-auto mb-3 text-secondary-300" />
            <p>No hay alertas de stock bajo en este momento</p>
            <p className="text-sm mt-1">
              Las alertas aparecerán aquí cuando los productos alcancen el nivel mínimo
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Charts Section - Placeholder */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Ventas de los Últimos 7 Días</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center text-secondary-400">
              <div className="text-center">
                <TrendingUp className="w-12 h-12 mx-auto mb-3" />
                <p>Gráfica de ventas</p>
                <p className="text-sm">Se mostrará con datos reales</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top 5 Productos Más Vendidos</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center text-secondary-400">
              <div className="text-center">
                <Package className="w-12 h-12 mx-auto mb-3" />
                <p>Lista de productos top</p>
                <p className="text-sm">Se mostrará con datos reales</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
