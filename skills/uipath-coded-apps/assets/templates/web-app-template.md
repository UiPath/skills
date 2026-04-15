# Web App File Templates

Ready-to-use boilerplate for a new UiPath Coded Web App (Vite + React + TypeScript + Tailwind) using the `@uipath/uipath-typescript` SDK. Replace `{{PLACEHOLDER}}` values with the answers gathered in the workflow at [../../references/create-web-app.md](../../references/create-web-app.md).

---

## `vite.config.ts`

`base: './'` is **always required** — the platform handles URL routing; the app must use relative asset paths. The `path-browserify` alias and `global: 'globalThis'` define are needed by the SDK in the browser.

```typescript
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
```

Do not add `server.proxy` — it interferes with the OAuth callback and asset resolution.

---

## `uipath.json`

Project-root config consumed by the `uip codedapp` CLI for deployment and by the Vite plugin for local dev meta-tag injection. Keep in sync with `.env` if scopes or client ID change.

```json
{
  "scope": "{{SCOPES}}",
  "clientId": "{{CLIENT_ID}}"
}
```

---

## `.env`

OAuth env vars consumed by `src/App.tsx` via `import.meta.env`. **No redirect URI env var** — the SDK computes it at runtime as `window.location.origin + window.location.pathname`.

```
VITE_UIPATH_CLIENT_ID={{CLIENT_ID}}
VITE_UIPATH_SCOPE={{SCOPES}}
VITE_UIPATH_ORG_NAME={{ORG_NAME}}
VITE_UIPATH_TENANT_NAME={{TENANT_NAME}}
VITE_UIPATH_BASE_URL={{BASE_URL}}
```

`{{BASE_URL}}` values: `https://api.uipath.com` (cloud) · `https://staging.api.uipath.com` (staging) · `https://alpha.api.uipath.com` (alpha)

---

## `.env.example`

Committed to the repo as a placeholder for new clones. No substitutions.

```
VITE_UIPATH_CLIENT_ID=
VITE_UIPATH_SCOPE=
VITE_UIPATH_ORG_NAME=
VITE_UIPATH_TENANT_NAME=
VITE_UIPATH_BASE_URL=https://api.uipath.com
```

---

## `src/hooks/useAuth.tsx`

`AuthProvider` + `useAuth` hook. Handles PKCE callback detection on return from login, exposes `login()` / `logout()` for the UI, and tracks auth state. The OAuth config comes in via the `<AuthProvider>`'s `config` prop, which `App.tsx` supplies from `import.meta.env`. No substitutions in this file.

Create the `src/hooks/` directory if it does not exist before writing.

```tsx
import React, { useState, useEffect, useRef, createContext, useContext } from 'react';
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
  const didInit = useRef(false);

  useEffect(() => {
    // Guard against React Strict Mode's double-invocation in dev.
    // OAuth authorization codes are single-use — calling completeOAuth()
    // twice would fail the second time with "Authentication failed".
    if (didInit.current) return;
    didInit.current = true;

    const initializeAuth = async () => {
      setIsLoading(true);
      setError(null);
      try {
        if (sdk.isInOAuthCallback()) {
          await sdk.completeOAuth();
          // Strip OAuth params from the URL so a refresh doesn't try to
          // re-consume the (now-invalid) code.
          window.history.replaceState({}, document.title, window.location.pathname);
        }
        setIsAuthenticated(sdk.isAuthenticated());
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
```

**Key SDK methods** (used inside `useAuth.tsx` — do not call these directly in app code):

| Method | Purpose |
|--------|---------|
| `sdk.isInOAuthCallback()` | Returns true if URL has OAuth `code` param |
| `sdk.completeOAuth()` | Exchanges the code for tokens |
| `sdk.isInitialized()` | Returns true once SDK initialization has completed — use to gate `completeOAuth()` and service calls inside `useEffect` |
| `sdk.isAuthenticated()` | Returns true if a valid token exists |
| `sdk.initialize()` | Initiates PKCE OAuth flow (redirects to UiPath login) |
| `sdk.getToken()` | Returns the current access token |
| `sdk.updateToken(tokenInfo)` | Inject or refresh the access token externally — used for silent-refresh flows |
| `sdk.logout()` | Clears auth state (requires re-`initialize()` to authenticate again) |

---

## `src/App.tsx`

Wraps app content in `<AuthProvider>` and renders a sign-in screen until the user is authenticated. Overwrite the file Vite generated. No substitutions.

```tsx
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
  const { isAuthenticated, isLoading, error, login, logout } = useAuth();

  if (isLoading) return <div className="p-8">Loading...</div>;
  if (error) return <div className="p-8 text-red-600">Error: {error}</div>;

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-sm w-full bg-white rounded-lg shadow p-8 text-center">
          <h1 className="text-2xl font-semibold mb-2">Welcome</h1>
          <p className="text-gray-600 mb-6">
            Sign in with your UiPath account to continue.
          </p>
          <button
            onClick={login}
            className="w-full py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Sign in with UiPath
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <header className="flex justify-end items-center p-4 border-b">
        <button
          onClick={logout}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          Sign out
        </button>
      </header>
      <main className="p-8">Your app content here</main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider config={authConfig}>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
```

---

## `tailwind.config.js`

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: {} },
  plugins: [],
}
```

---

## `postcss.config.js`

```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

---

## `src/index.css`

Overwrite the file Vite generated.

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

---

## Optional: Router base path

Only add this if the app uses a client-side router. Set the basename/base to `getAppBase()` — it reads the `uipath:app-base` meta tag injected by the platform at runtime and falls back to `'/'` locally, so it is safe to use unconditionally.

**React Router (v5 / `BrowserRouter`):**
```tsx
import { getAppBase } from '@uipath/uipath-typescript';
import { BrowserRouter } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter basename={getAppBase()}>
      {/* your routes */}
    </BrowserRouter>
  );
}
```

**React Router v6 (`createBrowserRouter`):**
```tsx
import { getAppBase } from '@uipath/uipath-typescript';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';

const router = createBrowserRouter(routes, { basename: getAppBase() });

function App() {
  return <RouterProvider router={router} />;
}
```

**Vue Router:**
```typescript
import { getAppBase } from '@uipath/uipath-typescript';
import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(getAppBase()),
  routes,
});
```
