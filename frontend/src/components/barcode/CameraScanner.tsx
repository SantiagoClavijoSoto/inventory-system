import { useEffect, useRef, useState, useCallback } from 'react'
import { BrowserMultiFormatReader, NotFoundException } from '@zxing/library'

interface CameraScannerProps {
  onScan: (barcode: string) => void
  onError?: (error: Error) => void
  enabled?: boolean
  className?: string
}

/**
 * Camera-based barcode scanner using @zxing/library.
 * Supports various barcode formats including EAN-13, EAN-8, UPC, Code128, etc.
 */
export function CameraScanner({
  onScan,
  onError,
  enabled = true,
  className = '',
}: CameraScannerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const readerRef = useRef<BrowserMultiFormatReader | null>(null)
  const [isInitializing, setIsInitializing] = useState(true)
  const [hasCamera, setHasCamera] = useState(true)
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([])
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('')
  const lastScannedRef = useRef<string>('')
  const lastScanTimeRef = useRef<number>(0)

  // Debounce duplicate scans
  const handleScan = useCallback(
    (barcode: string) => {
      const now = Date.now()
      // Prevent same barcode from being processed within 2 seconds
      if (
        barcode === lastScannedRef.current &&
        now - lastScanTimeRef.current < 2000
      ) {
        return
      }

      lastScannedRef.current = barcode
      lastScanTimeRef.current = now
      onScan(barcode)
    },
    [onScan]
  )

  // Get available cameras
  useEffect(() => {
    async function getDevices() {
      try {
        // Request camera permission first
        await navigator.mediaDevices.getUserMedia({ video: true })

        const allDevices = await navigator.mediaDevices.enumerateDevices()
        const videoDevices = allDevices.filter(
          device => device.kind === 'videoinput'
        )

        setDevices(videoDevices)

        if (videoDevices.length > 0) {
          // Prefer back camera on mobile devices
          const backCamera = videoDevices.find(
            device =>
              device.label.toLowerCase().includes('back') ||
              device.label.toLowerCase().includes('trasera') ||
              device.label.toLowerCase().includes('environment')
          )
          setSelectedDeviceId(backCamera?.deviceId || videoDevices[0].deviceId)
        } else {
          setHasCamera(false)
        }
      } catch (error) {
        console.error('Error accessing camera:', error)
        setHasCamera(false)
        onError?.(error as Error)
      }
    }

    getDevices()
  }, [onError])

  // Initialize scanner
  useEffect(() => {
    if (!enabled || !hasCamera || !selectedDeviceId || !videoRef.current) {
      return
    }

    const reader = new BrowserMultiFormatReader()
    readerRef.current = reader
    setIsInitializing(true)

    let mounted = true

    async function startScanning() {
      try {
        await reader.decodeFromVideoDevice(
          selectedDeviceId,
          videoRef.current!,
          (result, error) => {
            if (!mounted) return

            if (result) {
              handleScan(result.getText())
            }

            if (error && !(error instanceof NotFoundException)) {
              // NotFoundException is normal when no barcode is visible
              console.error('Scanning error:', error)
            }
          }
        )

        if (mounted) {
          setIsInitializing(false)
        }
      } catch (error) {
        console.error('Failed to start scanning:', error)
        if (mounted) {
          setIsInitializing(false)
          onError?.(error as Error)
        }
      }
    }

    startScanning()

    return () => {
      mounted = false
      reader.reset()
      readerRef.current = null
    }
  }, [enabled, hasCamera, selectedDeviceId, handleScan, onError])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      readerRef.current?.reset()
    }
  }, [])

  if (!hasCamera) {
    return (
      <div className={`bg-secondary-100 rounded-lg p-6 text-center ${className}`}>
        <svg
          className="mx-auto h-12 w-12 text-secondary-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
          />
        </svg>
        <p className="mt-2 text-secondary-600">
          No se detectó cámara o el acceso fue denegado
        </p>
        <p className="mt-1 text-sm text-secondary-500">
          Usa el escáner USB o ingresa el código manualmente
        </p>
      </div>
    )
  }

  return (
    <div className={`relative ${className}`}>
      {/* Camera selector */}
      {devices.length > 1 && (
        <select
          value={selectedDeviceId}
          onChange={e => setSelectedDeviceId(e.target.value)}
          className="absolute top-2 right-2 z-10 bg-black/50 text-white text-sm rounded px-2 py-1"
        >
          {devices.map(device => (
            <option key={device.deviceId} value={device.deviceId}>
              {device.label || `Cámara ${devices.indexOf(device) + 1}`}
            </option>
          ))}
        </select>
      )}

      {/* Video preview */}
      <div className="relative bg-black rounded-lg overflow-hidden aspect-video">
        <video
          ref={videoRef}
          className="w-full h-full object-cover"
          playsInline
          muted
        />

        {/* Scanning indicator */}
        {!isInitializing && (
          <div className="absolute inset-0 pointer-events-none">
            {/* Scanning frame */}
            <div className="absolute inset-4 sm:inset-8 border-2 border-white/30 rounded-lg">
              {/* Animated scan line */}
              <div className="absolute top-0 left-0 right-0 h-0.5 bg-primary-500 animate-scan" />

              {/* Corner markers */}
              <div className="absolute -top-0.5 -left-0.5 w-6 h-6 border-t-2 border-l-2 border-primary-500 rounded-tl" />
              <div className="absolute -top-0.5 -right-0.5 w-6 h-6 border-t-2 border-r-2 border-primary-500 rounded-tr" />
              <div className="absolute -bottom-0.5 -left-0.5 w-6 h-6 border-b-2 border-l-2 border-primary-500 rounded-bl" />
              <div className="absolute -bottom-0.5 -right-0.5 w-6 h-6 border-b-2 border-r-2 border-primary-500 rounded-br" />
            </div>
          </div>
        )}

        {/* Loading overlay */}
        {isInitializing && (
          <div className="absolute inset-0 bg-black/70 flex items-center justify-center">
            <div className="text-center">
              <svg
                className="animate-spin h-8 w-8 text-primary-500 mx-auto"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <p className="mt-2 text-white text-sm">Iniciando cámara...</p>
            </div>
          </div>
        )}
      </div>

      <p className="mt-2 text-sm text-secondary-500 text-center">
        Apunta la cámara al código de barras
      </p>
    </div>
  )
}
