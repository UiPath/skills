# HITL Node — Implementation

HITL nodes pause the flow for human input via a UiPath App. Pattern: `uipath.core.human-task.{key}`.

## Discovery

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.human-task" --output json
```

## Registry Validation

```bash
uip flow registry get "uipath.core.human-task.{key}" --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType` — `Actions.HITL`
- `model.bindings.resourceSubType` — the app type

## Adding via CLI

```bash
uip flow node add <ProjectName>.flow "uipath.core.human-task.{key}" --output json \
  --label "Review Data" \
  --position 400,300
```

## Wiring Pattern

```
[Automation nodes] -> [HITL] -> [Continue with human's input]
```

The human task node's output (`$vars.{nodeId}.output`) contains the form data submitted by the user.

## Use Cases

- **Approval workflows** — manager approval before processing
- **Data validation** — human reviews extracted data before submission
- **Exception handling** — human resolves items the automation cannot handle

## Common Pattern — Human-in-the-Loop

```
Manual Trigger -> RPA Process (extract) -> HITL (review) -> Decision (approved?) ->
  true: Script (submit) -> End
  false: End
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | App not published or registry stale | Run `uip login` then `uip flow registry pull --force` |
| Task never completes | Human hasn't submitted the form | Check task assignment in Orchestrator |
| Output missing expected fields | App form doesn't match expected schema | Verify app form fields match what the flow expects |
