# Agent Job Recipe

The current supported implementation wrapper for confirmed agent execution is
`bpmn:serviceTask`.

Supported shells:

- `Orchestrator.StartAgentJob` for UiPath agent jobs.
- `A2A.AgentExecution` for A2A agent execution.
- `Intsvc.SyncAgentExecution`, `Intsvc.AsyncAgentExecution`, or legacy `Intsvc.AsyncExecution` for Integration Service external-agent execution; these require CLI enrichment.

The model may draft:

- Service task wrapper, variables, mappings, timeout/error paths, and validation gateways.
- Public-safe prompt/input and output variable names.
- A documented non-Integration-Service shell when resource metadata is known.

CLI or operator must resolve:

- Agent identity, version, folder binding, and generated resources.
- Dynamic input and output schemas.
- External-agent connector metadata for `Intsvc.*` variants.

Add HITL review when agent output drives high-impact decisions or irreversible actions.
