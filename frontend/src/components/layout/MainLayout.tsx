import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { ForcePasswordChangeModal } from '@/components/auth/ForcePasswordChangeModal'

export function MainLayout() {
  return (
    <div className="min-h-screen bg-secondary-50">
      <Sidebar />
      <div className="pl-64">
        <Header />
        <main className="p-6">
          <Outlet />
        </main>
      </div>
      <ForcePasswordChangeModal />
    </div>
  )
}
