<!--skill-flavor:rpa-intro:start-->
RPA nodes invoke RPA processes (XAML or coded C# workflows) from within a flow. Published processes appear in the registry after `uip maestro flow registry pull` (auth is host-provided). **In-solution** (unpublished) processes in sibling projects of the open solution are listed with `uip solution resources list --kind Process --output json` — no publish required.
<!--skill-flavor:rpa-intro:end-->

<!--skill-flavor:rpa-selection-table:start-->
| Situation | Use RPA? |
| --- | --- |
| Desktop/browser automation via a published RPA process | Yes |
| Target system has a REST API | No — use [Connector](../connector/planning.md) or [HTTP](../http/planning.md) |
| RPA process in the same solution but not yet published | Yes — find it with `uip solution resources list --kind Process` (see below) |
| RPA process does not exist yet | Create it in the open solution with `uip rpa init <Name>` (implement it with `uipath-rpa`), then find it with `uip solution resources list` |
| Need AI reasoning, not desktop automation | No — use [Agent](../agent/planning.md) |
<!--skill-flavor:rpa-selection-table:end-->

<!--skill-flavor:rpa-discovery:start-->
**Published (tenant registry):**

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.rpa-workflow" --output json
```

Auth is host-provided (a 401/403 means the signed-in user lacks rights). Only published processes from your tenant appear.

**In-solution (sibling projects of the open solution):**

```bash
uip solution resources list --kind Process --output json
uip solution resources get <key> --output json
```

`solutionResources` lists the open solution's projects with `key`, `name`, `kind`, `type`; deployed processes are under `availableResources`. `registry list|get --local` needs a `.uipx` and fails in Studio Web. Create a missing sibling with `uip rpa init <Name>` — registration is automatic, no `.uipx`, no `uip solution projects add`.
<!--skill-flavor:rpa-discovery:end-->
