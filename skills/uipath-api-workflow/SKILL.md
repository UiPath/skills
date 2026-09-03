---
name: uipath-api-workflow
description: "UiPath API Workflow assistant — author, run, validate, package, publish, deploy, and troubleshoot JSON workflows for `uip api-workflow`. Load for ANY create/edit of a `Workflow.json` / API workflow project; with `evals/` present, tests come first (TDD). Covers Sequence, Assign, JavaScript, If (#Wrapper/#Then/#Else), ForEach, DoWhile, Break, TryCatch, Wait, Response, nested; files as JobAttachment refs via File to Base64 / Base64 to File (`$helpers.file.*`, `serializeData()`, `--input-file`/`--output-dir`); HTTP / IS connector activities via `uip api-workflow registry`. Operate: run, IS connections, pack/publish/deploy. Test/eval: `evals/<scope>/eval-sets/` datasets (exact-match, Evaluations panel); loop until green. Triggers on API workflows, project type \"Api\", JSON with `document.dsl`/`do[]`, those activity types, or file/base64 handling. Agent evals (`evals/eval-sets/`, no scope) & coded agents→uipath-agents. Flow & its evals→uipath-maestro-flow. .xaml/coded RPA→uipath-rpa. Coded Apps→uipath-coded-apps."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath API Workflow Assistant

<!--skill-flavor:surface-summary:start-->
Build, run, and publish UiPath API Workflows — JSON files conforming to the CNCF Serverless Workflow DSL 1.0.0 with UiPath activity-type extensions. Executed by `@uipath/api-workflow-executor` via `uip api-workflow run`. Packaged as `Type: "Api"` projects via `uip solution pack`.
<!--skill-flavor:surface-summary:end-->
<!--skill-flavor:host-command-contract:start-->
<!--skill-flavor:host-command-contract:end-->

> **TDD gate — read this first (rule 22).** On ANY request to create or edit a workflow, Phase 0 first checks whether the project has an `evals/` folder — it lives **inside the project directory, next to `Workflow.json`** (`<project>/evals/`), not at the workspace or solution root, so list the project directory itself. **No `evals/` folder → the Evaluations feature is not enabled for this project: skip everything about tests and loop mode and author normally.** `evals/` present → **end your turn** with two questions — **(1) tests:** the eval set has rows → "should anything change, or use as-is?" / it is empty → "want me to add some?"; **(2) loop mode:** "run the tests and re-try until every case passes, or author once?" — and NOTHING is authored until the user answers. Tests come **first**: once answered, write or update the eval set, then author the workflow to make it pass. If you are about to write `Workflow.json` in a project with `evals/` and the user has not answered these two questions in this conversation, stop. Later change requests that alter behavior can break the tests — ask before editing whether to update them (rule 22, [references/testing-and-evals.md](references/testing-and-evals.md) §3). Only a prompt that explicitly says not to ask skips the gate when `evals/` exists — and that skips the questions, not the run consent (rule 21): run rows only when the request itself asks for a run.

## When to Use This Skill

- User wants to **create or edit** an API workflow JSON file
<!--skill-flavor:surface-lifecycle-scope:start-->
- User wants to **run** an API workflow locally with `uip api-workflow run`
- User wants to **package** an API workflow project into `.nupkg` / solution `.zip`
- User wants to **publish** an API workflow to UiPath Cloud / Orchestrator
<!--skill-flavor:surface-lifecycle-scope:end-->
- User asks about **activity types** (Sequence, Assign, JavaScript, If, ForEach, DoWhile, Break, TryCatch, Wait, Response, File to Base64, Base64 to File, HTTP Request, Connector)
- User wants to **handle a file** in an API workflow — take a file input, send a file as base64 to an API, turn a base64 payload back into a file, or asks about `JobAttachment`, `$helpers.file`, `serializeData()`, `--input-file` / `--output-dir`. See [references/files-and-base64.md](references/files-and-base64.md)
- User asks about **nested control flow** — If inside ForEach, TryCatch around a loop, conditional Break, multi-way branching, etc.
- User asks for an **Integration Service connector activity** (Gmail Send Email, Outlook Get Newest Email, GitHub Search Issues, Slack Send Message, etc.) — follow the discovery flow in [references/connector-activity-discovery.md](references/connector-activity-discovery.md)
- User asks for a **generic HTTP Request** that needs to render in StudioWeb's designer — same discovery flow
- User asks about **JavaScript expressions, `$context`, `$input`, `$workflow`, `WorkflowStart`, or the `export.as` pattern**
<!--skill-flavor:surface-operations-scope:start-->
- User asks how to **debug** a failing API workflow run — the local `validate` → `run --no-auth` loop, or a **post-publish cloud run** (job logs/traces). See [references/operating-published-workflows.md](references/operating-published-workflows.md)
- User wants to **operate** a published workflow — invoke it (HTTP/schedule/Integration Service event trigger), start/list/stop its Orchestrator jobs, or **manage the Integration Service connections** it uses (`uip is connections list`/`ping`/`edit`). See [references/operating-published-workflows.md](references/operating-published-workflows.md)
<!--skill-flavor:surface-operations-scope:end-->
- User wants to **test / evaluate** a workflow — author `(inputs, expectedOutput)` cases in the project's `evals/` folder (the dataset Studio Web's **Evaluations** panel reads), run them, score them by the project's evaluator, or **"loop until the tests pass"**. Follow [references/testing-and-evals.md](references/testing-and-evals.md). An `evals/` folder alone is not the signal — it is an API-workflow one only when it sits next to `Workflow.json` and uses the `evals/<scope>/eval-sets/` layout; low-code agents use `evals/eval-sets/` (no scope) → `uipath-agents`, Flow evals → `uipath-maestro-flow`
- **Any authoring request** (create or edit) — Phase 0 discovery checks for an `evals/` folder; when it exists, the two test questions (change / add tests? loop mode?) are asked up front — the turn ends there — whether or not the user mentioned testing (rule 22). No `evals/` folder → the feature is off, author normally. See Phase 0 and [references/testing-and-evals.md](references/testing-and-evals.md)

Do NOT use for: `.flow` Maestro flows (→ `uipath-maestro-flow`), `.xaml` / coded RPA (→ `uipath-rpa`), coded agents (→ `uipath-agents`), Coded Web Apps (→ `uipath-coded-apps`).

## Core Principles

0. **Tests first — when the project has `evals/`, and only after asking.** Discover `<project>/evals/` (next to `Workflow.json`). Absent → the Evaluations feature is off for this project: author normally, no test or loop-mode questions. Present → ask the two rule-22 questions, end the turn; once answered: declare `output.schema`, eval set first, workflow second, then run the rows **only in loop mode** (that "yes" is the rule-21 consent; "author once" means hand over without running). Behavior changes later on re-open the question — the tests may need updating.
1. **Know before you write.** Read the existing workflow file before editing. Read an example template before creating from scratch.
<!--skill-flavor:runtime-validation-contract:start-->
2. **Start minimal, iterate to correct.** Add one activity at a time. Run with `--no-auth --output json` after each addition. Fix what breaks. Repeat.
3. **Validate before running.** `uip api-workflow validate` is the offline static pre-flight (autonomous); `uip api-workflow run` is the runtime validator that catches what static analysis can't (live HTTP, expression evaluation, connection state) and needs user consent. See rules 20–21.
<!--skill-flavor:runtime-validation-contract:end-->
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
<!--skill-flavor:designer-literal-runtime-comparison:start-->
5. **String literals in `Assign.set` / `Response` / If `when` MUST be wrapped as `"${'literal'}"`** — a JS string inside an expression. Plain `"literal"` runs fine under `uip api-workflow run`, but **StudioWeb's designer normalizes unwrapped values to `"${literal}"` on save** (treating them as expressions you typed into the property panel). At runtime the bare identifier `literal` has no binding → `ReferenceError: literal is not defined`. Use single quotes inside the expression to avoid JSON escaping: `"set": { "tier": "${'PLATINUM'}" }`. Numbers, booleans, and references like `${$context.variables.X}` need no extra wrapping. (Response payloads have a related but distinct constraint — see rule 15.) **Scope:** this rule applies to Assign / Response / If / variable contexts only. **It does NOT apply to connector `bodyParameters` / `queryParameters` / `pathParameters` — those take BARE literals; `${'...'}` there is read as an expression and the field is cleared on save.** See rule 16 and [references/connector-activity-discovery.md#field-shape-rules-flat-keys-bare-literals-renamed-export-hub-prefix](references/connector-activity-discovery.md#field-shape-rules-flat-keys-bare-literals-renamed-export-hub-prefix). See [references/troubleshooting.md](references/troubleshooting.md#studioweb-roundtrip-pitfalls).
<!--skill-flavor:designer-literal-runtime-comparison:end-->
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
    - **Object-valued responses MUST use the single-expression form**, NOT the JSON-object-with-`${}`-fields form. StudioWeb's designer corrupts the latter on save.
      - ✗ Wrong (CLI runs but StudioWeb corrupts): `"response": { "tier": "${$context.variables.tier}", "count": "${$context.variables.count}" }`
      - ✓ Correct: `"response": "${{ tier: $context.variables.tier, count: $context.variables.count }}"`
      Inside the outer `${{ ... }}` you are already in expression scope, so reference variables/outputs directly without an inner `${...}` wrapper. JS object literal keys can be unquoted identifiers (`tier:`, `count:`); literal string values use single quotes (`status: 'ok'`); numbers/booleans/references are bare. The designer leaves an already-wrapped single expression alone; the JSON-object form gets flattened to a stringified expression where inner `${...}` substitutions are inside JS double-quoted strings (which don't interpolate), turning each field into the literal text of its expression.
      - Either `"${ { ... } }"` (single-brace, expression-of-object-literal) or `"${{ ... }}"` (double-brace, object-literal-expression form) is valid — both evaluate to the same JS object. Pick one and stay consistent within a workflow.
    - For single-value responses (returning one variable or one expression), the simple form is fine: `"response": "${$context.outputs.Javascript_1}"` or `"response": "${'done'}"`.
<!--skill-flavor:response-roundtrip-validation:start-->
    - **On-disk is authoritative.** Even with the single-expression workaround, every StudioWeb designer save can re-trigger normalization passes that may corrupt the Response shape. After any designer roundtrip, re-validate with `uip api-workflow run --no-auth` and re-apply the workaround if needed. Until the designer fix ships, treat the file on disk as truth, not what the designer renders.
<!--skill-flavor:response-roundtrip-validation:end-->
16. **Connector activities (HTTP + Integration Service) come from `uip api-workflow registry resolve` + `stub` — never hand-author or guess.** The stub computes `metadata.configuration`, the kind (`UiPath.Http` vs `UiPath.IntSvc`), the endpoint (with hub prefix), `SlotKey`, and `ExportBucketKey` (which can differ — HTTP slot `HttpRequest_1` vs bucket `http_request_1`). Use all of them verbatim; NEVER invent a `uiPathActivityTypeId`, hand-author `metadata.configuration`, or reconstruct a key from `objectName`. Non-negotiables (full step-by-step, field-shape rules, multipart, and worked examples in [references/connector-activity-discovery.md](references/connector-activity-discovery.md)):
    - **A keyword `resolve` miss is NOT proof no curated activity exists — verify connector-first before giving up.** `resolve` AND-matches every token, so a marketing phrase + guessed verb over-narrows (the product "UiPath Data Fabric" carries `connectorKey: uipath-uipath-dataservice` and activity names like "Create Entity Record" — `resolve "data fabric insert"` returns 0; fewer/truer tokens, not more). Before concluding none exists or falling back to a hand-built HTTP call (a Rule 0 fork): map the product/vendor → connector key with `uip is connectors list --filter "<product>"`, then enumerate with `uip is activities list <connector-key>`. Do NOT hardcode/guess the key — look it up. See the reference's Step 1 recovery.
    - **IntSvc/vendor activities require a *pinged* connection.** `uip is connections ping <uuid>` must succeed before authoring — listing-state ≠ runtime-state; an `Enabled` connection can still 401 in cloud. An empty listing is NOT proof no connection exists — `uip is connections list` is folder-scoped. On empty/failed listing, walk the fallbacks in order: unfiltered `uip is connections list`, then `uip is connections list --all-folders` (catches connections in other folders), re-pinging a different `Id` for that `ConnectorKey` each time.
    - **No connection pings cleanly → STOP and ask the user — do not decide alone.** Offer: **(a)** continue with a placeholder (stub without `--connection-id`, leaving the `<REPLACE_WITH_VENDOR_CONNECTION_UUID>` sentinel — workflow is structurally complete but 401s until replaced; only with explicit user consent), or **(b)** stop and wait for the user to create/fix the connection, then re-ping. Never silently emit the placeholder, never silently abort. (Instance of Rule 0 — escalate design forks.)
    - **NEVER ship a `<REPLACE_WITH_*>` placeholder** in `with.connectionId` / `connectionResourceId` / Http `bodyParameters.url`. StudioWeb renders it as a broken connection and the workflow 401s. The placeholder is a sentinel for "re-stub with the real value," not a fill-in-later field.
    - **After every stub, cross-check required fields** — the stub drops `required: true` request fields (e.g. Outlook `getNewestEmail` needs `parentFolderId`). Confirm via `uip is resources describe ... --operation <op>` or the stub's own `metadata.configuration` inputFields; re-stub with `--inputs` if missing.
    - **Connector params use flat dotted keys and BARE literals.** `"message.toRecipients": "..."`, not nested objects; plain `"x@y.com"`, not `"${'x@y.com'}"` — rule 5's wrap is **inverted** here (`${'...'}` clears the field on save). Real references (`${$context...}`) stay wrapped.
    - **NEVER use Http kind with a vendor connection UUID** (401 "Invalid Element token"). IntSvc output is wrapped: read `$context.outputs.<ExportBucketKey>.content.<field>`.
<!--skill-flavor:connector-solution-registration:start-->
    - **(Solutions-mode + IntSvc only)** sync the connection into the catalogue: `uip api-workflow bindings sync --workflow <Workflow.json>` then `uip solution resource refresh --solution-folder <path>`. Skip for Http kind, non-connector activities, and standalone (no `Solution/`) projects.
<!--skill-flavor:connector-solution-registration:end-->
<!--skill-flavor:runtime-invocation-io:start-->
17. **Pass input as a JSON string.** `--input-arguments '{"key":"value"}'`. Invalid JSON exits 1.
18. **Always `--output json`** when parsing CLI output programmatically. Success → `{ "Result": "Success", "Code": "WorkflowRun", "Data": {...} }`. Failure → `{ "Result": "Failure", "Message": "...", "Instructions": "..." }` with exit 1.
<!--skill-flavor:runtime-invocation-io:end-->
<!--skill-flavor:project-creation:start-->
19. **Scaffold with `uip api-workflow init`; publish goes through the solution packager.** Create every API workflow project with `uip api-workflow init <name>` (rule 19a) — never hand-assemble the project files. Project-level CLI commands also exist: `uip api-workflow build <projectDir>` (compile) and `uip api-workflow pack <projectDir> <outputDir>` (single-project `.nupkg`, useful to test one project in isolation). Solution-level build/publish go through `uip solution pack <solutionDir> <outputDir>` + `uip solution publish <package.zip>`. There is NO `uip api-workflow publish` command. Project type must be `"Api"` in the solution `.uipx`.

19a. **Create projects with `uip api-workflow init <name>` — it produces the correct Studio Web editable shape and wires the solution.** Run it from inside the solution directory (the folder containing the `.uipx`):
    ```bash
    uip api-workflow init <name> --output json   # add --skip-solution-registration for a standalone (no .uipx) project
    ```
    It scaffolds `project.uiproj` + `Workflow.json` + `entry-points.json` + `bindings_v2.json` and, when run inside a solution, **auto-registers the project in the surrounding `.uipx`** (correct `ProjectRelativePath` + a fresh `Id`). Success → `Code: "ApiWorkflowInit"`. Then edit `Workflow.json` only.

    **Which mode.** Default = `init` inside a solution (Studio Web-editable + deployable — what a shipped automation needs). Use `--skip-solution-registration` ONLY when the user explicitly wants a CLI-only/local workflow that never opens in Studio Web or ships in a solution; it still emits the full project folder (`<name>/Workflow.json` + siblings), just no `.uipx` wiring. Never emit a lone `Workflow.json` with no project files — even a throwaway local workflow gets a project.

    **Why it matters:** a legacy `project.json` + `workflows/WF_*.json` layout (no `.uiproj`) passes every runtime gate — `validate`, `run`, `pack`, `publish`, deploy — but Studio Web rejects it as `invalid_project_folder` and never shows it. `init` is the one step that can't produce the wrong shape. Full layout + field rules: [references/workflow-file-format.md](references/workflow-file-format.md#project-structure-studio-web-editable-contract).

    To **convert a legacy `project.json` project**, `init` a fresh sibling and move the existing workflow content into its `Workflow.json` (cleanest), or convert in place — see [references/troubleshooting.md](references/troubleshooting.md). Never wire it with `uip solution projects add/remove` (errors on an already-registered name; `remove`+`add` destroys the project `Id`).
<!--skill-flavor:project-creation:end-->

20. **`uip api-workflow validate <Workflow.json>` is the autonomous closure step for every authoring or edit cycle.** Run it as the LAST command before asking the user anything about runtime. It's offline (no auth, no network, no side effects): JSON Schema + semantic checks on the static file. Output codes:
    - `Result: "Success"`, `Code: "ApiwfValidate"`, `Data.Status: "Valid"` (exit 0) — possibly with `Data.Warnings`. Proceed to rule 21 (ask the user whether to run).
    - `Result: "Failure"` (exit 1) — do NOT bother the user. Read `Instructions`, locate the offending activity by its JSON path (e.g. `/do/0/Sequence_1/do/2/Mystery_1/metadata/activityType`), edit `Workflow.json` to fix it, then re-validate. Loop until pass.

    **Reading the error list.** AJV schema errors from `oneOf` branches produce duplicate "Missing required property" noise (each unmatched variant lists all its required fields). Focus on the **semantic-tail errors** — the ones with prose messages like `Unknown activityType 'X'`, `must contain a 'do' with inner 'switch'`, `is missing 'metadata.configuration'`, `Variable must have a non-empty 'type'`. Those uniquely identify the root cause. Fix one root cause, re-validate, repeat — don't chase the schema-level fanout one by one.

<!--skill-flavor:runtime-validation-limit:start-->
    **What validate catches:** malformed JSON; unknown `activityType` values (see VALID_ACTIVITY_TYPES list in the validate source); per-activity required keys (If → `do` + inner `switch`, Sequence → `do`, Assign → `set`, ForEach → `for` + `do`, DoWhile → `for` + `doWhile`, Connector → `call` + `metadata.configuration` + `essentialConfiguration`, Response → `response`, etc.); missing `metadata.activityType`/`displayName` (warnings); bad `evaluate.language`/`evaluate.mode`; duplicate or empty-named workflow variables; empty task lists. **What it does NOT catch:** wrong `selectedResourceId`, broken connector connection IDs, runtime expression errors (`ReferenceError: x is not defined`), unwrapped string literals (rule 5), multi-key `Assign.set` (rule 6) — those still need runtime validation via `uip api-workflow run` once the user consents.
<!--skill-flavor:runtime-validation-limit:end-->

<!--skill-flavor:runtime-execution-consent:start-->
21. **Never run `uip api-workflow run` without an explicit user "yes."** Validation (rule 20) is autonomous; *running* is not. Once validate passes, ask the user: (a) run now or skip, (b) if running, with `--no-auth` (fast, structure-only — IntSvc kind vendor calls fail) or with auth (real Integration Service calls — vendor side effects WILL happen: emails sent, tickets created, files uploaded). Suggest a default based on workflow content (`--no-auth` for control-flow-only + Http kind `ImplicitConnection`; with-auth for any IntSvc kind vendor activity), but wait for the user's answer. Never invoke `uip api-workflow run` with auth on speculation — once a vendor call goes out, it can't be unsent.
<!--skill-flavor:runtime-execution-consent:end-->

22. **TDD gate — only for projects with an `evals/` folder; STOP and ask before authoring; tests are written before the workflow.** Every authoring request (create OR edit — including a one-line change) runs Phase-0 discovery of the project's `evals/` folder — `<project>/evals/`, the directory next to `Workflow.json` (list that directory; the workspace or solution root is the wrong place to look):
    - **No `evals/` folder** → the Evaluations feature is not enabled for this project. Skip the gate entirely: do not offer to create tests, do not mention loop mode, do not create the folder — author normally (Phases 1–3).
    - **`evals/` present** → **end the turn** with two questions. Do not write or edit `Workflow.json`, and do not create or change eval files, until the user has answered both:
      1. **Tests** — the eval set has rows → *"I found N test case(s): [one line each]. Should anything change, or use them as-is?"*; the set is empty (the panel seeds one with 0 rows) → *"There are no test cases yet — want me to add some? I'd suggest: [2–3 proposed cases]."*
      2. **Loop mode** — *"Run in loop mode (run the tests and re-try — fix, re-run — until every case passes), or author once and you verify?"* A "yes" to loop mode is also the consent to run the rows with `--no-auth` (rule 21) — do not ask "run now?" separately; connector/authed runs still need their own explicit "yes".

    **Order after the answers (TDD):** first declare `input.schema` / `output.schema` in `Workflow.json` (`init` scaffolds `output: null`, so the row keys have no other source — property names and casing come from here, and the Response must emit exactly those keys), then write or update the eval set, then author the workflow, then run the rows (loop mode) or hand over (author once — do not run). **Later change requests that alter behavior** (threshold, rounding, branch order, a new default — even with the schema unchanged) can make existing expectations wrong: before editing, list the affected rows and ask whether to update them; after editing, re-run the rows. Ask as two specific questions — never one vague "how do you want to verify it?". With `evals/` present, the gate is skipped only when the user already answered, or explicitly asked not to be prompted ("don't ask for confirmation"); then keep existing tests as-is and add tests only if requested. "Don't ask" waives the two questions, **not** rule 21's run consent: run the rows only if the request itself asks for a run or a loop ("run the evaluations", "until they pass" — that wording is the consent); otherwise author once and hand over the exact command to run them. Protocol and wording: [references/testing-and-evals.md](references/testing-and-evals.md) §3.

23. **Files are references, not bytes — and base64 is a file too.** A file input or output is a `JobAttachment` (`{ ID, FullName, MimeType, Metadata? }`) pointing at a blob in Orchestrator storage; `$workflow.input.<file>` is that object, never the bytes.
    - **The two activities.** Both are `run.script` tasks; the `$helpers.file.*` call in the script is what identifies them (it is what `validate` checks). **File to Base64** (`metadata.activityType: "FileToBase64"`, code `return { output: await $helpers.file.fileToBase64(<file ref>) }`) returns a NEW reference whose blob content IS the base64 text (`<name>.base64`, `text/plain`, `Metadata.Encoding: "base64"`). **Base64 to File** (`metadata.activityType: "Base64ToFile"`, code `return { output: await $helpers.file.base64ToFile({ base64: <ref or string>, fileName?, mimeType? }) }`) returns a binary reference. The script is that single `return` expression and nothing else: Studio Web rebuilds the script from the parsed call on every designer save and silently drops a preceding or trailing statement, a second argument, or an extra option key. `validate` warns only about the extra statements — an extra argument passes as `Valid` and still breaks — so put any pre-processing in a JavaScript activity before the conversion.
    - **Reading results.** Read either activity's result as `$context.outputs.<Key>.output`.
    - **Inlining file content.** To put a file's content INLINE in an HTTP request body or a Response field, call `<ref>.serializeData()` right there — it returns a deferred-read marker the engine fills at send time; never store it in a variable or use it in script logic. Nested in a JSON body it works **only for a base64 reference** (the File to Base64 output): a binary file's marker, or a bare reference, nested in a body is a send-time error — send a binary file as the *whole* body (bare reference) or convert it first.
    - **Naming.** `fileName` / `mimeType` apply only to a raw base64 *string*; a reference keeps its own name and the engine sniffs the type from bytes (a `.txt` round-trips to an extension-less file).
    - **Running.** Both helpers need Orchestrator blob storage:
<!--skill-flavor:file-run-cli:start-->
    `uip api-workflow run --no-auth` refuses such a workflow up front; run it signed in (`uip login`, no `--no-auth`) — it still needs the rule-21 "yes". Pass local files with `--input-file <name>=<path>` (uploaded, arriving as `$workflow.input.<name>`), collect returned files with `--output-dir <dir>` (each reference in the output gains a `LocalPath`), and `--folder-key <guid>` if the tenant's Attachments API requires a folder. In the printed output the CLI PascalCases keys (`ID` → `Id`).
<!--skill-flavor:file-run-cli:end-->
    Shapes, worked example and pitfalls: [references/files-and-base64.md](references/files-and-base64.md).

## Workflow Phases

### Phase 0: Discovery

Before touching anything, understand what exists — the workflow structure **and** whether the project has tests. Discovery ALWAYS includes checking for an `evals/` folder inside the project directory (`ls <project>/` — the folder is a sibling of `Workflow.json`, never at the workspace/solution root): Studio Web creates it when the Evaluations feature is enabled and the panel is opened, so its absence means the feature is off for this project. If present, read `evals/<scope>/eval-sets/*.json` (`<scope>` is `default` unless the project says otherwise) and the evaluator(s) in `evals/<scope>/evaluators/` — the same files the **Evaluations** panel reads and writes. Contract and semantics: [references/testing-and-evals.md](references/testing-and-evals.md) §1.

Then apply **rule 22 (TDD gate)**: no `evals/` folder → the feature is off, continue to Phase 1 without any test or loop-mode question; `evals/` present → end the turn with the two questions — tests (change / add?) and loop mode — and start Phase 1 only after the user has answered, writing the eval set before the workflow.

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
| Encode a file (input or downloaded) as base64 for an API that wants inline base64 | **File to Base64** (`FileToBase64`) | `run.script` calling `await $helpers.file.fileToBase64(<ref>)`; output is a base64 FILE reference — inline it in the body with `.serializeData()`. Rule 23. |
| Turn a base64 payload (API response string or a base64 file) back into a file | **Base64 to File** (`Base64ToFile`) | `run.script` calling `await $helpers.file.base64ToFile({ base64, fileName?, mimeType? })`; output is a binary file reference. Rule 23. |
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

**Precondition (projects with `evals/`):** the two rule-22 questions have been answered in this conversation and the eval set (if wanted) is already written. If not, go back to Phase 0 and ask — do not write `Workflow.json` yet. Projects without `evals/` have no such gate.

For each activity, read its reference section in [references/task-types.md](references/task-types.md), copy the minimal JSON, fill in values.

**For CREATE:** copy from a template, then add user activities AFTER `WorkflowStart` inside the root sequence (literally `Sequence_1.do` in the template skeleton).

**For EDIT:** read the file first, identify the exact insertion / replacement point, use `Edit` with sufficient context for unique matching.

If the edit **changes behavior** and the project has an eval set, rule 22 applies first: ask whether to update the expectations the change would invalidate, then edit, then re-run the rows (see [references/testing-and-evals.md](references/testing-and-evals.md) §3 step 5).

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

<!--skill-flavor:validation-run-lifecycle:start-->
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
<!--skill-flavor:validation-run-lifecycle:end-->

<!--skill-flavor:runtime-troubleshooting:start-->
Fix run failures in category order — **Structure > Expression > Activity Config > Logic** (higher categories often resolve lower ones). Full pitfall catalog: [references/troubleshooting.md](references/troubleshooting.md).
<!--skill-flavor:runtime-troubleshooting:end-->

### Phase 4: Package, Publish, and Operate

<!--skill-flavor:deployment-lifecycle:start-->
Once the workflow runs locally, deploy via the solution packager. If the project must open in Studio Web, confirm it uses the `init`-produced shape first (rule 19a) — runtime/pack success does not prove it.

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

**Operate + diagnose the published workflow.** Once deployed, the workflow is an Orchestrator API process — the local `uip api-workflow` verbs no longer apply to it. Invoke it (HTTP/schedule/Integration Service event trigger), start/list/stop its jobs, manage the Integration Service connections it uses, and read cloud-run logs/traces via `uip or` / `uip is` / `uip traces`. Full command map: [references/operating-published-workflows.md](references/operating-published-workflows.md). These are sibling-skill surfaces (`uipath-platform`, `uipath-troubleshoot`) — delegate there for depth.
<!--skill-flavor:deployment-lifecycle:end-->

<!--skill-flavor:quick-start-create:start-->
## Quick Start (CREATE from scratch)

```bash
# 0. Create the solution (skip if one already exists). Creates ./MySolution/ with the .uipx.
uip solution init MySolution --output json

# 1. Scaffold the project — correct Studio Web shape + auto-registers in the .uipx (rule 19a).
#    init's <name> arg takes no slashes, so cd into the solution dir first; it registers the
#    project in the nearest parent .uipx. Creates MyApiProject/ with project.uiproj,
#    Workflow.json, entry-points.json, bindings_v2.json.
cd ./MySolution
uip api-workflow init MyApiProject --output json

# 1b. TDD gate (rule 22): if ./MyApiProject/evals/ exists (next to Workflow.json), STOP and ask the two questions
#     (tests: change / add?  loop mode?) and wait for the answers before step 2.
#     No evals/ folder → the feature is off for this project; go straight to step 2.

# 2. Edit MyApiProject/Workflow.json to add user activities after WorkflowStart inside the root sequence

# 3. Validate (offline, autonomous — fix + re-validate until Status: Valid)
uip api-workflow validate ./MyApiProject/Workflow.json --output json

# 4. Ask the user, then run (only on user "yes")
uip api-workflow run ./MyApiProject/Workflow.json --no-auth --output json

# 5. Package (cwd is the solution dir)
uip solution pack . ./build --name MyApiSolution --version 1.0.0 --output json

# 6. Publish
uip login
uip solution publish ./build/MyApiSolution_1.0.0.zip --tenant MyTenant --output json   # pack names the zip <name>_<version>.zip
```
<!--skill-flavor:quick-start-create:end-->

## Reference Navigation

| File | Use when |
|------|----------|
| [references/workflow-file-format.md](references/workflow-file-format.md) | Authoring or editing the JSON skeleton: top-level keys, `document.metadata.variables` schema, `input.schema`/`output.schema`, `WorkflowStart` |
| [references/http-retry-config.md](references/http-retry-config.md) | Adding workflow-level HTTP retry policy (`httpRetryConfig`) — scope (GET-only), constant/linear/exponential backoff formulas, defaults, `Retry-After` handling, anti-patterns |
| [references/task-types.md](references/task-types.md) | Adding/editing any single activity — exact JSON shape, required fields, export pattern, common mistakes, basic nesting hints per type |
| [references/control-flow-patterns.md](references/control-flow-patterns.md) | Combining activities into hierarchical structures — nested If, ForEach inside DoWhile, TryCatch around/inside loops, conditional Break, multi-way branching, key uniqueness rules |
| [references/connector-activity-discovery.md](references/connector-activity-discovery.md) | Authoring HTTP Request / Gmail / Outlook / GitHub / Slack / etc. activities via `uip api-workflow registry resolve` + `stub` — three-step flow, sample stub output, field-shape rules, multipart subsection, worked examples |
| [references/expressions-and-context.md](references/expressions-and-context.md) | Writing JS expressions, propagating outputs via `export.as`, accessing `$context` / `$input` / `$workflow`, JS_Invoke argument passing, strict-mode gotchas, key patterns |
| [references/files-and-base64.md](references/files-and-base64.md) | **Files & base64** — `JobAttachment` references, the File to Base64 / Base64 to File activities (exact JSON, `$helpers.file.*`), `serializeData()` for inline bodies/Responses, passing local files in and getting files out of a run, pitfalls |
<!--skill-flavor:cli-reference-navigation:start-->
| [references/cli-reference.md](references/cli-reference.md) | All `uip` commands — `api-workflow init`, `run`, `build`, `pack`, `validate`, `solution init`, `solution pack`, `solution publish`, `login` |
<!--skill-flavor:cli-reference-navigation:end-->
<!--skill-flavor:published-reference-navigation:start-->
| [references/operating-published-workflows.md](references/operating-published-workflows.md) | **Operating + diagnosing a published workflow** — invoke via HTTP/schedule/event triggers, manage Integration Service connections (`uip is connections`), start/list/stop Orchestrator jobs (`uip or jobs`), diagnose a faulted cloud run (`uip or jobs get` — `jobs logs` and `traces spans get` are dead ends here). Delegates depth to `uipath-platform` / `uipath-troubleshoot` |
<!--skill-flavor:published-reference-navigation:end-->
| [references/troubleshooting.md](references/troubleshooting.md) | Failed runs, structure/expression/loop/nesting/response/validation pitfalls, packaging errors, publish errors, debugging strategy |
| [references/testing-and-evals.md](references/testing-and-evals.md) | **Testing / evals** — the `evals/<scope>/eval-sets` + `evaluators` file contract shared with Studio Web's Evaluations panel, `uipath-exact-match` scoring (strict deep-equal on the RAW output — the CLI PascalCases printed keys), running a row locally with `--no-auth` (or through the host in Studio Web), and the **interactive test-until-green loop** (offer → check `evals/` → create/update cases → run/fix/repeat with progress → stale-expectation guard) |
<!--skill-flavor:reference-navigation-extra:start-->

<!--skill-flavor:reference-navigation-extra:end-->

## Templates

| File | Description |
|------|-------------|
| [assets/templates/api-workflow-template.json](assets/templates/api-workflow-template.json) | Empty valid workflow with `WorkflowStart` and empty schemas — drop activities into the root sequence (`Sequence_1.do` in this template) after `WorkflowStart` |
| [assets/templates/conditional-workflow-example.json](assets/templates/conditional-workflow-example.json) | If branching with TryCatch — input validation + classification + error fallback |
| [assets/templates/loop-aggregation-example.json](assets/templates/loop-aggregation-example.json) | DoWhile + ForEach + Assign accumulation — pure-compute aggregation pattern |
| [assets/templates/nested-control-flow-example.json](assets/templates/nested-control-flow-example.json) | Heavy nesting demo — TryCatch around DoWhile around If with conditional Break |
| [assets/templates/file-base64-roundtrip-example.json](assets/templates/file-base64-roundtrip-example.json) | **Files** — a `document` file input → File to Base64 → Base64 to File → Response returning both references. The exact `run.script` shape Studio Web writes for the two activities (rule 23). Verified end-to-end with a signed-in run: local file in → `.base64` reference → decoded file out, bytes identical. |
<!--skill-flavor:template-execution-proof:start-->
| [assets/templates/connector-call-example.json](assets/templates/connector-call-example.json) | **Http kind** — HTTP Request curated activity (`call: "UiPath.Http"`) for arbitrary REST calls. Generated by `registry stub` against the catfacts URL. Shows the canonical shape: `connectionId: "ImplicitConnection"`, `unifiedTypesCompatible: true`, `savedJitInputFieldId: "in_http-request"`, URL in `bodyParameters.url`. Verified end-to-end with `uip api-workflow run --no-auth`. |
<!--skill-flavor:template-execution-proof:end-->
| [assets/templates/vendor-curated-call-example.json](assets/templates/vendor-curated-call-example.json) | **IntSvc kind** — vendor curated activity (`call: "UiPath.IntSvc"`) using Outlook GetNewestEmail as exemplar. The `<REPLACE_WITH_VENDOR_CONNECTION_UUID>` placeholder is a sentinel — replace it with a pinged UUID from `uip is connections list/ping` **before** writing the workflow to disk. StudioWeb renders the literal placeholder as a broken connection if it survives. See rule 16. |
<!--skill-flavor:solution-resource-template:start-->
| [assets/templates/solution-connection-resource-template.json](assets/templates/solution-connection-resource-template.json) | **Solution connection resource** — declares a IntSvc kind connection as a Solution resource. Write to `Solution/resources/solution_folder/connection/<connector-key>/<connection-name>.json`. Required for Solutions-mode projects; without it the StudioWeb properties panel flags the activity as having an invalid connection. |
<!--skill-flavor:solution-resource-template:end-->

## Anti-patterns

The mistakes an agent makes most often (each maps to a Critical Rule above — see it for the full reasoning):

- **Do NOT** use `call: "http"` for a REST call — it's the training-data default, but StudioWeb rejects it (renders as a "block" icon). Use `call: "UiPath.Http"` from `registry stub`. See rule 16.
- **Do NOT** wrap connector `bodyParameters` / `queryParameters` literals as `${'literal'}` — rule 5's wrap is **inverted** for connectors; bare literals only, or the field clears on save. See rule 16.
- **Do NOT** ship a `<REPLACE_WITH_*>` placeholder in a workflow — StudioWeb renders it as a broken connection and it 401s. No pinged UUID → ask the user. See rule 16.
- **Do NOT** read workflow inputs as `$input.<name>` from a non-first activity — use `$workflow.input.<name>`. See rule 13.
- **Do NOT** treat a file input or a File to Base64 result as a string — both are `JobAttachment` references. Inline a file's content only with `<ref>.serializeData()` inside an HTTP body / Response, never in an Assign or script — and inside a JSON body field only on the File to Base64 output (`$workflow.input.document.serializeData()` nested in a body fails with "Raw bytes cannot be embedded in JSON"). See rule 23.
- **Do NOT** write `$helpers.fileToBase64(...)` / `$helpers.base64ToFile(...)` — the helpers live under `$helpers.file.`; `validate` rejects the task and the runtime says `is not a function`. See rule 23.
<!--skill-flavor:runtime-execution-antipattern:start-->
- **Do NOT** invoke `uip api-workflow run` autonomously, and never with auth without an explicit "yes" — vendor calls have irreversible side effects (emails sent, tickets created). See rules 20–21.
<!--skill-flavor:runtime-execution-antipattern:end-->
<!--skill-flavor:project-creation-antipatterns:start-->
- **Do NOT** hand-assemble a project (`project.json` + `main.json`/`workflows/WF_*.json`). Scaffold with `uip api-workflow init <name>` — it writes the correct `project.uiproj` shape and registers it in the `.uipx`. The legacy `project.json`-only shape runs and packs but Studio Web rejects it (`invalid_project_folder`) and never shows it. See rules 19–19a.
- **Do NOT** emit a lone `Workflow.json` with no project files, even for a quick local run. It runs under `uip api-workflow run` but is not a Studio Web project — can't be edited or shipped. Every workflow lives in an `init`-scaffolded project (`--skip-solution-registration` when no solution is needed). See rule 19a ("Which mode").
- **Do NOT** wire a project into the solution with `uip solution projects add/remove` — it errors on an already-registered name, and `remove`+`add` destroys the project `Id`. `init` registers it; for an already-built project, edit the `.uipx` `ProjectRelativePath` in place. See rule 19a.
- **Do NOT** trust "it packed / published / ran" as proof a project opens in Studio Web — every runtime gate passes on the wrong shape. Scaffolding with `init` is what guarantees it (rule 19a).
<!--skill-flavor:project-creation-antipatterns:end-->
- **Do NOT** copy expected outputs from the CLI's printed `Data` — `uip` PascalCases every key (`grade` → `Grade`) and `uipath-exact-match` is case-sensitive on keys, so the row passes for you and fails in the Evaluations panel. Derive keys from `output.schema` / the Response expression and read the raw output from the debug log. See [references/testing-and-evals.md](references/testing-and-evals.md) §2.
- **Do NOT** author first and ask later in a project that has `evals/`: rule 22 ends the turn with the two test questions (change / add tests? loop mode?) BEFORE any `Workflow.json` or eval file is written, unless the user already answered or asked not to be prompted. **Do NOT** offer tests or loop mode — or create an `evals/` folder — in a project that has none: the feature is not enabled there. And **do NOT** "fix" the workflow to satisfy an expectation a requested behavior change made stale — re-derive the expected outputs instead, after asking. See rule 22 + [references/testing-and-evals.md](references/testing-and-evals.md) §3–4.

## Infinite Loop Prevention

If a CLI command fails with the same error 2+ times, do NOT retry it. Investigate the root cause:
<!--skill-flavor:authentication-remediation:start-->
- `Not authenticated` / `Organization ID not available` → ask the user to `uip login`, do not retry
<!--skill-flavor:authentication-remediation:end-->
- `File not found` → check the path with `ls`
- Repeated structural errors after fixes → re-read the workflow and the relevant reference section; you may be misreading the file

Maximum 3 attempts for any single operation. After 3 failures, stop and report what was tried.
