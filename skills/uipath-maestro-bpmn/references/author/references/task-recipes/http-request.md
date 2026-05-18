# HTTP Request Recipe

Use this recipe for a plain HTTP request where the workflow owns the URL,
method, payload, and response parsing. Do not use it for connector-authenticated
operations, Integration Service connector objects, dynamic connector schemas, or
tenant-specific connection resources; those remain CLI-enriched Integration
Service work.

## BPMN shape

Use `bpmn:sendTask` for request-and-continue HTTP work.

Do not represent an executable HTTP call as:

- A blank `bpmn:task` or unlabeled placeholder.
- A script task that performs network I/O.
- A connector activity with guessed metadata or copied tenant values.

If the executable HTTP activity shape is unavailable in the current tooling,
keep the node as draft intent and report it as not implemented.

## Executable contract

For confirmed connectionless HTTP execution, use the current UiPath HTTP
activity shape rather than a generic connector guess:

- `uipath:type` service type: `Intsvc.HttpExecution`.
- Request fields are explicit runtime inputs: `mode`, `method`, `url`,
  `headers`, `parameters`, and `body`.
- JSON fields use CDATA and valid JSON objects; use `{}` when no headers,
  parameters, or body are required.
- Output maps the activity `response` to a declared JSON variable with
  `source="=response"`.
- Downstream script or mapping steps consume that response variable and write
  typed process variables for business decisions.

Declare variables for:

- Configurable request inputs when the caller should control them.
- Raw HTTP response, including status code and body.
- Parsed fields that downstream gateways, scripts, or outputs need.
- Final user-facing result variables.

## Generic XML shape

Use this shape for plain connectionless HTTP. Keep IDs, names, URL, method,
and target variables specific to the workflow; keep the field set intact.

```xml
<uipath:inputOutput id="Var_HttpResponse" name="httpResponse" type="jsonSchema"><![CDATA[
{"type":"object"}
]]></uipath:inputOutput>

<bpmn:sendTask id="Task_CallHttpEndpoint" name="Call HTTP endpoint">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Intsvc.HttpExecution" version="v1" />
      <uipath:context>
        <uipath:input name="mode" type="string" value="manual" />
        <uipath:input name="method" type="string" value="GET" />
        <uipath:input name="url" type="string" value="https://example.invalid/resource" />
        <uipath:input name="headers" type="json"><![CDATA[{}]]></uipath:input>
        <uipath:input name="parameters" type="json"><![CDATA[{}]]></uipath:input>
        <uipath:input name="body" type="json"><![CDATA[{}]]></uipath:input>
      </uipath:context>
      <uipath:output name="response" type="json" source="=response" var="Var_HttpResponse" />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>Flow_Previous_CallHttpEndpoint</bpmn:incoming>
  <bpmn:outgoing>Flow_CallHttpEndpoint_Next</bpmn:outgoing>
</bpmn:sendTask>
```

For `POST`, `PUT`, or `PATCH`, keep `headers`, `parameters`, and `body`
present. Put JSON request payloads in `body` CDATA and parse the raw response
in a downstream script task rather than embedding business logic in the HTTP
activity.

## Verification

Local validation is necessary but not enough to call HTTP work implemented.
Before reporting an HTTP node as executable, verify one of:

- CLI/Studio Web enrichment generated the HTTP activity metadata.
- A debug/run instance shows the HTTP element received request inputs and
  produced the mapped response variable.

When a run is available, inspect instance variables and confirm:

- The HTTP task output includes status and response body.
- Parse steps read the raw response variable and produce non-placeholder
  business variables.
- Final outputs reflect parsed runtime data, not canned text.

## Status language

Use precise status in summaries:

- **Executable** - request activity, input fields, output variable, and
  downstream mappings are present; runtime variable evidence is available if a
  run was performed.
- **Draft** - BPMN shape and intent are present, but executable HTTP metadata is
  missing or awaiting enrichment.
- **Mock** - the process returns fixed sample data instead of calling HTTP.
- **Blocked** - required URL, auth, schema, or enrichment decision is missing.
