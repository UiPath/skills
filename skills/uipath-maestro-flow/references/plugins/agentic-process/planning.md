# Agentic Process Node — Planning

Agentic process nodes invoke orchestration processes from within a flow. Published processes appear in the registry after `uip login` + `uip flow registry pull`. **In-solution** (unpublished) processes in sibling projects are discovered via `--local` — no login or publish required.

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
| Process not yet published but in the same solution | Yes — discover with `--local` (no login or publish needed) |
| Process does not exist yet | Create it in the same solution, then use `--local` discovery |

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
uip flow registry search "uipath.core.agentic-process" --output json
```

Requires `uip login`. Only published agentic processes from your tenant appear.

### In-solution (sibling projects)

```bash
uip flow registry list --local --output json
uip flow registry get "<nodeType>" --local --output json
```

No login or publish required. Discovers unpublished agentic processes in sibling projects within the same solution.

## Planning Annotation

In the architectural plan:

- If the process exists: note as `resource: <name> (agentic-process)`
- If it does not exist: note as `[CREATE NEW] <description>`
