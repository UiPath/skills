# Flow Node — Planning

Flow nodes invoke other published flows as subprocesses from within a flow. They are tenant-specific resources that appear in the registry after `uip login` + `uip flow registry pull`.

## Node Type Pattern

`uipath.core.flow.{key}`

## When to Use

Use a Flow node when you need to call another published flow as a subprocess.

### Selection Heuristics

| Situation | Use Flow? |
| --- | --- |
| Call another published flow as a subprocess | Yes |
| Group related steps with isolated scope (within same project) | No — use [Subflow](../subflow/planning.md) |
| Invoke a published orchestration process | No — use [Agentic Process](../agentic-process/planning.md) |
| Flow not yet published | No — use `core.logic.mock` placeholder, create with `uipath-maestro-flow` |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output` |

## Output Variables

- `$vars.{nodeId}.error` — error details if execution fails (`code`, `message`, `detail`, `category`, `status`)

## Discovery

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.flow" --output json
```

Requires `uip login`. Only published flows from your tenant appear.

## Planning Annotation

In the architectural plan:

- If the flow exists: note as `resource: <name> (flow)`
- If it does not exist: note as `[CREATE NEW] <description>` with skill `uipath-maestro-flow`
