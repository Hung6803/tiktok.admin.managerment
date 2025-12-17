'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'

/**
 * OAuth callback handler component
 * Processes TikTok OAuth callback redirect from backend
 */
function CallbackHandler() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing')
  const [error, setError] = useState('')
  const [accountName, setAccountName] = useState('')

  useEffect(() => {
    // Backend redirects here with query params: success, error, account
    const success = searchParams.get('success')
    const errorParam = searchParams.get('error')
    const account = searchParams.get('account')

    if (success === 'true') {
      setStatus('success')
      setAccountName(account || '')
      setTimeout(() => router.push('/accounts'), 1500)
      return
    }

    if (errorParam) {
      setStatus('error')
      // Map error codes to user-friendly messages
      const errorMessages: Record<string, string> = {
        'session_expired': 'Session expired. Please try again.',
        'missing_params': 'Invalid callback. Missing parameters.',
        'user_not_found': 'User not found. Please login again.',
        'csrf_failed': 'Security check failed. Please try again.',
        'connection_failed': 'Failed to connect TikTok account.',
        'access_denied': 'TikTok access was denied.',
      }
      setError(errorMessages[errorParam] || `Error: ${errorParam}`)
      setTimeout(() => router.push('/accounts'), 3000)
      return
    }

    // No success or error - still processing or invalid state
    setStatus('error')
    setError('Invalid callback state')
    setTimeout(() => router.push('/accounts'), 3000)
  }, [searchParams, router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full p-8 bg-white rounded-lg shadow text-center">
        {status === 'processing' && (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold mb-2">Connecting TikTok Account</h2>
            <p className="text-gray-600">Please wait while we complete the connection...</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="text-green-600 text-5xl mb-4">✓</div>
            <h2 className="text-xl font-semibold mb-2">Success!</h2>
            <p className="text-gray-600">
              {accountName
                ? `TikTok account @${accountName} has been connected.`
                : 'Your TikTok account has been connected.'
              }
            </p>
            <p className="text-sm text-gray-500 mt-2">Redirecting to accounts...</p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="text-red-600 text-5xl mb-4">✕</div>
            <h2 className="text-xl font-semibold mb-2">Connection Failed</h2>
            <p className="text-gray-600 mb-2">{error}</p>
            <p className="text-sm text-gray-500">Redirecting to accounts page...</p>
          </>
        )}
      </div>
    </div>
  )
}

/**
 * OAuth callback page wrapper with Suspense
 */
export default function CallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full p-8 bg-white rounded-lg shadow text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold mb-2">Loading...</h2>
        </div>
      </div>
    }>
      <CallbackHandler />
    </Suspense>
  )
}
