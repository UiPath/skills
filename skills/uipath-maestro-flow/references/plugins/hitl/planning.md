# HITL Node — Planning

HITL nodes pause the flow and present a UiPath App to a human user for input. The flow resumes when the user submits the form. They are tenant-specific resources that appear in the registry after `uip login` + `uip flow registry pull`.

## Node Type Pattern

`uipath.core.human-task.{key}`

## When to Use

Use a HITL node when the flow needs to pause for human input, approval, or review.

### Selection Heuristics

| Situation | Use HITL? |
| --- | --- |
| Manager approval before processing | Yes |
| Human reviews extracted data before submission | Yes |
| Human resolves items the automation cannot handle | Yes |
| Fully automated processing with no human involvement | No |
| App not yet published | No — use `core.logic.mock` placeholder, tell user to create with `uipath-coded-apps` |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output` |

## Output Variables

- `$vars.{nodeId}.output` — the form data submitted by the user
- `$vars.{nodeId}.error` — error details if execution fails (`code`, `message`, `detail`, `category`, `status`)

## Discovery

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.human-task" --output json
```

Requires `uip login`. Only published apps from your tenant appear.

## Planning Annotation

In the architectural plan:

- If the app exists: note as `resource: <name> (human-task)`
- If it does not exist: note as `[CREATE NEW] <description>` with skill `uipath-coded-apps`
