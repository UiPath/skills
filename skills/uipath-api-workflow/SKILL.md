---
name: uipath-api-workflow
description: "UiPath API Workflow assistant — author, run, package, publish JSON workflows executed by `uip api-workflow run`. Focused on logical/hierarchical structure: Sequence, Assign, JavaScript, If (with #Wrapper/#Then/#Else), ForEach, DoWhile, Break, TryCatch, Wait, Response — including nested patterns. Triggers on prompts about UiPath API workflows, project type \"Api\", JSON workflow files containing `document.dsl`/`do[]`, or any of those activity types. Uses `uip api-workflow run` for local execution and `uip solution pack`/`publish` for deployment. HTTP/Connector activities are out of scope (require StudioWeb editor metadata). For .flow Maestro→uipath-maestro-flow. For .xaml/coded RPA→uipath-rpa. For coded agents→uipath-agents. For Coded Apps→uipath-coded-apps."
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
- User asks about **activity types** (Sequence, Assign, JavaScript, If, ForEach, DoWhile, Break, TryCatch, Wait, Response)
- User asks about **nested control flow** — If inside ForEach, TryCatch around a loop, conditional Break, multi-way branching, etc.
- User asks about **JavaScript expressions, `$context`, `$input`, `$workflow`, `WorkflowStart`, or the `export.as` pattern**
- User asks how to **debug** a failing API workflow run

Do NOT use for: `.flow` Maestro flows (→ `uipath-maestro-flow`), `.xaml` / coded RPA (→ `uipath-rpa`), coded agents (→ `uipath-agents`), Coded Web Apps (→ `uipath-coded-apps`).

**Out of scope (for now):** HTTP Request and Integration Service Connector activities. They require StudioWeb-side editor metadata (`metadata.configuration` blob plus connection plumbing) that the CLI cannot generate cleanly. If the user needs outbound HTTP, recommend authoring that activity in StudioWeb directly and merging it in. The `uip case registry` commands (case-tool) can resolve activity-type GUIDs and connector schemas if a future iteration of this skill grows that capability.

## Core Principles

1. **Know before you write.** Read the existing workflow file before editing. Read an example template before creating from scratch.
2. **Start minimal, iterate to correct.** Add one activity at a time. Run with `--no-auth --output json` after each addition. Fix what breaks. Repeat.
3. **Validate by running.** There is no `uip api-workflow validate` command — local execution is the only validator. The executor fails fast on malformed JSON, unknown activity types, or missing required fields.
4. **Fix errors by category.** Triage: Structure > Expression > Activity Config > Logic. Higher-category fixes often resolve lower-category errors automatically.

## Critical Rules

1. **Workflow file is JSON, not YAML.** Top-level keys: `document` (with `dsl: "1.0.0"`), `evaluate` (`language: "javascript"`, `mode: "strict"`), `do` (root `Sequence_1` containing `WorkflowStart` + user activities). See [references/workflow-file-format.md](references/workflow-file-format.md).
2. **`WorkflowStart` is always the first activity** inside `Sequence_1.do`. It hydrates variable defaults into `$context.variables` and forwards inputs to `$input`. Never remove, rename, or modify it. `isTransparent: true` (only `WorkflowStart` uses `true`).
3. **Every activity is a single-key object** wrapped in the `do` array: `{ "<ActivityKey>": { ...activity body... } }`. Activity keys must be **globally unique** across the whole workflow — including `#Wrapper`, `#Then`, `#Else`, `#Body` suffixes.
4. **Every activity should `export` its output** to propagate state. Two patterns:
   - **Variables (Assign only):** `{ ...$context, variables: { ...$context.variables, ...$output } }`
   - **Outputs (everything else):** `{ ...$context, outputs: { ...$context?.outputs, "<ActivityKey>": $output } }`
   See [references/expressions-and-context.md](references/expressions-and-context.md).
5. **String literals in `Assign.set` MUST be wrapped as `"${'literal'}"`** — a JS string inside an expression. Plain `"literal"` runs fine under `uip api-workflow run`, but **StudioWeb's designer normalizes unwrapped values to `"${literal}"` on save** (treating them as expressions you typed into the property panel). At runtime the bare identifier `literal` has no binding → `ReferenceError: literal is not defined`. Use single quotes inside the expression to avoid JSON escaping: `"set": { "tier": "${'PLATINUM'}" }`. Numbers, booleans, and references like `${$context.variables.X}` need no extra wrapping. (Response payloads have a related but distinct constraint — see rule 15.) See [references/troubleshooting.md](references/troubleshooting.md#studioweb-roundtrip-pitfalls).
6. **Each `Assign` activity MUST set exactly ONE variable.** `Assign.set` is a single-key object, NOT a multi-variable update. **StudioWeb's designer collapses multi-key `set` blocks to one key on save**, silently dropping the others — the runtime then only updates the surviving key. To update N variables, use N separate Assign activities placed sequentially in the same `do` array. Example: instead of `"set": { "sum": "${$context.variables.sum + 1}", "count": "${$context.variables.count + 1}" }` (loses `count` after StudioWeb save), write two Assigns — `Assign_Sum` with `"set": { "sum": "${...}" }` and `Assign_Count` with `"set": { "count": "${...}" }`. Each runs in order; each Assign's variables export merges its single key into `$context.variables`.
7. **If activity requires the wrapper pattern.** `If_N#Wrapper` contains `If_N` (switch), `If_N#Then`, `If_N#Else`. Both `#Then` and `#Else` MUST end with `"then": "exit"` to prevent fall-through. Conditions in `when` MUST be wrapped in `${...}`. For deeply-nested If patterns and multi-way branching, see [references/control-flow-patterns.md](references/control-flow-patterns.md).
8. **Loops (ForEach, DoWhile) require a `#Body` element** inside `do`. ForEach body uses index-aware accumulation (resets on iteration 0); DoWhile body uses simple accumulation. Loop variables (`each`, `at`) are plain strings, NOT expressions.
9. **DoWhile `for.in` is always `"${ [1] }"`.** The `doWhile` condition controls repetition. The body MUST update the condition variable, otherwise the loop runs forever.
10. **Nested loops MUST use distinct iterator/index names.** Outer `for.each: "outerItem"`, inner `for.each: "innerItem"`. Reusing `currentItem` shadows the outer.
11. **Loop iterators and catch error variables are prefixed with `$` in expressions.** Declare `for.each: "currentItem"` (plain string, no `$`); reference it everywhere else (in `when` conditions, in script bodies, in `set` expressions, in body export patterns) as `$currentItem` — the `$` is a literal character in the global identifier name. Same for `for.at` (`$currentItemIndex`) and `catch.as` (`$error`). Empirically verified: the executor calls `setVariables({"$currentItem": item, ...})` — `currentItem` (no `$`) is **not bound** as a global. Forgetting the `$` produces `<name> is not defined`.
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
16. **Pass input as a JSON string.** `--input-arguments '{"key":"value"}'`. Invalid JSON exits 1.
17. **Always `--output json`** when parsing CLI output programmatically. Success → `{ "Result": "Success", "Code": "WorkflowRun", "Data": {...} }`. Failure → `{ "Result": "Failure", "Message": "...", "Instructions": "..." }` with exit 1.
18. **Build & publish goes through the solution packager.** API workflows pack via `uip solution pack <solutionDir> <outputDir>` and publish via `uip solution publish <package.zip>`. There is no `uip api-workflow build` or `uip api-workflow publish` command. Project type must be `"Api"` in the solution `.uipx`.

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

Before generating, determine:
1. Which activities are needed and in what order
2. What unique keys to assign (check existing keys to avoid collision)
3. What variables to declare (in `document.metadata.variables.schema.document.properties`)
4. What inputs/outputs to declare (in `input.schema` / `output.schema`)

### Phase 2: Generate or Edit

For each activity, read its reference section in [references/task-types.md](references/task-types.md), copy the minimal JSON, fill in values.

**For CREATE:** copy from a template, then add user activities AFTER `WorkflowStart` inside `Sequence_1.do`.

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

After EVERY edit, run the workflow:

```bash
uip api-workflow run ./my-workflow.json --no-auth --output json
```

`--no-auth` skips token loading. The activities this skill covers (Sequence, Assign, JS, If, ForEach, DoWhile, Break, TryCatch, Wait, Response) all run cleanly under `--no-auth` — no login needed.

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

# 2. Edit main.json to add user activities after WorkflowStart inside Sequence_1.do

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
| [references/expressions-and-context.md](references/expressions-and-context.md) | Writing JS expressions, propagating outputs via `export.as`, accessing `$context` / `$input` / `$workflow`, JS_Invoke argument passing, strict-mode gotchas, key patterns |
| [references/cli-reference.md](references/cli-reference.md) | All `uip` commands — `api-workflow run`, `solution pack`, `solution publish`, `solution new`, `login` |
| [references/troubleshooting.md](references/troubleshooting.md) | Failed runs, structure/expression/loop/nesting/response/validation pitfalls, packaging errors, publish errors, debugging strategy |

## Templates

| File | Description |
|------|-------------|
| [assets/templates/api-workflow-template.json](assets/templates/api-workflow-template.json) | Empty valid workflow with `WorkflowStart` and empty schemas — drop activities into `Sequence_1.do` after `WorkflowStart` |
| [assets/templates/conditional-workflow-example.json](assets/templates/conditional-workflow-example.json) | If branching with TryCatch — input validation + classification + error fallback |
| [assets/templates/loop-aggregation-example.json](assets/templates/loop-aggregation-example.json) | DoWhile + ForEach + Assign accumulation — pure-compute aggregation pattern |
| [assets/templates/nested-control-flow-example.json](assets/templates/nested-control-flow-example.json) | Heavy nesting demo — TryCatch around DoWhile around If with conditional Break |

## Anti-patterns

- **Do NOT** modify the `WorkflowStart` activity — it is system-generated. Add user activities AFTER it inside `Sequence_1.do`.
- **Do NOT** omit `export.as` on activities whose output later activities need. Without `export`, only `$output` (the most recent activity's result) is visible.
- **Do NOT** use YAML — the runtime parses JSON only.
- **Do NOT** invent a `uip api-workflow build`, `uip api-workflow validate`, or `uip api-workflow publish` command. Build/publish goes through `uip solution pack` / `uip solution publish`. Validation is `uip api-workflow run --no-auth`.
- **Do NOT** treat activity keys as cosmetic — they are the keys downstream activities use to read outputs (`$context.outputs.<ActivityKey>`).
- **Do NOT** use boolean `true` for Break — must be string `"true"`. Same for `then: "exit"` / `then: "end"` — these are control-flow keywords as strings.
- **Do NOT** read workflow inputs as `$input.<name>` from any non-first activity — use `$workflow.input.<name>`.
- **Do NOT** reuse activity keys across nested scopes. `If_1#Then` cannot appear in two Ifs even at different levels — increment to `If_2`. See [control-flow-patterns.md](references/control-flow-patterns.md#core-structural-rules).
- **Do NOT** reuse iteration variable names across nested loops. Inner `currentItem` shadows outer `currentItem`. Use distinct names per nesting level.
- **Do NOT** add HTTP / Connector activities — they're out of scope for this skill (need StudioWeb editor metadata). For workflows that need outbound calls, point the user to author the HTTP card in StudioWeb directly.

## Infinite Loop Prevention

If a CLI command fails with the same error 2+ times, do NOT retry it. Investigate the root cause:
- `Not authenticated` / `Organization ID not available` → ask the user to `uip login`, do not retry
- `File not found` → check the path with `ls`
- Repeated structural errors after fixes → re-read the workflow and the relevant reference section; you may be misreading the file

Maximum 3 attempts for any single operation. After 3 failures, stop and report what was tried.
