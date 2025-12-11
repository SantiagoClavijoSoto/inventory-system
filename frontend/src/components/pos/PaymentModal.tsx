import { useState, useEffect } from 'react'
import {
  Banknote,
  CreditCard,
  ArrowRightLeft,
  Layers,
  User,
  Phone,
  Mail,
  FileText,
  Check,
} from 'lucide-react'
import { Modal, ModalFooter, Button, Input } from '@/components/ui'
import { useCartStore } from '@/store/cartStore'
import { formatCurrency } from '@/utils/formatters'
import type { PaymentMethod } from '@/types'

interface PaymentModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => Promise<void>
  isProcessing: boolean
}

const QUICK_AMOUNTS = [50, 100, 200, 500, 1000]

const paymentMethods: {
  value: PaymentMethod
  label: string
  icon: React.ElementType
}[] = [
  { value: 'cash', label: 'Efectivo', icon: Banknote },
  { value: 'card', label: 'Tarjeta', icon: CreditCard },
  { value: 'transfer', label: 'Transferencia', icon: ArrowRightLeft },
  { value: 'mixed', label: 'Mixto', icon: Layers },
]

export function PaymentModal({
  isOpen,
  onClose,
  onConfirm,
  isProcessing,
}: PaymentModalProps) {
  const {
    getTotal,
    getChange,
    paymentMethod,
    amountTendered,
    paymentReference,
    customerName,
    customerPhone,
    customerEmail,
    notes,
    setPaymentMethod,
    setAmountTendered,
    setPaymentReference,
    setCustomerName,
    setCustomerPhone,
    setCustomerEmail,
    setNotes,
  } = useCartStore()

  const [showCustomerFields, setShowCustomerFields] = useState(false)

  const total = getTotal()
  const change = getChange()
  const canProceed =
    paymentMethod !== 'cash' ||
    (paymentMethod === 'cash' && amountTendered >= total)

  // Auto-set amount tendered to total for non-cash payments
  useEffect(() => {
    if (paymentMethod !== 'cash' && paymentMethod !== 'mixed') {
      setAmountTendered(total)
    }
  }, [paymentMethod, total, setAmountTendered])

  // Handle keyboard number input for quick amount entry
  useEffect(() => {
    if (!isOpen || paymentMethod !== 'cash') return

    const handleKeyDown = (e: KeyboardEvent) => {
      // Number keys for quick amounts
      if (/^\d$/.test(e.key) && !e.ctrlKey && !e.metaKey) {
        const input = document.querySelector(
          '[data-amount-input]'
        ) as HTMLInputElement
        if (document.activeElement !== input) {
          input?.focus()
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, paymentMethod])

  const handleQuickAmount = (amount: number) => {
    setAmountTendered(amountTendered + amount)
  }

  const handleExactAmount = () => {
    setAmountTendered(Math.ceil(total))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await onConfirm()
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Procesar Pago"
      size="lg"
    >
      <form onSubmit={handleSubmit}>
        {/* Total Display */}
        <div className="text-center mb-6 pb-4 border-b border-secondary-200">
          <p className="text-secondary-500 mb-1">Total a pagar</p>
          <p className="text-4xl font-bold text-secondary-900">
            {formatCurrency(total)}
          </p>
        </div>

        {/* Payment Method Selection */}
        <div className="mb-6">
          <p className="text-sm font-medium text-secondary-700 mb-3">
            Método de pago
          </p>
          <div className="grid grid-cols-4 gap-2">
            {paymentMethods.map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                type="button"
                onClick={() => setPaymentMethod(value)}
                className={`flex flex-col items-center gap-2 p-3 rounded-lg border-2 transition-colors ${
                  paymentMethod === value
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-secondary-200 hover:border-secondary-300 text-secondary-600'
                }`}
              >
                <Icon className="w-6 h-6" />
                <span className="text-sm font-medium">{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Cash Payment - Amount Tendered */}
        {(paymentMethod === 'cash' || paymentMethod === 'mixed') && (
          <div className="mb-6">
            <p className="text-sm font-medium text-secondary-700 mb-3">
              Monto recibido
            </p>
            <div className="relative mb-3">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-secondary-400 text-lg">
                $
              </span>
              <input
                data-amount-input
                type="number"
                value={amountTendered || ''}
                onChange={(e) =>
                  setAmountTendered(parseFloat(e.target.value) || 0)
                }
                placeholder="0.00"
                className="w-full pl-10 pr-4 py-3 text-2xl font-semibold text-center border-2 border-secondary-200 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 outline-none"
                autoFocus
              />
            </div>

            {/* Quick Amount Buttons */}
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleExactAmount}
                className="px-3 py-2 bg-green-100 text-green-700 rounded-lg text-sm font-medium hover:bg-green-200 transition-colors"
              >
                Exacto
              </button>
              {QUICK_AMOUNTS.map((amount) => (
                <button
                  key={amount}
                  type="button"
                  onClick={() => handleQuickAmount(amount)}
                  className="px-3 py-2 bg-secondary-100 text-secondary-700 rounded-lg text-sm font-medium hover:bg-secondary-200 transition-colors"
                >
                  +${amount}
                </button>
              ))}
              <button
                type="button"
                onClick={() => setAmountTendered(0)}
                className="px-3 py-2 bg-red-100 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200 transition-colors"
              >
                Limpiar
              </button>
            </div>

            {/* Change Display */}
            {amountTendered > 0 && (
              <div
                className={`mt-4 p-4 rounded-lg ${
                  change >= 0 ? 'bg-green-50' : 'bg-red-50'
                }`}
              >
                <div className="flex justify-between items-center">
                  <span
                    className={`font-medium ${
                      change >= 0 ? 'text-green-700' : 'text-red-700'
                    }`}
                  >
                    {change >= 0 ? 'Cambio' : 'Falta'}
                  </span>
                  <span
                    className={`text-2xl font-bold ${
                      change >= 0 ? 'text-green-700' : 'text-red-700'
                    }`}
                  >
                    {formatCurrency(Math.abs(change >= 0 ? change : total - amountTendered))}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Card/Transfer - Reference */}
        {(paymentMethod === 'card' ||
          paymentMethod === 'transfer' ||
          paymentMethod === 'mixed') && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-secondary-700 mb-2">
              Referencia de pago (opcional)
            </label>
            <Input
              type="text"
              value={paymentReference}
              onChange={(e) => setPaymentReference(e.target.value)}
              placeholder="Número de autorización o referencia"
            />
          </div>
        )}

        {/* Customer Info Toggle */}
        <div className="mb-4">
          <button
            type="button"
            onClick={() => setShowCustomerFields(!showCustomerFields)}
            className="flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700"
          >
            <User className="w-4 h-4" />
            {showCustomerFields
              ? 'Ocultar datos del cliente'
              : 'Agregar datos del cliente (opcional)'}
          </button>
        </div>

        {/* Customer Fields */}
        {showCustomerFields && (
          <div className="space-y-4 mb-6 p-4 bg-secondary-50 rounded-lg">
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-1">
                Nombre
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-400" />
                <Input
                  type="text"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder="Nombre del cliente"
                  className="pl-10"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-1">
                  Teléfono
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-400" />
                  <Input
                    type="tel"
                    value={customerPhone}
                    onChange={(e) => setCustomerPhone(e.target.value)}
                    placeholder="10 dígitos"
                    className="pl-10"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-1">
                  Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-400" />
                  <Input
                    type="email"
                    value={customerEmail}
                    onChange={(e) => setCustomerEmail(e.target.value)}
                    placeholder="correo@ejemplo.com"
                    className="pl-10"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Notes */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-secondary-700 mb-1">
            Notas (opcional)
          </label>
          <div className="relative">
            <FileText className="absolute left-3 top-3 w-4 h-4 text-secondary-400" />
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Notas adicionales sobre la venta..."
              rows={2}
              className="w-full pl-10 pr-4 py-2 border border-secondary-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 outline-none resize-none"
            />
          </div>
        </div>

        <ModalFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            type="submit"
            disabled={!canProceed || isProcessing}
            className="min-w-[150px]"
          >
            {isProcessing ? (
              'Procesando...'
            ) : (
              <>
                <Check className="w-4 h-4 mr-2" />
                Confirmar Venta
              </>
            )}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  )
}
