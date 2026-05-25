import React, { useState, useEffect, useRef, createContext, useContext, useCallback } from 'react'
import type { ReactNode } from 'react'
import { UiPath, UiPathError } from '@uipath/uipath-typescript/core'
import type { UiPathSDKConfig } from '@uipath/uipath-typescript/core'

interface AuthContextType {
  isAuthenticated: boolean
  isLoading: boolean
  sdk: UiPath
  tenantId: string
  getToken: () => Promise<string>
  error: string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

function resolveConfig(): UiPathSDKConfig {
  const base = {
    baseUrl: import.meta.env.VITE_UIPATH_BASE_URL as string,
    orgName: import.meta.env.VITE_UIPATH_ORG_NAME as string,
    tenantName: import.meta.env.VITE_UIPATH_TENANT_NAME as string,
  }
  const pat = import.meta.env.VITE_UIPATH_PAT as string | undefined
  if (pat && pat.length > 0) {
    // Dev mode: use session PAT from ~/.uipath/.auth
    return { ...base, secret: pat }
  }
  // Production (FP surface): ActionCenterTokenManager handles auth via postMessage.
  // The SDK union type requires secret or OAuth fields, but the FP host injects the
  // token manager at runtime. Cast through unknown to satisfy the discriminated union.
  return base as unknown as UiPathSDKConfig
}

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sdk] = useState<UiPath>(() => new UiPath(resolveConfig()))
  const didInit = useRef(false)

  useEffect(() => {
    if (didInit.current) return
    didInit.current = true

    const init = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const pat = import.meta.env.VITE_UIPATH_PAT as string | undefined
        if (pat && pat.length > 0) {
          // Dev mode: PAT from uip login session — skip OAuth, go straight to dashboard
          setIsAuthenticated(true)
        } else {
          // Production (FP surface): SDK initialises via ActionCenterTokenManager
          await sdk.initialize()
          setIsAuthenticated(sdk.isAuthenticated())
        }
      } catch (err) {
        setError(err instanceof UiPathError ? err.message : 'Authentication failed')
      } finally {
        setIsLoading(false)
      }
    }
    void init()
  }, [sdk])

  const getToken = useCallback(async (): Promise<string> => {
    // In dev mode, PAT is available directly from env
    const pat = import.meta.env.VITE_UIPATH_PAT as string | undefined
    if (pat && pat.length > 0) return pat
    // In production, get token from SDK's internal token manager
    // The SDK refreshes it automatically via ActionCenterTokenManager
    throw new Error('Token not available — ensure VITE_UIPATH_PAT is set for local dev')
  }, [])

  const value: AuthContextType = {
    isAuthenticated,
    isLoading,
    sdk,
    tenantId: import.meta.env.VITE_INSIGHTS_TENANT_ID as string,
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
