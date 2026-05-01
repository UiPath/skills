---
name: uipath-maestro-flow
description: "UiPath Maestro Flow (.flow) — read, edit, author, debug. `uip` CLI: nodes, edges, subflows, scripts, variables, triggers, End nodes, registry. For C#/XAML→uipath-rpa. For agents→uipath-agents."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath Flow Skill

Comprehensive guide for creating, editing, validating, debugging, publishing, and diagnosing UiPath Flow projects using the `uip` CLI and `.flow` file format. The skill is organized into three capabilities — **Author**, **Operate**, **Diagnose** — each with its own index doc.

## When to use this skill

**Author** — building or editing a `.flow` file. Read [references/author/CAPABILITY.md](references/author/CAPABILITY.md).

- Create a new Flow project (`uip maestro flow init`)
- Edit a `.flow` file — add nodes, edges, variables, subflows, transforms, triggers
- Explore available node types via the registry
- Validate or tidy a Flow file locally
- Choose between Edit / Write and CLI editing strategies
- Configure connector, connector-trigger, or inline-agent nodes
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

## Capability router

| I want to...                                                 | Read                                                                                             |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| Create a new flow or edit an existing one                    | [references/author/CAPABILITY.md](references/author/CAPABILITY.md)                               |
| Publish, deploy, debug, or manage a flow's lifecycle         | [references/operate/CAPABILITY.md](references/operate/CAPABILITY.md)                             |
| Diagnose a failed or misbehaving flow run                    | [references/diagnose/CAPABILITY.md](references/diagnose/CAPABILITY.md)                           |
| Look up CLI command syntax                                   | [references/shared/cli-commands.md](references/shared/cli-commands.md)                                   |
| Look up CLI conventions (`--output json`, login, FOLDER_KEY) | [references/shared/cli-conventions.md](references/shared/cli-conventions.md)                     |
| Understand the `.flow` JSON format                           | [references/shared/file-format.md](references/shared/file-format.md)                             |
| Understand variables and `=js:` expressions                  | [references/shared/variables-and-expressions.md](references/shared/variables-and-expressions.md) |
| Wire one node's output into another node's input             | [references/shared/node-output-wiring.md](references/shared/node-output-wiring.md)               |
| Narrate progress to the user + maintain todos                | [references/shared/ux-narration-and-todos.md](references/shared/ux-narration-and-todos.md)       |

## Critical rules (universal)

These rules apply across all three capabilities. Each capability index adds capability-scoped rules on top.

1. **ALWAYS use `--output json`** on all `uip` commands when parsing output programmatically.
2. **Do NOT run `flow debug` without explicit user consent** — debug executes the flow for real (sends emails, posts messages, calls APIs).
3. **Resource discovery order — search before creating.** When the prompt references an existing resource by name ("use the X agent", "call the Y API workflow", "invoke the Z RPA process"), follow this order strictly before deciding the resource doesn't exist:
   1. **Tenant registry search** — `uip maestro flow registry search "<name>" --output json`. Requires `uip login`; returns published resources.
   2. **In-solution local discovery** — `uip maestro flow registry list --local --output json`. No login required; returns sibling projects in the same `.uipx` solution.
   3. **Only then create/scaffold** — scaffold an inline agent, mock, or create-new-resource only when both searches return no match AND either the user explicitly asks to embed/inline/create, or no published resource can satisfy the requirement.

   The words "coded" and "low-code" describe the _implementation style_ of a published agent — they are NOT synonyms for "inline". `uipath.agent.autonomous` (inline) is only correct when the user explicitly asks to embed/inline/create a new agent inside this flow. `node add` auto-falls back to local discovery when a node type is not found in the cached registry. Only use `core.logic.mock` when the resource is **not** in the same solution and not yet published. See the relevant resource plugin's `impl.md` (e.g., [rpa](references/author/references/plugins/rpa/impl.md), [agent](references/author/references/plugins/agent/impl.md)).

4. **Never invoke other skills automatically** — when a flow needs an RPA process, agent, or app, identify the gap and provide handoff instructions. Let the user decide when to switch skills.
5. **Always present user questions as a dropdown with a "Something else" escape hatch** — Whenever this skill needs a decision from the user (which solution to use, publish vs debug vs deploy, which connector to pick, which trigger type, which resource to bind, etc.), use the `AskUserQuestion` tool with the enumerated choices as options AND include **"Something else"** as the last option so the user can supply free-form string input. Never ask open-ended questions in chat when a finite set of sensible defaults exists. If the user picks "Something else", parse their string answer and continue.
6. **A Flow project MUST live inside a solution** — always scaffold the solution first (`uip solution new <Name>`), then `cd <Name>` and run `uip maestro flow init <Name>`. The correct layout is **always** `<Solution>/<Project>/<Project>.flow` (double-nested). Running `uip maestro flow init` in a bare directory produces a single-nested `<Project>/<Project>.flow` layout that fails Studio Web upload, packaging, and downstream tooling. See [author/greenfield.md](references/author/references/greenfield.md) Step 2.
7. **Always narrate progress in plain English at each logical step boundary.** One short line per step, in user terms ("checking your tenant login", "adding the Slack node and wiring its inputs", "editing the flow JSON to add the new variable", "running validate") — no flag-level or JSON-structure-level detail. Applies uniformly to `uip` CLI calls, shell builtins (`ls`, `cat`, `cd`, `mkdir`, `find`, `grep`), file edits (Read/Write/Edit), and bulk searches (Glob/Grep). The user should never need to know `bash`, `uip` flags, or `.flow` JSON internals to follow along. See [shared/ux-narration-and-todos.md](references/shared/ux-narration-and-todos.md).
8. **Use `TodoWrite` for any journey above the trivial threshold; keep granularity per-step, not per-phase.** Standard journeys (greenfield, brownfield with multiple nodes, ship, run, full diagnose) require a granular todo list (~15–25 items). One logical step ≈ one todo. Bash plumbing inside a step (registry lookups, JSON parsing, intermediate file reads) is invisible — do not surface as todos. See [shared/ux-narration-and-todos.md](references/shared/ux-narration-and-todos.md) for granularity rules, threshold table, and pivot rules.
9. **Never use a scripting language (`python`, `node`, `jq`, `sed`, `awk`, inline shell heredocs) to mutate a `.flow` file, `bindings_v2.json`, or any other file under a Flow project.** Allowed mutation tools: `Edit`, `Write`, `uip maestro flow node {add,delete,configure}`, `uip maestro flow edge {add,delete}`, `uip maestro flow variable {add,...}`. Reading with `cat`, `jq`, or a Python one-liner is fine when output is parsed. **Mutating is not.** Scripted mutations bypass the CLI's auto-managed `definitions[]` / `variables.nodes` / layout state and produce opaque diffs that are not reviewable line-by-line. If a mutation feels too coordinated for a sequence of `Edit` calls, use `Write` for a wholesale rewrite (only when ≥70% of nodes change) or stop and ask the user — do not reach for a scripting language. See [author/editing-operations.md — Tool Selection Ladder](references/author/references/editing-operations.md#tool-selection-ladder) for the per-operation tool ladder and the rationale.

## Anti-patterns (universal)

- **Never use `--format json` on any `uip` command** — the flag is `--output json` (rule #1). `--format` produces `error: unknown option '--format'` and exit code 3 on every `uip` subcommand, not a helpful message pointing you at `--output`.
- **Never run `flow debug` as a validation step** — debug executes the flow with real side effects (rule #2). Use `flow validate` for checking correctness.

> **Trouble?** If something didn't work as expected, use `/uipath-feedback` to send a report.
