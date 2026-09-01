---
name: uipath-api-workflow
description: "UiPath API Workflow assistant — author, run, validate, package, publish, deploy, and troubleshoot JSON workflows for `uip api-workflow`. Load for ANY create or edit of a `Workflow.json` / API workflow project (even one line); with `evals/` present, tests come first (TDD). Covers Sequence, Assign, JavaScript, If (#Wrapper/#Then/#Else), ForEach, DoWhile, Break, TryCatch, Wait, Response, nested; AND HTTP / IS connector activities via `uip api-workflow registry`. Operate: run locally, IS connections, pack/publish/deploy via `uip solution`, triggers. Test/eval: `evals/<scope>/eval-sets/` datasets (exact-match, Evaluations panel); loop until green. Diagnose: validate → run --no-auth loop, root-cause. Triggers on API workflows, project type \"Api\", JSON with `document.dsl`/`do[]`, those activity types, or public API fetch. Agent evals (`evals/eval-sets/`, no scope) and coded agents→uipath-agents. Flow (.flow) incl. its evals→uipath-maestro-flow. .xaml/coded RPA→uipath-rpa. Coded Apps→uipath-coded-apps."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath API Workflow Assistant

<!--skill-flavor:surface-summary:start-->
Build, run, and publish UiPath API Workflows: JSON conforming to CNCF Serverless Workflow DSL 1.0.0 with UiPath activity extensions. Workflows run through `@uipath/api-workflow-executor` and `uip api-workflow run`, and package as `Type: "Api"` projects through `uip solution pack`.
<!--skill-flavor:surface-summary:end-->
<!--skill-flavor:host-command-contract:start-->
<!--skill-flavor:host-command-contract:end-->

> **TDD gate — read first (rule 22).** For create/edit requests, check `<project>/evals/` beside `Workflow.json`, never at workspace or solution root. If absent, Evaluations is off: do not ask about tests or loop mode; author normally. If present, stop before authoring and ask whether existing rows remain/change or empty tests should be added, and whether to run/retry until all pass or author once. After both answers, declare schemas, write/update evals first, then author. A request not to ask skips these questions, not runtime consent; run rows only when requested. Later behavior changes require asking whether affected expectations should change.

## When to Use This Skill

Use for API workflow JSON creation/editing, local `uip api-workflow run`, validation, build/packaging, publishing, operating published workflows, and activities including Sequence, Assign, JavaScript, If, ForEach, DoWhile, Break, TryCatch, Wait, Response, HTTP Request, and connector activities. Use the connector and testing references for Studio Web connector workflows and project `evals/` layouts.

Do not use for `.flow` Maestro flows (`uipath-maestro-flow`), `.xaml` or coded RPA (`uipath-rpa`), coded agents (`uipath-agents`), or Coded Web Apps (`uipath-coded-apps`). API-workflow evals are only `evals/` beside `Workflow.json` using `evals/<scope>/eval-sets/`; `evals/eval-sets/` is for low-code agents and Flow evals for `uipath-maestro-flow`.

## Core Principles

0. **Escalate judgment-based forks before building.** If a connection is unavailable, no curated activity exists, an undocumented HTTP fallback is needed, an assumed input is missing, or structurally different workflows are plausible, perform only shared discovery, then stop with trade-offs and a recommendation. Do not build every branch. Mechanical choices need no escalation.
1. **Know before writing.** Read an existing workflow before editing and the relevant template before creating.
2. **Start minimal and iterate.** Add one activity at a time; validate and, after consent, run with `--no-auth --output json`; fix and repeat.
3. **Validate before running.** `uip api-workflow validate` is autonomous/offline. `run` is runtime validation, may access HTTP or connections, and requires consent.
4. **Fix by category:** Structure > Expression > Activity Config > Logic.

## Critical Rules

1. **Workflow JSON.** Top level has `document` with `dsl: "1.0.0"`, `evaluate` with `language: "javascript"` and `mode: "strict"`, and `do` containing one root sequence. Root sequence names may vary; read the file. See [references/workflow-file-format.md](references/workflow-file-format.md).

2. **WorkflowStart.** It is first in the root sequence, hydrates variable defaults into `$context.variables`, forwards inputs to `$input`, and must not be removed, renamed, or modified. Only it uses `isTransparent: true`.

3. **Activity objects and keys.** Each activity is one single-key object in a `do` array. Keys are globally unique, including wrapper suffixes such as `#Wrapper`, `#Then`, `#Else`, and `#Body`.

4. **Exports.** Every activity should export output. Assign uses `{ ...$context, variables: { ...$context.variables, ...$output } }`; all others use `{ ...$context, outputs: { ...$context?.outputs, "<ActivityKey>": $output } }`. See [references/expressions-and-context.md](references/expressions-and-context.md).

5. **Literal expressions.** In Assign `set`, Response, If `when`, and variable contexts, string literals must be expressions such as `"${'literal'}"`; numbers, booleans, and references need no wrapping. Connector `bodyParameters`, `queryParameters`, and `pathParameters` instead use bare literals; references remain expressions. See [references/connector-activity-discovery.md](references/connector-activity-discovery.md) and [references/troubleshooting.md](references/troubleshooting.md#studioweb-roundtrip-pitfalls).

6. **Assign.** Each Assign sets exactly one variable. Studio Web collapses multi-key `set`; use sequential Assign activities and merge each single key through the variables export.

7. **If.** Use `If_N#Wrapper` containing `If_N`, `If_N#Then`, and `If_N#Else`. Both branches end with `then: "exit"`; `when` is wrapped in `${...}`. See [references/control-flow-patterns.md](references/control-flow-patterns.md).

8. **Loops.** ForEach and DoWhile require `#Body`. ForEach uses index-aware accumulation, resetting on iteration 0; DoWhile uses simple accumulation. `each` and `at` are plain names, not expressions.

9. **DoWhile.** `for.in` is always `"${ [1] }"`; `doWhile` controls repetition. The body must update the condition variable or the loop may be infinite.

10. **Nested loops.** Use distinct iterator and index names for each loop.

11. **Loop/catch bindings.** Declare `for.each`, `for.at`, and `catch.as` without `$`, but reference them in expressions/scripts with `$`: `"row"` binds `$row`, `"idx"` binds `$idx`, and `"err"` binds `$err`. Omitting `$` causes an undefined-name error.

12. **Break.** It exits only the innermost loop and is valid only inside `#Body`. Put it inside an If; `break` must be string `"true"`, with `then: "exit"` and `set: "${$input}"`. To exit nested loops, set a flag and check it in the outer loop. See [references/control-flow-patterns.md](references/control-flow-patterns.md#5-conditional-break-inside-a-loop).

13. **Workflow inputs.** Use `$workflow.input.<name>`, never `$input.<name>` from a non-first activity; `$input` is current task input and may be prior output.

14. **JavaScript.** Scripts read `$context`, `$workflow`, and `$input` as globals and must return a value. Keep standard Studio Web `run.script.arguments` scaffolding: `"${{ \"$context\": $context, \"$workflow\": $workflow, \"$input\": $input }}"`; runtime ignores it.

15. **Response.** `markJobAsFailed` is a sibling of `response`. Always use `then: "end"`; `then: "exit"` is for branches/loops. Object responses use one expression, e.g. `"${{ key: $context.variables.value }}"`, not independently interpolated fields. Single values may use `"${$context.outputs.Activity}"` or `"${'done'}"`. `${ { ... } }` and `${{ ... }}` are both valid; stay consistent. After Studio Web saves, treat disk as authoritative and rerun `uip api-workflow run --no-auth` after reapplying needed workarounds.

16. **Connectors and HTTP are registry-generated only.** Run `uip api-workflow registry resolve` then `stub`; never guess `uiPathActivityTypeId`, `metadata.configuration`, activity kind, endpoint, `SlotKey`, or `ExportBucketKey`; use stub output verbatim.
   - A keyword `resolve` miss is not proof of no curated activity because it AND-matches tokens. Identify product/vendor with `uip is connectors list --filter`, then enumerate with `uip is activities list <connector-key>` before fallback.
   - IntSvc/vendor activities require successful `uip is connections ping <uuid>`. If listing is empty/fails, try unfiltered listing, then `--all-folders`, and ping another matching connection.
   - If none ping successfully, stop and ask whether to continue with explicit placeholder consent or wait for a fixed connection. Never silently choose.
   - Never put replacement sentinels in `with.connectionId`, `connectionResourceId`, or an HTTP URL. Re-stub with a real value before writing.
   - After every stub, check required fields using resource description or stub inputs, then re-stub with `--inputs` if needed.
   - Connector parameters use flat dotted keys and bare literals; do not use `${'literal'}`.
   - Do not use `UiPath.Http` with a vendor connection UUID. IntSvc results are wrapped; read `$context.outputs.<ExportBucketKey>.content.<field>`.
   - In Solutions mode, sync IntSvc bindings with `uip api-workflow bindings sync --workflow <Workflow.json>` and refresh with `uip solution resource refresh --solution-folder <path>`. Skip for HTTP, non-connectors, and standalone projects.
   - See [references/connector-activity-discovery.md](references/connector-activity-discovery.md) for discovery, fields, multipart, and examples.

17. **CLI input.** Pass JSON as a string: `--input-arguments '{"key":"value"}'`; invalid JSON exits 1.

18. **CLI output.** Parse with `--output json`. Success: `{ "Result": "Success", "Code": "WorkflowRun", "Data": {...} }`; failure: `{ "Result": "Failure", "Message": "...", "Instructions": "..." }` with exit 1.

19. **Project creation and publishing.** Scaffold with `uip api-workflow init <name>`; do not hand-assemble project files. Project commands include `build <projectDir>` and `pack <projectDir> <outputDir>`. Use `uip solution pack` and `uip solution publish`; there is no `uip api-workflow publish`. Solution type is `"Api"`.

19a. **Init shape and registration.** Run `uip api-workflow init <name> --output json` inside the solution directory. It creates `project.uiproj`, `Workflow.json`, `entry-points.json`, and `bindings_v2.json`, and registers the project in the nearest `.uipx`. Use `--skip-solution-registration` only when explicitly requested for a standalone CLI/local project. Always create a full project, never a lone workflow file. Do not use solution project add/remove or change existing project IDs. For legacy `project.json`, initialize a fresh sibling and move content into its `Workflow.json`, or convert in place; see [references/troubleshooting.md](references/troubleshooting.md). Runtime success does not prove Studio Web compatibility; init-produced shape does.

20. **Static validation.** Run `uip api-workflow validate <Workflow.json> --output json` as the last autonomous command in every author/edit cycle. On `Result: "Failure"`, read `Instructions`, fix the activity at its JSON path, and repeat until `Data.Status: "Valid"`. Prioritize semantic-tail errors over duplicate `oneOf` noise. Validation catches malformed JSON, unknown types, required-field errors, bad evaluate settings, duplicate/empty variables, and empty task lists; not broken connections, wrong resource IDs, runtime expression errors, unwrapped literals, or multi-key Assign sets.

21. **Runtime consent.** Never run `uip api-workflow run` without explicit consent. After validation, ask whether to skip, run `--no-auth`, or run with auth. Recommend `--no-auth` for control-flow-only workflows and HTTP with `ImplicitConnection`; recommend authenticated execution only for IntSvc after confirming real side effects. Authenticated calls may send emails, create tickets, or upload files. Loop-mode consent authorizes eval rows with `--no-auth`, but authenticated connector runs still require explicit consent.

22. **TDD gate.** Check `<project>/evals/` on every create/edit. Without it, do not offer tests, create the folder, or mention loop mode. With it, stop before modifying `Workflow.json` or evals and ask whether existing cases change or new cases are added, and whether to run/retry until all pass or author once. If rows exist, report their count and summarize each; if empty, propose 2–3 cases. After answers, declare `input.schema` and `output.schema`, update evals, author, then run rows only in loop mode or hand over in author-once mode. Behavior changes require identifying affected rows and asking whether expectations should change. A request not to ask keeps existing tests and does not authorize runtime. See [references/testing-and-evals.md](references/testing-and-evals.md) §3.

## Workflow Phases

### Phase 0: Discovery

Check the project directory for `evals/`, then read `evals/<scope>/eval-sets/*.json` and evaluators when present. For edits, read `Workflow.json`, keys, variables, schemas, and export patterns. For creates, read [assets/templates/api-workflow-template.json](assets/templates/api-workflow-template.json), the closest conditional/loop/nested-control-flow template, and [references/control-flow-patterns.md](references/control-flow-patterns.md) as needed. Apply rule 22 before authoring.

### Phase 1: Plan

Choose activities, unique keys, variables, inputs, outputs, and nesting. Use Assign for variables, JavaScript/JsInvoke for custom logic, If for branching, ForEach for collections, DoWhile for repetition, TryCatch for errors, Wait for pauses, Response for termination, Break inside an If, and registry-generated `UiPath.Http` or `UiPath.IntSvc` for HTTP/connectors. Use generic connector activities only when registry discovery finds no curated operation. Read [references/task-types.md](references/task-types.md).

### Phase 2: Generate or Edit

Copy minimal shapes from references. Create from the template and place activities after `WorkflowStart` in the root sequence. For edits, preserve conventions and use sufficient unique context. When rule 22 applies, declare schemas before eval rows. Skeleton:

```json
{
  "document": { "dsl": "1.0.0", "name": "...", "version": "0.0.1", "namespace": "default", "metadata": { "variables": { "schema": { "format": "json", "document": { "type": "object", "properties": {}, "title": "Variables" } } } } },
  "input": { "schema": { "format": "json", "document": { "type": "object", "properties": {}, "title": "Inputs" } } },
  "output": { "schema": { "format": "json", "document": { "type": "object", "properties": {}, "title": "Outputs" } } },
  "do": [{ "Sequence_1": { "do": [{ "WorkflowStart": {} }] } }],
  "evaluate": { "mode": "strict", "language": "javascript" }
}
```

### Phase 3: Validate, Then Run With Consent

```bash
uip api-workflow validate ./<project>/Workflow.json --output json
uip api-workflow run ./<project>/Workflow.json [--no-auth] --output json
```

Validate autonomously and fix until valid; then ask before running. If skipped, provide the exact command. Triage failures as Structure > Expression > Activity Config > Logic; see [references/troubleshooting.md](references/troubleshooting.md).

### Phase 4: Package, Publish, and Operate

Confirm init-produced shape, then:

```bash
uip solution pack <solutionDir> <outputDir> --name <PACKAGE_NAME> --version 1.0.0 --output json
uip solution publish <outputDir>/<package>.zip --tenant <TENANT_NAME> --output json
```

Publishing requires `uip login`. The packager detects `Type: "Api"`, validates/copies workflows, generates deployment metadata, and produces a `.nupkg` inside a `.zip`. After deployment, operate through Orchestrator/API triggers, jobs, connections, logs, and traces; local `uip api-workflow` verbs no longer operate the published workflow. See [references/operating-published-workflows.md](references/operating-published-workflows.md), delegating depth to `uipath-platform` or `uipath-troubleshoot` when appropriate.

## Quick Start (CREATE from scratch)

```bash
uip solution init <SolutionName> --output json
cd <SolutionName>
uip api-workflow init <ProjectName> --output json
# If <ProjectName>/evals/ exists, stop and apply rule 22; otherwise edit after WorkflowStart.
uip api-workflow validate ./<ProjectName>/Workflow.json --output json
# Ask for consent, then run if approved:
uip api-workflow run ./<ProjectName>/Workflow.json --no-auth --output json
uip solution pack . ./build --name <PackageName> --version 1.0.0 --output json
uip login
uip solution publish ./build/<package>.zip --tenant <TenantName> --output json
```

## Reference Navigation

| File | Use |
|---|---|
| [references/workflow-file-format.md](references/workflow-file-format.md) | JSON skeleton, schemas, variables, `WorkflowStart`, Studio Web structure |
| [references/http-retry-config.md](references/http-retry-config.md) | Workflow-level HTTP retry/backoff |
| [references/task-types.md](references/task-types.md) | Activity shapes, required fields, exports, mistakes |
| [references/control-flow-patterns.md](references/control-flow-patterns.md) | Nested If, loops, TryCatch, Break, branching, key uniqueness |
| [references/connector-activity-discovery.md](references/connector-activity-discovery.md) | Registry resolve/stub, connections, fields, multipart, examples |
| [references/expressions-and-context.md](references/expressions-and-context.md) | Expressions, context, inputs, scripts, exports, strict mode |
| [references/cli-reference.md](references/cli-reference.md) | API workflow, solution, login, build, pack, validate, publish |
| [references/operating-published-workflows.md](references/operating-published-workflows.md) | Published triggers, connections, jobs, logs, traces |
| [references/troubleshooting.md](references/troubleshooting.md) | Runtime, structure, expression, connector, response, packaging, publish failures |
| [references/testing-and-evals.md](references/testing-and-evals.md) | Eval contract, scoring, raw outputs, test-until-green protocol |

## Templates

- [assets/templates/api-workflow-template.json](assets/templates/api-workflow-template.json) — empty valid skeleton.
- [assets/templates/conditional-workflow-example.json](assets/templates/conditional-workflow-example.json) — conditional branching/error handling.
- [assets/templates/loop-aggregation-example.json](assets/templates/loop-aggregation-example.json) — loop aggregation.
- [assets/templates/nested-control-flow-example.json](assets/templates/nested-control-flow-example.json) — deeply nested control flow.
- [assets/templates/connector-call-example.json](assets/templates/connector-call-example.json) — registry-generated HTTP with `ImplicitConnection`.
- [assets/templates/vendor-curated-call-example.json](assets/templates/vendor-curated-call-example.json) — IntSvc activity; replace its connection sentinel before writing.
- [assets/templates/solution-connection-resource-template.json](assets/templates/solution-connection-resource-template.json) — Solutions-mode IntSvc connection resource.

## Anti-patterns

- Do not use `call: "http"`; use registry-generated `UiPath.Http`.
- Do not wrap connector parameter literals as `${'literal'}`.
- Do not ship connection or URL replacement sentinels.
- Do not read later workflow inputs from `$input.<name>`.
- Do not run autonomously or authenticated vendor calls without consent.
- Do not hand-assemble legacy projects, emit a lone `Workflow.json`, or use solution project add/remove.
- Do not treat runtime, pack, or publish success as Studio Web compatibility proof.
- Do not copy expected eval outputs from PascalCased CLI display data; derive keys from `output.schema` and Response, using raw output for expectations.
- Do not author first when `evals/` exists; apply rule 22. Do not create or offer evals when absent. Do not change logic merely to satisfy stale expectations.

## Infinite Loop Prevention

If a command fails with the same error twice, investigate instead of retrying. Allow at most three attempts per operation, then stop and report what was tried.

- Authentication/organization errors: ask the user to run `uip login`.
- File-not-found errors: verify paths with `ls`.
- Repeated structural errors: reread the workflow and relevant reference.
