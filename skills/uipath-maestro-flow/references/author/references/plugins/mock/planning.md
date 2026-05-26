# Mock — Planning

## Node Type

`core.logic.mock`

## When to Use

Use a Mock as a placeholder when a step is still to-be-determined, you are prototyping the topology, or a resource (RPA process, agent, flow, app) the flow needs **does not exist in the solution and is not yet published**. The mock holds the slot with a simple `input` → `output` pass-through so the rest of the flow can be wired and validated.

### Selection Heuristics

| Situation | Use Mock? |
| --- | --- |
| Resource is TBD / prototyping the shape of the flow | Yes — placeholder, resolve later |
| Resource exists as a sibling project in the same solution | **No** — use `--local` discovery and add the real resource node ([planning-arch.md](../../planning-arch.md)) |
| Resource is published on the tenant | **No** — add the real resource node |
| A registered connector operation exists but has no live connection | **No** — add the real connector node and surface "configure pending" as an Open Question (see [connector/planning.md](../connector/planning.md)) |

> **Mocks are only for resources that are neither in the current solution nor published** (see [Anti-patterns](../../../CAPABILITY.md#anti-patterns)). Beyond that rule: never reach for a mock to dodge a *configuration* step — a missing connection or missing tenant access is not a missing resource. Add the real node and report the gap in Open Questions.

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `output` |

## Key Inputs

None. The mock has no required inputs; `output` carries a placeholder object.

## Replacing a Mock

Every mock is a debt to resolve before publish. For each mock node:

1. Check in-solution discovery first: `uip maestro flow registry list --local --output json`
2. If found locally: replace the mock with the in-solution resource node type, update inputs/outputs.
3. If not found locally, check the tenant registry: `uip maestro flow registry search "<name>" --output json`
4. If published: replace the mock with the real resource node type, update inputs/outputs.
5. If found in neither: keep the mock and note it in the **Open Questions** section for user resolution.

Step-by-step Edit/Write procedure: [Replace a mock with a real resource node](../../editing-operations-json.md#replace-a-mock-with-a-real-resource-node).

## Key Rules

- A mock is a **placeholder, not a destination** — every mock left at publish time is an unresolved gap; surface it in Open Questions.
- Prefer in-solution (`--local`) resources over mocks whenever the sibling project exists.
- The mock's `input` → `output` shape lets `flow validate` pass while the real node is pending.
