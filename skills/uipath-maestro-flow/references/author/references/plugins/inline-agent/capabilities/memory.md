# Memory Spaces

A memory space gives an agent dynamic few-shot retrieval over past cases (episodic memory backed by a tenant Memory Space resource).

> **Not available for autonomous inline agents (verified 2026-08).** The autonomous agent manifest — every shipped version, v1.3 current — declares handles `escalation`/`context`/`tool`/`input`/`success`/`error` only: **no `memory` handle** (platform-side TODO, pending memory support in the Agents runtime). Three independent blockers:
>
> 1. **No handle** — `flow validate` rejects a `memory`-port edge ("rewire to one of: escalation, context, tool, success, error").
> 2. **No manifest** — memory node types (`uipath.agent.resource.memory.<name>.<id>`) are minted by the canvas studio layer from AgentHub episodic memories, not by the registry the CLI reads; `registry search memory` returns zero types, so the definitions-or-nothing law ([impl.md § 3](../impl.md#3-manifest-and-definitions-contract)) cannot be satisfied.
> 3. **No `tool`-handle fallback** — unlike MCP servers, the memory node's own `input` handle accepts ONLY an agent `memory` handle, so it cannot attach via `tool`.
>
> When asked to add memory to an inline agent: **STOP and surface the limitation.** Do NOT author memory nodes, do NOT hand-fabricate a `definitions[]` entry, do NOT create `features/<id>/feature.json` in a sidecar.

## Alternatives

1. **Standalone agent with memory, attached as an agent tool.** Build the agent as a standalone low-code agent (owned by the `uipath-agents` skill — memory attaches there via `uip agent memory add`), publish it, then wire it to the flow's inline agent as a process-family agent tool ([process.md](process.md)). Memory lives inside the tool agent.
2. **Context grounding** ([context-index.md](context-index.md)) when the actual need is retrieval over reference content rather than recall of past agent runs.

## Re-Probe Before Assuming the Gap

Support ships platform-side when the autonomous manifest gains a `memory` handle and the registry mints memory manifests. Check both:

```bash
uip maestro flow registry get uipath.agent.autonomous --output json   # handleConfiguration gains a "memory" handle?
uip maestro flow registry search memory --output json                  # Data[] non-empty?
```

Both positive ⇒ authoring follows the universal recipe (impl.md § 7); until then this doc is the contract.

## Brownfield — Recognizing Memory in Legacy Artifacts

- **Legacy sidecar `features/<featureId>/feature.json`** (`$featureType: "memorySpace"` — a feature, NOT a resource) = memory attached under the old sidecar architecture (`uip agent memory add`). Leave it in place; never edit or delete it during a legacy-shell migration ([impl.md § 11](../impl.md#11-legacy-flows--detect-and-migrate)) — memory has no embedded representation, so the feature file is the only copy.
- **A canvas-hydrated legacy flow may carry a `uipath.agent.resource.memory.<name>.<id>` node wired to a `memory`-port edge.** The storage layer tolerates this (hydration preserves legacy memory), but `flow validate` rejects the edge. Do NOT delete the node or the edge to silence validate — a canvas save prunes any stored feature no node represents, so removal is data loss. Surface the conflict to the user and leave the cluster untouched.

## Conversational Agents

`uipath.agent.conversational` DOES declare a `memory` handle — but conversational inline agents are outside this plugin's scope (autonomous-only), and the type is not exposed on typical tenant registries.
