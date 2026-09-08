<!--skill-flavor:hitl-apptask-discovery:start-->
**In-solution (apps in the open solution, no login required):**

```bash
uip solution resources list --kind App --output json
uip solution resources get <key> --output json
```

`registry list|get --local` needs a `.uipx` and fails in Studio Web; the solution-resources listing is the replacement.
<!--skill-flavor:hitl-apptask-discovery:end-->
