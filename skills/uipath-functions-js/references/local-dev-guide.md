# Local Development Guide

The local loop for JS/TS coded functions: `uip function serve` for the HTTP surface, `uip function run` for one-shot job execution, plus the env/ctx differences between local and deployed. Handler authoring → [authoring-guide.md](authoring-guide.md); deployed behavior → [deployment-guide.md](deployment-guide.md).

## `uip function serve` — local HTTP server

```bash
uip function serve [--port 7070] [--runtime node|deno]
```

- Hot reload; auto-syncs the `uipath.json` functions map on start.
- Default port `7070`. Sharp edge: serve frees its port by killing whatever process currently holds it — anything else listening there dies. Run with `--port <PORT>` when another dev server you care about might occupy the default.
- `--runtime node` (default) or `deno` — the choice matters for `.env` loading (below).
- `GET http://localhost:7070/` = health check + list of all registered routes. Use it to confirm your function file was picked up.
- CORS is open ([http-semantics-guide.md](http-semantics-guide.md#cors)) — a browser app on another port (e.g. Vite `:5173`) fetches directly; never add a dev proxy. Frontend wiring → [coded-app-wiring-guide.md](coded-app-wiring-guide.md).

## The `.env` problem

Node cannot auto-load `.env`: the CLI's `--env-file` injection breaks in some environments (`node: --env-file= is not allowed in NODE_OPTIONS`). Two working options:

```bash
# Option A — Deno reads .env natively
uip function serve --runtime deno

# Option B — load .env into the shell, then serve on Node
set -a && source .env && set +a
uip function serve
```

`.env` for local platform access:

```bash
UIPATH_ACCESS_TOKEN=<OAUTH_TOKEN>
UIPATH_BASE_URL=https://cloud.uipath.com
UIPATH_ORG_ID=<ORG_UUID>
UIPATH_TENANT_ID=<TENANT_UUID>
```

## What is null locally

| ctx field | Deployed source | Under local serve |
|---|---|---|
| `ctx.user` | Gateway-forwarded caller identity | null unless the request carries `Authorization: Bearer <JWT>` — claims decoded straight from the token, so send a real token to exercise auth paths |
| `ctx.robot` | Platform-injected robot-identity headers | always null — nothing sends those headers locally |
| `ctx.platform` | Platform-injected `X-UiPath-*` headers (HTTP) / `runtime-context.json` (job) | null unless `UIPATH_BASE_URL` + `UIPATH_ORG_ID` + `UIPATH_TENANT_ID` are all set (all-or-nothing rule → [authoring-guide.md](authoring-guide.md)) |

Token fallback in handlers (robot-first to `UIPATH_ACCESS_TOKEN` — the local fallback for both identities) → [calling-uipath-apis-guide.md](calling-uipath-apis-guide.md). Never read base URL/org/tenant from input ([SKILL.md](../SKILL.md) Rule 9).

## Testing the HTTP surface

curl/fetch against the serve server — there is no `uip`-exposed invoke command ([SKILL.md](../SKILL.md) Rule 13):

```bash
curl -s http://localhost:7070/                                   # health + route list
curl -s "http://localhost:7070/invoices?limit=5"                 # GET: query string is the input
curl -s -X POST http://localhost:7070/invoice \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -d '{"invoiceId":"INV-1"}'
```

Local-only leniency: an empty or unparseable POST body becomes `{}` before schema validation; deployed, the gateway rejects it ([http-semantics-guide.md](http-semantics-guide.md)) — always send `-d '{}'` so the habit carries to production. Deployed-only failure modes → [deployment-guide.md](deployment-guide.md).

## `uip function run` — one-shot local job execution

Runs one function to completion with no server — the same code path a production job run uses. Job semantics, not an HTTP call ([SKILL.md](../SKILL.md) Rule 13).

```bash
uip function run --function <NAME> --input '{"key":"value"}'
uip function run --entrypoint functions/<FILE>.ts --input-file <INPUT_JSON_PATH>
```

| Flag | Meaning |
|---|---|
| `--function <NAME>` \| `--entrypoint <PATH>` | Target — exactly one: name resolved via `uipath.json`, or file path |
| `--input '<JSON>'` \| `--input-file <PATH>` | Input payload (default `{}`; file takes priority) |
| `--context '<JSON>'` \| `--context-file <PATH>` | Runtime-context JSON — simulate job identity/platform values (file takes priority) |
| `--runtime node\|deno` | Runtime (default `node`) |

Exit code mirrors the job outcome: non-zero when the run would Fault. Fault mapping and the runtime-context shape → [job-mode-guide.md](job-mode-guide.md).

Sharp edge: the CLI help for `run` may describe an HTTP invoke against the serve endpoint — that text is stale. `run` is the job runner; the flags above are the real surface and are forwarded correctly.

## Worked loop

```bash
# terminal 1
uip function serve --runtime deno

# terminal 2 — HTTP surface
curl -s http://localhost:7070/          # confirm the route registered
curl -s -X POST http://localhost:7070/invoice \
  -H 'Content-Type: application/json' -d '{"invoiceId":"INV-1","amount":50}'

# job surface — same handler, job semantics
uip function run --function approve-invoice --input '{"invoiceId":"INV-1","amount":50}'
echo $?                                  # 0 = Successful, non-zero = Faulted
```

## Mock at the network boundary

Not internal modules: stub `fetch`/HTTP responses so handler code runs unmodified — the same code that runs deployed. Module-level mocks hide the two classic local-passes-deployed-fails bugs:

- extensionless intra-project imports resolve locally but hang the deployed cold start with no logs — always `./_helpers.ts` ([SKILL.md](../SKILL.md) Rule 4);
- empty POST body accepted locally, rejected `400 4804` deployed (above).

Both surface only in production — [deployment-guide.md](deployment-guide.md).
