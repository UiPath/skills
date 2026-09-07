<!--skill-flavor:hitl-quickform-availability:start-->
Available: always — OOTB, no registry pull required.
<!--skill-flavor:hitl-quickform-availability:end-->

<!--skill-flavor:hitl-apptask-availability:start-->
Available: tenant-specific resource — requires `uip maestro flow registry pull` (auth is host-provided).
<!--skill-flavor:hitl-apptask-availability:end-->

<!--skill-flavor:hitl-apptask-discovery:start-->
**Published (tenant registry):**

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.human-task" --output json
```

**In-solution (apps in the open solution):**

```bash
uip solution resources list --kind App --output json
uip solution resources get <key> --output json
```

`registry list|get --local` needs a `.uipx` and fails in Studio Web; the solution-resources listing is the replacement.
<!--skill-flavor:hitl-apptask-discovery:end-->
