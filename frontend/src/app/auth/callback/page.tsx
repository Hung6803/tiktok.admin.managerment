'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api-client'

/**
 * OAuth callback handler component
 * Processes TikTok OAuth callback and redirects to accounts page
 */
function CallbackHandler() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing')
  const [error, setError] = useState('')

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code')
      const state = searchParams.get('state')
      const errorParam = searchParams.get('error')

      if (errorParam) {
        setStatus('error')
        setError(`OAuth error: ${errorParam}`)
        setTimeout(() => router.push('/accounts'), 3000)
        return
      }

      if (!code) {
        setStatus('error')
        setError('No authorization code received')
        setTimeout(() => router.push('/accounts'), 3000)
        return
      }

      try {
        // Send authorization code to backend
        await apiClient.get('/tiktok/callback', {
          params: { code, state }
        })

        setStatus('success')
        setTimeout(() => router.push('/accounts'), 1500)
      } catch (err: any) {
        setStatus('error')
        const errorMessage = err.response?.data?.message || 'Failed to connect TikTok account'
        setError(errorMessage)
        setTimeout(() => router.push('/accounts'), 3000)
      }
    }

    handleCallback()
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
            <p className="text-gray-600">Your TikTok account has been connected.</p>
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
