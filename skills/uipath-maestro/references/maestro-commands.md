# uip maestro — CLI Command Reference

All commands require `uip login` first. All commands output `{ "Result": "Success"|"Failure", "Code": "...", "Data": { ... } }`. Use `--format json` for programmatic use.

> **Prerequisite:** Install the Maestro tool plugin: `uip tools install @uipath/maestro-tool`

---

## Instances

Manage Maestro process instances (running, paused, completed, faulted, or cancelled).

### uip maestro instances list

List process instances with optional filters.

```bash
uip maestro instances list --format json
uip maestro instances list --folder-key <key> --format json
uip maestro instances list --process-key <key> --format json
uip maestro instances list --package-id <id> --format json
uip maestro instances list --error-code <code> --format json
uip maestro instances list -l 50 --offset 0 --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--folder-key <key>` | No | Filter by Orchestrator folder key |
| `--process-key <key>` | No | Filter by process key |
| `--package-id <id>` | No | Filter by package ID |
| `--error-code <code>` | No | Filter by error code |
| `-l <n>` | No | Limit number of results (default varies) |
| `--offset <n>` | No | Skip first N results for pagination |

### uip maestro instances get

Get details of a specific process instance.

```bash
uip maestro instances get <instance-id> --format json
uip maestro instances get <instance-id> --folder-key <key> --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<instance-id>` | **Yes** | The process instance ID (positional) |
| `--folder-key <key>` | No | Orchestrator folder key |

### uip maestro instances pause

Pause a running process instance.

```bash
uip maestro instances pause <instance-id> --format json
uip maestro instances pause <instance-id> --folder-key <key> --format json
uip maestro instances pause <instance-id> --comment "Pausing for review" --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<instance-id>` | **Yes** | The process instance ID (positional) |
| `--folder-key <key>` | No | Orchestrator folder key |
| `--comment <text>` | No | Optional comment explaining the action |

### uip maestro instances resume

Resume a paused process instance.

```bash
uip maestro instances resume <instance-id> --format json
uip maestro instances resume <instance-id> --folder-key <key> --format json
uip maestro instances resume <instance-id> --comment "Resuming after review" --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<instance-id>` | **Yes** | The process instance ID (positional) |
| `--folder-key <key>` | No | Orchestrator folder key |
| `--comment <text>` | No | Optional comment explaining the action |

### uip maestro instances cancel

Cancel a running or paused process instance.

```bash
uip maestro instances cancel <instance-id> --format json
uip maestro instances cancel <instance-id> --comment "No longer needed" --format json
uip maestro instances cancel <instance-id> --folder-key <key> --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<instance-id>` | **Yes** | The process instance ID (positional) |
| `--folder-key <key>` | No | Orchestrator folder key |
| `--comment <text>` | No | Optional comment explaining the cancellation |

### uip maestro instances retry

Retry a faulted process instance.

```bash
uip maestro instances retry <instance-id> --format json
uip maestro instances retry <instance-id> --folder-key <key> --format json
uip maestro instances retry <instance-id> --comment "Retrying after fix" --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<instance-id>` | **Yes** | The process instance ID (positional) |
| `--folder-key <key>` | No | Orchestrator folder key |
| `--comment <text>` | No | Optional comment explaining the retry |

### uip maestro instances goto

Navigate a process instance to specific step(s). The steps argument is a **JSON array** passed as a positional argument.

```bash
# Navigate to a single step
uip maestro instances goto <instance-id> '["StepName"]' --format json

# Navigate to multiple steps
uip maestro instances goto <instance-id> '["Step1","Step2"]' --format json

# With folder key
uip maestro instances goto <instance-id> '["ApprovalStep"]' --folder-key <key> --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<instance-id>` | **Yes** | The process instance ID (positional) |
| `<steps>` | **Yes** | JSON array of step names (positional) |
| `--folder-key <key>` | No | Orchestrator folder key |

> **Shell quoting:** Always wrap the JSON array in single quotes in bash to prevent shell expansion. If step names contain single quotes, use `$'...'` syntax or escape accordingly.

### uip maestro instances input

Set input data on a process instance.

```bash
uip maestro instances input <instance-id> '{"key":"value"}' --format json
uip maestro instances input <instance-id> '{"approver":"john@example.com","amount":5000}' --folder-key <key> --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<instance-id>` | **Yes** | The process instance ID (positional) |
| `<input-data>` | **Yes** | JSON object with input key-value pairs (positional) |
| `--folder-key <key>` | No | Orchestrator folder key |

### uip maestro instances deadline

Set or update the deadline on a process instance.

```bash
uip maestro instances deadline <instance-id> "2025-12-31T23:59:59Z" --format json
uip maestro instances deadline <instance-id> "2025-12-31T23:59:59Z" --folder-key <key> --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<instance-id>` | **Yes** | The process instance ID (positional) |
| `<deadline>` | **Yes** | ISO 8601 datetime string (positional) |
| `--folder-key <key>` | No | Orchestrator folder key |

### uip maestro instances create-note

Create a note on a process instance.

```bash
uip maestro instances create-note <instance-id> "This is a note" --format json
uip maestro instances create-note <instance-id> "Escalated to manager" --folder-key <key> --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<instance-id>` | **Yes** | The process instance ID (positional) |
| `<note-text>` | **Yes** | The note content (positional) |
| `--folder-key <key>` | No | Orchestrator folder key |

### uip maestro instances list-notes

List all notes on a process instance.

```bash
uip maestro instances list-notes <instance-id> --format json
uip maestro instances list-notes <instance-id> --folder-key <key> --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<instance-id>` | **Yes** | The process instance ID (positional) |
| `--folder-key <key>` | No | Orchestrator folder key |

### uip maestro instances update-priority

Update the priority of a process instance.

```bash
uip maestro instances update-priority <instance-id> <priority> --format json
uip maestro instances update-priority <instance-id> <priority> --folder-key <key> --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<instance-id>` | **Yes** | The process instance ID (positional) |
| `<priority>` | **Yes** | New priority value (positional) |
| `--folder-key <key>` | No | Orchestrator folder key |

### uip maestro instances list-tasks

List tasks associated with a process instance.

```bash
uip maestro instances list-tasks <instance-id> --format json
uip maestro instances list-tasks <instance-id> --folder-key <key> --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<instance-id>` | **Yes** | The process instance ID (positional) |
| `--folder-key <key>` | No | Orchestrator folder key |

---

## Processes

View deployed Maestro process definitions.

### uip maestro processes list

List all deployed Maestro processes.

```bash
uip maestro processes list --format json
uip maestro processes list --folder-key <key> --format json
uip maestro processes list -l 50 --offset 0 --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--folder-key <key>` | No | Filter by Orchestrator folder key |
| `-l <n>` | No | Limit number of results |
| `--offset <n>` | No | Skip first N results for pagination |

### uip maestro processes get

Get details of a specific Maestro process.

```bash
uip maestro processes get <process-key> --format json
uip maestro processes get <process-key> --folder-key <key> --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<process-key>` | **Yes** | The process key (positional) |
| `--folder-key <key>` | No | Orchestrator folder key |

---

## Incidents

View runtime incidents (errors) for Maestro processes.

### uip maestro incidents list

List Maestro incidents.

```bash
uip maestro incidents list --format json
uip maestro incidents list --folder-key <key> --format json
uip maestro incidents list -l 50 --offset 0 --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--folder-key <key>` | No | Filter by Orchestrator folder key |
| `-l <n>` | No | Limit number of results |
| `--offset <n>` | No | Skip first N results for pagination |

---

## Global Options (all commands)

| Option | Description |
|--------|-------------|
| `--format json\|yaml\|table` | Output format (default: table in TTY, json otherwise) |
| `--verbose` | Enable debug logging |
| `--help` | Show command help |

## Common Workflows

### Monitor a running instance

```bash
# List running instances
uip maestro instances list --format json

# Get details of a specific instance
uip maestro instances get <instance-id> --format json

# Check tasks within the instance
uip maestro instances list-tasks <instance-id> --format json

# View notes
uip maestro instances list-notes <instance-id> --format json
```

### Handle a faulted instance

```bash
# Find faulted instances (check error-code or inspect each)
uip maestro instances list --format json

# Inspect the faulted instance
uip maestro instances get <instance-id> --format json

# Check incidents for error details
uip maestro incidents list --format json

# Retry after fixing the underlying issue
uip maestro instances retry <instance-id> --comment "Fixed data issue" --format json
```

### Navigate an instance past a stuck step

```bash
# Inspect current state
uip maestro instances get <instance-id> --format json

# Navigate to specific steps (skipping the stuck step)
uip maestro instances goto <instance-id> '["NextStep"]' --format json

# Add a note explaining the navigation
uip maestro instances create-note <instance-id> "Skipped stuck step, navigated to NextStep" --format json
```
