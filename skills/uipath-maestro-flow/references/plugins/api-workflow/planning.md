# API Workflow Node — Planning

API workflow nodes invoke published API functions from within a flow. They are tenant-specific resources that appear in the registry after `uip login` + `uip flow registry pull`.

## Node Type Pattern

`uipath.core.api-workflow.{key}`

## When to Use

Use an API Workflow node when the flow needs to call a published UiPath API function.

### Selection Heuristics

| Situation | Use API Workflow? |
| --- | --- |
| Call a published UiPath API function | Yes |
| Call an external REST API | No — use [HTTP](../http/planning.md) or [Connector](../connector/planning.md) |
| Invoke a published RPA process | No — use [RPA Workflow](../rpa/planning.md) |
| Resource not yet published | No — use `core.logic.mock` placeholder |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output` |

## Output Variables

- `$vars.{nodeId}.error` — error details if execution fails (`code`, `message`, `detail`, `category`, `status`)

## Discovery

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.api-workflow" --output json
```

Requires `uip login`. Only published API workflows from your tenant appear.

## Planning Annotation

In the architectural plan:

- If the API workflow exists: note as `resource: <name> (api-workflow)`
- If it does not exist: note as `[CREATE NEW] <description>`
