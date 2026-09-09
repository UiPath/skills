<!--skill-flavor:agent-impl-kinds:start-->
- **In this solution**: a sibling project of the open solution. `{key}` is the sibling's resource `key` from `uip solution resources list --kind Process --output json` (`solutionResources`); registration into the solution is automatic when the project is created (`uip agent init <Name>`), and runtime resolution uses the open solution's Resources panel. `definitions[]` uses `model.section: "In this solution"`.
<!--skill-flavor:agent-impl-kinds:end-->

<!--skill-flavor:agent-impl-discovery:start-->
Only published agents from the logged-in tenant appear. There is no `.uipx` in Studio Web, so the `--local` registry lookups do not exist here (`registry list|get --local` fails with `No .uipx solution file found`). List the open solution's projects instead; no login is required:

```bash
uip solution resources list --kind Process --output json   # solutionResources = in-solution projects (key, name, kind, type); --kind Agent is also accepted
uip solution resources get <key> --output json
```

<!--skill-flavor:agent-impl-discovery:end-->

<!--skill-flavor:agent-impl-discovery-2:start-->
```bash
uip maestro flow registry get "uipath.core.agent.{key}" --output json
```

The command requires `uip login` and shows only published tenant agents. Confirm from `registry get`:
<!--skill-flavor:agent-impl-discovery-2:end-->

<!--skill-flavor:agent-impl-in-solution-definition:start-->
Set `display.icon` by inspecting the sibling project root: use `"autonomous-agent"` when `agent.json` exists, otherwise `"coded-agent"`.

Never hand-author `definitions[]`. In Studio Web the registry serves no manifest for an unpublished sibling (`registry get --local` needs a `.uipx` and fails here): add the in-solution agent node from the designer's add-node panel, which writes the definition into `new.flow`, then continue editing that file. Read `<resourceKey>` from the sibling's `key` in `uip solution resources list --kind Process --output json` (`solutionResources`); there is no `resources/solution_folder/` in Studio Web. For a published agent, read `<DEFINITION_VERSION>` from `.version` in `registry get` output.
<!--skill-flavor:agent-impl-in-solution-definition:end-->

<!--skill-flavor:agent-impl-create:start-->
- **In-solution sibling, low-code**: `uip agent init <Name>` creates the agent project in the open solution (registration is automatic — no `.uipx`, no `uip solution projects add`); configure it with `uipath-agents`, then read its `key` from `uip solution resources list --kind Process --output json`.
- **Coded agents**: `uip codedagent init|deploy|run` are not available in Studio Web — coded agents cannot be scaffolded or run from the browser. Plan a published one (deployed from a developer machine), then `uip maestro flow registry pull --force`. See [coded/embedding-in-flows.md](../../../../../uipath-agents/references/coded/embedding-in-flows.md).
- **Published low-code**: the agent is published with its solution — for the open one, `uip solution publish --location "<FolderPathOrKey>"` (destination from `uip solution publish --help` PublishLocations) — then `uip maestro flow registry pull --force`.
<!--skill-flavor:agent-impl-create:end-->

<!--skill-flavor:agent-impl-debug-table:start-->
| Node type not found in registry | Agent is unpublished or registry is stale | For an in-solution agent, run `uip solution resources list --kind Process --output json`. Otherwise run `uip login` then `uip maestro flow registry pull --force`. Coded agents must be deployed from a developer machine — `uip codedagent` is not available in Studio Web. |
| In-solution node does not resolve | `resourceKey` was invented | Run `uip solution resources list --kind Process --output json` and use the sibling's `key`; there is no `resources/solution_folder/` in Studio Web. |
| Agent execution failed | Underlying agent error | Inspect `$vars.{nodeId}.error`; coded agents cannot be run from the browser (`uip codedagent run` is unavailable) — test them on a developer machine. |
| Empty `output.content` | Agent returned no response | Verify configuration in Orchestrator for published agents or in the designer for in-solution agents. |
<!--skill-flavor:agent-impl-debug-table:end-->
