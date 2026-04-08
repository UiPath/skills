# Agentic Process Node — Planning

Agentic process nodes invoke published orchestration processes from within a flow. They are tenant-specific resources that appear in the registry after `uip login` + `uip flow registry pull`.

## Node Type Pattern

`uipath.core.agentic-process.{key}`

## When to Use

Use an Agentic Process node when the flow needs to invoke a published orchestration process.

### Selection Heuristics

| Situation | Use Agentic Process? |
| --- | --- |
| Invoke a published orchestration process | Yes |
| Invoke a published AI agent | No — use [Agent](../agent/planning.md) |
| Call another published flow | No — use [Flow](../flow/planning.md) |
| Need desktop/browser automation | No — use [RPA Workflow](../rpa/planning.md) |
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
uip flow registry search "uipath.core.agentic-process" --output json
```

Requires `uip login`. Only published agentic processes from your tenant appear.

## Planning Annotation

In the architectural plan:

- If the process exists: note as `resource: <name> (agentic-process)`
- If it does not exist: note as `[CREATE NEW] <description>`
