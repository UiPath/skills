<!--skill-flavor:troubleshooting-intro:start-->
Diagnostic workflow for failed debug runs and deployed process runs. Authentication is injected by the host on every `uip` call — never run `uip login` or `uip login status`; a 401/403 means the signed-in user lacks rights on the tenant or folder — report it, do not retry.
<!--skill-flavor:troubleshooting-intro:end-->

<!--skill-flavor:priority-step-0-item:start-->
0. The failed `uip flow debug` output you already have (status line, `Run logs:`, `Execution trace:` — no extra call)
<!--skill-flavor:priority-step-0-item:end-->

<!--skill-flavor:step-0-body:start-->
A faulted `uip flow debug` run already carries the cause. **Do not re-run `flow debug` before you read it.** An unchanged re-run repeats the same fault against real systems.

The host prints plain text (no JSON envelope, at most ~12 KB) in this order:

| Section | What it holds |
|---|---|
| line 1 | Status: `Successful`, `Faulted`, `Failed`, or `TimedOut after 300s` |
| `Trace ID: <id>` | The job key for `uip maestro flow job status` / `job traces`. Omitted when the host determined none — report `Trace ID: <not returned>` |
| `Run logs:` | Error messages and the faulting node (≤4000 chars; `(no run logs emitted)` when empty) |
| `Execution trace:` | Spans in execution order (≤8000 chars); the last non-successful span is the failing element |

The command exits 1 when the run failed. Never report a faulted run as "incomplete" — report the status line, the Trace ID, and the error from `Run logs:`. **`TimedOut after 300s` together with `(no run logs emitted)` means the run never reached the runtime** — do not retry in a loop; check that the project validates and has an End node, report it, and ask the user to run Debug from the designer's Debug button and paste the result (or a Trace ID) back.

### Capture once, then extract

Call the shell tool with `timeoutSeconds: 600`; the host prints only when the run reaches a terminal state (up to 5 minutes), so an empty file means the command is still running — see [operate/run.md — Debug](../operate/run.md#debug--controlled-end-to-end-run). `--output json` and `--output-filter` are ignored by the host.

```bash
uip flow debug > /tmp/flow-debug.txt; echo "exit=$?"
head -2 /tmp/flow-debug.txt                                                        # status line + Trace ID
grep -n -i -E 'fault|error|exception|failed|denied|not found' /tmp/flow-debug.txt  # error lines from Run logs
sed -n '/^Execution trace:/,$p' /tmp/flow-debug.txt | tail -20                    # last spans = failing element
```

### Match the fault marker

Match the marker found in `Run logs:` to a known cause:

| Fault marker | Cause and fix |
|---|---|
| `AGENT_STARTUP.INPUT_VALIDATION_ERROR` | Declared `type` does not match the bound node's real output shape — the runtime strict-validates agent inputs. The detail names the failing key and the real type (for example `input_type=list`). See [author/plugins/inline-agent/impl.md — Anti-patterns](../author/plugins/inline-agent/impl.md#anti-patterns). |
| `Folder does not exist or the user does not have access to the folder` | Missing top-level `bindings[]` entries on a resource node — see [failure-modes.md — Missing `bindings[]`](failure-modes.md#missing-bindings-on-resource-node). |

No match, or the log line is not enough → `uip maestro flow job traces <TRACE_ID> --output json` returns the full execution timeline (only with a real Trace ID, `timeoutSeconds: 120` — an unknown key hangs until the tool timeout). For a deployed process run, continue with Step 1.
<!--skill-flavor:step-0-body:end-->

<!--skill-flavor:step-1-body:start-->
The `Trace ID` printed by `uip flow debug` is the **job key**, not an instance id. Resolve the instance and folder from it (real key only, `timeoutSeconds: 120`):

```bash
uip maestro flow job status <TRACE_ID> --output json             # state + folderKey
uip maestro flow job status <TRACE_ID> --detailed --output json  # full job detail
uip maestro flow instance list -f <FOLDER_KEY> --output json     # find the instance of that job (-f is required)
```

For a deployed process run, use the job key from `process run` / `job list` the same way. Parse the instance ID and folder key from the responses.
<!--skill-flavor:step-1-body:end-->

<!--skill-flavor:step-5-body:start-->
Traces are verbose but contain the full execution timeline. Use them only when incidents and variables are insufficient (for a `uip flow debug` run, the job key is the printed Trace ID; call with `timeoutSeconds: 120` and only with a real key):

```bash
uip maestro flow job traces <JOB_KEY> --output json
```
<!--skill-flavor:step-5-body:end-->

<!--skill-flavor:instance-command-reference:start-->
Inspect and manage Flow process instances. Authentication is injected by the host. All subcommands require `--folder-key <FOLDER_KEY>` (`-f` shorthand) — `instance list` rejects the call without it.

```bash
uip maestro flow instance list -f <FOLDER_KEY> --output json                                        # list instances in a folder
uip maestro flow instance get <INSTANCE_ID> -f <FOLDER_KEY> --output json                           # get instance details
uip maestro flow instance incidents <INSTANCE_ID> -f <FOLDER_KEY> --output json                     # get incidents for a failed instance
uip maestro flow instance variables <INSTANCE_ID> -f <FOLDER_KEY> --output json                     # get runtime variable values
uip maestro flow instance variables <INSTANCE_ID> -f <FOLDER_KEY> --parent-element-id <ELEMENT_ID> --output json  # scope to a specific element
uip maestro flow instance element-executions <INSTANCE_ID> -f <FOLDER_KEY> --output json            # get per-element execution details
uip maestro flow instance asset <INSTANCE_ID> -f <FOLDER_KEY> --output json                         # get the deployed BPMN definition
uip maestro flow instance cursors <INSTANCE_ID> -f <FOLDER_KEY> --output json                       # get current execution cursor positions
```
<!--skill-flavor:instance-command-reference:end-->

<!--skill-flavor:incident-reference-intro:start-->
Get incident details for failed flows. Authentication is injected by the host.
<!--skill-flavor:incident-reference-intro:end-->
