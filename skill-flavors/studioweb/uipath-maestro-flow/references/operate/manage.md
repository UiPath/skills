<!--skill-flavor:manage-intro:start-->
Intervene in a running or faulted Flow instance: pause, resume, cancel, retry. All commands require `--folder-key <FOLDER_KEY>` (`-f` shorthand). Authentication is injected by the host on every `uip` call — never run `uip login` or `uip login status`; a 401/403 means the signed-in user lacks rights on the folder — report it, do not retry.
<!--skill-flavor:manage-intro:end-->

<!--skill-flavor:manage-preflight:start-->
1. **Authenticated by the host.** No login step exists in Studio Web; on 401/403 report the missing permission instead of retrying.
2. **Folder key resolved.** Get it from `uip or folders list --output json` or from the job/process context. See [shared/cli-conventions.md — `--folder-key` requirement](../shared/cli-conventions.md#6---folder-key-requirement).
3. **Instance ID known.** `uip flow debug` prints a `Trace ID` — that is the job key, not an instance id. Resolve the instance with `uip maestro flow job status <TRACE_ID> --detailed --output json` (call it with `timeoutSeconds: 120` and only with a real Trace ID) or `uip maestro flow instance list -f <FOLDER_KEY> --output json` (`-f` is required), or take it from a `flow job status` response for a deployed run.
<!--skill-flavor:manage-preflight:end-->
