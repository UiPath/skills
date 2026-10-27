# Critical Rules and Anti-Patterns - Autonomous Low-Code Agents

These rules are the canonical source for rules specific to low-code autonomous agent authoring, in addition to the shared rules defined in [critical-rules.md](critical-rules.md). Capability files cross-reference back here; they do not restate rules.

## Critical Rules

1. **Inline autonomous agents in flows use `uipath.agent.autonomous` nodes.** The node's `inputs.source` references the inline agent's `projectId` UUID. Attached resource nodes (`uipath.agent.resource.tool.*`, `uipath.agent.resource.escalation`, `uipath.agent.resource.context.*`) use the same `inputs.source` convention to reference their `<RES_UUID>` subdirectory under `<projectId>/resources/`. The definition still declares `model.source: true`, but flow-core hoists the source identity onto `inputs.source` for the node instance; no node instance carries an instance `model` block. The agent definition lives in a subdirectory inside the flow project. See [../capabilities/inline-in-flow/inline-in-flow.md](../capabilities/inline-in-flow/inline-in-flow.md).

2. **Use `uip agent memory` for memory spaces and memory items.** `memory add` owns `features/{FeatureName}/feature.json` and, inside a solution, declares or links the memory space as a solution resource (check `Data.SolutionResource.Status`); `--folder-path` is only needed outside a solution or for a space in another folder. `memory item add/list` work on the runtime store after deploy: episodic items need `--feedback-id`, escalation items need `--trace-id` and `--span-id`, and both need the deployment folder via `--folder-path` or `--folder-key` when the feature points at `solution_folder`. Run `uip agent refresh --output json` and `uip agent validate --output json` after memory changes. See [../capabilities/memory/memory.md](../capabilities/memory/memory.md).

## What NOT to Do

1. **Always include `"guardrail": { "policies": [] }` in every tool resource.json, and never populate `policies` with entries** — the field must be present for backward-compatible solution loading; omitting it causes the runtime to fail. All guardrails are configured at the agent.json root `guardrails` array with `selector.scopes` and `selector.matchNames`. **This anti-pattern is autonomous-only — for conversational agents, populate `policies` per-tool per [conversational-critical-rules.md](conversational-critical-rules.md) Critical Rule 1 + Anti-pattern 2.**

2. **Do not hand-edit memory feature files for routine changes** — use `uip agent memory add/list/remove` and `uip agent memory item add/list`. Hand-writing `features/{Name}/feature.json` or `bindings_v2.json` can desynchronize generated state and skip CLI validation for search mode, field weights, and the solution link. Do not try to seed memory items from files: the runtime store only accepts items promoted from real runs.
