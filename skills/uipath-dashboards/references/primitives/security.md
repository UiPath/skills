# security

## Purpose
Document the threat model and the guardrails enforced in generated code. Token refresh is the SDK's responsibility (see [auth-strategy.md](auth-strategy.md)); this file covers the surface area we OWN inside the dashboard bundle.

## v1 token model

**Full user session token**, supplied by UiPath Action Center via the SDK's `ActionCenterTokenManager` postMessage handshake. Blast radius if the token leaks = whatever the logged-in user can do in UiPath. Guardrails are **mandatory**, not nice-to-have.

The SDK owns the token at runtime — we never see it directly. Our concern is: don't log it, don't persist it, don't let it leave memory. Same discipline applies to the local-dev PAT path, plus an extra build-time guardrail that prevents PATs from ever ending up in the production bundle.

## Guardrails (enforced in the scaffold and incremental-editor)

| Guardrail | Enforcement site |
|---|---|
| **CSP `frame-ancestors`** restricts which origins can iframe the deployed dashboard (UiPath cloud origins only) | `vite.config.ts.template` / deploy-time headers |
| **No `dangerouslySetInnerHTML`** with tenant data | `incremental-editor.md` pre-write regex check |
| **In-memory-only tokens** — SDK's `TokenManager` keeps secret-mode tokens off localStorage/sessionStorage/cookies | SDK behavior; we just don't override it |
| **`.env.local` + `.env.production` gitignored** | `.gitignore.template` |
| **Build-time fail if `VITE_UIPATH_PAT` is set in the production build's loaded env** | `vite.config.ts.template` `failBuildIfPatSet` plugin uses Vite's `loadEnv` so `.env.local`, `.env.production.local`, etc. are all caught. Deploy flow handles this by temp-moving `.env.local` aside before `npm run build`. |
| **No `console.log(sdk)`** | SKILL.md critical rule + incremental-editor regex |
| **Generated `SECURITY.md`** in each dashboard | `SECURITY.md.template` |

## What we DO NOT need to enforce ourselves

These were guardrail concerns in earlier drafts; the SDK's `ActionCenterTokenManager` covers them:

- **Origin validation on postMessage** — SDK checks parent origin before posting and on every received message.
- **Handshake timeout** — SDK times out on unresponsive parent and surfaces an authentication error.
- **Token rotation on expiry** — SDK re-runs the `REFRESHTOKEN` handshake when `expiresAt` passes or on 401.
- **Allow-list of trusted parent origins** — SDK's allow-list is the source of truth; duplicating it in the dashboard would just create drift.

If a future audit or compliance question lands on these, point reviewers at `@uipath/uipath-typescript/src/core/auth/token-manager.ts` and `action-center-token-manager.ts` — that's the canonical implementation.

## Anti-patterns to reject in incremental-editor

| Regex | What it flags |
|---|---|
| `dangerouslySetInnerHTML=\{` | HTML injection surface |
| `console\.log\([^)]*sdk` | token-in-log |
| `localStorage\.(setItem\|getItem).*token` | token in web storage |
| `document\.cookie.*=.*token` | token in cookie |
| `window\.location.*=.*token` | token in URL |
| `innerHTML\s*=` | DOM injection surface (prefer React state) |

Any edit matching a pattern → halt with "security anti-pattern detected; see primitives/security.md".

## v2 path: scoped tokens

If/when the platform exposes a token-exchange endpoint (mint a scoped token per-iframe-per-session), the dashboard side doesn't change — the SDK's `TokenManager` would pick up scoped tokens from the same `REFRESHTOKEN`/`TOKENREFRESHED` postMessage shape; only the host's response payload changes.
