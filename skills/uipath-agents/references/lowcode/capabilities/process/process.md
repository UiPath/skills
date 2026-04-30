# Process Tool Capability

Tools that call a runnable process — RPA workflows, other agents, API workflows, or agentic processes (process orchestration). The target can be **inside the same solution** (a sibling project) or **already deployed in Orchestrator** (external). All process tools share the `$resourceType: "tool"` resource with one of these `type` values: `process` / `agent` / `api` / `processOrchestration`.

For Integration Service connector tools (a separate capability), see [../integration-service/integration-service.md](../integration-service/integration-service.md).

## When to Use

- Agent needs to invoke an RPA process, another agent, an API workflow, or an agentic process
- Calling either a project that lives in the **same solution** (solution-internal) or a process that is **already deployed in Orchestrator** (external)

## Variants

| Variant | `type` | `location` | When to use | Walkthrough |
|---|---|---|---|---|
| External RPA process | `process` | `external` | XAML workflow already deployed in Orchestrator | [external.md](external.md) |
| External agent | `agent` | `external` | Low-code or coded agent already deployed in Orchestrator | [external.md](external.md) |
| External API workflow | `api` | `external` | API workflow already deployed in Orchestrator | [external.md](external.md) |
| External agentic process | `processOrchestration` | `external` | Agentic process / process orchestration already deployed in Orchestrator | [external.md](external.md) |
| Solution RPA process | `process` | `solution` | RPA project in the **same solution** | [solution.md](solution.md) |
| Solution agent | `agent` | `solution` | Agent project in the **same solution** (parent-tool agent topology) | [solution.md](solution.md) |
| Solution API workflow | `api` | `solution` | API workflow project in the **same solution** | [solution.md](solution.md) |
| Solution agentic process | `processOrchestration` | `solution` | Agentic process project in the **same solution** | [solution.md](solution.md) |

## Decision

- **Same solution?** See [solution.md](solution.md) (4 variants). Discovery via `uip solution resource list --source local`; schemas come from each sibling project's `entry-points.json`. Solution-level files are auto-generated; no `debug_overwrites.json` is needed.
- **Already deployed in Orchestrator?** See [external.md](external.md) (4 variants). Discovery via `--source remote` + Releases API + `GetPackageEntryPointsV2`. Requires solution-level files and `debug_overwrites.json`.

## Lifecycle Overview

For all process tool variants:

1. **Discover** the target process (CLI + REST APIs as needed).
2. **Author** the agent-level `resources/{ToolName}/resource.json`.
3. **Validate** with `uip agent validate "<AGENT_NAME>" --output json` — emits `bindings_v2.json`.
4. **Refresh** solution resources with `uip solution resource refresh --output json` — auto-generates solution-level files for external tools.
5. **Bundle and upload** the solution.

## Sibling Files

- [external.md](external.md) — full walkthrough for the 4 external Orchestrator process types (RPA / agent / api / agentic process). Covers discovery via Releases API + GetPackageEntryPointsV2.
- [solution.md](solution.md) — full walkthrough for the 4 solution-internal process types (RPA / agent / api / agentic process). Covers discovery via `--source local` + `entry-points.json`. Includes the multi-agent solution topology.
- [solution-files.md](solution-files.md) — hand-authoring fallback reference for solution-level process and package declarations + debug_overwrites. **External tools only.** Used when `uip solution resource refresh` cannot auto-generate the files.

## Gotchas

See [../../critical-rules.md](../../critical-rules.md) Critical Rules 11, 12, 13. Anti-patterns 7, 8 also apply specifically to process tools.

## References

- [../../agent-definition.md](../../agent-definition.md) § Resources Convention
- [../../solution-resources.md](../../solution-resources.md) § Refresh Mechanics
- [../../project-lifecycle.md](../../project-lifecycle.md) § Resource Discovery
