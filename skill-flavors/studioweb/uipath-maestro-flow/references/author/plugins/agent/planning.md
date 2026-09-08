<!--skill-flavor:agent-intro:start-->
Agent nodes invoke UiPath AI agents from within a flow. Published agents appear in the registry after `uip maestro flow registry pull` (auth is host-provided). **In-solution** (unpublished) agents in sibling projects of the open solution are listed with `uip solution resources list --kind Process --output json` — no publish required. Both **coded** (Python) and **low-code** (agent.json) agents appear here once deployed — the flow treats them identically.
<!--skill-flavor:agent-intro:end-->

<!--skill-flavor:agent-when-not-local:start-->
- **Agent in the same solution but not yet published** — find it with `uip solution resources list --kind Process` (see below)
- **Agent does not exist yet** — create it in the open solution with `uip agent init <Name>` (configure it with `uipath-agents`), then find it with `uip solution resources list --kind Process --output json`
<!--skill-flavor:agent-when-not-local:end-->

<!--skill-flavor:agent-discovery:start-->
**Published (tenant registry):**

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.agent" --output json
```

Auth is host-provided; a 401/403 means the signed-in user lacks rights on the tenant. Returns published tenant resources only — for in-solution sibling projects, use the solution-resources listing below.

**In-solution (sibling projects of the open solution):**

```bash
uip solution resources list --kind Process --output json   # --kind Agent is also accepted
uip solution resources get <key> --output json
```

`solutionResources` lists the open solution's projects with `key`, `name`, `kind`, `type`; deployed processes are under `availableResources`. `registry list|search|get --local` needs a `.uipx` and fails in Studio Web. Create a missing sibling with `uip agent init <Name>` — registration is automatic, no `.uipx`, no `uip solution projects add`.
<!--skill-flavor:agent-discovery:end-->
