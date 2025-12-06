'use client'

import { useAccounts, useGetAuthUrl } from '@/hooks/use-accounts'
import { Button } from '@/components/ui/button'
import { AccountCard } from '@/components/accounts/account-card'
import { Skeleton } from '@/components/ui/skeleton'
import { Plus, AlertCircle } from 'lucide-react'

/**
 * Accounts management page
 * Displays all connected TikTok accounts with OAuth connection flow
 */
export default function AccountsPage() {
  const { data: accounts, isLoading, error } = useAccounts()
  const getAuthUrl = useGetAuthUrl()

  const handleConnectAccount = async () => {
    try {
      const authUrl = await getAuthUrl.mutateAsync()
      window.location.href = authUrl
    } catch (error) {
      console.error('Failed to get auth URL:', error)
    }
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900">Error loading accounts</h3>
            <p className="text-sm text-red-700 mt-1">
              {(error as any)?.response?.data?.message || 'Failed to load TikTok accounts. Please try again.'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">TikTok Accounts</h1>
          <p className="text-gray-600 mt-1">Manage your connected TikTok accounts</p>
        </div>
        <Button onClick={handleConnectAccount} disabled={getAuthUrl.isPending}>
          <Plus className="mr-2 h-4 w-4" />
          {getAuthUrl.isPending ? 'Loading...' : 'Connect Account'}
        </Button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="space-y-4 p-6 border rounded-lg">
              <div className="flex items-center gap-3">
                <Skeleton className="h-12 w-12 rounded-full" />
                <div className="space-y-2">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-24" />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <Skeleton className="h-16" />
                <Skeleton className="h-16" />
                <Skeleton className="h-16" />
              </div>
            </div>
          ))}
        </div>
      ) : accounts && accounts.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <div className="max-w-md mx-auto">
            <div className="h-16 w-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Plus className="h-8 w-8 text-blue-600" />
            </div>
            <h2 className="text-xl font-semibold mb-2">No TikTok accounts connected</h2>
            <p className="text-gray-600 mb-6">
              Connect your first TikTok account to start scheduling and managing your content
            </p>
            <Button onClick={handleConnectAccount} disabled={getAuthUrl.isPending}>
              <Plus className="mr-2 h-4 w-4" />
              Connect Your First Account
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {accounts?.map((account) => (
            <AccountCard key={account.id} account={account} />
          ))}
        </div>
      )}
    </div>
  )
}
