# Supported Elements

Use this supported coverage map before choosing a BPMN wrapper or UiPath extension type. Treat anything outside this map as preserve-only unless a newer product contract says otherwise.

## Modeling rule

Pick the BPMN element first, then pick the UiPath execution recipe.

- RPA workflows, agents, API workflows, and most async external executions are `bpmn:serviceTask`.
- Queue item creation is `bpmn:sendTask`; create-and-wait queue work is `bpmn:serviceTask`.
- Business rules are `bpmn:businessRuleTask`.
- HITL is `bpmn:userTask`.
- Agentic process and case-management process calls are `bpmn:callActivity`.
- Integration Service waits are `bpmn:receiveTask` or event wrappers, and their executable metadata is CLI-owned.
- Script work is `bpmn:scriptTask`; it is not a generic service task.

## Standard BPMN coverage

The model may author these standard BPMN structures when the process intent is clear and every visible element has BPMN DI.

| Family | Supported elements |
| --- | --- |
| Events | `bpmn:startEvent`, `bpmn:endEvent`, `bpmn:intermediateCatchEvent`, `bpmn:intermediateThrowEvent`, `bpmn:boundaryEvent` |
| Event definitions | none, message, timer, conditional, signal, error, escalation, link, compensate, terminate where valid for that event kind |
| Gateways | `bpmn:exclusiveGateway`, `bpmn:inclusiveGateway`, `bpmn:parallelGateway`, `bpmn:eventBasedGateway`, `bpmn:complexGateway` |
| Tasks | `bpmn:task`, `bpmn:serviceTask`, `bpmn:sendTask`, `bpmn:receiveTask`, `bpmn:userTask`, `bpmn:manualTask`, `bpmn:businessRuleTask`, `bpmn:scriptTask` |
| Containers | `bpmn:subProcess`, event subprocess, `bpmn:callActivity`, `bpmn:adHocSubProcess` for preservation or explicit user intent |
| Flow | `bpmn:sequenceFlow` with source, target, optional condition, optional default references on gateways |
| Definitions | `bpmn:message`, `bpmn:signal`, `bpmn:error`, `bpmn:escalation`, item definitions, data objects, data stores, participants when required by the model |

`bpmn:transaction` can appear in imported projects, but do not generate new executable transaction flows until there is a dedicated execution contract. Preserve imported transactions unless the user asks to normalize.

## UiPath extension coverage

Use lower-case XML tags in authored examples: `uipath:activity`, `uipath:event`, and `uipath:mapping`.

| Extension type | BPMN wrapper | XML tag | Ownership |
| --- | --- | --- | --- |
| `BPMN.Variables` | `bpmn:task`, start/end mapping contexts | `uipath:mapping` | Model-owned |
| `BPMN.ScriptTask` | `bpmn:scriptTask` | `uipath:mapping` plus `uipath:scriptVersion` | Model-owned; parser executes as `Scp.Script` |
| `Actions.HITL` | `bpmn:userTask` | `uipath:activity` | Model may draft shell; resource/form binding resolved by CLI or operator |
| `Orchestrator.StartJob` | `bpmn:serviceTask` | `uipath:activity` | Model may draft shell; resource binding and schemas resolved by CLI or operator |
| `Orchestrator.StartAgentJob` | `bpmn:serviceTask` | `uipath:activity` | Model may draft shell; agent binding and schemas resolved by CLI or operator |
| `A2A.AgentExecution` | `bpmn:serviceTask` | `uipath:activity` | Model may draft shell; agent metadata resolved by CLI or operator |
| `Orchestrator.ExecuteApiWorkflowAsync` | `bpmn:serviceTask` | `uipath:activity` | Model may draft shell; API workflow binding and schemas resolved by CLI or operator |
| `Orchestrator.CreateQueueItem` | `bpmn:sendTask` | `uipath:activity` | Model may draft shell; queue binding resolved by CLI or operator |
| `Orchestrator.CreateAndWaitForQueueItem` | `bpmn:serviceTask` | `uipath:activity` | Model may draft shell; queue binding and callback behavior resolved by CLI or operator |
| `Orchestrator.BusinessRules` | `bpmn:businessRuleTask` | `uipath:activity` | Model may draft shell; rule binding and schemas resolved by CLI or operator |
| `Orchestrator.StartAgenticProcess` | `bpmn:callActivity` | `uipath:activity` | Model may draft shell; called process binding resolved by CLI or operator |
| `Orchestrator.StartAgenticProcessAsync` | `bpmn:callActivity` | `uipath:activity` | Model may draft shell; called process binding resolved by CLI or operator |
| `Orchestrator.StartCaseMgmtProcess` | `bpmn:callActivity` | `uipath:activity` | Preserve or draft only with a dedicated case-management contract |
| `Orchestrator.StartCaseMgmtProcessAsync` | `bpmn:callActivity` | `uipath:activity` | Preserve or draft only with a dedicated case-management contract |
| `Maestro.ReceiveMessageEvent` | start, intermediate catch, or boundary message event | `uipath:event` | Model-owned when message name and public-safe payload contract are known |
| `Maestro.SendMessageEvent` | intermediate throw or end message event | `uipath:event` | Model-owned when message name and public-safe payload contract are known |
| `Maestro.CasePlanScheduler` | `bpmn:serviceTask` | `uipath:activity` | Preserve or draft only with a dedicated case-management contract |
| `Maestro.CaseManagerGuardrails` | `bpmn:serviceTask` | `uipath:activity` | Preserve-only until documented |
| `Maestro.CaseRulesEvaluator` | `bpmn:serviceTask` | `uipath:activity` | Preserve-only until documented |
| `Intsvc.ActivityExecution` | `bpmn:sendTask` and supported event wrappers | `uipath:activity` | CLI-owned enrichment |
| `Intsvc.HttpExecution` | `bpmn:sendTask` or intermediate throw | `uipath:activity` | CLI-owned enrichment |
| `Intsvc.UnifiedHttpRequest` | `bpmn:sendTask` or intermediate throw | `uipath:activity` | CLI-owned enrichment |
| `Intsvc.AsyncExecution` | `bpmn:serviceTask` | `uipath:activity` | CLI-owned enrichment |
| `Intsvc.SyncAgentExecution` | `bpmn:serviceTask` | `uipath:activity` | CLI-owned enrichment |
| `Intsvc.AsyncAgentExecution` | `bpmn:serviceTask` | `uipath:activity` | CLI-owned enrichment |
| `Intsvc.SyncWorkflowExecution` | `bpmn:serviceTask` | `uipath:activity` | CLI-owned enrichment |
| `Intsvc.AsyncWorkflowExecution` | `bpmn:serviceTask` | `uipath:activity` | CLI-owned enrichment |
| `Intsvc.EventTrigger` | message start event | `uipath:event` | CLI-owned enrichment |
| `Intsvc.TimerTrigger` | timer start event | `uipath:activity` | CLI-owned enrichment |
| `Intsvc.WaitForEvent` | `bpmn:receiveTask`, intermediate catch, or boundary message event | `uipath:event` | CLI-owned enrichment |

## Script task runtime

Script tasks execute JavaScript through Jint, not Node.js or a browser runtime.

- Use `bpmn:scriptTask scriptFormat="JavaScript"`.
- Put source in `bpmn:script` CDATA and include `uipath:scriptVersion`; prefer `v3`.
- Inputs are exposed as named JavaScript variables after Maestro maps inputs into an `args` JSON body.
- Available helpers are limited to `uipath.aggregate`, `uipath._aggregate`, `uipath._pipe`, and a no-op `console`.
- There is a 64 MB memory limit and a 30 second execution timeout.
- Do not use packages, filesystem, network, browser globals, or long-running async behavior.
- For version `v2` and later the script may return any JSON value under `response`; older versions must return a JSON object.

## Integration Service boundary

For `Intsvc.*` elements, the model may author the surrounding BPMN shell, variables, mappings, error paths, and diagram geometry. The CLI must enrich connector key, operation/event metadata, connection binding, trigger property bindings, schemas, generated outputs, `bindings_v2.json`, and package metadata before upload or run.

## Preservation boundary

If an imported file contains extension types not listed here, preserve them and report that the skill cannot safely regenerate them. Do not delete unknown extensions unless the user explicitly asks for normalization.
