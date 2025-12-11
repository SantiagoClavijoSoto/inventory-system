import { useState, useCallback, useRef, useEffect } from 'react'
import { Search, Package, AlertCircle } from 'lucide-react'
import { Input, Spinner } from '@/components/ui'
import { productApi } from '@/api/inventory'
import type { Product } from '@/types'
import { useBarcodeScanner } from '@/components/barcode/useBarcodeScanner'
import { useAuthStore } from '@/store/authStore'
import { formatCurrency } from '@/utils/formatters'

interface ProductSearchProps {
  onSelectProduct: (product: Product) => void
  onError?: (error: string) => void
}

interface SearchResult extends Product {
  stock_in_branch?: number
  available_in_branch?: number
}

export function ProductSearch({ onSelectProduct, onError }: ProductSearchProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const resultsRef = useRef<HTMLDivElement>(null)
  const searchTimeoutRef = useRef<number | null>(null)

  const currentBranch = useAuthStore((state) => state.currentBranch)

  // Handle barcode scan (from USB scanner)
  const handleBarcodeScan = useCallback(
    async (barcode: string) => {
      if (!currentBranch) {
        onError?.('Selecciona una sucursal primero')
        return
      }

      setIsLoading(true)
      try {
        const data = await productApi.getByBarcode(barcode, currentBranch.id)
        if (data.product) {
          onSelectProduct(data.product)
          setSearchTerm('')
          setResults([])
          setShowResults(false)
        }
      } catch (error: unknown) {
        const errorMsg = error instanceof Error ? error.message : 'Producto no encontrado'
        onError?.(errorMsg)
      } finally {
        setIsLoading(false)
      }
    },
    [currentBranch, onSelectProduct, onError]
  )

  // USB barcode scanner hook
  useBarcodeScanner({
    onScan: handleBarcodeScan,
    enabled: true,
    minLength: 4,
    maxDelay: 50,
  })

  // Search products
  const searchProducts = useCallback(
    async (term: string) => {
      if (!term || term.length < 2) {
        setResults([])
        setShowResults(false)
        return
      }

      setIsLoading(true)
      try {
        // First try barcode search
        if (currentBranch) {
          try {
            const barcodeResult = await productApi.getByBarcode(term, currentBranch.id)
            if (barcodeResult.product) {
              setResults([
                {
                  ...barcodeResult.product,
                  stock_in_branch: barcodeResult.stock_in_branch,
                  available_in_branch: barcodeResult.available_in_branch,
                },
              ])
              setShowResults(true)
              setSelectedIndex(0)
              setIsLoading(false)
              return
            }
          } catch {
            // Not a barcode, continue with text search
          }
        }

        // Text search
        const data = await productApi.getAll({
          search: term,
          is_active: true,
          is_sellable: true,
          page_size: 10,
        })
        setResults(data.results)
        setShowResults(true)
        setSelectedIndex(data.results.length > 0 ? 0 : -1)
      } catch (error: unknown) {
        const errorMsg = error instanceof Error ? error.message : 'Error buscando productos'
        onError?.(errorMsg)
        setResults([])
      } finally {
        setIsLoading(false)
      }
    },
    [currentBranch, onError]
  )

  // Debounced search
  const handleSearchChange = (value: string) => {
    setSearchTerm(value)
    setSelectedIndex(-1)

    if (searchTimeoutRef.current) {
      window.clearTimeout(searchTimeoutRef.current)
    }

    searchTimeoutRef.current = window.setTimeout(() => {
      searchProducts(value)
    }, 300)
  }

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showResults || results.length === 0) {
      if (e.key === 'Enter' && searchTerm.length > 0) {
        searchProducts(searchTerm)
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1))
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex((prev) => Math.max(prev - 1, 0))
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && results[selectedIndex]) {
          handleSelectProduct(results[selectedIndex])
        }
        break
      case 'Escape':
        setShowResults(false)
        setSelectedIndex(-1)
        break
    }
  }

  // Handle product selection
  const handleSelectProduct = (product: SearchResult) => {
    onSelectProduct(product)
    setSearchTerm('')
    setResults([])
    setShowResults(false)
    setSelectedIndex(-1)
    inputRef.current?.focus()
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        resultsRef.current &&
        !resultsRef.current.contains(e.target as Node) &&
        !inputRef.current?.contains(e.target as Node)
      ) {
        setShowResults(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Scroll selected item into view
  useEffect(() => {
    if (selectedIndex >= 0 && resultsRef.current) {
      const selectedEl = resultsRef.current.querySelector(
        `[data-index="${selectedIndex}"]`
      )
      selectedEl?.scrollIntoView({ block: 'nearest' })
    }
  }, [selectedIndex])

  return (
    <div className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-secondary-400" />
        <Input
          ref={inputRef}
          type="text"
          value={searchTerm}
          onChange={(e) => handleSearchChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => results.length > 0 && setShowResults(true)}
          placeholder="Buscar producto por nombre, SKU o código de barras..."
          className="pl-10 pr-10 text-lg"
          data-barcode-input="true"
          autoFocus
        />
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <Spinner className="w-5 h-5" />
          </div>
        )}
      </div>

      {/* Search Results Dropdown */}
      {showResults && (
        <div
          ref={resultsRef}
          className="absolute top-full left-0 right-0 mt-1 bg-white border border-secondary-200 rounded-lg shadow-lg z-50 max-h-80 overflow-y-auto"
        >
          {results.length === 0 ? (
            <div className="p-4 text-center text-secondary-500">
              <AlertCircle className="w-8 h-8 mx-auto mb-2 text-secondary-400" />
              <p>No se encontraron productos</p>
            </div>
          ) : (
            results.map((product, index) => (
              <button
                key={product.id}
                data-index={index}
                onClick={() => handleSelectProduct(product)}
                className={`w-full flex items-center gap-3 p-3 text-left hover:bg-primary-50 transition-colors ${
                  index === selectedIndex ? 'bg-primary-50' : ''
                } ${index !== results.length - 1 ? 'border-b border-secondary-100' : ''}`}
              >
                {product.image ? (
                  <img
                    src={product.image}
                    alt={product.name}
                    className="w-12 h-12 object-cover rounded-lg"
                  />
                ) : (
                  <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center">
                    <Package className="w-6 h-6 text-secondary-400" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-secondary-900 truncate">
                    {product.name}
                  </p>
                  <div className="flex items-center gap-2 text-sm text-secondary-500">
                    <span className="font-mono">{product.sku}</span>
                    {product.barcode && (
                      <>
                        <span>•</span>
                        <span className="font-mono">{product.barcode}</span>
                      </>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-secondary-900">
                    {formatCurrency(product.sale_price)}
                  </p>
                  {product.available_in_branch !== undefined && (
                    <p
                      className={`text-sm ${
                        product.available_in_branch > 0
                          ? 'text-green-600'
                          : 'text-red-600'
                      }`}
                    >
                      Stock: {product.available_in_branch}
                    </p>
                  )}
                </div>
              </button>
            ))
          )}
        </div>
      )}

      {/* Helper text */}
      <p className="mt-2 text-xs text-secondary-500">
        <span className="inline-flex items-center gap-1">
          <kbd className="px-1.5 py-0.5 bg-secondary-100 rounded text-xs font-mono">
            ↑↓
          </kbd>
          navegar
        </span>
        <span className="mx-2">•</span>
        <span className="inline-flex items-center gap-1">
          <kbd className="px-1.5 py-0.5 bg-secondary-100 rounded text-xs font-mono">
            Enter
          </kbd>
          seleccionar
        </span>
        <span className="mx-2">•</span>
        <span className="text-green-600">Escáner USB activo</span>
      </p>
    </div>
  )
}
