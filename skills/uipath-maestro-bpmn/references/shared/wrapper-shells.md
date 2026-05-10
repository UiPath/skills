# Minimal UiPath BPMN Wrapper Shells

Copyable, public-safe XML shells for each documented Maestro BPMN wrapper.
Use these as the starting point during pass 2 authoring; substitute synthetic
IDs and public-safe values for your project. Every shell shows the exact
required tokens (`bpmn:*` element class + `uipath:type value="..."`) used by
Maestro BPMN import and validation.

Anchors of every shell:

- `bpmn:<element>` element class is the model's choice; do not collapse to
  `bpmn:task` for any of these.
- `bpmn:extensionElements` wraps every `uipath:*` payload.
- `uipath:activity` (or `uipath:event` for message and Integration Service
  events) carries the wrapper kind through `<uipath:type value="..." version="v1" />`.
- Every `uipath:input` body that references a root variable uses
  `=vars.<variableId>`, not bare names.
- Every visible flow node and sequence flow needs matching `bpmndi:BPMNShape`
  / `bpmndi:BPMNEdge` entries; the shells below omit DI for brevity.

> Public-safe synthetic IDs only. Never paste real connection IDs, folder
> keys, tenant URLs, release keys, queue IDs, user names, or process names.

## Orchestrator.StartJob (RPA)

`bpmn:serviceTask` with `Orchestrator.StartJob`.

```xml
<bpmn:serviceTask id="Task_StartRpaJob" name="Start RPA Job">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Orchestrator.StartJob" version="v1" />
      <uipath:context>
        <uipath:input name="processName" type="string" value="Synthetic Process" />
      </uipath:context>
      <uipath:input name="inArgs" type="json" target="bodyField"><![CDATA[{"requestId":"=vars.Var_RequestId"}]]></uipath:input>
      <uipath:output name="JobId" type="string" var="Var_JobId" source="id" />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_RpaJob</bpmn:incoming>
  <bpmn:outgoing>Flow_RpaJob_Out</bpmn:outgoing>
</bpmn:serviceTask>
```

## Orchestrator.StartAgentJob (UiPath agent)

`bpmn:serviceTask` with `Orchestrator.StartAgentJob`.

```xml
<bpmn:serviceTask id="Task_StartAgentJob" name="Start Agent Job">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Orchestrator.StartAgentJob" version="v1" />
      <uipath:context>
        <uipath:input name="agentName" type="string" value="Synthetic Agent" />
      </uipath:context>
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_AgentJob</bpmn:incoming>
  <bpmn:outgoing>Flow_AgentJob_Out</bpmn:outgoing>
</bpmn:serviceTask>
```

## A2A.AgentExecution

`bpmn:serviceTask` with `A2A.AgentExecution`.

```xml
<bpmn:serviceTask id="Task_A2AAgent" name="A2A Agent">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="A2A.AgentExecution" version="v1" />
      <uipath:context />
      <uipath:input name="Prompt" type="string" value="Summarize the synthetic request." />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_A2A</bpmn:incoming>
  <bpmn:outgoing>Flow_A2A_Out</bpmn:outgoing>
</bpmn:serviceTask>
```

## Orchestrator.ExecuteApiWorkflowAsync

`bpmn:serviceTask` with `Orchestrator.ExecuteApiWorkflowAsync`.

```xml
<bpmn:serviceTask id="Task_ExecuteApiWorkflow" name="Execute API Workflow">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Orchestrator.ExecuteApiWorkflowAsync" version="v1" />
      <uipath:context />
      <uipath:input name="payload" type="json" target="bodyField"><![CDATA[{"requestId":"=vars.Var_RequestId"}]]></uipath:input>
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_ApiWorkflow</bpmn:incoming>
  <bpmn:outgoing>Flow_ApiWorkflow_Out</bpmn:outgoing>
</bpmn:serviceTask>
```

## Orchestrator.BusinessRules

`bpmn:businessRuleTask` with `Orchestrator.BusinessRules`.

```xml
<bpmn:businessRuleTask id="Task_BusinessRule" name="Evaluate Business Rule">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Orchestrator.BusinessRules" version="v1" />
      <uipath:context />
      <uipath:input name="facts" type="json" target="bodyField"><![CDATA[{"requestId":"=vars.Var_RequestId"}]]></uipath:input>
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_BusinessRule</bpmn:incoming>
  <bpmn:outgoing>Flow_BusinessRule_Out</bpmn:outgoing>
</bpmn:businessRuleTask>
```

## Orchestrator.CreateQueueItem

`bpmn:sendTask` with `Orchestrator.CreateQueueItem` (fire-and-continue).

```xml
<bpmn:sendTask id="Task_CreateQueueItem" name="Create Queue Item">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Orchestrator.CreateQueueItem" version="v1" />
      <uipath:context />
      <uipath:input name="itemData" type="json" target="bodyField"><![CDATA[{"requestId":"=vars.Var_RequestId"}]]></uipath:input>
      <uipath:output name="QueueItemId" type="string" var="Var_WorkItemId" source="id" />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_CreateQueue</bpmn:incoming>
  <bpmn:outgoing>Flow_CreateQueue_Out</bpmn:outgoing>
</bpmn:sendTask>
```

## Orchestrator.CreateAndWaitForQueueItem

`bpmn:serviceTask` with `Orchestrator.CreateAndWaitForQueueItem` (waits for completion).

```xml
<bpmn:serviceTask id="Task_WaitQueueItem" name="Create And Wait For Queue Item">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Orchestrator.CreateAndWaitForQueueItem" version="v1" />
      <uipath:context />
      <uipath:input name="reference" type="string" value="=vars.Var_WorkItemId" />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_WaitQueue</bpmn:incoming>
  <bpmn:outgoing>Flow_WaitQueue_Out</bpmn:outgoing>
</bpmn:serviceTask>
```

## Orchestrator.StartAgenticProcess (and Async variant)

`bpmn:callActivity` with `Orchestrator.StartAgenticProcess` for synchronous
or `Orchestrator.StartAgenticProcessAsync` for asynchronous calls.

```xml
<bpmn:callActivity id="Call_AgenticProcess" name="Call Agentic Process">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Orchestrator.StartAgenticProcess" version="v1" />
      <uipath:context />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_CallAgentic</bpmn:incoming>
  <bpmn:outgoing>Flow_CallAgentic_Out</bpmn:outgoing>
</bpmn:callActivity>

<bpmn:callActivity id="Call_AgenticProcessAsync" name="Call Agentic Process Async">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Orchestrator.StartAgenticProcessAsync" version="v1" />
      <uipath:context />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_CallAgenticAsync</bpmn:incoming>
  <bpmn:outgoing>Flow_CallAgenticAsync_Out</bpmn:outgoing>
</bpmn:callActivity>
```

## Orchestrator.StartCaseMgmtProcess (and Async variant) — preserve / draft only

`bpmn:callActivity` with `Orchestrator.StartCaseMgmtProcess` or
`Orchestrator.StartCaseMgmtProcessAsync`. Author only with a dedicated
case-management contract; otherwise preserve imported XML and mark
`uipath:caseManagement` payloads `preserve-only`.

```xml
<bpmn:callActivity id="Call_CaseManagement" name="Call Case Management">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Orchestrator.StartCaseMgmtProcess" version="v1" />
      <uipath:context />
    </uipath:activity>
    <uipath:caseManagement version="v1"><![CDATA[{"mode":"preserve-only","note":"Synthetic case-management payload"}]]></uipath:caseManagement>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_CallCase</bpmn:incoming>
  <bpmn:outgoing>Flow_CallCase_Out</bpmn:outgoing>
</bpmn:callActivity>

<bpmn:callActivity id="Call_CaseManagementAsync" name="Call Case Management Async">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Orchestrator.StartCaseMgmtProcessAsync" version="v1" />
      <uipath:context />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_CallCaseAsync</bpmn:incoming>
  <bpmn:outgoing>Flow_CallCaseAsync_Out</bpmn:outgoing>
</bpmn:callActivity>
```

## Maestro.SendMessageEvent

`bpmn:intermediateThrowEvent` with `Maestro.SendMessageEvent`. Pair with a
`bpmn:messageEventDefinition` so the event renders as a message throw.

```xml
<bpmn:intermediateThrowEvent id="Event_SendMessage" name="Send Message">
  <bpmn:extensionElements>
    <uipath:event version="v1">
      <uipath:type value="Maestro.SendMessageEvent" version="v1" />
      <uipath:context>
        <uipath:input name="messageName" type="string" value="SyntheticReply" />
        <uipath:input name="payload" type="json"><![CDATA[{"requestId":"=vars.Var_RequestId"}]]></uipath:input>
      </uipath:context>
    </uipath:event>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_SendMessage</bpmn:incoming>
  <bpmn:outgoing>Flow_SendMessage_Out</bpmn:outgoing>
  <bpmn:messageEventDefinition id="MessageDef_SyntheticReply" />
</bpmn:intermediateThrowEvent>
```

## Maestro.ReceiveMessageEvent

`bpmn:intermediateCatchEvent` (or `bpmn:startEvent` / `bpmn:boundaryEvent` for
the corresponding event positions) with `Maestro.ReceiveMessageEvent`.

```xml
<bpmn:intermediateCatchEvent id="Event_WaitForMessage" name="Wait For Message">
  <bpmn:extensionElements>
    <uipath:event version="v1">
      <uipath:type value="Maestro.ReceiveMessageEvent" version="v1" />
      <uipath:context>
        <uipath:input name="messageName" type="string" value="SyntheticItemReady" />
      </uipath:context>
    </uipath:event>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_WaitForMessage</bpmn:incoming>
  <bpmn:outgoing>Flow_WaitForMessage_Out</bpmn:outgoing>
  <bpmn:messageEventDefinition id="MessageDef_SyntheticItemReady" messageRef="Message_SyntheticItemReady" />
</bpmn:intermediateCatchEvent>
```

## Maestro.CasePlanScheduler — draft / preserve only

`bpmn:serviceTask` with `Maestro.CasePlanScheduler`. Mark
`preservation="draft-only"` (or `preserve-only`) until a dedicated
case-management contract is available; do not invent payload content.

```xml
<bpmn:serviceTask id="Task_CasePlanScheduler" name="Case Plan Scheduler">
  <bpmn:extensionElements>
    <uipath:activity version="v1" preservation="draft-only">
      <uipath:type value="Maestro.CasePlanScheduler" version="v1" />
      <uipath:context />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_CasePlanScheduler</bpmn:incoming>
  <bpmn:outgoing>Flow_CasePlanScheduler_Out</bpmn:outgoing>
</bpmn:serviceTask>
```

## Maestro.CaseManagerGuardrails — preserve only

`bpmn:serviceTask` with `Maestro.CaseManagerGuardrails`. Preserve imported
XML; do not author a new payload.

```xml
<bpmn:serviceTask id="Task_CaseManagerGuardrails" name="Case Manager Guardrails">
  <bpmn:extensionElements>
    <uipath:activity version="v1" preservation="preserve-only">
      <uipath:type value="Maestro.CaseManagerGuardrails" version="v1" />
      <uipath:context />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_CaseManagerGuardrails</bpmn:incoming>
  <bpmn:outgoing>Flow_CaseManagerGuardrails_Out</bpmn:outgoing>
</bpmn:serviceTask>
```

## Maestro.CaseRulesEvaluator — preserve only

`bpmn:serviceTask` with `Maestro.CaseRulesEvaluator`. Preserve imported XML.

```xml
<bpmn:serviceTask id="Task_CaseRulesEvaluator" name="Case Rules Evaluator">
  <bpmn:extensionElements>
    <uipath:activity version="v1" preservation="preserve-only">
      <uipath:type value="Maestro.CaseRulesEvaluator" version="v1" />
      <uipath:context />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_CaseRulesEvaluator</bpmn:incoming>
  <bpmn:outgoing>Flow_CaseRulesEvaluator_Out</bpmn:outgoing>
</bpmn:serviceTask>
```

## Actions.HITL

`bpmn:userTask` with `Actions.HITL`. Resource/form binding is resolved by
CLI or operator.

```xml
<bpmn:userTask id="Task_ReviewItem" name="Review Item">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Actions.HITL" version="v1" />
      <uipath:context />
      <uipath:output name="Outcome" type="string" var="Var_Outcome" source="outcome" />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_Review</bpmn:incoming>
  <bpmn:outgoing>Flow_Review_Out</bpmn:outgoing>
</bpmn:userTask>
```

## Intsvc.WaitForEvent — draft Integration Service shell

`bpmn:receiveTask` with `Intsvc.WaitForEvent`. The model owns the BPMN
wrapper, ID, name, and surrounding flow; the CLI owns connector resource
key, connection binding, dynamic schemas, and trigger property metadata.

```xml
<bpmn:receiveTask id="Task_WaitForExternalEvent" name="Wait For External Event">
  <bpmn:extensionElements>
    <uipath:event version="v1">
      <uipath:type value="Intsvc.WaitForEvent" version="v1" />
      <uipath:context>
        <uipath:input name="connectorKey" type="string" value="placeholder-connector" />
        <uipath:input name="eventName" type="string" value="placeholder-event" />
      </uipath:context>
    </uipath:event>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_WaitEvent</bpmn:incoming>
  <bpmn:outgoing>Flow_WaitEvent_Out</bpmn:outgoing>
  <bpmn:messageEventDefinition id="MessageDef_ExternalSignal" messageRef="Message_ExternalSignal" />
</bpmn:receiveTask>
```

For other `Intsvc.*` shells (`ActivityExecution`, `HttpExecution`,
`UnifiedHttpRequest`, `AsyncExecution`, `SyncAgentExecution`,
`AsyncAgentExecution`, `SyncWorkflowExecution`, `AsyncWorkflowExecution`,
`EventTrigger`, `TimerTrigger`), keep the same draft shape: model writes the
BPMN wrapper plus a `uipath:type` payload with placeholder strings only,
then hands enrichment to the CLI. See
[../author/references/plugins/integration-service/](../author/references/plugins/integration-service/).

## Preserve markers and migration metadata

Preserve these markers when present on import. Do not delete unknown
extension XML on a normal edit; pass them through.

```xml
<bpmn:process id="Process_ImportedExample" isExecutable="true">
  <bpmn:extensionElements>
    <uipath:variables version="v1">
      <!-- ... -->
    </uipath:variables>
    <uipath:migrationVersion version="5" />
    <uipath:migrationVersion version="11" />
    <uipath:migrationVersion version="11.5" />
  </bpmn:extensionElements>

  <bpmn:scriptTask id="Task_LegacyScript" name="Legacy Script" scriptFormat="JavaScript">
    <bpmn:extensionElements>
      <uipath:scriptVersion value="v2" />
      <uipath:Activity version="v1" preservation="unsupported"><![CDATA[{"kind":"generic","behavior":"preserve-only"}]]></uipath:Activity>
    </bpmn:extensionElements>
    <bpmn:script><![CDATA[
return { result: "preserved" };
]]></bpmn:script>
  </bpmn:scriptTask>
</bpmn:process>
```

Rules:

- `uipath:migrationVersion` is preserve-only. Numeric values such as `5`,
  `11`, and `11.5` carry import migration history; do not delete them.
- `uipath:scriptVersion value="v2"` is preserve-only on imported scripts.
  New script tasks prefer `value="v3"`.
- Unknown `uipath:Activity` payloads (capital `A`) and other unrecognized
  extension elements are preserve-only with `preservation="unsupported"`.
- `uipath:caseManagement` payloads stay `preserve-only` outside a dedicated
  case-management contract.

## Where to read more

- [bpmn-xml-contract.md](bpmn-xml-contract.md) - model-owned versus CLI-owned XML.
- [variables-bindings-expressions.md](variables-bindings-expressions.md) - variable id, binding, mapping, and expression rules.
- [../author/references/supported-elements.md](../author/references/supported-elements.md) - supported wrapper coverage map.
- [../author/references/task-recipes/](../author/references/task-recipes/) - per-recipe planning notes.
- [../author/references/plugins/integration-service/](../author/references/plugins/integration-service/) - Integration Service draft shell and CLI enrichment boundary.
- [../../fixtures/validation/contract-variants/contract-variants.bpmn](../../fixtures/validation/contract-variants/contract-variants.bpmn) - the canonical full fixture combining every shell above with BPMN DI.
