# Operating & Diagnosing a Published API Workflow

<!--skill-flavor:published-operations:start-->
After `uip solution publish` + deploy, the workflow is an Orchestrator **API process**. Local verbs (`uip api-workflow init/validate/run/pack`) no longer apply to the deployed copy. Operate and diagnose it through the platform surfaces below. These commands belong to sibling skills—`uip or` / `uip is` to `uipath-platform`, and root-cause work to `uipath-troubleshoot`—but remain actionable here. All require `uip login`.

## Invoke the published workflow

A published API workflow has three triggers:

| Trigger | Fires when | Drive it with |
|---|---|---|
| **HTTP** | A caller POSTs JSON matching `input.schema`; the run is synchronous and returns the `Response` output. | Run `uip or jobs start <process-key> --output json`. |
| **Schedule** | Orchestrator reaches the cron cadence. | Run `uip or triggers create` / `list` / `get` / `update` / `delete`. |
| **Integration Service event** | An upstream connector event/webhook starts the workflow and passes its payload as input. | Configure the event subscription in Integration Service; inspect it with `uip or triggers list --folder-path <path>`. |

All three deliver payloads as workflow input variables; the same body runs when the input shape matches.

`uip or` commands are folder-scoped:

- Run `jobs list` with `--folder-path <path>`, `--folder-key <key>`, or `--all-folders` (searches every folder).
- Run `triggers list`/`create`/`get`/`update`/`delete` with `--folder-path <path>` or `--folder-key <key>`; these commands do not accept `--all-folders`.
- Run `jobs start <process-key>` with the process key as a required positional; the folder is optional and is inferred from the process when omitted.
- Run `jobs get`/`logs`/`stop` with `<jobId>` directly; these commands have no folder selector.

## Manage consumed Integration Service connections

API workflows bind named Integration Service connections at author time and reuse them at runtime. Run:

```bash
uip is connections list --all-folders --output json   # enumerate (folder-scoped; --all-folders searches every folder)
uip is connections ping <connection-uuid> --output json # health — Code: "ConnectionPing" = usable
uip is connections edit <connection-uuid>               # re-authenticate (opens OAuth browser flow)
```

If the bound connection does not `ping`, the cloud run returns 401 regardless of JSON correctness. See [connector-activity-discovery.md](connector-activity-discovery.md) for author-time discovery and verification, and [troubleshooting.md](troubleshooting.md) for stale-listing / `ConnectionNotEnabled` failures.

## Operate the deployed process

Run:

```bash
uip or processes list --output json                     # confirm the API process deployed
uip or jobs start <process-key> --output json           # invoke a run (folder optional — inferred from the process)
uip or jobs list --all-folders --output json            # runs + their states (needs a folder selector)
uip or jobs get <jobId> --output json                   # one run's status / fault detail
uip or jobs stop <jobId> --output json                  # cancel a running job
```

## Diagnose a failed cloud run

Always run the local diagnose loop before publishing; it catches structure, expression, and logic faults:

```bash
uip api-workflow validate ./Workflow.json --output json   # static: schema + semantic
uip api-workflow run ./Workflow.json --no-auth --output json  # runtime: expression / logic
```

Diagnose cloud-only faults—auth, connection state, real vendor responses, and trigger wiring—from the deployed job. Run `uip or jobs get <jobId> --output json`; it is the only surface carrying the fault, verified end-to-end against a deliberately-faulting deployed API workflow (alpha, uip 1.200.0). Read `Data.Info` first: `Data.State` is `Faulted`, and `Data.Info` usually contains the complete runtime message, such as `"Worker operation failed: <the error your JavaScript or connector activity raised>"`.

Do not diagnose API-workflow jobs from these surfaces:

| Command | Limitation |
|---|---|
| `uip or jobs logs <jobId>` | Returns lifecycle lines only—`"Workflow started"` / `"Workflow completed"`, both at level `Info`. It can report `"Workflow completed"` for a Faulted job and never carries the error. Do not read `"completed"` as success. |
| `uip traces spans get --job-key <jobKey>` | Returned `"Error retrieving trace ID for job"` for every API-workflow job probed. The CLI emits that message for any trace-ID lookup failure, including a malformed GUID; interpret it as "no trace resolved for this job," not proof the surface is absent. It carries no fault detail. |
| `uip or jobs traces <jobId>` | Documented Agent-type-process-only; not applicable to API-workflow jobs. |

Diagnose before teardown. After uninstalling the deployment, `uip or jobs get <jobId>` returns `Result: Failure` with an empty `State`. Jobs are immutable audit records (`uip or jobs --help`: they "cannot be deleted -- they age out per the binding process's retention period"); the likely cause is that the folder/process context needed to resolve the job is gone. Capture required details while the deployment still exists.

For per-activity detail, run `uip api-workflow run <Workflow.json> --no-auth --output json`; local execution names the failing activity, while cloud supplies the fault message. Map the error to [troubleshooting.md](troubleshooting.md)'s category catalog: Structure > Expression > Activity Config > Logic. Hand off deep, multi-signal root-cause investigations—what changed, cross-run comparison, or incident correlation—to **uipath-troubleshoot**.

## Mode cheat-sheet

| Mode | Local (this skill's CLI) | Post-publish (delegate) |
|---|---|---|
| **Build** | Run `init`, edit, `validate`, `registry resolve`/`stub`, and `pack`. | — |
| **Operate** | Run `run` (local execution). | Run `uip or jobs start <process-key>`/`list`/`stop`, manage `uip or triggers` with `--folder-path`/`--folder-key`, and manage `uip is connections`. |
| **Diagnose** | Run `validate` → `run --no-auth`, and run `uip is connections ping`. | Run `uip or jobs get`; `Data.Info` carries the fault. `jobs logs` and `traces spans get` do not work for API-workflow jobs. Then hand off to uipath-troubleshoot. |
<!--skill-flavor:published-operations:end-->