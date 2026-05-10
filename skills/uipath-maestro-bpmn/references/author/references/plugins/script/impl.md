# Script Implementation

This document defines the implementation boundary for script tasks.

## Model-owned implementation

The model may edit:

- `bpmn:scriptTask` with `scriptFormat="JavaScript"`.
- `bpmn:script` content in CDATA.
- `uipath:scriptVersion`.
- `uipath:mapping` for `args` input and outputs.
- Declared variables and JSON schemas used by the script.
- Boundary error paths.

## Implementation rules

- Script tasks execute through Jint, not Node.js or a browser runtime.
- Keep script source deterministic and side-effect-light.
- Keep the XML mapping input named `args`, but read mapped fields as top-level
  script identifiers. For example, a mapped `caseId` field is available as
  `caseId`, not `args.caseId`.
- When mapping BPMN variables into script inputs, use runtime variable-id
  expressions such as `=vars.Var_CaseId`, not bare names such as `=caseId`.
- Return or map explicit outputs instead of mutating undeclared globals.
- Prefer `uipath:scriptVersion value="v3"` unless preserving an imported version.
- Available helpers are limited to `uipath.aggregate`, `uipath._aggregate`, `uipath._pipe`, and no-op `console` methods.
- Do not use npm packages, filesystem, network, browser globals, or long-running async behavior.
- Keep execution within the 64 MB memory and 30 second timeout envelope.
- Do not embed secrets, account data, URLs, or local paths.
- Do not use scripts as a substitute for connector enrichment or RPA work.

## Minimal Jint script task shell

Copy this shape when authoring a new BPMN script task. It is the exact
mapping shape Maestro expects: `uipath:input name="args"`
wraps the mapped fields, the script body reads top-level identifiers,
and the output maps back through `=result.<field>`.

```xml
<bpmn:scriptTask id="Task_RiskScore" name="Risk Score" scriptFormat="JavaScript">
  <bpmn:extensionElements>
    <uipath:scriptVersion value="v3" />
    <uipath:mapping version="v1">
      <uipath:type value="BPMN.Variables" version="v1" />
      <uipath:context>
        <uipath:inputSchema><![CDATA[{"type":"object","properties":{"amount":{"type":"number"},"daysOverdue":{"type":"number"}}}]]></uipath:inputSchema>
      </uipath:context>
      <uipath:input name="args" type="json" target="bodyField"><![CDATA[{"amount":"=vars.Var_Amount","daysOverdue":"=vars.Var_DaysOverdue"}]]></uipath:input>
      <uipath:output name="riskScore" type="number" var="Var_RiskScore" source="=result.response" />
    </uipath:mapping>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_Start_To_RiskScore</bpmn:incoming>
  <bpmn:outgoing>Flow_RiskScore_To_End</bpmn:outgoing>
  <bpmn:script><![CDATA[
var score = amount * 0.01 + daysOverdue * 2;
return { response: score };
]]></bpmn:script>
</bpmn:scriptTask>
```

Required pieces:

| Position | Required token | Why |
| --- | --- | --- |
| `bpmn:scriptTask` attribute | `scriptFormat="JavaScript"` | Selects the Jint executor |
| `uipath:scriptVersion` | `value="v3"` for new scripts; preserve `value="v2"` only on imports | Selects the script contract |
| `uipath:input` | `name="args"` | The canvas merges `args` JSON into top-level script identifiers |
| `uipath:input` body | `=vars.<variableId>` for each mapped field | Reads root variables by id, not by name |
| `bpmn:script` CDATA | top-level identifiers (`amount`, `daysOverdue`); not `args.amount` | Jint sees the merged JSON as top-level vars |
| `uipath:output` | `source="=result.<field>"` for `v2+`; `var` points at a declared variable id | Maps the script return back to a declared variable |

Anti-patterns the checker rejects:

- `uipath:input` with `name` other than `args`.
- Bare `=amount` style expressions instead of `=vars.Var_Amount`.
- `args.amount` style reads inside the script body.
- Missing `uipath:scriptVersion` when the canvas requires it.
- Returning a bare value instead of `{ response: ... }` for `v2+` mappings.

## Validation expectations

- Input variables exist and are readable.
- Output variables exist and are writable.
- Script CDATA is syntactically coherent.
- `uipath:scriptVersion` is present when required by the local contract.
- For `v2` and later, returned JSON may map through `=result.response`; older script versions must return a JSON object.
