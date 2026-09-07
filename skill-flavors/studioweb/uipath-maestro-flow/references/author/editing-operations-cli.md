<!--skill-flavor:cli-carveouts-scope-note:start-->
This is **not** a structural editing guide. Use direct `.flow` authoring via [editing-operations-json.md](editing-operations-json.md) for OOTB node/edge/variable CRUD, trigger swaps, output mapping, subflows, inline-agent node/wiring, non-connector resources, and in-place updates.

> **When to use this file:** only for CLI-managed carve-outs documented by a plugin: connector activities, connector triggers, and managed HTTP nodes (both `node add` and `node configure`). If you landed here while adding/removing/wiring OOTB nodes, inline-agent nodes, non-connector resources, or other structural graph elements, go back to the Edit / Write guide.

> **Studio Web file name.** In Studio Web the flow file is `/solution/<ProjectName>/new.flow` — read every `<ProjectName>.flow` below as that path (run the commands from `/solution/<ProjectName>`, or pass the absolute path).

The primitive commands below are support commands for carve-out workflows only. They are not an opt-in path for non-carve-out structural edits.
<!--skill-flavor:cli-carveouts-scope-note:end-->

<!--skill-flavor:cli-configure-connector-effects:start-->
**What the CLI handles automatically:**
- Populates `inputs.detail` (connectionId, method, endpoint, bodyParameters, etc.)
- Writes the connection binding into `bindings_v2.json` in the project directory
- In Studio Web the solution's connection resources are managed live by the designer's Resources panel — check them with `uip solution resources list --kind Connection --output json` rather than looking for `resources/solution_folder/…` files (that layout does not exist here)
<!--skill-flavor:cli-configure-connector-effects:end-->

<!--skill-flavor:cli-configure-http-effects:start-->
**What the CLI handles automatically:**
- Wraps your fields into the full `inputs.detail` structure (connector: `uipath-uipath-http`, bodyParameters, configuration)
- Writes the target connector's connection binding into `bindings_v2.json` in the project directory
- In Studio Web the solution's connection resources are managed live by the designer's Resources panel — check them with `uip solution resources list --kind Connection --output json` rather than looking for `resources/solution_folder/…` files (that layout does not exist here)
<!--skill-flavor:cli-configure-http-effects:end-->
