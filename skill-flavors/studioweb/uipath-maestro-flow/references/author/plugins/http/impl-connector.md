<!--skill-flavor:http-connector-node-add:start-->
uip maestro flow node add /solution/<FlowProject>/new.flow core.action.http.v2 \
<!--skill-flavor:http-connector-node-add:end-->

<!--skill-flavor:http-connector-configure:start-->
uip maestro flow node configure /solution/<FlowProject>/new.flow <nodeId> \
<!--skill-flavor:http-connector-configure:end-->

<!--skill-flavor:http-connector-cli-effects:start-->
- Writes `bindings_v2.json` in the project directory (`/solution/<FlowProject>/bindings_v2.json`); the host debug reads the saved project directly
- Does not create a `resources/solution_folder/connection/` file — there is no solution-level resources folder in Studio Web. The connection must be on the open solution's Resources panel: check with `uip solution resources list --kind Connection --output json` and add it there if missing
<!--skill-flavor:http-connector-cli-effects:end-->
