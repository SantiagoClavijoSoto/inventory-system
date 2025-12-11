import { useEffect, useCallback, useRef, useState } from 'react'

interface UseBarcodeScanner {
  onScan: (barcode: string) => void
  enabled?: boolean
  minLength?: number
  maxDelay?: number
}

/**
 * Hook to detect barcode scanner input (USB hardware scanners).
 *
 * Hardware barcode scanners work by emulating keyboard input:
 * - They type characters very quickly (faster than human typing)
 * - They typically end with an Enter key
 *
 * This hook detects rapid consecutive keystrokes and interprets them as barcodes.
 */
export function useBarcodeScanner({
  onScan,
  enabled = true,
  minLength = 4,
  maxDelay = 50, // Max ms between keystrokes for scanner detection
}: UseBarcodeScanner) {
  const bufferRef = useRef<string>('')
  const lastKeyTimeRef = useRef<number>(0)
  const timeoutRef = useRef<number | null>(null)

  const resetBuffer = useCallback(() => {
    bufferRef.current = ''
    if (timeoutRef.current) {
      window.clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
  }, [])

  const processBarcode = useCallback(() => {
    const barcode = bufferRef.current.trim()

    if (barcode.length >= minLength) {
      onScan(barcode)
    }

    resetBuffer()
  }, [minLength, onScan, resetBuffer])

  useEffect(() => {
    if (!enabled) return

    const handleKeyDown = (event: KeyboardEvent) => {
      // Ignore if focus is on an input field (unless it's our hidden scanner input)
      const target = event.target as HTMLElement
      const isInputField =
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable

      // Allow scanner input if target has data-barcode-input attribute
      if (isInputField && !target.dataset.barcodeInput) {
        return
      }

      const currentTime = Date.now()
      const timeSinceLastKey = currentTime - lastKeyTimeRef.current
      lastKeyTimeRef.current = currentTime

      // If too much time has passed, reset the buffer
      if (timeSinceLastKey > maxDelay && bufferRef.current.length > 0) {
        resetBuffer()
      }

      // Handle Enter key - process barcode
      if (event.key === 'Enter') {
        event.preventDefault()
        processBarcode()
        return
      }

      // Only accept printable characters
      if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
        bufferRef.current += event.key

        // Clear any existing timeout
        if (timeoutRef.current) {
          window.clearTimeout(timeoutRef.current)
        }

        // Set timeout to process barcode if no more keys come
        timeoutRef.current = window.setTimeout(() => {
          // Only process if we have enough characters and no new input
          if (bufferRef.current.length >= minLength) {
            processBarcode()
          } else {
            resetBuffer()
          }
        }, maxDelay * 3)
      }
    }

    window.addEventListener('keydown', handleKeyDown)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current)
      }
    }
  }, [enabled, maxDelay, minLength, processBarcode, resetBuffer])

  return {
    resetBuffer,
    isEnabled: enabled,
  }
}

/**
 * Hook for manual barcode input field.
 * Handles Enter key to submit barcode.
 */
export function useManualBarcodeInput(onScan: (barcode: string) => void) {
  const [value, setValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim()
    if (trimmed.length > 0) {
      onScan(trimmed)
      setValue('')
    }
  }, [value, onScan])

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === 'Enter') {
        event.preventDefault()
        handleSubmit()
      }
    },
    [handleSubmit]
  )

  const focus = useCallback(() => {
    inputRef.current?.focus()
  }, [])

  return {
    value,
    setValue,
    inputRef,
    handleKeyDown,
    handleSubmit,
    focus,
  }
}
