#!/usr/bin/env bash
# setup.sh — Scaffolds a new UiPath coded web app (React + Vite + TypeScript)
# Usage: bash scripts/setup.sh <app-name> <org-name> <tenant-name> <client-id> "<scopes>" [environment]
#
# Arguments:
#   app-name     Name of the app (used for directory and npm init)
#   org-name     UiPath organization name
#   tenant-name  UiPath tenant name
#   client-id    OAuth client ID
#   scopes       OAuth scopes (space-separated, e.g. "OR.Assets PIMS")
#   environment  cloud (default), alpha, staging, or a custom base URL
#
# Example:
#   bash scripts/setup.sh my-app myOrg myTenant abc-123 "OR.Assets PIMS" cloud

set -euo pipefail

APP_NAME="${1:?Usage: setup.sh <app-name> <org-name> <tenant-name> <client-id> <scopes> [environment]}"
ORG_NAME="${2:?ERROR: Organization name is required.}"
TENANT_NAME="${3:?ERROR: Tenant name is required.}"
CLIENT_ID="${4:?ERROR: Client ID is required.}"
SCOPES="${5:?ERROR: Scopes are required. Provide as a space-separated string (e.g. \"OR.Assets PIMS\").}"
ENV_INPUT="${6:-cloud}"

# Resolve environment to base URL
case "$ENV_INPUT" in
  cloud)              BASE_URL="https://api.uipath.com" ;;
  alpha)              BASE_URL="https://alpha.api.uipath.com" ;;
  staging)            BASE_URL="https://staging.api.uipath.com" ;;
  http://*|https://*) BASE_URL="$ENV_INPUT" ;;
  *)                  BASE_URL="https://${ENV_INPUT}.api.uipath.com" ;;
esac

echo ""
echo "Configuration:"
echo "  App name:     $APP_NAME"
echo "  Org name:     $ORG_NAME"
echo "  Tenant name:  $TENANT_NAME"
echo "  Client ID:    $CLIENT_ID"
echo "  Environment:  $BASE_URL"
echo "  Scopes:       $SCOPES"
echo ""

# --- Project scaffolding ---
echo "==> Creating Vite project: $APP_NAME"
npx --yes create-vite@latest "$APP_NAME" --template react-ts
cd "$APP_NAME"

echo "==> Installing dependencies"
npm install @uipath/uipath-typescript --@uipath:registry=https://registry.npmjs.org
npm install path-browserify tailwindcss@3 postcss autoprefixer

echo "==> Writing vite.config.ts"
cat > vite.config.ts << 'VITEEOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: './',
  define: {
    global: 'globalThis',
  },
  resolve: {
    alias: {
      path: 'path-browserify',
    },
  },
  optimizeDeps: {
    include: ['@uipath/uipath-typescript'],
  },
})
VITEEOF

echo "==> Writing uipath.json"
cat > uipath.json << EOF
{
  "scope": "${SCOPES}",
  "clientId": "${CLIENT_ID}"
}
EOF

echo "==> Writing .env"
cat > .env << EOF
UIPATH_BASE_URL=${BASE_URL}
UIPATH_CLIENT_ID=${CLIENT_ID}
UIPATH_ORG_NAME=${ORG_NAME}
UIPATH_TENANT_NAME=${TENANT_NAME}
UIPATH_SCOPE=${SCOPES}

VITE_UIPATH_BASE_URL=\${UIPATH_BASE_URL}
VITE_UIPATH_CLIENT_ID=${CLIENT_ID}
VITE_UIPATH_ORG_NAME=${ORG_NAME}
VITE_UIPATH_TENANT_NAME=${TENANT_NAME}
VITE_UIPATH_SCOPE=${SCOPES}
EOF

echo "==> Writing .env.example"
cat > .env.example << 'ENVEOF'
UIPATH_BASE_URL=
UIPATH_CLIENT_ID=
UIPATH_ORG_NAME=
UIPATH_TENANT_NAME=
UIPATH_SCOPE=

VITE_UIPATH_BASE_URL=
VITE_UIPATH_CLIENT_ID=
VITE_UIPATH_ORG_NAME=
VITE_UIPATH_TENANT_NAME=
VITE_UIPATH_SCOPE=
ENVEOF

echo "==> Updating .gitignore"
echo ".env" >> .gitignore

echo "==> Writing src/hooks/useAuth.tsx"
mkdir -p src/hooks
cat > src/hooks/useAuth.tsx << 'AUTHEOF'
import React, { useState, useEffect, createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { UiPath, UiPathError } from '@uipath/uipath-typescript/core';
import type { UiPathSDKConfig } from '@uipath/uipath-typescript/core';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  sdk: UiPath;
  login: () => Promise<void>;
  logout: () => void;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode; config: UiPathSDKConfig }> = ({ children, config }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sdk] = useState<UiPath>(() => new UiPath(config));

  useEffect(() => {
    const initializeAuth = async () => {
      setIsLoading(true);
      setError(null);
      try {
        if (sdk.isInOAuthCallback()) {
          await sdk.completeOAuth();
        }
        if (!sdk.isAuthenticated()) {
          await sdk.initialize();
          return;
        }
        setIsAuthenticated(true);
      } catch (err) {
        console.error('Authentication failed:', err);
        setError(err instanceof UiPathError ? err.message : 'Authentication failed');
      } finally {
        setIsLoading(false);
      }
    };
    initializeAuth();
  }, [sdk]);

  const login = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await sdk.initialize();
    } catch (err) {
      setError(err instanceof UiPathError ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    sdk.logout();
    setIsAuthenticated(false);
    setError(null);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, sdk, login, logout, error }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
AUTHEOF

echo "==> Writing src/App.tsx"
cat > src/App.tsx << 'APPEOF'
import { AuthProvider, useAuth } from './hooks/useAuth';
import type { UiPathSDKConfig } from '@uipath/uipath-typescript/core';

const authConfig: UiPathSDKConfig = {
  clientId: import.meta.env.VITE_UIPATH_CLIENT_ID,
  orgName: import.meta.env.VITE_UIPATH_ORG_NAME,
  tenantName: import.meta.env.VITE_UIPATH_TENANT_NAME,
  baseUrl: import.meta.env.VITE_UIPATH_BASE_URL,
  redirectUri: window.location.origin + window.location.pathname,
  scope: import.meta.env.VITE_UIPATH_SCOPE,
};

function AppContent() {
  const { isAuthenticated, isLoading, error } = useAuth();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!isAuthenticated) return <div>Redirecting to login...</div>;

  return <div>Your app content here</div>;
}

function App() {
  return (
    <AuthProvider config={authConfig}>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
APPEOF

echo "==> Writing tailwind.config.js"
cat > tailwind.config.js << 'TWEOF'
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: {} },
  plugins: [],
}
TWEOF

echo "==> Writing postcss.config.js"
cat > postcss.config.js << 'PCEOF'
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
PCEOF

echo "==> Writing src/index.css with Tailwind directives"
cat > src/index.css << 'CSSEOF'
@tailwind base;
@tailwind components;
@tailwind utilities;
CSSEOF

echo ""
echo "==> Setup complete! Project created at ./$APP_NAME"
echo "    cd $APP_NAME && npm run dev"
