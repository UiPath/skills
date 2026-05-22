# Agent Job Recipe

Agent wrappers are authored as `bpmn:serviceTask`, but the executable runtime
contract depends on the process type reported by
`uip or processes list --all-fields`, not the source project label. Some coded
Python "agents" are published as `processType: "Function"` and are not the same
runtime contract as low-code Agent Builder processes published as
`processType: "Agent"`.

| Agent deployment style | Wrapper shell | Notes |
| --- | --- | --- |
| Coded Python dependency published as `Function` | Not yet live-debug verified for `StartAgentJob` | Direct Orchestrator `jobs start` can work, but BPMN `StartAgentJob` may fault before creating a child job. Record `debug-instance incidents` and treat as a product/runtime blocker. |
| Low-code Agent Builder agent published as `Agent` | `Orchestrator.StartAgentJob` draft shell | Use resolved process identity fields. Current debug runs may still fault with `Required field 'releaseKey' missing in the input args to RPA task` after solution refresh imports the agent and debug variables show `releaseKey` populated; do not claim executable success until a tenant debug run proves it. |
| External A2A agent addressed by URL / skillId / authToken | `A2A.AgentExecution` | Studio Web renders this as an external A2A node and disables the Action dropdown. Do not use for folder-deployed agents — the canvas will treat the task as misconfigured. |
| Integration Service external agent | `Intsvc.SyncAgentExecution`, `Intsvc.AsyncAgentExecution`, or legacy `Intsvc.AsyncExecution` | CLI must enrich connector resource key, connection binding, dynamic schemas, and operation metadata. |

Common authoring mistake: assuming local validation or packaging proves the
agent wrapper is executable. The validator may accept stale shapes that fault
before child-job creation. Always inspect
`uip maestro bpmn debug-instance incidents <INSTANCE_ID> --output json` after a
faulted debug run.
If the incident reports a missing `releaseKey`, inspect
`uip maestro bpmn debug-instance variables <INSTANCE_ID> --output json` before
editing the XML. If variables already contain the process identity and no child
job exists in the target folder, treat the result as a wrapper/runtime blocker
rather than continuing to move the same fields between context, direct inputs,
`JobArguments`, and `body`.
Put the `JobArguments` input payload and `Process response` output payload as
direct children of `uipath:activity`; do not put them in a sibling
`uipath:mapping`.

The model may draft:

- Service task wrapper, variables, mappings, timeout/error paths, and validation gateways.
- Public-safe prompt/input and output variable names.
- A documented non-Integration-Service shell when resource metadata is known.

CLI or operator must resolve:

- Agent identity, version, folder binding, and generated resources.
- Dynamic input and output schemas.
- External-agent connector metadata for `Intsvc.*` variants.

Add HITL review when agent output drives high-impact decisions or irreversible actions.
