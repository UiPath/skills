# auth-strategy

## Purpose
Resolve the UiPath SDK's auth config inside the generated dashboard. Two cases — deployed (Action Center handles tokens) and local dev (PAT from `.env.local`). No custom postMessage protocol; the SDK owns that layer.

## Rules

1. **Don't reinvent token refresh.** When dashboards run inside UiPath Action Center, the SDK's `TokenManager` auto-detects the context via `isInActionCenter` (in `@uipath/uipath-typescript/core`) and wires its built-in `ActionCenterTokenManager`. That class implements the `REFRESHTOKEN` / `TOKENREFRESHED` postMessage handshake with the host page, validates origins, handles expiry, and re-handshakes on token rotation. The scaffold passes through with no postMessage code of its own.
2. **Local dev uses a PAT.** Read `import.meta.env.VITE_UIPATH_PAT` and pass it as `secret` in the SDK config. Long-lived PATs are fine for dev; the SDK accepts them directly without a refresh manager.
3. **No `secret` when running deployed.** Production builds MUST NOT include `VITE_UIPATH_PAT` — the `failBuildIfPatSet` plugin in `vite.config.ts` aborts `npm run build` if the variable is detected in any loaded env file. The deploy flow handles this by temp-moving `.env.local` aside before production builds; see [../plugins/deploy/impl.md § Build](../plugins/deploy/impl.md). When the SDK is initialized without a `secret` AND `isInActionCenter` is true, the SDK fetches a token from the parent on first request.
4. **Fail loudly, not silently.** If neither a PAT nor the Action Center context is available, the first SDK call fails with an authentication error. That's the correct outcome — beats silently issuing requests with a blank secret.
5. **In-memory only.** PATs read from `import.meta.env` live in JS heap. Never write the resolved secret to localStorage, sessionStorage, cookies, or URLs.

## Resolver shape

The scaffold ships `assets/templates/scaffold/src/lib/auth-strategy.ts.template` — the entire resolver is ~30 lines:

```ts
export function resolveAuth(): UiPathSDKConfig {
  const base = {
    baseUrl:    import.meta.env.VITE_UIPATH_BASE_URL,
    orgName:    import.meta.env.VITE_UIPATH_ORG_NAME,
    tenantName: import.meta.env.VITE_UIPATH_TENANT_NAME,
  };

  const pat = import.meta.env.VITE_UIPATH_PAT;
  if (pat) return { ...base, secret: pat };

  // No PAT → SDK detects Action Center context and uses
  // ActionCenterTokenManager automatically.
  return base;
}
```

That's the whole runtime auth surface for the generated app.

## What the SDK does for us (informational)

- **Origin allow-listing** — `ActionCenterTokenManager` validates the parent origin before posting and on every received message. We don't need our own allow-list.
- **Handshake timeout** — SDK times out the iframe handshake and surfaces an authentication error to the consuming code.
- **Token rotation** — when the SDK observes a 401 or `expiresAt` passes, it triggers another `REFRESHTOKEN` postMessage automatically.
- **Storage policy** — secret-mode tokens stay in-memory only (per the SDK's `TokenManager` implementation); they don't leak to storage.

If any of those properties matter for compliance review, point reviewers at `@uipath/uipath-typescript/src/core/auth/token-manager.ts` and `action-center-token-manager.ts` — that's the canonical implementation.

## Anti-patterns

- **Reimplementing the postMessage protocol** — the dead-code anti-example. The SDK ships it, just initialize and let it run.
- **Maintaining a parent-origin allow-list in the dashboard** — the SDK's allow-list is the source of truth.
- **Storing a PAT in localStorage so it survives reloads** — defeats the in-memory invariant.
- **Baking a PAT into the production bundle** — the `failBuildIfPatSet` plugin in `vite.config.ts` makes this a build error. If the build fails because `.env.local` still has a PAT, the deploy flow's `.env.local` move-aside step didn't run.
