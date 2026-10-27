<!--skill-flavor:manual-trigger-entry-point:start-->
To run a root other than the default, pass `--entry-point`. For
`uip flow debug`, the value is the path exactly as the `entry-points.json` of
the project lists it: `content/<file>.bpmn#<id>`, where `<id>` is the `id` you
gave `.entryPoint` (the default root's trigger is `start` unless the flow sets
`.triggerId(...)`). For `uip maestro flow process run`, the value is the bare
`<id>`.
<!--skill-flavor:manual-trigger-entry-point:end-->
