import { useEffect } from 'react'
import { RouterProvider } from 'react-router-dom'
import { router } from './router'
import { useAuthStore } from './store/authStore'
import { ThemeProvider } from './providers/ThemeProvider'

function App() {
  const { checkAuth } = useAuthStore()

  useEffect(() => {
    // Check authentication status on app load
    checkAuth()
  }, [checkAuth])

  return (
    <ThemeProvider>
      <RouterProvider router={router} />
    </ThemeProvider>
  )
}

export default App
