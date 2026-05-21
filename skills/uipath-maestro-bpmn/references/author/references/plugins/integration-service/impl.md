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

## Shared Integration Service discovery

BPMN and Flow use different source shapes, but the executable Integration
Service metadata is the same product contract. Flow stores connector
configuration in `.flow` node `inputs.detail`; BPMN stores enriched
`uipath:activity` / `uipath:event` XML plus generated JSON package resources.
Do not copy Flow node JSON into BPMN. Do use the same CLI and IS discovery
rules to decide whether executable BPMN enrichment is complete.

### Registry and connector discovery

1. Pull or refresh the BPMN registry before connector decisions:

   ```bash
   uip maestro bpmn registry pull --output json
   uip maestro bpmn registry search "<service-or-operation>" --output json
   ```

2. If search returns connector triggers but no activities for a known connector,
   or returns no activities for a connector that exists in Integration Service,
   force a refresh before falling back:

   ```bash
   uip maestro bpmn registry pull --force --output json
   uip maestro bpmn registry search "<service-or-operation>" --output json
   ```

   Treat the first result as a stale-cache symptom, not proof that the
   connector has no activity branch.

3. Use Integration Service connector discovery for disambiguation when multiple
   connectors can satisfy the same intent:

   ```bash
   uip is connectors list --output json
   uip is activities list "<connector-key>" --output json
   uip is activities list "<connector-key>" --triggers --output json
   ```

   Apply the platform connector-disambiguation rules, including JDBC gateway
   handling for database SQL intents. Use the activity lists to distinguish
   connector actions from connector events; do not infer trigger support from
   action names or action support from trigger names.

### Connections and resource metadata

1. List and verify a connection for the selected connector:

   ```bash
   uip is connections list "<connector-key>" --folder-key "<folder-key>" --output json
   uip is connections ping "<connection-id>" --output json
   ```

   If no expected connection appears, retry once with `--refresh` before
   declaring it missing.

2. Fetch BPMN extension metadata and, when supported, live IS enrichment:

   ```bash
   uip maestro bpmn registry get Intsvc.ActivityExecution \
     --connection-id "<connection-id>" \
     --object-name "<objectName>" \
     --output json
   ```

   Use the result as enrichment evidence or as input to a BPMN-specific
   generator. Do not manually translate it into executable XML when the
   generator/enricher is unavailable.

3. For generic activities, discover the object through the live connection
   before resolving operation metadata:

   ```bash
   uip is resources list "<connector-key>" \
     --connection-id "<connection-id>" \
     --output json
   ```

   Use the resource `Name` as the object name. It is case-sensitive; do not
   substitute display names.

4. For activity fields, describe the selected object and operation:

   ```bash
   uip is resources describe "<connector-key>" "<objectName>" \
     --connection-id "<connection-id>" \
     --operation "<Operation>" \
     --output json
   ```

   Read the full metadata file when the response provides one. Required
   request fields, query/path parameters, references, filters, dynamic schemas,
   and output fields come from this metadata, not from examples. Use
   `availableOperations[]` / `operation` values for method and endpoint
   evidence; generic activities cannot derive those from a fixed manifest.

5. For parent-field-driven custom schemas, rerun `resources describe` with the
   parent values before validating required fields:

   ```bash
   uip is resources describe "<connector-key>" "<objectName>" \
     --connection-id "<connection-id>" \
     --operation "<Operation>" \
     -f "<parentField>=<value>" \
     --output json
   ```

   This exercises api-type ObjectActions such as Jira project/issue-type,
   SQL-query schema, or Data Service entity metadata. If the enriched describe
   cannot be produced, keep the BPMN element as draft intent rather than
   fabricating dynamic fields.

6. Resolve reference fields with the connection bound to this project:

   ```bash
   uip is resources execute list "<connector-key>" "<reference-object>" \
     --connection-id "<connection-id>" \
     --output json
   ```

   Reference IDs are connection-scoped. Never carry IDs from another solution,
   another connection, or a prior session. Paginate through
   `Data.Pagination.HasMore` / `NextPageToken` until the target is found or the
   server says there are no more pages. If the installed CLI documents a
   renamed `run` verb instead of `execute`, retry this same reference-resolution
   call with that verb. Do not retry with the alternate verb for authentication,
   permission, network, or connector errors.

### Activity metadata rules

These rules apply to BPMN enrichment inputs and validation evidence. They are
not permission to hand-author the final executable BPMN payload.

- Copy the IS `method` value verbatim from metadata, including synthesized
  labels such as `GETBYID`; do not translate it by hand.
- Treat concrete and generic activities differently. Concrete activities carry
  object/operation metadata in the registry response; generic activities need a
  selected `objectName` plus `resources describe` before method, endpoint, and
  field details are known.
- Path-parameterized retrieve operations require both the endpoint path with
  placeholders and matching path parameters.
- For FilterBuilder parameters, use a structured filter tree through the CLI
  enrichment path. Confirm support through `parameters[].design.component ===
  "FilterBuilder"`, choose only searchable fields and supported operators from
  metadata, and do not pass a raw CEQL string as the only design-time
  representation. Studio Web needs both runtime and design-time filter data.
- `requestFields[].name` values ending in `[*]` mark array fields. Strip the
  suffix from the runtime key and pass an array value. Names containing `[*].`
  with further path segments are not authorable unless current CLI metadata and
  enrichment explicitly support them.
- Validate every required `requestFields[]` and `parameters[]` value before
  enrichment. Missing required values are blockers unless metadata declares a
  usable default.
- `customFieldsRequestDetails` uses camelCase keys and
  `parameterValues` as an array of `[key, value]` tuples. Object-map form and
  PascalCase keys are invalid. Parent-field-driven schema values must appear in
  both the runtime parameter bucket and the design-time replay cache when the
  CLI-enriched payload requires both.
- Detect parent-field-driven schemas by checking both top-level
  `objectActions[]` (`ActionType: "Api"`) and
  `connectorMethodInfo.design.actions[]` (`actionType: "api"`). Encode
  parameter-value keys with the same IS sanitizer rules (`.` / `::` / `:::` to
  `_sub_`, `[*]` to `_array`) only for the design-time replay cache; keep raw
  field names in runtime request/query/path parameter buckets.
- Multipart and pagination input metadata are derived from IS metadata by the
  enrichment path. Do not hand-author BPMN executable XML for these shapes from
  Flow examples.

### Trigger metadata rules

Connector triggers and wait-event shapes require trigger-specific IS metadata:

1. List trigger activities and note the selected activity's operation:

   ```bash
   uip is activities list "<connector-key>" --triggers --output json
   ```

2. Query trigger objects before final connection selection for CRUD-style
   operations such as `CREATED`, `UPDATED`, or `DELETED`:

   ```bash
   uip is triggers objects "<connector-key>" "<OPERATION>" \
     --connection-id "<connection-id>" \
     --output json
   ```

   For non-CRUD/custom trigger operations, use the trigger activity's
   `ObjectName` when current metadata says no objects step is required.

3. Respect the selected event object's `byoaConnection` flag. If it is `true`,
   use a BYOA connection; a normal connection is not interchangeable.
4. Fetch trigger metadata with `--connection-id` and use `eventParameters`,
   `filterFields`, `outputResponseDefinition`, and `eventMode` from the live
   response:

   ```bash
   uip is triggers describe "<connector-key>" "<OPERATION>" "<objectName>" \
     --connection-id "<connection-id>" \
     --output json
   ```

5. Resolve trigger reference fields against the final selected connection, with
   the same pagination and connection-scoping rules as activity references.
6. Author trigger filters as structured filter trees through enrichment. Do not
   pass a raw `filterExpression`; the CLI/runtime needs both the design-time
   filter tree and the compiled runtime expression.
7. If the event object has `isWebhookUrlVisible: true`, retrieve and present the
   webhook URL during Operate/debug handoff. If it is `false`, do not invent
   webhook-registration instructions. If metadata includes `design.textBlocks`,
   surface that text verbatim with the retrieved webhook URL rather than
   inventing connector-specific setup guidance.

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
operator and the CLI know which fields are still placeholders. Prefer the
handoff summary or an existing project-owned documentation location. Do not
create a new `README.md`, `notes.md`, or other project file solely for draft
blockers unless the user asks for that artifact.

The handoff should make each unresolved CLI-owned blocker explicit:

1. **`connector metadata`** - the CLI fills in operation/event metadata, version, and connector key.
2. **`connection binding`** - the CLI generates the root `uipath:bindings` connection entry and the `=bindings.<id>` references on the node.
3. **`dynamic schemas`** - the CLI generates the `uipath:inputSchema` payloads and generated output schemas.
4. **`bindings_v2.json`** - the CLI generates binding resources, deduplicated by resource key.
5. **`entry-points.json`** - the CLI generates trigger entry-point wiring and root variable schema.
6. **`operate.json`** - the CLI generates project ID, content type, target framework, and runtime options.
7. **`package-descriptor.json`** - the CLI generates file mappings for the BPMN file and generated JSON.
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
