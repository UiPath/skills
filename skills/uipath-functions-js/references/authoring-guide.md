# Authoring Guide — defineFunction, Contracts, Context, Errors

Field-level reference for writing JS/TS coded functions: `defineFunction` options, schema-first contracts, `FunctionContext`, error handling, logging. Running locally → [local-dev-guide.md](local-dev-guide.md); routing and deployed status codes → [http-semantics-guide.md](http-semantics-guide.md).

## File Layout and Manifest Sync

- One default-exported `defineFunction` per file, directly in `functions/` — discovery is top-level only, not recursive.
- Helper modules: `_`-prefix them (`functions/_helpers.ts`) and import with the `.ts` extension ([SKILL.md](../SKILL.md) Rules 3-4). Discovery skips `_`-prefixed files and `.d.ts`. Sharp edge (current behavior): a helper file WITHOUT the `_` prefix breaks function discovery silently — always prefix.
- `uipath.json` `functions` map auto-syncs on every `serve`/`pack`/`push`: keyed by filename, values `functions/<FILE>:default`, entries pointing outside `functions/` pruned. Never hand-edit it.

## defineFunction Options

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | `string` | yes | Logical name — manifest + Studio |
| `method` | `GET\|POST\|PUT\|PATCH\|DELETE` | no* | Only together with `path` |
| `path` | `string` | no* | Must start `/`; `:param` segments supported ([routing](http-semantics-guide.md)) |
| `input` / `output` | contract schema | no | See [Contracts](#contracts) |
| `handler` | `(input, ctx) => result` | yes | Sync or async |
| `description` | `string` | no | Shown in Studio |
| `tags` | `string[]` | no | Studio grouping |

*`method` + `path` together or both omitted. `defineFunction` throws at module load on: one of the pair alone, a method outside the five verbs, a path not starting `/`.

**One calling mode per function.** `method` + `path` make it an HTTP-semantics function, invoked through its Orchestrator HTTP trigger — the Coded Apps backend case (the trigger executes each call as a job under the hood). Omitting both makes it a plain run-as-job function. On a job run there is no HTTP request: `ctx.user` carries no caller identity (may hold a legacy compat object — test `ctx.user?.accessToken`, not `!ctx.user`), `ctx.params`/`ctx.headers` empty. The runtime does not yet enforce the split — an HTTP function can currently be started as a plain job; treat that as an enforcement gap, never a design pattern. Details → [job-mode-guide.md](job-mode-guide.md).

## Handler Return Forms

| Return | Result |
|---|---|
| Plain value | JSON body, status 200 |
| `FunctionResponse` `{status, body?, headers?}` | Full control; `204` or undefined body → empty response |
| Raw `Response` | Passed through untouched |
| `void` | Empty 200 |

Return success data only — errors are thrown ([Errors](#errors)). A returned response with status >= 400 faults the job when run as one.

## Contracts

A contract is a curated JSON Schema subset — inert data, statically extractable without executing your code (what Studio Web reads).

**TypeScript** — `defineSchema<T>()` over an interface. Inert at runtime; lowered to the equivalent JSON Schema literal at build (`pack`/`serve`/`run`). A deprecated `type` alias of `defineSchema` exists — write `defineSchema`.

**JavaScript** — write the JSON Schema literal directly; the handler's input type derives from the literal (add `// @ts-check` for editor typing):

```javascript
export default defineFunction({
  name: "hello",
  method: "POST",
  path: "/hello",
  input: {
    type: "object",
    properties: { name: { type: "string", default: "World" } },
    additionalProperties: false,
  },
  handler: async (input) => ({ message: `Hello, ${input.name}!` }),
});
```

### TS type → schema mapping

| TypeScript | JSON Schema |
|---|---|
| `string` / `number` / `boolean` | Same-type schema |
| Literal union, TS `enum` | `enum` |
| `T[]` | `array` + `items` |
| Interface / object type | Closed object: `additionalProperties: false`, non-optional props in `required` |
| `foo?: T` | Property present, not in `required` |
| `Record<string, T>` | `additionalProperties: <schema of T>` |
| `unknown` (value position) | `{}` — any JSON value |
| `Date` | `string`, `format: date-time` |
| Non-literal union `A \| B` | `anyOf` |
| `any`, `bigint`, tuples, functions, top-level `unknown` | **Rejected at build with a diagnostic** |

### Defaults via JSDoc

TS types cannot express defaults — put `@default` in JSDoc on an optional property (`/** @default "World" */` above `name?: string;`); tag text parses as JSON (`"World"` → string, `3` → number, `true` → boolean). Lowers to schema `default`; the runtime fills the field when the caller omits it.

### Allowed keywords (hand-written literals)

`type` (string/number/integer/boolean/object/array/null), `title`/`description`/`default`, `const`/`enum`, `format` (date-time/date/time/email/uri/uuid), `minLength`/`maxLength`/`pattern`, `minimum`/`maximum`/`exclusiveMinimum`/`exclusiveMaximum`/`multipleOf`, `items`/`minItems`/`maxItems`/`uniqueItems`, `properties`/`required`/`additionalProperties`, `anyOf`/`oneOf`/`allOf`. No `$ref`/`$defs`, no custom keywords or format functions. The literal must be static: no spreads, computed keys, or identifier references.

### Validator libraries (zod/arktype/valibot)

Standard Schema objects (zod >= 4.2, arktype >= 2.1.28, valibot >= 1.2 + `@valibot/to-json-schema` >= 1.5) still work, but obtaining the contract requires executing the module — Studio Web static extraction breaks — and the validator becomes a runtime dependency. Do not use for new functions. On the run path an existing validator is preserved as-is (refinements and coercions intact, never replaced by a derived schema), so migrating old functions is about extraction and dependency weight, not correctness.

### Runtime validation

ajv compiles the contract inside the runtime — it is never a project dependency. Full pipeline (400 `ValidationFailed`, GET coercion, defaults, invalid output → 500) → [http-semantics-guide.md](http-semantics-guide.md).

## FunctionContext

Second handler argument. Import the `FunctionContext` type from the SDK to type `_`-helper signatures with the same interface.

| Field | Shape | Null / empty when |
|---|---|---|
| `user` | `{sub, name?, email?, accessToken?}` — caller identity; `accessToken` = the caller's Bearer token (delegated calls) | Unauthenticated HTTP; carries no caller identity on job runs (may hold a legacy compat object — test `ctx.user?.accessToken`, not `!ctx.user`; → [job-mode-guide.md](job-mode-guide.md)) |
| `robot` | `{key, accessToken}` — the function's own serverless-robot identity | Local serve — fall back per [SKILL.md](../SKILL.md) Rule 8 |
| `platform` | `{baseUrl, orgId, tenantId, folderKey}` | All-or-nothing: null unless baseUrl + orgId + tenantId all present; `folderKey` independently nullable. Local fallback: `UIPATH_BASE_URL`/`UIPATH_ORG_ID`/`UIPATH_TENANT_ID` |
| `params` | Strings bound from `:param` path segments | Empty on job runs |
| `headers` | Request headers, keys lowercased — job key at `ctx.headers["x-uipath-jobkey"]` | Empty on job runs |

Using the tokens against UiPath APIs → [calling-uipath-apis-guide.md](calling-uipath-apis-guide.md).

## Errors

Throw `FunctionError` — argument order is `(message, status)`, never `(status, message)`. In JS (and transpile-only TS runs) the wrong order slips through and misbehaves at runtime.

```typescript
throw new FunctionError("Invoice not found", 404);                              // HTTP form
throw new FunctionError("Invoice not found", 404, "NOT_FOUND", { id });         // + errorCode + details
throw new FunctionError("Already renewed", { errorCode: "ALREADY_RENEWED" });   // status-less — job-only functions (a job fault has no HTTP status)
```

- Over HTTP: response status = thrown `status` (500 when omitted); body `{error: <MESSAGE>, details?}`. `errorCode` is job-surface only ([http-semantics-guide.md](http-semantics-guide.md)); fault mapping → [job-mode-guide.md](job-mode-guide.md).
- Plain `Error` or any other throw: 500, generic code `JsCodedFunction.HandlerError`, message as `error`, stack as `details` (customer-owned code is not sanitized).
- Custom error classes: extend `FunctionError` and pass status/errorCode through `super` — e.g. to carry a downstream API's status. Do not reassign `this.name`: the runtime identifies a `FunctionError` structurally by `name === "FunctionError"`, not by `instanceof FunctionError`.

```typescript
class UpstreamError extends FunctionError {
  constructor(message: string, downstreamStatus: number) {
    super(message, downstreamStatus, "UPSTREAM_API_ERROR");
  }
}
```

### Response helpers

Helpers **return** a `FunctionResponse` — execution continues; use in conditional branches. `FunctionError` **throws** — execution halts; use for auth failures and conditions that invalidate the rest of the handler.

| Helper | Status / body |
|---|---|
| `ok(body)` / `created(body)` / `accepted(body?)` | 200 / 201 / 202, `body` |
| `noContent()` | 204, no body |
| `badRequest(msg?, details?)` | 400, `{error, details?}` |
| `unauthorized(msg?)` / `forbidden(msg?)` / `notFound(msg?)` / `conflict(msg?)` | 401 / 403 / 404 / 409, `{error}` |
| `response(status, body?, headers?)` | Any status, full control |

## Logging

Only the SDK `logger.*` (exported by `@uipath/coded-functions-js-sdk`) is forwarded to Orchestrator job logs — scoped per job key, flushed before the response. `console.*` prints to the local/server console only and is never forwarded.
