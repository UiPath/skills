<!--skill-flavor:api-workflow-intro:start-->
API workflow nodes invoke API functions from within a flow. Published API workflows appear in the registry after `uip maestro flow registry pull` (auth is host-provided). **In-solution** (unpublished) API workflows in sibling projects of the open solution are listed with `uip solution resources list --kind Process --output json` — no publish required.
<!--skill-flavor:api-workflow-intro:end-->

<!--skill-flavor:api-workflow-selection-table:start-->
| Situation | Use API Workflow? |
| --- | --- |
| Call a published UiPath API function | Yes |
| Call an external REST API | No — use [HTTP](../http/planning.md) or [Connector](../connector/planning.md) |
| Invoke a published RPA process | No — use [RPA Workflow](../rpa/planning.md) |
| API workflow not yet published but in the same solution | Yes — find it with `uip solution resources list --kind Process` (no publish needed) |
| API workflow does not exist yet | Create it in the open solution with `uip api-workflow init <Name>`, then find it with `uip solution resources list` |
<!--skill-flavor:api-workflow-selection-table:end-->

<!--skill-flavor:api-workflow-discovery:start-->
### Published (tenant registry)

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.api-workflow" --output json
```

Auth is host-provided (a 401/403 means the signed-in user lacks rights). Only published API workflows from your tenant appear.

### In-solution (sibling projects)

```bash
uip solution resources list --kind Process --output json
uip solution resources get <key> --output json
```

`solutionResources` lists the open solution's projects with `key`, `name`, `kind`, `type` (`api` for API workflows); deployed processes are under `availableResources`. `registry list|get --local` needs a `.uipx` and fails in Studio Web. Create a missing sibling with `uip api-workflow init <Name>` — registration is automatic, no `.uipx`, no `uip solution projects add`.
<!--skill-flavor:api-workflow-discovery:end-->
