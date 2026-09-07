# Flow Node — Planning

<!--skill-flavor:flow-intro:start-->
Flow nodes invoke other flows as subprocesses from within a flow. Published flows appear in the registry after `uip login` + `uip maestro flow registry pull`. **In-solution** (unpublished) flows in sibling projects are discovered via `--local` — no login or publish required.
<!--skill-flavor:flow-intro:end-->

## Node Type Pattern

`uipath.core.flow.{key}`

## When to Use

Use a Flow node when you need to call another published flow as a subprocess.

### Selection Heuristics

<!--skill-flavor:flow-selection-table:start-->
| Situation | Use Flow? |
| --- | --- |
| Call another published flow as a subprocess | Yes |
| Group related steps with isolated scope (within same project) | No — use [Subflow](../subflow/planning.md) |
| Invoke a published orchestration process | No — use [Agentic Process](../agentic-process/planning.md) |
| Flow not yet published but in the same solution | Yes — discover with `--local` (no login or publish needed) |
| Flow does not exist yet | Create it in the same solution with `uipath-maestro-flow`, then use `--local` discovery |
<!--skill-flavor:flow-selection-table:end-->

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output` |

## Output Variables

- `$vars.{nodeId}.error` — error details if execution fails (`code`, `message`, `detail`, `category`, `status`)

## Discovery

<!--skill-flavor:flow-discovery:start-->
### Published (tenant registry)

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.flow" --output json
```

Requires `uip login`. Only published flows from your tenant appear.

### In-solution (sibling projects)

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry get "<node-type>" --local --output json
```

No login or publish required. Discovers unpublished flows in sibling projects within the same solution.
<!--skill-flavor:flow-discovery:end-->

## Planning Annotation

In the architectural plan:

- If the flow exists: note as `resource: <name> (flow)`
- If it does not exist: note as `[CREATE NEW] <description>` with skill `uipath-maestro-flow`
