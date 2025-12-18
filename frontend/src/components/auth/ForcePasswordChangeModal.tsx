import { useState } from 'react'
import { Modal, ModalFooter } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'
import { Shield } from 'lucide-react'

interface FormData {
  current_password: string
  new_password: string
  new_password_confirm: string
}

interface FormErrors {
  current_password?: string
  new_password?: string
  new_password_confirm?: string
  general?: string
}

export function ForcePasswordChangeModal() {
  const user = useAuthStore((state) => state.user)
  const setUser = useAuthStore((state) => state.setUser)

  const [formData, setFormData] = useState<FormData>({
    current_password: '',
    new_password: '',
    new_password_confirm: '',
  })
  const [errors, setErrors] = useState<FormErrors>({})
  const [isLoading, setIsLoading] = useState(false)

  const isOpen = user?.must_change_password ?? false

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    if (!formData.current_password) {
      newErrors.current_password = 'La contraseña actual es requerida'
    }

    if (!formData.new_password) {
      newErrors.new_password = 'La nueva contraseña es requerida'
    } else if (formData.new_password.length < 8) {
      newErrors.new_password = 'La contraseña debe tener al menos 8 caracteres'
    }

    if (!formData.new_password_confirm) {
      newErrors.new_password_confirm = 'Confirma la nueva contraseña'
    } else if (formData.new_password !== formData.new_password_confirm) {
      newErrors.new_password_confirm = 'Las contraseñas no coinciden'
    }

    if (formData.current_password && formData.new_password === formData.current_password) {
      newErrors.new_password = 'La nueva contraseña debe ser diferente a la actual'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) return

    setIsLoading(true)
    setErrors({})

    try {
      await authApi.changePassword(formData)

      // Update user state to remove must_change_password flag
      if (user) {
        setUser({ ...user, must_change_password: false })
      }
    } catch (error: unknown) {
      const apiError = error as { response?: { data?: Record<string, string | string[]> } }
      if (apiError.response?.data) {
        const data = apiError.response.data
        const newErrors: FormErrors = {}

        if (data.current_password) {
          newErrors.current_password = Array.isArray(data.current_password)
            ? data.current_password[0]
            : data.current_password
        }
        if (data.new_password) {
          newErrors.new_password = Array.isArray(data.new_password)
            ? data.new_password[0]
            : data.new_password
        }
        if (data.new_password_confirm) {
          newErrors.new_password_confirm = Array.isArray(data.new_password_confirm)
            ? data.new_password_confirm[0]
            : data.new_password_confirm
        }
        if (data.detail) {
          newErrors.general = Array.isArray(data.detail) ? data.detail[0] : data.detail
        }
        if (data.non_field_errors) {
          newErrors.general = Array.isArray(data.non_field_errors)
            ? data.non_field_errors[0]
            : String(data.non_field_errors)
        }

        setErrors(newErrors)
      } else {
        setErrors({ general: 'Error al cambiar la contraseña. Intenta de nuevo.' })
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleChange = (field: keyof FormData) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [field]: e.target.value }))
    // Clear field error when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }))
    }
  }

  // Prevent closing the modal - user must change password
  const handleClose = () => {
    // Do nothing - modal cannot be closed
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Cambio de contraseña requerido"
      description="Por seguridad, debes cambiar tu contraseña antes de continuar."
      showCloseButton={false}
      size="sm"
      zIndex="z-[100]"
    >
      <form onSubmit={handleSubmit}>
        <div className="flex justify-center mb-6">
          <div className="p-4 bg-primary-100 rounded-full">
            <Shield className="w-8 h-8 text-primary-600" />
          </div>
        </div>

        {errors.general && (
          <div className="mb-4 p-3 bg-danger-50 border border-danger-200 rounded-lg text-sm text-danger-700">
            {errors.general}
          </div>
        )}

        <div className="space-y-4">
          <Input
            label="Contraseña actual"
            type="password"
            value={formData.current_password}
            onChange={handleChange('current_password')}
            error={errors.current_password}
            placeholder="Ingresa tu contraseña actual"
            autoComplete="current-password"
          />

          <Input
            label="Nueva contraseña"
            type="password"
            value={formData.new_password}
            onChange={handleChange('new_password')}
            error={errors.new_password}
            placeholder="Ingresa tu nueva contraseña"
            helperText="Mínimo 8 caracteres"
            autoComplete="new-password"
          />

          <Input
            label="Confirmar nueva contraseña"
            type="password"
            value={formData.new_password_confirm}
            onChange={handleChange('new_password_confirm')}
            error={errors.new_password_confirm}
            placeholder="Confirma tu nueva contraseña"
            autoComplete="new-password"
          />
        </div>

        <ModalFooter>
          <Button type="submit" isLoading={isLoading}>
            Cambiar contraseña
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  )
}
