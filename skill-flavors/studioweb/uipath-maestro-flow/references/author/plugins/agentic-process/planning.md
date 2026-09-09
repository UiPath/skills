<!--skill-flavor:agentic-process-intro:start-->
Agentic process nodes invoke orchestration processes from within a flow. Published processes appear in the registry after `uip login` + `uip maestro flow registry pull`. **In-solution** (unpublished) processes in sibling projects of the open solution are listed with `uip solution resources list --kind Process --output json` — no login or publish required.
<!--skill-flavor:agentic-process-intro:end-->

<!--skill-flavor:agentic-process-selection-table:start-->
| Process not yet published but in the same solution | Yes — find it with `uip solution resources list --kind Process` (no login or publish needed) |
| Process does not exist yet | Create it in the open solution with `uip bpmn init <Name>`, then find it with `uip solution resources list --kind Process --output json` |
<!--skill-flavor:agentic-process-selection-table:end-->

<!--skill-flavor:agentic-process-discovery:start-->
```bash
uip solution resources list --kind Process --output json
uip solution resources get <key> --output json
```

`solutionResources` lists the open solution's projects with `key`, `name`, `kind`, `type`; deployed processes are under `availableResources`. `registry list|get --local` needs a `.uipx` and fails in Studio Web. Create a missing sibling with `uip bpmn init <Name>` — registration is automatic, no `.uipx`, no `uip solution projects add`.
<!--skill-flavor:agentic-process-discovery:end-->
