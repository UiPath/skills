# Agent Job Recipe

The current supported implementation wrapper for confirmed agent execution is
`bpmn:serviceTask`. Pick the shell from agent deployment style, not from the
agent's implementation language. Coded Python agents (LangGraph / LlamaIndex /
OpenAI Agents) and low-code Agent Builder agents use the same wire format when
both are deployed to an Orchestrator folder.

| Agent deployment style | Wrapper shell | Notes |
| --- | --- | --- |
| Coded Python agent published to an Orchestrator folder | `Orchestrator.StartAgentJob` | Required binding pair: two `uipath:binding` entries sharing one `resourceKey`, `resource="process"`, `resourceSubType="Agent"`, with `propertyAttribute="name"` and `propertyAttribute="folderPath"`. Context inputs MUST be `name` and `folderPath`, both `value="=bindings.<bindingId>"`. Studio Web's palette generates this shape under the "Coded Agent" service-task option. |
| Low-code Agent Builder agent published to an Orchestrator folder | `Orchestrator.StartAgentJob` | Identical wire format to the coded case above. Agent type is opaque at the BPMN layer. |
| External A2A agent addressed by URL / skillId / authToken | `A2A.AgentExecution` | Studio Web renders this as an external A2A node and disables the Action dropdown. Do not use for folder-deployed agents — the canvas will treat the task as misconfigured. |
| Integration Service external agent | `Intsvc.SyncAgentExecution`, `Intsvc.AsyncAgentExecution`, or legacy `Intsvc.AsyncExecution` | CLI must enrich connector resource key, connection binding, dynamic schemas, and operation metadata. |

Common authoring mistake: drafting `Orchestrator.StartAgentJob` with a literal
`agentName` context input, or with `releaseKey` / `folderId`. The Maestro
BPMN packager validator rejects all three. Always use the binding-pair shape
shown in
[../../../shared/wrapper-shells.md](../../../shared/wrapper-shells.md#orchestratorstartagentjob-folder-deployed-agent--coded-python-or-low-code)
and in the
[agent-invocation fixture](../../../../fixtures/validation/agent-invocation/).

The model may draft:

- Service task wrapper, variables, mappings, timeout/error paths, and validation gateways.
- Public-safe prompt/input and output variable names.
- A documented non-Integration-Service shell when resource metadata is known.

CLI or operator must resolve:

- Agent identity, version, folder binding, and generated resources.
- Dynamic input and output schemas.
- External-agent connector metadata for `Intsvc.*` variants.

Add HITL review when agent output drives high-impact decisions or irreversible actions.
