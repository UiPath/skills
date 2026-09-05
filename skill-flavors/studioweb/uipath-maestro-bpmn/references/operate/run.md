<!--skill-flavor:local-debug-solution:start-->
In Studio Web the BPMN project already lives in the open solution at
`/solution/<ProjectDirName>/`, so generated resources, bindings, and debug
metadata are available without creating or importing anything. Run debug from
`/solution`:

```bash
uip maestro bpmn debug <ProjectDirName> --output json
```
<!--skill-flavor:local-debug-solution:end-->
