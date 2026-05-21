# Variables, Bindings, and Expressions

## Variables

Use root `uipath:variables version="v1"` for entry point contracts and process globals.

For new authored BPMN, declare variables with the supported child elements:

- `uipath:input` for entry-point inputs.
- `uipath:inputOutput` for mutable process state.
- `uipath:output` for process outputs.

Do not create new generic `uipath:variable direction="..."` entries. The local
CLI currently reports generic `uipath:variable` as an unsupported extension tag;
preserve it only when editing imported XML that already contains it.

Variable elements may include:

- `id`
- `name`
- `type`
- `subType`
- `elementId`
- `canonicalId`
- `default`
- `custom`
- `internal`
- CDATA body for schema-like variable content

Entry point inputs use `elementId` to scope an input or input-output variable to the corresponding root-level start event. Root output variables become entry point output schema properties. JSON schema variables carry the schema body in CDATA; generated entry-point schema should strip `$schema`.

Maestro exports commonly model trigger-bound values as `uipath:inputOutput`
variables scoped with `elementId`. Prefer that shape for new runtime-oriented
examples unless a value is only an entry input or only a process output.

### Entry-point input lifecycle

`uipath:input` entry-point input variables are read-only at runtime. Static
validation accepts a downstream `=vars.<inputId>` reference because the variable
id is declared, but the runtime engine treats entry-point inputs as immutable
caller-supplied values and raises `Unknown identifier '<name>'` when downstream
mappings, conditions, or scripts try to read them as if they were process state.

To make an entry-point input usable downstream, declare a sibling
`uipath:inputOutput` variable and mirror the entry input into it from a
`BPMN.Variables` mapping on the start event. The downstream nodes then read the
mutable variable, never the entry-point input directly.

Minimal shell:

```xml
<bpmn:process id="Process_Demo" name="Demo" isExecutable="true">
  <bpmn:extensionElements>
    <uipath:variables version="v1">
      <uipath:input id="Var_RequestId_In" name="requestId" type="string" elementId="Start_Manual" />
      <uipath:inputOutput id="Var_RequestId" name="requestId" type="string" />
    </uipath:variables>
  </bpmn:extensionElements>
  <bpmn:startEvent id="Start_Manual" name="Start">
    <bpmn:extensionElements>
      <uipath:entryPointId value="Entry_Demo" />
      <uipath:mapping version="v1">
        <uipath:output name="requestId" type="string" var="Var_RequestId" source="=vars.Var_RequestId_In" />
      </uipath:mapping>
    </bpmn:extensionElements>
    <bpmn:outgoing>Flow_Start_To_Next</bpmn:outgoing>
  </bpmn:startEvent>
</bpmn:process>
```

After the start event runs, downstream nodes read `=vars.Var_RequestId` (the
`uipath:inputOutput`), never `=vars.Var_RequestId_In` (the `uipath:input`).

Subprocesses can carry scoped `uipath:variables` in subprocess extension elements. Do not silently move variables across scopes.

Author variables in pass 2 after the BPMN skeleton and entry points are stable. If an entry point changes during pass 1, update every variable whose `elementId` points at the old start event.

### Entry-point inputs used downstream

A `uipath:input` is read-only and scoped to the start event it declares
(`elementId`). If downstream nodes need to read or mutate the value, model it
as a start-scoped `uipath:inputOutput` instead of a read-only input.

Use the same `elementId` as the root start event so the value remains part of
the entry-point input schema while also being readable later through
`=vars.<variableId>`:

```xml
<uipath:variables version="v1">
  <uipath:inputOutput id="Var_Request" name="request" type="json"
                      elementId="Start_Manual" />
</uipath:variables>

<bpmn:startEvent id="Start_Manual" name="Start">
  <bpmn:extensionElements>
    <uipath:entryPointId value="Entry_Example" />
  </bpmn:extensionElements>
  <bpmn:outgoing>Flow_Start_To_Next</bpmn:outgoing>
</bpmn:startEvent>
```

Downstream nodes then read `=vars.Var_Request`. The same pattern applies to
trigger-bound inputs and to entry-point inputs that downstream logic needs to
mutate. See the runnable example in
[../../fixtures/validation/agent-invocation/](../../fixtures/validation/agent-invocation/).

## Bindings

Use root `uipath:bindings version="v1"` for resources that become `bindings_v2.json` entries.

Binding attributes may include:

- `id`
- `name`
- `type`
- `elementId`
- `default`
- `resource`
- `resourceSubType`
- `resourceKey`
- `propertyAttribute`

Node context inputs refer to bindings as expressions in the `=bindings.<binding id>` form. Folder key/path binding attributes can exist to support resource shape, but package generation may skip them as standalone resources.

Never paste real tenant folder keys, connection IDs, release keys, queue IDs, URLs, or private names into skill examples.

Integration Service connection bindings, trigger property bindings, connector resource metadata, and generated schemas are CLI-owned. Model-authored bindings are limited to documented non-Integration-Service resource shells or placeholder-safe draft intent.

## Mappings

Use `uipath:mapping version="v1"` for `BPMN.Variables` input/output mapping on
plain `bpmn:task` elements. Use `BPMN.ScriptTask` mappings for script tasks.

Output mappings should target declared root or scoped variables. Missing variables should be fixed in the BPMN source before package generation.

When changing a task ID, subprocess ID, or entry start event, recheck every mapping and variable `elementId` that may reference it.

## Expressions

Conditions, scripts, variable mappings, and skip conditions are expression-normalized during import. Author expressions in the Maestro-compatible form and avoid assignment operators in fields that require read-only expression evaluation. For the full lint-sensitive expression rules, read [expression-authoring.md](expression-authoring.md).

Use a leading `=` for expressions where Maestro expects expression content. Treat plain strings as literals.

When a UiPath extension expression reads a BPMN variable, reference the
variable by its XML variable id through the runtime `vars` object, for example
`=vars.Var_RequestId`. Do not use bare names such as `=requestId` in generated
runtime examples.

Gateway conditions belong on outgoing sequence flows. Service skip conditions belong on the documented `uipath:activity` attribute. Script source belongs in BPMN `script` CDATA, not in an extension text field.

Output mappings should target mutable variables: `uipath:inputOutput` or
`uipath:output`. Do not write task outputs back to read-only `uipath:input`
variables. If a caller-provided input must also become mutable state, declare a
separate `uipath:inputOutput` variable and map the entry input into it. See
[Entry-point input lifecycle](#entry-point-input-lifecycle) for the start-event
mirroring pattern.

## Script tasks

Script tasks use BPMN `script` CDATA with `scriptFormat="JavaScript"`. UiPath
script inputs are declared in a single JSON `uipath:input name="args"` body
with an `inputSchema` in context, but the Jint script body receives the mapped
fields as top-level identifiers. For example, a mapped `caseId` field is read
as `caseId` in script source, not `args.caseId`. Script outputs must map back
to declared variable ids through the `var` attribute, usually with sources such
as `=result.response` for a scalar return or `=result.response.<field>` for an
object return:

```xml
<uipath:mapping version="v1">
  <uipath:type value="BPMN.ScriptTask" version="v1" />
  <uipath:input name="args"><![CDATA[
    {"caseId":"=vars.Var_CaseId"}
  ]]></uipath:input>
  <uipath:output name="status" type="string" var="Var_Status" source="=result.response" />
</uipath:mapping>
```

If the script returns `{ status: "ok" }`, map the status with
`source="=result.response.status"`. `source="=result.status"` can complete the
script task while leaving the target variable null.

Do not use `name="Var_Status"` as a substitute for `var="Var_Status"`. The
`name` field identifies the output field; `var` identifies the target BPMN
variable.

For the exact required XML shape — including `uipath:input name="args"` with
`=vars.<variableId>` mapping bodies and a Jint-safe top-level identifier
script — see [../author/references/plugins/script/impl.md](../author/references/plugins/script/impl.md#minimal-jint-script-task-shell)
and [wrapper-shells.md](wrapper-shells.md).
