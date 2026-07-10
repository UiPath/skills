---
name: uipath-process-mining
description: "UiPath Process Mining via `uip pm` — create process apps from templates, upload event-log data, trigger ingestions, edit and run dbt SQL transformations. Covers app-types discovery, apps create/list, chunked file upload, ingestion runs + logs, ETag-safe transformation file edits, builds, build status/logs. For job execution metrics→uipath-insights, Orchestrator jobs/queues/processes→uipath-platform, root-cause of a specific error→uipath-troubleshoot, BPMN orchestration→uipath-maestro-bpmn."
when_to_use: "User says 'process mining', 'process app', 'uip pm', 'event log', 'upload event log', 'ingest data', 'ingestion', 'dbt transformation', 'app template', 'transformation build', 'process miner'. NOT for job monitoring dashboards (uipath-insights), NOT for Orchestrator job management (uipath-platform), NOT for authoring BPMN processes (uipath-maestro-bpmn)."
allowed-tools: Bash, Read, Write, Edit
---

# UiPath Process Mining — Process Apps Agent Skill

Process Mining analyzes event logs to reconstruct and improve real business processes. This skill covers the full CLI pipeline: discover an app template → create a process app → upload data files → ingest them → inspect/edit/run the dbt SQL transformations.

All operations go through `uip pm <group> <subcommand> --output json`.

---

## When to Use

- Creating a process app from an app template (app type)
- Uploading event-log/data files into a process app
- Triggering and monitoring data ingestions
- Reading, editing, and running the dbt SQL transformations of a process app
- Re-running the transform on already-ingested data

> **Not in scope:** job execution metrics (uipath-insights), Orchestrator jobs/queues (uipath-platform), dashboards or published-app analytics (no CLI surface yet).

---

## Login & Tenant Setup

**Default to the current session. Only switch environment/org/tenant when the request names one.**

```bash
# Check current environment, org, and tenant
uip login status --output json

# Login to a specific environment
uip login --authority https://cloud.uipath.com --tenant MyTenant
```

The tenant must have **Process Mining enabled**. If every `uip pm` command fails at the API, the tenant likely lacks Process Mining — stop and report; do not retry.

---

## Critical Rules

1. **Pipeline order is fixed.** app-types list → apps create → files upload → ingestions create → transformations. Each step needs output from the previous one (template key/version, `AppId`, ingestion id, model path).

2. **Ingestions and builds are asynchronous.** `ingestions create`, `transformations run`, and `transformations apply` return `Status: "Accepted"` immediately — that means started, not done. Poll:
   - ingestion / apply progress: `uip pm apps list --output json` → `LastIngestion` field
   - build progress: `uip pm transformations status <APP_ID> --output json`

   Runs take minutes. A still-running ingestion/build is PENDING, not failed.

3. **Always `--output json`.** Every command returns the envelope `{ Result, Code, Data }`. Parse `Data`.

4. **Stage is `dev` or `published`; default `dev`.** `transformations run` supports only `dev`.

5. **Transformation writes are ETag-safe.** `transformations update` fetches the remote ETag and writes with `If-Match`. On a 412 (concurrent edit): re-`get` the file, reapply the edit, retry once. Never assume the local copy is current.

6. **There are no delete commands.** The CLI cannot delete apps, files, or ingestions. Do not invent `uip pm apps delete`. To fix bad data: re-upload files and re-ingest, or run `transformations apply`.

7. **The data mapping must match the template model.** Build the `--data-mapping` JSON from the input tables/fields returned by `uip pm app-types get <TYPE_KEY> <VERSION> --output json`.

---

## Command Reference

| Command | Purpose |
|---------|---------|
| `uip pm app-types list` | List available app templates at latest version (`AppTypeKey`, `Version`) |
| `uip pm app-types get <key> <version>` | Full app model of a template version (input tables/fields) |
| `uip pm apps list [--stage dev\|published]` | List process apps (`Id`, `Name`, `LastIngestion`) |
| `uip pm apps create <name> --type <key> [--type-version <v>] [--miner directly-follows\|inductive\|bpmn] [--description <text>] [--data-mapping <json-file>]` | Create app from template; latest version resolved when `--type-version` omitted → `Data.AppId` |
| `uip pm files upload <app-id> <file-path> [--stage] [--input-table <name>]` | Chunked upload (5 MB parts) of a data file → `{ Filename, UploadId, Size, Parts, InputTable }` |
| `uip pm ingestions create <app-id> [--stage] [--file-format csv\|tsv] [--field-delimiter ,] [--quote-character "] [--encoding utf-8\|iso-8859-1]` | Ingest the uploaded files (async) |
| `uip pm ingestions logs <app-id> <ingestion-id> [--stage] [--limit 100] [--offset 0]` | Ingestion run logs (paged) |
| `uip pm transformations list <app-id> [--stage]` | dbt file tree of the app |
| `uip pm transformations get <app-id> <path> [--stage] [--destination <local-file>]` | Read a transformation file — inline `Content`, or to disk with `--destination`; returns `ETag` |
| `uip pm transformations update <app-id> <path> --file <local-file> [--stage]` | ETag-safe write of a transformation file |
| `uip pm transformations run <app-id> [--model <model-path>]` | Run dbt build on dev (async); `--model` builds one model + dependents |
| `uip pm transformations apply <app-id> [--stage]` | Re-run the full transform on already-ingested data (async) |
| `uip pm transformations status <app-id>` | Status of current/last build |
| `uip pm transformations logs <app-id>` | Logs of current/last build |

---

## Workflow: Create an App and Ingest Data

```bash
# 1. Discover templates; pick TYPE_KEY (e.g. uipath.custom) and VERSION
uip pm app-types list --output json

# 2. Fetch the template model; derive mapping.json from its input tables/fields
uip pm app-types get <TYPE_KEY> <VERSION> --output json

# 3. Create the app; save Data.AppId as APP_ID
uip pm apps create "<APP_NAME>" --type <TYPE_KEY> --data-mapping ./mapping.json --output json

# 4. Upload the event-log file(s)
uip pm files upload <APP_ID> ./Event_log.csv --input-table Event_log --output json

# 5. Trigger ingestion (async)
uip pm ingestions create <APP_ID> --file-format csv --encoding utf-8 --output json

# 6. Poll until LastIngestion reports completion; note the ingestion id
uip pm apps list --output json

# 7. Inspect ingestion logs (paged)
uip pm ingestions logs <APP_ID> <INGESTION_ID> --limit 50 --output json
```

---

## Workflow: Edit and Rebuild a dbt Transformation

```bash
# 1. Pick a model path, e.g. models/Cases.sql
uip pm transformations list <APP_ID> --output json

# 2. Download the file
uip pm transformations get <APP_ID> <MODEL_PATH> --destination ./model.sql --output json

# 3. Edit ./model.sql locally, then push back (ETag-safe)
uip pm transformations update <APP_ID> <MODEL_PATH> --file ./model.sql --output json

# 4. Build only this model and its dependents (omit --model for a full build)
uip pm transformations run <APP_ID> --model <MODEL_PATH> --output json

# 5. Poll status until complete, then read logs
uip pm transformations status <APP_ID> --output json
uip pm transformations logs <APP_ID> --output json
```

To re-run the full transform on data already ingested (no re-upload):

```bash
uip pm transformations apply <APP_ID> --output json
uip pm apps list --output json   # poll LastIngestion
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Not logged in` | Auth expired | `uip login` |
| Every `uip pm` command fails at the API | Process Mining not enabled on tenant | Report; switch tenant only if the user names one |
| `App type '<key>' not found.` | Wrong `--type` key | `uip pm app-types list --output json` |
| `File not found: <path>` / `Local file not found: <path>` | Wrong local path | Fix the path; command exits 1 without any API call |
| 412 on `transformations update` | Concurrent edit changed the file | Re-`get`, reapply edit, retry once |
| Upload or ingest rejected | Another ingestion in progress | Poll `uip pm apps list` until `LastIngestion` completes, retry |
| `error: option '--stage' argument 'X' is invalid` | Invalid stage | Only `dev` and `published` exist |

---

## What NOT to Do

- **Don't hand-roll HTTP calls to the Process Mining API.** The CLI handles auth, chunked 5 MB blob uploads with presigned URIs, and ETag concurrency. `curl`/`fetch` will miss these.
- **Don't treat `Status: "Accepted"` as completion.** Ingestions and builds are async — poll before asserting results or starting the next stage.
- **Don't retry auth failures.** 401 / "Not logged in" means `uip login`, not re-running the command.
- **Don't run `transformations run` on `published`.** Builds run on `dev` only; use `transformations apply` for published-stage re-transforms.
- **Don't write transformation files without `transformations update`.** It is the only ETag-safe write path.
- **Don't try to delete or recreate apps to fix data.** No delete exists — re-upload + `ingestions create`, or `transformations apply`.
