# Coded App Wiring Guide

Architecture and mechanics of the Coded App (frontend) ↔ JS function (backend) pairing: when a function belongs between the app and the platform, token flow, the two-server local loop, deployed calls, timeout budget, and the error contract the frontend codes against. The app side itself (scaffolding, PKCE registration, app deploy) → `uipath-coded-apps`.

## When to Put a Function Between the App and the Platform

Default: the app calls UiPath APIs directly with `@uipath/uipath-typescript` and the user's PKCE token. Add a function backend when any of these apply:

| Reason | Why a function |
|---|---|
| Credentials / API keys / secrets | Must exist server-side only — browser code and its network tab are public. Secret Vault pattern → [calling-uipath-apis-guide.md](calling-uipath-apis-guide.md) |
| S2S calls to third-party systems | Third-party credentials come from the vault via the function's robot identity — never a browser-held key |
| Audit / tracing of privileged operations | Server-side `logger.*` lands in job logs; browser-side logging is unverifiable |
| Heavy / multi-call orchestration | One browser round-trip; N platform calls server-side, inside the timeout budget |
| Hiding internal API shapes | Function exposes a minimal stable contract; OData filters, folder IDs, endpoint quirks stay server-side |

**Honest boundary:** a function in front of *delegated* calls is not a security layer. The caller's `OR.Default` PKCE token already grants broad Orchestrator API access — anything the function does with `ctx.user.accessToken`, the browser could do directly with the same token. Folder RBAC, not the function layer, is the effective security boundary for delegated calls. A function only *adds* privilege through its own robot identity (`ctx.robot`, Secret Vault pattern → [calling-uipath-apis-guide.md](calling-uipath-apis-guide.md)).

## Token Flow

The app sends its PKCE access token on every function call:

```ts
headers: { Authorization: `Bearer ${token}` }
```

Deployed, it arrives as `ctx.user.accessToken` — delegated identity, the caller's folder permissions apply. The app's PKCE scope string MUST include `OR.Default` explicitly; it is auto-granted to any registered External App but is not implicit in the scope string, and omitting it makes the deployed trigger return 403:

```text
openid profile email offline_access OR.Default
```

## Local Dev Loop

Two terminals, no proxy:

```bash
uip function serve    # terminal 1 — functions on :7070, hot reload
npm run dev           # terminal 2 — app dev server (Vite, :5173)
```

1. The app fetches `http://localhost:7070/<PATH>` directly — `serve` answers with CORS `Access-Control-Allow-Origin: *`, so the cross-port call works as-is.
2. Do NOT add `server.proxy` to the app's Vite config to reach the function — it breaks the app's OAuth callback (hard rule in the coded-apps guidance → `uipath-coded-apps`).
3. `serve` decodes `ctx.user` from a forwarded Bearer JWT when the app sends one (decoded, not verified — dev convenience only); an unauthenticated call (plain curl) gets `ctx.user = null`. `ctx.robot` / `ctx.platform` local values and env fallbacks → [local-dev-guide.md](local-dev-guide.md).

## Deployed Calls from the App

```ts
const FN_BASE = import.meta.env.DEV
  ? "http://localhost:7070"
  : "https://api.<HOST>/<ORG_ID>/<TENANT_ID>/orchestrator_/t/<FOLDER_KEY>/<PACKAGE_ID>";

async function callFn<T>(path: string, input?: unknown, token?: string): Promise<T> {
  const res = await fetch(`${FN_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    // Never an empty body: the deployed gateway rejects it with 400 errorCode 4804.
    body: JSON.stringify(input ?? {}),
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.error ?? `HTTP ${res.status}`);
  return body as T;
}
```

- Always the `api.<HOST>` subdomain — the portal domain sends no CORS headers ([http-semantics-guide.md](http-semantics-guide.md#cors)). curl doesn't enforce CORS, so a portal-domain URL "working" in a terminal proves nothing about the browser.
- `<ORG_ID>`/`<TENANT_ID>` as GUIDs (preferred over slugs in browser URLs). `<FOLDER_KEY>` is the folder's Key GUID, shared by every function in the folder — discovery recipe in [deployment-guide.md](deployment-guide.md).

## Timeout Budget

The gateway's 25 s timeout / `303 See Other` mechanism → [http-semantics-guide.md](http-semantics-guide.md): a browser caller loses the result permanently; server-side callers aren't CORS-blocked, but recovery via the redirect is undocumented. Budget every browser-invoked function to finish under 20 s ([SKILL.md](../SKILL.md) Rule 6). Enforce it in the handler:

```ts
handler: async (input, ctx) => Promise.race([
  actualHandler(input, ctx),
  new Promise<never>((_, reject) =>
    AbortSignal.timeout(18_000).addEventListener("abort", () =>
      reject(new FunctionError("Function timed out", 504)),
    ),
  ),
])
```

Put `signal: AbortSignal.timeout(8_000)` on every external `fetch` inside the handler so one slow upstream cannot eat the whole budget. Work that cannot fit under 20 s does not belong behind a browser call: move it to a job-mode function ([job-mode-guide.md](job-mode-guide.md)).

## Error Contract for the Frontend

Every non-2xx response from the function runtime has the shape `{ "error": "<MESSAGE>", "details"?: ... }`; gateway errors (last row) carry `{ "errorCode": <N>, "message": "..." }` instead:

| Source | Status / body | Frontend treatment |
|---|---|---|
| Thrown `FunctionError(message, status)` | That status, `error` = message | 4xx: user-actionable — surface `error` |
| Input schema validation failure | `400`, `error` = `"ValidationFailed"`, `details` = per-field errors | Client bug — fix the request shape |
| Plain `throw` in the handler | `500`, `error` = message, `details` = stack | Generic failure UI; treat as transient |
| 18 s guard above | `504`, `error` = `"Function timed out"` | Retryable |
| Gateway (no function reached) | e.g. `403` missing `OR.Default`, `404` errorCode `1623` bad route/folder key, `400` errorCode `4804` empty body | Wiring bug — recheck scope, URL, body |

Branch on status class: 4xx is user-actionable (show `error`, let the user correct input or permissions), 5xx is transient/retryable. Full status semantics → [http-semantics-guide.md](http-semantics-guide.md).

Response shape discipline: the output schema describes success data only, and errors are thrown — a function never returns an `errors[]` array inside a 200. The frontend can therefore branch on `res.ok` alone: ok → body matches the declared output contract; not ok → body carries `{error, details?}`.
