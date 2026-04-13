---
name: uipath-case-task-planner
description: "[PREVIEW] Case spec interpreter (sdd.md + spec.json → tasks.md). Resolves registry taskTypeIds and generates ordered CLI commands for uip case. For direct case editing→uipath-case-management."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Case Task Planner

Convert a case design document (sdd.md) into a tasks.md file that an implementation agent can follow to build the case definition using the `uip case` CLI.

## When to Use This Skill

- User asks to "generate implementation tasks from a case spec"
- User asks to "break down a case spec into tasks" or "plan case tasks from sdd"
- User asks to "create a tasks.md from spec" or "interpret case spec"
- User asks to "convert spec to implementation plan"
- Another skill needs to convert a case design document (sdd.md) into a step-by-step implementation plan for the `uip case` CLI

> **Not this skill:** For directly editing case JSON files or running `uip case` commands, use `uipath-case-management` instead.

## Critical Rules

1. **Always regenerate tasks.md from scratch** — never do incremental updates to an existing tasks.md. This avoids stale state from previous runs.
2. **Run `uip case registry pull` before any interpretation** — pulling the registry cache upfront avoids network failures partway through.
3. **No `uip` CLI commands in tasks.md** — tasks.md is a declarative specification. Each task entry contains parameters, IDs, and metadata only. The implementation agent (uipath-case-management skill) translates specs into CLI calls.
4. **Follow every step as written — do not skip or shortcut** — the procedures exist because previous shortcuts caused failures. Do not skip registry lookups based on assumptions.
5. **Best effort on registry failures** — if a lookup fails, mark it as `[REGISTRY LOOKUP FAILED: <keywords>]` and continue. Do not abort the entire run.
6. **One task per T-number** — do not group multiple sdd.md tasks under a single T-number.
7. **Max 2 registry refresh retries** — if `registry pull --force` still yields no match after 2 retries, mark the lookup as failed and move on.
8. **Ask the user when login fails** — if `uip login status` shows not logged in, prompt the user to run `uip login` and stop until they confirm.

## Overview

The user (or another skill) has already designed a case — they have a semantic design document (sdd.md) that describes the case in plain language, including its stages, tasks, edges, rules, SLA, and component types. This skill bridges the gap between "design" and "implementation" by producing a concrete, ordered list of CLI commands with all the registry lookups already resolved.

## Step 0 -- Resolve the uip binary

The uip CLI is installed via npm. In nvm environments it may not be on PATH, so resolve it first:

```bash
UIP=$(command -v uip 2>/dev/null || echo "$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip")
$UIP --version
```

Use `$UIP` in place of `uip` for subsequent commands if the plain `uip` command is not found.

## Step 1 -- Check login and pull registry

Registry discovery happens during interpretation, so login is required before starting.

```bash
uip login status --output json
uip case registry pull
```

If not logged in, prompt the user to log in first. The registry pull caches all resources locally so that subsequent searches are local disk lookups with no network failures mid-interpretation.

## Step 2 -- Locate and parse the design document

Accept the sdd.md file path from the user, or ask if not provided.

- **sdd.md** -- the semantic design document. This is the sole input: it describes stages, tasks, edges, rules, SLA, component types, persona information, and provides the search keywords for registry lookups.

Parse sdd.md as the single source of truth for the case design.

## Step 3 -- Resolve task types via registry

For each task in the sdd.md, determine the correct `taskTypeId` by reading the local registry cache files directly. After `registry pull` (Step 1), all resources are cached at `~/.uip/case-resources/`. Search these files instead of using CLI search commands — it is more reliable and faster.

### Component type mapping

This table maps sdd.md component types to the primary cache file to search and the CLI `--type` flag:

| component_type | Primary cache file | CLI tasks add --type |
|---|---|---|
| API_WORKFLOW | `api-index.json` | api-workflow |
| AGENTIC_PROCESS | `processOrchestration-index.json` | process |
| HITL | `action-apps-index.json` | action |
| RPA | `process-index.json` | rpa |
| AGENT | `agent-index.json` | agent |
| CASE_MANAGEMENT | `caseManagement-index.json` | case-management |
| CONNECTOR_ACTIVITY | `typecache-activities-index.json` | execute-connector-activity |
| CONNECTOR_TRIGGER | `typecache-triggers-index.json` | wait-for-connector |
| EXTERNAL_AGENT | *(not in cache)* | external-agent |
| TIMER | *(not in cache)* | wait-for-timer |
| PROCESS | `process-index.json` | process |

For types marked "not in cache" (`EXTERNAL_AGENT`, `TIMER`), use the `--type` value directly without searching.

For all other types, follow the procedure in the [registry-discovery reference](references/registry-discovery.md):

1. **Search the primary cache file** by matching the task name and folder path from the sdd.md.
2. **If no match in the primary file**, search all other cache files — the sdd.md component type label may not match the actual registry type (e.g., an "RPA" task may be registered as `process`).
3. **Pick the best match** using exact name + folder path from sdd.md Process References.
4. **Force-refresh and retry** (`uip case registry pull --force`) only if no match is found across all cache files.
5. **Extract the correct identifier field** per cache file type (`entityKey`, `id`, or `uiPathActivityTypeId`).
6. For **connector tasks** (typecache-activities, typecache-triggers), also run `get-connector` and `get-connection` CLI commands to collect full details.

Collect all registry results for the debug output in Step 5.

## Step 4 -- Generate tasks.md

Create a `tasks/` folder in the same directory as the sdd.md file. Generate `tasks.md` using the structure below. Each section is a numbered task (T01, T02, ...) that maps to one or more CLI commands.

Read the [CLI command reference](references/case-commands.md) and the [case JSON schema reference](references/case-schema.md) to understand the available flags and data structures as you generate each task.

### Task structure

The task ordering follows the `uipath-case-management` skill's implementation steps: stages → edges → tasks → conditions → SLA. The task title IS the action description — do not add a redundant `what` or `type` field. Absorb type into the title (e.g., "Add api-workflow task" not "Add task" + "type: api-workflow").

#### 1. Create case file (T01)

Title format: `Create case file "<name>"`

Set up the case definition with name, description, key prefix.

#### 2. Configure trigger (T02)

Title format: `Configure wait-for-connector trigger "<name>"`

For connector triggers, resolve via registry using `typecache-triggers` and include connection details from `get-connection` if applicable.

#### 3. Create stages (one per stage)

Title format: `Create stage "<name>"` or `Create exception stage "<name>"`

Each stage is its own task. Basic properties only — SLA and escalation come later (step 7). Each stage specifies:

- **isRequired** -- whether this stage must complete for the case to be considered complete (true/false). Determines which stages are tracked by `required-stages-completed` case exit conditions. Determine from the sdd.md using these criteria:
  - `true` — **Default for regular stages.** The stage is part of the main case flow and must complete before the case can close. Look for: stages on the happy path, stages described as mandatory, stages without "optional" or "exception" qualifiers.
  - `false` — Use for exception stages, optional review stages, or rework loops that the case can complete without entering. Look for: stages labeled as "exception", "optional", "fallback", "on-error", or stages that are only reached via conditional/interrupting entry conditions.

Example:
```
## T05: Create stage "PO Receipt & Triage"
- isRequired: true
- order: after T04
- verify: Confirm Result: Success, capture StageId

## T06: Create exception stage "Exception Handling"
- isRequired: false
- order: after T05
- verify: Confirm Result: Success, capture StageId
```

#### 4. Setup edges (one per edge)

Title format: `Add edge "<source>" → "<target>"`

One task per edge with human-readable condition labels.

#### 5. Add tasks (one per task)

Title format: `Add <type> task "<name>" to "<stage>"`

Each task from the sdd.md becomes its own numbered task. Do NOT group multiple tasks under a single T-number. Each task specifies:

- **taskTypeId** -- resolved from the registry in Step 3.
- **inputs** -- what data this task consumes, using human-readable cross-references in the format `"Stage Name"."Task Name".field_name`.
- **outputs** -- what data this task produces and where it is stored (e.g., `email_id -> CaseEntity.source_email_id`).
- **runOnlyOnce** -- whether the task should execute only once per case instance (true/false). Sourced from the sdd.md. Maps to CLI flag `--should-run-only-once`. Defaults to true if not specified in sdd.md.
- **isRequired** -- whether the task is required for stage completion (true/false). Sourced from the sdd.md. Maps to CLI flag `--is-required`. Defaults to true if not specified in sdd.md.
- **order** -- which task(s) must complete before this one runs (expressed as a dependency, e.g., "after T05").
- **verify** -- what the implementation agent should check after executing this task to confirm success.
- **recipient** -- for `action` tasks only: the email address of the assigned user, sourced from sdd.md. Omit if the sdd.md does not specify an assignee.
- **priority** -- for `action` tasks only: `Low`, `Medium`, `High`, or `Critical`, sourced from sdd.md (default: `Medium` if not specified).

> **No uip commands in task entries.** Each task is a declarative specification — parameters, IDs, and metadata only. Never write `uip case tasks add ...` or any shell command inside a task body. The implementation agent translates these specs into CLI commands.

> Ignore lane concept in creating the task. It is no longer feasible for managing the parallelism

Example (non-HITL):
```
## T25: Add api-workflow task "Monitor Order Inbox" to "PO Receipt & Triage"
- taskTypeId: abc-123-def
- inputs: inbox_config (config), po_patterns (config)
- outputs: email_id -> CaseEntity.source_email_id, sender_email -> CaseEntity.sender_email
- runOnlyOnce: true
- isRequired: true
- order: after T24
- verify: Confirm Result: Success, capture TaskId from output
```

Example (HITL/action):
```
## T30: Add action task "Review Purchase Order" to "PO Receipt & Triage"
- taskTypeId: xyz-456-abc
- recipient: approver@corp.com
- priority: High
- inputs: po_document -> "PO Receipt & Triage"."Monitor Order Inbox".po_document
- isRequired: true
- order: after T25
- verify: Confirm Result: Success, capture TaskId from output
```

#### 6. Configure conditions (one per condition)

Title format: `Add <scope> <event> condition for "<target>"` (e.g., `Add stage entry condition for "PO Receipt & Triage"`)

Each condition is its own numbered task. Process conditions in this order: stage entry conditions, stage exit conditions, case exit conditions, then task entry conditions.

**Stage entry conditions** — control when a stage is entered:

- **rule-type** -- `case-entered`, `selected-stage-completed`, `selected-stage-exited`, or `wait-for-connector`
- **selected-stage-id** -- the stage this rule references (required when rule-type is `selected-stage-completed` or `selected-stage-exited`)
- **order** -- which task(s) must complete before this one
- **verify** -- what to check after execution

**Stage exit conditions** — control when/how a stage exits:

- **rule-type** -- depends on the exit behavior:
  - `required-tasks-completed` — use when `marks-stage-complete: true`. All tasks in the stage must complete; no task ID list needed.
  - `selected-tasks-completed` — use when `marks-stage-complete: false` (exit-only conditions). Requires explicit task IDs.
  - `wait-for-connector` — wait for an external connector event.
- **selected-tasks-ids** -- comma-separated task names that must complete (required only when rule-type is `selected-tasks-completed`)
- **type** -- exit routing type. Determine from the sdd.md using these criteria:
  - `exit-only` — **Default.** Use when the stage exits normally and the case continues forward along the configured edges. The sdd.md describes a straightforward transition with no user gate at the exit point (e.g., "after all tasks complete, move to next stage", "auto-advance when done").
  - `wait-for-user` — Use when the sdd.md indicates the exit requires a manual user decision or approval before proceeding. Look for: "user decides next step", "manual approval gate", "wait for user input", "user selects outcome", or multiple named exit paths where a human chooses which one to take.
  - `return-to-origin` — Use when the sdd.md describes a rework or exception loop that sends the case back to the stage it came from. Look for: "return to previous stage", "send back for rework", "re-route to originating stage", or exception/review stages whose exit is defined as going back to wherever the case was before entering this stage.
- **exit-to-stage-id** -- the target stage name when the exit routes to a specific stage. Required when the sdd.md names an explicit destination stage for this exit (e.g., "exit to Review stage"). Omit when the routing follows the default edge configuration or uses `return-to-origin`.
- **marks-stage-complete** -- whether this exit counts as stage completion (true/false)
- **order** -- which task(s) must complete before this one
- **verify** -- what to check after execution

**Case exit conditions** — control when the entire case completes:

Use `required-stages-completed` as the primary rule-type. This mirrors how stage exit conditions use `required-tasks-completed` — the case completes when all stages marked `isRequired: true` (set in section 3) have completed. This avoids hard-coding specific stage IDs and keeps the case exit condition resilient to stage additions/removals.

- **rule-type** -- determines completion logic:
  - `required-stages-completed` — **Preferred.** Use when `marks-case-complete: true`. The case completes when every stage with `isRequired: true` has completed. No stage ID list needed — the system tracks required stages automatically.
  - `selected-stage-completed` — Use only when a non-completion exit depends on a specific stage (e.g., an exit-only path triggered by one stage finishing). Requires `selected-stage-id`.
  - `selected-stage-exited` — Use only when an exit depends on a stage being exited (not necessarily completed). Requires `selected-stage-id`.
  - `wait-for-connector` — wait for an external connector event.
- **selected-stage-id** -- the stage this rule references (required only for `selected-stage-completed` or `selected-stage-exited`)
- **marks-case-complete** -- whether this exit counts as case completion (true/false)
- **order** -- which task(s) must complete before this one
- **verify** -- what to check after execution

Example:
```
## T100: Add case exit condition — case resolved
- rule-type: required-stages-completed
- marks-case-complete: true
- order: after T99
- verify: Confirm Result: Success
```

**Task entry conditions** — control when a task within a stage starts:

- **rule-type** -- `current-stage-entered`, `selected-tasks-completed`, `wait-for-connector`, or `adhoc`
- **selected-tasks-ids** -- comma-separated task names that must complete (required when rule-type is `selected-tasks-completed`)
- **condition-expression** -- expression for the rule (required when rule-type is `adhoc`)
- **order** -- which task(s) must complete before this one
- **verify** -- what to check after execution

**Stage exit condition examples:**

```
## T80: Add stage exit condition for "PO Receipt & Triage" — all tasks done
- rule-type: required-tasks-completed
- type: exit-only
- marks-stage-complete: true
- order: after T79
- verify: Confirm Result: Success

## T81: Add stage exit condition for "Manager Review" — user picks next step
- rule-type: required-tasks-completed
- type: wait-for-user
- marks-stage-complete: true
- order: after T80
- verify: Confirm Result: Success

## T82: Add stage exit condition for "Exception Handling" — return to origin
- rule-type: required-tasks-completed
- type: return-to-origin
- marks-stage-complete: false
- order: after T81
- verify: Confirm Result: Success

## T83: Add stage exit condition for "Initial Review" — route to Escalation
- rule-type: selected-tasks-completed
- selected-tasks-ids: "Flag for Escalation"
- type: exit-only
- exit-to-stage-id: "Escalation"
- marks-stage-complete: false
- order: after T82
- verify: Confirm Result: Success
```

#### 7. Set SLA and escalation rules

SLA and escalation come last. They are broken into individual tasks, ordered as follows for each target (root first, then each stage):

1. **Set default SLA** -- the time-based catch-all SLA. Always last in the slaRules array. Used when no conditional SLA rule evaluates to true. Title format: `Set default SLA for "<target>" to <duration>`
2. **Add conditional SLA rules** (if any) -- condition-based SLA overrides evaluated before the default. Describe the condition in natural language from the sdd.md (e.g., "when case priority is Urgent"). Do NOT fabricate expression syntax — the implementation agent determines the correct expression format. **Order matters:** rules are evaluated in the order they are added; the first rule whose expression evaluates to true becomes the active SLA. If none match, the default is used. Title format: `Add conditional SLA rule for "<target>" — <condition summary>`
3. **Add escalation rules** -- one task per escalation rule. Each rule specifies a trigger type (`at-risk` with percentage threshold, or `sla-breached`) and one or more recipients. Each recipient has a scope (`User` or `UserGroup`), a target (email or group identifier), and a display value. **Order does not matter** — escalation rules operate on the configured threshold, not on position. Title format: `Add escalation rule for "<target>" — <trigger summary>`

Example:
```
## T150: Set default SLA for "PO Receipt & Triage" to 15 minutes
- count: 15
- unit: m
- order: after T149
- verify: Confirm Result: Success

## T151: Add conditional SLA rule for root case — when priority is Urgent
- condition: Priority = Urgent
- count: 30
- unit: m
- order: after T150
- verify: Confirm Result: Success

## T152: Add escalation rule for "PO Receipt & Triage" — At-Risk 80%
- trigger-type: at-risk
- at-risk-percentage: 80
- recipients:
  - User: manager@corp.com
  - UserGroup: Order Management Team
- order: after T151
- verify: Confirm Result: Success and capture the EscalationRuleId
```

#### Not Covered section

Add a brief section at the end listing things referenced in the sdd.md but outside the scope of the `uip case` CLI:
- **Data Fabric entity schemas and global variables** -- referenced in task mappings but must be configured separately in Data Fabric.

## Step 5 -- Generate registry-resolved.json

Write a JSON file in the `tasks/` folder containing all registry lookup results keyed by task ID. This serves as a debugging and audit trail. Include:
- The search query used
- All matched results
- Which result was selected and why

## Anti-patterns — What NOT to Do

- **Do NOT put `uip case ...` CLI commands in tasks.md.** Including shell commands causes the implementation agent to double-execute or mis-parse. Tasks.md is declarative only.
- **Do NOT incrementally update an existing tasks.md.** Always regenerate from scratch to avoid stale state.
- **Do NOT skip registry lookups** based on assumptions like "this type is not discoverable." Always search the cache files first.
- **Do NOT group multiple sdd.md tasks under one T-number.** Each task in the sdd.md gets its own numbered entry.
- **Do NOT fabricate expression syntax** for conditional SLA rules. Describe the condition in natural language — the implementation agent determines the correct expression format.
- **Do NOT add interactive checkpoints** during generation. Run silently and let the user review the output after completion.
- **Do NOT include parameters the CLI does not support.** Only include what `uip case` can act on (see [CLI command reference](references/case-commands.md)).
- **Do NOT use lane assignments.** The lane concept is no longer used for managing parallelism.

## Reference Navigation

- [Registry Discovery Reference](references/registry-discovery.md) — how to resolve task types from the local cache
- [CLI Command Reference](references/case-commands.md) — all `uip case` commands with flags and examples
- [Case JSON Schema Reference](references/case-schema.md) — the case definition JSON structure
