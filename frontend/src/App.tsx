import { useEffect, useRef } from 'react'
import { RouterProvider } from 'react-router-dom'
import { router } from './router'
import { useAuthStore } from './store/authStore'
import { ThemeProvider } from './providers/ThemeProvider'

function App() {
  const checkAuth = useAuthStore((state) => state.checkAuth)
  const hasCheckedAuth = useRef(false)

  useEffect(() => {
    // Check authentication status only once on app load
    if (!hasCheckedAuth.current) {
      hasCheckedAuth.current = true
      checkAuth()
    }
  }, [checkAuth])

  return (
    <ThemeProvider>
      <RouterProvider router={router} />
    </ThemeProvider>
  )
}

export default App
