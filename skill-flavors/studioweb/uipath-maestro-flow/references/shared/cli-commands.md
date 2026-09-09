<!--skill-flavor:flow-init-command:start-->
## uip flow init

Create a Flow project inside the open solution. Studio Web works on one open solution, already scaffolded as the workspace root (`/solution`); never create another — the solution-creation verbs (`solution init`, `solution new`) are refused by the host. `uip flow init <ProjectName>` (alias `uip maestro flow init <ProjectName>`) is intercepted by the host: it creates the project entity through the same path as the New Project dialog and prints `Created Flow project "<ProjectName>" in the open solution. Its files are under /solution/<ProjectName>.`

```bash
uip flow init <ProjectName>
```

Pass just the name (or `/solution/<ProjectName>`); a nested path is rejected, and template-shaping flags are accepted but reported as ignored. The scaffold is `/solution/<ProjectName>/new.flow` (the entrypoint you edit — manual trigger only, empty `edges`/`definitions`/`bindings`) plus `project.uiproj`; host-generated files such as `entry-points.json`, `bindings_v2.json`, `operate.json`, and `package-descriptor.json` appear after the first debug or publish. Registration into the solution is automatic: there is no `.uipx` and no `uip solution projects add` step.
<!--skill-flavor:flow-init-command:end-->

<!--skill-flavor:pack-command-section:start-->
Not needed in Studio Web, and the two spellings behave differently. The two-token `uip flow pack` (and every two-token `uip <family> pack`) is intercepted by the host and exits 0 with a no-op message. The three-token `uip maestro flow pack` is NOT intercepted — like `uip maestro flow debug` it reaches the browser bundle, whose packager is excluded from that build, so it fails instead of no-opping. Do not script either form: `uip solution publish` packages the open solution server-side and there is no `.nupkg` to produce locally.
<!--skill-flavor:pack-command-section:end-->

<!--skill-flavor:solution-resources-refresh-section:start-->
Not available in Studio Web: `refresh` (and `remove`) need a local solution manifest (`.uipx`) and fail with `not a UiPath solution`. The open solution's resources are managed live with the host-served `uip solution resources list|get|add|edit` or in the designer's Resources panel; bindings written by `node configure` into `/solution/<ProjectName>/bindings_v2.json` are picked up by the solution without a refresh step.

```bash
uip solution resources list --kind Process --output json
```

`--kind Process` returns `solutionResources` — the in-solution projects with their resource keys (`{key,name,kind:"process",type:"flow"|"api"}`) — and `availableResources` (deployed processes per folder). Use it wherever this skill mentions `registry list|search|get --local`, which needs a `.uipx` and fails here. `list --source remote|all` also requires `--kind`.
<!--skill-flavor:solution-resources-refresh-section:end-->

<!--skill-flavor:solution-resources-mutations:start-->
## uip solution resources add / edit

Use atomic mutations when adding or changing one resource:
<!--skill-flavor:solution-resources-mutations:end-->

<!--skill-flavor:solution-resources-mutations-2:start-->
```bash
uip solution resources add --source local --kind <Kind> --name <Name> --output json
uip solution resources add --source remote --kind <Kind> --name <Name> --folder-path <FolderPath> --output json
uip solution resources edit <KEY> --patch '{"maxNumberOfRetries":5}' --output json
```

`add` is idempotent on `(kind, name, folder)` for local resources and on resource key for remote resources; retries return `Status: "Unchanged"`. `edit` mutates an existing resource spec and takes only an inline `--patch` (no stdin `-`). `remove` and `refresh` are not available in Studio Web; `list --source remote|all` needs `--kind`. These commands do not modify `bindings_v2.json`. See [uipath-solution Step 9–11](/uipath:uipath-solution).
<!--skill-flavor:solution-resources-mutations-2:end-->

<!--skill-flavor:upload-safety-eval-surface-note:start-->
<!--skill-flavor:upload-safety-eval-surface-note:end-->

<!--skill-flavor:upload-command-section:start-->
<!--skill-flavor:upload-command-section:end-->

<!--skill-flavor:flow-debug-command-usage:start-->
<a id="uip-maestro-flow-debug"></a>

## uip flow debug

Debug the open Flow through the host. **In Studio Web the verb is `uip flow debug`, not `uip maestro flow debug`** — the two-token form is intercepted by the host; the three-token form is not and lands on a command whose debug service is excluded from the browser bundle, failing with `TypeError: … is not a constructor` (its `--help` prints the Node CLI text and is misleading). Authentication comes from the active Studio Web session. Always run `uip maestro flow validate` first.

```bash
uip flow debug

# Pass input arguments to the flow
uip flow debug --inputs '{"numberA": 5, "numberB": 7}'

# Target a project other than the active one by name
uip flow debug "<ProjectName>" --inputs '{"numberA": 5}'
```

The positional argument is a **project name in the open solution**, not a directory path, and it defaults to the active project. The host runs the already-saved project, so there is no pack, upload, or resource-refresh step. Call it with `timeoutSeconds: 600`: the host waits up to 5 minutes for a terminal state and prints only at exit.

> **Only `-i` / `--inputs` is honoured.** The host interceptor accepts the project name and inline JSON inputs; `--attachment`, `--output`, `--timeout`, and folder flags are ignored or rejected. `--bpmn-file` and a local `.xaml` target are rejected with an explicit message. Inline JSON only — `@file` indirection is not supported.

<!--skill-flavor:flow-debug-command-usage:end-->

<!--skill-flavor:flow-debug-command-usage-2:start-->
`--attachment` cannot bind files in Studio Web — `uip flow debug` ignores it without warning, so a `type:"file"` input stays unset for the run. Declare the variable as usual (see [variables-and-expressions.md — File input](variables-and-expressions.md#file-input)) and test file-typed inputs from the designer's Debug panel or with an upstream node that produces the attachment.

Run `uip flow debug --help` for the host's exact surface.
<!--skill-flavor:flow-debug-command-usage-2:end-->

<!--skill-flavor:flow-debug-command-usage-3:start-->
The output is plain text, not a JSON envelope: line 1 is the status (`Successful`, `Faulted`, `Failed`, or `TimedOut after 300s`), then `Trace ID: <id>` when a trace id was determined, then `Run logs:` (up to 4000 characters) and `Execution trace:` (up to 8000 characters); a run that never started prints `(no run logs emitted)` / `(no execution traces emitted)`. The exit code is 1 when the run did not succeed. Report the status line first and the Trace ID second (`Trace ID: <not returned>` when absent), then a digest of the logs and trace:

```text
Faulted
Trace ID: <id>

<what failed, from Run logs / Execution trace>
```

If the status is `TimedOut…`, say so and do not re-run. `TimedOut after 300s` with `(no run logs emitted)` means the run never reached the runtime — do not retry in a loop; ask the user to run Debug from the designer and paste the result. Only call `uip maestro flow job status <TRACE_ID>` / `job traces <TRACE_ID>` with a real Trace ID from this output — a made-up key hangs until the shell timeout. There is no Studio Web URL or instance id to report.
<!--skill-flavor:flow-debug-command-usage-3:end-->

<!--skill-flavor:eval-login-note:start-->
Evaluation surface: evaluator, eval-set, and data-point CRUD; Studio Web run start/status/results/list/compare. Local CRUD works with `--path /solution/<ProjectName>`. `eval run *` needs both ids passed explicitly (`--solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId>`), can hang on first use — call with `timeoutSeconds: 120`, never `--wait`; on a time-out hand the run to the user via the Studio Web Evaluations panel.
<!--skill-flavor:eval-login-note:end-->

<!--skill-flavor:eval-commands-synopsis:start-->
uip maestro flow eval add <name> --set <set> [flags] --output json
uip maestro flow eval list --set <set> --path /solution/<ProjectName> --output json
uip maestro flow eval remove <id> --set <set> --path /solution/<ProjectName> --output json
uip maestro flow eval set add <name> [--evaluators <refs>] [--entry-point <id>] --path /solution/<ProjectName> --output json
uip maestro flow eval set list --path /solution/<ProjectName> --output json
uip maestro flow eval set remove <id> --path /solution/<ProjectName> --output json
uip maestro flow eval evaluator add <name> --type <type> [--model <m>] [--target-key <k>] [--prompt <p>] --path /solution/<ProjectName> --output json
uip maestro flow eval evaluator list --path /solution/<ProjectName> --output json
uip maestro flow eval evaluator remove <id> --path /solution/<ProjectName> --output json
# every `eval run` verb needs BOTH ids from the context and is called without --wait, with timeoutSeconds: 120
uip maestro flow eval run start <name> --set <set> [--entry-point <e>] --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> --path /solution/<ProjectName> --output json
uip maestro flow eval run status <run_id> --set <set> --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> --path /solution/<ProjectName> --output json
uip maestro flow eval run results <run_id> --set <set> [--only-failed] [--verbose] [--export-format json|csv] --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> --path /solution/<ProjectName> --output json
uip maestro flow eval run list --set <set> --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> --path /solution/<ProjectName> --output json
uip maestro flow eval run compare <run_a> --compare-to <run_b> --set <set> --solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId> --path /solution/<ProjectName> --output json
<!--skill-flavor:eval-commands-synopsis:end-->

<!--skill-flavor:registry-available-on-tenant-note:start-->
Treat `AvailableOnTenant` as a usability gate: `true` permits `registry get <NodeType>` or `node add <NodeType>`; `false` means the node is not enabled or available for the tenant. Do not use unsupported flags such as `--include-unavailable`; choose an enabled alternative, use `uip solution resources list --kind Process --output json` for in-solution projects (`--local` needs a `.uipx` and fails here), or report unavailability. Pass `--limit <n>` whenever you filter `registry list`.
<!--skill-flavor:registry-available-on-tenant-note:end-->
