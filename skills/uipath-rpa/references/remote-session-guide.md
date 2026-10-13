# Remote Session — Live Authoring and Remote Debug/Run on an Orchestrator Unattended Robot

The `uip rpa remote` group connects the local project to a remote robot — an Orchestrator unattended robot — and operates on it: configure the target, open and close the remote session, execute shell commands, transfer files both ways. Every remote operation acts on the **configured remote target**, stored per project by `remote configure`.

<!--skill-flavor:host-scope:start-->
<!--skill-flavor:host-scope:end-->
## When to Use

- **Design a workflow on a remote machine** — the target application exists only on the remote machine, or UI-heavy design should run there so the user's own machine stays free → **Live Authoring**. Live Authoring is a superset of Remote Run Only: in the same session, also debug/run the workflow on the remote machine — do NOT switch to Remote Run Only for that.
- **Only debug/run a locally designed workflow on a remote machine** (no remote design work, no Live Authoring target configured) → **Remote Run Only**.

Authoring is unchanged: create, edit, and validate the workflow locally per the normal skill workflow.

## Remote Session Modes

The mode is set on `remote configure` with `--live-authoring` or `--remote-run-only`.

| | Live Authoring (`--live-authoring`) | Remote Run Only (`--remote-run-only`) |
|---|---|---|
| Connection | Persistent — one long-lived remote session job on the robot | None |
| Debug / run with `--remote` | Executes on the remote machine, over the session | Each run/debug session is an Orchestrator job of its own |
| `remote exec`, `remote upload-file`, `remote download-file` | Served by the session — return in seconds | Use Live Authoring |
| Remote UI Automation (the `uip rpa uia` group in remote mode — syntax in the UIA package guide `ui-automation-guide.md` § Documentation), remote screen streaming | Available | Not available |
| `remote start` / `remote stop` | Open / close the session | Not applicable — `remote start` fails |
| Default | — | Yes, for a target that never had a mode stored |

Choose the mode:

1. **Live Authoring** when the workflow is designed on the remote machine — UI elements must be captured, inspected, or exercised there, or the design work should not occupy the user's machine. It covers everything Remote Run Only does: debug/run with `--remote` executes on the remote machine over the session.
2. **Remote Run Only** when the workflow is designed locally and only debug/run must happen on the robot.
3. **Never downgrade Live Authoring to Remote Run Only to debug/run.** When the stored mode is Live Authoring, keep it — debug/run within it.

The two flags are mutually exclusive. Passing neither keeps the stored mode. Switching from Live Authoring to Remote Run Only releases the session.

## Critical Rules

1. **Run `uip rpa remote status` first, at the start of every task.** It is read-only. If the stored target already matches the intended folder/machine/robot/runtime and mode (a Live Authoring target also matches a debug/run-only task), do NOT reconfigure — in Live Authoring run `uip rpa remote start`; in Remote Run Only proceed directly to debug/run. Configure only when no target is stored or it differs (§ Session Lifecycle).
2. **IMPORTANT — always pass `--robot` on `configure`.** The CLI lists it as optional (falls back to the machine's default identity), but the remote connection does not work without it. In Live Authoring, `configure` itself fails with `Could not start remote debug session. Foreground process requires you to have an unattended robot with credentials defined`; in Remote Run Only, `configure` succeeds and every later operation fails with that error. Either way the broken target (`robot: null`) is stored — reconfigure with `--robot`.
3. **Ask the user which target to use.** Unless the user already named the folder/machine/robot/runtime, look up the candidates from Orchestrator with the uip CLI and ask which to use — never silently pick one (§ Discovering Option Values).
4. **Pass the mode flag explicitly on every `configure`.** Pick `--live-authoring` or `--remote-run-only` from § Remote Session Modes; do not rely on whatever mode is stored. Live Authoring is a superset of Remote Run Only — when the target is in Live Authoring, debug/run there and never reconfigure it to `--remote-run-only`.
5. **Always run `uip rpa remote stop` when Live Authoring work is finished** — also when abandoning the task or after an unrecoverable error. The session job holds an unattended runtime on the robot; on a machine with a single unattended runtime it blocks every other job until it is stopped. `stop` MUST be the last remote command.
6. **Orchestrator sign-in required.** On `not authenticated` / `401` / `403`, sign in with the uip CLI per [cli-reference.md § Authentication](cli-reference.md#authentication), then retry.
7. **The remote filesystem is not directly accessible — transfer first.** To read a remote file, `download-file` it and read the local copy. To use a local file on the remote machine, `upload-file` it first and reference the remote path. Always use absolute remote paths.
8. **`exec` verdict = the trailing JSON envelope.** The command's stdout and stderr stream to local stdout ahead of the envelope; read the command output from the streamed lines and the verdict from `Result` / `Message` only (§ Execute a Shell Command on the Remote).
9. **Use `--output json`** on every command whose output is parsed, and **pass `--project-dir "<PROJECT_DIR>"` on every `uip rpa remote` command.** The target is stored per project; without the flag the current directory is used, and outside a project folder every command fails with `Not a UiPath project at '<DIR>': project.json is missing.`
10. **Run/debug verdict = outer `Result` / inner `HasErrors`** — same as local runs, never log-entry levels (SKILL.md Common Rule 8a).

## Session Lifecycle

1. **Check** the stored target (Rule 1):

   ```bash
   uip rpa remote status --project-dir "<PROJECT_DIR>" --output json
   ```

2. **Already configured and matching** — `target` is `UnattendedRobot`; folder/machine/robot/runtime and `liveAuthoring` match the intent; `liveAuthoring: true` matches a debug/run-only task too (§ Reading `remote status`):
   - Live Authoring → open the session (no-op when it is already open):

     ```bash
     uip rpa remote start --project-dir "<PROJECT_DIR>" --output json
     ```

   - Remote Run Only → nothing to start; proceed to § Debug / Run a Workflow on the Remote.
3. **Not configured, or different** → `remote configure` (§ Configure a Remote Target). In Live Authoring, `configure` also opens the session — no separate `start` needed.
4. **Work** — debug/run with `--remote`; in Live Authoring also `exec`, `upload-file`, `download-file`, and remote UI Automation.
5. **Finish (Live Authoring)** — close the session (Rule 5):

   ```bash
   uip rpa remote stop --project-dir "<PROJECT_DIR>" --output json
   ```

   The target stays stored. Next task: step 2 applies — `remote start` reopens the session without reconfiguring.

| Command | Behavior |
|---|---|
| `configure` | Resolves and stores the target and mode, then connects. In Live Authoring it blocks until the session job is running — tens of seconds; do not wrap it in a short timeout. Reconfiguring replaces the stored target. A `configure` that fails to resolve a name (folder, machine, robot, runtime) keeps the previous target and leaves a running session untouched; one that fails while connecting (e.g. missing `--robot`) stores the new target |
| `start` | Opens the Live Authoring session → `"Remote session ready."`. No-op when the session is already open. Does not start the UI Automation design host — the first remote UI Automation command sets it up. Fails with no target (`Remote debugging is not configured for an unattended robot…`) or in Remote Run Only (`The remote connection is in Remote Run Only mode, which has no remote UI Automation session…`) |
| `stop` | Closes the session and releases the robot, including the UI Automation design host → `"Remote session stopped."`. Always succeeds — also when no session is running or no target is configured |
| `status` | Read-only — changes nothing, starts nothing |

## Reading `remote status`

```json
{
  "Result": "Success",
  "Code": "ToolResult",
  "Data": {
    "success": true,
    "target": "UnattendedRobot",
    "remoteSessionEnabled": true,
    "liveAuthoring": true,
    "folder": "<FOLDER_PATH>",
    "robot": "<RESOLVED_ROBOT_NAME>",
    "machine": "<MACHINE_NAME>",
    "runtime": "<RESOLVED_RUNTIME_LABEL>"
  }
}
```

| Field | Meaning |
|---|---|
| `target` | `UnattendedRobot` — a remote target is in effect. `LocalMachine` — no target (not configured, or the backend restarted); the other fields are then absent |
| `remoteSessionEnabled` | `true` after `configure` / `start`; `false` after `stop` |
| `liveAuthoring` | `true` — Live Authoring; `false` — Remote Run Only |
| `folder`, `machine` | Resolved folder path and machine name |
| `robot` | Resolved robot name — may differ from the account name passed to `--robot`. `null` means `--robot` was omitted: reconfigure with it (Rule 2) |
| `runtime` | Pinned host as `<HOST> - <HOST>\<ACCOUNT>`; `null` when `--runtime` was omitted and Orchestrator picks the connected session |

## Configure a Remote Target

```bash
uip rpa remote configure \
  --folder-path "<FOLDER_PATH>" \
  --machine "<MACHINE_NAME>" \
  --robot "<ROBOT_NAME>" \
  --live-authoring \
  --project-dir "<PROJECT_DIR>" --output json
```

Pinned to one host of a machine template (§ When to Pass `--runtime`):

```bash
uip rpa remote configure \
  --folder-path "<FOLDER_PATH>" \
  --machine "<MACHINE_NAME>" \
  --robot "<ROBOT_NAME>" \
  --runtime "<RUNTIME_NAME>" \
  --live-authoring \
  --project-dir "<PROJECT_DIR>" --output json
```

| Flag | Required | Value |
|------|----------|-------|
| `--machine` | Yes | Orchestrator machine name to run the unattended robot on |
| `--robot` | **Yes** | Robot/user account name to run as; resolved to the robot in the folder. Listed as optional, but operations fail without it (Rule 2) |
| `--folder-path` | No | Fully-qualified Orchestrator folder path the machine/robot belong to (e.g. `Shared/Finance`). Defaults to the backend's current folder — pass it whenever the user named a folder |
| `--runtime` | No | Connected host of the machine to pin the session to: the host machine name (case-insensitive) or the full `<HOST> - <HOST>\<ACCOUNT>` label. Ignored for serverless machines. Omitted → Orchestrator picks the connected session |
| `--live-authoring` / `--remote-run-only` | One of them (Rule 4) | Session mode — § Remote Session Modes |

### When to Pass `--runtime`

1. **Pass it when the machine has more than one connected host and the work depends on a specific one** — typically Live Authoring where the target application is installed on only one host, or when the user names a host. Without it, Orchestrator may open the session on another host.
2. **Omit it when the machine has a single connected host** — Orchestrator picks that one.
3. **Never guess the host name.** Look up the connected hosts per § Discovering Option Values. A wrong name fails with an error that lists the machine's connected runtimes — offer those to the user (Rule 3).

### Discovering Option Values

Look up each value from Orchestrator with the uip CLI: the folder's fully-qualified path, the machines assigned to that folder, the robot accounts in that folder, and each machine's connected unattended sessions (their host machine names are the `--runtime` values). Prefer a machine whose host is connected and responsive — `configure` rejects a machine with no connected host. Then apply Rule 3: present the candidates and ask the user which to use.

### Configure Errors

| Message | Fix |
|---|---|
| `Folder '<FOLDER_PATH>' not found. Available folders: …` | Pick from the listed folders |
| `Machine '<MACHINE_NAME>' not found in folder '<FOLDER_PATH>'. Available machines: …` | Pick from the listed machines, or correct `--folder-path` |
| `Machine '<MACHINE_NAME>' has no available unattended session in folder '<FOLDER_PATH>' - last reported state: …` | No host of that machine is connected. Ask the user to start the machine and connect its robot service to Orchestrator, or pick another machine |
| `Robot/user '<ROBOT_NAME>' not found in folder '<FOLDER_PATH>'.` | Re-check the robot accounts in that folder |
| `Connected runtime '<RUNTIME_NAME>' not found for machine '<MACHINE_NAME>'. Available runtimes: …` | Pick from the listed runtimes. An empty list means no host of that machine is connected — handle as the "no available unattended session" row |
| `--live-authoring and --remote-run-only are the two modes of one connection; pass at most one.` | Pass exactly one mode flag |
| `Could not start remote debug session. Foreground process requires you to have an unattended robot with credentials defined` — from `configure` in Live Authoring, or from later operations in Remote Run Only | `--robot` was omitted — reconfigure with it (Rule 2) |
| Later operations fail: `Remote debugging is not configured for an unattended robot…` | No target is stored — run `configure` |
| Any `remote` command: `…HelmProjectLoadException: "Not a UiPath project at '<DIR>': project.json is missing…"` | `--project-dir` is missing or wrong — pass the folder containing `project.json` (Rule 9) |

### Validate After Configuring

1. Check `remote status` (§ Reading `remote status`): `target` is `UnattendedRobot`, `liveAuthoring` matches the chosen mode, and folder/machine/robot/runtime match what was requested.
2. **Live Authoring** — smoke-test end to end and confirm the host:

   ```bash
   uip rpa remote exec --command "hostname" --timeout 60 --project-dir "<PROJECT_DIR>" --output json
   ```

   `Result: Success` proves the session executes commands; the streamed host name must match the pinned `--runtime` when one was set. The call returns in a few seconds when the session is open; 20+ seconds means the command had to start a new session job.
3. **Remote Run Only** — the first `--remote` run (§ Debug / Run a Workflow on the Remote) is the end-to-end check.

## Debug / Run a Workflow on the Remote

Add `--remote` to `run` or `debug start` — the workflow executes on the configured unattended robot instead of locally:

```bash
uip rpa run --file-path "<WORKFLOW_FILE>" --remote --project-dir "<PROJECT_DIR>" --output json

uip rpa debug start --file-path "<WORKFLOW_FILE>" --remote \
  --breakpoints 'workflowFile=Main.xaml,activityIdRef=Assign_1' \
  --project-dir "<PROJECT_DIR>" --output json
```

`--remote` affects **start commands only** (`run`, `debug start`, plus the Studio Desktop verbs `debug start-from-here` / `debug test-activity`). Mid-session verbs (`debug step-over`, `debug continue`, `debug state`, `execution cancel`, …) operate on the active session and take no `--remote`:

```bash
uip rpa debug continue --output json
uip rpa execution cancel --output json
```

- **Live Authoring** — run/debug travel over the open session. After a `stop`, run `remote start` before the next `--remote` run.
- **Remote Run Only** — every `--remote` run or debug session is an Orchestrator job of its own; nothing to start or stop.
- The debug loop is unchanged from local debugging — breakpoints by `activityIdRef`, `DebugState` branching (`Paused` / `Suspended` / `Completed` / `Running`), locals in `DebugDetails`. Full loop: [debugging.md](debugging.md).
- Works with both Studio and Helm backends.
- `--profiling-mode stream` is ignored when running remote; end-of-run profiling delivery still applies.
- To read files the run produced on the robot (logs, screenshots, reports), download them (§ Transfer Files).

## Execute a Shell Command on the Remote

Use in Live Authoring with the session open. Runs through the remote OS shell — `cmd.exe /c` on Windows, `/bin/sh -c` otherwise — as the robot's account, so profile paths resolve to that account's profile.

```bash
uip rpa remote exec --command "<COMMAND_LINE>" --timeout <SECONDS> \
  --project-dir "<PROJECT_DIR>" --output json
```

| Flag | Required | Value |
|------|----------|-------|
| `--command` | Yes | Shell command line to run (e.g. `dir` on Windows, `ls -la` on Linux). With a restored package, may be a path relative to the package folder (e.g. `tools\\app.exe --flag`) |
| `--package-id` | No | NuGet package id to restore on the remote machine before running the command. Requires `--package-version` |
| `--package-version` | No | Version of `--package-id` to restore. Required when `--package-id` is set |
| `--working-directory` | No | Working directory for the command. Defaults to the restored package folder when a package is restored, otherwise the Robot installation directory on the remote machine |
| `--timeout` | No | Seconds after which the remote command is killed. Omit for no timeout — set one for any command that could hang |

Reading the result (Rule 8):

- The command's stdout and stderr stream to local stdout **before** the JSON envelope; the envelope's `Data.output` is empty. Take the command output from the streamed lines and parse only the trailing envelope — never feed the whole stdout to a JSON parser.
- stdout and stderr arrive merged, and their relative order is not preserved — do not rely on line order across the two streams.
- Exit code 0 → `Result: Success`, `hasErrors: false`.
- Non-zero exit → `Result: Failure`, `Message` contains `Command exited with code <N>.`, and the CLI process exits 1.
- Timeout → `Result: Failure`, `Message` contains `Command timed out.`

On a Windows robot use `cmd.exe` syntax (`&&`, `type`, `dir`, `rmdir /s /q`); run PowerShell as `powershell -NoProfile -Command "<SCRIPT>"`.

Examples:

```bash
# Inspect the remote environment (Windows robot)
uip rpa remote exec --command "hostname && whoami" --timeout 60 \
  --project-dir "<PROJECT_DIR>" --output json

# Check a directory the workflow writes to
uip rpa remote exec --command "dir C:\\Output" --timeout 30 \
  --project-dir "<PROJECT_DIR>" --output json

# Run a PowerShell snippet
uip rpa remote exec --command "powershell -NoProfile -Command \"Get-ChildItem C:\\Output\"" --timeout 60 \
  --project-dir "<PROJECT_DIR>" --output json

# Restore a published package and run a tool from its folder
uip rpa remote exec \
  --command "tools\\app.exe --flag" \
  --package-id "<PACKAGE_ID>" --package-version "<PACKAGE_VERSION>" \
  --timeout 300 --project-dir "<PROJECT_DIR>" --output json
```

## Transfer Files

Use in Live Authoring with the session open. Files travel through a temporary Orchestrator bucket that is deleted afterwards.

Download a remote file — logs, screenshots, generated reports, exported data — and read the local copy (Rule 7):

```bash
uip rpa remote download-file \
  --remote-path "<REMOTE_FILE_PATH>" \
  --local-path "<LOCAL_DESTINATION_PATH>" \
  --project-dir "<PROJECT_DIR>" --output json
```

Upload a local file — test data, config files, documents the workflow processes — then reference the remote path in the workflow or an `exec` command:

```bash
uip rpa remote upload-file \
  --local-path "<LOCAL_FILE_PATH>" \
  --remote-path "<REMOTE_DESTINATION_PATH>" \
  --project-dir "<PROJECT_DIR>" --output json
```

- `--remote-path` MUST be absolute (e.g. `C:\\Temp\\input.xlsx`). A relative path resolves against the Robot installation directory on the remote machine — files written there clutter the robot's install.
- Parent directories are created on the destination side, in both directions.
- Both directions overwrite an existing destination file without warning — `upload-file` on the remote machine, `download-file` locally.
- A missing remote file fails with `File not found on the remote machine: <REMOTE_FILE_PATH>`; a missing local file fails with `Could not find file '<LOCAL_FILE_PATH>'.`
- Robots are often shared. Before `remote stop`, delete the temporary files and folders the task uploaded or created, with `exec` (e.g. `rmdir /s /q "<REMOTE_DIR>"` on Windows).

## Anti-patterns

- **Reconfiguring a target that `remote status` already shows** — in Live Authoring run `remote start` instead (Rule 1).
- **Leaving a Live Authoring session running after the work is done** — it holds a robot runtime; always `remote stop` (Rule 5).
- **Running `exec` or a file transfer after `remote stop` and leaving** — the command reopens the session, which then holds the robot again; `stop` must be the last remote command (Rule 5).
- **Running `remote start` in Remote Run Only** — there is no session to start; it fails. Switch to Live Authoring when a persistent session, shell/file commands, or remote UI Automation are needed.
- **Choosing Remote Run Only for design work on the remote machine** — it has no remote UI Automation session.
- **Switching a Live Authoring target to Remote Run Only to debug/run** — Live Authoring already debugs/runs on the remote machine; switching releases the session and loses remote UI Automation, shell, and file commands (Rule 4).
- **Omitting `--robot` on `configure`** — `configure` fails in Live Authoring, or succeeds in Remote Run Only and every later operation fails; the broken target is stored either way (Rule 2).
- **Guessing folder/machine/robot/runtime names** — look them up from Orchestrator and ask the user (Rule 3).
- **Configuring a machine whose host is not connected** — `configure` rejects it; pick a machine with a connected, responsive host.
- **Omitting `--runtime` on a multi-host machine when the application exists on only one host** — the session may open on a host without it (§ When to Pass `--runtime`).
- **Setting `--runtime` for a serverless machine** — the flag is ignored there; it only pins a session on a classic machine.
- **Wrapping `configure --live-authoring` in a short timeout** — it blocks until the session job runs, tens of seconds.
- **Passing `--remote` to mid-session debug verbs** — only start commands take it.
- **Parsing all of `exec` stdout as JSON** — streamed command output precedes the envelope (Rule 8).
- **Relative `--remote-path`** — the file lands in the robot's installation directory; use absolute paths.
- **Passing `--package-id` without `--package-version`** — the version is required whenever a package is restored.
- **Omitting `--timeout` on an `exec` command that can hang** — without it the command runs unbounded on the remote machine.
