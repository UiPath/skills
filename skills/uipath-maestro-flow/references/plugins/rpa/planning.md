# RPA Node — Planning

RPA nodes invoke published RPA processes (XAML or coded C# workflows) from within a flow. They are tenant-specific resources that appear in the registry after `uip login` + `uip flow registry pull`.

## Node Type Pattern

`uipath.core.rpa-workflow.{key}`

## When to Use

Use an RPA node when the flow needs desktop/browser automation via a published RPA process.

### Selection Heuristics

| Situation | Use RPA? |
| --- | --- |
| Desktop/browser automation via a published RPA process | Yes |
| Target system has a REST API | No — use [Connector](../connector/planning.md) or [HTTP](../http/planning.md) |
| RPA process not yet published | No — use `core.logic.mock` placeholder, tell user to create with `uipath-rpa` |
| Need AI reasoning, not desktop automation | No — use [Agent](../agent/planning.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output` |

## Output Variables

- `$vars.{nodeId}.output` — the RPA process return value (structure depends on the process)
- `$vars.{nodeId}.error` — error details if execution fails (`code`, `message`, `detail`, `category`, `status`)

## Discovery

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.rpa-workflow" --output json
```

Requires `uip login`. Only published processes from your tenant appear.

## Planning Annotation

In the architectural plan:

- If the process exists: note as `resource: <name> (rpa-workflow)`
- If it does not exist: note as `[CREATE NEW] <description>` with skill `uipath-rpa`
