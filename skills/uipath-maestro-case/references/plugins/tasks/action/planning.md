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

- If sdd.md **names a specific user email**, record the bare email exactly as authored in `tasks.md`; never replace it with a UUID resolved for an SLA recipient or write the SLA-only `<uuid> / <email>` pair. Sets `assignmentCriteria: "user"` at execution time.
- If sdd.md **names a group or role**, do **not** record a recipient — group assignment is configured separately via Actions app rules. Record a note in `tasks.md` so the user remembers to configure group assignment externally.
- If sdd.md is **silent on assignee**, **prompt the user** using **AskUserQuestion** with a direct open-ended prompt:
  > "The action task '<display-name>' has no assignee specified in sdd.md. Who should receive it? Enter an email, a group/role name, or 'Skip' to leave it unassigned for now."

  Parse the user's response:
  - Looks like an email → record as `recipient: <email>`.
  - Group / role name → omit recipient; record a note in `tasks.md` reminding the user to configure group assignment externally.
  - `Skip` or empty → omit recipient.

For open-ended inputs like an email address, use a direct prompt rather than AskUserQuestion with a finite option list.

## tasks.md Entry Format

Resolved action task. For the unresolved placeholder shape, see [placeholder-tasks.md § `tasks.md` Planning-Entry Shape](../../../placeholder-tasks.md#tasksmd-planning-entry-shape).

```markdown
## T<n>: Add action task "<display-name>" to "<stage>"
- taskTypeId: <action-app-id>
- name: "<selected-deployment-title>"
- folder-path: "<selected-deployment-folder>"
- task-title: "<title-shown-to-user>"
- priority: Medium
- recipient: user@company.com   # omit when group-assigned or when user chose Skip
- assignment-note: "<free-form note if group-assigned>"   # optional
- runOnlyOnce: false   # from sdd.md "Run Only Once" column
- inputs:
  - <input_name> <- "<Stage>"."<Task>".<output>
  - <input_name> = "<literal-or-expression>"
- outputs:
  - <SDD output row, copied verbatim>
- isRequired: true
- order: after T<m>
- lane: <n>  # structural/layout position only; sequencing is the task entry rule plus data.tasks order.
- verify: Confirm Result: Success, capture TaskId
```
