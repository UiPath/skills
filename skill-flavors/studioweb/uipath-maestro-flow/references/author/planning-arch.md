<!--skill-flavor:planning-arch-registry-rules:start-->
> **Registry rules:** `registry search` and `registry list` are allowed for discovery. Run `registry get` once for every OOTB action node type used (`core.action.http`, `core.action.http.v2`, `core.action.script`, `core.action.transform`, queue actions, etc.); this provides real schemas, ports, and required fields. Defer `registry get` for connector nodes requiring `--connection-id` and resource nodes requiring in-solution or published-resource resolution to [Planning Phase 2: Implementation](planning-impl.md).
<!--skill-flavor:planning-arch-registry-rules:end-->

<!--skill-flavor:planning-arch-registry-auth:start-->
Authentication is host-provided — the registry already includes tenant connector and resource nodes, there is no login step, and a 401/403 means the signed-in user lacks rights on the tenant or folder. For sibling projects in the open solution, list them with:

```bash
uip solution resources list --kind Process --output json   # solutionResources = in-solution projects; availableResources = deployed processes per folder
```

Prefer in-solution resources over mocks. `registry list|search|get --local` needs a local solution manifest and is unavailable in Studio Web; resolve a sibling's node type through the tenant registry (`uip maestro flow registry search "<name>" --output json`) and record it as a mock in **Open Questions** only when the sibling is not published yet.
<!--skill-flavor:planning-arch-registry-auth:end-->

<!--skill-flavor:planning-arch-discovery-record:start-->
- **Resources:** check `uip solution resources list --kind Process --output json` (`solutionResources`) first, then tenant registry; record whether each RPA process, agent, or flow exists. Defer schemas to Phase 2.
- **Gaps:** use `core.action.http.v2` manual mode when no connector exists; use in-solution resources when unpublished but in solution; use `core.logic.mock` when a resource is neither in solution nor published; flag connectors lacking connections after verified empty results.

Run `registry get` for OOTB actions during discovery. Defer connector `registry get --connection-id` and resource resolution (in-solution or published) to Phase 2.
<!--skill-flavor:planning-arch-discovery-record:end-->

<!--skill-flavor:planning-arch-connector-nodes:start-->
Connector nodes are Integration Service nodes, not built-in. They appear after `uip maestro flow registry pull` (the host injects your session; there is no login step). Use [connector](plugins/connector/planning.md) when a pre-built connector exists. In Phase 1 record `connector: <service-name>` and intended operation; Phase 2 resolves exact type, connection, and fields.
<!--skill-flavor:planning-arch-connector-nodes:end-->

<!--skill-flavor:planning-arch-output-location:start-->
Generate `<SolutionName>.uipath.flow.arch.plan.md` inside the Flow project directory (`/solution/<ProjectName>/`) — there is no solution folder on disk in Studio Web — or under `/tmp` if the user does not want the plan in the project. Use `$SOLUTION` (or `CurrentSolution.SolutionName`) for the solution name; the plan covers the entire solution.
<!--skill-flavor:planning-arch-output-location:end-->
