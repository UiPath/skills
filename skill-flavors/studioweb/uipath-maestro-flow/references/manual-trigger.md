<!--skill-flavor:manual-trigger-entry-point:start-->
To run a root other than the default, pass `--entry-point`. For
`uip maestro flow debug`, the value is the path exactly as the `entry-points.json` of
the project lists it: `content/<file>.bpmn#<id>`, where `<id>` is the `id` you
gave `.entryPoint` (the default root's trigger is `start` unless the flow sets
`.triggerId(...)`). For `uip maestro flow process run`, the value is the bare
`<id>`.
<!--skill-flavor:manual-trigger-entry-point:end-->

<!--skill-flavor:trigger-updates-sdk-version:start-->
Needs `@uipath/maestro-builder-sdk` newer than 6.85.2. Check that `entryPoint(` in
`dist/flow-sdk.d.ts` of the SDK that Studio Web ships takes `'version' | 'label' | 'updates'`.
If not, set the variable in the first step's `{ updates }` instead: an older SDK refuses
`.trigger(spec, { updates })` (`UPDATES_NOT_SUPPORTED`) and compiles
`.entryPoint(id, spec, { updates })` with no row at all.
<!--skill-flavor:trigger-updates-sdk-version:end-->
