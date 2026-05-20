---
name: uipath-api-workflow
description: "[PREVIEW] UiPath API Workflow assistant — author, run, package, publish JSON workflows executed by `uip api-workflow run`. Covers logical/hierarchical structure (Sequence, Assign, JavaScript, If with #Wrapper/#Then/#Else, ForEach, DoWhile, Break, TryCatch, Wait, Response — including nested patterns) AND HTTP / Integration Service connector activities (Gmail, Outlook, GitHub, Slack, etc.) authored via `uip api-workflow registry resolve` + `stub`. Triggers on prompts about UiPath API workflows, project type \"Api\", JSON workflow files containing `document.dsl`/`do[]`, any of those activity types, or fetching data from a public/vendor API. Uses `uip api-workflow run` for local execution and `uip solution pack`/`publish` for deployment. For .flow Maestro→uipath-maestro-flow. For .xaml/coded RPA→uipath-rpa. For coded agents→uipath-agents. For Coded Apps→uipath-coded-apps."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath API Workflow Assistant

> **Preview** — this skill is in preview. Behavior, file shapes, and rules may change as the underlying executor and StudioWeb roundtrip story evolve.

Build, run, and publish UiPath API Workflows — JSON files conforming to the CNCF Serverless Workflow DSL 1.0.0 with UiPath activity-type extensions. Executed by `@uipath/api-workflow-executor` via `uip api-workflow run`. Packaged as `Type: "Api"` projects via `uip solution pack`.

## When to Use This Skill

- User wants to **create or edit** an API workflow JSON file
- User wants to **run** an API workflow locally with `uip api-workflow run`
- User wants to **package** an API workflow project into `.nupkg` / solution `.zip`
- User wants to **publish** an API workflow to UiPath Cloud / Orchestrator
- User asks about **activity types** (Sequence, Assign, JavaScript, If, ForEach, DoWhile, Break, TryCatch, Wait, Response, HTTP Request, Connector)
- User asks about **nested control flow** — If inside ForEach, TryCatch around a loop, conditional Break, multi-way branching, etc.
- User asks for an **Integration Service connector activity** (Gmail Send Email, Outlook Get Newest Email, GitHub Search Issues, Slack Send Message, etc.) — follow the discovery flow in [references/connector-activity-discovery.md](references/connector-activity-discovery.md)
- User asks for a **generic HTTP Request** that needs to render in StudioWeb's designer — same discovery flow
- User asks about **JavaScript expressions, `$context`, `$input`, `$workflow`, `WorkflowStart`, or the `export.as` pattern**
- User asks how to **debug** a failing API workflow run

Do NOT use for: `.flow` Maestro flows (→ `uipath-maestro-flow`), `.xaml` / coded RPA (→ `uipath-rpa`), coded agents (→ `uipath-agents`), Coded Web Apps (→ `uipath-coded-apps`).

**Connector activities come from the registry, not from guessing.** HTTP Request and Integration Service Connector activities (Gmail Send Email, Outlook Get Newest Email, etc.) need StudioWeb-side editor metadata (`metadata.uiPathActivityTypeId` + `metadata.configuration`) to render correctly in the designer. The data is NOT in `uip is activities list`. Use `uip api-workflow registry resolve` + `uip api-workflow registry stub`: `resolve` searches the StudioWeb TypeCache (`projectType=Api`) for candidate GUIDs; `stub` combines the TypeCache entry with the Integration Service Elements schema (full endpoint path, request/response fields, multipart signal) and emits a ready-to-paste activity object — picking Http kind (`UiPath.Http`) or IntSvc kind (`UiPath.IntSvc`) automatically, building `metadata.configuration`, computing the slot and export-bucket keys, and declaring `multipartParameters` when needed. Follow the flow in [references/connector-activity-discovery.md](references/connector-activity-discovery.md). **NEVER invent a `uiPathActivityTypeId` or hand-author the configuration blob** — both come from the stub output.

## Core Principles

1. **Know before you write.** Read the existing workflow file before editing. Read an example template before creating from scratch.
2. **Start minimal, iterate to correct.** Add one activity at a time. Run with `--no-auth --output json` after each addition. Fix what breaks. Repeat.
3. **Validate by running.** There is no `uip api-workflow validate` command — local execution is the only validator. The executor fails fast on malformed JSON, unknown activity types, or missing required fields.
4. **Fix errors by category.** Triage: Structure > Expression > Activity Config > Logic. Higher-category fixes often resolve lower-category errors automatically.

## Critical Rules

1. **Workflow file is JSON, not YAML.** Top-level keys: `document` (with `dsl: "1.0.0"`), `evaluate` (`language: "javascript"`, `mode: "strict"`), `do` (one root sequence — named `Sequence_1` in the template skeleton, but the literal key may differ in existing workflows; always read the actual key from the file before editing — containing `WorkflowStart` + user activities). See [references/workflow-file-format.md](references/workflow-file-format.md).
2. **`WorkflowStart` is always the first activity** inside the root sequence's `do` array. It hydrates variable defaults into `$context.variables` and forwards inputs to `$input`. Never remove, rename, or modify it. `isTransparent: true` (only `WorkflowStart` uses `true`).
3. **Every activity is a single-key object** wrapped in the `do` array: `{ "<ActivityKey>": { ...activity body... } }`. Activity keys must be **globally unique** across the whole workflow — including `#Wrapper`, `#Then`, `#Else`, `#Body` suffixes.
4. **Every activity should `export` its output** to propagate state. Two patterns:
   - **Variables (Assign only):** `{ ...$context, variables: { ...$context.variables, ...$output } }`
   - **Outputs (everything else):** `{ ...$context, outputs: { ...$context?.outputs, "<ActivityKey>": $output } }`
   See [references/expressions-and-context.md](references/expressions-and-context.md).
5. **String literals in `Assign.set` / `Response` / If `when` MUST be wrapped as `"${'literal'}"`** — a JS string inside an expression. Plain `"literal"` runs fine under `uip api-workflow run`, but **StudioWeb's designer normalizes unwrapped values to `"${literal}"` on save** (treating them as expressions you typed into the property panel). At runtime the bare identifier `literal` has no binding → `ReferenceError: literal is not defined`. Use single quotes inside the expression to avoid JSON escaping: `"set": { "tier": "${'PLATINUM'}" }`. Numbers, booleans, and references like `${$context.variables.X}` need no extra wrapping. (Response payloads have a related but distinct constraint — see rule 15.) **Scope:** this rule applies to Assign / Response / If / variable contexts only. **It does NOT apply to connector `bodyParameters` / `queryParameters` / `pathParameters` — those take BARE literals; `${'...'}` there is read as an expression and the field is cleared on save.** See rule 16 and [references/connector-activity-discovery.md#field-shape-rules-flat-keys-bare-literals-renamed-export-hub-prefix](references/connector-activity-discovery.md#field-shape-rules-flat-keys-bare-literals-renamed-export-hub-prefix). See [references/troubleshooting.md](references/troubleshooting.md#studioweb-roundtrip-pitfalls).
6. **Each `Assign` activity MUST set exactly ONE variable.** `Assign.set` is a single-key object, NOT a multi-variable update. **StudioWeb's designer collapses multi-key `set` blocks to one key on save**, silently dropping the others — the runtime then only updates the surviving key. To update N variables, use N separate Assign activities placed sequentially in the same `do` array. Example: instead of `"set": { "sum": "${$context.variables.sum + 1}", "count": "${$context.variables.count + 1}" }` (loses `count` after StudioWeb save), write two Assigns — `Assign_Sum` with `"set": { "sum": "${...}" }` and `Assign_Count` with `"set": { "count": "${...}" }`. Each runs in order; each Assign's variables export merges its single key into `$context.variables`.
7. **If activity requires the wrapper pattern.** `If_N#Wrapper` contains `If_N` (switch), `If_N#Then`, `If_N#Else`. Both `#Then` and `#Else` MUST end with `"then": "exit"` to prevent fall-through. Conditions in `when` MUST be wrapped in `${...}`. For deeply-nested If patterns and multi-way branching, see [references/control-flow-patterns.md](references/control-flow-patterns.md).
8. **Loops (ForEach, DoWhile) require a `#Body` element** inside `do`. ForEach body uses index-aware accumulation (resets on iteration 0); DoWhile body uses simple accumulation. Loop variables (`each`, `at`) are plain strings, NOT expressions.
9. **DoWhile `for.in` is always `"${ [1] }"`.** The `doWhile` condition controls repetition. The body MUST update the condition variable, otherwise the loop runs forever.
10. **Nested loops MUST use distinct iterator/index names.** Outer `for.each: "outerItem"`, inner `for.each: "innerItem"`. Reusing `currentItem` shadows the outer. "Distinct" just means "not the same string" — semantic (`outerItem` / `innerItem`) and incremental (`item1` / `item2`, `currentItem` / `currentItem2`) naming both work.
11. **Loop iterators and catch error variables are prefixed with `$` in expressions.** Declare `for.each: "currentItem"` (plain string, no `$`); reference it everywhere else (in `when` conditions, in script bodies, in `set` expressions, in body export patterns) as `$currentItem` — the `$` is a literal character in the global identifier name. `currentItem` is not a reserved name — `for.each: "customer"` binds `$customer`, `for.each: "row"` binds `$row`, etc. Same shape for `for.at` (`$currentItemIndex`, `$idx`, etc.) and `catch.as` (`$error`, `$err`, etc.). Empirically verified: the executor calls `setVariables({"$currentItem": item, ...})` — `currentItem` (no `$`) is **not bound** as a global. Forgetting the `$` produces `<name> is not defined`.
12. **Break exits only the innermost enclosing loop.** To exit nested loops, set a flag variable + check it in the outer loop. Break value MUST be the string `"true"`, with `then: "exit"` and `set: "${$input}"`. Only valid inside a `#Body`.
13. **Use `$workflow.input.<name>` to read workflow inputs**, never `$input.<name>`. `$input` is the *task's* input — for any non-first task, it's the previous task's output, NOT the workflow arguments.
14. **JavaScript scripts read `$context`/`$workflow`/`$input` as globals.** Scripts MUST `return` a value. The task's `run.script.arguments` field is StudioWeb designer scaffolding — keep it as the standard `"${{ \"$context\": $context, \"$workflow\": $workflow, \"$input\": $input }}"` block for designer roundtrip; the runtime ignores it.
15. **Response activity shape — STRICT for StudioWeb roundtrip:**
    - `markJobAsFailed` is a sibling of `response`, not nested inside it.
    - Always include `"then": "end"` — without it, the workflow does not terminate properly. `then: "end"` is for Response only; `then: "exit"` is for control-flow branches/loops.
    - **Object-valued responses MUST use the single-expression form**, NOT the JSON-object-with-`${}`-fields form. StudioWeb's designer corrupts the latter on save (issue **SW-28452** / [UiPath/cli#1537](https://github.com/UiPath/cli/issues/1537)).
      - ✗ Wrong (CLI runs but StudioWeb corrupts): `"response": { "tier": "${$context.variables.tier}", "count": "${$context.variables.count}" }`
      - ✓ Correct: `"response": "${{ tier: $context.variables.tier, count: $context.variables.count }}"`
      Inside the outer `${{ ... }}` you are already in expression scope, so reference variables/outputs directly without an inner `${...}` wrapper. JS object literal keys can be unquoted identifiers (`tier:`, `count:`); literal string values use single quotes (`status: 'ok'`); numbers/booleans/references are bare. The designer leaves an already-wrapped single expression alone; the JSON-object form gets flattened to a stringified expression where inner `${...}` substitutions are inside JS double-quoted strings (which don't interpolate), turning each field into the literal text of its expression.
      - Either `"${ { ... } }"` (single-brace, expression-of-object-literal) or `"${{ ... }}"` (double-brace, object-literal-expression form) is valid — both evaluate to the same JS object. Pick one and stay consistent within a workflow.
    - For single-value responses (returning one variable or one expression), the simple form is fine: `"response": "${$context.outputs.Javascript_1}"` or `"response": "${'done'}"`.
    - **On-disk is authoritative.** Even with the single-expression workaround, every StudioWeb designer save can re-trigger normalization passes that may corrupt the Response shape. After any designer roundtrip, re-validate with `uip api-workflow run --no-auth` and re-apply the workaround if needed. Until SW-28452 ships a fix, treat the file on disk as truth, not what the designer renders.
16. **Connector activities (Http kind AND IntSvc kind) are produced by `uip api-workflow registry resolve` + `stub`, gated by a connection ping for vendor activities.** The `stub` command combines TypeCache lookup (GUID + `InstanceParameters`) with Integration Service Elements metadata (full path, request/response fields, multipart signal) and emits the activity object — with `unifiedTypesCompatible: true` and `savedJitInputFieldId` so StudioWeb renders the **unified activity card** (the one on the current activity picker). Discovery flow:
    1. **Resolve** — `uip api-workflow registry resolve "<keyword>" --output json`. Returns candidates with `uiPathActivityTypeId`, `displayName`, `connectorKey`, `objectName`, `httpMethod`, `activityType`. Pick the right GUID by `displayName` / `connectorKey` (filter by connector name when the operation name is ambiguous — e.g. "gmail" vs "outlook" for "send email").
    2. **(IntSvc kind / vendor only) Verify a working connection.** `uip is connections list <connector-key> --output json` → pick `Id`. `uip is connections ping <uuid>` is **REQUIRED** — listing-state and runtime-state diverge (orphaned upstream element, expired OAuth, wrong tenant). On `ConnectionNotEnabled` / 404 `"Connection […] is invalid or you do not have access to it"`, run the unfiltered fallback `uip is connections list --output json` and search for a different `Id` whose `ConnectorKey` matches. Re-ping. Abort only when no UUID for that connector pings cleanly. NEVER author against a connection that hasn't pinged — it WILL 401 in cloud.
    3. **Stub** — `uip api-workflow registry stub <activity-type-id> [--connection-id <uuid>] [--inputs '<json>'] --output json`. Returns: `Activity` (single-key object — drop directly into the root sequence's `do` array), `Kind` (`"Http"` or `"IntSvc"`), `SlotKey` (the activity key in the `do` array, e.g. `GetNewestEmail_1`), `ExportBucketKey` (what `export.as` writes AND what `$context.outputs.<X>` reads as, e.g. `getNewestEmail_1`, `http_request_1`, `ListEmails_1`), `ResponseFields` (downstream binding targets), `Warnings`. The CLI builds `metadata.configuration`, picks Http kind vs IntSvc kind from `connectorKey`, computes both keys, hub-prefixes the endpoint when IS Elements requires it, and declares `multipartParameters` for multipart operations. NEVER hand-author `metadata.configuration`, invent a `uiPathActivityTypeId`, or reconstruct either key from `objectName` — use what the stub returned. `--inputs` values are passed through verbatim — pass bare strings for literals, `${...}` for references (see field-shape rule (b) below).
    4. **Required-field cross-check — MANDATORY after every stub call.** The stub drops `required: true` request fields. Run `uip is resources describe <connector-key> <object-name> --operation <op> --connection-id <uuid> --output json` (or parse `metadata.configuration.optionalConfiguration.fieldsContainer.inputFields` from the stub's own output) and confirm every `required: true` field appears in the corresponding `queryParameters` / `pathParameters` / `bodyParameters` block. Verified case: Outlook `getNewestEmail` requires `parentFolderId` (`fieldLocation: "query"`); the stub returns `queryParameters: {}` unless that field was passed via `--inputs`. Re-stub with `--inputs '{"<field>":"<value>"}'` or hand-edit the activity. Skipping this check is the second-most-common cause of "renders fine, runs fine, fails in cloud" connector activities (see [troubleshooting.md](references/troubleshooting.md#required-request-field-dropped-by-registry-stub)).
    5. **Kind-specific finalization.**
       - **Http kind** (HTTP Request, `connectorKey === uipath-uipath-http`): the stub leaves `<REPLACE_WITH_TARGET_URL>` in `bodyParameters.url` (unless passed via `--inputs`). Replace with the target URL (literal or `${$workflow.input.<name>}`). `connectionId: "ImplicitConnection"` is fine for inline-credential calls. See the verified template at [assets/templates/connector-call-example.json](assets/templates/connector-call-example.json) (a real stub-generated workflow that fetches catfacts).
       - **IntSvc kind** (vendor curated, `UiPath.IntSvc`): if `--connection-id` was omitted, the stub contains `<REPLACE_WITH_VENDOR_CONNECTION_UUID>` placeholders — replace before running. Output payload is wrapped: read `$context.outputs.<ExportBucketKey>.content.<field>`, NOT `.<field>`. NEVER use Http kind with a vendor connection UUID — that produces 401 "Invalid Element token" in cloud.
    6. **NEVER ship a workflow with `<REPLACE_WITH_*>` placeholders in `with.connectionId` or `with.connectionResourceId`.** StudioWeb's properties panel renders the placeholder string as if it were a real connection name — the connection pill shows `<REPLACE_WITH_VENDOR_C...>` with a red error, and the workflow 401s in cloud. The placeholder is a sentinel for "you forgot to run `stub` with `--connection-id`," not a value the user fills in later. If you don't have a pinged UUID, STOP authoring and ask the user — do not emit the placeholder. Same for `<REPLACE_WITH_TARGET_URL>` in Http kind. The vendor template at [assets/templates/vendor-curated-call-example.json](assets/templates/vendor-curated-call-example.json) keeps the placeholder ONLY because it is a template; generated workflows MUST have real values.
    7. **(Solutions-mode + IntSvc kind only) Sync the connection into the Solution catalogue.** When the project lives under a `Solution/` tree, every vendor connection used by an IntSvc kind activity MUST also be declared as a Solution resource (`Solution/resources/solution_folder/connection/<connector-key>/<name>.json`) AND registered in the per-user debug overwrites (`Solution/userProfile/<guid>/debug_overwrites.json`). Without both, StudioWeb's properties panel marks the activity with **"to debug this resource, select a connection for it from the resource definition page"**, and clicking the activity overwrites `with.connectionId` with `null` in `Workflow.json` (the runtime resolves from `Workflow.json`; the panel resolves from the Solution resource tree + debug overwrites, which is why "Run" works but the panel breaks). The two-step CLI flow: (a) `uip api-workflow bindings sync --workflow <Workflow.json>` — generates `bindings_v2.json` next to the workflow (the input StudioWeb normally produces in-memory on open). (b) `uip solution resource refresh --solution-folder <path>` — reads every project's `bindings_v2.json`, uses `@uipath/resource-builder-sdk` to write both the catalogue file and the per-user debug overwrites via `editOverwritesAsync`. Idempotent and additive: run after every Workflow.json edit that adds/changes a connection. **SKIP this step entirely for:** (a) Http kind activities (`call: "UiPath.Http"`, `connectionId: "ImplicitConnection"` — literal sentinel, not a real connection), (b) non-connector activities (Sequence/Assign/If/ForEach/TryCatch/Wait/Response — no connectionId at all), (c) standalone projects with a top-level `project.json` and no `Solution/` wrapper. See [connector-activity-discovery.md — Step 5](references/connector-activity-discovery.md#step-5--solutions-mode-intsvc-kind-sync-the-connection-into-the-solution-catalogue).

    **Field-shape rules — must hold across edits, not just at stub time. Violating any silently drops data on the first StudioWeb save:**
    - **(a) Flat dotted keys.** Connector field names like `message.toRecipients` are literal keys, NOT paths. `"message.toRecipients": "..."`, NOT `{ message: { toRecipients: "..." } }`. Nested objects are dropped.
    - **(b) Literals are BARE in connector params.** Plain `"andrei@uipath.com"`, NOT `"${'andrei@uipath.com'}"`. The Assign / Response wrap rule (rule 5) is **inverted** here — `${'...'}` reads as a (broken) expression and the field clears on save. References (`${$context.variables.X}`) stay wrapped because they're real expressions.
    - **(c) Use `Data.SlotKey` and `Data.ExportBucketKey` from the stub verbatim.** Connector activities are the only activity type where the slot key (in the `do` array) and the export-bucket key (what `$context.outputs.<X>` reads as) can differ. The stub computes both; never derive either by hand from `objectName`. The two are sometimes identical (e.g. Outlook `ListEmails` → both `ListEmails_1`) and sometimes different (e.g. HTTP → `HttpRequest_1` slot vs `http_request_1` bucket).
    - **(d) Endpoint may include a hub prefix.** Outlook `send-mail-v2` → `/hubs/productivity/send-mail-v2`. The stub fills the full path from IS Elements; don't truncate.

    See [references/connector-activity-discovery.md](references/connector-activity-discovery.md) for the full flow, sample `stub` output, and worked examples (Http kind HTTP Request, IntSvc kind GetNewestEmail, IntSvc kind multipart SendEmail).
17. **Pass input as a JSON string.** `--input-arguments '{"key":"value"}'`. Invalid JSON exits 1.
18. **Always `--output json`** when parsing CLI output programmatically. Success → `{ "Result": "Success", "Code": "WorkflowRun", "Data": {...} }`. Failure → `{ "Result": "Failure", "Message": "...", "Instructions": "..." }` with exit 1.
19. **Build & publish goes through the solution packager.** API workflows pack via `uip solution pack <solutionDir> <outputDir>` and publish via `uip solution publish <package.zip>`. There is no `uip api-workflow build` or `uip api-workflow publish` command. Project type must be `"Api"` in the solution `.uipx`.
20. **Never run `uip api-workflow run` without an explicit user "yes."** Authoring and editing the JSON happens autonomously; *running* it does not. Before each validation invocation, ask the user: (a) run validation now or skip, (b) if running, with `--no-auth` (fast, structure-only — IntSvc kind vendor calls fail) or with auth (real Integration Service calls — vendor side effects WILL happen: emails sent, tickets created, files uploaded). Suggest a default based on workflow content (`--no-auth` for control-flow-only + Http kind `ImplicitConnection`; with-auth for any IntSvc kind vendor activity), but wait for the user's answer. Never invoke `uip api-workflow run` with auth on speculation — once a vendor call goes out, it can't be unsent.

## Workflow Phases

### Phase 0: Discovery

Before touching anything, understand what exists.

For **edit** requests:
1. Read the existing workflow file with `Read`
2. Identify activity keys already in use (avoid collisions)
3. Identify variables, inputs, outputs already declared
4. Identify export patterns in use (stay consistent)

For **create** requests:
1. Read [assets/templates/api-workflow-template.json](assets/templates/api-workflow-template.json) for the empty skeleton
2. Read a closer example based on need:
   - Conditional branching with error handling → [assets/templates/conditional-workflow-example.json](assets/templates/conditional-workflow-example.json)
   - Loops with aggregation → [assets/templates/loop-aggregation-example.json](assets/templates/loop-aggregation-example.json)
   - Heavily nested control flow (TryCatch around DoWhile around If with Break) → [assets/templates/nested-control-flow-example.json](assets/templates/nested-control-flow-example.json)
3. For nested patterns specifically, read [references/control-flow-patterns.md](references/control-flow-patterns.md) — pattern catalog for If-in-If, ForEach-with-If, TryCatch-around-loop, conditional Break, etc.

### Phase 1: Plan

Decide which activities to use and in what order.

| User wants | Activity type | Key points |
|------------|---------------|------------|
| Set/transform variables | **Assign** | Sets `$context.variables`; uses variables export pattern |
| Run custom logic | **JavaScript** (JsInvoke) | Inline JS; access context via `$context` / `$workflow` / `$input` globals (NOT `arguments[0]`) |
| Branch on condition (2-way) | **If** | `#Wrapper` + `#Then` + `#Else` structure required |
| Branch on condition (3+ way) | **Chain of Ifs** | Each `#Else` holds the next If — see [control-flow-patterns.md](references/control-flow-patterns.md#2-multi-way-branching-3-outcomes) |
| Iterate over collection | **ForEach** | `for.each`/`for.in`/`for.at`; needs `#Body` |
| Repeat until condition | **DoWhile** | `for.in: "${ [1] }"`; needs `#Body`; must update condition variable |
| Handle errors (whole batch) | **TryCatch around loop** | One bad item kills the batch — see [control-flow-patterns.md](references/control-flow-patterns.md#6-trycatch-around-a-loop-whole-batch-error-handling) |
| Handle errors (skip & continue) | **TryCatch inside body** | One bad item skipped, loop continues — see [control-flow-patterns.md](references/control-flow-patterns.md#7-trycatch-inside-a-loop-body-skip-and-continue-error-handling) |
| Return result and end | **Response** | `then: "end"`; `markJobAsFailed` sibling of `response` |
| Pause execution | **Wait** | `wait.seconds`/`minutes`/`milliseconds` |
| Exit loop early | **Break (in If)** | Wrap Break in an If — there's no "break when" condition on Break itself. `break: "true"` (string!), `then: "exit"`, `set: "${$input}"` |
| Exit nested loops | **Flag variable + Break twice** | Set a flag in inner loop, check + Break in outer — see [control-flow-patterns.md](references/control-flow-patterns.md#5-conditional-break-inside-a-loop) |
| Call an arbitrary REST API (catfacts, stock prices, weather, any public/internal HTTP endpoint) | **Unified HTTP Request** (`call: "UiPath.Http"`, Http kind) | `uip api-workflow registry resolve "http request"` → pick the HTTP Request GUID → `registry stub <guid> --inputs '{"method":"GET","url":"<TARGET>"}' --output json`. The stub emits `call: "UiPath.Http"` with `unifiedTypesCompatible: true` so StudioWeb renders the unified HTTP card. **NEVER use `call: "http"`** (deprecated simple form — renders as block icon). See [connector-activity-discovery.md](references/connector-activity-discovery.md#http-kind--call-uipathhttp-http-request-curated-activity) and the verified template at [assets/templates/connector-call-example.json](assets/templates/connector-call-example.json). |
| Call a vendor service via its UiPath connection (Gmail, Outlook, GitHub, Slack, etc.) | **Vendor curated activity** (`call: "UiPath.IntSvc"`, IntSvc kind) | `uip is connections list/ping` for the UUID → `uip api-workflow registry resolve "<keyword>"` → `registry stub <guid> --connection-id <uuid>`. Stub returns IntSvc kind with the full hub-prefixed endpoint. Never use `UiPath.Http` with a vendor connection UUID. See [connector-activity-discovery.md](references/connector-activity-discovery.md#intsvc-kind--call-uipathintsvc-vendor-curated-activity) |

Before generating, determine:
1. Which activities are needed and in what order
2. What unique keys to assign (check existing keys to avoid collision)
3. What variables to declare (in `document.metadata.variables.schema.document.properties`)
4. What inputs/outputs to declare (in `input.schema` / `output.schema`)

### Phase 2: Generate or Edit

For each activity, read its reference section in [references/task-types.md](references/task-types.md), copy the minimal JSON, fill in values.

**For CREATE:** copy from a template, then add user activities AFTER `WorkflowStart` inside the root sequence (literally `Sequence_1.do` in the template skeleton).

**For EDIT:** read the file first, identify the exact insertion / replacement point, use `Edit` with sufficient context for unique matching.

Workflow skeleton:
```json
{
  "document": { "dsl": "1.0.0", "name": "...", "version": "0.0.1", "namespace": "default", "metadata": { "variables": { "schema": { "format": "json", "document": { "type": "object", "properties": {...}, "title": "Variables" } } } } },
  "input":  { "schema": { "format": "json", "document": { "type": "object", "properties": {...}, "title": "Inputs" } } },
  "output": { "schema": { "format": "json", "document": { "type": "object", "properties": {...}, "title": "Outputs" } } },
  "do": [{ "Sequence_1": { "do": [ { "WorkflowStart": { /* system */ } }, /* user activities */ ], "metadata": {...} } }],
  "evaluate": { "mode": "strict", "language": "javascript" }
}
```

### Phase 3: Validate by Running

After authoring or editing, **ask the user before running anything** (see Critical Rule 20). The choice has real consequences:

| Mode | Flag | What happens | Use when |
|--|--|--|--|
| No-auth | `--no-auth` | Skips token loading. Structure / expressions / control flow validated. IntSvc kind vendor calls fail with a missing-token error. | Workflow contains only Sequence / Assign / JS / If / ForEach / DoWhile / Break / TryCatch / Wait / Response, OR Http kind HTTP with `connectionId: "ImplicitConnection"`. Default for most authoring iterations. |
| With auth | (none) | Uses the user's `uip login` token. Real Integration Service calls — vendor APIs touched, side effects happen. | Workflow contains a IntSvc kind vendor activity AND the user has confirmed it's OK to send the real call (email actually sent, ticket actually created, file actually uploaded). |

Phrase the question explicitly, with a recommended default. Examples:

- Control-flow workflow: "Workflow's ready. Validate with `--no-auth`? (Y/n)"
- IntSvc kind workflow: "Workflow's ready. It contains a IntSvc kind Outlook send-mail-v2 call — running with auth WILL send a real email to `<recipient>`. Options: (1) skip validation, (2) run `--no-auth` (will fail at the connector call but confirms structure), (3) run with auth and send the email. Which?"

Wait for the user's reply. Then run the chosen command:

```bash
# User picked --no-auth:
uip api-workflow run ./my-workflow.json --no-auth --output json

# User confirmed running with auth (uip login required):
uip api-workflow run ./my-workflow.json --output json
```

If the user picks "skip," tell them the exact command to run themselves and stop.

**Read the failure output:**
- `Message` describes the error
- `Instructions` often contains the fix
- Exit code: `0` = success, `1` = failure

**Fix in this order** (higher categories often resolve lower ones):
1. **Structure** — missing `#Wrapper`/`#Body`, duplicate keys, malformed JSON, missing `WorkflowStart`
2. **Expression** — missing `${...}`, unwrapped condition, undefined references
3. **Activity Config** — wrong required fields, wrong export key casing, missing `then: "end"` on Response
4. **Logic** — wrong behavior, infinite loops, unreachable code

See [references/troubleshooting.md](references/troubleshooting.md) for the full pitfall catalog.

### Phase 4: Package and Publish

Once the workflow runs locally, deploy via the solution packager.

**Pack:**
```bash
uip solution pack <solutionDir> <outputDir> \
  --name <PACKAGE_NAME> \
  --version 1.0.0 \
  --output json
```

The packager auto-detects `Type: "Api"` projects, validates structure, copies workflow files, generates `operate.json` + `package-descriptor.json`, and produces a `.nupkg` wrapped in a `.zip`.

**Publish:**
```bash
uip solution publish <outputDir>/<package>.zip \
  --tenant <TENANT_NAME> \
  --output json
```

Requires `uip login`.

## Quick Start (CREATE from scratch)

```bash
# 1. Copy the empty template
cp ./.claude/plugins/uipath/skills/uipath-api-workflow/assets/templates/api-workflow-template.json \
   ./MyApiProject/main.json

# 2. Edit main.json to add user activities after WorkflowStart inside the root sequence

# 3. Smoke test
uip api-workflow run ./MyApiProject/main.json --no-auth --output json

# 4. Iterate — fix, re-run, repeat until exit 0

# 5. Package
uip solution pack ./MySolution ./build --name MyApiSolution --version 1.0.0 --output json

# 6. Publish
uip login
uip solution publish ./build/MyApiSolution.zip --tenant MyTenant --output json
```

## Reference Navigation

| File | Use when |
|------|----------|
| [references/workflow-file-format.md](references/workflow-file-format.md) | Authoring or editing the JSON skeleton: top-level keys, `document.metadata.variables` schema, `input.schema`/`output.schema`, `WorkflowStart` |
| [references/task-types.md](references/task-types.md) | Adding/editing any single activity — exact JSON shape, required fields, export pattern, common mistakes, basic nesting hints per type |
| [references/control-flow-patterns.md](references/control-flow-patterns.md) | Combining activities into hierarchical structures — nested If, ForEach inside DoWhile, TryCatch around/inside loops, conditional Break, multi-way branching, key uniqueness rules |
| [references/connector-activity-discovery.md](references/connector-activity-discovery.md) | Authoring HTTP Request / Gmail / Outlook / GitHub / Slack / etc. activities via `uip api-workflow registry resolve` + `stub` — three-step flow, sample stub output, field-shape rules, multipart subsection, worked examples |
| [references/expressions-and-context.md](references/expressions-and-context.md) | Writing JS expressions, propagating outputs via `export.as`, accessing `$context` / `$input` / `$workflow`, JS_Invoke argument passing, strict-mode gotchas, key patterns |
| [references/cli-reference.md](references/cli-reference.md) | All `uip` commands — `api-workflow run`, `solution pack`, `solution publish`, `solution new`, `login` |
| [references/troubleshooting.md](references/troubleshooting.md) | Failed runs, structure/expression/loop/nesting/response/validation pitfalls, packaging errors, publish errors, debugging strategy |

## Templates

| File | Description |
|------|-------------|
| [assets/templates/api-workflow-template.json](assets/templates/api-workflow-template.json) | Empty valid workflow with `WorkflowStart` and empty schemas — drop activities into the root sequence (`Sequence_1.do` in this template) after `WorkflowStart` |
| [assets/templates/conditional-workflow-example.json](assets/templates/conditional-workflow-example.json) | If branching with TryCatch — input validation + classification + error fallback |
| [assets/templates/loop-aggregation-example.json](assets/templates/loop-aggregation-example.json) | DoWhile + ForEach + Assign accumulation — pure-compute aggregation pattern |
| [assets/templates/nested-control-flow-example.json](assets/templates/nested-control-flow-example.json) | Heavy nesting demo — TryCatch around DoWhile around If with conditional Break |
| [assets/templates/connector-call-example.json](assets/templates/connector-call-example.json) | **Http kind** — HTTP Request curated activity (`call: "UiPath.Http"`) for arbitrary REST calls. Generated by `registry stub` against the catfacts URL. Shows the canonical shape: `connectionId: "ImplicitConnection"`, `unifiedTypesCompatible: true`, `savedJitInputFieldId: "in_http-request"`, URL in `bodyParameters.url`. Verified end-to-end with `uip api-workflow run --no-auth`. |
| [assets/templates/vendor-curated-call-example.json](assets/templates/vendor-curated-call-example.json) | **IntSvc kind** — vendor curated activity (`call: "UiPath.IntSvc"`) using Outlook GetNewestEmail as exemplar. The `<REPLACE_WITH_VENDOR_CONNECTION_UUID>` placeholder is a sentinel — replace it with a pinged UUID from `uip is connections list/ping` **before** writing the workflow to disk. StudioWeb renders the literal placeholder as a broken connection if it survives. See rule 16 step 6. |
| [assets/templates/solution-connection-resource-template.json](assets/templates/solution-connection-resource-template.json) | **Solution connection resource** — declares a IntSvc kind connection as a Solution resource. Write to `Solution/resources/solution_folder/connection/<connector-key>/<connection-name>.json`. Required for Solutions-mode projects; without it the StudioWeb properties panel flags the activity as having an invalid connection. |

## Anti-patterns

- **Do NOT** modify the `WorkflowStart` activity — it is system-generated. Add user activities AFTER it inside the root sequence.
- **Do NOT** omit `export.as` on activities whose output later activities need. Without `export`, only `$output` (the most recent activity's result) is visible.
- **Do NOT** use YAML — the runtime parses JSON only.
- **Do NOT** invent a `uip api-workflow build`, `uip api-workflow validate`, or `uip api-workflow publish` command. Build/publish goes through `uip solution pack` / `uip solution publish`. Validation is `uip api-workflow run` (with or without `--no-auth` depending on the user's choice — see rule 20).
- **Do NOT** treat activity keys as cosmetic — they are the keys downstream activities use to read outputs (`$context.outputs.<ActivityKey>`).
- **Do NOT** use boolean `true` for Break — must be string `"true"`. Same for `then: "exit"` / `then: "end"` — these are control-flow keywords as strings.
- **Do NOT** read workflow inputs as `$input.<name>` from any non-first activity — use `$workflow.input.<name>`.
- **Do NOT** reuse activity keys across nested scopes. `If_1#Then` cannot appear in two Ifs even at different levels — increment to `If_2`. See [control-flow-patterns.md](references/control-flow-patterns.md#core-structural-rules).
- **Do NOT** reuse iteration variable names across nested loops. Inner `currentItem` shadows outer `currentItem`. Use distinct names per nesting level.
- **Do NOT** invent a `uiPathActivityTypeId` or hand-author the `metadata.configuration` blob for connector activities. Both must come from `uip api-workflow registry stub`. See [connector-activity-discovery.md](references/connector-activity-discovery.md).
- **Do NOT** use `call: "http"` (the deprecated simple form) when asked to fetch data from a public REST API (catfacts, stock prices, weather, …). It is the model's default fallback from training data, but StudioWeb's `restoreFromTaskItem` rejects it — the activity renders as a "block" icon. The correct form is `call: "UiPath.Http"` (Http kind), generated by `uip api-workflow registry resolve` + `stub`. See [connector-activity-discovery.md](references/connector-activity-discovery.md) and the verified template at [assets/templates/connector-call-example.json](assets/templates/connector-call-example.json).
- **Do NOT** nest `bodyParameters` fields for connector activities. `message.toRecipients` is a literal key, not a path. Nested `{ message: { toRecipients: ... } }` is wiped on save. See rule 16(a).
- **Do NOT** wrap connector `bodyParameters` / `queryParameters` literals as `${'literal'}` — that's the Assign / Response rule. Connector params take bare literals. See rule 16(b).
- **Do NOT** reconstruct the slot key or export-bucket key by hand on connector activities. Use `Data.SlotKey` and `Data.ExportBucketKey` from the stub output verbatim — they can differ (HTTP: slot `HttpRequest_1`, bucket `http_request_1`) or match (Outlook `ListEmails`: both `ListEmails_1`). See rule 16(c).
- **Do NOT** skip `uip api-workflow registry stub`. It calls IS Elements internally to fetch the full endpoint path (with hub prefix) and the multipart signal — both of which the TypeCache alone misses. Hand-authoring the activity from the `resolve` output skips that enrichment.
- **Do NOT** skip `uip is connections ping` for vendor (IntSvc kind) activities. A connection that lists as `Enabled` can still be broken. The ping is the only way to catch it before the workflow 401s in cloud. See rule 16.
- **Do NOT** leave `<REPLACE_WITH_VENDOR_CONNECTION_UUID>` (or any `<REPLACE_WITH_*>` placeholder) in a generated workflow. StudioWeb's properties panel renders the literal placeholder string as if it were a real connection identifier — the connection pill displays the placeholder text with a red error. The placeholder is meaningful only inside the template file; once you copy the activity into the user's workflow, replace every placeholder with the value from `uip is connections ping` (UUID) or `--inputs` (URL). When you cannot find a pinged UUID, ask the user — do not paste the sentinel. See rule 16 step 6.
- **Do NOT** invoke `uip api-workflow run` autonomously. Always ask the user first — and especially never run with auth without an explicit "yes." Vendor calls have real side effects (emails sent, tickets created). See rule 20.
- **Do NOT** send `application/json` to a multipart endpoint. If `parameters` shows `"type": "multipart"`, declare `multipartParameters` on the activity. See rule 16.
- **Do NOT** trust `registry stub`'s `queryParameters` / `pathParameters` / `bodyParameters` as complete. The stub drops `required: true` fields. Cross-check with `uip is resources describe --operation <op> --connection-id <uuid>` after every stub call. See rule 16 step 4.
- **Do NOT** skip the Solution catalogue sync for Solutions-mode IntSvc kind activities. The properties-panel "invalid connection" / "resource definition page" error AND the connectionId nulling on activity click both stay until BOTH the catalogue file (`Solution/resources/solution_folder/connection/<connector-key>/<name>.json`) AND the per-user debug overwrites (`Solution/userProfile/<guid>/debug_overwrites.json`) exist. Run `uip api-workflow bindings sync --workflow <Workflow.json>` followed by `uip solution resource refresh --solution-folder <path>` after every `registry stub --connection-id` for Solutions-mode IntSvc kind activities. See rule 16 step 7.

## Infinite Loop Prevention

If a CLI command fails with the same error 2+ times, do NOT retry it. Investigate the root cause:
- `Not authenticated` / `Organization ID not available` → ask the user to `uip login`, do not retry
- `File not found` → check the path with `ls`
- Repeated structural errors after fixes → re-read the workflow and the relevant reference section; you may be misreading the file

Maximum 3 attempts for any single operation. After 3 failures, stop and report what was tried.
