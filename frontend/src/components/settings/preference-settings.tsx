'use client'

import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { User, PostVisibility } from '@/types'
import { Loader2, Check, Info } from 'lucide-react'

interface PreferenceSettingsProps {
  user: User | null
}

/**
 * Preference settings section
 * Default visibility, notification preferences
 */
export function PreferenceSettings({ user: _user }: PreferenceSettingsProps) {
  const [defaultVisibility, setDefaultVisibility] = useState<PostVisibility>(PostVisibility.PUBLIC)
  const [emailNotifications, setEmailNotifications] = useState(true)
  const [publishNotifications, setPublishNotifications] = useState(true)
  const [saving, setSaving] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')

  const handleSave = async () => {
    setSaving(true)
    // Simulated save - preferences stored in localStorage for now
    // Backend integration can be added later
    try {
      localStorage.setItem(
        'userPreferences',
        JSON.stringify({ defaultVisibility, emailNotifications, publishNotifications })
      )
      setSuccessMessage('Preferences saved')
      setTimeout(() => setSuccessMessage(''), 3000)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Default Post Settings</CardTitle>
          <CardDescription>Configure default values for new posts</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="visibility">Default Visibility</Label>
            <select
              id="visibility"
              value={defaultVisibility}
              onChange={(e) => setDefaultVisibility(e.target.value as PostVisibility)}
              className="flex h-10 w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2"
            >
              <option value={PostVisibility.PUBLIC}>Public - Everyone can see</option>
              <option value={PostVisibility.FRIENDS}>Friends - Mutual followers only</option>
              <option value={PostVisibility.PRIVATE}>Private - Only you</option>
            </select>
            <p className="text-xs text-gray-500">Applied when creating new posts</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Notifications</CardTitle>
          <CardDescription>Manage how you receive updates</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Email Notifications</Label>
              <p className="text-xs text-gray-500">Receive updates via email</p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={emailNotifications}
              onClick={() => setEmailNotifications(!emailNotifications)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                emailNotifications ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  emailNotifications ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Publish Notifications</Label>
              <p className="text-xs text-gray-500">Get notified when posts are published</p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={publishNotifications}
              onClick={() => setPublishNotifications(!publishNotifications)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                publishNotifications ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  publishNotifications ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-2">
            <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-blue-700">
              Notification preferences are stored locally. Backend integration coming soon.
            </p>
          </div>

          {successMessage && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center gap-2">
              <Check className="h-4 w-4 text-green-600" />
              <p className="text-sm text-green-700">{successMessage}</p>
            </div>
          )}
        </CardContent>
        <CardFooter>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Preferences'
            )}
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
