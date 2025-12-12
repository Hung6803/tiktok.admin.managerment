'use client'

import { useState } from 'react'
import { useAuth } from '@/lib/auth-context'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { AccountSettings } from '@/components/settings/account-settings'
import { PreferenceSettings } from '@/components/settings/preference-settings'
import { SecuritySettings } from '@/components/settings/security-settings'
import { Skeleton } from '@/components/ui/skeleton'
import { User, Shield, Bell } from 'lucide-react'

/**
 * Settings page with tabbed navigation
 * Contains: Account, Preferences, Security sections
 */
export default function SettingsPage() {
  const { user, loading } = useAuth()
  const [activeTab, setActiveTab] = useState('account')

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-12 w-full max-w-md" />
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Manage your account and preferences</p>
      </div>

      <Tabs className="space-y-6">
        <TabsList>
          <TabsTrigger
            data-state={activeTab === 'account' ? 'active' : 'inactive'}
            onClick={() => setActiveTab('account')}
          >
            <User className="h-4 w-4 mr-2" />
            Account
          </TabsTrigger>
          <TabsTrigger
            data-state={activeTab === 'preferences' ? 'active' : 'inactive'}
            onClick={() => setActiveTab('preferences')}
          >
            <Bell className="h-4 w-4 mr-2" />
            Preferences
          </TabsTrigger>
          <TabsTrigger
            data-state={activeTab === 'security' ? 'active' : 'inactive'}
            onClick={() => setActiveTab('security')}
          >
            <Shield className="h-4 w-4 mr-2" />
            Security
          </TabsTrigger>
        </TabsList>

        <TabsContent className={activeTab === 'account' ? '' : 'hidden'}>
          <AccountSettings user={user} />
        </TabsContent>

        <TabsContent className={activeTab === 'preferences' ? '' : 'hidden'}>
          <PreferenceSettings user={user} />
        </TabsContent>

        <TabsContent className={activeTab === 'security' ? '' : 'hidden'}>
          <SecuritySettings />
        </TabsContent>
      </Tabs>
    </div>
  )
}
