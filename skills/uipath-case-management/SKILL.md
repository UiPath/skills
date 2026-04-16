---
name: uipath-case-management
description: "[PREVIEW] Case Management authoring (sdd.md → tasks.md → caseplan.json). Resolves registry taskTypeIds, generates task plans, executes uip case CLI. For .xaml→uipath-rpa, for .flow→uipath-flow."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Case Management Authoring Assistant

End-to-end guide for creating UiPath Case Management definitions. Takes a design document (sdd.md), generates a reviewable task plan (tasks.md), and executes the plan via the `uip case` CLI.

## When to Use This Skill

- User asks to create a case management project or definition
- User asks to generate implementation tasks from an sdd.md
- User asks to break down a case spec into tasks or plan case tasks from sdd
- User asks to create a tasks.md from spec or interpret case spec
- User asks to convert a spec to an implementation plan
- User provides an sdd.md and wants a case built from it
- User is editing an existing case JSON file — adding stages, tasks, edges, or properties
- User wants to manage runtime case instances (list, pause, resume, cancel)
- User asks about the case management JSON schema — nodes, edges, tasks, rules, SLA

## Critical Rules

1. **Always regenerate tasks.md from scratch** — never do incremental updates to an existing tasks.md. This avoids stale state from previous runs.
2. **Run `uip case registry pull` before any interpretation** — pulling the registry cache upfront avoids network failures partway through.
3. **tasks.md entries are declarative specifications** — no `uip` CLI commands in tasks.md. Each task entry contains parameters, IDs, and metadata only. The execution phase translates specs into CLI calls.
4. **Follow every step as written — do not skip or shortcut** — the procedures exist because previous shortcuts caused failures. Do not skip registry lookups based on assumptions.
5. **Best effort on registry failures** — if a lookup fails, mark it as `[REGISTRY LOOKUP FAILED: <keywords>]` and continue. Do not abort the entire run.
6. **One task per T-number** — do not group multiple sdd.md tasks under a single T-number.
7. **Max 2 registry refresh retries** — if `registry pull --force` still yields no match after 2 retries, mark the lookup as failed and move on.
8. **Ask the user when login fails** — if `uip login status` shows not logged in, prompt the user to run `uip login` and stop until they confirm.
9. **Every stage needs at least one edge** connecting it to the case or it will be orphaned.
10. **Trigger node is created automatically** on `cases add` — don't add another unless it's a separate entry point (e.g. for a multi-trigger case).
11. **Tasks are 2D arrays**: `tasks[lane][index]` — use `--lane` to put tasks in parallel lanes.
12. **Edit `content/*.json` only** — `content/*.bpmn` is auto-generated and will be overwritten.
13. **Execute all commands in sequence. No parallel execution.**

## Workflow

This skill has two phases: **Planning** generates a reviewable tasks.md from the sdd.md. **Implementation** translates tasks.md into CLI commands and builds the case definition. There is a hard stop between them — do not proceed to implementation without explicit user approval.

---

### Phase 1 — Planning

**Read [references/planning.md](references/planning.md)** for the full planning process: resolve CLI, check login, pull registry, parse sdd.md, resolve task types, and generate tasks.md.

Follow the process in that guide to produce:
1. `tasks/tasks.md` — declarative task plan with T-numbered entries (stages → edges → tasks → conditions → SLA)
2. `tasks/registry-resolved.json` — registry lookup audit trail

Present tasks.md to the user for review.

**Do NOT proceed to Phase 2 until the user explicitly approves tasks.md.**

### Phase 2 — Implementation

**Read [references/implementation.md](references/implementation.md)** for the full implementation process.

Phase 2 takes the approved tasks.md and executes it:
1. Create case project structure (solution + project + case file)
2. Add stages, edges, tasks, conditions, SLA
3. Bind variables and wire cross-task references
4. Validate the case file
5. Optionally debug or publish to Studio Web

Execute each task from tasks.md in order, translating declarative specifications into `uip case` CLI commands. Capture IDs returned by each command and use them in subsequent steps.

**After the user approves tasks.md:** run `/compact` to free context, then re-read `tasks.md` before proceeding. The tasks.md file is the complete handoff artifact between the two phases.

## Anti-patterns — What NOT to Do

- Do NOT put `uip case ...` CLI commands in tasks.md — causes double-execution or mis-parsing. tasks.md is declarative only.
- Do NOT incrementally update an existing tasks.md — always regenerate from scratch to avoid stale state.
- Do NOT skip registry lookups based on assumptions like "this type is not discoverable." Always search the cache files first.
- Do NOT group multiple sdd.md tasks under one T-number — each task in the sdd.md gets its own numbered entry.
- Do NOT fabricate expression syntax for conditional SLA rules — describe the condition in natural language; the execution phase determines the correct expression format.
- Do NOT add interactive checkpoints during tasks.md generation — run silently and let the user review the output after completion.
- Do NOT include parameters the CLI does not support — only include what `uip case` can act on (see [CLI command reference](references/case-commands.md)).
- Do NOT use lane assignments in tasks.md — the lane concept is no longer used for managing parallelism in the planning phase.
- Do NOT edit `.bpmn` files — they are auto-generated and will be overwritten.
- Do NOT run debug automatically — it has real side effects (sends emails, calls APIs, writes to databases).
- Do NOT execute commands in parallel — run all CLI commands sequentially.
- Do NOT fabricate input or output names in cross-task references — run `uip case tasks describe` to discover actual input/output names from the task's schema.

## Reference Navigation

| I need to... | Read these |
|---|---|
| **Plan tasks from sdd.md** | [references/planning.md](references/planning.md) |
| **Execute tasks.md into a case** | [references/implementation.md](references/implementation.md) |
| **Understand the case JSON schema** | [references/case-schema.md](references/case-schema.md) |
| **Know all CLI commands** | [references/case-commands.md](references/case-commands.md) |
| **Resolve task types from registry** | [references/registry-discovery.md](references/registry-discovery.md) |
| **Connect stages** | [references/implementation.md](references/implementation.md) Step 8 + [references/case-schema.md — Edges](references/case-schema.md) |
| **Add a task to a stage** | [references/implementation.md](references/implementation.md) Step 9 + [references/case-commands.md](references/case-commands.md) |
| **Find available processes/agents** | Run `uip case registry pull` then `uip case registry list` |

## Key Concepts

### Local vs cloud commands

| Commands | What they do | Auth needed |
|---------|-------------|-------------|
| `uip case cases`, `stages`, `tasks`, `edges` | Edit local JSON definition files | No |
| `uip case instance`, `processes`, `incidents` | Query/manage live Orchestrator data | Yes |

### CLI output format

All `uip case` commands return structured JSON:
```json
{ "Result": "Success", "Code": "StageAdded", "Data": { ... } }
{ "Result": "Failure", "Message": "...", "Instructions": "..." }
```

Use `--output json` for programmatic use.
