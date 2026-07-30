# Integration Service activity authoring

Use this guide for one live, runnable `Intsvc.ActivityExecution` after
[live resource resolution](live-resource-resolution-guide.md) has selected one
exact enabled connection. It applies to every Integration Service connector and
login context; do not infer a provider, environment, organization, tenant, or
profile.

This is an authoring workflow. The catalog, resource, and schema commands are
read-only. Never invoke `uip is resources run`, mutate a connection, or call the
external operation merely to discover its contract.

## 1. Require the current registry-owned V1 template

Retrieve the activity contract in the selected context:

```bash
uip maestro bpmn registry get Intsvc.ActivityExecution --output json
```

For a named login profile, repeat the same `--profile <name>` on this and every
other tenant-dependent command in this guide.

The current V1 `XmlTemplate` contains:

- `connectorKey`, `connection`, `folderKey`, `operation`, `objectName`,
  `method`, `path`, and `activityConfigurationVersion` context inputs, each
  with `type="string"`, plus JSON `metadata`;
- distinct `{connectionBindingId}` and `{folderBindingId}` placeholders, with
  no `resourceKey` context input;
- `InputFields: []` and the `separateInputs` pattern: request fields come from
  the selected operation as direct children of `uipath:activity`, after the
  closed `uipath:context`, rather than as context fields or fixed grouped
  path/query containers; and
- one registry-owned output with `name="response"`, `type="jsonSchema"`, and
  `source="=response"`.

If the retrieved template instead has a legacy `activity` context, untyped
string context inputs, a context-level `resourceKey`, one binding placeholder,
a literal folder value, fixed `pathParameters` / `queryParameters` inputs, or a
`result` / `custom` / `.` output, the CLI predates this runnable V1 contract.
Do not rewrite the registry payload by hand. Update the CLI or keep the node a
non-runnable draft.

## 2. Select an exact catalog activity

List the catalog only after the connector and connection are known:

```bash
uip is activities list <connector-key> --output json
```

Match the requested capability to one exact row. Preserve its values verbatim:

| Row shape | Meaning | Object resolution |
| --- | --- | --- |
| `IsCurated: Yes`, concrete `ObjectName`, concrete `MethodName`, `Operation: N/A` | Connector-specific curated activity | Use the row's `ObjectName`; do not run `resources list`. |
| `IsCurated: No`, `ObjectName: N/A`, concrete CRUD `Operation` | Generic CRUD activity | Discover a concrete object with `resources list`. |

The BPMN context `operation` is always the selected activity row's exact
`Name`, including for generic CRUD. `Operation` on a generic row is the schema
operation used for resource discovery; it does not replace the catalog `Name`.
If multiple rows remain plausible, resolve the ambiguity instead of selecting
the first.

For a generic row, list only resources supporting its schema operation:

```bash
uip is resources list <connector-key> \
  --connection-id <connection-id> \
  --operation <schema-operation> \
  --output json
```

Select one exact `Name` from the result and use it as the BPMN
`objectName`. Never serialize `N/A`, a display name, or an object from a
different connector.

## 3. Resolve and verify the operation schema

Inspect available operations independently for every selected object, curated
and generic, then describe the selected one. Do this for the generic object
even when its catalog row already names a CRUD operation:

```bash
uip is resources describe <connector-key> <object-name> \
  --connection-id <connection-id> \
  --output json

uip is resources describe <connector-key> <object-name> \
  --connection-id <connection-id> \
  --operation <schema-operation> \
  --output json
```

For a curated row, select the available operation whose `method` equals the
row's exact `MethodName`, then pass that operation's exact CRUD `name` (for
example, `Create`) as `<schema-operation>`. Verify that the described
operation's `method` still equals the catalog `MethodName`. If more than one
available operation has that method and the contract does not otherwise
disambiguate them, stop. For a generic row, require an available operation whose
exact `name` equals the catalog row's exact `Operation`; use that name as
`<schema-operation>`, and stop if it is absent.

Some schemas depend on already chosen parent request values. When the described
schema says more fields depend on those values, repeat `resources describe`
with the same connection and operation plus one `-f <exact-name=value>` per
known parent field. Do not guess parent values or an ObjectAction. If the CLI
cannot produce the fields required by the business payload, keep the node
blocked.

Accept the schema only when all of these identities agree:

- connection discovery and the two schema calls use the selected connection;
- the result `elementKey` equals the selected connector key;
- the result `name` equals the selected object name;
- the selected operation's `method` and `path` are present; and
- an enriched registry lookup for the same connection and object reports the
  same connector and object:

  ```bash
  uip maestro bpmn registry get Intsvc.ActivityExecution \
    --connection-id <connection-id> \
    --object-name <object-name> \
    --output json
  ```

An omitted `ISEnrichment`, mismatched `ElementKey`, or mismatched `Name` blocks
a runnable claim. Raw enrichment is evidence, not runtime payload.

## 4. Fill only the retrieved template

Preserve the retrieved template's `uipath:activity`, type, context, and output
structure. If its BPMN host tag is PascalCase, normalize only that host tag from
`bpmn:SendTask` to `bpmn:sendTask`. Fill the V1 context as follows and preserve
`type="string"` on every string row:

| Context input | Exact source |
| --- | --- |
| `activityConfigurationVersion` | Registry literal `v1` |
| `connectorKey` | Selected catalog/schema connector key |
| `connection` | `=bindings.<connection-binding-id>` |
| `folderKey` | `=bindings.<folder-binding-id>` when the exact selected connection row supplies a nonempty folder key; otherwise omit it |
| `operation` | Catalog activity row `Name` |
| `objectName` | Curated row `ObjectName`, or selected generic resource `Name` |
| `method` / `path` | Selected `resources describe` operation |
| `metadata` | `{}` unless the retrieved runtime template explicitly requires another value; never paste `ISEnrichment` |

Declare a root connection `<uipath:binding>` with `resource="Connection"`,
`type="string"`, `default="<connection-id>"`, and
`propertyAttribute="ConnectionId"`. When the exact selected connection row
supplies a nonempty folder key, preserve it by adding a distinct folder binding
that also uses `resource="Connection"` and `type="string"`, with
`default="<folder-key>"` and `propertyAttribute="folderKey"`; omit both the
folder binding and the `folderKey` context input only when discovery supplies no
folder key. Point each present context input at its binding id. When both
bindings exist, give them nonempty distinct names and the same `resourceKey`.
Never copy `resourceKey` into `uipath:context`.

When folder context is present, the V1 validator requires a nonempty matching
`resourceKey` on the two root bindings; it does not choose that source-model
identity. Preserve an explicit root-binding resource key supplied by an
existing solution. For standalone source with no supplied key, use the selected
connection id as the deterministic fallback rather than inventing another
identifier. Reuse a binding pair only for activities with the same connection
and the same resource key; the same connection id can legitimately appear
under different solution resource keys.

These root bindings are source model state. `bindings_v2.json`,
`entry-points.json`, `operate.json`, and `package-descriptor.json` are generated
package state: never hand-create or edit them. After source validation, run
the BPMN `refresh` command to derive the V1 Connection resources and the rest
of the package metadata from the BPMN.

## 5. Serialize request inputs from the described schema

Treat `requestFields` and `parameters` from the accepted operation description
as the allowlist. Add each selected field as its own `uipath:input` directly
under `uipath:activity`, as a sibling immediately after the closed
`uipath:context` and before `uipath:output`. Never put operation inputs inside
`uipath:context`; that element contains only the registry-declared context rows
from section 4. The registry template intentionally contains no fixed
request-input rows.

```xml
<uipath:context>...</uipath:context>
<uipath:input name="tenantId" type="string" target="path" value="tenant-west" />
<uipath:output name="response" type="jsonSchema" source="=response" var="Response" />
```

- Include every required request field and every optional request field the
  business request actually supplies. Exclude response-only fields and unused
  optional fields.
- Use each exact `name`, not a dictionary key, display name, or provider
  synonym. Presentation-only metadata such as `RequestCurated` never turns a
  response-only field into a request field.
- For each operation parameter, copy its `dataType`, exact name, and target
  (`path` or `query`) onto one input. Keep the context `path` exactly as
  described, including its `{parameter}` tokens.
- For each selected request field, copy its described type and target. Body
  fields use `target="body"`; preserve dotted names such as `record.owner.id`
  as the operation describes them instead of regrouping them into one JSON
  object.
- Keep file fields separate with their exact names, described types, and
  `target="file"`.
- Do not emit fixed `pathParameters` or `queryParameters` inputs, empty group
  placeholders, or an unused `body` input. Use JSON element content only when
  the selected field itself has `type="json"`.

If a required parameter uses an unverified target, a dotted array path cannot
be represented without changing its meaning, or a field type cannot be mapped
without guessing, stop instead of claiming the node is runnable.

## 6. Preserve the response contract

Keep the template's one `uipath:output` with `name="response"`,
`type="jsonSchema"`, and `source="=response"`, and point it at a response
variable. Declare that variable as `jsonSchema` and choose its scope for its
consumers: a root `uipath:output` (without `elementId`) is visible to
runtime/global inspection, while `elementId="<task-id>"` limits an
`inputOutput` variable to that element. Preserve an existing variable's scope
when editing. Construct its properties from the accepted `responseFields`,
preserving exact names and types. Reconstruct dotted response names into nested
object properties. Do not add request-only fields or invent response
properties.

Finally, wire the task structurally, add its diagram shape and edge waypoints,
and run local BPMN validation. Passing validation is structural preflight; for
dynamic Integration Service payloads it does not prove that every discovered
operation field has the right target or type. Check those against the selected
operation schema. Only an authorized live run proves the external operation's
business behavior.
