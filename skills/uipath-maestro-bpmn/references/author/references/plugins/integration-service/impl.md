# Integration Service Implementation

This document defines the implementation boundary for Integration Service BPMN elements.

## Model-owned implementation

The model may edit:

- Standard BPMN wrapper element: service task, start event, intermediate event, boundary event, or receive/wait pattern.
- Stable element ID and public-safe display name.
- Sequence flows and diagram geometry.
- Variables and mappings that consume the eventual output.
- Error handling and retry intent, when specified by the user.

The model must keep any Integration Service service payload as draft intent unless CLI enrichment has supplied the concrete metadata.

## CLI-owned implementation

The CLI or registry-backed tool must generate or enrich:

- `uipath:activity` or `uipath:event` contents for `Intsvc.*` service types.
- `uipath:type` service type and version from supported metadata.
- `uipath:context` fields for connector key, operation, object, connection binding, event name, folder fields, and trigger properties.
- `uipath:input` bodies for request parameters and filter expressions.
- `uipath:output` mappings and dynamic output schemas.
- `uipath:inputSchema` payloads.
- Root `uipath:bindings` entries that point to generated binding resources.
- `bindings_v2.json` resource entries.

## Safe placeholder shape

When enrichment is unavailable, keep the BPMN element structurally visible and
mark it as draft in planning notes rather than inventing executable XML. The
project should remain in Author state until enrichment completes.

The model still writes the BPMN wrapper and a draft `uipath:activity` (or
`uipath:event`) shell with `uipath:type` and placeholder strings. The CLI
fills in connector resource keys, connection bindings, dynamic schemas,
trigger property bindings, and generated outputs.

Minimal draft `Intsvc.ActivityExecution` shell on a `bpmn:serviceTask`:

```xml
<bpmn:serviceTask id="Task_SendDigest" name="Send Slack Digest">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Intsvc.ActivityExecution" version="v1" />
      <uipath:context>
        <uipath:input name="connectorKey" type="string" value="placeholder-connector" />
        <uipath:input name="activity" type="string" value="placeholder-operation" />
      </uipath:context>
      <uipath:input name="DigestBody" type="json" target="bodyField"><![CDATA[{"channel":"=vars.Var_Channel","message":"=vars.Var_Digest"}]]></uipath:input>
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_SendDigest</bpmn:incoming>
  <bpmn:outgoing>Flow_SendDigest_Out</bpmn:outgoing>
</bpmn:serviceTask>
```

Minimal draft `Intsvc.WaitForEvent` shell on a `bpmn:receiveTask`:

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

The same draft shape applies to other `Intsvc.*` types (`HttpExecution`,
`UnifiedHttpRequest`, `AsyncExecution`, `SyncAgentExecution`,
`AsyncAgentExecution`, `SyncWorkflowExecution`, `AsyncWorkflowExecution`,
`EventTrigger`, `TimerTrigger`); only the wrapper class and `uipath:type`
value change. See [../../../../shared/wrapper-shells.md](../../../../shared/wrapper-shells.md).

Use synthetic names only, for example `Task_CreateTicket` or
`Start_WhenRecordCreated`. Do not use real connection IDs, tenant URLs,
folder keys, account-specific resource IDs, or copied metadata from another
project. Do not hand-author `connection`, `trigger`, or `object` `type="resource"` inputs that point at `=bindings.<id>` — those expressions
require generated `bindings_v2.json` resources and are CLI-owned.

## Draft handoff notes

Until CLI enrichment runs, record an explicit handoff in the project so the
operator and the CLI know which fields are still placeholders. Add a
`README.md` (or `notes.md`) inside the project that lists every CLI-owned
blocker before upload, publish, debug, or run.

The README should make each unresolved CLI-owned blocker explicit:

1. **`connector metadata`** - the CLI fills in `uipath:type` operation/event metadata, version, and connector key.
2. **`connection binding`** - the CLI generates the root `uipath:bindings` connection entry and the `=bindings.<id>` references on the node.
3. **`dynamic schemas`** - the CLI generates the `uipath:inputSchema` payloads and the generated output schemas.
4. **`bindings_v2.json`** - the CLI generates the binding resources, deduplicated by resource key.
5. **`entry-points.json`** - the CLI generates trigger entry-point wiring and the root variable schema.
6. **`operate.json`** - the CLI generates project ID, main file, target framework, and runtime options.
7. **`package-descriptor.json`** - the CLI generates manifest entries for the BPMN file and generated JSON.
8. **`package metadata`** - the CLI produces the final package identifiers, paths, and generated outputs.

Minimal `README.md` template:

```markdown
# <ProjectName> - draft Integration Service boundary

This project keeps the Integration Service step at the model-owned draft
boundary. The BPMN file owns the wrapper, sequence flows, variables, and
diagram geometry. The Integration Service activity shell carries
`uipath:type value="Intsvc.<Variant>"` with placeholder strings only;
connector enrichment is CLI-owned.

## CLI-owned blockers (must be enriched before upload, debug, publish, or run)

- **`connector metadata`** - real connector key, operation/event name, version, and resource keys.
- **`connection binding`** - real connection: a root `uipath:bindings` connection entry plus a `=bindings.<id>` `type="resource"` input on the node.
- **`dynamic schemas`** - `uipath:inputSchema` payloads and any generated output schemas come from connector metadata.
- **`bindings_v2.json`** - generated binding resources, deduplicated by resource key.
- **`entry-points.json`** - entry-point wiring derived from root variables.
- **`operate.json`** - project ID, main file, target framework, and runtime options.
- **`package-descriptor.json`** - manifest entries for the BPMN file and generated JSON.
- **`package metadata`** - final package identifiers, paths, and generated outputs.

## Public-safety constraints

No real connection IDs, folder keys, tenant URLs, or connector resource
keys appear in this project.
```

## Validation expectations

Before Operate, confirm that:

- Every executable Integration Service element has CLI-enriched context, inputs, outputs, and schemas.
- Root binding references resolve.
- Generated package resources exist and are deduped.
- Required filters and parameters are present.
- Trigger property bindings are generated for trigger elements.
- No private IDs are present in files intended for commit.
