# Integration Service Implementation

This document defines the implementation boundary for Integration Service BPMN elements.

This boundary covers connector-backed and dynamically schematized Integration
Service work. For confirmed pass-2 plain connectionless HTTP where the workflow
owns the URL, method, payload, and parsing, use
[task-recipes/http-request.md](../../task-recipes/http-request.md).

## Model-owned implementation

The model may edit:

- Standard BPMN wrapper element: service task, start event, intermediate event, boundary event, or receive/wait pattern.
- Stable element ID and public-safe display name.
- Sequence flows and diagram geometry.
- Variables and mappings that consume the eventual output.
- Error handling and retry intent, when specified by the user.

The model must keep any connector-backed Integration Service service payload as
draft intent unless CLI enrichment has supplied the concrete metadata. A draft
shell may identify the wrapper family with `uipath:type value="Intsvc.<Variant>"`
and placeholder strings, but it must not include real connector metadata,
connection bindings, generated schemas, or generated resource references.

Sanitized fixtures may be used to understand where enriched XML and generated package files appear, but their connector keys, resource keys, operation names, schemas, and bindings must not be copied into a live project.

## CLI-owned implementation

The CLI or registry-backed tool must generate or enrich from current tenant/registry data:

- `uipath:activity` or `uipath:event` contents for connector-backed or dynamically schematized `Intsvc.*` service types.
- `uipath:type` service type and version from supported metadata.
- `uipath:context` fields for connector key, operation, object, connection binding, event name, folder fields, and trigger properties.
- `uipath:input` bodies for request parameters and filter expressions.
- `uipath:output` mappings and dynamic output schemas.
- `uipath:inputSchema` payloads.
- Root `uipath:bindings` entries that point to generated binding resources.
- `bindings_v2.json` resource entries.

## Safe placeholder shape

When enrichment is unavailable, keep the BPMN element structurally visible and
mark it as draft in planning notes rather than inventing executable connector
metadata. The project should remain in Author state until enrichment completes.

The draft shell uses the same canonical wrapper shape as other BPMN wrappers:
`bpmn:extensionElements`, `uipath:activity` or `uipath:event`, and a nested
`uipath:type`. Any placeholder payload mapping belongs in sibling
`uipath:mapping`, but executable connector metadata remains CLI-owned. See
[shared/wrapper-shells.md](../../../../shared/wrapper-shells.md) for copyable
generic examples.

Minimal draft `Intsvc.ActivityExecution` shell on a `bpmn:sendTask`:

```xml
<bpmn:sendTask id="Task_ConnectorActivity" name="Connector Activity">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Intsvc.ActivityExecution" version="v1" />
      <uipath:context>
        <uipath:input name="connectorKey" type="string" value="placeholder-connector" />
        <uipath:input name="activity" type="string" value="placeholder-operation" />
      </uipath:context>
    </uipath:activity>
    <uipath:mapping version="v1">
      <uipath:input name="Body" type="json" target="bodyField"><![CDATA[{"value":"=vars.Var_RequestId"}]]></uipath:input>
    </uipath:mapping>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_To_ConnectorActivity</bpmn:incoming>
  <bpmn:outgoing>Flow_ConnectorActivity_Out</bpmn:outgoing>
</bpmn:sendTask>
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

These shells are not executable. The CLI still owns the real connector key,
operation/event name, connection binding, trigger properties, input and output
schemas, generated outputs, and `bindings_v2.json` resources.

Use synthetic names only, for example `Task_CreateTicket` or
`Start_WhenRecordCreated`. Do not use real connection IDs, tenant URLs, folder
keys, account-specific resource IDs, or copied metadata from another project.
Do not hand-author `connection`, `trigger`, or `object` `type="resource"`
inputs that point at `=bindings.<id>`; those expressions require generated
`bindings_v2.json` resources and are CLI-owned.

## Draft handoff notes

Until CLI enrichment runs, record an explicit handoff in the project so the
operator and the CLI know which fields are still placeholders. Add a
`README.md` or `notes.md` inside the project that lists every CLI-owned blocker
before upload, publish, debug, or run.

The README should make each unresolved CLI-owned blocker explicit:

1. **`connector metadata`** - the CLI fills in operation/event metadata, version, and connector key.
2. **`connection binding`** - the CLI generates the root `uipath:bindings` connection entry and the `=bindings.<id>` references on the node.
3. **`dynamic schemas`** - the CLI generates the `uipath:inputSchema` payloads and generated output schemas.
4. **`bindings_v2.json`** - the CLI generates binding resources, deduplicated by resource key.
5. **`entry-points.json`** - the CLI generates trigger entry-point wiring and root variable schema.
6. **`operate.json`** - the CLI generates project ID, main file, target framework, and runtime options.
7. **`package-descriptor.json`** - the CLI generates manifest entries for the BPMN file and generated JSON.
8. **`package metadata`** - the CLI produces final package identifiers, paths, and generated outputs.

## Validation expectations

Before Operate, confirm that:

- Every executable connector-backed Integration Service element has CLI-enriched context, inputs, outputs, and schemas.
- Root binding references resolve.
- Generated package resources exist and are deduped.
- Required filters and parameters are present.
- Trigger property bindings are generated for trigger elements.
- No private IDs are present in files intended for commit.
- Enrichment evidence comes from the current target tenant/registry, not from copied exports or synthetic fixtures.

Use [shared/local-metadata-regeneration-guide.md](../../../../shared/local-metadata-regeneration-guide.md) to verify the generated `bindings_v2.json`, `entry-points.json`, and `Intsvc.*` payloads agree before upload, debug, publish, or deploy.
