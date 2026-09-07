<!--skill-flavor:agentic-process-intro:start-->
Agentic process nodes invoke orchestration processes from within a flow. Published processes appear in the registry after `uip maestro flow registry pull` (auth is host-provided). **In-solution** (unpublished) processes in sibling projects of the open solution are listed with `uip solution resources list --kind Process --output json` — no publish required.
<!--skill-flavor:agentic-process-intro:end-->

<!--skill-flavor:agentic-process-selection-table:start-->
| Situation | Use Agentic Process? |
| --- | --- |
| Invoke a published orchestration process | Yes |
| Invoke a published AI agent | No — use [Agent](../agent/planning.md) |
| Call another published flow | No — use [Flow](../flow/planning.md) |
| Need desktop/browser automation | No — use [RPA Workflow](../rpa/planning.md) |
| Process not yet published but in the same solution | Yes — find it with `uip solution resources list --kind Process` (no publish needed) |
| Process does not exist yet | Create it in the open solution with `uip bpmn init <Name>`, then find it with `uip solution resources list` |
<!--skill-flavor:agentic-process-selection-table:end-->

<!--skill-flavor:agentic-process-discovery:start-->
### Published (tenant registry)

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.agentic-process" --output json
```

Auth is host-provided (a 401/403 means the signed-in user lacks rights). Only published agentic processes from your tenant appear.

### In-solution (sibling projects)

```bash
uip solution resources list --kind Process --output json
uip solution resources get <key> --output json
```

`solutionResources` lists the open solution's projects with `key`, `name`, `kind`, `type`; deployed processes are under `availableResources`. `registry list|get --local` needs a `.uipx` and fails in Studio Web. Create a missing sibling with `uip bpmn init <Name>` — registration is automatic, no `.uipx`, no `uip solution projects add`.
<!--skill-flavor:agentic-process-discovery:end-->
