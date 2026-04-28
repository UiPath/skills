# UiPath Low-Code Agent Authoring

Entry point for low-code agent work. Read this first after low-code mode is detected.

## When to Use

- Create a new low-code agent project (standalone or inline in a flow)
- Edit `agent.json` — prompts, model, schemas, settings, resources
- Add tools to an agent: RPA processes, other agents, Integration Service connections
- Add RAG contexts (semantic index) and escalations (human-in-the-loop)
- Wire agent-to-agent calls within a solution or to an external deployed agent
- Design input/output schemas and sync with `entry-points.json`
- Validate agent project structure
- Publish agent to Studio Web, pack and deploy to Orchestrator

## Read These First

Read in this order before doing anything else:

1. **[critical-rules.md](critical-rules.md)** — the 16 Critical Rules and 13 anti-patterns. Always read first.
2. **[project-lifecycle.md](project-lifecycle.md)** — read when scaffolding a new project, validating, or running solution lifecycle commands. Contains the canonical end-to-end example for a new standalone agent.
3. **[agent-definition.md](agent-definition.md)** — read when editing `agent.json` (prompts, schemas, model settings) or `entry-points.json`. Covers contentTokens construction.
4. **[solution-resources.md](solution-resources.md)** — read when working with external tools, integration tools, indexes, or escalations (anything that needs `uip solution resource refresh`). Covers solution architecture, UUID cross-references, bindings, and debug_overwrites.

Then pick from the capability registry below.

## Capability Registry

| I need to... | Read first | Then |
|--------------|------------|------|
| Understand agent.json schema | [agent-definition.md](agent-definition.md) | |
| Edit system prompt or user message | [agent-definition.md](agent-definition.md) § Messages, § contentTokens | |
| Add/remove input or output fields | [agent-definition.md](agent-definition.md) § entry-points.json | |
| Scaffold a new agent project | [project-lifecycle.md](project-lifecycle.md) § End-to-End Example | [agent-definition.md](agent-definition.md) |
| Validate, upload, pack, publish, or deploy | [project-lifecycle.md](project-lifecycle.md) | |
| Discover solution resources (processes/apps/indexes/buckets/connections) | [project-lifecycle.md](project-lifecycle.md) § Resource Discovery | |
| Add a tool — pick the right kind | [capabilities/process/process.md](capabilities/process/process.md) | applicable sibling |
| Add an external Orchestrator process tool (RPA / agent / API / agentic) | [capabilities/process/external.md](capabilities/process/external.md) | [capabilities/process/solution-files.md](capabilities/process/solution-files.md) |
| Wire a solution-internal agent tool / multi-agent solution | [capabilities/process/solution-agent.md](capabilities/process/solution-agent.md) | |
| Add an Integration Service tool | [capabilities/integration-service/integration-service.md](capabilities/integration-service/integration-service.md) | |
| Add an MCP server tool | [capabilities/mcp/mcp.md](capabilities/mcp/mcp.md) | |
| Add a context (Context Grounding / attachments / DataFabric) | [capabilities/context/context.md](capabilities/context/context.md) | applicable sibling |
| Add an index-backed context (RAG) | [capabilities/context/index.md](capabilities/context/index.md) | |
| Add attachments context | [capabilities/context/attachments.md](capabilities/context/attachments.md) | |
| Add DataFabric entity-set context | [capabilities/context/datafabric.md](capabilities/context/datafabric.md) | |
| Add an Action Center escalation (HITL) | [capabilities/escalation/escalation.md](capabilities/escalation/escalation.md) | |
| Embed an agent inline in a flow | [capabilities/inline-in-flow/inline-in-flow.md](capabilities/inline-in-flow/inline-in-flow.md) | |
| Set up Orchestrator resources | Tell the user to use the `uipath-platform` skill | |
| Wire agent into a flow | Tell the user to use the `uipath-maestro-flow` skill | |

## Composing Multiple Capabilities

A single agent often combines a tool + a context + an escalation. Capabilities are **orthogonal** at the agent level — adding one does not constrain another. To compose:

1. Scaffold the agent project once via [project-lifecycle.md](project-lifecycle.md).
2. Apply each capability file independently — each adds its own `resources/{Name}/resource.json` and (if applicable) solution-level files.
3. Run `uip agent validate` once after all capability edits are complete (per Critical Rule 2 — validate after every bulk of edits, not after every single edit).
4. Run `uip solution resource refresh` once if any capability needs solution-level files (external tools, integration tools, index contexts, action center escalations).
5. Bundle and upload once.

There is no ordering requirement among capabilities. Working on a tool and an escalation in parallel is safe — they do not interact at the file level.

## Completion Output

After completing a task, report:

1. **File paths** — which files were created or modified
2. **What was configured** — summary of agent settings and schemas
3. **Validation result** — output of `uip agent validate --output json`; confirm `MigrationApplied`, `StorageVersion`, and `Validated` counts
4. **Schema sync status** — confirm agent.json and entry-points.json match
5. **Next steps** — suggest what the user should do next (publish, test in Studio Web, add resources)
