<!--skill-flavor:cli-carveouts-scope-note:start-->
This is **not** a structural editing guide. Use direct `.flow` authoring via [editing-operations-json.md](editing-operations-json.md) for OOTB node/edge/variable CRUD, trigger swaps, output mapping, subflows, inline-agent node/wiring, non-connector resources, and in-place updates.

> **When to use this file:** only for CLI-managed carve-outs documented by a plugin: connector activities, connector triggers, and managed HTTP nodes (both `node add` and `node configure`). If you landed here while adding/removing/wiring OOTB nodes, inline-agent nodes, non-connector resources, or other structural graph elements, go back to the Edit / Write guide.

> **Studio Web file name.** The flow file is always `new.flow`, so every command below is written against that name. Run them from the project directory — `cd /solution/<ProjectName>` (the T1 chain already does this, and the cwd only carries over from a Bash call that exited 0) — or pass the absolute `/solution/<ProjectName>/new.flow`.

The primitive commands below are support commands for carve-out workflows only. They are not an opt-in path for non-carve-out structural edits.
<!--skill-flavor:cli-carveouts-scope-note:end-->

<!--skill-flavor:cli-node-add-command:start-->
```bash
uip maestro flow node add new.flow <node-type> --output json \
  --input '<INPUT_JSON>' \
  --label "<LABEL>" \
  --position <X>,<Y> \
  --parent <PARENT_NODE_ID>
```
<!--skill-flavor:cli-node-add-command:end-->

<!--skill-flavor:cli-node-remove-command:start-->
```bash
uip maestro flow node remove new.flow <NODE_ID>
uip maestro flow node remove new.flow <NODE_ID> --output json
```
<!--skill-flavor:cli-node-remove-command:end-->

<!--skill-flavor:cli-node-list-command:start-->
```bash
uip maestro flow node list new.flow --output json
```
<!--skill-flavor:cli-node-list-command:end-->

<!--skill-flavor:cli-edge-add-command:start-->
```bash
uip maestro flow edge add new.flow <SOURCE_NODE_ID> <TARGET_NODE_ID> --output json \
  --source-port <PORT> \
  --target-port <PORT>
```
<!--skill-flavor:cli-edge-add-command:end-->

<!--skill-flavor:cli-edge-remove-command:start-->
```bash
uip maestro flow edge remove new.flow <EDGE_ID>
uip maestro flow edge remove new.flow <EDGE_ID> --output json
```
<!--skill-flavor:cli-edge-remove-command:end-->

<!--skill-flavor:cli-edge-list-command:start-->
```bash
uip maestro flow edge list new.flow --output json
```
<!--skill-flavor:cli-edge-list-command:end-->

<!--skill-flavor:cli-node-configure-connector-command:start-->
```bash
uip maestro flow node configure new.flow <NODE_ID> \
  --detail '<DETAIL_JSON>'
```
<!--skill-flavor:cli-node-configure-connector-command:end-->

<!--skill-flavor:cli-configure-connector-effects:start-->
**What the CLI handles automatically:**
- Populates `inputs.detail` (connectionId, method, endpoint, bodyParameters, etc.)
- Writes the connection binding into `bindings_v2.json` in the project directory
- In Studio Web the solution's connection resources are managed live by the designer's Resources panel — check them with `uip solution resources list --kind Connection --output json` rather than looking for `resources/solution_folder/…` files (that layout does not exist here)
<!--skill-flavor:cli-configure-connector-effects:end-->

<!--skill-flavor:cli-node-configure-detail-file:start-->
```bash
cat > /tmp/detail.json <<'EOF'
{"connectionId": "<CONNECTION_ID>", "folderKey": "<FOLDER_KEY>", "method": "POST", "endpoint": "/Account"}
EOF
uip maestro flow node configure new.flow <NODE_ID> --detail "$(cat /tmp/detail.json)" --output json
```
<!--skill-flavor:cli-node-configure-detail-file:end-->

<!--skill-flavor:cli-node-configure-http-command:start-->
```bash
uip maestro flow node configure new.flow <NODE_ID> \
  --detail '{
    "authentication": "connector",
    "targetConnector": "<TARGET_CONNECTOR_KEY>",
    "connectionId": "<TARGET_CONNECTION_ID>",
    "folderKey": "<FOLDER_KEY>",
    "method": "GET",
    "path": "/api/endpoint",
    "query": {"param1": "value1"}
  }'
```
<!--skill-flavor:cli-node-configure-http-command:end-->

<!--skill-flavor:cli-configure-http-effects:start-->
**What the CLI handles automatically:**
- Wraps your fields into the full `inputs.detail` structure (connector: `uipath-uipath-http`, bodyParameters, configuration)
- Writes the target connector's connection binding into `bindings_v2.json` in the project directory
- In Studio Web the solution's connection resources are managed live by the designer's Resources panel — check them with `uip solution resources list --kind Connection --output json` rather than looking for `resources/solution_folder/…` files (that layout does not exist here)
<!--skill-flavor:cli-configure-http-effects:end-->

<!--skill-flavor:cli-validate-command:start-->
```bash
uip maestro flow validate new.flow --output json
```
<!--skill-flavor:cli-validate-command:end-->

<!--skill-flavor:cli-trigger-swap-steps:start-->
1. Remove the manual trigger (also removes its edges and orphaned definition):
   ```bash
   uip maestro flow node remove new.flow start --output json
   ```
2. Add the connector trigger node:
   ```bash
   uip maestro flow node add new.flow <TRIGGER_NODE_TYPE> \
     --label "<LABEL>" --position 200,144 --output json
   ```
3. Re-wire edge from the new trigger to the next node:
   ```bash
   uip maestro flow edge add new.flow <NEW_TRIGGER_ID> <NEXT_NODE_ID> \
     --source-port output --target-port input --output json
   ```
4. Configure the trigger with connection and event parameters:
   ```bash
   uip maestro flow node configure new.flow <NEW_TRIGGER_ID> --detail '<TRIGGER_DETAIL_JSON>'
   ```
<!--skill-flavor:cli-trigger-swap-steps:end-->
