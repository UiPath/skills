# Placeholder Tasks Reference

Read this file only after the user has explicitly accepted placeholder fallback
for unresolved resources. A placeholder preserves case topology and intent
without fabricating runtime identity or schema.

## Placeholder vs mock

| Field | Resolved task | Placeholder | Mock (forbidden) |
|---|---|---|---|
| `type`, `displayName`, flags | real | real | real |
| runtime identity | real | omitted | fabricated |
| runtime inputs/outputs | described schema | omitted | invented schema |
| task entry rules | authored | authored | authored |
| stage dependency references | valid | valid | often invalid |

Mocks are forbidden. A fake ID or schema may pass shallow validation and fail at
runtime. A placeholder is intentionally unconfigured and therefore visible.

## Creation contract

For each accepted unresolved entry in `case-build/registry-resolved.json`:

1. Skip `tasks describe` / connector spec generation.
2. Create the structural task at its exact SDD position.
3. Omit runtime identity, inputs, outputs, and bindings.
4. Preserve every SDD-authored task condition and stage dependency.
5. Add the task's generated ID to the semantic `id-map.json` locator.
6. Mark the evidence entry `status: "placeholder"` and retain the intended
   resource name, folder, type, authored bindings, and unresolved reason.

## Task JSON shape

```json
{
  "id": "t8GQTYo8O",
  "elementId": "Stage_aB3kL9-t8GQTYo8O",
  "displayName": "Validate Submission Completeness",
  "isRequired": true,
  "type": "process",
  "data": {},
  "entryConditions": [
    {
      "id": "c4fGhJ2Mn",
      "displayName": "After Fetch Submission",
      "rules": [[{
        "rule": "selected-tasks-completed",
        "id": "rK9xQw3Lp",
        "selectedTasksIds": ["tSOURCE01"]
      }]]
    }
  ]
}
```

Keep sequential/parallel task grouping exactly as authored by the SDD. The
placeholder uses `data: {}` uniformly, including action and connector tasks.

### In-stage timer

Never placeholder a timer: it has no registry dependency. Use
[wait-for-timer](plugins/tasks/wait-for-timer/impl-json.md).

### Case-level event trigger

An unresolved event trigger retains the node render fields and
`data.inputs.serviceType: "Intsvc.EventTrigger"`, but no invented connector
identity. See [event trigger](plugins/triggers/event/impl-json.md).

### Connector condition rule

Use the sanctioned stub `uipath` block described by
[connector-trigger-impl.md](connector-trigger-impl.md). It is intentionally not
runnable and must be reported as a release blocker.

## Resolution evidence for a placeholder

```json
{
  "stage": "Submission Review",
  "task": "Validate Submission Completeness",
  "taskType": "process",
  "requested": {
    "name": "Validate Submission Completeness",
    "folder": "Shared/Claims",
    "identity": "<UNRESOLVED>"
  },
  "selected": null,
  "ioContract": null,
  "status": "placeholder",
  "rationale": "no exact registry match; user accepted placeholder fallback",
  "intendedBindings": {
    "lob": "=metadata.lob",
    "sourceDocs": "<- Submission Review/Fetch Submission/submissionData"
  }
}
```

This is the only durable deferred-wiring record. Do not duplicate it into a
human task list.

## Upgrade Procedure — Placeholder to resolved task

### 1. Refresh and resolve

With user approval, force-pull the registry when a stale cache is likely. Use
[registry-discovery.md](registry-discovery.md) to exact-match the intended
resource. For a local agent/API workflow sibling, use
`uip maestro case registry search "<name>" --type <agent|api> --local --output json`.

### 2. Fetch the runtime contract

- Non-connector: `uip maestro case tasks describe --type <type> --id <entityKey> --output json`.
- Connector: resolve connection, then use `uip maestro case spec --type
  <activity|trigger> ... --output json`.
- Local API workflow I/O fallback: flat entry-point properties, then the
  `input.schema.document.properties` wrapper, then root workflow schemas. Note
  any fallback in resolution evidence.

### 3. Edit in place

Keep task `id`, `elementId`, stage position, entry rules, and semantic locator.
Replace only `data` with the owning task recipe's fully resolved shape.

### 4. Bind I/O

Apply `intendedBindings` against the fetched schema. A named input/output absent
from the runtime contract is a deterministic mismatch; do not drop or rename it
silently. Cross-task references resolve through `id-map.json` and the source
task's real output contract.

### 5. Prove the upgrade

Update the evidence entry to `resolved`, then run `check-caseplan`,
`check-parity`, CLI validate, and preview/debug as appropriate. The placeholder
warning and release blocker must disappear.

## Completion report

List every remaining placeholder with stage, task, type, TaskId, intended
resource, unresolved reason, and the next exact resolution command. List inline
built resources separately as resolved. A placeholder means structure is
reviewable; it does not mean the case is releasable.

## Anti-patterns

- fake IDs, schemas, connections, or connector context;
- partial bindings on an empty placeholder schema;
- omitting authored entry rules;
- placeholders for built-in timer tasks;
- placeholdering an agent/API workflow that was created and verified inline;
- claiming debug/publish readiness while any accepted placeholder remains.

<!-- END: placeholder-tasks.md -->
