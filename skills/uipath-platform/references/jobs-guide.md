# Jobs Guide

Manage Orchestrator jobs via `uip or jobs` — start, monitor, stop, and debug automation executions.

## Concepts

A **job** is a single execution of a process. States: `Pending → Running → Successful | Faulted | Stopped | Suspended → Resumed → Running`.

- **Process key** — GUID from `uip or processes list`. Required to start jobs.
- **Job key** — GUID from `uip or jobs list` or `uip or jobs start`. Required for all per-job commands.

> **Folder context:** All `list` commands require `--folder-path` or `--folder-key`. Per-job commands (`get`, `stop`, `restart`, `resume`, `logs`, `traces`, `healing-data`, `history`) use the globally unique job key — no folder needed.

---

## Commands

### 1. List Jobs

```bash
uip or jobs list --folder-path "<FOLDER_PATH>" --output json
```

| Option | Required | Description |
|---|---|---|
| `--folder-path` / `--folder-key` | Yes (one of) | Folder scope |
| `--state <STATE>` | No | `Pending`, `Running`, `Successful`, `Faulted`, `Stopped`, `Stopping`, `Suspended`, `Resumed`, `Terminating` |
| `--process-name "<NAME>"` | No | Contains match, case-insensitive |
| `--source "<SOURCE>"` | No | `Manual`, `Schedule`, `Trigger` |
| `--created-after` / `--created-before` | No | ISO8601 timestamp filters |
| `--started-after` / `--started-before` | No | ISO8601 timestamp filters |
| `--ended-after` / `--ended-before` | No | ISO8601 timestamp filters |
| `--limit <N>` | No | Default: `50` |
| `--offset <N>` | No | Default: `0` |
| `--order-by "<FIELD>"` | No | Default: `"Id desc"` |

**Example — list faulted jobs from the last 24 hours:**

```bash
uip or jobs list \
  --folder-path "Finance/Invoicing" \
  --state Faulted \
  --started-after "2026-04-03T00:00:00Z" \
  --output json
```

---

### 2. Get Job Details

```bash
uip or jobs get <JOB_KEY> --output json
```

Returns state, input/output arguments, timestamps, machine name, fault info, and diagnostic reasons (for pending jobs).

---

### 3. Start a Job

```bash
uip or jobs start <PROCESS_KEY> --output json
```

| Option | Required | Description |
|---|---|---|
| `--folder-path` / `--folder-key` | No | Inferred from process if omitted |
| `--strategy <STRATEGY>` | No | `ModernJobsCount` (default), `All`, `Specific`, `JobsCount` |
| `--jobs-count <N>` | No | Instances to start (default: `1`) |
| `--input-arguments '<JSON>'` | No | JSON input arguments |
| `--input-file <NAME>=<PATH>` | No | File input. Repeatable. |
| `--job-priority <PRIORITY>` | No | `Low`, `Normal`, `High` |
| `--reference "<REFERENCE>"` | No | Tag string (e.g., ticket ID) |

> Get `<PROCESS_KEY>` (GUID) from `uip or processes list --folder-path "<FOLDER_PATH>" --output json`.

**Example — start with input arguments:**

```bash
uip or jobs start "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  --input-arguments '{"invoiceId": "INV-001", "dryRun": false}' \
  --output json
```

**Example — start three instances at high priority:**

```bash
uip or jobs start "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  --strategy ModernJobsCount \
  --jobs-count 3 \
  --job-priority High \
  --output json
```

---

### 4. Stop Jobs

```bash
uip or jobs stop <JOB_KEYS...> --output json
```

| Option | Required | Description |
|---|---|---|
| `--strategy <STRATEGY>` | No | `SoftStop` (default) or `Kill`. Only valid for single-job stops — multiple keys always force-stop. |

---

### 5. Restart a Job

```bash
uip or jobs restart <JOB_KEY> --output json
```

Creates a new job from the same process/parameters. Only valid for `Faulted` or `Stopped` jobs.

---

### 6. Resume a Suspended Job

```bash
uip or jobs resume <JOB_KEY> --output json
```

| Option | Required | Description |
|---|---|---|
| `--input-arguments '<JSON>'` | No | Updated input data for resumption |

**Example:**

```bash
uip or jobs resume "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  --input-arguments '{"approvalDecision": "Approved"}' \
  --output json
```

---

### 7. Job Logs

```bash
uip or jobs logs <JOB_KEY> --output json
```

> Known issue: May fail with "A folder is required" despite auto-inference. No `--folder-path` flag exists — use Orchestrator UI as fallback.

| Option | Required | Description |
|---|---|---|
| `--level <LEVEL>` | No | `Trace`, `Info`, `Warning`, `Error` |
| `--limit <N>` | No | Default: `50` |
| `--offset <N>` | No | Default: `0` |

---

### 8. Job Traces (LlmOps)

```bash
uip or jobs traces <JOB_KEY> --output json
```

Returns LLM observability traces (API calls, tool invocations, agent reasoning). Only returns data for **agent-type processes** — empty for standard RPA jobs.

---

### 9. Job Healing Data

```bash
uip or jobs healing-data <JOB_KEY> --output json
```

Downloads a ZIP with failure screenshots, UI element snapshots, and recovery logs. Export is async — CLI polls until ready.

---

### 10. Job State History

```bash
uip or jobs history <JOB_KEY> --output json
```

Returns full state-transition timeline with timestamps. Same "folder required" known issue as `logs`.

---

## Common Workflows

### Start and Monitor Until Completion

1. Get process key: `uip or processes list --folder-path "<FOLDER_PATH>" --output json`
2. Start job: `uip or jobs start "<PROCESS_KEY>" --output json` — note the job key
3. Poll: `uip or jobs get "<JOB_KEY>" --output json` — repeat until state is not `Pending`/`Running`
4. If `Successful` — read `outputArguments` from the response
5. If `Faulted` — run `uip or jobs logs "<JOB_KEY>" --level Error --output json`

> Stop polling after 30 attempts or 10 minutes. If `Pending` after 5 minutes, check runtime configuration.

---

## Anti-Patterns

- **Do not use process names as `<PROCESS_KEY>`.** The `start` command requires the GUID from `processes list`.
- **Do not poll indefinitely.** Cap at 30 attempts / 10 minutes.
- **Do not use `--strategy Kill` as default.** Prefer `SoftStop`. Use `Kill` only for unresponsive jobs.
- **Do not restart without reading the fault first.** Use `jobs get` + `jobs logs --level Error` to check if the failure is transient.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Job stays `Pending` | No runtimes in folder | Assign machines: `uip or machines assign` |
| `Pending` with diagnostic reasons | No matching robot free | Read `diagnosticReasons` from `jobs get` |
| `start` fails "Process not found" | Used process name instead of GUID | Use `key` from `processes list` |
| `start` fails error 2818 | No runtimes configured | Assign machines with unattended slots to folder |
| `start` fails "no user with unattended robot permissions" | No Automation User in folder | Assign user with Automation User role |
| Need jobs across all folders | `list` is folder-scoped, no `--all-folders` flag | Script: list all folders, then iterate `jobs list` per folder |
