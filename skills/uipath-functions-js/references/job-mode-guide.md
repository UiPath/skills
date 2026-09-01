# Job Mode Guide

How a JS/TS coded function executes as an Orchestrator job: the runtime context, `ctx` in job mode, fault semantics, the StandardError→JobErrorData contract, and job logging. Local one-shot parity → [local-dev-guide.md](local-dev-guide.md); deploy/release mechanics → [deployment-guide.md](deployment-guide.md).

## The Model

Every function in `functions/` is job-startable — from a Trigger, a Maestro process, a Flow, or the Orchestrator job API against the function's release. Declaring `method` + `path` adds an HTTP route on top; omitting both makes the function job-only. Run-mode enforcement is not yet implemented: an HTTP-declared function can currently be started as a plain job. That is current behavior, not a guarantee — do not design around it.

## How a Job Run Executes

One process, one job, one function. The platform writes `.uipath/run/runtime-context.json`; the runtime reads it, imports only the target module (no HTTP server, no route table), validates input, runs the handler, validates output, and reports one terminal job result.

| runtime-context field | Effect |
|---|---|
| `workloadAccessToken` | → `ctx.robot.accessToken` — the job's robot identity |
| `robotKey` | → `ctx.robot.key` |
| `baseUrl`, `orgId`, `tenantId`, `folderKey` | → `ctx.platform` (all-or-nothing rule → [authoring-guide.md](authoring-guide.md) FunctionContext table) |
| `jobId` | serverless-internal job id, echoed in the result — not the Orchestrator JobKey |
| `jobApiEndpoint` | IPC endpoint (named pipe / unix socket) for result + log reporting; absent locally — result goes to stdout |
| `resourceOverwrites` | not on `ctx` — installed process-wide for `@uipath/uipath-typescript` to read; see [bindings-guide.md](bindings-guide.md) |

## ctx in Job Mode

- `ctx.user` carries no caller identity — there is no HTTP caller. Treat it as null, but do not test `if (!ctx.user)` to detect job mode: the current runtime sets a legacy compat object (`{workloadAccessToken}`, for packages built against SDK < 0.5) whenever a robot token exists. Check `ctx.user?.accessToken` instead.
- `ctx.robot` is populated from the runtime context (`{key, accessToken}`); null when the context provides neither field (e.g. a bare local `uip function run`).
- `ctx.params` and `ctx.headers` are `{}` — the job key does NOT surface in a pure job run. `ctx.headers["x-uipath-jobkey"]` exists only on deployed HTTP-triggered executions (→ [authoring-guide.md](authoring-guide.md) FunctionContext table).
- `ctx.platform` comes only from the context file; local token/coordinate fallbacks → [local-dev-guide.md](local-dev-guide.md).

## Fault Semantics

Handler outcome → job status:

| Handler outcome | Job result |
|---|---|
| Plain return value passing the output schema | Successful; value = job output arguments |
| `FunctionResponse` / raw `Response`, status < 400 | Successful; body = output (raw body JSON-parsed when possible); output schema skipped |
| `FunctionResponse` / raw `Response`, status >= 400 | **Faulted** — a returned error response is an error outcome, not output |
| Thrown `FunctionError` | **Faulted**, author-controlled error fields |
| Any other throw | **Faulted**, `JsCodedFunction.HandlerError` |
| Return value failing the output schema | **Faulted**, `JsCodedFunction.OutputValidationFailed` |
| Input failing the input schema | **Faulted**, `JsCodedFunction.ValidationFailed` — the handler never runs |

## The Error Contract

Every fault renders as one `StandardError {code, title, detail, category, status}` and travels field-for-field to Orchestrator's `JobErrorData` (the job error info). Job-surface only — HTTP error bodies keep the `{error, details?}` shape ([http-semantics-guide.md](http-semantics-guide.md)).

| StandardError field | From `FunctionError` | From plain throw |
|---|---|---|
| `code` | `errorCode` (default `JsCodedFunction.FunctionError`) | `JsCodedFunction.HandlerError` |
| `title` | `message` | `message` |
| `detail` | `details` (string as-is, else JSON-stringified) | stack |
| `status` | `status` (absent when not given — never invented) | absent |
| `category` | `User` | `User` |

System-category failures (the runtime's own machinery) are sanitized: generic title/detail on every surface, real error only in the runtime logs.

### Emitted error codes (all `JsCodedFunction.`-prefixed)

| Code | Emitted when |
|---|---|
| `FunctionError` | `FunctionError` thrown without explicit `errorCode` |
| `HandlerError` | unanticipated throw from handler code |
| `ErrorResponse` | handler returned (not threw) a status >= 400 response |
| `ValidationFailed` | input rejected by the input schema |
| `OutputValidationFailed` | output rejected by the output schema |
| `InvalidInput` | job input was not valid JSON |
| `InvalidFunctionDefinition` | target function/module could not be resolved or loaded (category Deployment) |
| `RunFailed` | one-shot run failed outside the handler |
| `InternalError` | runtime machinery failed (category System) |

### FunctionError for job-only functions

A job fault has no inherent HTTP status — use the status-less options form instead of inventing one:

```typescript
throw new FunctionError("Contract already renewed", { errorCode: "ALREADY_RENEWED" });
```

Job error info shows `code: "ALREADY_RENEWED"`, `title: "Contract already renewed"`, `category: "User"`, no `status`. Full constructor forms and the `(message, status)` argument-order gotcha → [authoring-guide.md](authoring-guide.md).

## Job Logging

Only SDK `logger.*` reaches Orchestrator job logs ([SKILL.md](../SKILL.md) Rule 10). Job mode adds two specifics: forwarding is installed before the target module is imported, so `logger.*` calls at module top level are captured for the job too; and all forwarded logs are flushed before the result is reported, so nothing is lost to a fast exit. Logs are scoped to the job. `console.*` prints to process output only.

## Local Parity: uip function run

`uip function run` executes the same one-shot code path the platform uses — same validation, same fault semantics, same StandardError rendering — with the exit code mirroring the job outcome (0 Successful, 1 Faulted):

```bash
uip function run --function <FUNCTION_NAME> --input-file input.json --context-file ctx.json
```

`--context-file` / `--context` inject a runtime-context JSON to simulate platform fields (`workloadAccessToken`, `baseUrl`, `orgId`, `tenantId`, `folderKey`, …). Flags, env fallbacks, and runtime selection → [local-dev-guide.md](local-dev-guide.md).

## Starting Deployed Functions as Jobs

There is no function-specific job API. Publish the package and update the Function Release to the new version ([SKILL.md](../SKILL.md) Rule 12), then start jobs the standard Orchestrator way against that release — manually, from a Trigger, from Maestro or a Flow, or via the Orchestrator job-start API. The job's input arguments are validated against the function's input schema before the handler runs. Release update, versioning, and invoke mechanics → [deployment-guide.md](deployment-guide.md).
