# Agent Job Recipe

Agent wrappers are `bpmn:serviceTask`. Choose the runtime contract from
discovery (`uip or processes list --all-fields`), not from the source project
label: coded Python dependencies may publish as `processType: "Function"`,
while low-code Agent Builder dependencies publish as `processType: "Agent"`.

| Agent deployment style | Wrapper shell | Notes |
| --- | --- | --- |
| Coded Python dependency published as `Function` | Use the process wrapper contract, not `StartAgentJob`, unless discovery documents a different wrapper | Resolve process identity, folder scope, input schema, and output schema before Operate. |
| Low-code Agent Builder agent published as `Agent` | `Orchestrator.StartAgentJob` shell | Use resolved process identity fields, generated bindings, and current input/output schema metadata. Do not claim executable success from local XML validation alone. |
| External A2A agent addressed by URL / skillId / authToken | `A2A.AgentExecution` | Studio Web renders this as an external A2A node and disables the Action dropdown. Do not use for folder-deployed agents — the canvas will treat the task as misconfigured. |
| Integration Service external agent | `Intsvc.SyncAgentExecution`, `Intsvc.AsyncAgentExecution`, or legacy `Intsvc.AsyncExecution` | CLI must enrich connector resource key, connection binding, dynamic schemas, and operation metadata. |

Local validation and packaging prove structure, not executable agent behavior;
claim runtime success only after an authorized target-environment run. Put
`JobArguments` and `Process response` directly under `uipath:activity`, not in a
sibling `uipath:mapping`.

The model may draft:

- Service task wrapper, variables, mappings, timeout/error paths, and validation gateways.
- Public-safe prompt/input and output variable names.
- A documented non-Integration-Service shell when resource metadata is known.

CLI or operator must resolve:

- Agent identity, version, folder binding, and generated resources.
- Dynamic input and output schemas.
- External-agent connector metadata for `Intsvc.*` variants.

Add HITL review when agent output drives high-impact decisions or irreversible actions.
