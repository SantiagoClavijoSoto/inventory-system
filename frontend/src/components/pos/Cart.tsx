import { Trash2, Minus, Plus, Package, ShoppingCart } from 'lucide-react'
import { Button, Input } from '@/components/ui'
import { useCartStore } from '@/store/cartStore'
import { formatCurrency } from '@/utils/formatters'

interface CartProps {
  onCheckout: () => void
  isProcessing?: boolean
}

export function Cart({ onCheckout, isProcessing = false }: CartProps) {
  const {
    items,
    getSubtotal,
    getTotalDiscount,
    getTax,
    getTotal,
    getTotalQuantity,
    updateItemQuantity,
    updateItemDiscount,
    removeItem,
    discountPercent,
    discountAmount,
    setDiscountPercent,
    setDiscountAmount,
  } = useCartStore()

  const subtotal = getSubtotal()
  const totalDiscount = getTotalDiscount()
  const tax = getTax()
  const total = getTotal()
  const totalQuantity = getTotalQuantity()

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-secondary-400 py-12">
        <ShoppingCart className="w-16 h-16 mb-4" />
        <p className="text-lg font-medium">El carrito está vacío</p>
        <p className="text-sm">Escanea o busca productos para agregar</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Cart Header */}
      <div className="flex items-center justify-between pb-4 border-b border-secondary-200">
        <h2 className="text-lg font-semibold text-secondary-900">
          Carrito ({totalQuantity} items)
        </h2>
      </div>

      {/* Cart Items */}
      <div className="flex-1 overflow-y-auto py-4 space-y-3 min-h-0">
        {items.map((item) => (
          <div
            key={item.product.id}
            className="bg-secondary-50 rounded-lg p-3 space-y-2"
          >
            <div className="flex items-start gap-3">
              {item.product.image ? (
                <img
                  src={item.product.image}
                  alt={item.product.name}
                  className="w-12 h-12 object-cover rounded-lg flex-shrink-0"
                />
              ) : (
                <div className="w-12 h-12 bg-secondary-200 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Package className="w-6 h-6 text-secondary-400" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="font-medium text-secondary-900 truncate">
                  {item.product.name}
                </p>
                <p className="text-sm text-secondary-500 font-mono">
                  {item.product.sku}
                </p>
                <p className="text-sm text-secondary-600">
                  {formatCurrency(item.customPrice ?? item.product.sale_price)} x{' '}
                  {item.quantity}
                </p>
              </div>
              <button
                onClick={() => removeItem(item.product.id)}
                className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                title="Eliminar"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>

            {/* Quantity controls */}
            <div className="flex items-center gap-2">
              <button
                onClick={() =>
                  updateItemQuantity(item.product.id, item.quantity - 1)
                }
                className="p-1.5 bg-white border border-secondary-200 rounded-lg hover:bg-secondary-50 transition-colors"
                disabled={item.quantity <= 1}
              >
                <Minus className="w-4 h-4" />
              </button>
              <input
                type="number"
                value={item.quantity}
                onChange={(e) =>
                  updateItemQuantity(
                    item.product.id,
                    Math.max(1, parseInt(e.target.value) || 1)
                  )
                }
                className="w-16 text-center py-1 border border-secondary-200 rounded-lg focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none"
                min="1"
              />
              <button
                onClick={() =>
                  updateItemQuantity(item.product.id, item.quantity + 1)
                }
                className="p-1.5 bg-white border border-secondary-200 rounded-lg hover:bg-secondary-50 transition-colors"
              >
                <Plus className="w-4 h-4" />
              </button>

              {/* Item discount */}
              <div className="flex-1 flex items-center gap-1 ml-2">
                <span className="text-xs text-secondary-500">Desc:</span>
                <input
                  type="number"
                  value={item.discount || ''}
                  onChange={(e) =>
                    updateItemDiscount(
                      item.product.id,
                      Math.max(0, parseFloat(e.target.value) || 0)
                    )
                  }
                  placeholder="0"
                  className="w-16 text-center text-sm py-1 border border-secondary-200 rounded-lg focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none"
                  min="0"
                />
              </div>
            </div>

            {/* Item subtotal */}
            <div className="flex justify-end">
              <span className="font-semibold text-secondary-900">
                {formatCurrency(
                  (item.customPrice ?? item.product.sale_price) * item.quantity -
                    item.discount
                )}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Global Discount */}
      <div className="py-3 border-t border-secondary-200">
        <p className="text-sm font-medium text-secondary-700 mb-2">
          Descuento global:
        </p>
        <div className="flex gap-2">
          <div className="flex-1">
            <div className="relative">
              <Input
                type="number"
                value={discountPercent || ''}
                onChange={(e) =>
                  setDiscountPercent(parseFloat(e.target.value) || 0)
                }
                placeholder="0"
                className="pr-8 text-sm"
                min="0"
                max="100"
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-secondary-400">
                %
              </span>
            </div>
          </div>
          <span className="self-center text-secondary-400">o</span>
          <div className="flex-1">
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary-400">
                $
              </span>
              <Input
                type="number"
                value={discountAmount || ''}
                onChange={(e) =>
                  setDiscountAmount(parseFloat(e.target.value) || 0)
                }
                placeholder="0"
                className="pl-8 text-sm"
                min="0"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Totals */}
      <div className="py-3 border-t border-secondary-200 space-y-2">
        <div className="flex justify-between text-secondary-600">
          <span>Subtotal</span>
          <span>{formatCurrency(subtotal + totalDiscount)}</span>
        </div>
        {totalDiscount > 0 && (
          <div className="flex justify-between text-red-600">
            <span>Descuentos</span>
            <span>-{formatCurrency(totalDiscount)}</span>
          </div>
        )}
        <div className="flex justify-between text-secondary-600">
          <span>IVA (16%)</span>
          <span>{formatCurrency(tax)}</span>
        </div>
        <div className="flex justify-between text-xl font-bold text-secondary-900 pt-2 border-t border-secondary-200">
          <span>Total</span>
          <span>{formatCurrency(total)}</span>
        </div>
      </div>

      {/* Checkout Button */}
      <Button
        onClick={onCheckout}
        disabled={isProcessing || items.length === 0}
        className="w-full py-4 text-lg"
      >
        {isProcessing ? 'Procesando...' : 'Cobrar'}
      </Button>
    </div>
  )
}
