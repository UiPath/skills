# HTTP Semantics Guide

The HTTP contract of a coded function — how requests become `input`, how routes match, how returns and throws become responses — both under local `uip function serve` and deployed behind the Orchestrator gateway. Handler authoring → [authoring-guide.md](authoring-guide.md); invoke URL construction → [deployment-guide.md](deployment-guide.md).

## Input assembly

| Source | Rule |
|---|---|
| GET | query-string entries become `input`; body never read |
| POST/PUT/PATCH/DELETE | JSON body becomes `input`; locally an empty or unparseable body becomes `{}` (deployed, empty body is rejected by the gateway first — see table below) |
| Path params | merged UNDER input (`{...params, ...rawInput}`) — a body/query key shadows a same-named path param; params stay available uncoerced on `ctx.params` |

Query params are independent of path matching and validate through the `input` schema. Use path params for identity, query params for optional filters.

## Validation pipeline

Runs in the runtime (ajv compiled there — never a project dependency), in order:

1. Input is validated against the `input` schema before the handler runs; failure returns `400` with body `{"error":"ValidationFailed","details":{"formErrors":[...],"fieldErrors":{...}}}` and the handler is never called.
2. GET query values arrive as strings; coercion to schema types (number/boolean) is automatic for schema-first contracts. Only zod contracts need `z.coerce.number()` — the runtime never replaces a Standard Schema validator with the derived JSON Schema (that would drop refinements and coercion).
3. `@default` values (JSDoc tag on optional props, or schema `default`) are filled into missing fields before the handler sees `input`.
4. Output is validated against the `output` schema after the handler returns; failure returns `500` with body `{"error":"Handler returned invalid output","details":{...}}`.

## Route matching

The deployed trigger slug is `path` minus the leading `/`, pattern segments preserved verbatim (the `bindings_v2.json` metadata field `Slug` stores `path` verbatim, leading `/` included — [bindings-guide.md](bindings-guide.md)); resolution is route matching, not string comparison. Local serve and deployed agree.

| Pattern | Matches |
|---|---|
| `:param` | exactly one segment → `ctx.params.<NAME>` (string) |
| `:param{regex}` | one segment, regex-constrained |
| `:param?` | that segment or nothing |
| trailing `*` | one or more trailing segments; catch-all only — NOT captured as a param |

Rules:

- Routes are sorted by specificity, mirroring Orchestrator's `HttpTriggerMatcher.CompareSpecificity`: a literal segment beats a param regardless of declaration order — `/users/me` wins over `/users/:id`.
- Extra segments are not absorbed: `/list/:filter?` does not match `/list/a/b`. Add an explicit `*` route for a catch-all.
- A deployed request that matches no trigger returns:

```json
{ "message": "HTTP trigger not found for path 'my-functions/invoices/a/b'.", "errorCode": 1623 }
```

  as a `404`. The same 1623 appears when the invoke URL carries a wrong folder key — see [deployment-guide.md](deployment-guide.md).

## Response mapping

| Handler outcome | HTTP result |
|---|---|
| plain value / void | `200`, value JSON-serialized (void → body `null`) |
| `FunctionResponse {status, body?, headers?}` (incl. helpers `ok`/`created`/`noContent`/`badRequest`/...) | status passthrough; `204` or undefined body → empty body |
| raw `Response` | passed through untouched |
| thrown `FunctionError(message, status)` | that status (default `500`), body `{"error": <MESSAGE>, "details"?: ...}` |
| any other throw | `500`, body `{"error": <MESSAGE>, "details": <STACK>}` |

- A `FunctionError`'s `errorCode` never appears in an HTTP response body — it maps only onto the job fault surface ([job-mode-guide.md](job-mode-guide.md)). `errorCode` values that DO show up in HTTP bodies (1623, 4804, 4801) come from the gateway, not from your function.
- The plain-throw `500` carries the real message and stack trace unsanitized — the code is customer-owned, so this holds locally and deployed. Still throw `FunctionError` for anything a caller should read (see [SKILL.md](../../SKILL.md) JS Rule 1; details in [authoring-guide.md](authoring-guide.md#errors)).

## CORS

- **Local serve:** `origin: '*'`; `allowHeaders` covers `Content-Type`, `Authorization`, and the full `X-UiPath-*` platform-header set. Any local frontend (e.g. a coded app on :5173) fetches `http://localhost:7070/<PATH>` directly — no proxy.
- **Deployed:** only the `api.<HOST>` subdomain serves CORS headers; the portal domain does not. Browsers MUST call `https://api.<HOST>/...`; `curl` and server-side code can use either domain. URL shape → [deployment-guide.md](deployment-guide.md); browser wiring → [coded-app-wiring-guide.md](coded-app-wiring-guide.md).

## Deployed gateway behaviors

Sharp edges of the current PublicPreview gateway — observed behavior, not guarantees. None reproduce under local serve, so test deployed too ([local-dev-guide.md](local-dev-guide.md) covers the local loop).

| Symptom | Cause | Handling |
|---|---|---|
| `303 See Other` after 25 s | gateway timeout; redirect target is a portal-domain polling URL WITHOUT CORS | browser callers lose the result permanently — keep the handler under 20 s: `AbortSignal.timeout(...)` on every external call plus an overall guard (`Promise.race` at ~18 s). Server-side callers aren't CORS-blocked from the 303 target, but recovering the result that way is undocumented — apply the same budget everywhere |
| `400 errorCode 4804` | empty POST body (deployed only) | always send `body: '{}'` |
| `403` | caller token missing `OR.Default` scope | fix the token's scopes → [coded-app-wiring-guide.md](coded-app-wiring-guide.md) |
| `404 errorCode 1623` | no trigger matched: wrong slug, wrong folder key, or pattern mismatch | see Route matching + [deployment-guide.md](deployment-guide.md) |
| single `500` right after deploy | cold start | retry once |
| `errorCode 4801` on every route | stale `package-lock.json` in the package | regenerate lockfile, re-pack → [deployment-guide.md](deployment-guide.md) |

## Path naming

The slug is public API surface: it appears in every caller's invoke URL, and renaming `path` is a trigger delete+create — every existing caller breaks ([bindings-guide.md](bindings-guide.md)). Choose short noun slugs and let the method carry the verb: `POST /invoice`, not `POST /create-invoice`; `GET /invoices/:id`, not `GET /get-invoice`.
