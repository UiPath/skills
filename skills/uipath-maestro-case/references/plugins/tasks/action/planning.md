# action task — Planning

A human-in-the-loop (HITL) action task assigns manual review, approval, or data entry to a user or group through the Actions app.

## When to Use

Use this plugin when sdd.md describes a `HITL` task or manual interaction: approval, review, sign-off, correction, or human classification.

## Required Fields from sdd.md

| Field | Source / rule |
|---|---|
| `display-name` | sdd.md task name |
| `resource-name` | `Action App: <deploymentTitle>` in sdd.md `HITL Implementation`; query the concrete registry value, REQUIRED and never `<UNRESOLVED>`. Never substitute `display-name`. |
| `name` | Selected registry `deploymentTitle`; canonical title consumed by Phase 2. |
| `folder-path` | Selected registry `deploymentFolder.fullyQualifiedName`; exact folder consumed by Phase 2. |
| `task-type-id` | Registry resolution below; action-app ID. |
| `task-title` | sdd.md task title or description; required for `action`, using the fallback below. |
| `priority` | sdd.md, default `Medium`; `Low` / `Medium` / `High` / `Critical`. |
| `recipient` | sdd.md assignee email; **prompt the user if silent**. See Recipient Handling. |
| `inputs` | sdd.md task data mapping; see [bindings-and-expressions.md](../../../bindings-and-expressions.md). |
| `outputs` | sdd.md task Outputs + `tasks describe` schema; follow [the shared I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-output-list). |
| `isRequired` | sdd.md, default `true`. |

## Task Title Fallback

`task-title` is shown in the Actions app and required on resolved action tasks; placeholders skip it (see § Unresolved Fallback). Derive it in order:

1. Use an explicit SDD title or question field.
2. Otherwise summarize the SDD Description into a short, concise title.
3. Otherwise use `display-name`.

## Registry Resolution

1. Use the primary cache file `action-apps-index.json`; always inspect it directly because **CLI search known to fail** for action-apps.
2. Query its `id` field, **not** `entityKey`.
3. Use `deploymentTitle`, not `name`.
4. Use `deploymentFolder.fullyQualifiedName` for the folder.
5. Query the exact concrete `resource-name` from the SDD, then set `name` to the selected entry's canonical `deploymentTitle` and `folder-path` to its exact `deploymentFolder.fullyQualifiedName`; never use the task display name or a parent/truncated folder.
6. Run `tasks describe` to discover form fields, inputs, and outputs—see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

`Action App ID` indicates whether the prior phase resolved the app; an unresolved ID does not erase or replace the intended title. Keep action lookups in `action-apps-index.json`; never use a same-named resource from another cache type. See [registry-discovery.md](../../../registry-discovery.md#when-a-search-returns-nothing) for the fallback rationale.

## Unresolved Fallback

Mark `<UNRESOLVED: action-app "<resource-name>" in folder "<folder>" not found in action-apps-index.json>`, preserving the SDD's Action App title even when its ID or folder is unresolved. Emit only structural fields: omit every action-specific line (`task-title`, `priority`, `recipient`, `inputs`, `outputs`). See [placeholder-tasks.md](../../../placeholder-tasks.md) for the full placeholder entry shape and wiring-block convention.

## Recipient Handling

> Resolved action tasks only; placeholders skip this section.

`recipient` determines whose Actions queue receives the task. Planning records a bare value; the build wraps it in the `{ Type, Value }` object carried by the caseplan.

1. If sdd.md names a user email, record it exactly as authored: `recipient: alex@corp.com`.
2. If it names a group or role, record the bare name behind a `UserGroup:` prefix: `recipient: UserGroup: Compliance`. The prefix marks it as a group and is stripped from the value. Do not look up the group.
3. If sdd.md is silent, ask with **AskUserQuestion** using a direct open-ended prompt, not a finite option list:
   > "The action task '<display-name>' has no assignee specified in sdd.md. Who should receive it? Enter an email, a group/role name, or 'Skip' to leave it unassigned for now."

   Apply rule 1 or 2 to the answer. `Skip`, an empty answer, or a non-interactive run without an answer omits `recipient` and records an `assignment-note` that the task will reach nobody until someone assigns it.

> **This field holds a name, never a UUID.** An assignment recipient is not an escalation recipient: SLA escalation writes `{ scope, target, value }` and requires the directory UUID in `target`; assignment writes one field containing a name or email. Do not reuse the SLA plugin's group-to-UUID lookup. A UUID here is rejected at runtime.

> **A group must already have folder access, which this skill cannot grant.** The group receives the task only if it exists in Orchestrator and holds a role on the task's folder; `uip admin groups create` grants neither. Without both, the task is created but reaches nobody—the same visible outcome as omitting the recipient—and `validate` sees neither. Record an `assignment-note` naming the group so the user can grant access.

## Fields to Resolve

For a resolved action task, record this ledger entry in `tasks/registry-resolved.json`. For the unresolved placeholder shape, see [placeholder-tasks.md § `registry-resolved.json` Entry Shape](../../../placeholder-tasks.md#registry-resolvedjson-entry-shape).

```json
{
  "stage": "<stage>",
  "task": "<display-name>",
  "taskType": "action",
  "cacheFile": "action-apps-index.json",
  "searchQuery": "<name the SDD used to seed the lookup>",
  "matches": [],
  "selected": {},
  "name": "<selected-deployment-title>",
  "taskTypeId": "<action-app-id>",
  "folder-path": "<selected-deployment-folder>",
  "recipient": "user@company.com",
  "assignment-note": "<why the task is unassigned, or the group that needs folder access>",
  "rationale": "<why this match was selected>"
}
```

`recipient` contains the resolved assignee—`UserGroup: <group name>` for a group—and is omitted on Skip or no answer; `assignment-note` is optional. `matches` is the complete exact-name set from the refreshed cache, and `selected` is the chosen match object.

All other SDD declarations—task title, priority, inputs, outputs, required, run-only-once, activation mode, entry rule, lane, and verify text—remain in `sdd.md`; Phase 2 reads them there ([planning.md § Step 4](../../../planning.md)).

<!-- END: planning.md -->