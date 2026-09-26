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

## Project Layout

The app and its function backend are **two sibling projects**, each with its own `package.json` and `uipath.json`:

```text
<WORKSPACE>/
├── <APP>/        # Coded App — Vite + React; uipath.json = clientId / scope / redirectUri (PKCE config)
└── <BACKEND>/    # uipath.json = the functions map
```

1. Scaffold the backend as its own project next to the app: run `uip function new <BACKEND> -l ts` from `<WORKSPACE>/`. The backend project holds every function file, the functions SDK and the functions map; the app project keeps its PKCE config. Each `package.json` `name` is one package id with one project type, WebApp or Function — publishing a function under the app's id returns `400`, `Project type has changed since the latest published version`.
2. `<BACKEND>` is the package id and becomes the process name that prefixes every function name the app invokes — name it for the backend as a whole (`pricing-backend`); one project holds every function, each with its own `defineFunction` `name` and `path`.

## Token Flow

`Functions.invoke` sends the app's PKCE access token on every call and resolves the route itself. Deployed, the token arrives as `ctx.user.accessToken` — delegated identity, the caller's folder permissions apply. The app's PKCE scope string MUST include `OR.Default` explicitly; it is auto-granted to any registered External App but is not implicit in the scope string, and omitting it makes the deployed trigger return 403:

```text
openid profile email offline_access OR.Default
```

## Local Dev Loop

Two terminals, no proxy:

```bash
uip function serve    # terminal 1 — functions on :7070, hot reload
npm run dev           # terminal 2 — app dev server (Vite, :5173)
```

1. Under `import.meta.env.DEV`, fetch `http://localhost:7070/<PATH>` directly — `serve` answers with CORS `Access-Control-Allow-Origin: *`, so the cross-port call works as-is. Put this branch at the top of the wrapper that invokes the deployed function (below), so UI code is identical in both modes:

   ```ts
   if (import.meta.env.DEV) {
     const token = sdk.getToken();
     const res = await fetch("http://localhost:7070/quotes", {
       method: "POST",
       headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
       body: JSON.stringify(input),
     });
     const body = await res.json();
     if (!res.ok) throw Object.assign(new Error(body.error ?? `HTTP ${res.status}`), { statusCode: res.status });
     return body as QuoteOutput;
   }
   ```
2. Do NOT add `server.proxy` to the app's Vite config to reach the function — it breaks the app's OAuth callback (hard rule in the coded-apps guidance → `uipath-coded-apps`).
3. `serve` decodes `ctx.user` from a forwarded Bearer JWT when the app sends one (decoded, not verified — dev convenience only); an unauthenticated call (plain curl) gets `ctx.user = null`. `ctx.robot` / `ctx.platform` local values and env fallbacks → [local-dev-guide.md](local-dev-guide.md).

## Deployed Calls from the App

Deployed, call the function through the SDK's `Functions` service, HTTP-semantics functions included. `invoke` takes the function's name as Orchestrator registers it: the process name, `_`, then the `defineFunction` `name` (`get-quote` in process `pricing-backend` → `pricing-backend_get-quote`). `Functions.getAll({ folderKey })` lists these names. A bare `defineFunction` name throws `404`, and the message lists the names the folder exposes. `invoke` also takes typed input. Use `@uipath/uipath-typescript` 1.7.2 or later. Scope: `OR.Default`; add `OR.Folders.Read` when `invoke` is given `folderId`/`folderPath` rather than `folderKey`.

```ts
import type { UiPath } from "@uipath/uipath-typescript/core";
import { Functions } from "@uipath/uipath-typescript/functions";

export async function requestQuote(sdk: UiPath, input: QuoteInput): Promise<QuoteOutput> {
  return new Functions(sdk).invoke<QuoteInput, QuoteOutput>(
    { name: "pricing-backend_get-quote" },
    input,
    { folderKey: "<FOLDER_KEY>" },
  );
}
```

- Folder context is required: pass one of `folderKey` / `folderId` / `folderPath`, or rely on the folder context the SDK was initialized with.

## Timeout Budget

The gateway's 25 s timeout / `303 See Other` mechanism → [http-semantics-guide.md](http-semantics-guide.md): a browser caller loses the result permanently; server-side callers aren't CORS-blocked, but recovery via the redirect is undocumented. Budget every browser-invoked function to finish under 20 s ([SKILL.md](../../SKILL.md) JS Rule 6). Enforce it in the handler:

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

A resolved `invoke` is the function's declared output. Any non-2xx answer is thrown as a `UiPathError` subclass carrying `statusCode` and `message`. Branch on `statusCode`:

| Source | `statusCode` | Frontend treatment |
|---|---|---|
| Thrown `FunctionError(message, status)` | That status | 4xx: user-actionable — map the status to UI text |
| Input schema validation failure | `400` | Client bug — fix the request shape |
| Plain `throw` in the handler | `500` | Generic failure UI; treat as transient |
| 18 s guard above | `504` | Retryable |
| No function with that name in the folder context | `404` | Wiring bug — check the process-name prefix and the folder option |
| `OR.Default` missing from the app's scope | `403` | Wiring bug — recheck the app's scope string |

4xx is user-actionable, 5xx is transient/retryable. Full status semantics → [http-semantics-guide.md](http-semantics-guide.md).

Response shape discipline: the output schema describes success data only, and errors are thrown — a function never returns an `errors[]` array inside a 200. The frontend therefore branches on thrown vs resolved alone: resolved → the declared output contract; thrown → `statusCode`.
