<!--skill-flavor:resolve-uip-prefix:start-->
## 1. `uip` is pre-installed

`uip` is registered in the Studio Web shell and its version is fixed by the host. Never probe or install it — no `uip --version`, `which uip`, `command -v uip`, `npm install`, or `uip tools update`; if a verb is missing, report the capability gap instead. Use `uip maestro flow <verb>` for every Flow command. The one Studio Web-specific exception is the two-token `uip flow debug` (see [cli-commands.md — uip flow debug](cli-commands.md#uip-flow-debug)); `uip flow init` and `uip maestro flow init` are both intercepted by the host.
<!--skill-flavor:resolve-uip-prefix:end-->

<!--skill-flavor:json-output-examples:start-->
uip maestro flow validate /solution/<ProjectName>/new.flow --output json
uip maestro flow registry list --output json
uip maestro flow instance incidents <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json
<!--skill-flavor:json-output-examples:end-->

<!--skill-flavor:output-filter-failure-exception:start-->
> **Exception — any command that fails.** The CLI applies `--output-filter` only on the success path; a `Result: "Failure"` envelope prints whole. The host's `uip flow debug` is different again: it prints plain text (status, `Trace ID`, `Run logs`, `Execution trace`), never an envelope, so redirect it to a file (`> /tmp/flow-debug.txt`) and read from there — see [diagnose/troubleshooting-guide.md — Step 0](../diagnose/troubleshooting-guide.md#step-0--read-the-cause-in-the-debug-output-you-already-have).
<!--skill-flavor:output-filter-failure-exception:end-->

<!--skill-flavor:python-jq-fallback:start-->
Use `jq` or `node` only when JMESPath cannot perform a multi-step join across CLI calls, JSON-to-CSV or JSON-to-env-var conversion, or conditional output based on multiple fields; the Studio Web shell has no `python`. Verify the shape first:
<!--skill-flavor:python-jq-fallback:end-->

<!--skill-flavor:response-shape-debug-note:start-->
Always check `Result` first. On failure, use `Message` and `Instructions` for diagnostics. A failure envelope may still carry `Data`. The host's `uip flow debug` is the exception to this shape: it prints plain text, not an envelope — see §7.
<!--skill-flavor:response-shape-debug-note:end-->

<!--skill-flavor:debug-log-level-section:start-->
<a id="7-use-uip_log_levelinfo-for-debug-runs"></a>

## 7. Reading a debug run

`uip flow debug` prints plain text: line 1 is the status (`Successful`, `Faulted`, `Failed`, or `TimedOut after 300s`), then `Trace ID: <id>` when one was determined, then `Run logs:` (up to 4000 characters) and `Execution trace:` (up to 8000 characters); the exit code is 1 when the run did not succeed. There is no `UIP_LOG_LEVEL` channel, no `jobKey`/`instanceId`, and no Studio Web URL. For more detail than the trace section shows, take the printed Trace ID to `uip maestro flow job status <TRACE_ID>` / `uip maestro flow job traces <TRACE_ID>` — only with a real id from the output; a guessed key hangs until the shell timeout. `TimedOut after 300s` with `(no run logs emitted)` means the run never reached the runtime — do not retry in a loop; ask the user to run Debug from the designer and paste the result. See [cli-commands.md — uip flow debug](cli-commands.md#uip-flow-debug).
<!--skill-flavor:debug-log-level-section:end-->
