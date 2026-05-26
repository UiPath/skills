---
name: uipath-maestro-flow
description: "Always invoke for `.flow` files. UiPath Maestro Flow (.flow) — build, edit, run, debug, fix, evaluate. Create, connect nodes; connector, approval, script, subflow; triggers, schedules; validate. Upload, publish, manage runs, instances. Diagnose errors, incidents, traces. Design eval sets, evaluators, run Studio Web evals via `uip maestro flow eval`. `uip maestro flow` CLI. For C#/XAML→uipath-rpa. For agents→uipath-agents."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Flow Skill

Comprehensive guide for creating, editing, validating, debugging, publishing, diagnosing, and evaluating UiPath Flow projects using the `uip` CLI and `.flow` file format. The skill is organized into four capabilities — **Author**, **Operate**, **Diagnose**, **Evaluate** — each with its own index doc.

## When to use this skill

**Author** — building or editing a `.flow` file. Read [references/author/CAPABILITY.md](references/author/CAPABILITY.md).

- Create a new Flow project (`uip maestro flow init`)
- Edit a `.flow` file — add nodes, edges, variables, subflows, transforms, triggers
- Explore available node types via the registry
- Validate or format a Flow file locally
- Apply Node ownership — Edit/Write for user-owned nodes, CLI for CLI-owned nodes (see Author capability)
- Configure connector, connector-trigger, or managed HTTP nodes; scaffold inline-agent projects
- Plan a complex flow before building

**Operate** — publishing, running, or managing a deployed flow. Read [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md).

- Push a flow to Studio Web (`uip solution upload`)
- Deploy a flow to Orchestrator (`uip maestro flow pack` + `uip solution publish`)
- Debug a flow end-to-end against real systems
- Trigger a deployed process
- Check job status or stream traces
- Pause, resume, cancel, or retry a running instance

**Diagnose** — investigating a failed or misbehaving run. Read [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md).

- Triage a failed `flow debug` or deployed process run
- Read incidents, runtime variables, deployed BPMN
- Recognize known failure modes (MST-9107, MST-9061, HITL-stuck, reused reference IDs, single-nested layout)

**Evaluate** — designing and running evaluations against a deployed flow. Read [references/evaluate/CAPABILITY.md](references/evaluate/CAPABILITY.md).

- Create evaluators (`exact-match`, `json-similarity`, `contains`, `llm-judge-*`) for a Flow project
- Create eval sets, add data points (test cases), pin entry points
- Start Studio Web eval runs, poll status, fetch results, compare runs
- Decide whether to call `uip solution upload` (almost always: don't auto-run; ask first)

## Capability router

| I want to...                                                 | Read                                                                                             |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| Create a new flow or edit an existing one                    | [references/author/CAPABILITY.md](references/author/CAPABILITY.md)                               |
| Publish, deploy, debug, or manage a flow's lifecycle         | [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md)                             |
| Diagnose a failed or misbehaving flow run                    | [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md)                           |
| Design and run evaluations (`uip maestro flow eval`)         | [references/evaluate/CAPABILITY.md](references/evaluate/CAPABILITY.md)                           |
| Look up CLI command syntax                                   | [references/shared/cli-commands.md](references/shared/cli-commands.md)                           |
| Look up CLI conventions (`--output json`, login, FOLDER_KEY) | [references/shared/cli-conventions.md](references/shared/cli-conventions.md)                     |
| Understand the `.flow` JSON format                           | [references/shared/file-format.md](references/shared/file-format.md)                             |
| Understand variables and `=js:` expressions                  | [references/shared/variables-and-expressions.md](references/shared/variables-and-expressions.md) |
| Wire one node's output into another node's input             | [references/shared/node-output-wiring.md](references/shared/node-output-wiring.md)               |
| Look up action-node boilerplate shared across plugin `impl.md`s | [references/shared/action-nodes.md](references/shared/action-nodes.md)                           |
| Narrate progress to the user + maintain todos                | [references/shared/ux-narration-and-todos.md](references/shared/ux-narration-and-todos.md)       |

## Critical rules (universal)

These rules apply across all three capabilities. Each capability index adds capability-scoped rules on top.

1. **ALWAYS use `--output json`** on all `uip` commands when parsing output programmatically.
2. **Do NOT run `flow debug` without explicit user consent** — debug executes the flow for real (sends emails, posts messages, calls APIs).
3. **Resource discovery order — search before creating.** When the prompt references an existing resource by name ("use the X agent", "call the Y API workflow", "invoke the Z RPA process"), follow this order strictly before deciding the resource doesn't exist:
   1. **Tenant registry search** — `uip maestro flow registry search "<name>" --output json`. Requires `uip login`; returns published resources.
   2. **In-solution local discovery** — `uip maestro flow registry list --local --output json`. No login required; returns sibling projects in the same `.uipx` solution.
   3. **Only then create/scaffold** — scaffold an inline agent, mock, or create-new-resource only when both searches return no match AND either the user explicitly asks to embed/inline/create, or no published resource can satisfy the requirement.

   The words "coded" and "low-code" describe the _implementation style_ of a published agent — they are NOT synonyms for "inline". `uipath.agent.autonomous` (inline) is only correct when the user explicitly asks to embed/inline/create a new agent inside this flow. Only use `core.logic.mock` when the resource is **not** in the same solution and not yet published. See the relevant resource plugin's `impl.md` (e.g., [rpa](references/author/references/plugins/rpa/impl.md), [agent](references/author/references/plugins/agent/impl.md)).

4. **Never invoke other skills automatically** — when a flow needs an RPA process, agent, or app, identify the gap and provide handoff instructions. Let the user decide when to switch skills.
5. **Always present user questions as a dropdown with a "Something else" escape hatch** — Whenever this skill needs a decision from the user (which solution to use, publish vs debug vs deploy, which connector to pick, which trigger type, which resource to bind, etc.), use the `AskUserQuestion` tool with the enumerated choices as options AND include **"Something else"** as the last option so the user can supply free-form string input. Never ask open-ended questions in chat when a finite set of sensible defaults exists. If the user picks "Something else", parse their string answer and continue.
6. **A Flow project MUST live inside a solution** — always scaffold the solution first (`uip solution init <Name>`), then `cd <Name>` and run `uip maestro flow init <Name>`. The correct layout is **always** `<Solution>/<Project>/<Project>.flow` (double-nested). Running `uip maestro flow init` in a bare directory produces a single-nested `<Project>/<Project>.flow` layout that fails Studio Web upload, packaging, and downstream tooling. See [author/greenfield.md](references/author/references/greenfield.md) Step 2.
7. **Always narrate progress in plain English at each logical step boundary.** One short line per step, in user terms ("checking your tenant login", "adding the Slack node and wiring its inputs", "editing the flow JSON to add the new variable", "running validate") — no flag-level or JSON-structure-level detail. Applies uniformly to `uip` CLI calls, shell builtins (`ls`, `cat`, `cd`, `mkdir`, `find`, `grep`), file edits (Read/Write/Edit), and bulk searches (Glob/Grep). The user should never need to know `bash`, `uip` flags, or `.flow` JSON internals to follow along. See [shared/ux-narration-and-todos.md](references/shared/ux-narration-and-todos.md).
8. **Use `TodoWrite` for any journey above the trivial threshold; keep granularity per-step, not per-phase.** Standard journeys (greenfield, brownfield with multiple nodes, ship, run, full diagnose) require a granular todo list — one logical step ≈ one todo. The count emerges from the journey's actual steps; do not target a number. Bash plumbing inside a step (registry lookups, JSON parsing, intermediate file reads) is invisible — do not surface as todos. See [shared/ux-narration-and-todos.md](references/shared/ux-narration-and-todos.md) for granularity rules, threshold table, and pivot rules.
9. **Every node has exactly one author — Edit/Write or CLI, never both.** Connector activities (`uipath.connector.<key>.<op>`), connector triggers (`uipath.connector.trigger.<key>.<trigger>`), wait for events (`uipath.connector.event.<key>.<event>` — a mid-flow event wait, configured exactly like a trigger), and managed HTTP (`core.action.http.v2`) are CLI-owned — use `uip maestro flow node add` + `uip maestro flow node configure`. Every other node type — triggers, control flow, logic, HITL, patterns, agents, resource nodes, queue — is user-owned: author the `.flow` JSON directly with `Edit` / `Write`. `inputs.detail` on CLI-owned nodes is a `=jsonString:essentialConfiguration` envelope that the validator rejects when hand-authored. Inline-agent CLI is limited to agent project lifecycle (`uip agent init / validate / migrate --inline-in-flow`); the `uipath.agent.autonomous` flow node itself is user-owned. Scripting languages (`python`, `node`, `jq`, `sed`, `awk`, inline shell heredocs) are a last resort for user-owned edits and require explicit user approval after the trade-offs (state bypass, opaque diff, no interruption point) are surfaced. **Canonical source of truth:** [author/CAPABILITY.md — Node ownership](references/author/CAPABILITY.md#node-ownership--who-authors-the-node) (full table); [author/editing-operations.md — Tool Selection Ladder](references/author/references/editing-operations.md#tool-selection-ladder) (per-operation ladder).

## Anti-patterns (universal)

- **Never use `--format json` on any `uip` command** — the flag is `--output json` (rule #1). `--format` produces `error: unknown option '--format'` and exit code 3 on every `uip` subcommand, not a helpful message pointing you at `--output`.
- **Never run `flow debug` as a validation step** — debug executes the flow with real side effects (rule #2). Use `flow validate` for checking correctness.
- **Never silently pick the first match from `uip maestro flow registry search`.** When a search returns multiple connectors for the same intent, apply the canonical Connector Disambiguation ladder via [connector/planning.md — Disambiguation](references/author/references/plugins/connector/planning.md#disambiguation--when-search-returns-multiple-connectors-for-the-same-intent), which defers to the Integration Service rules.
- **Never write `customFieldsRequestDetails.parameterValues` as a JSON object map** — Studio Web's TS port emits `Map<string,string|null>` via `Array.from(entries())`, so the on-wire shape is `[[key, value], ...]` tuples. Object-form `{key: value}` is rejected by the CLI at validate time. Inner keys are camelCase (`objectActionName`, `parameterValues`), not PascalCase. See [connector/impl.md Step 6c](references/author/references/plugins/connector/impl.md).

> **Trouble?** If something didn't work as expected, use `/uipath-feedback` to send a report.
