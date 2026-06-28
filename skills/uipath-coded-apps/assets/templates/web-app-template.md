# Web App File Templates

Ready-to-use boilerplate for a new UiPath Coded Web App (Vite + React + TypeScript + Tailwind) using the `@uipath/uipath-typescript` SDK. Replace `{{PLACEHOLDER}}` values with the answers gathered in the workflow at [../../references/create-web-app.md](../../references/create-web-app.md).

**Both Q6 paths share the same Tailwind toolchain and SDK initialization pattern.** The SDK is instantiated with `new UiPath()` (no config) — `clientId`, `scope`, `orgName`, `tenantName`, `baseUrl`, and `redirectUri` are read at runtime from `<meta name="uipath:*">` tags. The `@uipath/coded-apps-dev` Vite plugin injects those tags locally from `uipath.json` (committed) and `.uipath/` (populated by `uip login`); the UiPath platform injects them in production.

The only difference between the paths is the component layer: Q6 = yes adds `@uipath/apollo-wind` components, Apollo design tokens, and a light/dark theme toggle; Q6 = no leaves you with bare Tailwind so you can bring your own component library.

---

## `vite.config.ts`

`base: './'` is **always required** — the platform handles URL routing; the app must use relative asset paths. The `uipathCodedApps()` plugin reads `uipath.json` (and the local `.uipath/` config populated by `uip login`) and injects `<meta name="uipath:*">` tags during local dev, so `new UiPath()` (no config) sees the same values in dev that the platform injects in production. The `path-browserify` alias and `global: 'globalThis'` define are kept as belt-and-suspenders polyfills — the current SDK does not require them on the browser bundle path, but a future version could.

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { uipathCodedApps } from '@uipath/coded-apps-dev/vite'

export default defineConfig({
  base: './',
  plugins: [
    react(),
    uipathCodedApps(),
  ],
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

Project-root config consumed by the `uip codedapp` CLI for deployment and by the `uipathCodedApps()` Vite plugin for local-dev meta-tag injection. This is the single source of truth for OAuth scopes and the client ID — no `.env` file is used.

```json
{
  "scope": "{{SCOPES}}",
  "clientId": "{{CLIENT_ID}}"
}
```

`orgName`, `tenantName`, and `baseUrl` are not stored here — they live in `.uipath/` (gitignored, populated by `uip login --org <org> --tenant <tenant>`) for local dev, and are injected by the platform at production runtime.

---

## `src/hooks/useAuth.tsx`

`AuthProvider` + `useAuth` hook. Handles PKCE callback detection on return from login, exposes `login()` / `logout()` for the UI, and tracks auth state. The SDK is instantiated with `new UiPath()` (no config) — it reads `clientId`, `scope`, `orgName`, `tenantName`, `baseUrl`, and `redirectUri` at runtime from the `<meta name="uipath:*">` tags injected by `@uipath/coded-apps-dev` (in dev) or by the platform (in production). No substitutions in this file.

Create the `src/hooks/` directory if it does not exist before writing.

```tsx
import React, { useState, useEffect, useRef, createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { UiPath, UiPathError } from '@uipath/uipath-typescript/core';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  sdk: UiPath;
  login: () => Promise<void>;
  logout: () => void;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // `new UiPath()` reads clientId/orgName/tenantName/baseUrl/scope/redirectUri
  // from <meta name="uipath:*"> tags. The uipathCodedApps() Vite plugin
  // injects them locally from uipath.json; the platform injects them in prod.
  const [sdk] = useState<UiPath>(() => new UiPath());
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

Wraps app content in `<AuthProvider>` and renders a sign-in screen until the user is authenticated. Bare HTML + Tailwind utility classes — bring your own component library to replace the buttons/cards as needed. Overwrite the file Vite generated. No substitutions.

```tsx
import { AuthProvider, useAuth } from './hooks/useAuth';

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
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
```

---

## `postcss.config.js`

```js
export default {
  plugins: {
    '@tailwindcss/postcss': {},
    autoprefixer: {},
  },
}
```

---

## `src/index.css`

A single `@import` pulls in Tailwind's base, components, and utilities. Customize theme tokens (colors, fonts, spacing) inline via `@theme { … }` per the Tailwind docs. Overwrite the file Vite generated.

```css
@import "tailwindcss";
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

---

# Default-styling templates (Apollo Vertex / apollo-wind)

The sections below are used **only** when the user answered **`yes`** to Q6 (default UI styling) in [../../references/create-web-app.md](../../references/create-web-app.md#step-2--ask-the-user-for-setup-info). Together they pull in the UiPath Apollo Vertex design system — `@uipath/apollo-wind` components, semantic Apollo design tokens, and a light/dark theme toggle via `next-themes`.

The substitution table in [Step 4.5](../../references/create-web-app.md#45--write-project-files-from-templates) lists which sections to use; do not mix-and-match with the non-styled sections above.

---

## `vite.config.ts (default styling)`

`base: './'` is **always required** — the platform handles URL routing; the app must use relative asset paths. The `uipathCodedApps()` plugin reads `uipath.json` and injects `<meta name="uipath:*">` tags during local dev, so `new UiPath()` (no config) sees the same values in dev that the platform injects in production.

No `define: { global }` and no `path-browserify` alias — the SDK no longer needs those polyfills. If a future SDK version reintroduces a Node-ism in the browser bundle, add them back here.

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { uipathCodedApps } from '@uipath/coded-apps-dev/vite'

export default defineConfig({
  base: './',
  plugins: [
    react(),
    uipathCodedApps(),
  ],
  optimizeDeps: {
    include: ['@uipath/uipath-typescript'],
  },
})
```

Do not add `server.proxy` — it interferes with the OAuth callback and asset resolution.

---

## `postcss.config.js (default styling)`

Apollo-wind ships its own PostCSS config — re-export it directly so the app stays in lockstep with the design system.

```js
import apolloWindPostcss from '@uipath/apollo-wind/postcss'

export default apolloWindPostcss
```

> **Why no `tailwind.config.js`?** All Tailwind configuration (theme tokens, `@source` paths, dark-mode trigger) lives directly in `src/index.css`. Same on both Q6 paths.

---

## `src/index.css (default styling)`

Imports apollo-wind's Tailwind source (base + utilities + Apollo tokens + `.dark` overrides), then tells Tailwind where to scan for utility classes. Apollo-wind components live under `node_modules/@uipath/apollo-wind/dist` and Tailwind skips `node_modules` by default — the `@source` directive opts that path back in so the components' utility classes (e.g. the Dialog's `p-6 gap-4`) actually get generated.

Overwrite the file Vite generated.

```css
/* Tailwind base + utilities, Apollo design tokens, light/dark overrides. */
@import '@uipath/apollo-wind/tailwind.css';

/* Tailwind skips node_modules — opt apollo-wind back in so its components'
   utility classes are emitted. The second line scans this app's own files. */
@source '../node_modules/@uipath/apollo-wind/dist';
@source './';
```

---

## `src/components/Theme.tsx (default styling)`

Wraps the app in `next-themes` and exposes a tiny Sun/Moon `<ThemeToggle>` button. `attribute="class"` toggles the `.dark` class on `<html>` so apollo-wind's built-in dark tokens take over. Place this file at `src/components/Theme.tsx`; create the directory if it does not exist.

```tsx
import { Moon, Sun } from 'lucide-react'
import { ThemeProvider, useTheme } from 'next-themes'
import type { ReactNode } from 'react'
import { Button } from '@uipath/apollo-wind/components/ui/button'

/** Wraps the app in next-themes with a `.dark` class on <html>. */
export function AppThemeProvider({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      {children}
    </ThemeProvider>
  )
}

/** Sun/Moon button — cycles light ↔ dark. */
export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme()
  const next = resolvedTheme === 'dark' ? 'light' : 'dark'
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(next)}
      aria-label={`Switch to ${next} mode`}
      title={`Switch to ${next} mode`}
    >
      <Sun className="h-4 w-4 dark:hidden" />
      <Moon className="hidden h-4 w-4 dark:block" />
    </Button>
  )
}
```

---

## `src/main.tsx (default styling)`

Wrap `<App>` in `<AppThemeProvider>` so the theme is available before any apollo-wind component mounts. Overwrite Vite's default `main.tsx`.

```tsx
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { AppThemeProvider } from './components/Theme'

createRoot(document.getElementById('root')!).render(
  <AppThemeProvider>
    <App />
  </AppThemeProvider>,
)
```

> The yes path intentionally does not import `StrictMode`. The OAuth `code` is single-use; the `didInit` guard in `useAuth` already prevents the double-invoke, so adding `StrictMode` provides no extra safety here. If you need StrictMode for other reasons, leave the guard in place.

---

## `src/App.tsx (default styling)`

Renders an apollo-wind sign-in card while unauthenticated, then a minimal authenticated shell with a `<ThemeToggle>` + `Sign out` in the header. Overwrite the file Vite generated. No substitutions.

```tsx
import { LayoutDashboard, LogOut, ShieldCheck } from 'lucide-react'
import { Alert, AlertDescription } from '@uipath/apollo-wind/components/ui/alert'
import { Button } from '@uipath/apollo-wind/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@uipath/apollo-wind/components/ui/card'
import { Spinner } from '@uipath/apollo-wind/components/ui/spinner'
import { Toaster } from '@uipath/apollo-wind/components/ui/sonner'
import { AuthProvider, useAuth } from './hooks/useAuth'
import { ThemeToggle } from './components/Theme'

function AppContent() {
  const { isAuthenticated, isLoading, login, logout, error } = useAuth()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner label="Initializing UiPath SDK…" showLabel />
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-4">
        <Card className="w-full max-w-sm">
          <CardHeader className="items-center text-center">
            <div className="mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <CardTitle>Welcome</CardTitle>
            <CardDescription>
              Sign in with your UiPath account to continue.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <Button onClick={login} className="w-full">
              Sign in with UiPath
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background text-foreground">
      <header className="flex items-center justify-between gap-4 border-b px-4 py-3 sm:px-6">
        <div className="flex min-w-0 items-center gap-2">
          <LayoutDashboard className="h-5 w-5 shrink-0 text-primary" />
          <h1 className="truncate text-base font-semibold">My App</h1>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button variant="ghost" size="sm" onClick={logout}>
            <LogOut className="h-4 w-4" />
            <span className="hidden sm:inline">Sign out</span>
          </Button>
        </div>
      </header>
      <main className="min-h-0 flex-1 p-6">Your app content here</main>
      <Toaster />
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}
```

### Common apollo-wind imports

Reach for these primitives instead of styling raw HTML. Each import is a single subpath under `@uipath/apollo-wind/components/ui/<name>`:

| Need | Component | Import path |
|------|-----------|-------------|
| Action buttons | `Button` | `@uipath/apollo-wind/components/ui/button` |
| Containers | `Card`, `CardHeader`, `CardContent`, `CardTitle`, `CardDescription`, `CardFooter` | `@uipath/apollo-wind/components/ui/card` |
| Modals | `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogDescription`, `DialogFooter` | `@uipath/apollo-wind/components/ui/dialog` |
| Side panels | `Sheet`, `SheetContent`, `SheetHeader`, `SheetTitle` | `@uipath/apollo-wind/components/ui/sheet` |
| Inline status | `Alert`, `AlertDescription`, `AlertTitle` | `@uipath/apollo-wind/components/ui/alert` |
| Toasts | `Toaster` + `toast()` | `@uipath/apollo-wind/components/ui/sonner` |
| Tags / chips | `Badge` | `@uipath/apollo-wind/components/ui/badge` |
| Loading | `Spinner`, `Skeleton` | `@uipath/apollo-wind/components/ui/spinner`, `…/skeleton` |
| Tabs | `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` | `@uipath/apollo-wind/components/ui/tabs` |
| Forms | `Input`, `Textarea`, `Checkbox`, `Select`, `Label` | `@uipath/apollo-wind/components/ui/<name>` |
| Empty states | `EmptyState` | `@uipath/apollo-wind/components/ui/empty-state` |
| Pickers | `Popover` + `Command` primitives | `@uipath/apollo-wind/components/ui/popover`, `…/command` |

> **Combobox caveat.** Apollo-wind ships a `Combobox` wrapper, but its `CommandItem` is keyed by `value={item.value}` (the id). cmdk filters by `value`, so typing a label finds nothing. When you need name-based search, compose `Popover` + `Command` directly and set `value={item.label}` on each `CommandItem`.

### Semantic Apollo design tokens

Use the semantic CSS variables, not raw colors — they automatically flip in `.dark` mode. Common ones (Tailwind reads them via `bg-background`, `text-foreground`, etc.):

- `--color-background` / `--color-foreground` — page surface + text
- `--color-card` / `--color-card-foreground` — cards/panels
- `--color-primary` / `--color-primary-foreground` — primary actions
- `--color-muted` / `--color-muted-foreground` — secondary text/surfaces
- `--color-border` — dividers (use `var(--color-border)` directly when the token is needed inside non-Tailwind CSS, e.g. AG Grid theming)
- `--color-destructive` / `--color-destructive-foreground` — errors

Avoid `hsl(var(--border))`-style references — apollo-core defines `--border` as a CSS shorthand (`1px solid #...`), not a bare color, so wrapping it in `hsl()` produces invalid CSS. Use `var(--color-border)` instead.

---

## Note on `.env` (default styling)

The yes path does not use a `.env` file. Configuration lives in `uipath.json` (committed) and is read at runtime from the `<meta name="uipath:*">` tags injected by `uipathCodedApps()` in dev and the platform in production. There is therefore no `.env` row in Step 4.5 for the yes path and no `.env` line to append to `.gitignore` in Step 4.6.

If you later need to add app-specific environment variables (feature flags, etc.), create a `.env` file separately and add it to `.gitignore` at that point.
