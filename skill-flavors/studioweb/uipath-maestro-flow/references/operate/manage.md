<!--skill-flavor:manage-preflight:start-->
3. **Instance ID known.** `uip flow debug` prints a `Trace ID` — that is the job key, not an instance id. Resolve the instance with `uip maestro flow job status <TRACE_ID> --detailed --output json` (call it with `timeoutSeconds: 120` and only with a real Trace ID) or `uip maestro flow instance list -f <FOLDER_KEY> --output json` (`-f` is required), or take it from a `flow job status` response for a deployed run.
<!--skill-flavor:manage-preflight:end-->
