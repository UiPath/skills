# External Auth Widget

Provider-agnostic React **sign-in screen**: renders one "Continue with {Provider}" button per configured authentication provider and starts the login **directly at that provider's IdP**. Ships a built-in OIDC authorization-code redirect (CSRF `state` + PKCE) enabled per provider via an `oauth` config; a per-provider `onSignIn` handler always wins over it.

Package: [`@uipath/ui-widgets-external-auth`](https://www.npmjs.com/package/@uipath/ui-widgets-external-auth). Full prop/API surface lives in the package README — this file covers only the integration steps that are easy to get wrong inside a Coded App.

> **Publish status:** this package is newer than the other widgets. Before recommending it, verify it resolves: `npm view @uipath/ui-widgets-external-auth version`. On a 404 the package is not yet on the public registry — tell the user instead of inventing an install path.

## When to Use

- The coded app is a **user-facing portal whose end users sign in with external identity providers** (Google, UAE PASS, a corporate SAML IdP) — the widget is the front-door sign-in screen.
- **NOT for signing in to UiPath.** Coded web apps authenticate to UiPath Cloud via the built-in OAuth-PKCE flow (`useAuth()` / `sdk.initialize()` — see [../create-web-app.md](../create-web-app.md)); action apps use the host-injected session. Never replace those with this widget.

## Critical Rules

1. **This widget only STARTS the login.** Everything after the browser leaves the page — the callback route, `state`/PKCE verification, code→token exchange, session creation — is the app's (or its backend's) responsibility. Rendering the widget without building the callback side yields a sign-in that goes nowhere.
2. **Each provider needs `onSignIn` or `oauth`** (`onSignIn` wins when both are set). With neither, the button click logs a console warning and does nothing.
3. **The built-in default covers OIDC-style providers only.** It builds an authorization-code redirect with CSRF `state` and PKCE, then navigates to the provider. **SAML cannot be started from the browser** — SAML providers must use `onSignIn` pointing at a backend Service Provider route (e.g. `window.location.assign('/auth/saml/login?connection=' + clientId)`).
4. **The callback route must read the persisted `state`/`codeVerifier`.** The built-in redirect stores them in `sessionStorage` under `uipath-external-auth:oauth:<clientId>` — verify `state` matches and send `codeVerifier` in the token exchange.
5. **Never put a provider client secret in the app.** The flow is a public-client authorization-code + PKCE redirect; secret-bearing exchanges belong on a backend.
6. **No UiPath scopes needed.** The widget makes no UiPath API calls, so it adds nothing to the `scope` field in `uipath.json`. (It still peer-depends on `@uipath/uipath-typescript` for telemetry.)
7. **Import the stylesheet once**: `import '@uipath/ui-widgets-external-auth/ExternalAuth.css'`. Body needs `light` or `dark` class. Peers: `react >= 19.2.0`, `react-dom >= 19.2.0`, `@uipath/uipath-typescript >= 1.4.1`.
8. **Redirect URIs must be registered at the provider.** The `oauth.redirectUri` you pass must exactly match a redirect URI configured in the provider's console (per environment — local dev vs deployed app URL).

## Install

From inside the scaffolded app directory (after the publish check above):

```bash
npm install @uipath/ui-widgets-external-auth --@uipath:registry=https://registry.npmjs.org
```

Registry flag forces the public npm registry (skill default — users may have `@uipath` scoped to GitHub Packages).

## Key Props

| Prop | Required | Notes |
|------|----------|-------|
| `authProviders` | Yes | `AuthProvider[]` — one button per entry, rendered in order. |
| `title` | No | Heading (default "Sign in to your account"). |

`AuthProvider`:

| Field | Required | Notes |
|-------|----------|-------|
| `displayName` | Yes | Button label — `"Google"` renders "Continue with Google". |
| `clientId` | Yes | Opaque to the widget; passed back to `onSignIn` and used by the `oauth` default. |
| `displayIcon` | No | String → `<img src>`; anything else (inline SVG element) renders as-is. |
| `onSignIn` | No* | `(clientId) => void \| Promise<void>` — always wins; required for non-OIDC (SAML). |
| `oauth` | No* | `OAuthRedirectConfig` — enables the built-in OIDC redirect when `onSignIn` is omitted. |

`OAuthRedirectConfig`: `authorizeUrl` + `redirectUri` + `scopes` (required); `responseType` (default `code`), `usePkce` (default `true`), `extraParams` (e.g. `{ acr_values: '...' }` for UAE PASS).

Also exported: `buildOAuthAuthorizeUrl(clientId, config)` and `createDefaultSignIn(config)` for composing custom handlers.

## Integration

```typescript
import { ExternalAuth } from '@uipath/ui-widgets-external-auth';
import '@uipath/ui-widgets-external-auth/ExternalAuth.css';

function SignInPage() {
  return (
    <ExternalAuth
      authProviders={[
        {
          displayName: 'Google',
          clientId: '<GOOGLE_CLIENT_ID>',
          oauth: {
            authorizeUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
            redirectUri: `${window.location.origin}/auth/google/callback`,
            scopes: 'openid email profile',
          },
        },
        {
          displayName: 'Corporate SSO',
          clientId: '<SAML_CONNECTION_ID>',
          onSignIn: (clientId) =>
            window.location.assign(`/auth/saml/login?connection=${clientId}`),
        },
      ]}
    />
  );
}
```

Callback route sketch (the part the widget does NOT do): parse `code` + `state` from the query string → load `sessionStorage['uipath-external-auth:oauth:<clientId>']` → verify `state` → POST the token exchange (with `codeVerifier`) from your backend → create the app session → clean up the storage entry.

> Deployed coded apps mount at a non-root prefix — build `redirectUri` and the callback route path with `getAppBase()` from `@uipath/uipath-typescript` (skill Critical Rule 10), and register the resulting absolute URL at the provider.

## Anti-patterns

- **Do not use this widget to sign in to UiPath Cloud** — that is the scaffold's built-in PKCE flow (`useAuth()`), not an external provider button.
- **Do not expect the widget to complete the login** — it only starts the redirect; without your callback route, nothing signs in.
- **Do not start SAML from the browser via `oauth`** — SAML requires a backend-initiated flow through `onSignIn`.
- **Do not embed provider client secrets** in app code or `oauth` config — public client + PKCE only; exchanges needing a secret run on a backend.
- **Do not configure a provider with neither `onSignIn` nor `oauth`** — the button becomes a silent no-op.
