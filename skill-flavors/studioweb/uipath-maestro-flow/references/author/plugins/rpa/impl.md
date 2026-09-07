<!--skill-flavor:rpa-impl-local-discovery:start-->
**In-solution (sibling projects of the open solution):** `registry list|get --local` needs a `.uipx` and fails in Studio Web. List the siblings instead:

```bash
uip solution resources list --kind Process --output json   # solutionResources = in-solution projects (key, name, kind, type)
uip solution resources get <key> --output json
```
<!--skill-flavor:rpa-impl-local-discovery:end-->

<!--skill-flavor:rpa-impl-registry-get:start-->
```bash
uip maestro flow registry get "uipath.core.rpa-workflow.{key}" --output json   # published only
```

For an unpublished sibling, `uip solution resources get <key> --output json` describes it. If `registry get` has no manifest for it, do not hand-author `definitions[]`: add the node from the designer's add-node panel (it lists in-solution processes) and continue editing `new.flow`.
<!--skill-flavor:rpa-impl-registry-get:end-->

<!--skill-flavor:rpa-impl-not-published:start-->
Use this path only after completing the empty-result confirmation in [Discovery](#discovery) and only when no sibling RPA project provides the process. Create the RPA project in the open solution with `uip rpa init <Name>` (registration is automatic — no `.uipx`, no `uip solution projects add`) and implement it with `uipath-rpa`. Once it exists, find its `key` with `uip solution resources list --kind Process --output json` and wire it directly; publishing is not required.
<!--skill-flavor:rpa-impl-not-published:end-->

<!--skill-flavor:rpa-impl-debug-table:start-->
| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Searched by process name (matches release name, not folder), process not published, or registry stale | Search the `uipath.core.rpa-workflow` token and match on folder path — not a name keyword. If in same solution: `uip solution resources list --kind Process --output json`. Otherwise: `uip maestro flow registry pull --force` (auth is host-provided; a 401/403 means missing rights) |
| Input schema mismatch | Inputs don't match `inputDefinition` | Run `registry get` and check required inputs in `inputDefinition.properties` |
| Process execution failed | Underlying RPA process errored | Check `$vars.{nodeId}.error` for details |
| Mock placeholder still in flow | Process not yet replaced | Follow the mock replacement workflow above |
<!--skill-flavor:rpa-impl-debug-table:end-->
