<!--skill-flavor:debug-instance-source:start-->
For debug runs, `uip bpmn debug` returns no instance id: read the run logs
and execution trace it printed. Keep deployed-instance status reads and
debug-session inspection separate.
<!--skill-flavor:debug-instance-source:end-->

<!--skill-flavor:safe-next-read:start-->
  `uip maestro bpmn instance incidents <INSTANCE_ID> -f <FOLDER_KEY> --output json`" (for a debug run, the
  run logs and execution trace `uip bpmn debug` printed). Name the read; do not run it now. If no repair is needed,
  the read alone is the next action.
<!--skill-flavor:safe-next-read:end-->
