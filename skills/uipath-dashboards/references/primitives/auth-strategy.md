# auth-strategy

## Purpose
Runtime auth resolver inside the generated dashboard app. Produces a `secret` string for the SDK from one of three ordered strategies. No OAuth, no External App.

## Inputs (runtime, not skill-time)
- `window` (iframe context — `basedomain` query param, `window.parent`)
- `document` (meta tags possibly injected by Apps service)
- `import.meta.env` (Vite env vars — `.env.local` for dev, `.env.production` for deploy)

## Outputs
A resolved `UiPathSDKConfig` with `secret` field populated — fed directly to `new UiPath(config)`.

## Rules
1. **Strategy order is fixed** — iframe postMessage → meta-tag → local PAT. Stop at first success.
2. **Validate parent origin against allow-list** before any postMessage handshake. Allow-list: `https://alpha.uipath.com`, `https://staging.uipath.com`, `https://cloud.uipath.com`, plus `http://localhost:*` for dev.
3. **Target postMessage to exact origin**, never `"*"`. Same discipline the SDK's `ActionCenterTokenManager` uses.
4. **In-memory only.** Never write resolved tokens to localStorage, sessionStorage, cookies, or URLs.
5. **Fail with actionable message** if no strategy succeeds. Don't silently init with blank secret.

## Details

### Strategy 1: iframe postMessage handshake (production path)
1. Read `basedomain` from `window.location.search`. If absent, skip to Strategy 2.
2. Validate against allow-list. If not allowed, throw `AuthStrategyError("Parent origin not allowed: <origin>")`.
3. `window.parent.postMessage({eventType: 'REFRESHTOKEN', content: {}}, basedomain)` (no clientId/scope since we're not OAuth).
4. Listen for `TOKENREFRESHED` response, validate `event.origin === basedomain`.
5. Extract `accessToken` + `expiresAt` from response. Return `{secret: accessToken, ...}`.
6. Timeout at 8s → throw; fall through to Strategy 2 isn't appropriate (the iframe signals "I'm running embedded" — falling through hides the host bug). So timeout → hard error.

### Strategy 2: meta tag (alt production path)
```html
<meta name="uipath:secret" content="<token>" />
```
If present, return that as `secret`. Future-compatible — if Apps service ships this mechanism instead of postMessage, we pick up automatically.

### Strategy 3: local PAT (dev path)
Read `import.meta.env.VITE_UIPATH_PAT`. If present, return as `secret`. This is how local dev works — user pastes PAT into `.env.local`.

### Throw if none
```ts
throw new AuthStrategyError(
  "No auth source available. Local dev: set VITE_UIPATH_PAT in .env.local. " +
  "Deployed: check basedomain query param + parent window responsiveness."
);
```

### Host-side requirements (appendix — for the user's future host)
When you build the host that responds to `REFRESHTOKEN`:
1. Validate the iframe's origin BEFORE responding. Only respond to known deployed-dashboard origins.
2. Target your `postMessage` to the iframe's exact origin, not `"*"`.
3. Short-lived tokens (≤15 min if possible); iframe re-handshakes on expiry via the SDK's token-manager.
4. Don't put tokens in URL params; don't log tokens.
5. Set CSP `frame-ancestors` on the host page to lock down which origins can embed the host.

Reference: mirror the SDK's `ActionCenterTokenManager` pattern (`src/core/auth/action-center-token-manager.ts` in `@uipath/uipath-typescript`). That class implements the correct iframe-side discipline; adapt the host side similarly.

### Template reference
The resolver is implemented in the scaffold template at `assets/templates/scaffold/src/lib/auth-strategy.ts.template`. See that file for the concrete TypeScript implementation.

### Fallback 2 (if uipath.json sentinel rejected at deploy)
If the Apps service rejects a sentinel `clientId` in `uipath.json` at deploy time, the user creates **one** non-confidential External App per tenant (shared across all dashboards), and pastes its clientId as the sentinel value. Runtime still uses `secret` mode — the clientId is not OAuth-exercised. This is a one-time-per-tenant setup, documented in the error surface when deploy's first attempt fails with "clientId not recognized".
