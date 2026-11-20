# HTTP Request (`http-request`)

Built-in tool for **inline agents in a Flow**. Sends one outbound HTTP request to a public URL and returns the status code, response headers, and response body. No connection, no deployment, no solution-level files.

For the built-in-tools capability overview, see [built-in-tools.md](built-in-tools.md).

## When to Use

- Inline agent in a Flow must call a public web API that needs no credentials
- Endpoint, method, or query is decided at run time by the model, or pinned per argument (see [§ Pin Arguments](#pin-arguments))

Do not use it when:

- **The agent is standalone.** The tool is available only to inline agents in a Flow — Agent Builder has no UI for it. Never author it on a standalone agent, even though `uip agent validate` accepts the resource there and even when the request names the tool. What to do instead: [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) § What NOT to Do 25. To build the agent inside a Flow: [../inline-in-flow/inline-in-flow.md](../inline-in-flow/inline-in-flow.md).
- The call needs credentials — add an Integration Service tool instead ([../integration-service/integration-service.md](../integration-service/integration-service.md)). This tool attaches no credentials of its own, and a secret written into a static header is plain text in `resource.json`.
- The target is inside a private network — the tool rejects hosts that resolve to non-public addresses.
- The response is binary — the body comes back as text.

## Authoring

Flow node: `uipath.agent.resource.tool.builtin.httprequest`, on tenants that offer it.

| Flow project | Do |
|---|---|
| Builder-SDK (`.flow.ts`) — the default | Do not author `resource.json`: `compile` writes it and deletes a hand-written one. Hand the tool to the `uipath-maestro-flow` skill, which declares it as an `httpRequest` tool on the `inlineAgent` step. State which arguments are fixed and which the model fills ([§ Arguments](#arguments)) |
| JSON-authored `.flow` | Follow [§ Walkthrough](#walkthrough): author the resource, then hand the node and its edge to the `uipath-maestro-flow` skill |

## Resource Shape

JSON-authored `.flow` only.

**Path:** `<FlowProjectDir>/<projectId>/resources/<RES_UUID>/resource.json` — `<RES_UUID>` is a fresh UUID, equal to the `id` field and to the flow node's `inputs.source`. See [../inline-in-flow/inline-in-flow.md](../inline-in-flow/inline-in-flow.md) § Inline-in-Flow Resource Paths.

```json
{
  "$resourceType": "tool",
  "id": "<RES_UUID>",
  "referenceKey": null,
  "name": "HTTP Request",
  "type": "internal",
  "description": "Make an outbound HTTP request to a URL and return the status code, response headers, and response body. Use this to call public web APIs.",
  "isEnabled": true,
  "inputSchema": {
    "type": "object",
    "properties": {
      "url": { "type": "string", "description": "The absolute URL to send the request to." },
      "method": { "type": "string", "description": "HTTP method to use, one of: GET, POST, PUT, PATCH, DELETE." },
      "headers": {
        "type": "array",
        "description": "Request headers as a list of name/value pairs.",
        "items": {
          "type": "object",
          "properties": {
            "name": { "type": "string", "description": "Header name." },
            "value": { "type": "string", "description": "Header value." }
          },
          "required": ["name", "value"]
        }
      },
      "params": {
        "type": "array",
        "description": "Query-string parameters as a list of name/value pairs.",
        "items": {
          "type": "object",
          "properties": {
            "name": { "type": "string", "description": "Parameter name." },
            "value": { "type": "string", "description": "Parameter value." }
          },
          "required": ["name", "value"]
        }
      },
      "body": {
        "type": "string",
        "description": "Request body sent as-is. Provide JSON as a string and set a Content-Type header if the endpoint expects JSON."
      },
      "timeout": { "type": "number", "description": "Request timeout in seconds." }
    },
    "required": ["url"]
  },
  "outputSchema": { "type": "object", "properties": {} },
  "settings": {},
  "guardrail": { "policies": [] },
  "argumentProperties": {},
  "properties": {
    "toolType": "http-request"
  }
}
```

Copy verbatim. Change only:

| Field | Rule |
|---|---|
| `id` | The resource folder's UUID |
| `name` | Rename when the agent has several HTTP tools (`Get Order Status`) |
| `description` | Say what the endpoint does — the model picks the tool from this text |
| `inputSchema.properties.<arg>.description` | Tell the model what to pass for an argument it fills (for example, which base URL or which query parameters) |
| `argumentProperties` | Pin arguments — [§ Pin Arguments](#pin-arguments) |

Keep the property names, types, and `required: ["url"]`. `outputSchema` stays as shown: the runtime returns the fixed output in [§ Output](#output) whatever this field holds.

## Arguments

| Argument | Type | Runtime behavior |
|---|---|---|
| `url` | string, required | A value without a scheme gets `https://`. Only `http` and `https` are sent |
| `method` | string | Default `GET`. Case-insensitive. One of `GET`, `POST`, `PUT`, `PATCH`, `DELETE` |
| `headers` | array of `{ "name", "value" }` | Sent as strings. A repeated name keeps the last value |
| `params` | array of `{ "name", "value" }` | Appended as the query string |
| `body` | string | Sent as-is. A string holding a JSON object or array gets `Content-Type: application/json` unless a `Content-Type` header is set |
| `timeout` | number | Seconds, greater than 0. Default 30 |

## Pin Arguments

An argument with no `argumentProperties` entry is filled by the model on each call. Pin the ones that must not vary. Entry shapes and rules: [built-in-tools.md § Argument Sources](built-in-tools.md#argument-sources-argumentproperties).

Fixed `GET` and `Accept` header, URL taken from an agent input field, model fills `params`:

```json
{
  "$['method']": { "variant": "static", "value": "GET", "isSensitive": false },
  "$['url']": { "variant": "argument", "argumentPath": "$['<AGENT_INPUT_FIELD>']", "isSensitive": false },
  "$['headers']": {
    "variant": "static",
    "value": [{ "name": "Accept", "value": "application/json" }],
    "isSensitive": false
  }
}
```

Static value types follow the argument: `headers` and `params` take an array of `{ "name", "value" }` pairs with string values, `timeout` a number, the others a string.

## Output

```json
{ "statusCode": 200, "headers": { "content-type": "application/json" }, "body": "<RESPONSE_BODY_TEXT>" }
```

- A non-2xx response is returned like any other — the model reads `statusCode` and decides. Tell it in the system prompt what to do on `4xx` / `5xx`.
- `body` is always text. JSON arrives as a string; the model parses it.

## Limits and Errors

- **Public hosts only.** A host that resolves to a private, loopback, link-local (cloud metadata included), multicast, or reserved address is rejected with `Request was blocked: …`. The check runs on every redirect hop.
- **Redirects** are followed, at most 5.
- **No credentials attached.** The request carries only the headers the tool is given — no UiPath token, no platform headers.
- **Model-correctable failures do not fault the run.** Invalid arguments, an unsupported method, a blocked or unresolvable host, a timeout, or a transport error come back to the model as a tool error message; the model can fix the call and retry. Each failed call costs one agent turn.

## Walkthrough

For an inline agent in a JSON-authored `.flow`. Builder-SDK project: [§ Authoring](#authoring). Standalone agent: stop — [§ When to Use](#when-to-use).

1. **Author the tool resource** at `<FlowProjectDir>/<projectId>/resources/<RES_UUID>/resource.json` from [§ Resource Shape](#resource-shape). Generate a fresh UUID; use it for the folder and for `id`.
2. **Pin what must not vary** in `argumentProperties`. For an `argument` entry, the field must exist in the inline agent's `agent.json` → `inputSchema`.
3. **Name the tool in the system prompt** when the agent should prefer it for a specific task, and state what to do with error status codes.
4. **Hand the flow node to the `uipath-maestro-flow` skill:** node `uipath.agent.resource.tool.builtin.httprequest` with `inputs.source` = `<RES_UUID>`, plus its edge to the agent's `tool` handle — [built-in-tools.md](built-in-tools.md) Critical Rule 5. If `uip maestro flow registry get` does not return that node, stop and tell the user — never hand-write the node.
5. **Refresh**, then **validate**. The tool produces no binding, so no `uip solution resources refresh` is needed for it:

   ```bash
   uip agent refresh "<FlowProjectDir>/<projectId>" --inline-in-flow --output json
   uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json
   ```

## Gotchas

- `properties.toolType` MUST be exactly `"http-request"`. Any other value fails validation with `Invalid input`.
- The Flow canvas HTTP Request node has a connector-authentication mode. That mode stores an Integration Service tool (`type: "integration"` with a connection), not this resource.

## References

- [built-in-tools.md](built-in-tools.md) — capability overview, argument sources
- [../inline-in-flow/inline-in-flow.md](../inline-in-flow/inline-in-flow.md) — inline agent layout, resource paths, flow node wiring
- [../integration-service/integration-service.md](../integration-service/integration-service.md) — authenticated calls through a connection
