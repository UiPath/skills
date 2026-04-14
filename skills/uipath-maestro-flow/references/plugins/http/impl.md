# HTTP Request Node — Implementation

## Node Type

`core.action.http`

## Registry Validation

```bash
uip flow registry get core.action.http --output json
```

Confirm: input port `input`, output ports `default` + dynamic `branch-{id}`, required inputs `method` and `url`.

## JSON Structure

### Basic GET

```json
{
  "id": "fetchOrders",
  "type": "core.action.http",
  "typeVersion": "1.0.0",
  "display": { "label": "Fetch Orders" },
  "inputs": {
    "method": "GET",
    "url": "=js:$vars.apiBaseUrl + '/orders'",
    "headers": {
      "Authorization": "=js:'Bearer ' + $vars.apiToken"
    },
    "contentType": "application/json",
    "timeout": "PT15M",
    "retryCount": 0
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the HTTP request",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the HTTP request fails",
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": { "type": "bpmn:ServiceTask" }
}
```

### POST with Body

```json
{
  "id": "createRecord",
  "type": "core.action.http",
  "typeVersion": "1.0.0",
  "display": { "label": "Create Record" },
  "inputs": {
    "method": "POST",
    "url": "https://api.example.com/records",
    "headers": {
      "Authorization": "=js:'Bearer ' + $vars.apiToken"
    },
    "body": "=js:JSON.stringify({ name: $vars.recordName, type: $vars.recordType })",
    "contentType": "application/json"
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the HTTP request",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the HTTP request fails",
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": { "type": "bpmn:ServiceTask" }
}
```

### Response Branching

```json
{
  "id": "callApi",
  "type": "core.action.http",
  "typeVersion": "1.0.0",
  "display": { "label": "Call API" },
  "inputs": {
    "method": "GET",
    "url": "https://api.example.com/status",
    "branches": [
      {
        "id": "ok",
        "name": "Success",
        "conditionExpression": "$vars.callApi.output.statusCode === 200"
      },
      {
        "id": "notFound",
        "name": "Not Found",
        "conditionExpression": "$vars.callApi.output.statusCode === 404"
      }
    ]
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the HTTP request",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the HTTP request fails",
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": { "type": "bpmn:ServiceTask" }
}
```

Each branch creates a dynamic output port (`branch-ok`, `branch-notFound`). Wire edges from these ports. Unmatched responses go to `default`.

### Connection-Authenticated Request

When a connector exists but lacks the specific endpoint, use the connector's HTTP Request activity. The connector handles auth:

```json
{
  "inputs": {
    "authenticationType": "connection",
    "application": "<connector-key>",
    "connection": "<connection-id>"
  }
}
```

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [flow-editing-operations.md](../../flow-editing-operations.md). Use the JSON structure above for the node-specific `inputs` and `model` fields.

When using response branching, each branch creates a dynamic output port (`branch-{id}`). Unmatched responses go to `default`. See [flow-editing-operations.md](../../flow-editing-operations.md) for edge add procedures.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `url` is empty or invalid | Missing URL input | Provide a valid URL or `=js:` expression |
| Timeout | Request took longer than `timeout` | Increase timeout or check target API |
| Auth failure (401/403) | Wrong or missing auth header | Check `headers.Authorization` or use connection auth |
| Branch not matched | No branch condition evaluated to true | Check `conditionExpression` values; unmatched goes to `default` |
| Body not sent | `body` is null or empty string | Ensure `body` is set for POST/PUT/PATCH |
| `$vars` reference in URL unresolvable | Upstream node not connected | Check edges and node IDs |
