---
name: uipath-maestro-flow
description: "TRIGGER for `.flow` files, UiPath Flow / Maestro Flow build/edit requests, and adding or listing IXP model/document-extraction nodes for a Flow. Build, edit, run, debug, fix, evaluate a Maestro Flow (.flow): create/connect nodes (connector, approval, script, subflow, ixp), triggers, schedules, validate; upload, publish, manage runs/instances; diagnose errors, incidents, traces; design eval sets, evaluators, run Studio Web evals. `uip maestro flow` CLI. DO NOT TRIGGER for raw IXP project labelling/prediction review/prompt tuning outside Flow→uipath-ixp; C#/XAML→uipath-rpa; standalone agents→uipath-agents."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Flow Skill

Guide for creating, editing, validating, debugging, publishing, diagnosing, and evaluating UiPath Flow projects with the `uip` CLI and `.flow` format.

## Capabilities

- **Author** — Build and edit `.flow` files; create projects with `uip maestro flow init`; add nodes, edges, variables, subflows, transforms, and triggers; explore the registry; validate and format locally; apply node ownership; configure connectors, triggers, managed HTTP, inline-agent scaffolding, IxP/document-extraction nodes, and IxP models; plan complex flows first. Read [references/author/CAPABILITY.md](references/author/CAPABILITY.md).
<!--skill-flavor:project-creation-scope:start-->
  - Create projects with `uip maestro flow init`.
<!--skill-flavor:project-creation-scope:end-->
- **Operate** — Publish, run, and manage deployed flows; push to Studio Web with `uip solution upload`; deploy to Orchestrator with `uip maestro flow pack` plus `uip solution publish`; debug real systems, trigger processes, inspect jobs/traces, and pause, resume, cancel, or retry instances. Read [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md).
<!--skill-flavor:upload-scope-bullets:start-->
  - Push to Studio Web with `uip solution upload`.
  - Deploy to Orchestrator with `uip maestro flow pack` plus `uip solution publish`.
<!--skill-flavor:upload-scope-bullets:end-->
- **Diagnose** — Investigate failed or misbehaving runs; triage `flow debug` or deployed runs; inspect incidents, runtime variables, and deployed BPMN; recognize MST-9107, MST-9061, HITL-stuck, reused-reference-ID, and single-nested-layout failures. Read [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md).
- **Evaluate** — Design and run evaluations; create evaluators and eval sets, add data points, pin entry points, run Studio Web evaluations, poll status, fetch results, and compare runs. Read [references/evaluate/CAPABILITY.md](references/evaluate/CAPABILITY.md).
<!--skill-flavor:upload-eval-scope-bullet:start-->
  - Decide whether to call `uip solution upload` (almost always do not auto-run; ask first).
<!--skill-flavor:upload-eval-scope-bullet:end-->

## Capability router

| Goal | Reference |
|---|---|
| Create or edit a flow | [references/author/CAPABILITY.md](references/author/CAPABILITY.md) |
| Publish, deploy, debug, or manage lifecycle | [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md) |
| Diagnose a failed or misbehaving run | [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md) |
| Design/run evaluations | [references/evaluate/CAPABILITY.md](references/evaluate/CAPABILITY.md) |
| CLI syntax | [references/shared/cli-commands.md](references/shared/cli-commands.md) |
| CLI conventions, `--output json`, `--output-filter`, login, and `FOLDER_KEY` | [references/shared/cli-conventions.md](references/shared/cli-conventions.md) |
| `.flow` JSON format | [references/shared/file-format.md](references/shared/file-format.md) |
| Variables and `=js:` expressions | [references/shared/variables-and-expressions.md](references/shared/variables-and-expressions.md) |
| Wire node outputs to inputs | [references/shared/node-output-wiring.md](references/shared/node-output-wiring.md) |
| Shared action-node boilerplate | [references/shared/action-nodes.md](references/shared/action-nodes.md) |
| Optional progress narration and todos | [references/shared/ux-narration-and-todos.md](references/shared/ux-narration-and-todos.md) |

## Critical rules (universal)

> **Tool vocabulary.** `Edit` means in-place replacement, `Write` a full-file write, `Read`/`Glob`/`Grep` file access, `Bash` shell, and a progress list the harness task list. Map them to equivalent tools elsewhere; preserve reviewable diffs and use shell file edits only as a last resort.

1. **Use `--output json`; prefer `--output-filter` for extraction.** Filters are global and run against the `Data` envelope, so expressions start at `Data` without a `Data.` prefix. Registry search returns a flat PascalCase array (`NodeType`, `DisplayName`, `Description`, `AvailableOnTenant`), not `Data.Nodes` or lowercase fields. Example: `uip maestro flow registry search <keyword> --output json --output-filter "[*].{NodeType:NodeType,DisplayName:DisplayName,Description:Description,AvailableOnTenant:AvailableOnTenant}"`. With `--local`, omit `AvailableOnTenant`. Use `python3 -c` or `jq` only after verifying shape and when JMESPath cannot express the transform. See [cli-conventions.md §3](references/shared/cli-conventions.md#3-prefer---output-filter-for-extraction).
2. **Do not run `flow debug` without explicit user consent.** It can cause real side effects, including emails, messages, and API calls.
3. **Search before creating or declaring resources absent.** For named agents, API workflows, RPA processes, and similar resources: (a) pull and search the tenant registry with `uip maestro flow registry pull --force && uip maestro flow registry search "<name>" --output json`; pull first because the cache expires after 30 minutes, login is required, and only published resources are returned; (b) search locally with `uip maestro flow registry list --local --output json` or `search "<name>" --local`; an empty keyword search does not prove absence, so confirm with `list --local`; (c) scaffold, mock, or create only when both searches find no match and the user explicitly requests embedding/creation or no published resource satisfies the need.

   “Coded” and “low-code” describe implementation style, not inline status. Use `uipath.agent.autonomous` only when explicitly asked to embed/inline/create an agent. Use `core.logic.mock` only when the resource is neither in the solution nor published. See [rpa](references/author/references/plugins/rpa/impl.md) and [agent](references/author/references/plugins/agent/impl.md).

   Apply the same discipline to connectors: derive the connector key from `uipath.connector.<connector-key>.<activity>`, never a brand name; discover connections with `uip is connections list "<connector-key>" --all-folders`. An unverified key or missing `--all-folders` makes an empty result a false negative.

   For every named external service, first run `uip maestro flow registry search "<service>" --output json`, then follow the [Selecting External Service Nodes](references/author/references/planning-arch.md#selecting-external-service-nodes) ladder: connector, managed HTTP, then RPA. Manual `core.action.http.v2` is last, not a brand-name first guess, even when skipping full planning; see [greenfield.md — Select the node type for each external service](references/author/references/greenfield.md#select-the-node-type-for-each-external-service-runs-even-when-full-planning-is-skipped).

   A manual `core.action.http.v2` for a well-known connector-backed SaaS domain, or an `in` variable containing its token/API key/bearer secret, indicates skipped search. Stop, search the registry, list connections with `--all-folders`, and use the connector or connector-mode HTTP (`authentication:"connector"`, `targetConnector`, and bound `connectionId`/`folderKey`). Manual mode is valid only when search proves no connector exists.
4. **Never invoke other skills automatically.** Identify the needed RPA process, agent, or app and provide handoff instructions; let the user choose whether to switch skills.
5. **Present finite decisions as dropdowns with a final “Something else” option.** This includes solution, publish/debug/deploy, connector, trigger, and resource-binding choices. If selected, parse the free-form answer. Without structured questions, use a numbered chat list. In CI/headless mode, take a marked recommended option and record it prominently in the final report; if none is recommended, stop and report the decision. Never auto-answer consent gates, including `flow debug` and destructive actions; stop and report them when no user is available.
<!--skill-flavor:project-creation:start-->
6. **Discover the target solution before scaffolding.** A Flow project must use double nesting: `<Solution>/<Project>/<Project>.flow`. Before any new `uip solution init` or `uip maestro flow init`, run `find . -maxdepth 2 -type f -name '*.uipx' -print`. If a solution exists, stop and ask which to use: one option per solution, “Create a new solution,” then “Something else.” Do not silently adopt, initialize, delete, or repair an existing solution, even if a new one was requested. If creating one, ask for its name rather than defaulting to the Flow name.

   If none exists, create one automatically, defaulting its name to the Flow name unless specified. Prefer solution-first: `uip solution init "<SolutionName>" --output json && cd "<SolutionName>" && uip maestro flow init "<FlowName>" --output json`, producing `<SolutionName>/<FlowName>/<FlowName>.flow` and registering it in the parent `.uipx` (`Data.SolutionRegistration.Status: "Registered"`). Names are independent. A current CLI may auto-scaffold outside a solution as `<FlowName>Solution/<FlowName>Solution.uipx` with `Data.AutoCreatedSolution`; use that only when the solution name does not matter. `--skip-solution-registration` creates a bare single-nested project that fails Studio Web upload and packaging. If the target directory is non-empty, init leaves it untouched. Never omit `cd`, or a duplicate auto-scaffolded solution may be created. Finish with one `project.uiproj`; remove strays. See [author/greenfield.md](references/author/references/greenfield.md) Step 2.
<!--skill-flavor:project-creation:end-->
7. **Narrate progress only when requested or clearly opted into.** Otherwise work silently and surface decisions, failures, consent gates, and the final result. When engaged, use one short plain-English line per logical step across CLI calls, shell builtins, edits, and searches; do not narrate flags or JSON structure. See [shared/ux-narration-and-todos.md](references/shared/ux-narration-and-todos.md) §When to engage.
8. **Maintain a user-facing progress list only when tracking or verbosity is requested.** In silent mode no visible todo list is required. When engaged, journeys above trivial complexity get granular step-level todos; counts follow actual work, not a target. Hide registry lookups, parsing, and file reads inside their logical step. See [shared/ux-narration-and-todos.md](references/shared/ux-narration-and-todos.md) for triggers, granularity, thresholds, and pivots.
9. **Each node has exactly one author: Edit/Write or CLI, never both.** CLI-owned nodes are connector activities (`uipath.connector.<key>.<op>`), connector triggers (`uipath.connector.trigger.<key>.<trigger>`), wait-for-events (`uipath.connector.event.<key>.<event>`, configured like triggers), and managed HTTP (`core.action.http.v2`); add/configure them with `uip maestro flow node add` and `node configure`. All others—triggers, control flow, logic, HITL, patterns, agents, resource nodes, and queues—are user-owned and should be authored directly with `Edit` or `Write`. Never full-file `Write` a flow containing CLI-owned nodes because it can clobber CLI-set `bindings[]` and `inputs.detail`; use `Edit` or configure CLI-owned nodes last. Their `inputs.detail` is a `=jsonString:essentialConfiguration` envelope rejected when hand-authored. Inline-agent CLI is limited to `uip agent init / refresh / validate --inline-in-flow`; the `uipath.agent.autonomous` node is user-owned. Scripting (`python`, `node`, `jq`, `sed`, `awk`, or shell heredocs) is a last resort for user-owned edits and requires explicit approval after explaining state bypass, opaque diffs, and lack of interruption points. See [author/CAPABILITY.md — Node ownership](references/author/CAPABILITY.md#node-ownership--who-authors-the-node) and [author/editing-operations.md — Tool Selection Ladder](references/author/references/editing-operations.md#tool-selection-ladder).
10. **Batch independent tool calls and chain dependent CLI calls.** A typical greenfield build is three turns: T1 scaffold, pull the registry, and add CLI-owned nodes in one chained `Bash`, alongside independent registry/file reads; T2 read the scaffold while editing/adding the End node and edges; T3 chain configure, validate, and format. Split only when later work depends on stdout or a mutation. See [author/references/greenfield.md — Three-turn execution map](references/author/references/greenfield.md#three-turn-execution-map).
11. **Cross-node bindings in `=js:` require `$vars.`** Use `=js:$vars.<nodeId>.output...`; bare `=js:<nodeId>.output...` resolves to `undefined`. See [variables-and-expressions.md — IS Activity Inputs Require `=js:`](references/shared/variables-and-expressions.md#is-activity-inputs-require-js-critical).
12. **Node and edge IDs must begin with a letter.** Use descriptive camelCase node IDs and `edge_<sourceNodeId>_<sourcePort>_<targetNodeId>_<targetPort>` edge IDs. Reserve UUIDs for the top-level flow `id` and `entryPointId`.

## Anti-patterns (universal)

- Never use `--format json`; use `--output json`.
- Do not pipe JSON to `python3 -c` or `jq` for simple extraction; use `--output-filter`, verify shape first, and use external parsers only for unsupported transforms. A valid but wrong filter can return `Data: []`; `keys(@)` fails on arrays, so probe with `type(@)` first. See [cli-conventions.md §3](references/shared/cli-conventions.md#3-prefer---output-filter-for-extraction).
- Never use `flow debug` for validation; use `flow validate`, because debug has real side effects.
- Never silently choose the first registry match. Use the Connector Disambiguation ladder in [connector/planning.md — Disambiguation](references/author/references/plugins/connector/planning.md#disambiguation--when-search-returns-multiple-connectors-for-the-same-intent), deferring to Integration Service rules.
- Never conclude that no connection exists from bare `uip is connections list`; use a registry-derived connector key and `--all-folders`.
- Never represent `customFieldsRequestDetails.parameterValues` as an object map. Studio Web emits `Map<string,string|null>` as `[[key, value], ...]`; inner keys are camelCase (`objectActionName`, `parameterValues`). See [connector/impl.md Step 6c](references/author/references/plugins/connector/impl.md).
- Never treat validation exit code 0 as completion when warnings remain. Resolve every warning. A connector-keyword warning about generic `core.action.http.v2` without a connection binding means a brand-name shortcut was used; bind the connector before shipping or debugging.
- Never issue setup or finalization CLI calls one per turn; chain them per rule 10 and the [Three-turn execution map](references/author/references/greenfield.md#three-turn-execution-map).

> **Trouble?** Use `/uipath-feedback` to report unexpected behavior.