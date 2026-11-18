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
| Remote UI Automation (the `uip rpa uia` group in remote mode — syntax in the UIA docs), remote screen streaming | Available | Not available |
| `remote start` / `remote stop` | Open / close the session | Not applicable — `remote start` fails |
| Default | — | Yes, for a target that never had a mode stored |

Choose the mode:

1. **Live Authoring** when the workflow is designed on the remote machine — the target application exists only there, or the design work should not occupy the user's machine. It covers everything Remote Run Only does: debug/run with `--remote` executes on the remote machine over the session.
2. **Remote Run Only** when the workflow is designed locally and only debug/run must happen on the robot.
3. **Never downgrade Live Authoring to Remote Run Only to debug/run.** When the stored mode is Live Authoring, keep it — debug/run within it.

The two flags are mutually exclusive. Passing neither keeps the stored mode. Switching from Live Authoring to Remote Run Only releases the session.

### Live Authoring Known Limitations

1. Live Authoring is unavailable on Serverless robots.
2. Live Authoring is unavailable on attended-only robots.
3. Live Authoring is unavailable on robots that can run only background jobs.

For a Serverless robot, tell the user Live Authoring is not supported on it and ask for a different target (Rule 3). A background-only robot becomes a target once prepared — ask the user whether to prepare it (Rule 11). A Robot signed in with interactive sign-in without unattended credentials becomes a target only when the user asks to convert that user account (§ Interactive Sign-In Robot with a User Account (On Request Only)); one that already has them (`hasCredentials: true`) is a target as is, while that account is signed in on the machine (§ Interactive Sign-In Robot with a User Account (On Request Only) item 5).

## Critical Rules

1. **Run `uip rpa remote status` first, at the start of every task.** It is read-only. If the stored target already matches the intended folder/machine/robot/runtime and mode (a Live Authoring target also matches a debug/run-only task), do NOT reconfigure — in Live Authoring with `remoteSessionEnabled: true` the session is already open: proceed directly to the work, no `remote start`; in Live Authoring with `remoteSessionEnabled: false` run `uip rpa remote start`; in Remote Run Only proceed directly to debug/run. Configure only when no target is stored or it differs (§ Session Lifecycle).
2. **IMPORTANT — always pass `--robot` on `configure`.** The CLI lists it as optional (falls back to the machine's default identity), but the remote connection does not work without it. In Live Authoring, `configure` itself fails with `Could not start remote debug session. Foreground process requires you to have an unattended robot with credentials defined`; in Remote Run Only, `configure` succeeds and every later operation fails with that error. Either way the broken target (`robot: null`) is stored — reconfigure with `--robot`.
3. **Ask the user which target to use.** Unless the user already named the folder/machine/robot/runtime, look up the candidates from Orchestrator with the uip CLI and ask which to use — never silently pick one (§ Discovering Option Values).
4. **Pass the mode flag explicitly on every `configure`.** Pick `--live-authoring` or `--remote-run-only` from § Remote Session Modes; do not rely on whatever mode is stored. Live Authoring is a superset of Remote Run Only — when the target is in Live Authoring, debug/run there and never reconfigure it to `--remote-run-only`.
5. **Always run `uip rpa remote stop` when Live Authoring work is finished** — also when abandoning the task or after an unrecoverable error. The session job holds an unattended runtime on the robot; on a machine with a single unattended runtime it blocks every other job until it is stopped. `stop` MUST be the last remote command.
6. **Orchestrator sign-in required.** On `not authenticated` / `401` / `403`, sign in with the uip CLI per [cli-reference.md § Authentication](cli-reference.md#authentication), then retry.
7. **The remote filesystem is not directly accessible — transfer first.** To read a remote file, `download-file` it and read the local copy. To use a local file on the remote machine, `upload-file` it first and reference the remote path. Always use absolute remote paths.
8. **`exec` verdict = the trailing JSON envelope.** The command's stdout and stderr stream to local stdout ahead of the envelope; read the command output from the streamed lines and the verdict from `Result` / `Message` only (§ Execute a Shell Command on the Remote).
9. **Use `--output json`** on every command whose output is parsed, and **pass `--project-dir "<PROJECT_DIR>"` on every `uip rpa remote` command.** The target is stored per project; without the flag the current directory is used, and outside a project folder every command fails with `Not a UiPath project at '<DIR>': project.json is missing.`
10. **Run/debug verdict = outer `Result` / inner `HasErrors`** — same as local runs, never log-entry levels (SKILL.md Common Rule 8a).
11. **No usable target → ask the user whether to prepare one in Orchestrator. Never prepare one unasked.** **Offer an Unattended Robot with a robot account — the preferred approach.** Use a user account (Interactive Sign-In Robot) only on the user's request. User agrees → § Prepare a Remote Target in Orchestrator. User declines → ask for another folder or target, or stop.

## Session Lifecycle

1. **Check** the stored target (Rule 1):

   ```bash
   uip rpa remote status --project-dir "<PROJECT_DIR>" --output json
   ```

2. **Already configured and matching** — `target` is `UnattendedRobot`; folder/machine/robot/runtime and `liveAuthoring` match the intent; `liveAuthoring: true` matches a debug/run-only task too (§ Reading `remote status`):
   - Live Authoring, `remoteSessionEnabled: true` → the session is already open; trust `status` and proceed to step 4 — do NOT run `remote start`. If a later remote command reports that no session is open, run `remote start` then and retry the command.
   - Live Authoring, `remoteSessionEnabled: false` → open the session:

     ```bash
     uip rpa remote start --project-dir "<PROJECT_DIR>" --output json
     ```

   - Remote Run Only → nothing to start; proceed to § Debug / Run a Workflow on the Remote.
3. **Not configured, or different** → `remote configure` (§ Configure a Remote Target). In Live Authoring, `configure` also opens the session — no separate `start` needed. No usable robot or host in the folder → ask the user whether to prepare a target (Rule 11).
4. **Work** — debug/run with `--remote`; in Live Authoring also `exec`, `upload-file`, `download-file`, and remote UI Automation.
5. **Finish (Live Authoring)** — close the session (Rule 5):

   ```bash
   uip rpa remote stop --project-dir "<PROJECT_DIR>" --output json
   ```

   The target stays stored. Next task: step 2 applies — `status` shows `remoteSessionEnabled: false`, so `remote start` reopens the session without reconfiguring.

| Command | Behavior |
|---|---|
| `configure` | Resolves and stores the target and mode, then connects. In Live Authoring it blocks until the session job is running — tens of seconds; do not wrap it in a short timeout. Reconfiguring replaces the stored target. A `configure` that fails to resolve a name (folder, machine, robot, runtime) keeps the previous target and leaves a running session untouched; one that fails while connecting (e.g. missing `--robot`) stores the new target |
| `start` | Opens the Live Authoring session → `"Remote session ready."`. No-op when the session is already open. Fails with no target (`Remote debugging is not configured for an unattended robot…`) or in Remote Run Only (`The remote connection is in Remote Run Only mode…`) |
| `stop` | Closes the session and releases the robot → `"Remote session stopped."`. Always succeeds — also when no session is running or no target is configured |
| `status` | Read-only — changes nothing, starts nothing |

## Reading `remote status`

```json
{
  "Result": "Success",
  "Code": "RemoteStatus",
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
| `remoteSessionEnabled` | `true` after `configure` / `start` — the session is open, skip `remote start`; `false` after `stop` — run `remote start` before remote work |
| `liveAuthoring` | `true` — Live Authoring; `false` — Remote Run Only |
| `folder`, `machine` | Resolved folder path and machine name |
| `robot` | Resolved robot name — may differ from the account name passed to `--robot`. `null` means `--robot` was omitted: reconfigure with it (Rule 2) |
| `runtime` | Pinned host as `<HOST> - <HOST>\<ACCOUNT>`; `null` when `--runtime` was omitted and Orchestrator picks the connected session |

## Prepare a Remote Target in Orchestrator

Prepare a target only when the user asks for it or agrees when asked (Rule 11). Ask when § Discovering Option Values finds no usable robot or host, or when the intended robot shows `hasCredentials: false`. Pick the scenario:

| Scenario | Robot identity | Machine | Use | Checklist |
|---|---|---|---|---|
| Unattended Robot with a robot account (**preferred**) | Robot account; Robot connected as unattended (machine key or client credentials) | Dedicated VM or server | Default — the one to offer | § Unattended Robot with a Robot Account (Recommended) |
| Interactive Sign-In Robot with a user account (on request only) | User account — the user's own or any other user account; Robot signed in with interactive sign-in | The machine where that account signs in to the Robot | Only when the user asks to convert a user account to unattended | § Interactive Sign-In Robot with a User Account (On Request Only) |

### Rules for Preparing a Target

1. **Run every Orchestrator check and change through the `uipath-platform` skill** — it owns the commands for folders, users, robots, machines, and licenses. Skill unavailable → walk the user through the same changes in the Orchestrator web UI.
2. **Check each item before changing it.** Change only items that fail.
3. **Confirm each change with the user before making it** — every change alters shared tenant configuration. No free unattended license in the tenant → stop and tell the user; never take a license from another machine.
4. **Never ask the user for a password.** Unattended Robot → the user or an administrator enters the Windows credentials in the Orchestrator web UI. Interactive Sign-In Robot → password is the fixed value `password`; username per OS (§ Interactive Sign-In Robot with a User Account (On Request Only) item 4).
5. **Shared folder only (e.g. `Shared`)** — never prepare a target only in a Personal Workspace.
6. **Robot 26.10.0 or later** — the floor for every remote target (§ Discovering Option Values, step 3). Older → ask the user to upgrade the Robot; stop until done.
7. **Steps on the machine belong to the user** — installing or upgrading the Robot, connecting it to Orchestrator, signing in. Tell the user what to do and wait for confirmation.

### Unattended Robot with a Robot Account (Recommended)

1. **Robot account assigned directly to the shared folder**, with a role that can run jobs. No robot account → ask the user whether to create one; robot accounts are created in Identity (the `uipath-admin` skill), then assigned to the folder (`uipath-platform`).
2. **Foreground automation enabled** — the robot's unattended setup holds the real Windows credentials of the account it runs as, so the Robot can start a Windows session or join an existing one; the remote session runs in it. Without them the robot is background-only: `hasCredentials: false` in `remote targets`, and the session fails with `Foreground process requires you to have an unattended robot with credentials defined`. Credentials come from the user or an administrator (item 4 of § Rules for Preparing a Target).
3. **Machine in the same folder with an unattended license** — the machine or machine template is assigned to the folder and has at least one unattended runtime.
4. **Robot 26.10.0+ connected as unattended** — its host shows `Available` in `remote targets`.

### Interactive Sign-In Robot with a User Account (On Request Only)

Only when the user asks to convert a user account to unattended — the user's own account or any other user account in the tenant; never propose or start it otherwise. Orchestrator registers a machine whose Robot is signed in with a user account in that account's Personal Workspace.

Before the first change:

- **Another user's account** → the signed-in user must be an Orchestrator administrator — check through the `uipath-platform` skill. Not an administrator → stop and tell the user an Orchestrator administrator has to make the changes.
- **Any account** → tell the user that once prepared, the machine accepts the folder's unattended jobs and remote shell commands run as that account on it (§ Execute a Shell Command on the Remote), until its unattended license and folder assignment are removed.

1. **Machine assigned to the shared folder** — assign that account's Personal Workspace machine to the shared folder too; it stays in the Personal Workspace.
2. **User account assigned directly to that folder** with a role that can run jobs (e.g. Automation User). Access through a group is not enough — the robot appears in `remote targets` only after a direct assignment.
3. **Unattended license allocated to the machine** — at least one unattended runtime. While the Robot is online, Orchestrator licenses the machine right away.
4. **The account's `Enterprise robot setup` = `Custom Windows Credentials`**, password `password` — a fixed value: the Robot joins the account's existing session (item 5) and does not use the password. Never ask the user or the account owner for the real password. Username by the machine's OS:
   - **macOS** → `.\user`, every time.
   - **Windows** → the Windows account that account is signed in to Windows with, as `DOMAIN\user`: the output of `whoami` in a terminal on that machine while that account is signed in to Windows. Agent runs on that machine under that account → run `whoami` itself; otherwise ask the user (or the account owner) to run it and share the output.
   - **OS unknown** → ask the user.

   Orchestrator rejects `.` as the username.
5. **Robot 26.10.0+ signed in with that account, and that account signed in on the machine** — on Windows, signed in to Windows. The Robot does not start a session for this account; it joins the open one, so the account stays signed in for as long as remote work runs. Signed out → ask the user (or the account owner) to sign in on the machine before any remote session starts. Another user's account → its owner signs in on their machine (item 7 of § Rules for Preparing a Target). Its host shows `Available` in `remote targets`.

### Verify the Prepared Target

1. Re-run `remote targets` for the folder (§ Discovering Option Values, step 2): the robot shows `enabled: true` and `hasCredentials: true`; the machine has an `Available` host.
2. Item still failing → re-check it against its checklist. Same item failing after two re-checks → stop and report what is missing.
3. Continue with § Configure a Remote Target and § Validate After Configuring.

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

Look up each value the user has not named with these read-only commands, in order. Skip step 1 when the user already named the folder.

1. **Folder** — the `--folder-path` value is `Path` (fully qualified, e.g. `Shared/Finance`), not `Name`:

   ```bash
   uip or folders list --output json
   ```

   Lists the folders the signed-in user can access; add `--all` to list every folder in the tenant.

2. **Remote targets in the folder** — robots, machines, and hosts in one call:

   ```bash
   uip rpa remote targets --folder-path "<FOLDER_PATH>" --project-dir "<PROJECT_DIR>" --output json
   ```

   Example output (trimmed):

   ```json
   {
     "success": true,
     "folder": "Shared",
     "robots": [
       { "name": "<ROBOT_NAME>", "enabled": true, "hasCredentials": true }
     ],
     "targets": [
       { "machine": "<MACHINE_NAME>", "host": "<RUNTIME_NAME>", "status": "Available" },
       { "machine": "<MACHINE_NAME>", "host": "<RUNTIME_NAME>", "status": "Disconnected" }
     ]
   }
   ```

   | Field | Use |
   |---|---|
   | `robots[].name` | `--robot` value. Offer only robots with `enabled: true` and `hasCredentials: true` — a disabled or credential-less robot passes `configure` and fails at session start. `hasCredentials: false` = background-only robot: ask the user whether to fix it (Rule 11) |
   | `targets[].machine` | `--machine` value. One row per host, so a machine with several hosts appears in several rows |
   | `targets[].host` | `--runtime` value, passed as-is |
   | `targets[].status` | `Available` — usable host; `configure` takes only an `Available` host as `--runtime`. `Serverless` — serverless machine: Remote Run Only (§ Live Authoring Known Limitations), `--runtime` does not apply. `Busy`, `Disconnected`, `Unresponsive`, `NoSession`, `Unknown` — not usable now; `Disconnected` means that host's robot service is not connected to Orchestrator |

   The number of `Available` hosts per machine decides whether to pass `--runtime` (§ When to Pass `--runtime`).

   When the user already named the robot or machine, narrow the listing: `--robot "<ROBOT_NAME>"` lists only the machines that robot can use and the hosts that serve it — the same check `configure --robot` runs; `--machine "<MACHINE_NAME>"` lists only that machine's hosts.

3. **Robot version of each candidate host** — every remote target, in both modes, needs Robot 26.10.0 or later on the host, also when the user named the target. `remote targets` does not report the version: read it from the host's session in Orchestrator through the `uipath-platform` skill, or ask the user to check it in the Orchestrator web UI when that skill is unavailable. Older → the host is not usable: ask the user to upgrade the Robot on it, or pick another host.

Then apply Rule 3: present the candidates and ask the user which to use. Offer only machines with at least one `Available` host on Robot 26.10.0 or later (step 3) — `configure` rejects a machine with no connected host; for Remote Run Only, `Serverless` machines are usable too. Empty `robots`, or no usable row in `targets`, means the folder has no usable robot or host; ask the user whether to prepare a target in that folder or use another folder (Rule 11). On `not authenticated` / `401` / `403`, sign in per Rule 6 and retry.

### Configure Errors

| Message | Fix |
|---|---|
| `Folder '<FOLDER_PATH>' not found. Available folders: …` | Pick from the listed folders |
| `Machine '<MACHINE_NAME>' not found in folder '<FOLDER_PATH>'. Available machines: …` | Pick from the listed machines, or correct `--folder-path` |
| `Machine '<MACHINE_NAME>' has no available unattended session in folder '<FOLDER_PATH>' - last reported state: …` | No host of that machine is connected. Ask the user to start the machine and connect its robot service to Orchestrator, or pick another machine |
| `Robot/user '<ROBOT_NAME>' not found in folder '<FOLDER_PATH>'.` | Re-list the robots in that folder (§ Discovering Option Values, step 2) |
| `Connected runtime '<RUNTIME_NAME>' not found for machine '<MACHINE_NAME>'. Available runtimes: …` | Pick from the listed runtimes. An empty list means no host of that machine is connected — handle as the "no available unattended session" row |
| `--live-authoring and --remote-run-only are the two modes of one connection; pass at most one.` | Pass exactly one mode flag |
| `Could not start remote debug session. Foreground process requires you to have an unattended robot with credentials defined` — from `configure` in Live Authoring, or from later operations in Remote Run Only | `--robot` omitted → reconfigure with it (Rule 2). `--robot` passed → the robot has no credentials (background-only): ask the user whether to fix it (Rule 11) — § Unattended Robot with a Robot Account (Recommended) item 2; for a user account the user asked to convert, § Interactive Sign-In Robot with a User Account (On Request Only) item 4 |
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
- A non-zero exit can still come with complete output: `query user` prints its table and exits 1, and PowerShell `-Command` exits 1 when its last pipeline hit an error, even one hidden by `-ErrorAction SilentlyContinue`. Read the streamed lines before deciding the command failed.
- Timeout → `Result: Failure`, `Message` contains `Command timed out.`

On a Windows robot use `cmd.exe` syntax (`&&`, `type`, `dir`, `rmdir /s /q`). The `--command` text passes through two shells before it runs — your local console (Bash, PowerShell or cmd), then `cmd.exe` on the robot — and each treats quotes and special characters differently. So that it works from any console:

- Put the whole value in double quotes and use only single quotes inside it. `\"` works in Bash and cmd but breaks the command in PowerShell.
- Single quotes quote only in PowerShell (write a literal `'` as `''`). `cmd.exe` ignores them, so a path with spaces needs PowerShell.
- For a short PowerShell command with none of ``$ % " ` | & < > ^``, put the code after `-Command` without quotes and write paths with forward slashes (example below).
- For any other PowerShell script, write it to a local `.ps1` file with your file-writing tool, upload it with `upload-file` (§ Transfer Files) to an absolute remote path without spaces, and run `powershell -NoProfile -ExecutionPolicy Bypass -File <REMOTE_SCRIPT_PATH>`. Don't use `-EncodedCommand`: each console needs a different encoder, and error output comes back as `#< CLIXML` XML.

Examples:

```bash
# Inspect the remote environment (Windows robot)
uip rpa remote exec --command "hostname && whoami" --timeout 60 \
  --project-dir "<PROJECT_DIR>" --output json

# Check a directory the workflow writes to
uip rpa remote exec --command "dir C:\Output" --timeout 30 \
  --project-dir "<PROJECT_DIR>" --output json

# Run a PowerShell snippet
uip rpa remote exec --command "powershell -NoProfile -Command Get-ChildItem 'C:/Output'" --timeout 60 \
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

- **Reconfiguring a target that `remote status` already shows** — in Live Authoring run `remote start` instead when `remoteSessionEnabled` is `false`, or nothing when it is `true` (Rule 1).
- **Running `remote start` when `remote status` shows `remoteSessionEnabled: true`** — the session is already open; trust `status` and go straight to the work (Rule 1).
- **Leaving a Live Authoring session running after the work is done** — it holds a robot runtime; always `remote stop` (Rule 5).
- **Running `exec` or a file transfer after `remote stop` and leaving** — the command reopens the session, which then holds the robot again; `stop` must be the last remote command (Rule 5).
- **Running `remote start` in Remote Run Only** — there is no session to start; it fails. Switch to Live Authoring when a persistent session, shell/file commands, or remote UI Automation are needed.
- **Choosing Remote Run Only for design work on the remote machine** — it has no remote session.
- **Switching a Live Authoring target to Remote Run Only to debug/run** — Live Authoring already debugs/runs on the remote machine; switching releases the session and loses remote UI Automation, shell, and file commands (Rule 4).
- **Omitting `--robot` on `configure`** — `configure` fails in Live Authoring, or succeeds in Remote Run Only and every later operation fails; the broken target is stored either way (Rule 2).
- **Guessing folder/machine/robot/runtime names** — look them up from Orchestrator and ask the user (Rule 3).
- **Configuring a machine whose host is not connected** — `configure` rejects it; pick a machine with a connected, responsive host.
- **Preparing a target without asking the user** — when no usable target exists, ask whether to prepare one; never start on your own (Rule 11).
- **Converting a user account to unattended without the user's request, or another user's account without being an Orchestrator administrator** — recommend an Unattended Robot with a robot account (Rule 11); for another user's account, check the administrator role first (§ Interactive Sign-In Robot with a User Account (On Request Only)).
- **Preparing a target only in a Personal Workspace** — remote sessions need the robot and machine in a shared folder (§ Rules for Preparing a Target).
- **Relying on group access for an Interactive Sign-In Robot** — assign the user account directly to the folder; otherwise the robot does not appear in `remote targets`.
- **Configuring a robot with `hasCredentials: false`** — it runs only background processes and the session fails; ask the user whether to enable foreground automation first (Rule 11).
- **Asking for the real password for an Interactive Sign-In Robot, or guessing the username** — password is always `password`; username is `.\user` on macOS and the `whoami` output (`DOMAIN\user`) on Windows, never `.` (§ Interactive Sign-In Robot with a User Account (On Request Only) item 4).
- **Omitting `--runtime` on a multi-host machine when the application exists on only one host** — the session may open on a host without it (§ When to Pass `--runtime`).
- **Setting `--runtime` for a serverless machine** — the flag is ignored there; it only pins a session on a classic machine.
- **Wrapping `configure --live-authoring` in a short timeout** — it blocks until the session job runs, tens of seconds.
- **Passing `--remote` to mid-session debug verbs** — only start commands take it.
- **Parsing all of `exec` stdout as JSON** — streamed command output precedes the envelope (Rule 8).
- **Relative `--remote-path`** — the file lands in the robot's installation directory; use absolute paths.
- **Passing `--package-id` without `--package-version`** — the version is required whenever a package is restored.
- **Omitting `--timeout` on an `exec` command that can hang** — without it the command runs unbounded on the remote machine.
