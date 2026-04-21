# API Workflow Node — Planning

API workflow nodes invoke API functions from within a flow. Published API workflows appear in the registry after `uip login` + `uip flow registry pull`. **In-solution** (unpublished) API workflows in sibling projects are discovered via `--local` — no login or publish required.

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
| API workflow not yet published but in the same solution | Yes — discover with `--local` (no login or publish needed) |
| API workflow does not exist yet | Create it in the same solution, then use `--local` discovery |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output` |

## Output Variables

- `$vars.{nodeId}.error` — error details if execution fails (`code`, `message`, `detail`, `category`, `status`)

## Discovery

### Published (tenant registry)

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.api-workflow" --output json
```

Requires `uip login`. Only published API workflows from your tenant appear.

### In-solution (sibling projects)

```bash
uip flow registry list --local --output json
uip flow registry get "<nodeType>" --local --output json
```

No login or publish required. Discovers unpublished API workflows in sibling projects within the same solution.

## Planning Annotation

In the architectural plan:

- If the API workflow exists: note as `resource: <name> (api-workflow)`
- If it does not exist: note as `[CREATE NEW] <description>`
