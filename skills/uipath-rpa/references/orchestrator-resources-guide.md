# Orchestrator Resources Guide (Assets, Credentials, Storage Buckets, Queues, Jobs, Connections)

Judgment layer: which Orchestrator capability fits, secret hygiene, queue patterns beyond REFramework, job/process orchestration, runtime preconditions. Property surfaces live in the activity docs — primary `{PROJECT_DIR}/.local/docs/packages/UiPath.System.Activities/`, bundled fallback [activity-docs/UiPath.System.Activities/26.4/overview.md](activity-docs/UiPath.System.Activities/26.4/overview.md) (XAML, per-activity files under `26.4/activities/`) and [26.4/coded/coded-api.md](activity-docs/UiPath.System.Activities/26.4/coded/coded-api.md) (coded `system` service). All activities below ship in `UiPath.System.Activities` — already in every project.

## Choosing a Resource

| Data | Use | Why |
|------|-----|-----|
| Per-environment scalar (URL, flag, threshold, retry count) | Asset (Text / Integer / Boolean) | Edited in Orchestrator without redeploy; per-robot values supported |
| Secret (password, API key, token) | Credential or Secret asset | Encrypted store; Common Rule 5a — never `Config.xlsx` cells, never hardcoded |
| Many non-secret config values versioned with the project | `Config.xlsx` | [reframework-guide.md § Configuration Management](reframework-guide.md) — its Assets sheet holds asset *names*, values stay in Orchestrator |
| Files crossing jobs / robots / machines | Storage bucket | Survives the job; local disk does not follow the work |
| Units of work (parallel workers, retry, SLA, audit) | Queue | Locking, auto-retry, deadlines, reporting built in |
| Structured records with queries/filters | Data Fabric entity | [activity-docs/UiPath.DataService.Activities/overview.md](activity-docs/UiPath.DataService.Activities/overview.md) |
| Run / coordinate another deployed process | Jobs & processes | § Jobs & Processes below |
| Third-party SaaS call (Slack, Outlook, Salesforce, …) | Integration Service connection | § Connections below |
| Alert operators / email humans | `RaiseAlert` / `SendEmailNotification` | § Alerts & Notifications below |
| React to schedule / new queue item / manual start | Integration trigger (`TimeTrigger` / `QueueTrigger` / Manual) | [trigger-pattern-guide.md](trigger-pattern-guide.md), Common Rule 12 |
| Orchestrator API data with no matching activity | [OrchestratorHttpRequest](activity-docs/UiPath.System.Activities/26.4/activities/OrchestratorHttpRequest.md) | Robot-authenticated; relative endpoint only, no token handling |

## Assets & Credentials

| Intent | XAML activity | Coded `system` method |
|--------|---------------|----------------------|
| Read asset | [GetRobotAsset](activity-docs/UiPath.System.Activities/26.4/activities/GetRobotAsset.md) | `GetAsset(name[, folderPath, cacheStrategy, timeoutMS])` |
| Read credential | [GetRobotCredential](activity-docs/UiPath.System.Activities/26.4/activities/GetRobotCredential.md) | `GetCredential(name, ...)` → `(string userName, SecureString password)` |
| Read secret asset | [GetSecret](activity-docs/UiPath.System.Activities/26.4/activities/GetSecret.md) | — none; use `OrchestratorHTTPRequest`, or store the value as a Credential asset instead |
| Write asset | [SetAsset](activity-docs/UiPath.System.Activities/26.4/activities/SetAsset.md) | `SetAsset(value, name[, folderPath])` |
| Write credential | [SetCredential](activity-docs/UiPath.System.Activities/26.4/activities/SetCredential.md) | `SetCredential(user, password, name[, folderPath])` |
| Write secret asset | [SetSecret](activity-docs/UiPath.System.Activities/26.4/activities/SetSecret.md) | — none |

Rules:

1. Asset value types: Text / Integer / Boolean / Credential / Secret — set in Orchestrator, not in the workflow. Orchestrator restricts Secret-asset consumption to coded agents — prefer Credential assets in RPA workflows.
2. `GetRobotAsset.Value` and coded `GetAsset` return `object` — cast (`CStr` / `CInt` / `CBool`, C# `(string)`) immediately after retrieval.
3. Value scoping: Global / Per Account / Per Account–Machine (the modern "per-robot"). A non-global value must exist for the executing account(-machine) or retrieval throws at runtime; only global-valued assets can be shared across folders.
4. Cross-folder: every activity/method takes `FolderPath` (advanced/hidden property in XAML, optional parameter in coded). Default = the folder resolved from the robot/session context.
5. `SetAsset` / `SetCredential` fail for assets backed by a **read-only credential store** (Azure Key Vault read-only, CyberArk Conjur, Delinea, …) — those secrets are provisioned by the vault admin; per-account vault values resolve via the asset value's External Name.

```xml
<ui:GetRobotCredential AssetName="[&quot;SAP_Login&quot;]" Username="[sapUser]" Password="[sapPassword]" />
```

```csharp
var (user, pwd) = system.GetCredential("<CREDENTIAL_ASSET_NAME>");
```

### SecureString and log hygiene

1. `Password` / secret outputs are `SecureString`. Pass them directly to `SecureString`-typed inputs — typing activities expose secure-text input properties (see [ui-automation-guide.md](ui-automation-guide.md) for the UIA surface).
2. Convert only at the last point of use: `New System.Net.NetworkCredential(String.Empty, sapPassword).Password` (VB; same call in C#). Never store the plaintext in a workflow-scope variable.
3. `project.json` → `runtimeOptions.excludedLoggedData` (scaffolded as `["Private:*", "*password*"]`, `*`/`?` wildcards) masks logged values when the variable/argument name matches a pattern or the activity `DisplayName` is prefixed `Private:`. Keep secret-bearing variable names inside the masks (e.g. `sapPassword` matches `*password*`); extend the array (`"*token*"`, `"*apikey*"`) for other secret names — never rename a variable out of the mask's reach.
4. Masks cover **default Verbose-level logging only** — an explicit `Log Message` / `Write Line` of a value bypasses them entirely (Anti-pattern 2).

## Storage Buckets

Bucket beats local file when the output must survive the job or be read by another robot/machine. Bucket beats queue `SpecificContent` for binary or large payloads — upload to the bucket, put the **bucket path** in `SpecificContent`.

| Operation | XAML activity | Coded `system` method |
|-----------|---------------|----------------------|
| Upload | [UploadStorageFile](activity-docs/UiPath.System.Activities/26.4/activities/UploadStorageFile.md) | `UploadStorageFile(destination, fileResource, bucketName[, folderPath])` |
| Download | [DownloadStorageFile](activity-docs/UiPath.System.Activities/26.4/activities/DownloadStorageFile.md) | `DownloadStorageFile(path, bucketName[, folderPath, destination])` → `ILocalResource` |
| List | [ListStorageFiles](activity-docs/UiPath.System.Activities/26.4/activities/ListStorageFiles.md) | `ListStorageFiles(directory, bucketName[, folderPath, recursive, filter])` |
| Read text | [ReadStorageText](activity-docs/UiPath.System.Activities/26.4/activities/ReadStorageText.md) | `ReadStorageText(path, bucketName[, folderPath, encoding])` |
| Write text | [WriteStorageText](activity-docs/UiPath.System.Activities/26.4/activities/WriteStorageText.md) | `WriteStorageText(path, text, bucketName[, folderPath, encoding])` |
| Delete | [DeleteStorageFile](activity-docs/UiPath.System.Activities/26.4/activities/DeleteStorageFile.md) | `DeleteStorageFile(path, bucketName[, folderPath])` |

Behavior notes:

- XAML `UploadStorageFile`: `Destination` is the in-bucket directory; `FileName` is separate. Bucket name + `FolderPath` configure on the activity's Orchestrator scope.
- Same-name upload **overwrites silently** — list first when overwrite matters.
- `ListStorageFiles` root = empty-string directory; `filter` takes a file-name pattern.

```csharp
system.WriteStorageText("runs/<RUN_ID>/summary.txt", summary, "<BUCKET_NAME>");
var files = system.ListStorageFiles("runs", "<BUCKET_NAME>");
```

## Queue Patterns Beyond REFramework

Full transaction-loop state machine (Init/Get/Process/End) → [reframework-guide.md](reframework-guide.md). Below: queue usage outside that template.

### Dispatcher (load work)

1. Batch from a `DataTable` → [BulkAddQueueItems](activity-docs/UiPath.System.Activities/26.4/activities/BulkAddQueueItems.md); columns become `SpecificContent` keys. `CommitType`: `AllOrNothing` rolls back the batch on any failure; `ProcessAllIndependently` commits per item and returns failed rows in `Result` — inspect it. Per-item `Reference`/`DueDate`/`Priority` are documented on `AddQueueItem` only — verify reserved-column support in the installed package docs (`{PROJECT_DIR}/.local/docs/packages/UiPath.System.Activities/`) before relying on it in bulk; fallback is per-row `AddQueueItem` for metadata-bearing items.
2. Trickle / single item → [AddQueueItem](activity-docs/UiPath.System.Activities/26.4/activities/AddQueueItem.md) (status `New`); [AddTransactionItem](activity-docs/UiPath.System.Activities/26.4/activities/AddTransactionItem.md) creates the item already `In Progress` for immediate same-job processing.
3. Set a unique `Reference` per item (invoice number, case ID) — enables dedup (enforce uniqueness at queue level), lookup, and end-to-end audit. A dispatcher without `Reference` re-adds duplicates on re-run. On a unique-reference queue a duplicate add fails with `Error creating Transaction. Duplicate Reference.`; dequeuing by reference on a non-unique queue risks `No Transaction Data` concurrency errors.
4. Set `DueDate` (deadline / SLA), `DeferDate` (earliest processing), `Priority` (`High`/`Normal`/`Low`) at add time. Processing order: deadline items first (by Priority, then Deadline), then the rest (by Priority, then FIFO). Do not combine `DueDate` and `DeferDate` on one item — they are not designed to work together.

### Performer (consume work)

1. Claim one item → [GetQueueItem](activity-docs/UiPath.System.Activities/26.4/activities/GetQueueItem.md) (coded: `GetTransactionItem`) — sets `In Progress`, locks against other robots; returns `null`/nothing when the queue is empty — always branch on that.
2. Long transactions: report checkpoints via [SetTransactionProgress](activity-docs/UiPath.System.Activities/26.4/activities/SetTransactionProgress.md).
3. Close every claimed item with [SetTransactionStatus](activity-docs/UiPath.System.Activities/26.4/activities/SetTransactionStatus.md): `Successful` — write results to its `Output` dictionary (downstream reads Output, not logs); `Failed` + `ErrorType`: `Application` = transient/system fault, Orchestrator auto-retries per the queue's Auto Retry setting (1–50); `Business` = data/rule fault, never auto-retried. `Reason` required on `Failed`. Misclassifying business faults as `Application` burns retries on permanently bad data.
4. Defer an item you cannot process yet → [PostponeTransactionItem](activity-docs/UiPath.System.Activities/26.4/activities/PostponeTransactionItem.md) — do not fail it.
5. Inspect without claiming → [GetQueueItems](activity-docs/UiPath.System.Activities/26.4/activities/GetQueueItems.md) (filtered, read-only; for reporting/monitoring, not processing).

Item lifecycle: `New` → `In Progress` → `Successful` / `Failed` / `Abandoned` (~24 h stuck `In Progress`; terminal, never auto-retried) / `Retried` (application-exception failure re-queued as a fresh `New` copy carrying the same `Reference`) / `Deleted`. Postpone returns an item to `New`.

Limits and retention (cloud):

- Size caps (UTF-16 chars): `SpecificContent` 256,000 · `Output` 51,200 · `Analytics` 5,120 — oversized writes fail with `Payload Too Large`; offload to a storage bucket and reference the path.
- Completed items are permanently deleted after 30 days by default (configurable 1–180; archive-to-bucket option) — queue `Output` is not a long-term audit store.

### Reacting to new items

- New job per item → [QueueTrigger](activity-docs/UiPath.System.Activities/26.4/activities/QueueTrigger.md) as workflow trigger (placement: Common Rule 12, [trigger-pattern-guide.md](trigger-pattern-guide.md)). A design-time `QueueTrigger` in the package becomes a **package requirement** — the queue is bound at process creation, and an Orchestrator-side queue trigger cannot be added for that process.
- Trigger dispatch is throttled by Orchestrator-side settings (minimum new items to start a job; cap on pending + running jobs counted together); conditions are evaluated when items are added plus a periodic safety-net check (default every 30 min). For burst loads (bulk dispatch), size these settings with the platform admin.
- Wait in a running job → [WaitQueueItem](activity-docs/UiPath.System.Activities/26.4/activities/WaitQueueItem.md).
- Never poll with a `Delay` loop — both forms above replace it.

## Jobs & Processes

Pick by execution model — the wrong pick costs a robot license slot or blocks the calling job:

| Need | XAML activity | Coded `system` method | Semantics |
|------|---------------|----------------------|-----------|
| Run another process inline, get outputs | [InvokeProcess](activity-docs/UiPath.System.Activities/26.4/activities/InvokeProcess.md) | `InvokeProcess(Async)(processName[, folderPath, args, ...])` | Runs inside the **current** job/session; waits; returns `OutputArguments` |
| Fire-and-forget in background | [BeginProcess](activity-docs/UiPath.System.Activities/26.4/activities/BeginProcess.md) | `StartJob(processName, out jobId[, folderPath, priority])` | New Orchestrator job; caller continues immediately |
| Start a job and wait for its outputs | [RunJob](activity-docs/UiPath.System.Activities/26.4/activities/RunJob.md) | `RunJob(Async)(processName, ...)` → `(JobData, OutputJson)` | XAML form suspends the workflow — requires persistence (`supportsPersistence`); coded form waits in-process (`doNotWait` to skip) |
| Stop running jobs | [StopJob](activity-docs/UiPath.System.Activities/26.4/activities/StopJob.md) | `StopJob(job, StopStrategy[, folderPath])` | `SoftStop` lets the job honor Should Stop; kill is forced |
| List / filter jobs | [GetJobs](activity-docs/UiPath.System.Activities/26.4/activities/GetJobs.md) | `GetJobs(filter, ...)` | Read-only |
| Current job metadata | [GetCurrentJobInfo](activity-docs/UiPath.System.Activities/26.4/activities/GetCurrentJobInfo.md) | — | Job ID, process name, folder — use in logs/queue `Output` |

Rules:

1. Target process must be **deployed in the target folder** before the run — see § Provisioning.
2. Long-running loops: poll [ShouldStop](activity-docs/UiPath.System.Activities/26.4/activities/ShouldStop.md) each iteration and exit cleanly on `True` — otherwise an operator Stop becomes a Kill mid-transaction. [ReportStatus](activity-docs/UiPath.System.Activities/26.4/activities/ReportStatus.md) surfaces loop progress on the job.
3. Chain of processes each needing its own retry/audit → queue between them, not nested `InvokeProcess`.

## Connections (Integration Service)

Third-party SaaS calls (Slack, Outlook, Salesforce, Jira, …) go through Integration Service **connections** — folder-scoped resources created and authorized in Integration Service, never credentials stored by the workflow. Authoring surface: XAML connector activities → [is-connector-xaml-guide.md](is-connector-xaml-guide.md); coded `connections` service → [coded/integration-service-guide.md](coded/integration-service-guide.md); IS-based triggers need the connection's `ConnectionId` (Common Rule 12). Precondition: the connection must exist **and be authorized** before run — pre-flight `uip is connections list --output json`, health-check `uip is connections ping`.

## Alerts & Notifications

- Operator alert in Orchestrator → [RaiseAlert](activity-docs/UiPath.System.Activities/26.4/activities/RaiseAlert.md) (coded: `RaiseAlert(severity, notification[, folderPath])`).
- Email via Orchestrator Notification Service — no SMTP/connection setup → [SendEmailNotification](activity-docs/UiPath.System.Activities/26.4/activities/SendEmailNotification.md).
- Business-level process/task telemetry → [ProcessTrackingScope](activity-docs/UiPath.System.Activities/26.4/activities/ProcessTrackingScope.md) + [TrackObject](activity-docs/UiPath.System.Activities/26.4/activities/TrackObject.md) / [SetTaskStatus](activity-docs/UiPath.System.Activities/26.4/activities/SetTaskStatus.md) / [SetTraceStatus](activity-docs/UiPath.System.Activities/26.4/activities/SetTraceStatus.md).

## Provisioning & Runtime Preconditions

Resolution model: at `uip rpa run` time the activities resolve against the Orchestrator folder of the authenticated session — verify with `uip login status --output json` before running workflows that touch assets/credentials/buckets/queues. Per-call `FolderPath` overrides the session folder.

Resources must exist **before** the run; the activities create queue *items* and bucket *files*, never the queue/bucket/asset itself. On a missing resource or no connection the activity throws at runtime — report the missing resource (name, type, folder) to the user and stop; never substitute a hardcoded value.

Pre-flight and provisioning via the `uip or` CLI — probe first (`uip or assets --help`): older CLI builds do not ship these verb groups.

| Resource | Pre-flight read | Create |
|----------|----------------|--------|
| Asset | `uip or assets list --output json` / `uip or assets get-asset-value` | `uip or assets create` |
| Queue | `uip or queues list --output json` | `uip or queues create` |
| Bucket | `uip or buckets list --output json` | `uip or buckets create` |
| Bucket file | `uip or bucket-files list --output json` | `uip or bucket-files upload` |
| Queue item | `uip or queue-items list --output json` | `uip or queue-items add` |
| Process (deployed package) | `uip or processes list --output json` | `uip or processes create` (package via `uip or packages upload`) |
| Job | `uip or jobs list --output json` | `uip or jobs start` (operate: `stop` / `restart` / `resume`) |
| IS connection | `uip is connections list --output json` / `uip is connections ping` | Create + authorize in Integration Service (`uip is connections create`) |

Flags: discover per verb with `--help`. When the probe fails (verb group absent), fall back in order:

1. Solution-scoped: wrap the project in a solution and declare the resource — `uip solution resources add`.
2. `OrchestratorHttpRequest` / coded `OrchestratorHTTPRequest` against the raw Orchestrator API from a bootstrap workflow.
3. Hand off to the user/admin to create the resource in Orchestrator — state exactly what is needed (name, type, folder).

## Anti-Patterns

1. **Hardcoded secrets** in expressions, arguments, or `Config.xlsx` cells — secrets live only in credential/secret assets (Common Rule 5a). The Config Assets sheet maps *names*, not values.
2. **Logging secrets** — `Log Message` on a converted password, or copying `SecureString` plaintext into a variable whose name escapes the `excludedLoggedData` masks.
3. **Delay-poll loop on a queue** — use `QueueTrigger` (job per item) or `WaitQueueItem` (in-process wait).
4. **File content stuffed into `SpecificContent`** — upload to a storage bucket, pass the bucket path in the item.
5. **Dispatcher without unique `Reference`** — duplicates on re-run, no audit trail.
6. **`ErrorType.Application` for data faults** — bad data retries forever and still fails; classify as `Business`.
7. **Creating queues/buckets/assets from the workflow at runtime** — provision before the run (CLI/solution/admin); workflows only consume.
8. **Long-running loop that never checks `ShouldStop`** — an operator Stop escalates to Kill mid-transaction; poll it each iteration.
