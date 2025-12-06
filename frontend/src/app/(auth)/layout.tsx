import { ReactNode } from 'react'

/**
 * Auth layout wrapper for login and register pages
 * Provides centered layout with background styling
 */
export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-gray-100">
      {children}
    </div>
  )
}
