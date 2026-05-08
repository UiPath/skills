---
name: uipath-integration-service
description: "UiPath Integration Service via the `uip is` CLI — connectors, connections, activities, triggers, and the reference-resolution model that ties IS resources to agent workflows. Use this BEFORE writing any code that talks to Integration Service APIs directly."
when_to_use: "User wants to manage Integration Service: list connectors, create or list connections, browse activities, set up IS triggers, or resolve agent-workflow references against IS connectors. Triggers: 'list connectors', 'add a Slack/Salesforce/Jira connection', 'set up an IS trigger', 'find activities for connector X', 'resolve a reference from agent workflow', 'IS reference resolution'. NOT for Orchestrator triggers/webhooks (→uipath-resources). NOT for Orchestrator admin (→uipath-orchestrator)."
allowed-tools: Bash, Read, Write, Glob, Grep
---

# UiPath Integration Service

Manage Integration Service (IS) resources via `uip is`: connectors, connections, activities, triggers, and the reference-resolution model used by agent workflows.

## Use the CLI. Don't roll your own REST.

**Always use `uip is <subject> <verb>` commands**. The IS APIs are not stable across regions/realms in the way Orchestrator's are; the CLI handles routing, auth scopes, and the multi-step reference-resolution flow that agent workflows depend on. Hand-rolled HTTP almost always misses one of those.

## When to Use This Skill

- **Concept overview** — connector/connection/activity model, IS in agentic workflows → [integration-service.md](references/integration-service.md)
- **Connectors** — list, get details, browse capabilities → [connectors.md](references/connectors.md)
- **Connections** — create, list, switch credentials, manage tokens → [connections.md](references/connections.md)
- **Activities** — discover what calls a connector exposes → [activities.md](references/activities.md)
- **Triggers** — schedule events from IS into agent workflows → [triggers.md](references/triggers.md)
- **Resources used in agent workflows** → [resources.md](references/resources.md)
- **Agent workflow integration** — how IS references resolve at runtime → [agent-workflow.md](references/agent-workflow.md)
- **Reference resolution** — the multi-step lookup chain → [reference-resolution.md](references/reference-resolution.md)

## Output Conventions

- Always pass `--output json` when scripting; the envelope is `{ Result, Code, Data, Pagination? }`.

## Cross-skill references

- Orchestrator triggers/webhooks (a different mechanism) → [`uipath-resources`](../uipath-resources/references/triggers-and-webhooks.md)
- Orchestrator admin → [`uipath-orchestrator`](../uipath-orchestrator/SKILL.md)
- Solution lifecycle → [`uipath-solution`](../uipath-solution/SKILL.md)
- Login, global flags → [`uipath-cli`](../uipath-cli/SKILL.md)
