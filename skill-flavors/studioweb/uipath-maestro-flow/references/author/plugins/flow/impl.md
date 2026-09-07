<!--skill-flavor:flow-impl-discovery:start-->
### Published (tenant registry)

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.flow" --output json
```

### In-solution (sibling projects)

```bash
uip solution resources list --kind Process --output json   # solutionResources = in-solution projects (key, name, kind, type)
uip solution resources get <key> --output json
```

`registry list|get --local` needs a `.uipx` and fails in Studio Web. Create a missing sibling with `uip flow init <Name>` — registration is automatic, no `.uipx`, no `uip solution projects add`.
<!--skill-flavor:flow-impl-discovery:end-->

<!--skill-flavor:flow-impl-registry-get:start-->
```bash
# Published — the registry serves manifests for published resources only
uip maestro flow registry get "uipath.core.flow.{key}" --output json
```

For an unpublished in-solution sibling, inspect it with `uip solution resources get <key> --output json`. If `registry get` has no manifest for it, do not hand-author `definitions[]`: add the node from the designer's add-node panel (it lists in-solution processes) and continue editing `new.flow`.
<!--skill-flavor:flow-impl-registry-get:end-->

<!--skill-flavor:flow-impl-debug-table:start-->
| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Flow not published or registry stale | Run `uip maestro flow registry pull --force` (auth is host-provided; a 401/403 means missing rights); for in-solution flows use `uip solution resources list --kind Process` |
| Flow execution failed | Underlying flow errored | Check `$vars.{nodeId}.error` for details |
<!--skill-flavor:flow-impl-debug-table:end-->
