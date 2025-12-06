'use client'

import { Menu } from 'lucide-react'
import { useAuth } from '@/lib/auth-context'

/**
 * Dashboard header component
 * Displays page title and user info for mobile view
 */
export function Header() {
  const { user } = useAuth()

  return (
    <header className="md:hidden bg-white border-b border-gray-200 px-4 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            className="p-2 hover:bg-gray-100 rounded-lg"
            aria-label="Open menu"
          >
            <Menu className="h-6 w-6" />
          </button>
          <h1 className="text-xl font-bold">TikTok Manager</h1>
        </div>

        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center">
            <span className="text-xs font-medium text-white">
              {user?.username?.charAt(0).toUpperCase()}
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}
