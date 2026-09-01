---
name: uipath-functions-js
description: "UiPath JS/TS Coded Functions — TypeScript/JavaScript serverless functions built as `defineFunction` handlers in `functions/` with `@uipath/coded-functions-js-sdk` and the `uip function` CLI (`new -l ts|js`, `serve`, `run`, `pack`, `publish`); project signals `package.json` + `uipath.json` functions map, `defineSchema<T>()` contracts. Covers HTTP triggers and job mode, `FunctionError`/status codes, `ctx.user`/`ctx.robot` tokens, calling `@uipath/uipath-typescript` from a function, `bindings_v2.json`, deploy/solution registration, and Coded App frontend↔function backend wiring. For Python functions (`pyproject.toml`, Pydantic, `-l py`, `uip function init`, `bindings.json`)→uipath-functions. For the Coded App frontend itself (React app code, PKCE setup, app deploy)→uipath-coded-apps. For LLM/agentic projects (`agent.json`, LangGraph)→uipath-agents."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath JS/TS Coded Functions

Deterministic TypeScript/JavaScript units — `defineFunction` handlers in `functions/` — that run on UiPath serverless. Every function can be started as an Orchestrator job; declaring `method` + `path` additionally exposes it as an HTTP endpoint (the backend for Coded Apps). Authored with `@uipath/coded-functions-js-sdk` (devDependency), managed with `uip function`.

## When to Use This Skill

- Scaffold, author, or modify a JS/TS coded function (`uip function new <NAME> -l ts|js`, `functions/*.ts`, `defineFunction`)
- Declare input/output contracts — `defineSchema<T>()` in TypeScript, bare JSON Schema literals in JavaScript
- Test locally: `uip function serve` (HTTP on :7070), `uip function run` (one-shot job), curl/fetch against `http://localhost:7070`
- Error handling: `FunctionError`, response helpers, HTTP status semantics, job fault semantics
- Call UiPath APIs from inside a function with `@uipath/uipath-typescript` and the `ctx.user`/`ctx.robot` tokens
- Wire a Coded App frontend to a function backend: tokens, CORS, timeout budget, local two-server dev loop
- Pack, publish, and invoke in production; register the project in a solution; resource bindings (`bindings_v2.json`)
- Debug deployed failures: cold-start hangs, errorCode 4801/4804/1623, 303 redirects, missing tokens

Do NOT use this skill for:
- Python coded functions (`pyproject.toml`, Pydantic Input/Output, `uip function init`) → `uipath-functions`
- The Coded App frontend itself (React/Vite app code, PKCE setup, app deploy) → `uipath-coded-apps`
- LLM/agentic projects (`agent.json`, LangGraph, agent loop) → `uipath-agents`

## Critical Rules

1. **Throw `FunctionError`, never plain `Error`.** A plain throw is always a generic 500 (`JsCodedFunction.HandlerError`) that leaks the raw stack; `FunctionError(message, status)` carries an author-controlled status (pass `errorCode` in options to set the job error code). Argument order is `(message, status)`. See [error handling](references/authoring-guide.md#errors).
2. **Contracts are schema-first.** `defineSchema<T>()` over interfaces (TS, lowered at build time) or a bare JSON Schema literal (JS). Do not use zod/arktype/valibot for new functions — they break static contract extraction and add a runtime dependency. No `$ref`, `any`, `bigint`, or tuples; the schema literal must be static.
3. **One default-exported `defineFunction` per file, directly under `functions/`.** Helper modules are `_`-prefixed (`functions/_helpers.ts`). Declare `method` + `path` together or omit both (job-only). Every function runs as a job; HTTP exposure is additive.
4. **Intra-project imports carry the `.ts` extension** (`./_helpers.ts`). Extensionless imports resolve in local dev but hang the whole runtime at production cold start, with no logs.
5. **Runtime deps go in `dependencies`, public npm only; the SDK stays in `devDependencies`.** Production runs `npm install --omit=dev` at cold start — a runtime import from `devDependencies` or a private registry crashes/hangs the function. Regenerate the lockfile after any dependency change; a stale `package-lock.json` fails every route with errorCode 4801.
6. **Finish in <20 s — the gateway times out at 25 s** and returns a `303` to a polling URL without CORS: a browser caller loses the result permanently, and recovering it server-side via the redirect is undocumented. Use `AbortSignal.timeout(...)` on every external call; move longer work to job mode.
7. **Deployed POST with empty input still needs `body: '{}'`** — the gateway rejects an empty body with `400 errorCode 4804` (local serve does not, so the bug only appears in production).
8. **Two tokens, two identities.** `ctx.user.accessToken` = the caller's token (delegated, caller's folder permissions); `ctx.robot.accessToken` = the function's own robot identity (S2S, privileged reads). `ctx.robot` is always null under local serve (`ctx.user` only when no Bearer token is sent) — fall back to `process.env["UIPATH_ACCESS_TOKEN"]`.
9. **Read platform coordinates from `ctx.platform`** (`baseUrl`, `orgId`, `tenantId`, `folderKey`), never from input fields — caller-controlled URLs are a redirect risk. Env vars (`UIPATH_BASE_URL`, `UIPATH_ORG_ID`, `UIPATH_TENANT_ID`) are the local-only fallback.
10. **Only the SDK `logger.*` reaches Orchestrator job logs.** `console.*` prints locally and is not forwarded.
11. **No `Buffer`.** Use `Uint8Array`, `TextEncoder`, `TextDecoder`.
12. **After `uip function publish`, manually update the Function Release** in Orchestrator (Automations → Processes) — triggers only sync to the new version once the release is updated.
13. **`uip function run` is a one-shot job execution, not an HTTP call.** To exercise the HTTP surface locally, curl/fetch against the `serve` server — no CLI subcommand invokes a route for you.

## Quick Start

### Step 1 — Scaffold

```bash
uip function new <FUNCTION_NAME> -l ts    # or -l js; --empty for no sample
cd <FUNCTION_NAME>
```

Creates `package.json`, `uipath.json` (functions map, auto-synced on every serve/pack), and `functions/` with a sample. TypeScript is the default language.

### Step 2 — Author

```ts
// functions/invoice.ts — one default-exported defineFunction per file
import { defineFunction, defineSchema, FunctionError } from "@uipath/coded-functions-js-sdk";

interface Input {
  invoiceId: string;
  /** @default 0 */
  amount?: number;
}
interface Output {
  approved: boolean;
}

export default defineFunction({
  name: "approve-invoice",
  method: "POST",
  path: "/invoice", // omit method+path entirely for a job-only function
  input: defineSchema<Input>(),
  output: defineSchema<Output>(),
  handler: async (input, ctx) => {
    if (!ctx.user?.accessToken) throw new FunctionError("Unauthorized", 401);
    return { approved: input.amount! < 10_000 }; // success data only — errors are thrown
  },
});
```

### Step 3 — Test locally

```bash
uip function serve                        # HTTP server on :7070, hot reload
curl -s -X POST http://localhost:7070/invoice \
  -H 'Content-Type: application/json' -d '{"invoiceId":"INV-1","amount":50}'

uip function run --function approve-invoice --input '{"invoiceId":"INV-1"}'   # one-shot job run
```

`GET http://localhost:7070/` lists all routes (health check). Node cannot auto-load `.env` — use `uip function serve --runtime deno` or export vars in the shell. See [local dev](references/local-dev-guide.md).

### Step 4 — Pack and publish

```bash
uip function pack        # -> .uipath/<PACKAGE>.<VERSION>.nupkg (raw sources + lockfile)
uip function publish     # upload to a process feed (--feed-id or interactive)
```

The package ships raw `.ts` sources plus `package-lock.json`; production installs dependencies at cold start — see [deployment](references/deployment-guide.md) for the dependency and lockfile rules that make or break this.

### Step 5 — Update the release and invoke

Update the Function Release to the new version in Orchestrator (Automations → Processes), then:

```bash
curl -s -X POST "https://api.<HOST>/<ORG_ID>/<TENANT_ID>/orchestrator_/t/<FOLDER_KEY>/<PACKAGE_ID>/invoice" \
  -H "Authorization: Bearer <TOKEN>" -H 'Content-Type: application/json' -d '{}'
```

`<FOLDER_KEY>` is the folder's Key GUID — discover it via `GET /orchestrator_/odata/HttpTriggers` (see [deployment](references/deployment-guide.md#invoke)). First call after deploy may 500 once (cold start).

### Step 6 — Register in a solution

```bash
uip solution projects add <FUNCTION_PROJECT_PATH>  # JS has no `uip function init` — the uipath.json marker is enough
uip solution pack
```

## CLI Reference

```bash
uip function new <NAME> -l ts|js [--empty]   # scaffold (TypeScript default)
uip function serve [--port 7070] [--runtime node|deno]   # local HTTP server, hot reload
uip function run --function <NAME> --input '{}'          # one-shot local job execution
uip function pack [--nolock]                 # build .uipath/<PACKAGE>.<VERSION>.nupkg
uip function publish [--feed-id <FEED_ID>]   # upload package to a process feed
uip function push --project-id <PROJECT_ID>  # sync sources to a Studio Web project
uip function runtime-install                 # one-time runtime pre-install (otherwise downloaded on first serve/run)
```

> `uip function init` is Python-only (JS/TS projects error with a pointer to `new --empty`). The plural spelling (`functions`) is retired — always write the singular — and the JS CLI's internal `invoke` subcommand is not exposed.

## Reference Navigation

| I need to… | Read |
|---|---|
| Write handlers, contracts, ctx, errors, logging | [authoring-guide.md](references/authoring-guide.md) |
| Run and test locally (serve, run, env, tokens) | [local-dev-guide.md](references/local-dev-guide.md) |
| Understand routing, status codes, deployed limits | [http-semantics-guide.md](references/http-semantics-guide.md) |
| Run functions as Orchestrator jobs, fault semantics | [job-mode-guide.md](references/job-mode-guide.md) |
| Pack, publish, invoke in prod, solutions, cold start | [deployment-guide.md](references/deployment-guide.md) |
| Bindings: entry-points.json, bindings_v2.json, overrides | [bindings-guide.md](references/bindings-guide.md) |
| Call UiPath APIs from a function (uipath-typescript, IS) | [calling-uipath-apis-guide.md](references/calling-uipath-apis-guide.md) |
| Wire a Coded App frontend to a function backend | [coded-app-wiring-guide.md](references/coded-app-wiring-guide.md) |

## Anti-patterns

1. **`throw new Error("…")`** — generic 500, raw stack leaked, no author-controlled status — Rule 1.
2. **Returning an `errors[]` array inside a 200.** Output schemas carry success data only; a function throws one error at a time.
3. **zod/arktype contracts on new functions** — break static extraction, drag a runtime dependency — Rule 2.
4. **Extensionless relative imports** — work locally, hang production cold start — Rule 4.
5. **Runtime dependency in `devDependencies` or on a private registry** — skipped or unfetchable at cold start — Rule 5.
6. **Adding `server.proxy` to the Coded App's Vite config to reach the function** — it breaks the app's OAuth callback; fetch `http://localhost:7070/<PATH>` directly (serve sends CORS `*`).
7. **Accepting `baseUrl`/`orgId`/`tenantId` as function input** — redirect risk; use `ctx.platform` — Rule 9.
8. **Calling the portal domain from a browser** — no CORS there; browsers must call the `api.<HOST>` subdomain.
9. **`console.log` for production diagnostics** — never reaches job logs — Rule 10.
10. **Building the invoke URL from the trigger's own Id** — 404 errorCode 1623; the URL takes the folder Key GUID + package id + slug.
11. **Expecting a caller to recover a result after 25 s** — keep HTTP functions under 20 s, move longer work to job mode — Rule 6.
