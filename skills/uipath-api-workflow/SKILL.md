---
name: uipath-api-workflow
description: "UiPath API Workflow assistant — author, run, package, publish JSON workflows executed by `uip api-workflow run`. Covers logical/hierarchical structure (Sequence, Assign, JavaScript, If with #Wrapper/#Then/#Else, ForEach, DoWhile, Break, TryCatch, Wait, Response — including nested patterns) AND HTTP / Integration Service connector activities (Gmail, Outlook, GitHub, Slack, etc.) authored via `uip api-workflow registry resolve` + `stub`. Triggers on prompts about UiPath API workflows, project type \"Api\", JSON workflow files containing `document.dsl`/`do[]`, any of those activity types, or fetching data from a public/vendor API. Uses `uip api-workflow run` for local execution and `uip solution pack`/`publish` for deployment. For .flow Maestro→uipath-maestro-flow. For .xaml/coded RPA→uipath-rpa. For coded agents→uipath-agents. For Coded Apps→uipath-coded-apps."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath API Workflow Assistant

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

## Core Principles

1. **Know before you write.** Read the existing workflow file before editing. Read an example template before creating from scratch.
2. **Start minimal, iterate to correct.** Add one activity at a time. Run with `--no-auth --output json` after each addition. Fix what breaks. Repeat.
3. **Validate before running.** `uip api-workflow validate` is the offline static pre-flight (autonomous); `uip api-workflow run` is the runtime validator that catches what static analysis can't (live HTTP, expression evaluation, connection state) and needs user consent. See rules 20–21.
4. **Fix errors by category.** Triage: Structure > Expression > Activity Config > Logic. Higher-category fixes often resolve lower-category errors automatically.

## Critical Rules

> **Rule 0 — Escalate big design forks before you build (highest priority, read first).** When the happy path doesn't work out of the box and the resolution is a judgment call the user would reasonably want to own, STOP and ask before committing to a branch. Present the concrete options with their trade-offs and a recommended default; proceed only on the user's answer. Triggers (non-exhaustive): no valid connection for a required activity (rule 16); no curated activity exists and the choice is generic activity vs. raw Http kind vs. a different connector; the requested operation isn't exposed by any resolvable activity and the fallback is a hand-built HTTP call against an undocumented endpoint; an input the prompt assumed is missing and the alternatives are placeholder, hardcoded value, or new workflow input; the prompt is satisfiable by structurally different workflows (single connector call vs. ForEach over a list). This does NOT cover mechanical choices with an obvious answer (variable names, activity key suffixes, export-pattern selection) — decide those and move on. Reserve escalation for forks where guessing wrong wastes work or ships something the user didn't intend.
>
> **Ask the fork BEFORE branch-specific research, not after.** Once you spot a structural fork, do only the shared work needed to surface the options (the cheap `resolve` that proves no curated activity exists, the `connections list`/`ping` that proves no connection works), then ask. Do NOT pre-research every branch — stubbing each candidate activity, describing resources, drafting alternative workflow shapes — so the user can "pick from finished work." The user picks one branch; deep work on the others is thrown away. Sequence: detect fork → minimal shared discovery → ask → then research and build only the chosen branch.

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
16. **Connector activities (HTTP + Integration Service) come from `uip api-workflow registry resolve` + `stub` — never hand-author or guess.** The stub computes `metadata.configuration`, the kind (`UiPath.Http` vs `UiPath.IntSvc`), the endpoint (with hub prefix), `SlotKey`, and `ExportBucketKey` (which can differ — HTTP slot `HttpRequest_1` vs bucket `http_request_1`). Use all of them verbatim; NEVER invent a `uiPathActivityTypeId`, hand-author `metadata.configuration`, or reconstruct a key from `objectName`. Non-negotiables (full step-by-step, field-shape rules, multipart, and worked examples in [references/connector-activity-discovery.md](references/connector-activity-discovery.md)):
    - **A keyword `resolve` miss is NOT proof no curated activity exists — verify connector-first before giving up.** `resolve` AND-matches every token, so a marketing phrase + guessed verb over-narrows (the product "UiPath Data Fabric" carries `connectorKey: uipath-uipath-dataservice` and activity names like "Create Entity Record" — `resolve "data fabric insert"` returns 0; fewer/truer tokens, not more). Before concluding none exists or falling back to a hand-built HTTP call (a Rule 0 fork): map the product/vendor → connector key with `uip is connectors list --filter "<product>"`, then enumerate with `uip is activities list <connector-key>`. Do NOT hardcode/guess the key — look it up. See the reference's Step 1 recovery.
    - **IntSvc/vendor activities require a *pinged* connection.** `uip is connections ping <uuid>` must succeed before authoring — listing-state ≠ runtime-state; an `Enabled` connection can still 401 in cloud. On failure, try the unfiltered `uip is connections list` fallback and re-ping a different `Id` for that `ConnectorKey`.
    - **No connection pings cleanly → STOP and ask the user — do not decide alone.** Offer: **(a)** continue with a placeholder (stub without `--connection-id`, leaving the `<REPLACE_WITH_VENDOR_CONNECTION_UUID>` sentinel — workflow is structurally complete but 401s until replaced; only with explicit user consent), or **(b)** stop and wait for the user to create/fix the connection, then re-ping. Never silently emit the placeholder, never silently abort. (Instance of Rule 0 — escalate design forks.)
    - **NEVER ship a `<REPLACE_WITH_*>` placeholder** in `with.connectionId` / `connectionResourceId` / Http `bodyParameters.url`. StudioWeb renders it as a broken connection and the workflow 401s. The placeholder is a sentinel for "re-stub with the real value," not a fill-in-later field.
    - **After every stub, cross-check required fields** — the stub drops `required: true` request fields (e.g. Outlook `getNewestEmail` needs `parentFolderId`). Confirm via `uip is resources describe ... --operation <op>` or the stub's own `metadata.configuration` inputFields; re-stub with `--inputs` if missing.
    - **Connector params use flat dotted keys and BARE literals.** `"message.toRecipients": "..."`, not nested objects; plain `"x@y.com"`, not `"${'x@y.com'}"` — rule 5's wrap is **inverted** here (`${'...'}` clears the field on save). Real references (`${$context...}`) stay wrapped.
    - **NEVER use Http kind with a vendor connection UUID** (401 "Invalid Element token"). IntSvc output is wrapped: read `$context.outputs.<ExportBucketKey>.content.<field>`.
    - **(Solutions-mode + IntSvc only)** sync the connection into the catalogue: `uip api-workflow bindings sync --workflow <Workflow.json>` then `uip solution resource refresh --solution-folder <path>`. Skip for Http kind, non-connector activities, and standalone (no `Solution/`) projects.
17. **Pass input as a JSON string.** `--input-arguments '{"key":"value"}'`. Invalid JSON exits 1.
18. **Always `--output json`** when parsing CLI output programmatically. Success → `{ "Result": "Success", "Code": "WorkflowRun", "Data": {...} }`. Failure → `{ "Result": "Failure", "Message": "...", "Instructions": "..." }` with exit 1.
19. **Build & publish goes through the solution packager.** API workflows pack via `uip solution pack <solutionDir> <outputDir>` and publish via `uip solution publish <package.zip>`. There is no `uip api-workflow build` or `uip api-workflow publish` command. Project type must be `"Api"` in the solution `.uipx`.
20. **`uip api-workflow validate <Workflow.json>` is the autonomous closure step for every authoring or edit cycle.** Run it as the LAST command before asking the user anything about runtime. It's offline (no auth, no network, no side effects): JSON Schema + semantic checks on the static file. Output codes:
    - `Result: "Success"`, `Code: "ApiwfValidate"`, `Data.Status: "Valid"` (exit 0) — possibly with `Data.Warnings`. Proceed to rule 21 (ask the user whether to run).
    - `Result: "Failure"` (exit 1) — do NOT bother the user. Read `Instructions`, locate the offending activity by its JSON path (e.g. `/do/0/Sequence_1/do/2/Mystery_1/metadata/activityType`), edit `Workflow.json` to fix it, then re-validate. Loop until pass.

    **Reading the error list.** AJV schema errors from `oneOf` branches produce duplicate "Missing required property" noise (each unmatched variant lists all its required fields). Focus on the **semantic-tail errors** — the ones with prose messages like `Unknown activityType 'X'`, `must contain a 'do' with inner 'switch'`, `is missing 'metadata.configuration'`, `Variable must have a non-empty 'type'`. Those uniquely identify the root cause. Fix one root cause, re-validate, repeat — don't chase the schema-level fanout one by one.

    **What validate catches:** malformed JSON; unknown `activityType` values (see VALID_ACTIVITY_TYPES list in the validate source); per-activity required keys (If → `do` + inner `switch`, Sequence → `do`, Assign → `set`, ForEach → `for` + `do`, DoWhile → `for` + `doWhile`, Connector → `call` + `metadata.configuration` + `essentialConfiguration`, Response → `response`, etc.); missing `metadata.activityType`/`displayName` (warnings); bad `evaluate.language`/`evaluate.mode`; duplicate or empty-named workflow variables; empty task lists. **What it does NOT catch:** wrong `selectedResourceId`, broken connector connection IDs, runtime expression errors (`ReferenceError: x is not defined`), unwrapped string literals (rule 5), multi-key `Assign.set` (rule 6) — those still need runtime validation via `uip api-workflow run` once the user consents.

21. **Never run `uip api-workflow run` without an explicit user "yes."** Validation (rule 20) is autonomous; *running* is not. Once validate passes, ask the user: (a) run now or skip, (b) if running, with `--no-auth` (fast, structure-only — IntSvc kind vendor calls fail) or with auth (real Integration Service calls — vendor side effects WILL happen: emails sent, tickets created, files uploaded). Suggest a default based on workflow content (`--no-auth` for control-flow-only + Http kind `ImplicitConnection`; with-auth for any IntSvc kind vendor activity), but wait for the user's answer. Never invoke `uip api-workflow run` with auth on speculation — once a vendor call goes out, it can't be unsent.

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
| Call an arbitrary REST API (catfacts, stock prices, weather, any public/internal endpoint) | **Unified HTTP Request** (`call: "UiPath.Http"`, Http kind) | `connectionId: "ImplicitConnection"`. NEVER `call: "http"` (block icon). Via rule 16's flow. |
| Call a vendor service via its UiPath connection (Gmail, Outlook, GitHub, Slack, …) | **Vendor curated activity** (`call: "UiPath.IntSvc"`, IntSvc kind) | Needs a pinged connection UUID. Via rule 16's flow. |
| CRUD a connector object that has no curated activity | **Generic activity** (`ActivityType: "Generic"` in resolve output — "List Records", "Get Record", …; IntSvc kind) | Add `--object-name <object>` (from `uip is resources list`) to the stub. Prefer a curated activity when one exists. Via rule 16's flow. |

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

### Phase 3: Validate (static) then Run (with consent)

Validate autonomously (rule 20), fixing + re-validating until `Data.Status: "Valid"`:

```bash
uip api-workflow validate ./my-workflow.json --output json
```

Once green, **ask before running** (rule 21) — pick the mode from workflow content:

| Mode | Flag | What happens | Use when |
|--|--|--|--|
| No-auth | `--no-auth` | Skips token loading. Structure / expressions / control flow validated. IntSvc vendor calls fail with a missing-token error. | Control-flow-only, OR Http kind with `connectionId: "ImplicitConnection"`. Default for most iterations. |
| With auth | (none) | Uses the `uip login` token. Real Integration Service calls — vendor side effects happen. | An IntSvc vendor activity AND the user confirmed the real call is OK (email sent, ticket created, file uploaded). |

State the consequence in the question (e.g. "running with auth WILL send a real email to `<recipient>` — (1) skip, (2) `--no-auth`, (3) run with auth?"), wait for the reply, then run `uip api-workflow run ./my-workflow.json [--no-auth] --output json`. If the user skips, give them the exact command and stop.

Fix run failures in category order — **Structure > Expression > Activity Config > Logic** (higher categories often resolve lower ones). Full pitfall catalog: [references/troubleshooting.md](references/troubleshooting.md).

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

# 3. Validate (offline, autonomous — fix + re-validate until Status: Valid)
uip api-workflow validate ./MyApiProject/main.json --output json

# 4. Ask the user, then run (only on user "yes")
uip api-workflow run ./MyApiProject/main.json --no-auth --output json

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
| [references/http-retry-config.md](references/http-retry-config.md) | Adding workflow-level HTTP retry policy (`httpRetryConfig`) — scope (GET-only), constant/linear/exponential backoff formulas, defaults, `Retry-After` handling, anti-patterns |
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
| [assets/templates/vendor-curated-call-example.json](assets/templates/vendor-curated-call-example.json) | **IntSvc kind** — vendor curated activity (`call: "UiPath.IntSvc"`) using Outlook GetNewestEmail as exemplar. The `<REPLACE_WITH_VENDOR_CONNECTION_UUID>` placeholder is a sentinel — replace it with a pinged UUID from `uip is connections list/ping` **before** writing the workflow to disk. StudioWeb renders the literal placeholder as a broken connection if it survives. See rule 16. |
| [assets/templates/solution-connection-resource-template.json](assets/templates/solution-connection-resource-template.json) | **Solution connection resource** — declares a IntSvc kind connection as a Solution resource. Write to `Solution/resources/solution_folder/connection/<connector-key>/<connection-name>.json`. Required for Solutions-mode projects; without it the StudioWeb properties panel flags the activity as having an invalid connection. |

## Anti-patterns

The mistakes an agent makes most often (each maps to a Critical Rule above — see it for the full reasoning):

- **Do NOT** use `call: "http"` for a REST call — it's the training-data default, but StudioWeb rejects it (renders as a "block" icon). Use `call: "UiPath.Http"` from `registry stub`. See rule 16.
- **Do NOT** wrap connector `bodyParameters` / `queryParameters` literals as `${'literal'}` — rule 5's wrap is **inverted** for connectors; bare literals only, or the field clears on save. See rule 16.
- **Do NOT** ship a `<REPLACE_WITH_*>` placeholder in a workflow — StudioWeb renders it as a broken connection and it 401s. No pinged UUID → ask the user. See rule 16.
- **Do NOT** read workflow inputs as `$input.<name>` from a non-first activity — use `$workflow.input.<name>`. See rule 13.
- **Do NOT** invoke `uip api-workflow run` autonomously, and never with auth without an explicit "yes" — vendor calls have irreversible side effects (emails sent, tickets created). See rules 20–21.

## Infinite Loop Prevention

If a CLI command fails with the same error 2+ times, do NOT retry it. Investigate the root cause:
- `Not authenticated` / `Organization ID not available` → ask the user to `uip login`, do not retry
- `File not found` → check the path with `ls`
- Repeated structural errors after fixes → re-read the workflow and the relevant reference section; you may be misreading the file

Maximum 3 attempts for any single operation. After 3 failures, stop and report what was tried.
