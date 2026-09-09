<!--skill-flavor:cli-carveouts-scope-note:start-->
> **Studio Web file name.** The flow file is always `new.flow`, so every command below is written against that name. Run them from the project directory — `cd /solution/<ProjectName>` (the T1 chain already does this, and the cwd only carries over from a Bash call that exited 0) — or pass the absolute `/solution/<ProjectName>/new.flow`.

<!--skill-flavor:cli-carveouts-scope-note:end-->

<!--skill-flavor:cli-node-add-command:start-->
uip maestro flow node add new.flow <node-type> --output json \
<!--skill-flavor:cli-node-add-command:end-->

<!--skill-flavor:cli-node-remove-command:start-->
uip maestro flow node remove new.flow <NODE_ID>
uip maestro flow node remove new.flow <NODE_ID> --output json
<!--skill-flavor:cli-node-remove-command:end-->

<!--skill-flavor:cli-node-list-command:start-->
uip maestro flow node list new.flow --output json
<!--skill-flavor:cli-node-list-command:end-->

<!--skill-flavor:cli-edge-add-command:start-->
uip maestro flow edge add new.flow <SOURCE_NODE_ID> <TARGET_NODE_ID> --output json \
<!--skill-flavor:cli-edge-add-command:end-->

<!--skill-flavor:cli-edge-remove-command:start-->
uip maestro flow edge remove new.flow <EDGE_ID>
uip maestro flow edge remove new.flow <EDGE_ID> --output json
<!--skill-flavor:cli-edge-remove-command:end-->

<!--skill-flavor:cli-edge-list-command:start-->
uip maestro flow edge list new.flow --output json
<!--skill-flavor:cli-edge-list-command:end-->

<!--skill-flavor:cli-node-configure-connector-command:start-->
uip maestro flow node configure new.flow <NODE_ID> \
<!--skill-flavor:cli-node-configure-connector-command:end-->

<!--skill-flavor:cli-configure-connector-effects:start-->
- Writes the connection binding into `bindings_v2.json` in the project directory
- In Studio Web the solution's connection resources are managed live by the designer's Resources panel — check them with `uip solution resources list --kind Connection --output json` rather than looking for `resources/solution_folder/…` files (that layout does not exist here)
<!--skill-flavor:cli-configure-connector-effects:end-->

<!--skill-flavor:cli-node-configure-detail-file:start-->
cat > /tmp/detail.json <<'EOF'
{"connectionId": "<CONNECTION_ID>", "folderKey": "<FOLDER_KEY>", "method": "POST", "endpoint": "/Account"}
EOF
uip maestro flow node configure new.flow <NODE_ID> --detail "$(cat /tmp/detail.json)" --output json
<!--skill-flavor:cli-node-configure-detail-file:end-->

<!--skill-flavor:cli-node-configure-http-command:start-->
uip maestro flow node configure new.flow <NODE_ID> \
<!--skill-flavor:cli-node-configure-http-command:end-->

<!--skill-flavor:cli-configure-http-effects:start-->
- Writes the target connector's connection binding into `bindings_v2.json` in the project directory
- In Studio Web the solution's connection resources are managed live by the designer's Resources panel — check them with `uip solution resources list --kind Connection --output json` rather than looking for `resources/solution_folder/…` files (that layout does not exist here)
<!--skill-flavor:cli-configure-http-effects:end-->

<!--skill-flavor:cli-validate-command:start-->
uip maestro flow validate new.flow --output json
<!--skill-flavor:cli-validate-command:end-->

<!--skill-flavor:cli-trigger-swap-steps:start-->
   uip maestro flow node remove new.flow start --output json
<!--skill-flavor:cli-trigger-swap-steps:end-->

<!--skill-flavor:cli-trigger-swap-steps-2:start-->
   uip maestro flow node add new.flow <TRIGGER_NODE_TYPE> \
<!--skill-flavor:cli-trigger-swap-steps-2:end-->

<!--skill-flavor:cli-trigger-swap-steps-3:start-->
   uip maestro flow edge add new.flow <NEW_TRIGGER_ID> <NEXT_NODE_ID> \
<!--skill-flavor:cli-trigger-swap-steps-3:end-->

<!--skill-flavor:cli-trigger-swap-steps-4:start-->
   uip maestro flow node configure new.flow <NEW_TRIGGER_ID> --detail '<TRIGGER_DETAIL_JSON>'
<!--skill-flavor:cli-trigger-swap-steps-4:end-->
