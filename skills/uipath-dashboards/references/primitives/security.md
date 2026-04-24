# security

## Purpose
Document the threat model, enforce guardrails in the generated code, and specify what the iframe host must do to be secure end-to-end.

## v1 token model

**Full user session token**, passed by host to iframe via postMessage. This means: blast radius if the token leaks = whatever the logged-in user can do in UiPath. Guardrails are **mandatory**, not nice-to-have.

## Guardrails (enforced in the scaffold and incremental-editor)

| Guardrail | Enforcement site |
|---|---|
| **CSP `frame-ancestors`** restricts who can iframe the deployed dashboard (UiPath cloud origins only) | `vite.config.ts.template` / deploy-time headers |
| **No `dangerouslySetInnerHTML`** with tenant data | `incremental-editor.md` pre-write regex check |
| **In-memory-only tokens** — never localStorage/sessionStorage/cookies | SDK's `ActionCenterTokenManager` pattern; auth-strategy template |
| **`.env.local` + `.env.production` gitignored** | `.gitignore.template` |
| **Build-time fail if `VITE_UIPATH_PAT` set in build env** | `vite.config.ts.template` plugin (aborts `npm run build` with message) |
| **No `console.log(sdk)`** | SKILL.md critical rule + incremental-editor regex |
| **Origin allow-list in auth-strategy** | `auth-strategy.ts.template` — matches SDK's pattern |
| **Scaffold generates `SECURITY.md`** in each dashboard | `SECURITY.md.template` |

## Generated `SECURITY.md` content (template)

Lives at `<project>/SECURITY.md`. Warns end-user that their dashboard runs with full-session-token scope and lists the guardrails above. See `assets/templates/scaffold/SECURITY.md.template`.

## Host-side requirements (your future host)

When you build the host that postMessages tokens to deployed dashboards:

1. **Validate iframe origin before responding to `REFRESHTOKEN`.** Only respond to known deployed-dashboard origins (check against a host-side allow-list).
2. **Target postMessage to the iframe's exact origin**, not `"*"`.
3. **Don't put tokens in URL params.** `basedomain` passes the origin (not a secret); tokens go through postMessage body only.
4. **Short-lived tokens with auto-refresh.** Ideally ≤ 15 min; SDK re-handshakes on expiry.
5. **CSP `frame-ancestors` on the host page** controls who can iframe the host.
6. **Log discipline.** Don't log tokens to browser console or server.

Reference implementation on the iframe side: `src/core/auth/action-center-token-manager.ts` in `@uipath/uipath-typescript` — mirror that pattern on the host side.

## v2 path: scoped tokens

If/when Apps platform gains a token-exchange endpoint (mint a scoped token per-iframe-per-session), migrate:
- iframe `auth-strategy.ts` resolver doesn't change (still reads `secret`).
- Host side swaps "forward my full session token" for "call token-exchange, forward scoped token".

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
