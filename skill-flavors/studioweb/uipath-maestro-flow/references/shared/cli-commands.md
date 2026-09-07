<!--skill-flavor:flow-init-command:start-->
## uip flow init

Create a Flow project inside the open solution. Studio Web works on one open solution, already scaffolded as the workspace root (`/solution`); never create another — the solution-creation verbs (`solution init`, `solution new`) are refused by the host. `uip flow init <ProjectName>` (alias `uip maestro flow init <ProjectName>`) is intercepted by the host: it creates the project entity through the same path as the New Project dialog and prints `Created Flow project "<ProjectName>" in the open solution. Its files are under /solution/<ProjectName>.`

```bash
uip flow init <ProjectName>
```

Pass just the name (or `/solution/<ProjectName>`); a nested path is rejected, and template-shaping flags are accepted but reported as ignored. The scaffold is `/solution/<ProjectName>/new.flow` (the entrypoint you edit — manual trigger only, empty `edges`/`definitions`/`bindings`) plus `project.uiproj`; host-generated files such as `entry-points.json`, `bindings_v2.json`, `operate.json`, and `package-descriptor.json` appear after the first debug or publish. Registration into the solution is automatic: there is no `.uipx` and no `uip solution projects add` step.
<!--skill-flavor:flow-init-command:end-->

<!--skill-flavor:validate-governance-login:start-->
`--governance` checks agent nodes against organization policies fetched from the platform with the host session. If governance data cannot be fetched, the command fails. Omit it for local-only schema validation.
<!--skill-flavor:validate-governance-login:end-->

<!--skill-flavor:pack-command-section:start-->
## uip maestro flow pack

Not needed in Studio Web: `uip maestro flow pack` (and every `uip <family> pack`) exits 0 with a no-op message, because `uip solution publish` packages the open solution server-side. There is no `.nupkg` to produce locally.
<!--skill-flavor:pack-command-section:end-->

<!--skill-flavor:solution-resources-refresh-section:start-->
## uip solution resources refresh

Not available in Studio Web: `refresh` (and `remove`) need a local solution manifest (`.uipx`) and fail with `not a UiPath solution`. The open solution's resources are managed live with the host-served `uip solution resources list|get|add|edit` or in the designer's Resources panel; bindings written by `node configure` into `/solution/<ProjectName>/bindings_v2.json` are picked up by the solution without a refresh step.

```bash
uip solution resources list --kind Process --output json
```

`--kind Process` returns `solutionResources` — the in-solution projects with their resource keys (`{key,name,kind:"process",type:"flow"|"api"}`) — and `availableResources` (deployed processes per folder). Use it wherever this skill mentions `registry list|search|get --local`, which needs a `.uipx` and fails here. `list --source remote|all` also requires `--kind`.
<!--skill-flavor:solution-resources-refresh-section:end-->

<!--skill-flavor:solution-resources-mutations:start-->
## uip solution resources add / edit

Use atomic mutations when adding or changing one resource:

```bash
uip solution resources add --source local --kind <Kind> --name <Name> --output json
uip solution resources add --source remote --kind <Kind> --name <Name> --folder-path <FolderPath> --output json
uip solution resources edit <KEY> --patch '{"maxNumberOfRetries":5}' --output json
```

`add` is idempotent on `(kind, name, folder)` for local resources and on resource key for remote resources; retries return `Status: "Unchanged"`. `edit` mutates an existing resource spec and takes only an inline `--patch` (no stdin `-`). `remove` and `refresh` are not available in Studio Web; `list --source remote|all` needs `--kind`. These commands do not modify `bindings_v2.json`. See [uipath-solution Step 9–11](/uipath:uipath-solution).
<!--skill-flavor:solution-resources-mutations:end-->

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

<a id="attachment-preflight"></a>

#### Pre-flight: `--attachment` binding

`--attachment` cannot bind files in Studio Web — `uip flow debug` ignores it without warning, so a `type:"file"` input stays unset for the run. Declare the variable as usual (see [variables-and-expressions.md — File input](variables-and-expressions.md#file-input)) and test file-typed inputs from the designer's Debug panel or with an upstream node that produces the attachment.

Run `uip flow debug --help` for the host's exact surface.

### Reporting the run back to the user

The output is plain text, not a JSON envelope: line 1 is the status (`Successful`, `Faulted`, `Failed`, or `TimedOut after 300s`), then `Trace ID: <id>` when a trace id was determined, then `Run logs:` (up to 4000 characters) and `Execution trace:` (up to 8000 characters); a run that never started prints `(no run logs emitted)` / `(no execution traces emitted)`. The exit code is 1 when the run did not succeed. Report the status line first and the Trace ID second (`Trace ID: <not returned>` when absent), then a digest of the logs and trace:

```text
Faulted
Trace ID: <id>

<what failed, from Run logs / Execution trace>
```

If the status is `TimedOut…`, say so and do not re-run. `TimedOut after 300s` with `(no run logs emitted)` means the run never reached the runtime — do not retry in a loop; ask the user to run Debug from the designer and paste the result. Only call `uip maestro flow job status <TRACE_ID>` / `job traces <TRACE_ID>` with a real Trace ID from this output — a made-up key hangs until the shell timeout. There is no Studio Web URL or instance id to report.
<!--skill-flavor:flow-debug-command-usage:end-->

<!--skill-flavor:process-login-note:start-->
Manage deployed Flow processes (auth comes from the host session):
<!--skill-flavor:process-login-note:end-->

<!--skill-flavor:job-login-note:start-->
Monitor jobs (auth comes from the host session):
<!--skill-flavor:job-login-note:end-->

<!--skill-flavor:eval-login-note:start-->
Evaluation surface: evaluator, eval-set, and data-point CRUD; Studio Web run start/status/results/list/compare. Local CRUD works with `--path /solution/<ProjectName>`. `eval run *` needs both ids passed explicitly (`--solution-id <CurrentSolution.SolutionId> --project-id <CurrentProject.ProjectId>`), can hang on first use — call with `timeoutSeconds: 120`, never `--wait`; on a time-out hand the run to the user via the Studio Web Evaluations panel.
<!--skill-flavor:eval-login-note:end-->

<!--skill-flavor:registry-login-note:start-->
Manage the local node-type cache. Tenant-specific connector nodes are returned with the host session; no login step exists:
<!--skill-flavor:registry-login-note:end-->

<!--skill-flavor:registry-available-on-tenant-note:start-->
Treat `AvailableOnTenant` as a usability gate: `true` permits `registry get <NodeType>` or `node add <NodeType>`; `false` means the node is not enabled or available for the tenant. Do not use unsupported flags such as `--include-unavailable`; choose an enabled alternative, use `uip solution resources list --kind Process --output json` for in-solution projects (`--local` needs a `.uipx` and fails here), or report unavailability. Pass `--limit <n>` whenever you filter `registry list`.
<!--skill-flavor:registry-available-on-tenant-note:end-->
