<!--skill-flavor:debug-handle:start-->
For a **debug** run in Studio Web, the reply of `uip maestro bpmn debug` has no
instance id. Its run logs and execution trace are the evidence. Keep
deployed-instance reads and debug-run evidence separate.
<!--skill-flavor:debug-handle:end-->

<!--skill-flavor:debug-runs:start-->
A Studio Web debug reply has no instance id, so the `debug-instance` commands
have nothing to read. Use the run logs and execution trace that
`uip maestro bpmn debug` printed. They list each element's status. When a
value matters, read the output that the trace shows for that element.
<!--skill-flavor:debug-runs:end-->

<!--skill-flavor:debug-instance-reference:start-->
<!--skill-flavor:debug-instance-reference:end-->
