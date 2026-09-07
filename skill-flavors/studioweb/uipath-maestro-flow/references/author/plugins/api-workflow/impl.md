<!--skill-flavor:api-workflow-impl-discovery:start-->
### Published (tenant registry)

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.api-workflow" --output json
```

### In-solution (sibling projects)

```bash
uip solution resources list --kind Process --output json   # solutionResources = in-solution projects (key, name, kind, type)
uip solution resources get <key> --output json
```

`registry list|get --local` needs a `.uipx` and fails in Studio Web. Create a missing sibling with `uip api-workflow init <Name>` — registration is automatic, no `.uipx`, no `uip solution projects add`.
<!--skill-flavor:api-workflow-impl-discovery:end-->

<!--skill-flavor:api-workflow-impl-registry-get:start-->
```bash
# Published — the registry serves manifests for published resources only
uip maestro flow registry get "uipath.core.api-workflow.{key}" --output json
```

For an unpublished in-solution sibling, inspect it with `uip solution resources get <key> --output json`. If `registry get` has no manifest for it, do not hand-author `definitions[]`: add the node from the designer's add-node panel (it lists in-solution processes) and continue editing `new.flow`.
<!--skill-flavor:api-workflow-impl-registry-get:end-->

<!--skill-flavor:api-workflow-impl-debug-table:start-->
| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | API workflow not published or registry stale | Run `uip maestro flow registry pull --force` (auth is host-provided; a 401/403 means missing rights); for in-solution API workflows use `uip solution resources list --kind Process` |
| Execution failed | Underlying API workflow errored | Check `$vars.{nodeId}.error` for details |
| Node Completed but `$vars.{nodeId}.output` is null downstream (consumer agent faults `AGENT_STARTUP.INPUT_VALIDATION_ERROR` / incident `170002`) | Instance declares `outputs.output` with `source: "=result.response"`, suppressing the injected `=this` output | Delete the `output` entry — keep `error` only |
<!--skill-flavor:api-workflow-impl-debug-table:end-->
