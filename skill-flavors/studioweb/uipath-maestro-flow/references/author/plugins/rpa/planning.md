<!--skill-flavor:rpa-intro:start-->
RPA nodes invoke RPA processes (XAML or coded C# workflows) from within a flow. Published processes appear in the registry after `uip login` + `uip maestro flow registry pull`. **In-solution** (unpublished) processes in sibling projects of the open solution are listed with `uip solution resources list --kind Process --output json` — no login or publish required.
<!--skill-flavor:rpa-intro:end-->

<!--skill-flavor:rpa-selection-table:start-->
| RPA process in the same solution but not yet published | Yes — find it with `uip solution resources list --kind Process` (see below) |
| RPA process does not exist yet | Create it in the open solution with `uip rpa init <Name>` (implement it with `uipath-rpa`), then find it with `uip solution resources list --kind Process --output json` |
<!--skill-flavor:rpa-selection-table:end-->

<!--skill-flavor:rpa-discovery:start-->
**In-solution (sibling projects of the open solution, no login required):**

```bash
uip solution resources list --kind Process --output json
uip solution resources get <key> --output json
```

`solutionResources` lists the open solution's projects with `key`, `name`, `kind`, `type`; deployed processes are under `availableResources`. `registry list|get --local` needs a `.uipx` and fails in Studio Web. Create a missing sibling with `uip rpa init <Name>` — registration is automatic, no `.uipx`, no `uip solution projects add`.
<!--skill-flavor:rpa-discovery:end-->
