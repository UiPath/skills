# Manage Sessions

Monitor robot sessions, check runtime availability, toggle debug mode, and manage maintenance windows.

> For full option details on any command, use `--help` (e.g., `uip or sessions list-attended-sessions --help`)

## When to Use

- Checking robot availability before starting jobs
- Debugging connectivity issues with connected robots
- Enabling debug mode for Studio remote debugging
- Planning and executing maintenance windows
- Cleaning up disconnected or stale sessions

## Prerequisites

- Authenticated (`uip login`)
- Environment set up with folders and machines (see [setup-environment.md](setup-environment.md))

---

## Step 1: Check Folder Runtimes

Before starting jobs, verify that the target folder has available runtime slots:

```bash
uip or folders runtimes <folder-key> --output json
```

This shows runtime capacity per type: total slots, connected machines, and available (idle) slots. If available slots are zero, jobs will queue in Pending state until a slot frees up.

## Step 2: List Attended Sessions

View attended robot sessions (human-interactive robots via UiPath Assistant):

```bash
uip or sessions list-attended-sessions --output json

# Filter by folder
uip or sessions list-attended-sessions --folder-path "Finance" --output json

# Filter by state
uip or sessions list-attended-sessions --state Available --output json
```

Session states: `Available`, `Busy`, `Disconnected`, `Unknown`.

## Step 3: List Unattended Sessions

View unattended robot sessions (autonomous execution robots):

```bash
uip or sessions list-unattended-sessions --output json

# Filter by folder and runtime type
uip or sessions list-unattended-sessions \
  --folder-path "Production" \
  --runtime-type Unattended \
  --output json
```

## Step 4: List Machine Sessions

View all sessions on a specific machine:

```bash
uip or sessions list-machines-sessions <machine-key> --output json

# Scoped to a folder
uip or sessions list-machines-sessions <machine-key> \
  --folder-path "Production" --output json
```

## Step 5: List Active Usernames

See which users currently have active sessions:

```bash
uip or sessions list-usernames --output json
```

## Step 6: List User Executors

See which execution slots are allocated to users:

```bash
uip or sessions list-user-executors --output json
```

## Step 7: Toggle Debug Mode

Enable debug mode on a session to allow Studio to connect remotely for live debugging:

```bash
# Enable debug mode for 30 minutes
uip or sessions toggle-debug-mode <session-id> \
  --enabled true --minutes 30 --output json

# Disable debug mode
uip or sessions toggle-debug-mode <session-id> \
  --enabled false --output json
```

Debug mode auto-expires after the specified `--minutes` duration. While active, Studio can attach to the robot session for step-through debugging.

## Step 8: Set Maintenance Mode

Put a session into maintenance mode to prevent new jobs from being assigned:

```bash
# Enable maintenance mode
uip or sessions set-maintenance-mode <session-id> \
  --maintenance-mode Enabled --output json

# Enable and stop current jobs
uip or sessions set-maintenance-mode <session-id> \
  --maintenance-mode Enabled \
  --stop-jobs-strategy SoftStop --output json

# Force-stop current jobs during maintenance
uip or sessions set-maintenance-mode <session-id> \
  --maintenance-mode Enabled \
  --stop-jobs-strategy Kill --output json

# Disable maintenance mode
uip or sessions set-maintenance-mode <session-id> \
  --maintenance-mode Disabled --output json
```

While maintenance mode is enabled, the Orchestrator will not assign new jobs to the session. Existing running jobs continue unless a `--stop-jobs-strategy` is specified.

## Step 9: Clean Up Inactive Sessions

Remove disconnected or stale sessions:

```bash
# Delete specific inactive sessions
uip or sessions delete-inactive <session-id-1> <session-id-2> --output json

# Delete ALL inactive sessions (no IDs = clean all)
uip or sessions delete-inactive --output json
```

**Warning:** Running `delete-inactive` without session IDs removes ALL inactive sessions in the tenant. Use with caution.

---

## Complete Example

Check runtime availability, inspect sessions, enable debug mode for troubleshooting, then clean up.

```bash
# 1. Check if the folder has available runtimes
uip or folders runtimes <folder-key> --output json

# 2. List unattended sessions to find the target robot
uip or sessions list-unattended-sessions \
  --folder-path "Production" --output json
# -> Note the session Id for the robot you need to debug

# 3. Enable debug mode for 30 minutes
uip or sessions toggle-debug-mode <session-id> \
  --enabled true --minutes 30 --output json

# 4. (Attach Studio, debug the issue...)

# 5. Disable debug mode when done
uip or sessions toggle-debug-mode <session-id> \
  --enabled false --output json

# 6. Clean up any stale disconnected sessions
uip or sessions delete-inactive --output json
```

---

## Variations and Gotchas

### Folder Scope

Sessions are tenant-wide by default. Add `--folder-path` to scope results to a specific folder. This applies to:

- `list-attended-sessions`
- `list-unattended-sessions`
- `list-machines-sessions`

Without `--folder-path`, you see all sessions across the tenant (requires appropriate permissions).

### Debug Mode Auto-Expiry

Debug mode automatically disables after the `--minutes` duration elapses. There is no persistent debug mode -- you must specify a duration. If you need more time, re-enable it before it expires.

### Maintenance Mode and Job Assignment

Maintenance mode prevents **new** job assignment only. It does not pause or stop jobs that are already running unless you explicitly set `--stop-jobs-strategy`:

| Strategy | Behavior |
|----------|----------|
| (none) | Running jobs continue, no new jobs assigned |
| `SoftStop` | Running jobs receive a graceful stop signal |
| `Kill` | Running jobs are forcefully terminated |

### Cleaning Inactive Sessions

`delete-inactive` targets sessions in a `Disconnected` state. It will not affect `Available` or `Busy` sessions. Omitting session IDs cleans **all** inactive sessions -- useful for periodic maintenance but should be confirmed before running in production.

### Session vs Machine

A **machine** is the registered host (physical or virtual). A **session** is a runtime connection from a robot on that machine to Orchestrator. One machine can host multiple sessions (e.g., multiple user sessions on a terminal server).

---

## Related

- [setup-environment.md](setup-environment.md) -- Folder creation, machine assignment, runtime configuration
- [run-jobs.md](run-jobs.md) -- Start and monitor jobs (check runtimes before starting)
- [orchestrator.md](orchestrator.md) -- Orchestrator concepts and common flags
