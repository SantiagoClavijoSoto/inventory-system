import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { ShieldOff } from 'lucide-react'

export function Unauthorized() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-secondary-50 flex items-center justify-center p-4">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-danger-100 rounded-full mb-6">
          <ShieldOff className="w-10 h-10 text-danger-600" />
        </div>
        <h1 className="text-3xl font-bold text-secondary-900 mb-2">
          Acceso Denegado
        </h1>
        <p className="text-secondary-600 mb-8 max-w-md">
          No tienes permisos suficientes para acceder a esta página. Contacta al
          administrador si crees que esto es un error.
        </p>
        <div className="flex gap-4 justify-center">
          <Button variant="secondary" onClick={() => navigate(-1)}>
            Volver
          </Button>
          <Button onClick={() => navigate('/')}>
            Ir al Inicio
          </Button>
        </div>
      </div>
    </div>
  )
}
