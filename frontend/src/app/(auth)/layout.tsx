import { ReactNode } from 'react'
import Link from 'next/link'

/**
 * Auth layout wrapper for login and register pages
 * Provides centered layout with background styling and legal links footer
 */
export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 to-gray-100">
      <div className="flex-1 flex items-center justify-center">
        {children}
      </div>
      <footer className="py-4 text-center text-sm text-gray-500">
        <div className="flex items-center justify-center gap-4">
          <Link href="/terms" className="hover:text-gray-700 transition-colors">
            Terms of Service
          </Link>
          <span className="text-gray-300">|</span>
          <Link href="/privacy" className="hover:text-gray-700 transition-colors">
            Privacy Policy
          </Link>
        </div>
      </footer>
    </div>
  )
}
