import React, { useState, useEffect, useRef, createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { UiPath } from '@uipath/uipath-typescript/core';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  sdk: UiPath;
  login: () => Promise<void>;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // `new UiPath()` reads clientId/orgName/tenantName/baseUrl/scope/redirectUri
  // from <meta name="uipath:*"> tags injected from uipath.json (local) or by
  // the platform (deployed).
  const [sdk] = useState<UiPath>(() => new UiPath());
  const didInit = useRef(false);

  useEffect(() => {
    if (didInit.current) return;
    didInit.current = true;
    (async () => {
      setIsLoading(true);
      try {
        if (sdk.isInOAuthCallback()) {
          await sdk.completeOAuth();
          setIsAuthenticated(true);
        } else if (sdk.isAuthenticated()) {
          setIsAuthenticated(true);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setIsLoading(false);
      }
    })();
  }, [sdk]);

  const login = async () => {
    setError(null);
    await sdk.initialize();
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, sdk, login, error }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
