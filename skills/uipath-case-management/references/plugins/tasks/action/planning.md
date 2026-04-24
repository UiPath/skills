# action task — Planning

A human-in-the-loop (HITL) action task. Assigns a task to a user or group for manual review, approval, or data entry via the Actions app.

## When to Use

Pick this plugin when the sdd.md describes a `HITL` task, or any task requiring manual user interaction: approval, review, sign-off, correction, classification by a person.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | sdd.md task name | CLI flag `--display-name` |
| `task-type-id` | Registry resolution (below) | CLI flag `--task-type-id` — the action-app ID |
| `task-title` | sdd.md task title or description (see fallback below) | CLI flag `--task-title`. Required for `action` type. |
| `priority` | sdd.md (default `Medium`) | `Low` / `Medium` / `High` / `Critical`. CLI flag `--priority`. |
| `recipient` | sdd.md assignee email; **prompt the user if silent** | CLI flag `--recipient`. See Recipient Handling below. |
| `inputs` | sdd.md task data mapping | See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | Discovered via `tasks describe` | Decision, comments, structured form fields |
| `isRequired` | sdd.md (default `true`) | CLI flag `--is-required` |

## Task Title Fallback

`task-title` is what the user sees in the Actions app. Always emit it — the validator requires it even on skeletons. Derive in this order:

1. SDD has an explicit title or question field → use it
2. SDD has a Description → summarize into a short, concise title
3. Neither → use the `display-name`

## Registry Resolution

1. **Primary cache file:** `action-apps-index.json`.
2. **Identifier field:** `id` (NOT `entityKey` — action-apps use a different field).
3. **Name field:** `deploymentTitle` (not `name`).
4. **Folder field:** `deploymentFolder.fullyQualifiedName`.
5. **CLI search known to fail** for action-apps — always use direct cache-file inspection.
6. Discover form fields / inputs / outputs via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

See [registry-discovery.md](../../../registry-discovery.md#cli-search-gaps) for the fallback rationale.

## Unresolved Fallback

Mark `<UNRESOLVED: action-app "<deploymentTitle>" in folder "<folder>" not found in action-apps-index.json>`. Omit `inputs:` and `outputs:`; capture intended wiring in a fenced ```` ```text ```` code block (not `#` prefixed — it renders as markdown H1). **Keep `task-title:`** — the validator requires it even on skeleton action tasks. Derive via the fallback above. See [skeleton-tasks.md](../../../skeleton-tasks.md).

## Recipient Handling

- If sdd.md **names a specific user email**, record it in `tasks.md`. Sets `assignmentCriteria: "user"` at execution time.
- If sdd.md **names a group or role**, do **not** record a recipient — group assignment is configured separately via Actions app rules. Record a note in `tasks.md` so the user remembers to configure group assignment externally.
- If sdd.md is **silent on assignee**, **prompt the user** using **AskUserQuestion** with a direct open-ended prompt:
  > "The action task '<display-name>' has no assignee specified in sdd.md. Who should receive it? Enter an email, a group/role name, or 'Skip' to leave it unassigned for now."

  Parse the user's response:
  - Looks like an email → record as `recipient: <email>`.
  - Group / role name → omit recipient; record a note in `tasks.md` reminding the user to configure group assignment externally.
  - `Skip` or empty → omit recipient.

This follows Critical Rule #19 — for open-ended inputs like an email address, use a direct prompt rather than AskUserQuestion with a finite option list.

## tasks.md Entry Format

```markdown
## T<n>: Add action task "<display-name>" to "<stage>"
- taskTypeId: <action-app-id>
- task-title: "<title-shown-to-user>"
- priority: Medium
- recipient: user@company.com   # omit when group-assigned or when user chose Skip
- assignment-note: "<free-form note if group-assigned>"   # optional
- runOnlyOnce: false   # from sdd.md "Run Only Once" column
- inputs:
  - <input_name> <- "<Stage>"."<Task>".<output>
  - <input_name> = "<literal-or-expression>"
- outputs: decision, comments
- isRequired: true
- order: after T<m>
- lane: <n>  # FE layout coordinate; increment per task within the stage
- verify: Confirm Result: Success, capture TaskId
```
