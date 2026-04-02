# Integration Service (IS) Connector Nodes

Connector nodes call external services (Jira, Slack, Salesforce, Outlook, etc.) via UiPath Integration Service. They are dynamically loaded — not built-in — and appear in the registry after `uip login` + `uip flow registry pull`.

## Implementation

### Node Type Pattern

`uipath.connector.<connector-key>.<activity>`

Examples:
- `uipath.connector.uipath-salesforce-slack.send-message`
- `uipath.connector.uipath-atlassian-jira.create-issue`

### Discovery

```bash
uip flow registry search <service> --output json
```

Confirm `category: "connector"` in the results. If the connector key fails, list all connectors:

```bash
uip is connectors list --output json
```

Keys are often prefixed — e.g., `uipath-salesforce-slack` not `slack`.

### How Connector Nodes Differ from OOTB

1. **Connection binding required** — every connector node needs an IS connection (OAuth, API key, etc.) bound in `bindings_v2.json`. Without it, the node cannot authenticate.
2. **Enriched metadata via `--connection-id`** — call `registry get` with `--connection-id` to get connection-aware field metadata. Without it, only base fields are returned — custom fields, dynamic enums, and reference resolution are missing.
3. **`inputs.detail` object** — connector nodes store operation-specific configuration in `inputs.detail`, populated by `uip flow node configure`:
   - `connectionId` — the bound IS connection UUID
   - `folderKey` — the Orchestrator folder key
   - `method` — HTTP method from `connectorMethodInfo` (e.g., `POST`)
   - `endpoint` — API path from `connectorMethodInfo` (e.g., `/issues`)
   - `bodyParameters` — field-value pairs for the request body
   - `queryParameters` — field-value pairs for query string parameters

### Configuration Workflow

Follow SKILL.md Step 4 (4a–4e) for the full connection binding and reference resolution workflow:

1. `uip is connections list "<connector-key>" --output json` — find a connection
2. `uip is connections ping "<connection-id>" --output json` — verify health
3. `uip flow registry get <nodeType> --connection-id <id> --output json` — get enriched metadata + `connectorMethodInfo`
4. `uip is resources describe "<connector-key>" "<objectName>" --connection-id "<id>" --output json` then read the `metadataFile` — full field details including references, types, descriptions
5. `uip is resources execute list` — resolve reference fields (channel IDs, project IDs, etc.)
6. Validate all `required: true` fields have values — ask the user if any are missing

After adding the node with `uip flow node add`, configure it:

```bash
uip flow node configure <file> <nodeId> \
  --detail '{"connectionId": "<id>", "folderKey": "<key>", "method": "<METHOD>", "endpoint": "<path>", "bodyParameters": {...}}'
```

The `method` and `endpoint` values come from `connectorMethodInfo` in the `registry get` response.

### Ports

| Input Port | Output Port(s) |
|---|---|
| `input` | `success` |

### Output Variables

- `$vars.{nodeId}.output` — the connector response (structure depends on the operation)
- `$vars.{nodeId}.error` — error details if the call fails

### HTTP Fallback

When a connector exists but lacks the specific endpoint, use the connector's HTTP Request activity. The connector still manages authentication; you supply the path and payload. Note as `connector: <service> (HTTP fallback)` during planning.

## Debug

### Common Errors

| Error | Cause | Fix |
|---|---|---|
| No connection found | Connection not bound in `bindings_v2.json` | Run SKILL.md Step 4a to bind a connection |
| Connection ping failed | Connection expired or misconfigured | Re-authenticate the connection in the IS portal |
| Missing `inputs.detail` | Node added but not configured | Run `uip flow node configure` with the detail JSON |
| Reference field has display name instead of ID | `uip is resources execute list` was skipped | Resolve the reference field to get the actual ID |
| Required field missing at runtime | Required input field not provided | Check metadataFile for all `required: true` fields in both `requestFields` and `parameters` |
| `$vars` expression unresolvable | Node outputs block missing or node not connected | Verify the node has edges and upstream outputs are correctly referenced |
| `connectorMethodInfo` missing method/path | Used `registry get` without `--connection-id` | Re-run with `--connection-id` for enriched metadata |

### Debug Tips

1. **Always check `bindings_v2.json`** — connector nodes silently fail if the binding is missing or malformed
2. **Compare inputs against metadataFile** — the full metadata (from `is resources describe`) has every field with types, descriptions, and whether it's required
3. **`flow validate` does NOT catch connector-specific issues** — validation only checks JSON schema and graph structure. Missing `inputs.detail` fields, wrong reference IDs, and expired connections are caught only at runtime (`flow debug`)
4. **If a connector key doesn't work** — list all connectors: `uip is connectors list --output json`. Keys are often prefixed with `uipath-`
5. **Query/path parameters** — some required parameters appear only in the metadataFile `parameters` section, not in `requestFields`. Check both.
