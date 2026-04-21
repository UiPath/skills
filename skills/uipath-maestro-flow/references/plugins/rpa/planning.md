# RPA Node — Planning

RPA nodes invoke RPA processes (XAML or coded C# workflows) from within a flow. Published processes appear in the registry after `uip login` + `uip flow registry pull`. **In-solution** (unpublished) processes in sibling projects are discovered via `--local` — no login or publish required.

## Node Type Pattern

`uipath.core.rpa-workflow.{key}`

## When to Use

Use an RPA node when the flow needs desktop/browser automation via a published RPA process.

### Selection Heuristics

| Situation | Use RPA? |
| --- | --- |
| Desktop/browser automation via a published RPA process | Yes |
| Target system has a REST API | No — use [Connector](../connector/planning.md) or [HTTP](../http/planning.md) |
| RPA process in the same solution but not yet published | Yes — use `--local` discovery (see below) |
| RPA process does not exist yet | Create it in the same solution with `uipath-rpa`, then use `--local` discovery |
| Need AI reasoning, not desktop automation | No — use [Agent](../agent/planning.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output` |

## Output Variables

- `$vars.{nodeId}.output` — the RPA process return value (structure depends on the process)
- `$vars.{nodeId}.error` — error details if execution fails (`code`, `message`, `detail`, `category`, `status`)

## Discovery

**Published (tenant registry):**

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.rpa-workflow" --output json
```

Requires `uip login`. Only published processes from your tenant appear.

**In-solution (local, no login required):**

```bash
uip flow registry list --local --output json
uip flow registry get "<nodeType>" --local --output json
```

Run from inside the flow project directory. Discovers sibling RPA projects in the same `.uipx` solution.

## Planning Annotation

In the architectural plan:

- If the process exists: note as `resource: <name> (rpa-workflow)`
- If it does not exist: note as `[CREATE NEW] <description>` with skill `uipath-rpa`
