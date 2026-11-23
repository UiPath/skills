<!--skill-flavor:debug-handle:start-->
For a **debug** run in Studio Web, the `Trace ID` that `uip maestro bpmn debug`
prints is the debug instance id. The `debug-instances` commands read it (see
below). Keep deployed-instance reads and debug-session reads separate.
<!--skill-flavor:debug-handle:end-->

<!--skill-flavor:debug-reads:start-->
```bash
uip maestro bpmn debug-instances incidents <TRACE_ID> --output json
uip maestro bpmn debug-instances variables <TRACE_ID> --output json
uip maestro bpmn debug-instances variables-all <TRACE_ID> --output json
```
<!--skill-flavor:debug-reads:end-->

<!--skill-flavor:debug-reference:start-->
```bash
uip maestro bpmn debug-instances incidents <TRACE_ID> --output json
uip maestro bpmn debug-instances variables <TRACE_ID> --output json
uip maestro bpmn debug-instances variables-all <TRACE_ID> --output json
```
<!--skill-flavor:debug-reference:end-->
