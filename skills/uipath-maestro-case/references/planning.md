# Phase 1 — Planning: sdd.md → tasks.md

Generate reviewable task plan (`tasks.md`) from design document (`sdd.md`). Discovers registry resources, resolves task type IDs, produces declarative specification that downstream execution phases (Phase 2 Prototyping → Phase 3 Implementation → Phase 4 Validate → Phase 5 Debug → Phase 6 Publish) consume via direct JSON writes to `caseplan.json`. See [implementation.md](implementation.md) for execution detail and [phased-execution.md](phased-execution.md) for phase contracts.

> **Output:** `tasks/tasks.md` + `tasks/registry-resolved.json` in the same directory as the sdd.md file.
>
> **Exit gate:** User must explicitly approve `tasks.md` before Phase 2 begins.

> **Per-node-type detail lives in plugins.** This document covers the cross-cutting planning workflow. For how to fill fields for a specific node, consult the relevant plugin:
> - Root case → `plugins/case/planning.md`
> - Stages (regular / exception) → `plugins/stages/planning.md`
> - Edges → `plugins/edges/planning.md`
> - Tasks → `plugins/tasks/<type>/planning.md`
> - Triggers → `plugins/triggers/<type>/planning.md`
> - Conditions → `plugins/conditions/<scope>/planning.md`
> - SLA → `plugins/sla/planning.md`
> - Global variables & arguments → `plugins/variables/global-vars/planning.md`
> - Task I/O binding → `plugins/variables/io-binding/planning.md`

---

## Step 0 — Resolve the `uip` binary

`uip` is installed via npm. Resolve the binary (it may not be on PATH in nvm environments), capture its version, and upgrade only when the installed version is **older** than the latest published `@uipath/cli` — dev builds may be newer than the npm release, leave those alone:

```bash
UIP=$(command -v uip 2>/dev/null || echo "$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip")
CURRENT=$($UIP --version 2>/dev/null | awk '{print $NF}')
LATEST=$(npm view @uipath/cli version 2>/dev/null)
OLDEST=$(printf '%s\n%s\n' "$LATEST" "$CURRENT" | sort -V | head -n1)
if [ -z "$CURRENT" ] || { [ "$CURRENT" != "$LATEST" ] && [ "$OLDEST" = "$CURRENT" ]; }; then
  npm install -g @uipath/cli@latest
  UIP=$(command -v uip 2>/dev/null || echo "$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip")
fi
$UIP --version
```

Use `$UIP` in place of `uip` for all subsequent commands if the plain `uip` command isn't found.

If `npm install -g` fails with a permission error, prompt the user to switch to a user-local installation method (for example, a Node version manager or a user-scoped npm prefix) rather than retrying with `sudo` — do not retry automatically.

## Step 1 — Check login and pull registry

Registry discovery happens during planning, so login is required first.

```bash
uip login status --output json
uip maestro case registry pull
```

If not logged in, prompt the user to log in. The registry pull caches all resources locally at `~/.uipcli/case-resources/` so subsequent searches are local disk lookups.

## Step 2 — Locate and parse the design document

Accept the `sdd.md` file path from the user, or ask if not provided. When the directory contains multiple `.md` files, use **AskUserQuestion** with the candidates + "Something else" to disambiguate.

If the resolved path has **no `sdd.md`**, skill enters Phase 0 (interview mode) before this step. See [phase-0-interview.md](phase-0-interview.md). Phase 1 resumes here only after Round 4 approval.

`sdd.md` is the **sole input**. It describes stages, tasks, edges, conditions, SLA, component types, persona information, and provides the search keywords for registry lookups. The skill does not validate or gap-fill sdd.md — trust it as written. (Phase 0 may have generated it; once approved, Rule 2 applies regardless of source.)

> **Phase 0 carryover.** When Phase 0 ran, `tasks/registry-resolved.json` already contains user-confirmed registry picks. During Step 3 below, **read the existing file first**: skip re-search for entries already resolved, only run discovery for tasks Phase 0 deferred (`<UNRESOLVED>` markers in `sdd.md`). Append new resolutions to the same file.

## Step 3 — Resolve resources

For every task, trigger, and condition in the sdd.md:

1. **Identify the plugin** by matching the sdd.md component description to an entry in the catalogs below (§3.1–§3.3).
2. **Load the plugin's `planning.md`** — it lists the exact fields to resolve from sdd.md, the cache file(s) to consult, and any discovery steps required.
3. **Apply registry discovery** via [registry-discovery.md](registry-discovery.md) when a taskTypeId is needed.
4. **Persist every resolution** to `registry-resolved.json` (search query, all matched results, selected result, rationale). Keep full detail for debugging.

### 3.1 Task Type catalog

> **Closed enum — 9 values.** sdd.md `Type:` and caseplan.json `type` field both use the schema-kebab values in column 1. Plugin folder name (column 2) is what to open during planning + execution; it is NOT what gets written into JSON. See SKILL.md Rule 16 + Plugin Index naming-asymmetry note. Any value outside this set (`external-agent`, `connector-activity`, `wait-for-event`, etc.) is invalid — write a `<UNRESOLVED>` skeleton instead.

| sdd.md `Type:` / caseplan.json `type` | Plugin folder |
|---|---|
| `process` (covers `AGENTIC_PROCESS` legacy label) | `plugins/tasks/process/` |
| `agent` | `plugins/tasks/agent/` |
| `rpa` | `plugins/tasks/rpa/` |
| `action` | `plugins/tasks/action/` |
| `api-workflow` | `plugins/tasks/api-workflow/` |
| `case-management` | `plugins/tasks/case-management/` |
| `execute-connector-activity` | `plugins/tasks/connector-activity/` |
| `wait-for-connector` | `plugins/tasks/connector-trigger/` |
| `wait-for-timer` | `plugins/tasks/wait-for-timer/` |

### 3.2 Trigger Type catalog (case-level)

| sdd.md description | Plugin |
|--------------------|--------|
| "Start manually" / "User initiates" | `plugins/triggers/manual/` |
| "Every N hours/days" / scheduled / cron-like | `plugins/triggers/timer/` |
| Event from external system (connector-based) | `plugins/triggers/event/` |

### 3.3 Condition Scope catalog

| Where the condition attaches | Plugin |
|------------------------------|--------|
| On stage entry | `plugins/conditions/stage-entry-conditions/` |
| On stage exit | `plugins/conditions/stage-exit-conditions/` |
| On task entry | `plugins/conditions/task-entry-conditions/` |
| On case exit | `plugins/conditions/case-exit-conditions/` |

### 3.4 Unresolved resources

When a resource cannot be resolved (registry gap and no cache match, or missing connection), **do not fabricate a placeholder or mock**. Instead:

1. Mark the line in `tasks.md` with `<UNRESOLVED: <reason>>` in the `taskTypeId` / `typeId` / `connectionId` slot.
2. **Omit `inputs:` and `outputs:` entirely** on that task entry — there is no schema to wire against. Any input mapping the sdd.md described becomes a fenced ```` ```text ```` code block under the entry with a `wiring notes (user must attach):` header line. **Do not start lines with `#`** — they would render as markdown headings; use a fenced code block instead. Example shape is in [skeleton-tasks.md § `tasks.md` Planning-Entry Shape](skeleton-tasks.md).
3. Keep every other structural field (display-name, isRequired, runOnlyOnce, order). Task-entry conditions still emit normally.
4. **Continue planning — do not halt.**

At execution time, unresolved tasks become **skeleton tasks** in `caseplan.json` (display-name + type only, no task-type-id, no bindings). The workflow graph is still reviewable end-to-end, and the user attaches real resources + bindings externally before runtime. See [skeleton-tasks.md](skeleton-tasks.md).

## Step 4 — Generate tasks.md and registry-resolved.json

Create a `tasks/` folder adjacent to the sdd.md file. Generate `tasks.md` using the structure below. Each section is a numbered task (`T01`, `T02`, …) — declarative parameters only. Field names use plain identifiers (e.g., `type:`, `displayName:`, `lane:`), not CLI flag syntax. The implementation phase translates each entry into the matching plugin's JSON writes.

Cross-reference: [case-schema.md](case-schema.md) for JSON shape, [bindings-and-expressions.md](bindings-and-expressions.md) for inputs/outputs wiring.

Also write `registry-resolved.json` — full detail per task: search query, all matches, selected entry, rationale.

### 4.0 Completeness principle (no omissions)

Every declaration in `sdd.md` must become a T-task in `tasks.md`. Mapping is 1-to-1:

- **Never filter** declarations on the grounds that the default rule-type, default field value, or "implicit behavior" would cover them. If `sdd.md` lists a task, stage, edge, trigger, condition, SLA row, **variable, or argument**, `tasks.md` emits a T-task for it — regardless of rule-type (`current-stage-entered`, `case-entered`, `exit-only`, `required-tasks-completed`, etc.).
- **Never merge** two sdd.md items into one T-task "because they're similar."
- **Never drop** defaults-looking items (e.g., `is-interrupting: false`, `runOnlyOnce: true`, `marks-stage-complete: true`). The explicit declaration is the signal — honor it.
- **When in doubt, emit.** It is always correct to create a T-task that mirrors an sdd.md row. It is never correct to silently omit one.
- **When format is ambiguous or unrecognized, ASK — do not skip.** If a row exists but you cannot determine the right plugin, category, or T-entry shape (e.g., trigger "Initial Variable Mapping" uses an aggregate phrase instead of explicit per-field mappings; a variable's category — In / Out / Variable — is unclear; a task type does not match the closed enum), invoke **AskUserQuestion** with the row content + the specific ambiguity + bounded options. Silent omission is a defect. This obligation applies to every sdd.md declaration class above, including variables and arguments.

Before presenting `tasks.md` at Step 5, run a completeness cross-check: for every declared stage / edge / task / trigger / condition / SLA row **and every Case Variables table row (one T-entry each, per §4.2.1)** in sdd.md, verify a corresponding T-task exists. Gaps are a defect — fix before approval.

**Cross-check inventory.** Before approval, count and report each class:

| Class | Source in sdd.md | T-entry section |
|---|---|---|
| Case file | Case Metadata | §4.2 (T01) |
| Triggers | Case Triggers | §4.3 (T02+) |
| Variables / arguments | Case Variables | §4.2.1 (after last trigger) |
| Stages | Section 2 stage headings | §4.4 |
| Edges | Stage Entry Conditions / Stage Exit Conditions referencing other stages | §4.5 |
| Tasks | Per-stage Tasks tables | §4.6 |
| Conditions | Stage Entry / Stage Exit / Task Entry / Case Exit tables | §4.7 |
| SLA | Case-Level SLA + per-stage Stage SLA + per-action Task SLA | §4.8 |

Counts that don't match the sdd.md → fix before Step 5 hard stop.

### 4.1 Task ordering

Always in this order: stages → edges → tasks → conditions → SLA.

The task **title IS the action description** — do not add a redundant `what` or `type` field. Absorb type into the title (e.g., `Add api-workflow task "..."` not `Add task` + `type: api-workflow`).

### 4.2 Create case file (T01)

Title format: `Create case file "<name>"`

Consult [`plugins/case/planning.md`](plugins/case/planning.md) for required fields (name, file path, case-identifier, identifier-type, case-app-enabled, description). Source all fields from sdd.md.

### 4.2.1 Declare global variables and arguments

Title format: `Declare <category> "<name>"` where category is `In argument`, `Out argument`, or `variable`.

One T-entry per variable or argument from the sdd.md "Case Variables" table. Place these after the case file (T01) and **all** trigger T-entries (T02+) — i.e., after the last trigger row, before stages. In multi-trigger cases the variables block starts at `T0<last-trigger>+1`, not at `T03`. Consult [`plugins/variables/global-vars/planning.md`](plugins/variables/global-vars/planning.md) for the SDD-to-category mapping rules and entry format.

Task-output variables (produced by tasks during execution) do NOT get T-entries here — they are wired automatically during task creation (§4.6).

### 4.3 Configure trigger(s) (T02+)

Title format: `Configure <trigger-type> trigger "<name>"`

Consult the corresponding trigger plugin (`plugins/triggers/<type>/planning.md`) for required fields.

**One T-entry per trigger row in sdd.md.** A case with N entry-point rows in its triggers table emits N trigger T-entries (T02, T03, …) — even when several rows would resolve to `<UNRESOLVED>` because the IS connection isn't provisioned. Per §4.0, "value can't be resolved yet" is not a reason to omit a row; it's a reason to mark `<UNRESOLVED: …>` and continue. See [edges/planning.md § Multi-Trigger Cases](plugins/edges/planning.md#multi-trigger-cases) for the matching N edges from triggers to the first stage.

Each trigger row uses its plugin's full field set — see `plugins/triggers/<type>/planning.md` for the per-type entry format. Worked example — sdd.md declares 3 entry-point rows (one manual + two events), one of which is unresolved:

```markdown
## T02: Configure manual trigger "Operator Starts Case"
- display-name: "Operator Starts Case"
- description: "Operator kicks off a case from the portal"
- order: after T01
- verify: Confirm node appended; capture TriggerId

## T03: Configure event trigger "New Inbound Email"
- type-id: <uiPathActivityTypeId>
- connection-id: <connection-uuid>
- connector-key: uipath-microsoft-office-365-outlook
- object-name: Email
- event-operation: created
- event-mode: webhooks
- input-values: {"parentFolderId": "AAMkADNm..."}
- filter: "(contains(subject, 'urgent'))"
- order: after T02
- verify: Confirm trigger configured with correct event parameters

## T04: Configure event trigger "Jira Issue Created"
- type-id: <UNRESOLVED: no IS connection for uipath-atlassian-jira>
- connection-id: <UNRESOLVED>
- connector-key: <UNRESOLVED>
- object-name: <UNRESOLVED>
- event-operation: <UNRESOLVED>
- event-mode: <UNRESOLVED>
- order: after T03
- verify: trigger skipped at execution; user attaches after registering connection
```

Do **not** collapse the unresolved trigger into a note on T02 or omit it entirely — execution behavior for unresolved event triggers is documented in [`triggers/event/planning.md § Unresolved Fallback`](plugins/triggers/event/planning.md#unresolved-fallback), but the planning row is still required.

### 4.4 Create stages

Title format: `Create stage "<name>"` or `Create exception stage "<name>"`

One task per stage. Consult [`plugins/stages/planning.md`](plugins/stages/planning.md) for required fields and the `stage` vs `exception` (a.k.a. secondary) decision. Basic properties only — SLA and escalation come later (§4.7).

### 4.5 Setup edges

Title format: `Add edge "<source>" → "<target>"`

One task per edge. Consult [`plugins/edges/planning.md`](plugins/edges/planning.md) for required fields (source, target, label, handles) and the orphan check.

### 4.6 Add tasks

Title format: `Add <type> task "<name>" to "<stage>"`

One task per task from the sdd.md — do NOT group multiple tasks under a single T-number. The plugin for the task's type (`plugins/tasks/<type>/planning.md`) lists exactly which fields to record.

Every task entry includes at least:

- **taskTypeId** — resolved from the registry in Step 3
- **inputs** / **outputs** — see [bindings-and-expressions.md](bindings-and-expressions.md) for the two input modes (literal/expression and cross-task reference)
- **runOnlyOnce** — from sdd.md (default `true` if not specified)
- **isRequired** — from sdd.md (default `true` if not specified)
- **order** — dependency on previous tasks (`after T05`, etc.)
- **lane** — FE layout coordinate (integer, increments per task within the stage starting at 0)
- **verify** — what the execution phase should check after running

Additional fields are plugin-specific; read the plugin's `planning.md` before filling the entry.

> **No shell commands in task entries.** Each task is a declarative specification. Never write `uip` invocations or any other shell commands inside a task body — the execution phase translates specs into JSON mutations.

> **Record `lane: <n>` per task** (incrementing within each stage, starting at 0). Lane is a FE layout coordinate with no execution semantics — task ordering and parallelism are expressed via task-entry conditions, not lanes.

> **Skeleton shape for unresolved resources.** If `taskTypeId` / `typeId` / `connectionId` is `<UNRESOLVED: …>`, omit `inputs:` and `outputs:` entirely and capture wiring intent in a trailing comment block. Execution creates a bare task node — structural only. See [skeleton-tasks.md](skeleton-tasks.md) for the full pattern and upgrade path.

### 4.7 Configure conditions

One task per condition. Order within §4.7: stage entry → stage exit → case exit → task entry.

Title format: `Add <scope> condition for "<target>"`

For per-scope fields, consult the corresponding condition plugin:
- `plugins/conditions/stage-entry-conditions/planning.md`
- `plugins/conditions/stage-exit-conditions/planning.md`
- `plugins/conditions/task-entry-conditions/planning.md`
- `plugins/conditions/case-exit-conditions/planning.md`

### 4.8 Set SLA and escalation rules

SLA comes last. Consult [`plugins/sla/planning.md`](plugins/sla/planning.md) for the three sub-operations (default SLA, conditional SLA rules, escalation rules), per-target ordering, and the constraint that conditional SLA rules are root-only.

### 4.9 Not Covered section

Add a brief section at the end of `tasks.md` listing things referenced in sdd.md but outside the scope of `caseplan.json` (e.g., Data Fabric entity schemas). These stay as notes for the user.

---

## Step 5 — HARD STOP: User reviews and approves tasks.md

Present the generated `tasks.md` to the user and ask for explicit approval before proceeding.

Use **AskUserQuestion** with options: `Approve and proceed`, `Request changes`.

If user requests changes, update `tasks.md` and re-present. Do NOT proceed to Phase 2 until user explicitly approves.

**After approval:** re-read `tasks.md` before proceeding to Phase 2 (see [implementation.md](implementation.md)). `tasks.md` is complete handoff artifact — all resolved IDs, inputs, outputs, and references captured there.
