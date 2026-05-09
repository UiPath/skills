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
- Script output mappings must target variables through the `var` attribute.
  Do not put the target variable id in `name`. Use `name` for the output
  field/display name and `var` for the declared BPMN variable id:

  ```xml
  <uipath:mapping version="v1">
    <uipath:input name="args"><![CDATA[
      {"amount":"=vars.Var_Amount","daysOverdue":"=vars.Var_DaysOverdue"}
    ]]></uipath:input>
    <uipath:output name="riskScore" type="number" var="Var_RiskScore" source="=result.response" />
  </uipath:mapping>
  ```
- Prefer `uipath:scriptVersion value="v3"` unless preserving an imported version.
- Available helpers are limited to `uipath.aggregate`, `uipath._aggregate`, `uipath._pipe`, and no-op `console` methods.
- Do not use npm packages, filesystem, network, browser globals, or long-running async behavior.
- Keep execution within the 64 MB memory and 30 second timeout envelope.
- Do not embed secrets, account data, URLs, or local paths.
- Do not use scripts as a substitute for connector enrichment or RPA work.

## Validation expectations

- Input variables exist and are readable.
- Output variables exist and are writable.
- Script CDATA is syntactically coherent.
- `uipath:scriptVersion` is present when required by the local contract.
- For `v2` and later, returned JSON may map through `=result.response`; older script versions must return a JSON object.
