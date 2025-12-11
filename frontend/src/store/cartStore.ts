import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import type { Product, CartItem, PaymentMethod } from '@/types'

interface CartState {
  // Cart items
  items: CartItem[]

  // Customer info
  customerName: string
  customerPhone: string
  customerEmail: string

  // Discount
  discountPercent: number
  discountAmount: number

  // Payment
  paymentMethod: PaymentMethod
  amountTendered: number
  paymentReference: string

  // Notes
  notes: string

  // Computed values (as functions to avoid stale state)
  getSubtotal: () => number
  getTotalDiscount: () => number
  getTax: () => number
  getTotal: () => number
  getChange: () => number
  getItemCount: () => number
  getTotalQuantity: () => number

  // Actions
  addItem: (product: Product, quantity?: number) => void
  updateItemQuantity: (productId: number, quantity: number) => void
  updateItemDiscount: (productId: number, discount: number) => void
  updateItemPrice: (productId: number, price: number) => void
  removeItem: (productId: number) => void
  clearCart: () => void

  setCustomerName: (name: string) => void
  setCustomerPhone: (phone: string) => void
  setCustomerEmail: (email: string) => void

  setDiscountPercent: (percent: number) => void
  setDiscountAmount: (amount: number) => void

  setPaymentMethod: (method: PaymentMethod) => void
  setAmountTendered: (amount: number) => void
  setPaymentReference: (reference: string) => void

  setNotes: (notes: string) => void

  // For API submission
  getCreateSalePayload: () => {
    items: { product_id: number; quantity: number; discount?: number; custom_price?: number }[]
    payment_method: PaymentMethod
    amount_tendered: number
    discount_percent: number
    discount_amount: number
    customer_name: string
    customer_phone: string
    customer_email: string
    payment_reference: string
    notes: string
  }
}

const TAX_RATE = 0.16 // 16% IVA

export const useCartStore = create<CartState>()(
  devtools(
    (set, get) => ({
      // Initial state
      items: [],
      customerName: '',
      customerPhone: '',
      customerEmail: '',
      discountPercent: 0,
      discountAmount: 0,
      paymentMethod: 'cash',
      amountTendered: 0,
      paymentReference: '',
      notes: '',

      // Computed values
      getSubtotal: () => {
        return get().items.reduce((sum, item) => {
          const price = item.customPrice ?? item.product.sale_price
          return sum + (price * item.quantity) - item.discount
        }, 0)
      },

      getTotalDiscount: () => {
        const state = get()
        const itemDiscounts = state.items.reduce((sum, item) => sum + item.discount, 0)
        const subtotal = state.getSubtotal() + itemDiscounts // Get subtotal before item discounts
        const percentDiscount = (subtotal * state.discountPercent) / 100
        return itemDiscounts + percentDiscount + state.discountAmount
      },

      getTax: () => {
        const state = get()
        const subtotal = state.getSubtotal()
        const globalDiscount = (subtotal * state.discountPercent) / 100 + state.discountAmount
        const taxableAmount = subtotal - globalDiscount
        return taxableAmount * TAX_RATE
      },

      getTotal: () => {
        const state = get()
        const subtotal = state.getSubtotal()
        const globalDiscount = (subtotal * state.discountPercent) / 100 + state.discountAmount
        const taxableAmount = subtotal - globalDiscount
        const tax = taxableAmount * TAX_RATE
        return taxableAmount + tax
      },

      getChange: () => {
        const state = get()
        const total = state.getTotal()
        return Math.max(0, state.amountTendered - total)
      },

      getItemCount: () => {
        return get().items.length
      },

      getTotalQuantity: () => {
        return get().items.reduce((sum, item) => sum + item.quantity, 0)
      },

      // Actions
      addItem: (product, quantity = 1) => {
        set((state) => {
          const existingIndex = state.items.findIndex(
            item => item.product.id === product.id
          )

          if (existingIndex >= 0) {
            // Update existing item quantity
            const newItems = [...state.items]
            newItems[existingIndex] = {
              ...newItems[existingIndex],
              quantity: newItems[existingIndex].quantity + quantity
            }
            return { items: newItems }
          }

          // Add new item
          return {
            items: [
              ...state.items,
              { product, quantity, discount: 0 }
            ]
          }
        })
      },

      updateItemQuantity: (productId, quantity) => {
        if (quantity <= 0) {
          get().removeItem(productId)
          return
        }

        set((state) => ({
          items: state.items.map(item =>
            item.product.id === productId
              ? { ...item, quantity }
              : item
          )
        }))
      },

      updateItemDiscount: (productId, discount) => {
        set((state) => ({
          items: state.items.map(item =>
            item.product.id === productId
              ? { ...item, discount: Math.max(0, discount) }
              : item
          )
        }))
      },

      updateItemPrice: (productId, price) => {
        set((state) => ({
          items: state.items.map(item =>
            item.product.id === productId
              ? { ...item, customPrice: price }
              : item
          )
        }))
      },

      removeItem: (productId) => {
        set((state) => ({
          items: state.items.filter(item => item.product.id !== productId)
        }))
      },

      clearCart: () => {
        set({
          items: [],
          customerName: '',
          customerPhone: '',
          customerEmail: '',
          discountPercent: 0,
          discountAmount: 0,
          paymentMethod: 'cash',
          amountTendered: 0,
          paymentReference: '',
          notes: ''
        })
      },

      setCustomerName: (name) => set({ customerName: name }),
      setCustomerPhone: (phone) => set({ customerPhone: phone }),
      setCustomerEmail: (email) => set({ customerEmail: email }),

      setDiscountPercent: (percent) => set({
        discountPercent: Math.min(100, Math.max(0, percent)),
        discountAmount: 0 // Clear fixed discount when setting percent
      }),

      setDiscountAmount: (amount) => set({
        discountAmount: Math.max(0, amount),
        discountPercent: 0 // Clear percent discount when setting fixed amount
      }),

      setPaymentMethod: (method) => set({ paymentMethod: method }),
      setAmountTendered: (amount) => set({ amountTendered: Math.max(0, amount) }),
      setPaymentReference: (reference) => set({ paymentReference: reference }),

      setNotes: (notes) => set({ notes }),

      getCreateSalePayload: () => {
        const state = get()
        return {
          items: state.items.map(item => ({
            product_id: item.product.id,
            quantity: item.quantity,
            discount: item.discount > 0 ? item.discount : undefined,
            custom_price: item.customPrice
          })),
          payment_method: state.paymentMethod,
          amount_tendered: state.amountTendered,
          discount_percent: state.discountPercent,
          discount_amount: state.discountAmount,
          customer_name: state.customerName,
          customer_phone: state.customerPhone,
          customer_email: state.customerEmail,
          payment_reference: state.paymentReference,
          notes: state.notes
        }
      }
    }),
    { name: 'cart-store' }
  )
)
