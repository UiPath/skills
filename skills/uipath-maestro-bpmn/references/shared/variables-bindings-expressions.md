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

Entry point inputs use `elementId` to scope an input variable to the corresponding root-level start event. Root output variables become entry point output schema properties. JSON schema variables carry the schema body in CDATA; generated entry-point schema should strip `$schema`.

Maestro exports commonly model trigger-bound values as `uipath:inputOutput`
variables scoped with `elementId`. Prefer that shape for new runtime-oriented
examples unless a value is only an entry input or only a process output.

Subprocesses can carry scoped `uipath:variables` in subprocess extension elements. Do not silently move variables across scopes.

Author variables in pass 2 after the BPMN skeleton and entry points are stable. If an entry point changes during pass 1, update every variable whose `elementId` points at the old start event.

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

Use `uipath:mapping version="v1"` for `BPMN.Variables` input/output mapping on tasks, start/end events, script tasks, and subprocesses.

Output mappings should target declared root or scoped variables. Missing variables should be fixed in the BPMN source before package generation.

When changing a task ID, subprocess ID, or entry start event, recheck every mapping and variable `elementId` that may reference it.

## Expressions

Conditions, scripts, variable mappings, and skip conditions are expression-normalized during import. Author expressions in the Maestro-compatible form and avoid assignment operators in fields that require read-only expression evaluation.

Use a leading `=` for expressions where Maestro expects expression content. Treat plain strings as literals.

When a UiPath extension expression reads a BPMN variable, reference the
variable by its XML variable id through the runtime `vars` object, for example
`=vars.Var_RequestId`. Do not use bare names such as `=requestId` in generated
runtime examples.

Gateway conditions belong on outgoing sequence flows. Service skip conditions belong on the documented `uipath:activity` attribute. Script source belongs in BPMN `script` CDATA, not in an extension text field.

## Script tasks

Script tasks use BPMN `script` CDATA with `scriptFormat="JavaScript"`. UiPath
script inputs are declared in a single JSON `uipath:input name="args"` body
with an `inputSchema` in context, but the Jint script body receives the mapped
fields as top-level identifiers. For example, a mapped `caseId` field is read
as `caseId` in script source, not `args.caseId`. Script outputs must map back
to declared variable ids through the `var` attribute, usually with sources such
as `=result.response`:

```xml
<uipath:mapping version="v1">
  <uipath:input name="args"><![CDATA[
    {"caseId":"=vars.Var_CaseId"}
  ]]></uipath:input>
  <uipath:output name="status" type="string" var="Var_Status" source="=result.response" />
</uipath:mapping>
```

Do not use `name="Var_Status"` as a substitute for `var="Var_Status"`. The
`name` field identifies the output field; `var` identifies the target BPMN
variable.

For the exact required XML shape — including `uipath:input name="args"` with
`=vars.<variableId>` mapping bodies and a Jint-safe top-level identifier
script — see [../author/references/plugins/script/impl.md](../author/references/plugins/script/impl.md#minimal-jint-script-task-shell)
and [wrapper-shells.md](wrapper-shells.md).
