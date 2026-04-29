# CLI Commands Reference

Only these `uip case` commands are needed in the SKILL-driven workflow. All local JSON structure is written directly by the agent.

---

## Project Scaffolding (Phase 0 — New Cases Only)

Required before writing `caseplan.json` for the first time. Skip if a project already exists.

```bash
# Create the directory and solution
mkdir -p <DIRECTORY>
cd <DIRECTORY> && uip solution new <SOLUTION_NAME>

# Create the case project inside the solution
cd <SOLUTION_NAME> && uip case init <PROJECT_NAME>

# Register the project in the solution manifest
uip solution project add <PROJECT_NAME> <SOLUTION_NAME>.uipx
```

---

## Authentication

```bash
uip login status --output json
uip login                                         # interactive OAuth
uip login --authority https://alpha.uipath.com    # non-production
```

---

## Registry (Phase 1 — Discovery)

```bash
# Refresh local cache from cloud
uip case registry pull

# Search by keyword (returns matching processes, agents, apps)
uip case registry search "<KEYWORD>" --output json

# List all cached entries
uip case registry list --output json

# Get full schema for a specific resource
uip case registry get --type <TYPE> --id <ID> --output json

# Get connector type details
uip case registry get-connector --key <CONNECTOR_KEY> --output json

# Get available connections for a connector
uip case registry get-connection --key <CONNECTOR_KEY> --output json
```

---

## Task Enrichment (Phase 4 — Connector Tasks Only)

Needed for: `external-agent`, `wait-for-connector`, `execute-connector-activity` tasks.

```bash
# Get enriched task schema from connector
uip case tasks describe \
  --file <PATH_TO_CASEPLAN_JSON> \
  --task-id <TASK_ID> \
  --type <TASK_TYPE> \
  --id <CONNECTOR_TYPE_ID> \
  --output json
```

---

## Event Trigger Enrichment (Phase 4 — Event Triggers Only)

```bash
# Add an enriched connector event trigger (replaces manual trigger node)
uip case triggers add-event \
  --file <PATH_TO_CASEPLAN_JSON> \
  --type-id <CONNECTOR_TYPE_ID> \
  --connection-id <CONNECTION_ID> \
  --output json

# Optional: filter events
uip case triggers add-event \
  --file <PATH_TO_CASEPLAN_JSON> \
  --type-id <CONNECTOR_TYPE_ID> \
  --connection-id <CONNECTION_ID> \
  --filter "<FILTER_EXPRESSION>" \
  --output json
```

---

## Validation (Phase 5)

```bash
# Validate local schema — no auth required
uip case validate --file <PATH_TO_CASEPLAN_JSON> --output json
```

If validation fails, fix the reported issues in caseplan.json directly and re-run.

---

## Debug (Phase 5 — Requires Explicit User Consent)

> **Warning:** `debug` uploads the project to Studio Web and executes it in Orchestrator. This has real side effects: emails sent, APIs called, database records written. Always get explicit user consent before running.

```bash
uip case debug --project-dir <PROJECT_DIR> --output json

# With specific Orchestrator folder
uip case debug --project-dir <PROJECT_DIR> --folder-id <FOLDER_ID> --output json
```

---

## Runtime Management

### Case Process

```bash
# List available processes in Orchestrator folder
uip case process list --folder-key <FOLDER_GUID> --output json

# Get process schema and entry points
uip case process get --folder-key <FOLDER_GUID> --process-key <KEY> --output json

# Start a case process
uip case process run \
  --folder-key <FOLDER_GUID> \
  --process-key <KEY> \
  --output json
```

### Job Status

```bash
# Stream real-time job traces
uip case job traces --job-key <KEY> --output json

# Get job status
uip case job status --job-key <KEY> --output json
```

### Instance Management

```bash
uip case instance list   --folder-key <FOLDER_GUID> --output json
uip case instance get    --folder-key <FOLDER_GUID> --instance-id <ID> --output json
uip case instance pause  --folder-key <FOLDER_GUID> --instance-id <ID> --output json
uip case instance resume --folder-key <FOLDER_GUID> --instance-id <ID> --output json
uip case instance cancel --folder-key <FOLDER_GUID> --instance-id <ID> --output json
```

### Incidents and Process Summaries

```bash
uip case processes list      --folder-key <FOLDER_GUID> --output json
uip case incident summary    --folder-key <FOLDER_GUID> --output json
uip case incident get --id <INCIDENT_ID> --output json
```

---

## Binary Resolution

If `uip` is not on PATH (common in nvm environments):

```bash
UIP=$(command -v uip 2>/dev/null || echo "$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip")
$UIP --version
```

Use `$UIP` in place of `uip` for all subsequent commands.
