import { useState, useCallback, useRef, useEffect } from 'react'
import { useBarcodeScanner, useManualBarcodeInput } from './useBarcodeScanner'
import { CameraScanner } from './CameraScanner'
import { Button, Input } from '@/components/ui'

type ScanMode = 'usb' | 'camera' | 'manual'

interface BarcodeScannerProps {
  onScan: (barcode: string) => void
  onError?: (error: string) => void
  placeholder?: string
  autoFocus?: boolean
  className?: string
  showModeSelector?: boolean
  defaultMode?: ScanMode
}

/**
 * Complete barcode scanner component supporting:
 * - USB hardware scanners (keyboard emulation)
 * - Camera scanning (using device camera)
 * - Manual input (text field)
 */
export function BarcodeScanner({
  onScan,
  onError,
  placeholder = 'Buscar producto o escanear código...',
  autoFocus = true,
  className = '',
  showModeSelector = true,
  defaultMode = 'usb',
}: BarcodeScannerProps) {
  const [mode, setMode] = useState<ScanMode>(defaultMode)
  const [lastScannedCode, setLastScannedCode] = useState<string>('')
  const inputRef = useRef<HTMLInputElement>(null)

  // Handle successful scan
  const handleScan = useCallback(
    (barcode: string) => {
      setLastScannedCode(barcode)
      onScan(barcode)
    },
    [onScan]
  )

  // USB scanner hook (always listening)
  useBarcodeScanner({
    onScan: handleScan,
    enabled: mode === 'usb',
    minLength: 4,
    maxDelay: 50,
  })

  // Manual input
  const {
    value: manualValue,
    setValue: setManualValue,
    handleKeyDown: handleManualKeyDown,
    handleSubmit: handleManualSubmit,
  } = useManualBarcodeInput(handleScan)

  // Auto-focus input
  useEffect(() => {
    if (autoFocus && (mode === 'usb' || mode === 'manual') && inputRef.current) {
      inputRef.current.focus()
    }
  }, [autoFocus, mode])

  // Mode icons
  const ModeIcon = ({ modeType }: { modeType: ScanMode }) => {
    switch (modeType) {
      case 'usb':
        return (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
            />
          </svg>
        )
      case 'camera':
        return (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
        )
      case 'manual':
        return (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
            />
          </svg>
        )
    }
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Mode selector */}
      {showModeSelector && (
        <div className="flex gap-2">
          <button
            onClick={() => setMode('usb')}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              mode === 'usb'
                ? 'bg-primary-100 text-primary-700 border-2 border-primary-500'
                : 'bg-secondary-100 text-secondary-600 border-2 border-transparent hover:bg-secondary-200'
            }`}
            title="Escáner USB"
          >
            <ModeIcon modeType="usb" />
            <span className="hidden sm:inline">Escáner USB</span>
          </button>

          <button
            onClick={() => setMode('camera')}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              mode === 'camera'
                ? 'bg-primary-100 text-primary-700 border-2 border-primary-500'
                : 'bg-secondary-100 text-secondary-600 border-2 border-transparent hover:bg-secondary-200'
            }`}
            title="Cámara"
          >
            <ModeIcon modeType="camera" />
            <span className="hidden sm:inline">Cámara</span>
          </button>

          <button
            onClick={() => setMode('manual')}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              mode === 'manual'
                ? 'bg-primary-100 text-primary-700 border-2 border-primary-500'
                : 'bg-secondary-100 text-secondary-600 border-2 border-transparent hover:bg-secondary-200'
            }`}
            title="Manual"
          >
            <ModeIcon modeType="manual" />
            <span className="hidden sm:inline">Manual</span>
          </button>
        </div>
      )}

      {/* Scanner area based on mode */}
      {mode === 'usb' && (
        <div className="space-y-2">
          <div className="relative">
            <input
              ref={inputRef}
              type="text"
              data-barcode-input="true"
              className="w-full px-4 py-3 pl-12 border-2 border-dashed border-secondary-300 rounded-lg bg-secondary-50 text-secondary-600 placeholder-secondary-400 focus:border-primary-500 focus:ring-2 focus:ring-primary-200 outline-none"
              placeholder={placeholder}
              readOnly
              onFocus={e => e.target.select()}
            />
            <div className="absolute left-4 top-1/2 -translate-y-1/2">
              <svg
                className="w-5 h-5 text-secondary-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"
                />
              </svg>
            </div>
            {mode === 'usb' && (
              <div className="absolute right-4 top-1/2 -translate-y-1/2">
                <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-700">
                  <span className="w-2 h-2 rounded-full bg-green-500 mr-1.5 animate-pulse" />
                  Escuchando
                </span>
              </div>
            )}
          </div>
          <p className="text-sm text-secondary-500 text-center">
            Escanea un código de barras con el lector USB
          </p>
        </div>
      )}

      {mode === 'camera' && (
        <CameraScanner
          onScan={handleScan}
          onError={err => onError?.(err.message)}
          enabled={mode === 'camera'}
        />
      )}

      {mode === 'manual' && (
        <div className="flex gap-2">
          <div className="flex-1">
            <Input
              ref={inputRef}
              type="text"
              value={manualValue}
              onChange={e => setManualValue(e.target.value)}
              onKeyDown={handleManualKeyDown}
              placeholder="Ingresa el código de barras o SKU..."
              className="text-lg"
            />
          </div>
          <Button onClick={handleManualSubmit} disabled={!manualValue.trim()}>
            Buscar
          </Button>
        </div>
      )}

      {/* Last scanned indicator */}
      {lastScannedCode && (
        <div className="flex items-center justify-center gap-2 py-2 px-4 bg-green-50 border border-green-200 rounded-lg">
          <svg
            className="w-5 h-5 text-green-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span className="text-sm text-green-700">
            Último código: <strong className="font-mono">{lastScannedCode}</strong>
          </span>
        </div>
      )}
    </div>
  )
}

export { CameraScanner } from './CameraScanner'
export { useBarcodeScanner, useManualBarcodeInput } from './useBarcodeScanner'
