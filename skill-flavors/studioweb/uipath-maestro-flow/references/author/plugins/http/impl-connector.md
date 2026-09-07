<!--skill-flavor:http-connector-node-add:start-->
```bash
uip maestro flow node add /solution/<FlowProject>/new.flow core.action.http.v2 \
  --label "<HTTP node label>" --output json
```
<!--skill-flavor:http-connector-node-add:end-->

<!--skill-flavor:http-connector-configure:start-->
```bash
uip maestro flow node configure /solution/<FlowProject>/new.flow <nodeId> \
  --detail '{
    "authentication": "connector",
    "targetConnector": "<target-connector-key>",
    "connectionId": "<target-connection-id>",
    "folderKey": "<folder-key>",
    "method": "GET",
    "url": "/api/endpoint",
    "query": {"param1": "value1"}
  }' --output json
```
<!--skill-flavor:http-connector-configure:end-->

<!--skill-flavor:http-connector-cli-effects:start-->
- Builds the full `inputs.detail` (connector, connectionId, bodyParameters, essentialConfiguration)
- Auto-fills both `bodyParameters.path` and `bodyParameters.url` from the single `url` value you pass
- Writes `bindings_v2.json` in the project directory (`/solution/<FlowProject>/bindings_v2.json`); the host debug reads the saved project directly
- Does not create a `resources/solution_folder/connection/` file — there is no solution-level resources folder in Studio Web. The connection must be on the open solution's Resources panel: check with `uip solution resources list --kind Connection --output json` and add it there if missing
<!--skill-flavor:http-connector-cli-effects:end-->
