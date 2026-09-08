<!--skill-flavor:flow-intro:start-->
Flow nodes invoke other flows as subprocesses from within a flow. Published flows appear in the registry after `uip login` + `uip maestro flow registry pull`. **In-solution** (unpublished) flows in sibling projects of the open solution are listed with `uip solution resources list --kind Process --output json` — no login or publish required.
<!--skill-flavor:flow-intro:end-->

<!--skill-flavor:flow-selection-table:start-->
| Flow not yet published but in the same solution | Yes — find it with `uip solution resources list --kind Process` (no login or publish needed) |
| Flow does not exist yet | Create it in the open solution with `uip flow init <Name>` (this skill), then find it with `uip solution resources list --kind Process --output json` |
<!--skill-flavor:flow-selection-table:end-->

<!--skill-flavor:flow-discovery:start-->
```bash
uip solution resources list --kind Process --output json
uip solution resources get <key> --output json
```

`solutionResources` lists the open solution's projects with `key`, `name`, `kind`, `type` (`flow` for Flow projects); deployed processes are under `availableResources`. `registry list|get --local` needs a `.uipx` and fails in Studio Web. Create a missing sibling with `uip flow init <Name>` — registration is automatic, no `.uipx`, no `uip solution projects add`.
<!--skill-flavor:flow-discovery:end-->
