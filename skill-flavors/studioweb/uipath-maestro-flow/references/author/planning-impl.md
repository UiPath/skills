<!--skill-flavor:planning-impl-local-sibling:start-->
If Phase 1 marked a resource not found, check the open solution first:

```bash
uip solution resources list --kind Process --output json   # solutionResources = in-solution projects; availableResources = deployed processes per folder
```

For a sibling project's node type, use the tenant registry — `registry list|search|get --local` needs a local solution manifest and is unavailable in Studio Web:

```bash
uip maestro flow registry get "<node-type>" --output json
```
<!--skill-flavor:planning-impl-local-sibling:end-->

<!--skill-flavor:planning-impl-mock-discovery:start-->
1. Run `uip solution resources list --kind Process --output json` and look for the resource in `solutionResources` (the in-solution projects).
<!--skill-flavor:planning-impl-mock-discovery:end-->

<!--skill-flavor:planning-impl-plan-location:start-->
Create `<SolutionName>.uipath.flow.impl.plan.md` beside `<SolutionName>.uipath.flow.arch.plan.md` in the Flow project directory (`/solution/<ProjectName>/`, or under `/tmp` if the user does not want it in the project).
<!--skill-flavor:planning-impl-plan-location:end-->
