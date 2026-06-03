# Planning Phase: spec.md → tasks.md

Convert a case design document (`spec.md`, sometimes called `sdd.md`) into a numbered `tasks.md` planning document that the [implementation phase](impl.md) executes mechanically.

The spec.md describes the case in plain language — stages, tasks, edges, rules, SLA, component types. This phase resolves every registry lookup upfront and emits a flat, ordered task list (`T01`, `T02`, …) so that the implementation phase can build caseplan.json without re-doing discovery mid-build.

> **Why a separate planning phase?** Without it, the implementation phase would have to read prose, guess registry resources, sequence everything, and recover from network failures partway through. By front-loading interpretation into a flat checklist, build becomes mechanical and resumable.

---

## When to Load This Reference

- The user provides a `spec.md` (or `sdd.md`) and no `tasks.md` exists yet
- The user explicitly asks to "plan", "break down a spec", or "generate tasks from spec"
- The user wants to regenerate tasks.md from a modified spec

If a tasks.md already exists and the user wants to build the case, skip this and go to [impl.md](impl.md).

---

## Step 0 — Resolve the `uip` binary

```bash
UIP=$(command -v uip 2>/dev/null || echo "$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip")
$UIP --version
```

Use `$UIP` if the plain `uip` command isn't on PATH.

## Step 1 — Check login and pull the registry

Registry discovery happens during interpretation, so login is required upfront. Pulling the cache once at the start avoids mid-run network failures.

```bash
uip login status --output json
uip case registry pull
```

Cache is written to `~/.uip/case-resources/`. All subsequent task-type resolution reads these files directly — no more network round-trips.

If not logged in, prompt the user to log in before continuing.

## Step 2 — Locate and parse the spec

Accept the spec.md path from the user, or ask. The spec is the **sole source of truth** for the design — it carries:

- Stages (with descriptions and isRequired)
- Tasks per stage (with component_type, name, folder path, inputs/outputs)
- Edges between stages
- Entry/exit conditions
- SLA and escalation rules
- Process References table (search keywords for the registry lookups)

Parse the entire spec before generating tasks.md. Do not generate incrementally.

## Step 3 — Resolve task types via the local registry cache

For each task in the spec, find its `taskTypeId` by reading the cache files at `~/.uip/case-resources/`. Direct disk reads are faster and more reliable than `uip case registry search` for batch interpretation.

### Component-Type → Cache File Mapping

The spec.md uses a `component_type` label per task. Map each label to the **primary** cache file to search and the corresponding implementation `--type`:

| spec component_type | Primary cache file | Implementation `type` |
|---|---|---|
| `API_WORKFLOW` | `api-index.json` | `api-workflow` |
| `AGENTIC_PROCESS` | `processOrchestration-index.json` | `process` |
| `HITL` | `action-apps-index.json` | `action` |
| `RPA` | `process-index.json` | `rpa` |
| `AGENT` | `agent-index.json` | `agent` |
| `CASE_MANAGEMENT` | `caseManagement-index.json` | `case-management` |
| `CONNECTOR_ACTIVITY` | `typecache-activities-index.json` | `execute-connector-activity` |
| `CONNECTOR_TRIGGER` | `typecache-triggers-index.json` | `wait-for-connector` |
| `EXTERNAL_AGENT` | *(not in cache)* | `external-agent` |
| `TIMER` | *(not in cache)* | `wait-for-timer` |
| `PROCESS` | `process-index.json` | `process` |

For `EXTERNAL_AGENT` and `TIMER`, no registry lookup is needed — write the type directly.

### Cache File Structure

Each `<type>-index.json` is a JSON array. The identifier and label fields differ per file:

| File | Identifier field | Name field | Folder field |
|---|---|---|---|
| `agent-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `process-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `api-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `processOrchestration-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `caseManagement-index.json` | `entityKey` | `name` | `folders[0].fullyQualifiedName` |
| `action-apps-index.json` | `id` | `deploymentTitle` | `deploymentFolder.fullyQualifiedName` |
| `typecache-activities-index.json` | `uiPathActivityTypeId` | `displayName` | *(none)* |
| `typecache-triggers-index.json` | `uiPathActivityTypeId` | `displayName` | *(none)* |

### Search Procedure

For each task in the spec:

1. **Search the primary cache file** by name and folder path (from the Process References table). Use:

   ```bash
   cat ~/.uip/case-resources/<type>-index.json | python3 -c "
   import sys, json
   data = json.load(sys.stdin)
   for item in data:
       name = item.get('name', '') or item.get('deploymentTitle', '')
       if '<task_name>' in name:
           folders = item.get('folders', [])
           folder = folders[0].get('fullyQualifiedName', '') if folders else ''
           if not folder:
               df = item.get('deploymentFolder', {})
               folder = df.get('fullyQualifiedName', '') if df else ''
           ident = item.get('entityKey') or item.get('id') or item.get('uiPathActivityTypeId', '')
           print(json.dumps({'identifier': ident, 'name': name, 'folder': folder}))
   "
   ```

2. **If no match in the primary file**, search **all** other cache files. The spec.md's `component_type` label is not always accurate — an "RPA" task may be registered under `process-index.json`, an "AGENTIC_PROCESS" might live in `process-index.json`, etc. When a match is found in a different cache file:
   - Use that cache file's identifier field for `taskTypeId`
   - Keep the spec's `component_type` for the implementation `type` flag

3. **Pick the best match** in this priority order:
   1. Exact name + exact folder match
   2. Exact name with multiple folders → pick the folder named in the spec
   3. Exact name with no folder in spec → pick the first match; record alternatives in `registry-resolved.json`
   4. No match → run `uip case registry pull --force` and retry

4. **If still no match after force-refresh**, write the task entry with `taskTypeId: [REGISTRY LOOKUP FAILED: <name> in <folder>]` and continue. Do not abort the run on a single missing resource — best-effort interpretation.

5. **For connector tasks** (typecache-activities, typecache-triggers), also collect connection metadata via CLI:

   ```bash
   uip case registry get-connector --type <typecache-activities|typecache-triggers> \
     --activity-type-id "<uiPathActivityTypeId>" --output json

   uip case registry get-connection --type <typecache-activities|typecache-triggers> \
     --activity-type-id "<uiPathActivityTypeId>" --output json
   ```

   The `get-connection` response has `Entry`, `Config` (with `connectorKey` + `objectName`), and `Connections[]`. Match the connection by name from the spec. If `Connections` is empty, surface this to the user — they need to create a connection in Integration Service before the case can run.

## Step 4 — Generate tasks.md

Create a `tasks/` folder next to the spec.md. Write a fresh `tasks.md` (do not incrementally update an existing one).

### Ordering convention

Strict order, mirrored by [impl.md](impl.md):

1. Create case file (T01)
2. Configure trigger (T02 — only if non-default trigger)
3. Create stages (one task per stage)
4. Add edges (one task per edge)
5. Add tasks (one task per spec task; type baked into title)
6. Add conditions — stage entry, then stage exit, then case exit, then task entry
7. Set SLA + escalation — root first, then per stage; default SLA, then conditional rules, then escalation rules

### Task entry format

The task title IS the action description. Do not add a redundant `what` or `type` field — bake type into the title (`Add api-workflow task` not `Add task` + `type: api-workflow`).

Each entry is declarative — parameters, IDs, and metadata only. **No `uip` shell commands inside task bodies.** The implementation phase translates each entry into JSON writes (or, for connector enrichment, into the right CLI call).

### Section 1 — Create case file

```
## T01: Create case file "<name>"
- caseIdentifier: <prefix>
- caseIdentifierType: constant
- description: <one-line description from spec>
- order: first
- verify: Confirm Result: Success, capture case file path
```

### Section 2 — Configure trigger (only if not the default manual trigger)

```
## T02: Configure wait-for-connector trigger "<name>"
- typeId: <uiPathActivityTypeId from typecache-triggers>
- connectionId: <id from get-connection match>
- order: after T01
- verify: Confirm Result: Success
```

### Section 3 — Create stages

Each stage gets its own task. Determine `isRequired` from the spec:

- `true` (default for regular stages) — happy-path, mandatory; tracked by `required-stages-completed`
- `false` — exception stages, optional review stages, rework loops reached only via interrupting/conditional entry

```
## T05: Create stage "PO Receipt & Triage"
- isRequired: true
- description: <stage description>
- order: after T04
- verify: Confirm Result: Success, capture StageId

## T06: Create exception stage "Exception Handling"
- isRequired: false
- description: <stage description>
- order: after T05
- verify: Confirm Result: Success, capture StageId
```

### Section 4 — Add edges

```
## T10: Add edge "Trigger" → "Stage 1"
- order: after T09
- verify: Confirm Result: Success
```

### Section 5 — Add tasks

One task per spec task. Required fields:

- `taskTypeId` — from Step 3
- `description` — copied from spec
- `inputs` — `none`, or human-readable cross-references like `po_document -> "PO Receipt & Triage"."Monitor Order Inbox".po_document`
- `outputs` — `none`, or `<output_name> -> <variable or entity field>`
- `runOnlyOnce` — defaults to `true`
- `isRequired` — defaults to `true`
- `order` — dependency ("after T24")
- `verify`

Action tasks add:
- `recipient` — assignee email from spec
- `priority` — `Low` / `Medium` / `High` / `Critical` (default `Medium`)
- `taskTitle` — display title shown to the human

> **Do not assign lanes.** Lane numbering is now auto-derived from task order during build (one task per lane). Parallelism is controlled by entry conditions, not lane grouping.

Examples:

```
## T25: Add api-workflow task "Monitor Order Inbox" to "PO Receipt & Triage"
- taskTypeId: abc-123-def
- description: Watches the PO inbox for new purchase orders
- inputs: inbox_config (config), po_patterns (config)
- outputs: email_id -> CaseEntity.source_email_id, sender_email -> CaseEntity.sender_email
- runOnlyOnce: true
- isRequired: true
- order: after T24
- verify: Confirm Result: Success, capture TaskId from output

## T30: Add action task "Review Purchase Order" to "PO Receipt & Triage"
- taskTypeId: xyz-456-abc
- taskTitle: Review Purchase Order
- recipient: approver@corp.com
- priority: High
- inputs: po_document -> "PO Receipt & Triage"."Monitor Order Inbox".po_document
- outputs: Action (Approve or Reject), reviewer_comment
- runOnlyOnce: true
- isRequired: true
- order: after T25
- verify: Confirm Result: Success, capture TaskId from output
```

### Section 6 — Conditions

Process in order: stage entry → stage exit → case exit → task entry.

**Stage entry — `rule-type`:** `case-entered` (first stage), `selected-stage-completed` / `selected-stage-exited` (with `selected-stage-id`), `current-stage-entered`, `wait-for-connector`, `adhoc`.

**Stage exit — `rule-type`:** `required-tasks-completed` (use with `marks-stage-complete: true`), `selected-tasks-completed` (use when `marks-stage-complete: false`, requires `selected-tasks-ids`), `wait-for-connector`.

**Stage exit — `type`:**
- `exit-only` (default) — case continues forward
- `wait-for-user` — manual user decision required
- `return-to-origin` — case returns to calling stage (used on exception stages)

**Stage exit — `exit-to-stage-id`:** Required only when the spec names an explicit destination ("exit to Review stage"). Omit for default-edge or `return-to-origin` routing.

**Case exit — `rule-type`:** Prefer `required-stages-completed` (no stage list needed; tracks all `isRequired: true` stages). Use `selected-stage-completed` / `selected-stage-exited` only for non-completion exits tied to one stage. **Never use `required-tasks-completed`** — that rule is stage-scoped.

**Task entry — `rule-type`:** `current-stage-entered` (default for parallel-on-entry), `selected-tasks-completed` (sequential), `wait-for-connector`, `adhoc`.

Examples:

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

## T100: Add case exit condition — case resolved
- rule-type: required-stages-completed
- marks-case-complete: true
- order: after T99
- verify: Confirm Result: Success
```

### Section 7 — SLA + escalation

Per target (root first, then each stage), in this order:

1. **Default SLA** — always last in the runtime `slaRules` array, but written first in tasks.md so escalation entries can reference it. Title: `Set default SLA for "<target>" to <duration>`.
2. **Conditional SLA rules** (if any) — describe the condition in plain language from the spec; do not fabricate expression syntax (the implementation phase determines `=js:...`). Order matters in the runtime — first matching wins. Title: `Add conditional SLA rule for "<target>" — <condition summary>`.
3. **Escalation rules** — one task per rule; order does not matter. Each rule has a `trigger-type` (`at-risk` with `at-risk-percentage`, or `sla-breached`) and `recipients[]` (`User: <email>` or `UserGroup: <name>`). Title: `Add escalation rule for "<target>" — <trigger summary>`.

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

### Section 8 — Exception Stages (if present in spec)

Exception stages handle error paths, customer response loops, denial/withdrawal flows, etc. They differ from regular stages:

- `isRequired: false` — not required for normal case completion
- Entry conditions use `isInterrupting: true` to preempt the source stage
- Exit conditions often use `return-to-origin` to return to the calling stage

```
## T40: Create exception stage "Pending with customer"
- isRequired: false
- description: Handles customer document requests and follow-up
- order: after T39
- verify: Confirm Result: Success, capture StageId

## T50: Add stage entry condition for "Pending with customer" — from Intake
- rule-type: selected-stage-exited
- selected-stage-id: "Intake"
- condition: decision == "Claim needs info from customer"
- isInterrupting: true
- order: after T49
- verify: Confirm Result: Success

## T51: Add stage entry condition for "Pending with customer" — from Review
- rule-type: selected-stage-exited
- selected-stage-id: "Review"
- condition: decision == "Claim needs info from customer"
- isInterrupting: true
- order: after T50
- verify: Confirm Result: Success

## T60: Add stage exit condition for "Pending with customer" — return to origin
- rule-type: required-tasks-completed
- type: return-to-origin
- marks-stage-complete: true
- order: after T59
- verify: Confirm Result: Success
```

### Section 9 — Re-entry Counter Variables (if spec has re-entry loops)

When stages can be re-entered, declare counter variables to differentiate first-pass vs re-entry behavior:

```
## T70: Declare re-entry counter for "Intake"
- variable-name: finishedRunCountIntake
- type: number
- internal: true
- order: after T69
- verify: Confirm Result: Success
```

These counters are used in `conditionExpression` fields to gate task execution on re-entry.

### Section 10 — Case App Config (if spec defines portal sections)

When the spec includes Case App / Case Portal configuration:

```
## T80: Configure Case App
- caseSummary: =string.Format("{0} - {1}", vars.response.customerName, vars.response.policyId)
- sections:
  - title: Applicant
    details: Name=vars.response.customerName, Email=vars.response.customerEmail
  - title: Claim details
    details: Loss date=vars.response.claimDate, Cause=vars.response.claimCauseOfLoss
- order: after T79
- verify: Confirm Result: Success
```

### Section 11 — Not Covered

End the file with a brief section listing things referenced in the spec but outside the scope of `caseplan.json` build:

- **Data Fabric entity schemas and global variables** — must be configured separately in Data Fabric.
- **Integration Service connector creation** — connections must exist before the case runs; flag any missing.
- **Document processing pipelines** — handled separately if used.
- **Detailed role/permission configuration** — defined during deployment.

## Step 5 — Generate registry-resolved.json

In the same `tasks/` folder, write `registry-resolved.json` keyed by task ID. This is the audit trail for the registry lookups in Step 3:

```json
{
  "T25": {
    "spec_component_type": "API_WORKFLOW",
    "search_name": "Monitor Order Inbox",
    "search_folder": "Shared/Procurement",
    "cache_file": "api-index.json",
    "matches": [
      { "identifier": "abc-123-def", "name": "Monitor Order Inbox", "folder": "Shared/Procurement" }
    ],
    "selected": "abc-123-def",
    "selection_reason": "exact name + exact folder match"
  }
}
```

This file is consumed by the implementation phase if any tasks.md entry needs a re-lookup, and by the user for debugging.

---

## Design Principles

- **Always regenerate tasks.md from scratch** — never patch an existing tasks.md. Stale state from earlier runs causes silent drift.
- **Run silently** — no interactive checkpoints during generation. The user reviews the output after it's complete.
- **Registry pull upfront** — avoids network failures partway through.
- **Best effort on registry failures** — mark missing lookups inline (`[REGISTRY LOOKUP FAILED: ...]`) and continue. Do not abort the whole run.
- **Single output file** — everything in one `tasks.md`. Length scales with case complexity.
- **No `uip` commands inside tasks.md** — declarative specification only. The implementation phase owns translation to JSON / CLI.
- **Human-readable cross-references** — use `"Stage Name"."Task Name".field_name` for input/output mappings so the file is reviewable without opening the registry.
