import React, { useState, useEffect, useRef, createContext, useContext, useCallback } from 'react'
import type { ReactNode } from 'react'
import { UiPath, UiPathError } from '@uipath/uipath-typescript/core'
import type { UiPathSDKConfig } from '@uipath/uipath-typescript/core'

interface AuthContextType {
  isAuthenticated: boolean
  isLoading: boolean
  sdk: UiPath
  tenantId: string
  login: () => Promise<void>
  logout: () => void
  getToken: () => Promise<string>
  error: string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Module-level token cache for Insights API calls.
// Safe: single-page app, single session, in-memory only.
let _cachedToken: string | null = null

export const AuthProvider: React.FC<{ children: ReactNode; config: UiPathSDKConfig }> = ({
  children,
  config,
}) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sdk] = useState<UiPath>(() => new UiPath(config))
  const didInit = useRef(false)

  useEffect(() => {
    // Guard against React Strict Mode double-invoke — OAuth codes are single-use.
    if (didInit.current) return
    didInit.current = true

    const init = async () => {
      setIsLoading(true)
      setError(null)
      try {
        if (sdk.isInOAuthCallback()) {
          await sdk.completeOAuth()
          window.history.replaceState({}, document.title, window.location.pathname)
        }
        setIsAuthenticated(sdk.isAuthenticated())
      } catch (err) {
        setError(err instanceof UiPathError ? err.message : 'Authentication failed')
      } finally {
        setIsLoading(false)
      }
    }

    void init()
  }, [sdk])

  const login = useCallback(async () => {
    await sdk.login()
  }, [sdk])

  const logout = useCallback(() => {
    _cachedToken = null
    sdk.logout()
    setIsAuthenticated(false)
  }, [sdk])

  // getToken: used by InsightsClient for raw bearer token access.
  // The SDK stores its OAuth token in sessionStorage after completeOAuth().
  // Find the key containing 'access_token' and return its value.
  const getToken = useCallback(async (): Promise<string> => {
    if (_cachedToken) return _cachedToken
    const keys = Object.keys(sessionStorage)
    const tokenKey = keys.find(
      (k) => k.includes('access_token') || k.includes('accessToken')
    )
    if (tokenKey) {
      const raw = sessionStorage.getItem(tokenKey)
      if (raw) {
        try {
          const parsed = JSON.parse(raw) as { value?: string; access_token?: string }
          _cachedToken = parsed.value ?? parsed.access_token ?? raw
        } catch {
          _cachedToken = raw
        }
        if (_cachedToken) return _cachedToken
      }
    }
    throw new Error('Access token not available — ensure user is authenticated')
  }, [])

  const value: AuthContextType = {
    isAuthenticated,
    isLoading,
    sdk,
    tenantId: import.meta.env.VITE_INSIGHTS_TENANT_ID as string,
    login,
    logout,
    getToken,
    error,
  }

  return React.createElement(AuthContext.Provider, { value }, children)
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
