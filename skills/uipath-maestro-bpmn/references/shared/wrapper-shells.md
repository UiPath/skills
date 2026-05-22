# Minimal UiPath BPMN Wrapper Shells

Copyable, public-safe XML shells for each documented Maestro BPMN wrapper.
Use these as the starting point during pass 2 authoring; substitute synthetic
IDs and public-safe values for your project. Every shell shows the exact
required tokens (`bpmn:*` element class + `uipath:type value="..."`) used by
Maestro BPMN import and validation.

Anchors of every shell:

- New BPMN files must declare `xmlns:uipath="http://uipath.org/schema/bpmn"`
  on `bpmn:definitions`. Do not use
  `http://schemas.uipath.com/workflow/activities`.
- `bpmn:<element>` element class is the model's choice; do not collapse to
  `bpmn:task` for any of these.
- `bpmn:extensionElements` wraps every `uipath:*` payload.
- `uipath:activity` or `uipath:event` carries the wrapper kind through
  `<uipath:type value="..." version="v1" />`.
- Do not use legacy shorthand such as `<uipath:activity type="...">` in new XML.
- Keep wrapper identity, resource context, and contract payload inputs/outputs
  in `uipath:activity` or `uipath:event`. Use `uipath:mapping version="v1"`
  for `BPMN.Variables` tasks and script-task mappings.
- Every expression that references a root variable uses
  `=vars.<variableId>`, not bare names.
- Every visible flow node and sequence flow needs matching `bpmndi:BPMNShape`
  and `bpmndi:BPMNEdge` entries; the shells below omit DI for brevity.
- If you add XML comments around a shell, keep them parseable: comments must
  not contain `--`, including dashed separator lines.

Namespace baseline for greenfield files:

```xml
<bpmn:definitions
  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
  xmlns:uipath="http://uipath.org/schema/bpmn">
  <!-- process and diagram content -->
</bpmn:definitions>
```

> Public-safe synthetic IDs only. Never paste real connection IDs, folder
> keys, tenant URLs, release keys, queue IDs, user names, or process names.

## Orchestrator.StartJob (RPA)

`bpmn:serviceTask` with `Orchestrator.StartJob`.
Live debug uses the process identity fields in `uipath:context`; a lone
display-name context can validate locally but fail before child-job creation.
For `StartJob`, live debug has also required the integer Orchestrator folder ID
as lower-case `folderId`, even when `FolderKey` is present. Use public-safe
placeholders in examples and resolve real values from
`uip or processes list --all-fields --output json` and folder discovery during
tenant-specific work.

```xml
<bpmn:serviceTask id="Task_StartRpaJob" name="Start RPA Job">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Orchestrator.StartJob" version="v1" />
      <uipath:context>
        <uipath:input name="ReleaseKey" type="string" value="<PROCESS_KEY_GUID>" />
        <uipath:input name="FolderKey" type="string" value="<FOLDER_KEY_GUID>" />
        <uipath:input name="folderId" type="string" value="<FOLDER_ID_INTEGER>" />
        <uipath:input name="FolderPath" type="string" value="Shared/Synthetic" />
        <uipath:input name="Name" type="string" value="Synthetic Process" />
      </uipath:context>
      <uipath:input name="JobArguments" type="json" target="bodyField"><![CDATA[{"requestId":"=vars.Var_RequestId"}]]></uipath:input>
      <uipath:output name="Process response" type="Orchestrator.RunJob" var="Var_JobResult" />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_RpaJob</bpmn:incoming>
  <bpmn:outgoing>Flow_RpaJob_Out</bpmn:outgoing>
</bpmn:serviceTask>
```

## Orchestrator.StartAgentJob (folder-deployed agent — coded Python or low-code)

`bpmn:serviceTask` with `Orchestrator.StartAgentJob`. Use this wrapper only
for a tenant dependency that is confirmed by `uip or processes list` as
`processType: "Agent"`. Coded Python dependencies may surface as
`processType: "Function"`; do not assume they use this wrapper.

Current runtime caveat: live debug has shown `StartAgentJob` faulting before
child-job creation with `Required field 'releaseKey' missing in the input args
to RPA task`, even when solution resource refresh imports the agent and runtime
variables show `releaseKey` populated under `JobArguments` or `body`. Treat
this shell as draft-only until a tenant debug run proves it executable. Capture
`uip maestro bpmn debug-instance incidents <INSTANCE_ID> --output json`,
`uip maestro bpmn debug-instance variables <INSTANCE_ID> --output json`, and a
child-job query for the target folder when it faults.

When drafting the wrapper from a resolved Agent process, use the same identity
context shape that process wrappers use:

```xml
<bpmn:serviceTask id="Task_StartAgentJob" name="Start Agent Job">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Orchestrator.StartAgentJob" version="v1" />
      <uipath:context>
        <uipath:input name="ReleaseKey" type="string" value="<AGENT_PROCESS_KEY_GUID>" />
        <uipath:input name="FolderKey" type="string" value="<FOLDER_KEY_GUID>" />
        <uipath:input name="FolderPath" type="string" value="Shared/SyntheticAgentSolution" />
        <uipath:input name="Name" type="string" value="Synthetic Agent" />
      </uipath:context>
      <uipath:input name="JobArguments" type="json" target="bodyField"><![CDATA[{"requestId":"=vars.Var_RequestId"}]]></uipath:input>
      <uipath:output name="Process response" type="Orchestrator.RunJob" var="Var_AgentJobResult" />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_AgentJob</bpmn:incoming>
  <bpmn:outgoing>Flow_AgentJob_Out</bpmn:outgoing>
</bpmn:serviceTask>
```

For `uip solution resource refresh`, `bindings_v2.json` must use the
versioned package resource wrapper. A process dependency usually has separate
resource entries for the process name and folder path; the older unwrapped BPMN
mirror shape and an unversioned `{ "resources": [] }` object are not sufficient
for refresh:

```json
{
  "version": "2.0",
  "resources": [
    {
      "id": "Binding_AgentName",
      "kind": "process",
      "resource": "process",
      "resourceSubType": "Agent",
      "propertyAttribute": "name",
      "name": "Synthetic Agent",
      "resourceKey": "synthetic-agent",
      "metadata": {
        "BindingsVersion": "v1",
        "DisplayLabel": "Synthetic Agent",
        "SolutionsSupport": "Required",
        "SubType": "Agent",
        "PropertyAttribute": "name"
      }
    },
    {
      "id": "Binding_AgentFolderPath",
      "kind": "process",
      "resource": "process",
      "resourceSubType": "Agent",
      "propertyAttribute": "folderPath",
      "name": "Synthetic Agent",
      "resourceKey": "synthetic-agent",
      "metadata": {
        "BindingsVersion": "v1",
        "DisplayLabel": "Synthetic Agent",
        "SolutionsSupport": "Required",
        "SubType": "Agent",
        "PropertyAttribute": "folderPath"
      }
    }
  ]
}
```

If a live debug run succeeds only after emptying `resources` and hard-coding
`ReleaseKey`, `FolderKey`, `folderId`, `FolderPath`, and `Name` in BPMN
context, record that as a debug workaround. Do not report it as dependency
binding refresh coverage.

`Var_RequestId` must already exist as a `uipath:inputOutput` variable readable at the task — see [variables-bindings-expressions.md](variables-bindings-expressions.md#entry-point-inputs-used-downstream) for the start-scoped input pattern.

For the local validation fixture covering BPMN structure, bindings, and
start-scoped entry input, see
[../../fixtures/validation/agent-invocation/](../../fixtures/validation/agent-invocation/).

## A2A.AgentExecution (external A2A agent addressed by URL)

`bpmn:serviceTask` with `A2A.AgentExecution`. Use this shell only for external A2A agents addressed by URL/skillId/authToken — not for agents deployed to an Orchestrator folder. Studio Web renders this as an external A2A node and disables the Action dropdown; if you want a folder-deployed coded or low-code agent, use `Orchestrator.StartAgentJob` above.

```xml
<bpmn:serviceTask id="Task_A2AAgent" name="A2A Agent">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="A2A.AgentExecution" version="v1" />
      <uipath:context />
      <uipath:input name="body" type="json" target="body"><![CDATA[{"input":"Summarize the synthetic request."}]]></uipath:input>
      <uipath:output name="a2aResponse" type="A2A.AgentExecution" var="Var_A2AResponse" />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_A2A</bpmn:incoming>
  <bpmn:outgoing>Flow_A2A_Out</bpmn:outgoing>
</bpmn:serviceTask>
```

## Orchestrator.ExecuteApiWorkflowAsync

`bpmn:serviceTask` with `Orchestrator.ExecuteApiWorkflowAsync`.
This wrapper is live-debug verified when context uses the Orchestrator process
GUID as `ReleaseKey` and the target folder GUID as `FolderKey`. The registry
may display lower-case `releaseKey` / `folderId`; those names can validate but
fault at runtime.

```xml
<bpmn:serviceTask id="Task_ExecuteApiWorkflow" name="Execute API Workflow">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Orchestrator.ExecuteApiWorkflowAsync" version="v1" />
      <uipath:context>
        <uipath:input name="ReleaseKey" type="string" value="<API_WORKFLOW_PROCESS_KEY_GUID>" />
        <uipath:input name="FolderKey" type="string" value="<FOLDER_KEY_GUID>" />
        <uipath:input name="FolderPath" type="string" value="Shared/Synthetic" />
        <uipath:input name="Name" type="string" value="Synthetic API Workflow" />
      </uipath:context>
      <uipath:input name="JobArguments" type="json" target="bodyField"><![CDATA[{"requestId":"=vars.Var_RequestId"}]]></uipath:input>
      <uipath:output name="Process response" type="Orchestrator.RunJob" var="Var_ApiWorkflowResult" />
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
      <uipath:context>
        <uipath:input name="name" type="string" value="Synthetic Rule" />
      </uipath:context>
      <uipath:input name="JobArguments" type="json" target="bodyField"><![CDATA[{"requestId":"=vars.Var_RequestId"}]]></uipath:input>
      <uipath:output name="Execute business rule [Preview]" type="Orchestrator.BusinessRules" var="Var_RuleResult" />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_BusinessRule</bpmn:incoming>
  <bpmn:outgoing>Flow_BusinessRule_Out</bpmn:outgoing>
</bpmn:businessRuleTask>
```

## Orchestrator.CreateQueueItem

`bpmn:sendTask` with `Orchestrator.CreateQueueItem` for fire-and-continue work.

```xml
<bpmn:sendTask id="Task_CreateQueueItem" name="Create Queue Item">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Orchestrator.CreateQueueItem" version="v1" />
      <uipath:context>
        <uipath:input name="queueName" type="string" value="SyntheticQueue" />
      </uipath:context>
      <uipath:input name="ItemData" type="json" target="body"><![CDATA[{"requestId":"=vars.Var_RequestId"}]]></uipath:input>
      <uipath:output name="response" type="Orchestrator.CreateQueueItem" var="Var_WorkItem" />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_CreateQueue</bpmn:incoming>
  <bpmn:outgoing>Flow_CreateQueue_Out</bpmn:outgoing>
</bpmn:sendTask>
```

## Orchestrator.CreateAndWaitForQueueItem

`bpmn:serviceTask` with `Orchestrator.CreateAndWaitForQueueItem` when the
process waits for completion.

```xml
<bpmn:serviceTask id="Task_WaitQueueItem" name="Create And Wait For Queue Item">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Orchestrator.CreateAndWaitForQueueItem" version="v1" />
      <uipath:context>
        <uipath:input name="queueName" type="string" value="SyntheticQueue" />
      </uipath:context>
      <uipath:input name="ItemData" type="json" target="body"><![CDATA[{"requestId":"=vars.Var_RequestId"}]]></uipath:input>
      <uipath:output name="response" type="Orchestrator.CreateQueueItem" var="Var_WorkItem" />
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

## Orchestrator.StartCaseMgmtProcess (and Async variant) - preserve / draft only

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

`bpmn:intermediateCatchEvent` or matching start/boundary message event with
`Maestro.ReceiveMessageEvent`.

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

## Maestro.CasePlanScheduler - draft / preserve only

`bpmn:serviceTask` with `Maestro.CasePlanScheduler`. Mark
`preservation="draft-only"` or `preserve-only` until a dedicated
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

## Maestro.CaseManagerGuardrails - preserve only

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

## Maestro.CaseRulesEvaluator - preserve only

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
      <uipath:input name="HitlTaskArguments" type="json" target="bodyField"><![CDATA[{"requestId":"=vars.Var_RequestId"}]]></uipath:input>
      <uipath:output name="Process response" type="Actions.HITL" var="Var_ActionResult" />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_Review</bpmn:incoming>
  <bpmn:outgoing>Flow_Review_Out</bpmn:outgoing>
</bpmn:userTask>
```

## Intsvc.ActivityExecution - draft Integration Service shell

`bpmn:sendTask` with `Intsvc.ActivityExecution`. The model owns the BPMN
wrapper, ID, name, and surrounding flow; the CLI owns connector resource key,
connection binding, dynamic schemas, and operation metadata.

```xml
<bpmn:sendTask id="Task_ConnectorActivity" name="Connector Activity">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Intsvc.ActivityExecution" version="v1" />
      <uipath:context>
        <uipath:input name="connectorKey" type="string" value="placeholder-connector" />
        <uipath:input name="activity" type="string" value="placeholder-operation" />
      </uipath:context>
      <uipath:input name="Body" type="json" target="bodyField"><![CDATA[{"value":"=vars.Var_RequestId"}]]></uipath:input>
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_ConnectorActivity</bpmn:incoming>
  <bpmn:outgoing>Flow_ConnectorActivity_Out</bpmn:outgoing>
</bpmn:sendTask>
```

## Intsvc.WaitForEvent - draft Integration Service shell

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

For other `Intsvc.*` shells (`HttpExecution`, `UnifiedHttpRequest`,
`AsyncExecution`, `SyncAgentExecution`, `AsyncAgentExecution`,
`SyncWorkflowExecution`, `AsyncWorkflowExecution`, `EventTrigger`,
`TimerTrigger`), keep the same draft shape: model writes the BPMN wrapper plus
a `uipath:type` payload with placeholder strings only, then hands enrichment to
the CLI. Confirmed plain connectionless HTTP is the documented pass-2
exception. Use the HTTP request recipe instead of a connector draft shell only
after the BPMN skeleton is chosen and the workflow owns URL, method, payload,
and parsing, with no tenant connector connection or dynamic connector schema.

## Preserve markers and migration metadata

Preserve these markers when present on import. Do not delete unknown extension
XML on a normal edit; pass them through.

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

- `<bpmn:script>` bodies on `bpmn:scriptTask` require either
  `<uipath:scriptVersion>` or a `<uipath:mapping>` containing
  `<uipath:type value="BPMN.ScriptTask" version="v1" />`. Without one of those
  extensions, `uip maestro bpmn validate` rejects the body.
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
