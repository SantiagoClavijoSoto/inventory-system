import { useState, useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { authApi } from '@/api/auth'
import { Button } from '@/components/ui/Button'
import { Package, Loader2, Mail, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import { extractErrorMessage } from '@/utils/errorSanitizer'

export function VerifyEmail() {
  const navigate = useNavigate()
  const location = useLocation()
  const { setAuthenticatedUser, isAuthenticated } = useAuthStore()

  // Get email from navigation state
  const email = (location.state as { email?: string })?.email || ''

  const [code, setCode] = useState(['', '', '', '', '', ''])
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isResending, setIsResending] = useState(false)
  const [resendCooldown, setResendCooldown] = useState(0)
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true })
    }
  }, [isAuthenticated, navigate])

  // Redirect if no email provided
  useEffect(() => {
    if (!email) {
      navigate('/login', { replace: true })
    }
  }, [email, navigate])

  // Resend cooldown timer
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000)
      return () => clearTimeout(timer)
    }
  }, [resendCooldown])

  // Focus first input on mount
  useEffect(() => {
    inputRefs.current[0]?.focus()
  }, [])

  const handleCodeChange = (index: number, value: string) => {
    // Only allow digits
    if (value && !/^\d$/.test(value)) return

    const newCode = [...code]
    newCode[index] = value
    setCode(newCode)
    setError('')

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }

    // Auto-submit when all digits entered
    if (value && index === 5 && newCode.every(d => d !== '')) {
      handleSubmit(newCode.join(''))
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    // Handle backspace
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    if (pastedData.length === 6) {
      const newCode = pastedData.split('')
      setCode(newCode)
      inputRefs.current[5]?.focus()
      handleSubmit(pastedData)
    }
  }

  const handleSubmit = async (codeString?: string) => {
    const fullCode = codeString || code.join('')

    if (fullCode.length !== 6) {
      setError('Por favor ingresa el código completo de 6 dígitos')
      return
    }

    setIsSubmitting(true)
    setError('')

    try {
      const response = await authApi.verifyEmail(email, fullCode)
      // Set user as authenticated - ForcePasswordChangeModal will show if must_change_password is true
      setAuthenticatedUser(response.user)
      toast.success('Email verificado exitosamente')
      navigate('/', { replace: true })
    } catch (err: unknown) {
      const message = extractErrorMessage(err, 'auth')
      setError(message)
      toast.error(message)
      // Clear code on error
      setCode(['', '', '', '', '', ''])
      inputRefs.current[0]?.focus()
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleResend = async () => {
    if (resendCooldown > 0 || isResending) return

    setIsResending(true)
    try {
      await authApi.resendVerification(email)
      toast.success('Se ha enviado un nuevo código a tu email')
      setResendCooldown(60) // 60 second cooldown
      setCode(['', '', '', '', '', ''])
      setError('')
      inputRefs.current[0]?.focus()
    } catch (err: unknown) {
      const message = extractErrorMessage(err, 'auth')
      toast.error(message)
    } finally {
      setIsResending(false)
    }
  }

  if (!email) {
    return null // Will redirect to login
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-600 to-primary-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-lg mb-4">
            <Package className="w-10 h-10 text-primary-600" />
          </div>
          <h1 className="text-3xl font-bold text-white">Verifica tu Email</h1>
          <p className="text-primary-200 mt-2">
            Ingresa el código de 6 dígitos enviado a
          </p>
          <p className="text-white font-medium mt-1">{email}</p>
        </div>

        {/* Verification Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
              <Mail className="w-8 h-8 text-primary-600" />
            </div>
          </div>

          {error && (
            <div className="bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded-lg text-sm mb-6">
              {error}
            </div>
          )}

          {/* 6-digit code input */}
          <div className="flex justify-center gap-2 mb-6" onPaste={handlePaste}>
            {code.map((digit, index) => (
              <input
                key={index}
                ref={el => inputRefs.current[index] = el}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={e => handleCodeChange(index, e.target.value)}
                onKeyDown={e => handleKeyDown(index, e)}
                disabled={isSubmitting}
                className="w-12 h-14 text-center text-2xl font-bold border-2 border-secondary-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 outline-none transition-all disabled:bg-secondary-100"
              />
            ))}
          </div>

          <Button
            onClick={() => handleSubmit()}
            className="w-full"
            size="lg"
            isLoading={isSubmitting}
            disabled={isSubmitting || code.some(d => d === '')}
          >
            Verificar
          </Button>

          <div className="mt-6 text-center">
            <p className="text-secondary-500 text-sm mb-2">
              ¿No recibiste el código?
            </p>
            <button
              onClick={handleResend}
              disabled={resendCooldown > 0 || isResending}
              className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 disabled:text-secondary-400 disabled:cursor-not-allowed transition-colors"
            >
              {isResending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              {resendCooldown > 0
                ? `Reenviar en ${resendCooldown}s`
                : 'Reenviar código'
              }
            </button>
          </div>

          <div className="mt-6 pt-6 border-t border-secondary-200 text-center">
            <button
              onClick={() => navigate('/login')}
              className="text-sm text-secondary-500 hover:text-secondary-700"
            >
              Volver al inicio de sesión
            </button>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-primary-200 text-sm mt-8">
          El código expira en 1 hora
        </p>
      </div>
    </div>
  )
}
