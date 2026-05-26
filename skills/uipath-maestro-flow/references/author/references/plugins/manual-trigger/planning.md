# Manual Trigger — Planning

## Node Type

`core.trigger.manual`

## When to Use

Use a Manual Trigger to start the flow on demand — by a user action, a parent flow, or an API call — rather than on a schedule or an external event.

> **Normally inherited from `flow init`.** A freshly scaffolded `.flow` already contains a `core.trigger.manual` node (id `start`) **and its definition**. In the common greenfield path you never add a manual trigger or its definition — you inherit both. Add one by hand only when **rebuilding** a flow, **swapping** another trigger type back to manual, or authoring a subflow entry point.

### Selection Heuristics

| Situation | Use Manual Trigger? |
| --- | --- |
| Flow started on demand by a user, parent flow, or API call | Yes (default — usually already scaffolded) |
| Flow runs on a recurring schedule | No — use `core.trigger.scheduled` ([scheduled-trigger](../scheduled-trigger/planning.md)) |
| Flow starts from an external service event (new email, new row, …) | No — use a connector trigger ([connector-trigger](../connector-trigger/planning.md)) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| — (none) | `output` |

The output port forbids targeting other trigger nodes (a flow has exactly one trigger).

## Key Inputs

| Input | Required | Description |
| --- | --- | --- |
| `entryPointId` | Yes | Stable UUID identifying the entry point. Instance-specific — lives under `inputs`, not in the definition. |
| `isDefaultEntryPoint` | Conditional | Boolean; set on trigger nodes inside a subflow with multiple entry points. |

Manual trigger has no other inputs — it passes data through `inputs` supplied at invocation, surfaced on `output`.

## Key Rules

- Every flow must have **exactly one** trigger node — manual, scheduled, or a connector trigger; never two.
- The trigger is always the first node in the topology.
- A manual and a scheduled trigger cannot coexist — to switch, replace one with the other (see [scheduled-trigger](../scheduled-trigger/planning.md) and the Edit/Write recipe [Replace manual trigger with scheduled trigger](../../editing-operations-json.md#replace-manual-trigger-with-scheduled-trigger)).
