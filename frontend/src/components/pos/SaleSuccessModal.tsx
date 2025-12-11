import { CheckCircle, Printer, Download } from 'lucide-react'
import { Modal, Button } from '@/components/ui'
import { formatCurrency } from '@/utils/formatters'
import type { Sale } from '@/types'

interface SaleSuccessModalProps {
  isOpen: boolean
  onClose: () => void
  sale: Sale | null
  onPrintReceipt?: (saleId: number) => void
  onNewSale: () => void
}

export function SaleSuccessModal({
  isOpen,
  onClose,
  sale,
  onPrintReceipt,
  onNewSale,
}: SaleSuccessModalProps) {
  if (!sale) return null

  const handlePrint = () => {
    onPrintReceipt?.(sale.id)
  }

  const handleNewSale = () => {
    onNewSale()
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="" showCloseButton={false}>
      <div className="text-center">
        {/* Success Icon */}
        <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
          <CheckCircle className="w-10 h-10 text-green-600" />
        </div>

        {/* Success Message */}
        <h2 className="text-2xl font-bold text-secondary-900 mb-2">
          ¡Venta completada!
        </h2>
        <p className="text-secondary-500 mb-6">
          La venta se ha registrado exitosamente
        </p>

        {/* Sale Details */}
        <div className="bg-secondary-50 rounded-lg p-4 mb-6 text-left">
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-secondary-500">Número de venta:</span>
              <p className="font-mono font-semibold text-secondary-900">
                {sale.sale_number}
              </p>
            </div>
            <div>
              <span className="text-secondary-500">Fecha:</span>
              <p className="font-semibold text-secondary-900">
                {new Date(sale.created_at).toLocaleString('es-MX')}
              </p>
            </div>
            <div>
              <span className="text-secondary-500">Método de pago:</span>
              <p className="font-semibold text-secondary-900">
                {sale.payment_method_display}
              </p>
            </div>
            <div>
              <span className="text-secondary-500">Productos:</span>
              <p className="font-semibold text-secondary-900">
                {sale.items_count} ({sale.total_quantity} unidades)
              </p>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-secondary-200">
            <div className="flex justify-between text-lg">
              <span className="font-medium text-secondary-700">Total:</span>
              <span className="font-bold text-secondary-900">
                {formatCurrency(parseFloat(String(sale.total)))}
              </span>
            </div>
            {sale.change_amount > 0 && (
              <div className="flex justify-between text-green-600 mt-1">
                <span>Cambio:</span>
                <span className="font-semibold">
                  {formatCurrency(parseFloat(String(sale.change_amount)))}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-3">
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={handlePrint}
              className="flex-1"
            >
              <Printer className="w-4 h-4 mr-2" />
              Imprimir recibo
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                // Download receipt as PDF (could be implemented)
                handlePrint()
              }}
              className="flex-1"
            >
              <Download className="w-4 h-4 mr-2" />
              Descargar PDF
            </Button>
          </div>
          <Button onClick={handleNewSale} className="w-full">
            Nueva venta
          </Button>
          <button
            onClick={onClose}
            className="text-secondary-500 hover:text-secondary-700 text-sm"
          >
            Cerrar
          </button>
        </div>
      </div>
    </Modal>
  )
}
