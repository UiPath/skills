# Flow Node — Planning

Flow nodes invoke other flows as subprocesses from within a flow. Published flows appear in the registry after `uip login` + `uip maestro flow registry pull`. **In-solution** (unpublished) flows in sibling projects are discovered via `--local` — no login or publish required.

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
| Flow in same solution but not yet published | Yes — use `--local` discovery (see below) |
| Flow not in the solution and not yet published | No — use `core.logic.mock` placeholder, create with `uipath-maestro-flow` |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output` |

## Output Variables

- `$vars.{nodeId}.error` — error details if execution fails (`code`, `message`, `detail`, `category`, `status`)

## Discovery

**Published (tenant registry):**

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.flow" --output json
```

Requires `uip login`. Only published flows from your tenant appear.

**In-solution (local, no login required):**

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry get "<nodeType>" --local --output json
```

Discovers unpublished flows in sibling projects within the same solution.

## Planning Annotation

In the architectural plan:

- If the flow exists: note as `resource: <name> (flow)`
- If it does not exist: note as `[CREATE NEW] <description>` with skill `uipath-maestro-flow`
