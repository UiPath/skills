# Call Activity Recipe

The current supported implementation wrapper for confirmed process calls
exposed through Orchestrator process-orchestration resource types is
`bpmn:callActivity`.

Supported shells:

- `Orchestrator.StartAgenticProcess`
- `Orchestrator.StartAgenticProcessAsync`
- `Orchestrator.StartCaseMgmtProcess`
- `Orchestrator.StartCaseMgmtProcessAsync`

The model may draft:

- Call activity wrapper, mappings, boundary events, and BPMN DI.
- Placeholder-safe called-resource intent when a documented contract exists.
- Synchronous versus asynchronous routing as explicit process behavior.

CLI or operator must resolve:

- Called process identity, package/resource binding, and generated package metadata.
- Dynamic input/output schemas.
- Case-management details unless a dedicated case-management contract is available.

Use subprocesses for inline local process structure. Use call activities when execution leaves the local BPMN scope.

## Mapping shape

Use normal activity mapping rules:

- Inputs read declared process variables with `=vars.<variableId>`.
- Outputs target declared `uipath:inputOutput` or `uipath:output` variable ids.
- Boundary errors, retries, and error mappings use
  [error-handling.md](../../../shared/error-handling.md).
- If the called resource contract is unknown, leave the call activity as draft
  intent instead of guessing input/output schemas.

Minimal draft shell:

```xml
<bpmn:callActivity id="Call_ReviewProcess" name="Call Review Process">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Orchestrator.StartAgenticProcess" version="v1" />
      <uipath:context>
        <uipath:input name="process" type="resource" value="=bindings.Binding_ReviewProcess" />
      </uipath:context>
      <uipath:input name="payload" type="json" target="bodyField"><![CDATA[
        {"requestId":"=vars.Var_RequestId"}
      ]]></uipath:input>
      <uipath:output name="status" type="string" var="Var_CallStatus" source="status" />
    </uipath:activity>
  </bpmn:extensionElements>
</bpmn:callActivity>
```
