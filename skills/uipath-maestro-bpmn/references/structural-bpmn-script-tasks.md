# Structural BPMN: script tasks

## Script tasks — Jint authoring contract

`bpmn:scriptTask scriptFormat="JavaScript"` (exact casing — the serializer is
case-sensitive) runs under **Jint**, not Node.js or
a browser. The mapping payload comes from the `BPMN.ScriptTask` registry
template, but the runtime contract is fixed — including one correction to that
template, in the first rule below (see the registry lookup and compatibility
fallback contract further down for the discovery workflow):

- Only these helpers exist: `uipath.aggregate`, `uipath._aggregate`,
  `uipath._pipe`, and a no-op `console`. No npm packages, filesystem, network,
  browser globals, or long-running async behavior. Execution envelope is ~64 MB
  / 30 s.
- Set `uipath:scriptVersion value="v3"` for new scripts; preserve an imported
  `value="v2"`. For v2+ the script returns JSON under `response`.
- The `args` input is fixed, not per-field: `<uipath:input name="args"
  type="json" target="bodyField"><![CDATA[{"vars":"=vars","metadata":"=metadata"}]]></uipath:input>`,
  paired with a fixed `uipath:context/uipath:inputSchema` declaring `vars` and
  `metadata` as objects. It is not a per-field body keyed by variable name,
  and sibling `uipath:input` elements are not supported.
  Read process data in the script as `vars.<id>` (dot access into the
  injected `vars` object), never as a bare top-level identifier. This rule
  applies to nodes you author and to mappings an edit explicitly targets;
  never retrofit these attributes onto an untouched node's mapping — a
  pre-existing `<uipath:input name="args">` outside the edit's target stays
  byte-identical.
- **The mapping's type child is `<uipath:type value="BPMN.Variables"
  version="v1" />`, not `BPMN.ScriptTask`.** The registry's `BPMN.ScriptTask`
  `xmlTemplate` emits the latter, and this is the first of two corrections that
  template needs: any `uipath:type` other than `BPMN.Variables` overwrites the parser's
  `Scp.Script` extension type, so the runtime never dispatches the script. The
  element still completes, the output mapping resolves against an empty result,
  and the target variable reads back `null`.
- Map the return through `source="=result.response"` for a scalar, or
  `source="=result.response.<field>"` for a field of a returned object; `var`
  points at a declared variable id (do not put the target id in `name`).
- Type `scriptResponse` from the script's return: `jsonSchema` for an object
  or array, `double` for a number, otherwise the primitive's own name. The
  canvas retypes it on every script edit (`ScriptTaskProperties.tsx:347`);
  `jsonSchema` is only the pre-edit default.
  Downstream nodes and the completion EndEvent can read the declared
  `scriptResponse` variable directly. Only when a distinct business variable
  is needed, add a custom output that reads `=vars.<script-response-id>` and
  writes that variable, marked `custom="true"`.
- Studio maps JavaScript/JSON Schema `number` to BPMN primitive `type="double"`
  and JSON Schema `integer` to BPMN primitive `type="integer"`. Keep the JSON
  Schema names inside schema bodies; on node-scoped `uipath:variables` and
  mapping attributes use `double` or `integer` respectively, not `number` or
  `long`. This is the inverse of the public declaration rule in
  [Variables](structural-bpmn-variables.md#variables): a root `uipath:input`/`uipath:output` must use `number`, because only
  public declarations reach entry-point schema derivation.
- **The template ships no `<uipath:scriptVersion>`, and that is the second
  correction.** A missing element parses as `v1`
  (`UiPath.PO.BpmnParser/Extensions/Xml/ScriptReader.cs`), and at v1 the runtime
  demands an object return and throws `ScriptTaskInvocationResultError`
  otherwise. Add `<uipath:scriptVersion value="v3" />` as a sibling of
  `uipath:mapping`.
- Return the value directly — `return 6 * 7;`. At v2+ the runtime wraps the
  return under `response` itself, so an extra `{ response: ... }` wrapper
  yields `result.response.response`; under v1 the runtime spreads the returned
  object's keys instead, so there the wrapper is required. The marker is
  matched as `/^v(\d+)$/` — case-sensitive, no trimming: `V3`, `3`, `v3.1` and
  `" v3 "` all fall back to v1 silently, flipping this rule. Do not use
  `source="=result"` or `source="=this.result"`, which read the wrapper object
  rather than the value.
- Do not mutate `Globals.*`, `vars.*`, or process variables inside the script
  body. The supported path is: return a value from the script, then use a
  `uipath:output` mapping to write it to the declared variable. Direct mutation
  is not applied to the runtime, so the variable reads empty afterward.
- Keep the script deterministic: no `Math.random`, `Date.now`, `new Date`, or
  `crypto.*`. Jint provides them, so nothing fails locally — but the same
  inputs must produce the same outputs for a run to be reproducible or
  replayable. Take any timestamp or identifier the process needs from a
  process variable supplied by the caller.

```xml
<!-- in bpmn:process/bpmn:extensionElements -->
<uipath:variables version="v1">
<uipath:inputOutput id="Var_ScriptResponse" name="scriptResponse"
  type="double" elementId="Task_RiskScore" />
<uipath:inputOutput id="Var_ScriptError" name="Error"
  type="jsonSchema" elementId="Task_RiskScore"><![CDATA[
{"type":"object","properties":{"code":{"type":"string"},"message":{"type":"string"},"detail":{"type":"string"},"category":{"type":"string"},"status":{"type":"number"},"element":{"type":"string"}}}
]]></uipath:inputOutput>
<uipath:inputOutput id="Var_RiskScore" name="riskScore"
  type="double" elementId="Task_RiskScore" />
</uipath:variables>

<bpmn:scriptTask id="Task_RiskScore" name="Risk Score" scriptFormat="JavaScript">
  <bpmn:extensionElements>
    <uipath:mapping version="v1">
      <uipath:type value="BPMN.Variables" version="v1" />
      <uipath:context>
        <uipath:inputSchema type="jsonSchema"><![CDATA[{"$schema":"http://json-schema.org/draft-07/schema#","type":"object","properties":{"vars":{"type":"object"},"metadata":{"type":"object"}},"required":[]}]]></uipath:inputSchema>
      </uipath:context>
      <uipath:input name="args" type="json" target="bodyField"><![CDATA[{"vars":"=vars","metadata":"=metadata"}]]></uipath:input>
      <uipath:output name="scriptResponse" type="double" var="Var_ScriptResponse" source="=result.response" />
      <uipath:output name="Error" type="jsonSchema" var="Var_ScriptError" source="=Error" />
      <uipath:output name="riskScore" type="double" var="Var_RiskScore" source="=vars.Var_ScriptResponse" custom="true" />
    </uipath:mapping>
    <uipath:scriptVersion value="v3" />
  </bpmn:extensionElements>
  <bpmn:script><![CDATA[
var score = vars.Var_Amount * 0.01 + vars.Var_DaysOverdue * 2;
return score;
]]></bpmn:script>
</bpmn:scriptTask>
```
