# Run Jobs

Upload automation packages, bind them as processes, start jobs, and monitor execution with logs, traces, healing data, and history.

> For full option details, run `uip or jobs start --help` (or `--help` on any command).

## When to Use

- Deploying/running automations end-to-end
- Debugging failed or faulted jobs
- CI/CD execution and verification
- Monitoring long-running unattended processes

## Prerequisites

- Verify authentication with `uip login status`; if not logged in, ask the user to run `uip login` (it opens an interactive browser flow).
- Ensure the target folder exists with machines assigned (see [setup-environment.md](setup-environment.md)).
- Have a built `.nupkg` automation package ready to upload.

## Flow

`packages upload` → `processes create` → `jobs start` → `jobs logs`, `traces spans get`, `jobs healing-data`, or `jobs history`.

---

## Step 1: Upload Package

```bash
uip or packages upload ./MyProcess.1.0.0.nupkg --output json
uip or packages upload ./MyProcess.1.0.0.nupkg --feed-id <feed-key> --output json
```

An upload to a personal workspace's feed also creates a process for the package in that workspace. Look for it with `processes list` before Step 3; `processes create` would add a second process for the same package.

## Step 2: Inspect Package

Verify the upload and discover entry points before creating a process. `packages get`, `packages versions`, and `processes create` use the **tenant** feed by default. For a folder-hierarchy feed, pass `--feed-id <feed-key>`; otherwise they return empty/404 although the package exists. `processes create` no longer pre-checks the feed and succeeds in a folder feed regardless.

```bash
uip or packages list --search "MyProcess" --output json
uip or packages versions <package-id> --output json
uip or packages entry-points "MyProcess:1.0.0" --output json
uip or packages get "MyProcess:1.0.0" --output json
uip or packages download "MyProcess:1.0.0" --destination ./MyProcess.1.0.0.nupkg --output json
```

Entry points identify executable workflows; multi-entry-point packages require `--entry-point` during process creation. `packages get` accepts the `Id:Version` key returned by `packages list`/`packages versions`; `--all-fields` returns the raw DTO, including `tags`, `targetFramework`, and `isCompiled`.

## Step 3: Create Process

Bind the package to a folder:

```bash
uip or processes list --folder-path "Production" --output json
uip or processes create --name "MyProcess" \
  --package-key "MyProcess" \
  --package-version "1.0.0" \
  --folder-path "Production" \
  --output json
```

Options:

- `--entry-point <path>`: required for multi-entry-point packages.
- `--auto-update` / `--no-auto-update`: auto-pick the latest package version on deploy.
- `--job-priority <Low|Normal|High>`: default priority; CLI maps Low=25, Normal=45, High=65 to `SpecificPriorityValue` bands, which the API derives and applies.
- `--specific-priority <1-100>`: numeric override, mutually exclusive with `--job-priority`, for ordering within a bucket.
- `--robot-size <Small|Standard|Medium|Large>`: cloud serverless machine size. Omit it for `Automatic` (stored as no size and selected by the serverless service); also supported by `processes update`.
- `--input-arguments <json>`: default arguments, merged with per-job inputs.
- `--environment-variables <pairs>`: newline-separated `KEY=VALUE`, **not JSON**; merged with per-job values.
- `--tags <list>`: comma-separated filtering tags.
- `--hidden-for-attended` / `--visible-for-attended`: attended-user visibility.
- `--auto-create-triggers` / `--no-auto-create-triggers`: create connected triggers on deploy.
- `--retention-period <days>` + `--retention-action <Delete|Archive|None>` (+ `--retention-bucket <bucket-key>`): retention policy; period is 1-180 (client-side); `Archive` requires `--retention-bucket`.
- `--stale-retention-period <days>` + `--stale-retention-action <Delete|Archive|None>` (+ `--stale-retention-bucket <bucket-key>`): stale-job policy. `Archive` requires both bucket and explicit period; Delete/None default to 180 days; a period without an action is rejected.

> Buckets are passed by **key (GUID)**: run `uip or buckets list --folder-path <folder> --output json` and use `Key`. `--retention-bucket` also accepts a legacy numeric id; `--stale-retention-bucket` does not. The bucket must be in or shared to the process folder, or Orchestrator returns `404 Bucket does not exist`. On `processes update`, omitted retention flags preserve stored values: archiving preserves bucket/period; switching to Delete/None clears the bucket.

> Runtime kind (Unattended / Headless / NonProduction / AgentService / Serverless) is selected per job with `jobs start --runtime-type`, not on the process. The process binds the package to a folder.

### Inspect / Edit / Roll back / Delete Processes

```bash
uip or processes get <process-key-guid> --output json
uip or processes resources <process-key-guid> --output json
uip or processes update <process-key-guid> --description "Updated description" --output json
uip or processes update <process-key-guid> --environment-variables $'API_HOST=api.example.com\nRETRIES=3' --output json
uip or processes update <process-key-guid> --environment-variables '' --output json
uip or processes update <process-key-guid> --robot-size Large --output json
uip or processes version-history <process-key-guid> --output json
uip or processes update-version <process-key-guid> --package-version 1.0.2 --output json
uip or processes rollback <process-key-guid> --output json
uip or processes delete <process-key-guid> --yes --output json
```

`processes get` is cross-folder. `processes update` has the create flags except name/package-key/package-version, plus `--healing-agent` / `--no-healing-agent`. Environment variables are newline-separated `KEY=VALUE`, not JSON; pass `''` to clear them (the CLI sends a bare newline because an empty body means leave unchanged). `--robot-size Large` resizes after deployment; omitting the flag preserves the size, while no value restores `Automatic`. `version-history` walks every package version the release pointed at; `update-version` pins a version (typically to roll back after a regression); `rollback` reverts to the previous version in version-history. `delete` removes the process (release); the package itself stays in the feed.

Run `processes resources` before `jobs start`. It returns one row per resource the package declares (Queue, Asset, Bucket, Connection, Process, EventTrigger, HttpTrigger, Entity, MCPServer, IXP, ProcessExecutionSettings, ...). Read each `ValidationResult`: `Success` means the folder contains the resource (`ResourceId` identifies it), `NotFound` means missing and `ValidationError` explains why, and `Unknown` means not folder-validated (connections, execution settings). Filter broken rows with `--output-filter "[?ValidationResult=='NotFound']"`.

`ResourceName`, `FolderPath`, `ResourceId`, and `ValidationResult` describe package declarations even after rebinding. A rebind has `IsOverwritten: true`; `OverwriteName`, `OverwriteEntityId`, and `OverwriteFolderId` identify the resolved target, while `OverwriteProperties` contains raw lowercase `name` and `folderPath` pairs. Thus `FolderPath: Dev/Apps` may pair with `OverwriteProperties.folderPath: Prod/Apps`; the latter is used by the job. Find rebound rows with `--output-filter "[?IsOverwritten]"`. Package-default `Success` does not prove the overwrite target exists; inspect `OverwriteProperties` when binding fails.

`processes update` maps `ReleaseDto` to `UiRelease` server-side, so hand-built bodies with missing fields null them (`tags`, `arguments`, `videoRecordingSettings`, `targetFramework`, `robotSize`, `resourceOverwrites`, `remoteControlAccess`, `targetRuntime`, `publisherLicense`, etc.). The CLI avoids this by spreading `currentRelease` before overrides.

On license-slots tenants, changing `--robot-size` during update is rejected with HTTP `400`, `'RobotSize' is not editable.` (`ErrorCode 1024`, `FieldNotEditable`); the CLI passes it through and the UI hides the field. The refusal applies only when changing to a non-null size; unrelated updates echoing the current size are unaffected.

## Step 4: Start Job

Get the process key from `uip or processes list`, then run:

```bash
uip or jobs start <process-key> --folder-path "Production" --output json
uip or jobs start <process-key> --folder-path "Production" \
  --input-arguments '{"invoiceId": "INV-001", "amount": 1500}' \
  --wait-for-completion --timeout 600 \
  --output json
```

Options:

- `--input-arguments <json>` / `--input-file <path>`: choose one. The former inlines a client-validated JSON object; the latter uploads a file as `InputFile`.
- Classic `StartJob` serialized input/output is capped at 10,240 characters. Oversized output is silently dropped (workflow receives `null`, job remains Successful). `StartAgentJob` is not subject to the same cap in practice; Robot 2025.10.1+ removes it entirely. For large payloads, use a storage bucket/queue reference or upgrade the Robot.
- `--attachment <[name=]path>`: upload one or more files; repeat for multiple. Pair with `--attachment-id <guid>` to reuse an uploaded attachment. File arguments must instead use an attachment reference in `--input-arguments`: `{"<ARGUMENT>": {"ID": "<ATTACHMENT_ID>", "FullName": "<FILE_NAME>"}}`, with `--attachment-id <ATTACHMENT_ID>`.
- `--runtime-type <type>`: `Unattended`, `Headless`, `NonProduction`, `AgentService`, or `Serverless`.
- `--strategy <strategy>`: `ModernJobsCount` (default; independent jobs with `--jobs-count`), `All` (every available folder robot), `Specific` (`--user-keys` / `--machine-keys`), or `JobsCount`; client-validated. `--jobs-count` must be a whole number greater than 0.
- `--user-keys <guids>` / `--machine-keys <guids>`: comma-separated GUIDs. With `ModernJobsCount`, restrict candidates; with `Specific`, required.
- `--healing-agent`: enable Autopilot for Robots for this job regardless of the process setting.
- `--reference <text>`: free-form external-correlation reference.
- `--environment-variables <pairs>`: newline-separated `KEY=VALUE`, not JSON; merged over folder/process values; malformed lines are rejected before submission.
- `--run-as-me`: use the caller identity instead of resolving an unattended account.
- `--wait-for-completion` + `--timeout <seconds>` (default 300) + `--poll-interval <seconds>` (default 5): poll to a terminal state.
- `--output-dir <path>` + `--no-download`: with `--wait-for-completion`, the CLI downloads the job's `OutputFile` to this directory automatically unless `--no-download` is passed.
- `--job-priority <Low|Normal|High>`: runtime queue priority.

## Step 5: Monitor Job

```bash
uip or jobs get <job-key> --output json
uip or jobs list --state Running --folder-path "Production" --output json
uip or jobs list --process-name "MyProcess" --folder-path "Production" --output json
uip or jobs list --all-folders --state Faulted --output json
```

`jobs get` is cross-folder. `jobs list` reads live Orchestrator records; use **uipath-insights** for historical metrics (failure counts, success rate, trends). It requires `--folder-path`, `--folder-key`, or `--all-folders`; bare `jobs list` is rejected. Older CLI versions listed tenant-wide by default; use `--all-folders` for that behavior.

## Step 6: Get Logs

```bash
uip or jobs logs <job-key> --output json
uip or jobs logs <job-key> --level Error --output json
uip or jobs logs <job-key> --export --destination ./logs.csv
```

`--export` writes CSV instead of terminal output; combine it with `--destination` or `-d`. Logs are cross-folder. Export calls RobotLogs Export, limited to 100 requests/day/tenant and shared tenant-wide. Diagnose with `--output json` (optionally `--level Error`) and export only when a CSV is requested. See [api-limits.md](api-limits.md).

## Step 7: Get Traces

```bash
uip traces spans get --job-key <job-key> --output json
```

Traces exist only for Autopilot/Agent processes, not standard Processes. Pass a trace id positionally when available; see [traces.md](../traces/traces.md). `uip or jobs traces` is removed: it parses, prints a pointer to the command above, exits non-zero, and must be replaced in scripts. Traces are cross-folder.

> To evaluate a published agent's output quality, trajectory, or tool use against eval sets/evaluators, load [`uipath-agents`](/uipath:uipath-agents). Commands are under `uip eval` (formerly `uip or eval`).

## Step 8: Get Healing Data

```bash
uip or jobs healing-data <job-key> -d ./healing-data.zip
```

The ZIP contains screenshots and UI metadata from Autopilot self-healing attempts.

## Step 9: Job History

```bash
uip or jobs history <job-key> --output json
```

This shows state transitions and timestamps, such as Pending -> Running -> Faulted.

## Step 10: Stop, Restart, Resume

```bash
uip or jobs stop <job-key> --strategy SoftStop --output json
uip or jobs stop <job-key> --strategy Kill --output json
uip or jobs restart <job-key> --output json
uip or jobs resume <job-key> --input-arguments '{"approved": true}' --output json
```

`SoftStop` is best-effort; activities ignoring the cancellation token can finish. `Kill` force-kills. `restart` accepts any finished outcome (faulted, stopped, successful) and returns the new run in the same `{ Jobs: [...] }` shape as `jobs start`. Jobs are immutable audit records; there is no `jobs delete`. They age out per the binding process's retention period.

## Step 11: Manage Processes

Use `processes update`, `processes update-version`, and `processes rollback` after deployment. To record manual time per item, volume, and employee cost for Orchestrator's Business ROI page, use `uip or process-roi`; see [business-roi.md](business-roi.md).

## Complete Example

```bash
# Upload -> create process -> start job -> check logs
uip or packages upload ./InvoiceProcessor.1.0.0.nupkg --output json
uip or packages entry-points "InvoiceProcessor:1.0.0" --output json

uip or processes create --name "InvoiceProcessor" \
  --package-key "InvoiceProcessor" --package-version "1.0.0" \
  --folder-path "Finance" --job-priority Normal \
  --output json

uip or jobs start <process-key> --folder-path "Finance" \
  --input-arguments '{"batchDate": "2026-04-22"}' \
  --wait-for-completion --timeout 600 --output json

uip or jobs logs <job-key> --level Error --output json
```

## Variations and Gotchas

### "Process" vs "Release"

The CLI's process is the API's Release; `ReleaseKey` equals the process key from `uip or processes list`.

### Process Key vs Package Key

| Key | Source | Format |
|---|---|---|
| Process key | `uip or processes list` | GUID (e.g., `a1b2c3d4-...`) |
| Package key | `uip or packages list` | String ID (e.g., `InvoiceProcessor`) |
| Package download key | `uip or packages download` | `PackageId:Version` (e.g., `InvoiceProcessor:1.0.0`) |

### Job States

```text
Pending -> Running -> Successful
                   -> Faulted
                   -> Stopped
                   -> Suspended (awaiting input)
```

Successful, Faulted, and Stopped are final and immutable.

### Wait and Input Behavior

`--wait-for-completion` polls every `--poll-interval` (default 5s) until a final state or `--timeout` (default 300s). `--input-arguments` accepts JSON; `--input-file` reads a path. If JSON exceeds 10K characters, the CLI automatically offloads it to an InputFile server-side. Run `uip or packages entry-points` to discover expected argument names and types.

### Cross-Folder Commands

These resolve the folder from the job key and need no `--folder-path`:

- `uip or jobs get <key>`
- `uip or jobs logs <key>`
- `uip or jobs history <key>`
- `uip or jobs healing-data <key>`

### Package Download

Use the `PackageId:Version` format:

```bash
uip or packages download "MyProcess:1.0.0" --destination ./packages/ --output json
```

## Related

- [setup-environment.md](setup-environment.md) — Folder creation, machine assignment, user setup
- [traces.md](../traces/traces.md) — Deep-dive into LLM/agentic traces and spans
- Resources (assets, queues, buckets, triggers, webhooks, libraries) → [resources.md](resources.md)