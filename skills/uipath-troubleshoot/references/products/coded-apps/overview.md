# Coded Apps

UiPath Coded Apps — custom web front-ends (**coded web apps**) and Action Center form apps (**coded action apps**) built in TypeScript/React and calling UiPath APIs through the `@uipath/uipath-typescript` SDK. Scaffolded, packed, published, and deployed with `uip codedapp`.

Unlike server-side products, a coded app runs **in the user's browser**. Most failures surface as an OAuth redirect error, a failed HTTP call, or a broken deployed URL — not as a faulted job with a trace.

## Runtime & Auth Model

- **SDK config comes from `<meta name="uipath:*">` tags**, not from code. `new UiPath()` reads `clientId`, `scope`, `orgName`, `tenantName`, `baseUrl`, `redirectUri` from those tags. Locally the tags are injected from **`uipath.json`** (project root, committed) — the single config source.
- **Auth is browser OAuth 2.0 Authorization Code + PKCE.** The External Application backing a coded app is a **non-confidential (public) client** with **user-delegated scopes**. The app redirects to UiPath, the user signs in, and the SDK exchanges the code for a token via `sdk.completeOAuth()`.
- **API host is the API subdomain** (`api.uipath.com`), NOT the portal domain (`cloud.uipath.com`). The portal domain does not return browser CORS headers.
- **Deployed apps** are served by the platform's Cloudflare Worker under `https://cloud.uipath.com/<org>/apps_/<system-name>`; the app must be built with a **relative** Vite base (`base: './'`) and read its route prefix from `getAppBase()`.

## Dependencies

- **Identity Server** — issues the OAuth token; owns the External Application (redirect URIs, scopes). Inspect/fix with `uip admin external-apps`.
- **Orchestrator / Data Fabric / Maestro / Action Center** — the APIs the SDK services call; each call needs a matching OAuth scope.
- **Apps service** — hosts and routes the deployed app; registered by `uip codedapp publish` / `deploy`.

## CLI

```
uip codedapp push [project-id]        — push local source to Studio Web
uip codedapp pull [project-id]        — pull project files from Studio Web
uip codedapp pack <dist>              — package build output into .nupkg
uip codedapp publish                  — upload .nupkg + register the app
uip codedapp deploy                   — deploy or upgrade the app (registers prod redirect URI)
uip admin external-apps get <client-id>       — registered redirect URIs + scopes of the OAuth client
uip admin external-apps update <client-id>    — add/replace redirect URIs (--redirect-uri) or scopes (--user-scope)
```

Key commands for troubleshooting:
- `uip admin external-apps get <client-id> --output json` — the External Application state: what redirect URIs and scopes are actually registered. Compare against what `uipath.json` requests.
- `uip admin external-apps update <client-id> --redirect-uri '<full-list>' --output json` — register a redirect URI. **`--redirect-uri` and `--user-scope` REPLACE the existing list** — always pass the complete desired set (existing + new), read first from `get`.
- `uip admin external-apps update <client-id> --user-scope '<full-list>' --output json` — register scopes.

## Evidence Sources

There is **no runtime job/trace/log CLI** for a deployed coded app. Diagnosis is current-state + the error signature the user reports:

| Source | What it tells you |
|--------|-------------------|
| Error string the user pastes | OAuth error param (`redirect_uri_mismatch`, `invalid_scope`), HTTP status (401/403/404), CORS message, deploy output |
| `uipath.json` (project root) | What the app **requests**: `clientId`, `scope`, `baseUrl`, `redirectUri` |
| `uip admin external-apps get <client-id>` | What the External Application **allows**: registered redirect URIs and scopes |
| `.uipath/app.config.json` | Deploy result: `appUrl`, `systemName` (present only after a successful `deploy`) |
| `vite.config.ts` | `base` and `server.port` — governs deployed routing and local dev URL |

The mismatch between what the app *requests* (`uipath.json`) and what the client *allows* (`external-apps get`) is the root of most coded-app auth failures.
