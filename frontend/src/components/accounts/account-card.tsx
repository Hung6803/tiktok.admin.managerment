'use client'

import { TikTokAccount } from '@/types'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Trash2, RefreshCw, Users, Heart, Video, CheckCircle } from 'lucide-react'
import { useDeleteAccount, useSyncAccount } from '@/hooks/use-accounts'
import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'

interface AccountCardProps {
  account: TikTokAccount
}

/**
 * TikTok account card component
 * Displays account information and actions
 */
export function AccountCard({ account }: AccountCardProps) {
  const deleteAccount = useDeleteAccount()
  const syncAccount = useSyncAccount()
  const [showConfirm, setShowConfirm] = useState(false)

  const handleDelete = async () => {
    if (!showConfirm) {
      setShowConfirm(true)
      setTimeout(() => setShowConfirm(false), 3000)
      return
    }

    try {
      await deleteAccount.mutateAsync(account.id)
    } catch (error) {
      console.error('Failed to delete account:', error)
    }
  }

  const handleSync = async () => {
    try {
      await syncAccount.mutateAsync(account.id)
    } catch (error) {
      console.error('Failed to sync account:', error)
    }
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M'
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K'
    }
    return num.toString()
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <Avatar className="h-12 w-12">
              <AvatarImage src={account.avatar_url} alt={account.display_name} />
              <AvatarFallback>{account.username.charAt(0).toUpperCase()}</AvatarFallback>
            </Avatar>
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                {account.display_name}
                {account.is_verified && (
                  <CheckCircle className="h-4 w-4 text-blue-600" />
                )}
              </CardTitle>
              <p className="text-sm text-gray-600">@{account.username}</p>
            </div>
          </div>
          <Badge variant={account.is_active ? 'success' : 'secondary'}>
            {account.is_active ? 'Active' : 'Inactive'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="flex items-center justify-center gap-1 text-gray-600 mb-1">
              <Users className="h-4 w-4" />
            </div>
            <p className="text-xl font-semibold">{formatNumber(account.follower_count)}</p>
            <p className="text-xs text-gray-600">Followers</p>
          </div>
          <div>
            <div className="flex items-center justify-center gap-1 text-gray-600 mb-1">
              <Heart className="h-4 w-4" />
            </div>
            <p className="text-xl font-semibold">{formatNumber(account.likes_count)}</p>
            <p className="text-xs text-gray-600">Likes</p>
          </div>
          <div>
            <div className="flex items-center justify-center gap-1 text-gray-600 mb-1">
              <Video className="h-4 w-4" />
            </div>
            <p className="text-xl font-semibold">{formatNumber(account.video_count)}</p>
            <p className="text-xs text-gray-600">Videos</p>
          </div>
        </div>

        {account.last_synced_at && (
          <p className="text-xs text-gray-500 mt-4 text-center">
            Last synced {formatDistanceToNow(new Date(account.last_synced_at), { addSuffix: true })}
          </p>
        )}
      </CardContent>

      <CardFooter className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          className="flex-1"
          onClick={handleSync}
          disabled={syncAccount.isPending}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${syncAccount.isPending ? 'animate-spin' : ''}`} />
          Sync
        </Button>
        <Button
          variant={showConfirm ? 'destructive' : 'outline'}
          size="sm"
          onClick={handleDelete}
          disabled={deleteAccount.isPending}
        >
          <Trash2 className="h-4 w-4 mr-2" />
          {showConfirm ? 'Confirm?' : 'Delete'}
        </Button>
      </CardFooter>
    </Card>
  )
}
