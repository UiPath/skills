# Manage Sessions

Monitor robot sessions, runtime availability, debug mode, maintenance windows, and stale-session cleanup.

> For full option details, run `uip or sessions attended list --help` or the relevant command with `--help`.

## When to Use

- Check robot availability before starting jobs.
- Troubleshoot connected robots.
- Enable Studio remote debugging.
- Plan or execute maintenance windows.
- Clean up disconnected or stale sessions.

## Prerequisites

- Run `uip login status`. If not logged in, ask the user to run `uip login` (it opens an interactive browser flow).
- Set up folders and machines; see [setup-environment.md](setup-environment.md).

## Step 1: Check Folder Runtimes

Run:

```bash
uip or folders runtimes <folder-key> --output json
```

Review total slots, connected machines, and available idle slots by runtime type. If available slots are zero, jobs queue in Pending state until a slot frees up.

## Step 2: List Attended Sessions

Run:

```bash
uip or sessions attended list --output json
uip or sessions attended list --folder-path "Finance" --output json
uip or sessions attended list --state Available --output json
```

Attended sessions are human-interactive robots using UiPath Assistant. Valid states are `Available`, `Busy`, `Disconnected`, and `Unknown`.

## Step 3: List Unattended Sessions

Run:

```bash
uip or sessions unattended list --output json
uip or sessions unattended list \
  --folder-path "Production" \
  --runtime-type Unattended \
  --output json
```

Unattended sessions are autonomous execution robots.

## Step 4: List Machine Sessions

Run:

```bash
uip or sessions machines list <machine-key> --output json
uip or sessions machines list <machine-key> \
  --folder-path "Production" --output json
```

## Step 5: List Active Usernames

Run:

```bash
uip or sessions list-usernames --output json
```

## Step 6: List User Executors

Run:

```bash
uip or sessions list-user-executors --output json
```

## Step 7: Toggle Debug Mode

Run:

```bash
uip or sessions toggle-debug-mode <session-id> \
  --enabled true --minutes 30 --output json
uip or sessions toggle-debug-mode <session-id> \
  --enabled false --output json
```

Enabling debug mode lets Studio attach for live step-through debugging. It expires after `--minutes`; debug mode is not persistent, so re-enable it before expiry if needed.

## Step 8: Set Maintenance Mode

Run one of:

```bash
uip or sessions set-maintenance-mode <session-id> \
  --maintenance-mode Enabled --output json

uip or sessions set-maintenance-mode <session-id> \
  --maintenance-mode Enabled \
  --stop-jobs-strategy SoftStop --output json

uip or sessions set-maintenance-mode <session-id> \
  --maintenance-mode Enabled \
  --stop-jobs-strategy Kill --output json

uip or sessions set-maintenance-mode <session-id> \
  --maintenance-mode Disabled --output json
```

Maintenance mode prevents new jobs from being assigned. Existing jobs continue unless a stop strategy is specified:

| Strategy | Behavior |
|---|---|
| (none) | Running jobs continue; no new jobs are assigned. |
| `SoftStop` | Running jobs receive a graceful stop signal. |
| `Kill` | Running jobs are forcefully terminated. |

## Step 9: Clean Up Inactive Sessions

Run either command as appropriate:

```bash
uip or sessions delete-inactive <session-id-1> <session-id-2> --output json
uip or sessions delete-inactive --output json
```

`delete-inactive` targets `Disconnected` sessions and does not affect `Available` or `Busy` sessions. Omitting session IDs removes all inactive sessions in the tenant; confirm before running this in production.

## Variations and Gotchas

### Folder Scope

Sessions are tenant-wide by default. Add `--folder-path` to scope results for:

- `sessions attended list`
- `sessions unattended list`
- `sessions machines list`

Without `--folder-path`, results include all tenant sessions and require appropriate permissions.

### Session vs Machine

A **machine** is a registered physical or virtual host. A **session** is a robot runtime connection from that machine to Orchestrator. One machine can host multiple sessions, such as multiple user sessions on a terminal server.

## Related

- [setup-environment.md](setup-environment.md) -- Folder creation, machine assignment, runtime configuration
- [run-jobs.md](run-jobs.md) -- Start and monitor jobs (check runtimes before starting)
- [orchestrator.md](orchestrator.md) -- Orchestrator concepts and common flags