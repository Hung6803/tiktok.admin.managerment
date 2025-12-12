'use client'

import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useUpdateProfile, COMMON_TIMEZONES } from '@/hooks/use-settings'
import { User } from '@/types'
import { Loader2, Check, AlertCircle, Calendar } from 'lucide-react'

interface AccountSettingsProps {
  user: User | null
}

/**
 * Account settings section
 * Allows editing username and timezone
 */
export function AccountSettings({ user }: AccountSettingsProps) {
  const [username, setUsername] = useState(user?.username || '')
  const [timezone, setTimezone] = useState(user?.timezone || 'UTC')
  const [successMessage, setSuccessMessage] = useState('')
  const updateProfile = useUpdateProfile()

  const handleSave = async () => {
    setSuccessMessage('')
    try {
      await updateProfile.mutateAsync({ username, timezone })
      setSuccessMessage('Profile updated successfully')
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (error) {
      // Error handled by mutation
    }
  }

  const hasChanges = username !== user?.username || timezone !== user?.timezone
  const memberSince = user?.created_at
    ? new Date(user.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : 'Unknown'

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Profile Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" value={user?.email || ''} disabled className="bg-gray-50" />
            <p className="text-xs text-gray-500">Email cannot be changed</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="timezone">Timezone</Label>
            <select
              id="timezone"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="flex h-10 w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2"
            >
              {COMMON_TIMEZONES.map((tz) => (
                <option key={tz.value} value={tz.value}>
                  {tz.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500">Used for scheduling posts</p>
          </div>

          {updateProfile.error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-red-700">
                {(updateProfile.error as any)?.response?.data?.detail || 'Failed to update profile'}
              </p>
            </div>
          )}

          {successMessage && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center gap-2">
              <Check className="h-4 w-4 text-green-600" />
              <p className="text-sm text-green-700">{successMessage}</p>
            </div>
          )}
        </CardContent>
        <CardFooter>
          <Button onClick={handleSave} disabled={updateProfile.isPending || !hasChanges}>
            {updateProfile.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Changes'
            )}
          </Button>
        </CardFooter>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Account Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3 text-gray-600">
            <Calendar className="h-5 w-5" />
            <span>Member since {memberSince}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
