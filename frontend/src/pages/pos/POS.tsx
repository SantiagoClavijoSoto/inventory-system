import { useState, useCallback, useEffect } from 'react'
import { Store, X, AlertTriangle, DollarSign } from 'lucide-react'
import toast from 'react-hot-toast'
import { Button, Card, CardContent, Badge, Input, Modal, ModalFooter } from '@/components/ui'
import { ProductSearch, Cart, PaymentModal, SaleSuccessModal } from '@/components/pos'
import { useCartStore } from '@/store/cartStore'
import { useAuthStore } from '@/store/authStore'
import { saleApi, cashRegisterApi } from '@/api/sales'
import { formatCurrency } from '@/utils/formatters'
import type { Product, Sale, DailyCashRegister } from '@/types'

export function POS() {
  const [showPaymentModal, setShowPaymentModal] = useState(false)
  const [showSuccessModal, setShowSuccessModal] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [completedSale, setCompletedSale] = useState<Sale | null>(null)
  const [cashRegister, setCashRegister] = useState<DailyCashRegister | null>(null)
  const [isLoadingRegister, setIsLoadingRegister] = useState(true)
  const [showOpenRegisterModal, setShowOpenRegisterModal] = useState(false)
  const [openingAmount, setOpeningAmount] = useState('')
  const [isOpeningRegister, setIsOpeningRegister] = useState(false)

  const { addItem, clearCart, getCreateSalePayload, getItemCount } = useCartStore()
  const { currentBranch } = useAuthStore()

  // Load current cash register
  useEffect(() => {
    const loadCashRegister = async () => {
      if (!currentBranch) return

      setIsLoadingRegister(true)
      try {
        const register = await cashRegisterApi.getCurrent(currentBranch.id)
        setCashRegister(register)
      } catch {
        setCashRegister(null)
      } finally {
        setIsLoadingRegister(false)
      }
    }

    loadCashRegister()
  }, [currentBranch])

  // Handle product selection from search
  const handleSelectProduct = useCallback(
    (product: Product) => {
      addItem(product, 1)
      toast.success(`${product.name} agregado al carrito`)
    },
    [addItem]
  )

  // Handle checkout
  const handleCheckout = () => {
    if (getItemCount() === 0) {
      toast.error('El carrito está vacío')
      return
    }

    if (!cashRegister) {
      toast.error('La caja no está abierta. Abre la caja primero.')
      return
    }

    setShowPaymentModal(true)
  }

  // Handle sale confirmation
  const handleConfirmSale = async () => {
    if (!currentBranch) {
      toast.error('Selecciona una sucursal')
      return
    }

    setIsProcessing(true)
    try {
      const payload = getCreateSalePayload()
      const sale = await saleApi.create({
        ...payload,
        branch_id: currentBranch.id,
      })

      setCompletedSale(sale)
      setShowPaymentModal(false)
      setShowSuccessModal(true)
      clearCart()

      // Refresh cash register info
      const register = await cashRegisterApi.getCurrent(currentBranch.id)
      setCashRegister(register)
    } catch (error: unknown) {
      const errorMsg =
        error instanceof Error ? error.message : 'Error al procesar la venta'
      toast.error(errorMsg)
    } finally {
      setIsProcessing(false)
    }
  }

  // Handle print receipt
  const handlePrintReceipt = async (saleId: number) => {
    try {
      const receipt = await saleApi.getReceipt(saleId)
      // For now, just log - in production this would trigger printing
      console.log('Receipt data:', receipt)
      toast.success('Recibo enviado a impresión')
    } catch {
      toast.error('Error al obtener el recibo')
    }
  }

  // Handle new sale
  const handleNewSale = () => {
    clearCart()
    setCompletedSale(null)
    setShowSuccessModal(false)
  }

  // Handle open cash register
  const handleOpenRegister = async () => {
    if (!currentBranch) return

    const amount = parseFloat(openingAmount)
    if (isNaN(amount) || amount < 0) {
      toast.error('Ingresa un monto válido')
      return
    }

    setIsOpeningRegister(true)
    try {
      const register = await cashRegisterApi.open(currentBranch.id, amount)
      setCashRegister(register)
      setShowOpenRegisterModal(false)
      setOpeningAmount('')
      toast.success('Caja abierta exitosamente')
    } catch (error: unknown) {
      const errorMsg =
        error instanceof Error ? error.message : 'Error al abrir la caja'
      toast.error(errorMsg)
    } finally {
      setIsOpeningRegister(false)
    }
  }

  // Handle error
  const handleError = (error: string) => {
    toast.error(error)
  }

  // No branch selected warning
  if (!currentBranch) {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="max-w-md">
          <CardContent className="p-8 text-center">
            <AlertTriangle className="w-16 h-16 text-amber-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-secondary-900 mb-2">
              Selecciona una sucursal
            </h2>
            <p className="text-secondary-500">
              Debes seleccionar una sucursal desde el menú superior para poder
              usar el punto de venta.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">
            Punto de Venta
          </h1>
          <div className="flex items-center gap-2 text-sm text-secondary-500">
            <Store className="w-4 h-4" />
            <span>{currentBranch.name}</span>
            {cashRegister && (
              <>
                <span>•</span>
                <Badge variant="success">Caja abierta</Badge>
                <span className="text-green-600">
                  {formatCurrency(cashRegister.cash_sales_total)} en efectivo
                </span>
              </>
            )}
            {!cashRegister && !isLoadingRegister && (
              <>
                <span>•</span>
                <Badge variant="warning">Caja cerrada</Badge>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Clear Cart */}
          {getItemCount() > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (confirm('¿Seguro que quieres vaciar el carrito?')) {
                  clearCart()
                  toast.success('Carrito vaciado')
                }
              }}
            >
              <X className="w-4 h-4 mr-1" />
              Limpiar
            </Button>
          )}
        </div>
      </div>

      {/* Cash Register Alert Banner */}
      {!cashRegister && !isLoadingRegister && (
        <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-amber-500" />
            <div>
              <p className="font-medium text-amber-800">
                La caja no está abierta
              </p>
              <p className="text-sm text-amber-600">
                Debes abrir la caja para poder realizar ventas
              </p>
            </div>
          </div>
          <Button
            onClick={() => setShowOpenRegisterModal(true)}
          >
            <DollarSign className="w-4 h-4 mr-1" />
            Abrir Caja
          </Button>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-0">
        {/* Left Panel - Product Search */}
        <div className="lg:col-span-2 flex flex-col min-h-0">
          <Card className="flex-1 flex flex-col min-h-0">
            <CardContent className="flex-1 flex flex-col p-4 min-h-0">
              <div className="space-y-4">
                <ProductSearch
                  onSelectProduct={handleSelectProduct}
                  onError={handleError}
                />

                {/* Quick Tips */}
                <div className="bg-secondary-50 rounded-lg p-4">
                  <h3 className="font-medium text-secondary-900 mb-2">
                    Consejos rápidos
                  </h3>
                  <ul className="text-sm text-secondary-600 space-y-1">
                    <li>
                      • Escribe el nombre o SKU del producto para buscar
                    </li>
                    <li>
                      • Usa las flechas ↑↓ para navegar y Enter para seleccionar
                    </li>
                    <li>
                      • Puedes buscar por nombre parcial o código SKU completo
                    </li>
                  </ul>
                </div>

                {/* Recent Products - Could be implemented */}
                <div>
                  <h3 className="font-medium text-secondary-900 mb-2">
                    Productos frecuentes
                  </h3>
                  <p className="text-sm text-secondary-500">
                    Los productos más vendidos aparecerán aquí
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Panel - Cart */}
        <div className="flex flex-col min-h-0">
          <Card className="flex-1 flex flex-col min-h-0">
            <CardContent className="flex-1 flex flex-col p-4 min-h-0">
              <Cart onCheckout={handleCheckout} isProcessing={isProcessing} />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Payment Modal */}
      <PaymentModal
        isOpen={showPaymentModal}
        onClose={() => setShowPaymentModal(false)}
        onConfirm={handleConfirmSale}
        isProcessing={isProcessing}
      />

      {/* Success Modal */}
      <SaleSuccessModal
        isOpen={showSuccessModal}
        onClose={() => setShowSuccessModal(false)}
        sale={completedSale}
        onPrintReceipt={handlePrintReceipt}
        onNewSale={handleNewSale}
      />

      {/* Open Register Modal */}
      <Modal
        isOpen={showOpenRegisterModal}
        onClose={() => {
          setShowOpenRegisterModal(false)
          setOpeningAmount('')
        }}
        title="Abrir Caja"
        description="Ingresa el monto inicial de efectivo en caja"
        size="sm"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-1">
              Monto de apertura
            </label>
            <Input
              type="number"
              value={openingAmount}
              onChange={(e) => setOpeningAmount(e.target.value)}
              placeholder="0.00"
              min="0"
              step="0.01"
              autoFocus
            />
            <p className="mt-1 text-xs text-secondary-500">
              Ingresa el monto de efectivo con el que inicias la caja
            </p>
          </div>
        </div>
        <ModalFooter>
          <Button
            variant="outline"
            onClick={() => {
              setShowOpenRegisterModal(false)
              setOpeningAmount('')
            }}
          >
            Cancelar
          </Button>
          <Button
            onClick={handleOpenRegister}
            disabled={isOpeningRegister}
          >
            {isOpeningRegister ? 'Abriendo...' : 'Abrir Caja'}
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  )
}
