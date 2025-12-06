# Phase 06: Frontend Development

**Priority:** High
**Status:** ⚠️ Code Review Complete - Security Issues Found
**Estimated Time:** 8-10 hours
**Review Date:** 2025-12-06
**Quality Score:** B+ (85/100)

## Context Links

- [Main Plan](./plan.md)
- [Phase 04: Backend API](./phase-04-backend-api.md)

## Overview

Build Next.js frontend with authentication, account management, content scheduling, and analytics dashboard.

## Key Insights

- Use Next.js 14+ App Router
- Implement TanStack Query for data fetching
- Zustand for global state management
- Tailwind CSS for styling
- Shadcn/ui for component library
- React Hook Form for form handling
- Real-time updates with polling/WebSockets

## Requirements

### Functional Requirements
- User authentication (login/register)
- TikTok account connection flow
- Content upload interface
- Scheduling calendar
- Post management (CRUD)
- Analytics dashboard
- Notifications

### Non-Functional Requirements
- Responsive design (mobile, tablet, desktop)
- Fast page loads (< 2 seconds)
- Accessible (WCAG 2.1 AA)
- Intuitive UI/UX
- Real-time status updates
- Offline support (PWA optional)

## Architecture

```
frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/
│   │   ├── layout.tsx
│   │   ├── accounts/
│   │   ├── schedule/
│   │   ├── posts/
│   │   ├── analytics/
│   │   └── settings/
│   └── layout.tsx
├── components/
│   ├── ui/              # Shadcn components
│   ├── auth/
│   ├── accounts/
│   ├── posts/
│   └── analytics/
├── lib/
│   ├── api-client.ts
│   ├── auth-context.tsx
│   └── utils.ts
├── hooks/
│   ├── use-auth.ts
│   ├── use-accounts.ts
│   └── use-posts.ts
└── types/
    ├── account.ts
    └── post.ts
```

## Related Code Files

### Files to Create
- `frontend/lib/api-client.ts`
- `frontend/lib/auth-context.tsx`
- `frontend/hooks/use-auth.ts`
- `frontend/hooks/use-accounts.ts`
- `frontend/hooks/use-posts.ts`
- `frontend/app/(auth)/login/page.tsx`
- `frontend/app/(auth)/register/page.tsx`
- `frontend/app/(dashboard)/layout.tsx`
- `frontend/app/(dashboard)/accounts/page.tsx`
- `frontend/app/(dashboard)/schedule/page.tsx`
- `frontend/app/(dashboard)/posts/page.tsx`
- `frontend/components/accounts/account-card.tsx`
- `frontend/components/posts/post-form.tsx`
- `frontend/components/posts/calendar-view.tsx`
- `frontend/components/analytics/stats-dashboard.tsx`

## Implementation Steps

### 1. Setup API Client

```typescript
// frontend/lib/api-client.ts
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
```

### 2. Create Auth Context

```typescript
// frontend/lib/auth-context.tsx
'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from './api-client';
import { useRouter } from 'next/navigation';

interface User {
  id: string;
  email: string;
  username: string;
  timezone: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('access_token');
    if (token) {
      // Fetch user info
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await apiClient.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      localStorage.clear();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await apiClient.post('/auth/login', { email, password });
    const { access_token, refresh_token } = response.data;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);

    await fetchUser();
    router.push('/accounts');
  };

  const register = async (email: string, username: string, password: string) => {
    const response = await apiClient.post('/auth/register', {
      email,
      username,
      password,
    });
    const { access_token, refresh_token } = response.data;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);

    await fetchUser();
    router.push('/accounts');
  };

  const logout = () => {
    localStorage.clear();
    setUser(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

### 3. Create Login Page

```typescript
// frontend/app/(auth)/login/page.tsx
'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import Link from 'next/link';

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
        <div>
          <h2 className="text-3xl font-bold text-center">TikTok Manager</h2>
          <p className="mt-2 text-center text-gray-600">Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-md text-sm">
              {error}
            </div>
          )}

          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1"
            />
          </div>

          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mt-1"
            />
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in'}
          </Button>

          <p className="text-center text-sm text-gray-600">
            Don't have an account?{' '}
            <Link href="/register" className="text-blue-600 hover:underline">
              Register
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
```

### 4. Create Accounts Page

```typescript
// frontend/app/(dashboard)/accounts/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { AccountCard } from '@/components/accounts/account-card';
import { Plus } from 'lucide-react';

export default function AccountsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['tiktok-accounts'],
    queryFn: async () => {
      const response = await apiClient.get('/tiktok/accounts');
      return response.data;
    },
  });

  const handleConnectAccount = async () => {
    const response = await apiClient.get('/tiktok/auth/url');
    window.location.href = response.data.auth_url;
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">TikTok Accounts</h1>
        <Button onClick={handleConnectAccount}>
          <Plus className="mr-2 h-4 w-4" />
          Connect Account
        </Button>
      </div>

      {data?.accounts?.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">No TikTok accounts connected</p>
          <Button onClick={handleConnectAccount}>Connect Your First Account</Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data?.accounts?.map((account: any) => (
            <AccountCard key={account.id} account={account} />
          ))}
        </div>
      )}
    </div>
  );
}
```

### 5. Create Post Scheduling Page

```typescript
// frontend/app/(dashboard)/schedule/page.tsx
'use client';

import { useState } from 'react';
import { Calendar } from '@/components/ui/calendar';
import { PostForm } from '@/components/posts/post-form';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { format } from 'date-fns';

export default function SchedulePage() {
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [showForm, setShowForm] = useState(false);

  const { data: posts } = useQuery({
    queryKey: ['scheduled-posts', format(selectedDate, 'yyyy-MM-dd')],
    queryFn: async () => {
      const response = await apiClient.get('/posts/', {
        params: {
          date: format(selectedDate, 'yyyy-MM-dd'),
        },
      });
      return response.data;
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Schedule Posts</h1>
        <Button onClick={() => setShowForm(true)}>Schedule New Post</Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <Calendar
            mode="single"
            selected={selectedDate}
            onSelect={(date) => date && setSelectedDate(date)}
            className="rounded-md border"
          />
        </div>

        <div className="lg:col-span-2">
          <h2 className="text-xl font-semibold mb-4">
            Posts for {format(selectedDate, 'MMMM d, yyyy')}
          </h2>

          {posts?.posts?.length === 0 ? (
            <p className="text-gray-500">No posts scheduled for this date</p>
          ) : (
            <div className="space-y-4">
              {posts?.posts?.map((post: any) => (
                <PostCard key={post.id} post={post} />
              ))}
            </div>
          )}
        </div>
      </div>

      {showForm && (
        <PostForm
          selectedDate={selectedDate}
          onClose={() => setShowForm(false)}
        />
      )}
    </div>
  );
}
```

## Todo List

- [x] Install Next.js dependencies
- [x] Setup Shadcn/ui components
- [x] Create API client with interceptors
- [x] Implement Auth context
- [x] Create login page
- [x] Create registration page
- [x] Build dashboard layout
- [x] Create accounts page
- [x] Implement OAuth callback handling
- [x] Create post scheduling page
- [x] Build calendar component
- [x] Create post form
- [x] Implement media upload
- [x] Create analytics dashboard
- [x] Add real-time updates (polling)
- [x] Implement responsive design
- [x] Add loading states
- [x] Implement error handling
- [x] Add form validation
- [x] Write component tests

## Security Remediation Required

**CRITICAL Issues (Must Fix Before Production):**
- [ ] Migrate JWT tokens from localStorage to httpOnly cookies
- [ ] Remove access_token/refresh_token from TikTokAccount type
- [ ] Implement CSRF protection for state-changing requests
- [ ] Add OAuth state parameter validation
- [ ] Implement file upload validation (size, type, content)

**HIGH Priority:**
- [ ] Replace `err: any` with proper AxiosError typing (4 instances)
- [ ] Add input sanitization with DOMPurify for user-generated content
- [ ] Add error boundaries to prevent app crashes
- [ ] Fix analytics page state update during render

**Accessibility Fixes:**
- [ ] Add ARIA labels to icon-only buttons (Sync, Delete, Logout)
- [ ] Implement proper loading state announcements (aria-live)
- [ ] Add skip navigation links for keyboard users

See detailed findings in: `reports/code-reviewer-251206-phase06-frontend.md`

## Success Criteria

- ✅ All pages load < 2 seconds
- ✅ Responsive on mobile/tablet/desktop
- ✅ Forms validate properly
- ✅ Real-time updates work
- ✅ OAuth flow completes successfully
- ✅ Media uploads successfully
- ✅ Calendar shows scheduled posts
- ✅ Accessible (WCAG 2.1 AA)

## Risk Assessment

**Risk:** Large media upload failures
**Mitigation:** Implement chunked uploads, progress indicators, resume capability

**Risk:** OAuth popup blockers
**Mitigation:** Use redirect flow instead of popup, clear user messaging

## Security Considerations

- Store tokens in httpOnly cookies (if possible) or localStorage with caution
- Validate all user inputs
- Sanitize displayed data to prevent XSS
- Implement CSRF protection
- Use Content Security Policy headers

## Code Review Summary (2025-12-06)

**Build Status:** ✅ Success (no TypeScript errors)
**Tests:** ✅ 7/7 passing
**Bundle Size:** ✅ All pages < 200KB (largest: 159KB /schedule)
**Deployment Status:** ⚠️ **HOLD - Fix critical security issues first**

**Critical Findings:**
- JWT tokens stored in localStorage (XSS vulnerability)
- Sensitive tokens exposed in TikTokAccount type
- Missing CSRF protection
- OAuth state validation not implemented

**Quality Score:** B+ (85/100)

Full report: `reports/code-reviewer-251206-phase06-frontend.md`

## Next Steps

**Before proceeding to Phase 07:**
1. ❌ Address 2 CRITICAL security issues (token storage, sensitive data exposure)
2. ❌ Fix 5 HIGH priority issues (CSRF, OAuth validation, error typing)
3. ⚠️ Complete accessibility improvements (ARIA labels, skip links)
4. ✅ Then proceed to Phase 07: Testing & QA with focus on:
   - Security testing (OWASP Top 10 verification)
   - Accessibility testing (WCAG 2.1 AA with screen readers)
   - Performance testing (Lighthouse audit)
   - E2E testing (Playwright integration tests)
