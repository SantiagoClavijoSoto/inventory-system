import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { FileQuestion } from 'lucide-react'

export function NotFound() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-secondary-50 flex items-center justify-center p-4">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-secondary-200 rounded-full mb-6">
          <FileQuestion className="w-10 h-10 text-secondary-600" />
        </div>
        <h1 className="text-6xl font-bold text-secondary-300 mb-2">404</h1>
        <h2 className="text-2xl font-bold text-secondary-900 mb-2">
          Página No Encontrada
        </h2>
        <p className="text-secondary-600 mb-8 max-w-md">
          La página que buscas no existe o ha sido movida.
        </p>
        <Button onClick={() => navigate('/')}>Ir al Inicio</Button>
      </div>
    </div>
  )
}
