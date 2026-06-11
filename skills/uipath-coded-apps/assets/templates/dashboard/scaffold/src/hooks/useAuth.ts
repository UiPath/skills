import React, { useState, useEffect, useRef, createContext, useContext, useCallback } from 'react'
import type { ReactNode } from 'react'
import { UiPath } from '@uipath/uipath-typescript/core'
import type { UiPathSDKConfig } from '@uipath/uipath-typescript/core'

interface AuthContextType {
  isAuthenticated: boolean
  isLoading: boolean
  sdk: UiPath
  getToken: () => Promise<string>
  login: () => Promise<void>
  error: string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Parent scopes only — must match DASHBOARD_SCOPES in build-dashboard.mjs and the
// scopes registered on the external OAuth app (.Read sub-scopes are not reliably registered).
const DEFAULT_SCOPES = 'OR.Assets OR.Jobs OR.Folders OR.Buckets OR.Execution OR.Tasks OR.Queues OR.Users Insights Insights.RealTimeData'
const SCOPES = (import.meta.env.VITE_UIPATH_SCOPE as string) || DEFAULT_SCOPES

function resolveConfig(): UiPathSDKConfig {
  return {
    baseUrl:     import.meta.env.VITE_UIPATH_BASE_URL as string,
    orgName:     import.meta.env.VITE_UIPATH_ORG_NAME as string,
    tenantName:  import.meta.env.VITE_UIPATH_TENANT_NAME as string,
    clientId:    import.meta.env.VITE_UIPATH_CLIENT_ID as string,
    scope:       SCOPES,
    redirectUri: `${window.location.origin}${window.location.pathname}`.replace(/\/+$/, ''),
  }
}

function isPlatformHosted(): boolean {
  return document.querySelector('meta[name="uipath:platform-hosted"]')?.getAttribute('content') === 'true'
}

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [{ sdk }] = useState(() => {
    const config = resolveConfig()
    return { sdk: new UiPath(config) }
  })
  const didInit = useRef(false)

  useEffect(() => {
    if (didInit.current) return
    didInit.current = true

    const init = async () => {
      setIsLoading(true)
      setError(null)
      try {
        if (isPlatformHosted()) {
          // Platform-hosted: wait for token injected by host
          await new Promise<void>((resolve, reject) => {
            let poll: ReturnType<typeof setInterval>
            const timer = setTimeout(() => {
              clearInterval(poll)
              reject(new Error('UIP.init timeout — host did not send token'))
            }, 9000)
            poll = setInterval(() => {
              if (sdk.isAuthenticated()) {
                clearTimeout(timer)
                clearInterval(poll)
                resolve()
              }
            }, 100)
          })
          setIsAuthenticated(true)
        } else {
          // Local preview: OAuth PKCE
          if (sdk.isInOAuthCallback()) {
            await sdk.completeOAuth()
            window.history.replaceState({}, document.title, window.location.pathname)
          }
          setIsAuthenticated(sdk.isAuthenticated())
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Authentication failed')
      } finally {
        setIsLoading(false)
      }
    }

    void init()
    return () => {
      didInit.current = false
      sdk.logout()
    }
  }, [sdk])

  const getToken = useCallback(async (): Promise<string> => {
    const token = sdk.getToken()
    if (token) return token
    throw new Error('Access token not available — please sign in')
  }, [sdk])

  const login = useCallback(async () => {
    await sdk.initialize()
  }, [sdk])

  const value: AuthContextType = {
    isAuthenticated,
    isLoading,
    sdk,
    getToken,
    login,
    error,
  }

  return React.createElement(AuthContext.Provider, { value }, children)
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
