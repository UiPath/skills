# HITL Node — Implementation

HITL nodes pause the flow for human input via a UiPath App. Pattern: `uipath.core.human-task.{key}`.

## Discovery

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.human-task" --output json
```

## Registry Validation

```bash
uip maestro flow registry get "uipath.core.human-task.{key}" --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType` — `Actions.HITL`
- `model.bindings.resourceSubType` — the app type

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the node type and `model` fields from the JSON structure section in your registry validation.

The human task node's output (`$vars.{nodeId}.output`) contains the form data submitted by the user.

## Use Cases

- **Approval workflows** — manager approval before processing
- **Data validation** — human reviews extracted data before submission
- **Exception handling** — human resolves items the automation cannot handle

## Common Pattern — Human-in-the-Loop

```text
Manual Trigger -> RPA Process (extract) -> HITL (review) -> Decision (approved?) ->
  true: Script (submit) -> End
  false: End
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | App not published or registry stale | Run `uip login` then `uip maestro flow registry pull --force` |
| Task never completes | Human hasn't submitted the form | Check task assignment in Orchestrator |
| Output missing expected fields | App form doesn't match expected schema | Verify app form fields match what the flow expects |
