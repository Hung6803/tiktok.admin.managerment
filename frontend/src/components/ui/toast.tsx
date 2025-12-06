'use client'

import * as React from "react"
import { cn } from "@/lib/utils"

export interface ToastProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'success' | 'error' | 'warning'
}

const Toast = React.forwardRef<HTMLDivElement, ToastProps>(
  ({ className, variant = 'default', ...props }, ref) => {
    const variantStyles = {
      default: 'bg-white border-gray-300',
      success: 'bg-green-50 border-green-500 text-green-900',
      error: 'bg-red-50 border-red-500 text-red-900',
      warning: 'bg-yellow-50 border-yellow-500 text-yellow-900',
    }

    return (
      <div
        ref={ref}
        className={cn(
          "pointer-events-auto fixed bottom-4 right-4 z-50 w-full max-w-sm rounded-lg border p-4 shadow-lg",
          variantStyles[variant],
          className
        )}
        {...props}
      />
    )
  }
)
Toast.displayName = "Toast"

export { Toast }
