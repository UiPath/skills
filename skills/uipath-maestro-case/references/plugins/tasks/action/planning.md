# action task — Planning

A human-in-the-loop (HITL) action task. Assigns a task to a user or group for manual review, approval, or data entry via the Actions app.

## When to Use

Pick this plugin when the sdd.md describes a `HITL` task, or any task requiring manual user interaction: approval, review, sign-off, correction, classification by a person.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | sdd.md task name |  |
| `resource-name` | `Action App: <deploymentTitle>` in sdd.md `HITL Implementation` | Concrete registry query; REQUIRED and never `<UNRESOLVED>`. Do not substitute `display-name`. |
| `name` | Selected registry `deploymentTitle` | Runtime resource binding consumed by Phase 2; use the selected app's canonical title. |
| `folder-path` | Selected registry `deploymentFolder.fullyQualifiedName` | Runtime folder binding consumed by Phase 2; use the selected app's exact deployment folder. |
| `task-type-id` | Registry resolution (below) | Action-app ID |
| `task-title` | sdd.md task title or description (see fallback below) | Required for `action` type. |
| `priority` | sdd.md (default `Medium`) | `Low` / `Medium` / `High` / `Critical`.  |
| `recipient` | sdd.md assignee email; **prompt the user if silent** | See Recipient Handling below. |
| `inputs` | sdd.md task data mapping | See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | sdd.md task Outputs + `tasks describe` schema | Follow the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-tasksmd-output-list). |
| `isRequired` | sdd.md (default `true`) |  |

## Task Title Fallback

`task-title` is what the user sees in the Actions app. Required on resolved action tasks (placeholders skip — see § Unresolved Fallback). Derive in this order:

1. SDD has an explicit title or question field → use it
2. SDD has a Description → summarize into a short, concise title
3. Neither → use the `display-name`

## Registry Resolution

1. **Primary cache file:** `action-apps-index.json`.
2. **Identifier field:** `id` (NOT `entityKey` — action-apps use a different field).
3. **Name field:** `deploymentTitle` (not `name`).
4. **Folder field:** `deploymentFolder.fullyQualifiedName`.
5. **CLI search known to fail** for action-apps — always use direct cache-file inspection.
6. Set `name` to the selected entry's canonical `deploymentTitle` and `folder-path` to its exact `deploymentFolder.fullyQualifiedName`. Never substitute the task display name or a parent/truncated folder.
7. Discover form fields / inputs / outputs via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

Query by the exact concrete `resource-name` from the SDD. `Action App ID` determines whether the prior phase resolved the app; an unresolved ID does not erase or replace the intended title. Action lookups stay in `action-apps-index.json` — never adopt a same-named resource from another cache type.

See [registry-discovery.md](../../../registry-discovery.md#cli-search-gaps) for the fallback rationale.

## Unresolved Fallback

Mark `<UNRESOLVED: action-app "<resource-name>" in folder "<folder>" not found in action-apps-index.json>`, using the SDD's preserved Action App title even when its ID/folder are unresolved. Emit only structural fields — drop every action-specific line (`task-title`, `priority`, `recipient`, `inputs`, `outputs`). See [placeholder-tasks.md](../../../placeholder-tasks.md) for the full placeholder entry shape and wiring-block convention.

## Recipient Handling

> Resolved action tasks only — placeholders skip this entire section (see § Unresolved Fallback).

`recipient` decides whose Actions queue the task lands in. Planning records a bare value; the build wraps it into the `{ Type, Value }` object the caseplan carries.

1. **sdd.md names a user email** — record the bare email exactly as authored: `recipient: alex@corp.com`.
2. **sdd.md names a group or role** — record the bare group name behind a `UserGroup:` prefix: `recipient: UserGroup: Compliance`. The prefix is what marks it a group; it is stripped from the value. Do not look the group up.
3. **sdd.md is silent** — ask with **AskUserQuestion**, using a direct open-ended prompt rather than a finite option list:
   > "The action task '<display-name>' has no assignee specified in sdd.md. Who should receive it? Enter an email, a group/role name, or 'Skip' to leave it unassigned for now."

   Then apply rule 1 or 2 to the answer. `Skip`, empty, or a non-interactive run with no answer available → omit `recipient` and record an `assignment-note` saying the task will reach nobody until someone assigns it.

> **This field holds a name, never a UUID.** An assignment recipient is not an escalation recipient: an SLA escalation writes `{ scope, target, value }` and needs the directory UUID in `target`, while an assignment writes one field that holds the name or email. The two shapes read alike, so the SLA plugin's group-to-UUID lookup looks reusable here. It is not, and a UUID in this field is rejected at runtime.

> **A group must already have folder access, which this skill cannot grant.** It reaches the task only when it exists in Orchestrator **and** holds a role on the task's folder; `uip admin groups create` gives it neither. Without both the task is created and reaches nobody — the same visible outcome as omitting the recipient, and `validate` sees neither. Record an `assignment-note` naming the group so the user can grant it access.

## tasks.md Entry Format

Resolved action task. For the unresolved placeholder shape, see [placeholder-tasks.md § `tasks.md` Planning-Entry Shape](../../../placeholder-tasks.md#tasksmd-planning-entry-shape).

```markdown
## T<n>: Add action task "<display-name>" to "<stage>"
- taskTypeId: <action-app-id>
- name: "<selected-deployment-title>"
- folder-path: "<selected-deployment-folder>"
- task-title: "<title-shown-to-user>"
- priority: Medium
- recipient: user@company.com   # or UserGroup: <group name>; omit when Skip or no answer
- assignment-note: "<why the task is unassigned, or the group that needs folder access>"   # optional
- runOnlyOnce: false   # from sdd.md "Run Only Once" column
- inputs:
  - <input_name> <- "<Stage>"."<Task>".<output>
  - <input_name> = "<literal-or-expression>"
- outputs:
  - <SDD output row, copied verbatim>
- isRequired: true
- activation-mode: <sequential|parallel|event-triggered|adhoc|fan-in|conditional-gate>   # required
- entry-rule: <runs-sequentially|current-stage-entered|wait-for-connector|adhoc|selected-tasks-completed>   # required; must pair with activation-mode — see ../../conditions/task-entry-conditions/planning.md
- order: after T<m>
- lane: <n>  # structural/layout position only; sequencing is the task entry rule plus data.tasks order.
- verify: Confirm Result: Success, capture TaskId
```

<!-- END: planning.md -->
