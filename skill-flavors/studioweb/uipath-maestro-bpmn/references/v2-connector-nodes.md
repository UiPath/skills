<!--skill-flavor:v2-solution-resources-refresh:start-->
Studio Web keeps the open solution's resources in sync, connections
included: skip the `uip solution resources refresh` step that
`Data.V2.Instructions` ends with. It is Node-CLI-only and is not run here.
<!--skill-flavor:v2-solution-resources-refresh:end-->

<!--skill-flavor:trigger-debug-commands:start-->
```bash
uip df records insert <entity-id> --folder-key <folder-key> --body '{"<column>":"<value>"}'
uip maestro bpmn debug "<ProjectName>" --entry-point "<File>.bpmn#<trigger-start-event-id>"
```

`--entry-point` takes the trigger's `filePath` exactly as `entry-points.json`
spells it. Without it the debug starts at the project's default entry point,
which can be the trigger; pass the manual start's `filePath` to debug from the
manual start. A wait is debugged from the manual start, and its event has to
happen while the wait is in progress. `uip maestro bpmn debug` blocks until the run
ends and prints no instance id, so ask the user to cause the event while the
wait runs.
<!--skill-flavor:trigger-debug-commands:end-->
