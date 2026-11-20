# Domain Catalog

Domain descriptions, namespaces, and CLI entry points. Runtime routing greps the playbook corpus directly (SKILL.md §4). Use this catalog to cross-check a (system, entity) classification, map exception namespaces to owning packages, browse a domain's playbook index during escalation, and route silent failures via the no-signature table.

## Orchestrator

Manages automation resources, robots, processes, execution, scheduling, queues, assets, triggers, storage buckets, and folder access. Covers failed/stuck jobs, queue-item and trigger failures, robot connectivity, permissions, and platform availability.

CLI: `uip or --help`

- [products/orchestrator/overview.md](./products/orchestrator/overview.md) — Product overview, features, and dependencies
- [products/orchestrator/summary.md](./products/orchestrator/summary.md) — All playbooks for Orchestrator issues

## Studio

UiPath Studio Desktop/Web authoring IDE. Covers platform failures, not workflow-code or activity faults: license acquisition (License Provider = Orchestrator), Studio/StudioX entitlement, and Autopilot for developers, including "No license exist for this installation", Autopilot greyed out/"disabled by your organization", and tenant-service gaps. For `.xaml`/`.cs` authoring and activity faults use UI Automation / System Activities / Runtime Exceptions; for agent/product LLM routing use LLM Gateway.

CLI: `uip login status`, `uip admin tenants get`, `uip admin tenants services enable`, `uip platform users licenses get`

- [products/studio/overview.md](./products/studio/overview.md) — Profiles, license acquisition, Autopilot, tenant-service dependencies, and CLI surface
- [products/studio/summary.md](./products/studio/summary.md) — All playbooks for Studio issues

## Runtime Exceptions

General .NET runtime exceptions from user workflow code, not activity packages or platform internals: null references; null/invalid/out-of-range arguments; invalid operations (LINQ, nullable, enumeration); `If` compiler/type errors including `Compiler error(s) encountered processing expression` and `Option Strict On disallows implicit conversions`; silent wrong-branch `If` faults; `Assign` design-time mismatches including `Cannot assign from type 'System.Object' to 'System.String'`; LINQ `CopyToDataTable` "source contains no data rows"; missing files/directories; out-of-bounds indexes; and missing dictionary keys in workflow logic, variables, and data processing.

- [runtime-exceptions/overview.md](./runtime-exceptions/overview.md) — Scope boundary, investigation sources (local logs and Orchestrator jobs)
- [runtime-exceptions/summary.md](./runtime-exceptions/summary.md) — All playbooks for runtime exception issues

## Maestro

CLI: `uip maestro --help`

Agentic orchestration on Orchestrator: BPMN processes designed in Studio Web, deployed as solutions, and managed through Maestro Instance Management; supports human-in-the-loop, AI-agent, and service tasks. Covers deployment failures, debug/deploy mismatches, expression/variable errors, file handling, boundary events, parallel markers, stuck instances, and service availability.

- [products/maestro/overview.md](./products/maestro/overview.md) — Product overview, dependencies, key concepts, and features
- [products/maestro/summary.md](./products/maestro/summary.md) — All playbooks for Maestro issues

## Integration Service

Third-party connector platform (Salesforce, Outlook, SAP, Slack, etc.) managing OAuth connections, automation/BPMN activities, and event triggers. Covers connection/authentication, expired credentials, trigger, and operation failures, including connector activity exceptions: `ConnectorActivity`, `ConnectorTriggerActivity`, `ConnectorHttpActivity`; `GeneralException`/`RuntimeException` with `DAP-GE-*`/`DAP-RT-*`; `UiPath.Ipc`/`UiPath.CoreIpc` `RemoteException`; and Connection Service HTTP API `CNS…` codes for connections/connectors/triggers CRUD, permissions, event callbacks, and Solutions installs. Errors may surface through Maestro or Orchestrator.

Namespaces: `UiPath.IntegrationService.Activities`, `UiPath.IntegrationService.Activities.Runtime.Exceptions`

CLI: `uip is --help`

- [products/integration-service/overview.md](./products/integration-service/overview.md) — Product overview, connectors, connections, and CLI commands
- [products/integration-service/dap-error-codes-reference.md](./products/integration-service/dap-error-codes-reference.md) — DAP runtime error-code catalog, telemetry customEvent fields, retry semantics, code → playbook map
- [products/integration-service/cns-error-codes-reference.md](./products/integration-service/cns-error-codes-reference.md) — CNS (Connection Service API) error-code catalog: wire format, fault buckets, overloaded-code traps, retry semantics, code → playbook map
- [products/integration-service/summary.md](./products/integration-service/summary.md) — All playbooks for Integration Service issues

## API Workflows

Studio Web JSON workflows (Serverless Workflow DSL) run by `uip api-workflow run` and publish to Orchestrator as API processes/jobs; they have no UI automation, robot, or agent runtime. Covers expression/undefined-output/loop/logic faults, connector 401/403, designer-roundtrip corruption, and pack/publish/deploy failures. Cloud 401 means wrong activity kind or stale connection binding; 403 means broken/disabled/under-scoped Integration Service connection. Also diagnose absent job records (trigger off/old release/dead event connection/no caller), limits (Script 10-second budget, loop `limit`, 15-minute serverless job limit), and outbound IP-route blocking. Connection faults belong to Integration Service; job/trigger mechanics to Orchestrator.

CLI: `uip api-workflow validate`, `uip api-workflow run --no-auth`, `uip is connections ping`, `uip or jobs get`/`logs`, `uip or triggers list`/`history`, `uip traces spans get --job-key`

- [products/api-workflows/overview.md](./products/api-workflows/overview.md) — Product overview, dependencies, evidence surfaces, and fault families
- [products/api-workflows/summary.md](./products/api-workflows/summary.md) — All playbooks for API Workflow issues

## Agents

Low-code agents built with `uip agent`; covers LLM failures, context-grounding index misconfiguration, and input-schema validation. Primary evidence: `uip traces spans get <traceId> --output json`, whose spans contain full error text, codes, and field detail.

CLI: `uip traces spans get`, `uip context-grounding`, `uip agent refresh`, `uip agent validate`, `uip agent debug` (run only with explicit user approval because it uploads and executes the agent)

- [products/agents/summary.md](./products/agents/summary.md) — All playbooks for Agents issues

## LLM Gateway

Routes agent/product LLM calls to platform-default or tenant-owned (BYO) providers. Covers BYO runtime failures, server-side `create`/`update` validation-probe failures, and bypassed routing to the platform default. Failures may surface through agents, agenthub, jarvis, IXP, or vendor-shaped auth errors (OpenAI, Azure OpenAI, Bedrock, Vertex, Anthropic). The gateway exposes no per-request invocation logs via CLI; use current state plus trace evidence.

CLI: `uip llm-configuration --help`, `uip traces spans get`, `uip gov aops-policy deployed-policy resolve`

- [products/llm-gateway/overview.md](./products/llm-gateway/overview.md) — Service model, dependencies, CLI surface, and what the CLI does NOT expose
- [products/llm-gateway/summary.md](./products/llm-gateway/summary.md) — All playbooks for LLM Gateway / BYO LLM issues

## Coded Apps

Custom TypeScript/React web fronts and Action Center form apps using `@uipath/uipath-typescript`, built/shipped with `uip codedapp`. Browser-runtime failures are OAuth (`redirect_uri_mismatch`, `invalid_scope`), HTTP 401/403/404, CORS, or broken deployed URLs—not faulted jobs/traces. `uipath.json` requests permissions; `uip admin external-apps` controls backing External Application redirect URIs/scopes. Diagnose from `uipath.json`, `uip admin external-apps get <client-id>`, `.uipath/app.config.json`, `vite.config.ts`, and reported signatures; no runtime job/trace/log CLI.

CLI: `uip codedapp --help`, `uip admin external-apps get <client-id>`

- [products/coded-apps/overview.md](./products/coded-apps/overview.md) — Runtime/auth model (PKCE public client), CLI surface, and evidence sources
- [products/coded-apps/summary.md](./products/coded-apps/summary.md) — All playbooks for Coded Apps issues

## Assistant (Desktop)

UiPath Assistant Windows desktop app (Electron host plus native .NET Robot service) handles sign-in, Orchestrator connection, and process starts. Diagnose exported `ExportDiagnoseArchive` using `combined.log` (Electron/main-process IPC/UI state) and `Robot.log` (native sign-in/connect/package work, machine-local time with offset). Covers sign-in, Orchestrator connection, missing/nonstarting processes, and crashes. No `uip` job/trace/log surface. Cross-reference Orchestrator (`401`/`403`, assignment, license), Identity/cloud (OAuth on `/identity_`/`/discovery_`), and NuGet feeds (`NU1101`).

Exception namespaces: `UiPath.Service.*`, `UiPath.RobotJS.*`

- [products/assistant/overview.md](./products/assistant/overview.md) — Two-log architecture, evidence model, dependencies, and flow attribution
- [products/assistant/summary.md](./products/assistant/summary.md) — All playbooks for UiPath Assistant desktop issues

## UI Automation

Desktop/web UI activities using XML selectors. Covers selector failures, missing elements, timeouts, Healing Agent, and interaction data validation.

Namespaces: `UiPath.UIAutomationNext.Activities`, `UiPath.UIAutomation.Activities`, `UiPath.Core.Activities`

- [activity-packages/ui-automation/overview.md](./activity-packages/ui-automation/overview.md) — Package overview, selector mechanics, exception types, and dependencies
- [activity-packages/ui-automation/summary.md](./activity-packages/ui-automation/summary.md) — All playbooks for UI Automation issues

## Computer Vision (CV) Activities

Screenshot/visual-analysis activities for virtualized/Citrix/RDP, image-based, and remote desktops. Every CV activity runs in `CVScope`, which screenshots the target; cloud/local CV server plus OCR detects elements; descriptor target/anchors match; action fires at coordinates. Covers element-not-found/descriptor-match, invalid descriptors, table-cell targeting, scroll-search, server auth/throttling/network, scope setup, post-find action, and silent/false results from `ContinueOnError`/`InRegion`.

Namespaces: `UiPath.CV.Activities` (exceptions: `UiPath.CV`)

- [activity-packages/cv-activities/overview.md](./activity-packages/cv-activities/overview.md) — Package overview, CV targeting mechanics, exception types, and common failure patterns
- [activity-packages/cv-activities/summary.md](./activity-packages/cv-activities/summary.md) — All playbooks for Computer Vision Activities issues

## OCR Activities

Low-level `UiPath.OCR.Activities` engines (Screen OCR, Document OCR cloud/local, CJK/Extended Languages OCR via Document Understanding), consumed by DU `Digitize` and CV scopes. Covers missing local-server/CoreIPC packages, companion-version incompatibility, invalid API key/endpoint/CJK configuration, timeouts/invalid responses, invalid or missing images, unsupported rotation, wrong scrape use, and empty/silent results. DU pipeline belongs to Document Understanding; CV targeting to Computer Vision.

Namespaces: `UiPath.OCR.Activities` (exceptions: `OCRException` with `OCRResultCode`)

- [activity-packages/ocr-activities/overview.md](./activity-packages/ocr-activities/overview.md) — Package overview, engines, local-server modes, and failure families
- [activity-packages/ocr-activities/summary.md](./activity-packages/ocr-activities/summary.md) — All playbooks for OCR Activities issues

## System Activities

Core `UiPath.System.Activities` families: Orchestrator resources (assets, credentials, queues, storage buckets: missing assets, permissions, folder scope, vault failures, package bugs) and local runtime (`Compress/Extract Files` → `CompressionException`; modern StudioX `Copy/Move/Rename/Delete` → `FileSystemException`; `Download File from URL` / `Wait for Download`). Classic `Rename/Move File`, `Kill Process`, `Invoke Code/Workflow File`, and `Add Queue Item` belong to Classic Activities.

Namespaces: `UiPath.Core.Activities`, `UiPath.System.Activities`

- [activity-packages/system-activities/overview.md](./activity-packages/system-activities/overview.md) — Package overview, activity types, and common failure patterns
- [activity-packages/system-activities/summary.md](./activity-packages/system-activities/summary.md) — All playbooks for System Activities issues

## Classic Activities

Classic non-modern/non-Next `UiPath.Core.Activities`: UI (`Click`, `Type Into`, `Send Hotkey`, `Open Browser`, `Close Tab`, `Open Application`, `Attach Browser`/`Window`, `Take Screenshot`, `Wait Image Vanish`, `Wait UI Element Appear`) with selector/image failures `SelectorNotFoundException` / `ActivityTimeoutException` / `ElementOperationException` / `BrowserOperationException`; and System/Core (`Invoke Workflow File`, `Invoke Code`, `Add Queue Item`, `Rename File`, `Move File`, `Append Line`, `Log Message`, `Kill Process`, `Start Triggers`, `For Each Row`) with file/process/code/queue/workflow failures. Use this package for those faulted activities. Modern Next activities (`NClick`, `Use Application/Browser`, Healing Agent) use UI Automation; `Get Asset`/`Get Credential`/`Get Robot Asset` use System Activities.

Namespaces: `UiPath.Core.Activities`, `UiPath.UIAutomation.Activities`, `UiPath.System.Activities`

- [activity-packages/classic-activities/overview.md](./activity-packages/classic-activities/overview.md) — Package overview, classic activity groups, and failure families
- [activity-packages/classic-activities/summary.md](./activity-packages/classic-activities/summary.md) — All playbooks for classic activity issues

## Google Workspace Activities

Google Calendar, Drive, Sheets, Gmail, Docs, Tasks, and Forms activities. Covers files not found, sheet-name conflicts, multiple-item name conflicts, emails not found, sheet cell limits, invalid ranges, and upload storage quota.

Namespaces: `UiPath.GSuite.Activities`

- [activity-packages/gsuite-activities/overview.md](./activity-packages/gsuite-activities/overview.md) — Package overview, activity types, and common failure patterns
- [activity-packages/gsuite-activities/summary.md](./activity-packages/gsuite-activities/summary.md) — All playbooks for Google Workspace Activities issues

## Microsoft Office 365 Activities

Graph API activities covering multiple-item name conflicts, missing drive items/mail folders, nonmatching email filters, and existing item names.

Namespaces: `UiPath.MicrosoftOffice365.Activities`

- [activity-packages/o365-activities/overview.md](./activity-packages/o365-activities/overview.md) — Package overview, activity types, and common failure patterns
- [activity-packages/o365-activities/summary.md](./activity-packages/o365-activities/summary.md) — All playbooks for Microsoft Office 365 issues

## Mail Activities (classic)

Classic direct-to-mail Robot packages: Outlook desktop COM (`UiPath.Mail.Outlook.Activities`: `Send Outlook Mail Message`, `Get Outlook Mail Messages`, `Move Outlook Mail Message`, `Reply To Outlook Mail Message`) and SMTP/IMAP/POP3/Exchange. Distinct from Graph/OAuth Office 365 and Google Workspace. Covers COM cast/library registration (`REGDB_E_CLASSNOTREG`, `TYPE_E_LIBNOTREGISTERED`), missing/unregistered Outlook, bitness, orphaned `OUTLOOK.EXE`; hangs/timeouts from hidden prompts, Work Offline, slow first launch (fragile on unattended Robots); and null To/Subject/Body/attachment paths causing `Object reference not set to an instance of an object`.

Namespaces: `UiPath.Mail.Outlook.Activities`, `UiPath.Mail.SMTP.Activities`, `UiPath.Mail.IMAP.Activities`, `UiPath.Mail.POP3.Activities`, `UiPath.Mail.EWS.Activities`

- [activity-packages/mail-activities/overview.md](./activity-packages/mail-activities/overview.md) — Package overview, Outlook COM execution model, and common failure patterns
- [activity-packages/mail-activities/summary.md](./activity-packages/mail-activities/summary.md) — All playbooks for classic Mail Activities issues

## Excel Activities

Desktop `UiPath.Excel.Activities` reads/writes/deletes/manipulates `.xlsx`/`.xls`, invokes VBA (`Invoke VBA`, `Execute Macro`), and looks up ranges through Excel COM (Excel installed) or OpenXML (not required). Covers locks, missing sheets, range parsing, provider parsing on heavily formatted/sensitivity-labeled files, Trust Center macro blocks, entry-method/parameter marshaling, COM instability (`0x80010100 RPC_E_SYS_CALL_FAILED` and related HRESULTs), and Application Scope/Use Excel File failures. Cloud Graph Excel belongs to Microsoft Office 365 Activities.

Namespaces: `UiPath.Excel.Activities`

- [activity-packages/excel-activities/overview.md](./activity-packages/excel-activities/overview.md) — Package overview, providers, scopes, execution models, and common failure patterns
- [activity-packages/excel-activities/summary.md](./activity-packages/excel-activities/summary.md) — All playbooks for Excel Activities issues

## Word Activities

Windows Word activities run in `Use Word File` (`WordProcessScope`) or classic `Word Application Scope` through `WINWORD.EXE` COM, requiring desktop Word. Covers type-library/class registration `0x8002801D` / `0x80040154` / `REGDB_E_CLASSNOTREG`, bitness, Word busy `0x8001010A`, crashes with `RPC_E_WRONG_THREAD`/`0x8001010E`; scope corrupted files, modal-dialog hangs, "cannot create unknown type", path resolution; and `Add Picture`/`WordAddImage` outside scope, missing target text/bookmark, or invalid image input.

Namespaces: `UiPath.Word.Activities`

- [activity-packages/word-activities/overview.md](./activity-packages/word-activities/overview.md) — Package overview, execution models, and common failure patterns
- [activity-packages/word-activities/summary.md](./activity-packages/word-activities/summary.md) — All playbooks for Word Activities issues

## Python Activities

`UiPath.Python.Activities` uses an out-of-process Python host and IPC pipe: `Python Scope` launches it; `Load Python Script` / `Run Python Script` / `Invoke Python Method` / `Get Python Object` call it. Covers `Pipe is broken` / `Error invoking Python method` from host death (missing pip module, unhandled exception, hard `sys.exit`, stdout flooding); `The specified Python path is not valid` (`Path` points at `python.exe` instead of the install folder, or at the `WindowsApps\python` Store alias); `One or more errors occurred`/engine-init from `Target`, `Version`, `Library path`, or missing .NET Desktop Runtime; and wrong files from relative paths resolving under robot per-package `WorkingFolder`.

Namespaces: `UiPath.Python.Activities`

- [activity-packages/python-activities/overview.md](./activity-packages/python-activities/overview.md) — Package overview, out-of-process execution model, and common failure patterns
- [activity-packages/python-activities/summary.md](./activity-packages/python-activities/summary.md) — All playbooks for Python Activities issues

## Database Activities

ADO.NET relational database activities (SQL Server, Oracle, MySQL, ODBC, OLE DB). `DatabaseConnection` from `Connect to Database` / `Start Transaction` feeds `Execute Query`, `Execute Non Query`, `Run Command`, and bulk/insert activities. Covers null/out-of-scope connections, provider/driver mismatch after Windows-Legacy → Windows migration, SQL syntax/unsafe concatenation, query text in the connection-string field, timeouts, `0xE0434352` CLR crashes, and wrong activity for statement type.

Namespaces: `UiPath.Database.Activities`

- [activity-packages/database-activities/overview.md](./activity-packages/database-activities/overview.md) — Package overview, connection model, key activities, and common failure patterns
- [activity-packages/database-activities/summary.md](./activity-packages/database-activities/summary.md) — All playbooks for Database Activities issues

## Web Activities

`HttpClient` (legacy, RestSharp) and `NetHttpRequest` (modern, `System.Net.Http`) make HTTP calls; `DeserializeJson`, `DeserializeJsonArray`, and `DeserializeXml` parse string to typed object/`JArray`/`XDocument`. Covers `System.Net.WebException` status/DNS/connection/SSL failures, `System.TimeoutException`, `System.NullReferenceException`, modern `System.AggregateException`, malformed JSON/XML (`Newtonsoft.Json.JsonReaderException` / `System.Xml.XmlException`), JSON type mismatch (`Newtonsoft.Json.JsonSerializationException`), and null/empty payload (`System.ArgumentNullException`). Raw framework exceptions propagate; faulted activity class plus exception class discriminates. Deserialize failure may reflect upstream HTTP failure.

Namespaces: `UiPath.Web.Activities`

- [activity-packages/web-activities/overview.md](./activity-packages/web-activities/overview.md) — Package overview, activity families, and common failure patterns
- [activity-packages/web-activities/summary.md](./activity-packages/web-activities/summary.md) — All playbooks for Web Activities issues

## Jira Activities

Classic `UiPath.Jira.Activities` targets Jira Cloud through RestSharp. Every operation runs in `JiraApplicationScope` and child Get Issue/Search Issues/Create Issue/Add Comment calls its session. Covers invalid authentication from `Api Token` as `String` not `SecureString`, `Username` as accountId not email, conflicting `Client Id`/`Client Secret` with `Authentication Type = Api Token`, or basic password under MFA/SSO; child `Response was not recognized as JSON`/HTTP `500` from appended `/secure/Dashboard.jspa` or project path, or unsupported Server/Data Center; and missing/unloadable activity from transitive RestSharp conflict (resolve pin or migrate to Integration Service Jira connector).

Namespaces: `UiPath.Jira.Activities`

- [activity-packages/jira-activities/overview.md](./activity-packages/jira-activities/overview.md) — Package overview, Jira Scope execution model and properties, and common failure patterns
- [activity-packages/jira-activities/summary.md](./activity-packages/jira-activities/summary.md) — All playbooks for Jira Activities issues

## App Events (Workflow Events) Activities

Internal `[Internal]` activities connect a UiPath App/Studio Web preview to its robot workflow; users do not place them. App-invoked jobs expose `HandleAppRequest`, `AppRequestTrigger`, or `InitializeHubConnection` in errors/traces. RobotJS uses a legacy local pipe; SignalR uses a modern hub. Raw .NET exceptions discriminate: `HandleAppRequest` `NullReferenceException` (workflow null dereference), `AppRequestTrigger` `TimeoutException`/`IOException`/`InvalidOperationException` (channel/transport loss), and `InitializeHubConnection` `AggregateException` (unwrap inner SignalR failure).

Namespaces: `UiPath.WorkflowEvents.Activities`

- [activity-packages/workflowevents-activities/overview.md](./activity-packages/workflowevents-activities/overview.md) — Package overview, connection modes, activity types, and common failure patterns
- [activity-packages/workflowevents-activities/summary.md](./activity-packages/workflowevents-activities/summary.md) — All playbooks for App Events (Workflow Events) Activities issues

## CSV Activities

`Read CSV`, `Write CSV`, `Append To CSV` (`UiPath.Core.Activities`, shipped in `UiPath.System.Activities`) exchange local delimited files and `DataTable` using bundled `CsvHelper`. Covers `CsvHelper` version conflict (`Method not found: 'CsvHelper...'`) between `UiPath.System.Activities` and `UiPath.Excel.Activities`, file locks/open Excel, invalid/raw `https://` paths (local-file only), and uninitialized or header/column-mismatched `DataTable`.

Namespaces: `UiPath.Core.Activities`

- [activity-packages/csv-activities/overview.md](./activity-packages/csv-activities/overview.md) — Package overview, execution model, and common failure patterns
- [activity-packages/csv-activities/summary.md](./activity-packages/csv-activities/summary.md) — All playbooks for CSV Activities issues

## File Operations Activities

Modern `UiPath.Activities.System.FileOperations` (`UiPath.System.Activities`) currently covers `Download File from URL` (`DownloadFileFromUrl`), native HTTP(S) to local filesystem without browser cookies/session. Covers `This instance has already started one or more requests` from reusing the internal client in `For Each`, HTTP `401`/`403` for authenticated/portal URLs or blocked `User-Agent`, stuck `.tmp` files from download/finalize race, and `Don't know about such a host` from DNS/firewall/SSL inspection.

Namespaces: `UiPath.Activities.System.FileOperations`

- [activity-packages/file-operations/overview.md](./activity-packages/file-operations/overview.md) — Package overview, Download File from URL execution model, and common failure patterns
- [activity-packages/file-operations/summary.md](./activity-packages/file-operations/summary.md) — All playbooks for File Operations issues

## Slack Activities (Integration Service)

Slack Integration Service activities (Send Message, Get User by Email, related BAF connector activities) resolve OAuth connection then call Slack Web API. Connection phase: `System.AggregateException` wrapping `ConnectionException` (deleted/invalid connection or transient 503). API phase: `UiPath.BAF.Infrastructure.Exceptions.BusinessActivityExecutionException` with Slack errors `invalid_arguments`/missing `channel`, `channel_not_found`, `not_in_channel`, `invalid_auth`. Legacy `UiPath.Slack.Activities`/`SlackScope` is a different path.

Namespaces: `UiPath.Slack.IntegrationService.Activities`

- [activity-packages/slack-activities/overview.md](./activity-packages/slack-activities/overview.md) — Package overview, connection-vs-API phase model, and common failure patterns
- [activity-packages/slack-activities/summary.md](./activity-packages/slack-activities/summary.md) — All playbooks for Slack Integration Service Activities issues

## Terminal Activities

Terminal/mainframe emulators (IBM 3270/5250 via EHLLAPI, VT, others) run in `TerminalSession`, which opens a new/reused connection, executes child screen interactions, and closes. Covers unreachable host/wrong port/provider, missing provider runtime, connect/wait timeout, stale reuse, `TerminalConnectionException` (`System.Exception`) with `... | ResultCode=<code> | ConnectionStatus=<status>`, async `System.AggregateException`, and masking `System.NullReferenceException`.

Namespaces: `UiPath.Terminal.Activities`

- [activity-packages/terminal-activities/overview.md](./activity-packages/terminal-activities/overview.md) — Package overview, session connection model, and common failure patterns
- [activity-packages/terminal-activities/summary.md](./activity-packages/terminal-activities/summary.md) — All playbooks for Terminal Activities issues

## PDF Activities

Local PDF activities: `Read PDF Text`, `Read PDF With OCR`, `Extract PDF Page Range`, `Extract Images/Attachments From PDF`, `Export PDF Page As Image`, `Merge PDF Files` / `Join PDFs`, `Create PDF From Images`, `Manage PDF Password`. No network/Orchestrator call except OCR engine for `Read PDF With OCR`. Covers missing/non-PDF/encrypted/corrupt inputs and invalid page/password/image arguments; validation `System.ArgumentException`/`ArgumentNullException` with fixed resource string; reader `UiPath.PDF.PdfException` (wrong/missing password, `Invalid input stream`) or `UiPath.PDF.ImageToPdfException`.

Namespaces: `UiPath.PDF.Activities` (exceptions: `UiPath.PDF`)

- [activity-packages/pdf-activities/overview.md](./activity-packages/pdf-activities/overview.md) — Package overview, validation-vs-reader exception shapes, and common failure patterns
- [activity-packages/pdf-activities/summary.md](./activity-packages/pdf-activities/summary.md) — All playbooks for PDF Activities issues

## SAP BAPI Activities

Direct SAP BAPI/RFC calls over SAP .NET Connector (RFC, no SAP GUI): `SAP Application Scope`, `Invoke BAPI`, `Open`/`Close SAP Connection`. Opens RFC from parameters, resolves interface, invokes BAPI. Covers `Connection could not be created.`, `Cannot create sap connection, connection info params are not set`, `Missing mandatory field: <field> for connection`, `Advanced Parameters has invalid parameter <param>...`, `System.TimeoutException`; lookup/naming `Function: <name> could not be created`, `BAPI name is null or empty`; and `Unsupported BAPI. Contains nested complex types.` Cannot reproduce without live SAP.

Namespaces: `UiPath.SAP.BAPI.Activities` (exceptions: `UiPath.SAP.BAPI.Utilities.SapActivityException`, `UiPath.SAP.BAPI.SapBapiExceptions.UnSupportedBapiException`)

- [activity-packages/sap-bapi-activities/overview.md](./activity-packages/sap-bapi-activities/overview.md) — Package overview, connection-vs-invoke phases, exception types, and common failure patterns
- [activity-packages/sap-bapi-activities/summary.md](./activity-packages/sap-bapi-activities/summary.md) — All playbooks for SAP BAPI Activities issues

## Intelligent OCR / Document Understanding (Classic) Activities

Classic `UiPath.IntelligentOCR.Activities`: `Digitize Document`, `Classify Document Scope`, `Data Extraction Scope`, `Present Validation Station`, `Export Extraction Results`, and Train scopes. Digitize → classify → extract → validate → export combines local taxonomy/extractor settings with DU endpoint/API-key/license and Orchestrator storage. Covers `DUApiException` HTTP license/page-unit/request-size/wrong-endpoint rejection, tenant errors `Failed to fetch Document Understanding projects list...` and `Couldn't retrieve a tenant key.`, missing bucket/taxonomy/folder, and `DocumentRejectedByUserException`. Modern DU/IXP uses IXP; generally requires licensed endpoint, OCR, and trained models.

Namespaces: `UiPath.IntelligentOCR.Activities` (exceptions: `UiPath.SmartData.Utils.DocumentUnderstandingClient.DUApiException`, `UiPath.IntelligentOCR.Exceptions.DocumentRejectedByUserException`)

- [activity-packages/intelligent-ocr-activities/overview.md](./activity-packages/intelligent-ocr-activities/overview.md) — Package overview, pipeline phases, exception types, and common failure patterns
- [activity-packages/intelligent-ocr-activities/summary.md](./activity-packages/intelligent-ocr-activities/summary.md) — All playbooks for Intelligent OCR / Document Understanding Activities issues

## IPC Activities

Same-host inter-process activities: `Broadcast Message` / `Send Message` publish on named **channel**; `Message Receiver Trigger` listens in a parallel process. Local named pipe is limited to the **same robot, same Windows user, same session, same machine**. `System.TimeoutException` (`Timeout of <N> ms has passed and no channel was found to send the message to.`) means no receiver before timeout, channel mismatch, or too-low `Timeout`; `System.UnauthorizedAccessException` (`Access to the path is denied.`) means pipe ACL rejection across session/user/elevation. Faulted activity plus exception class discriminates; `System.*` prefix alone does not route here. Internal `UiPath.Ipc`/`UiPath.CoreIpc` connector transport (`RemoteException`, `DAP-*`) belongs to Integration Service.

Namespaces: `UiPath.IPC.Activities`

- [activity-packages/ipc-activities/overview.md](./activity-packages/ipc-activities/overview.md) — Package overview, channel / named-pipe execution model, and common failure patterns
- [activity-packages/ipc-activities/summary.md](./activity-packages/ipc-activities/summary.md) — All playbooks for IPC Activities issues

## Playbooks

All playbooks use `## Context`, optional `## Investigation`, and optional `## Resolution`. Confidence levels:

| Confidence | What you know | Investigation | Example |
|---|---|---|---|
| **High** | Exact error → exact cause | Quick verification | "GetAsset" error → asset missing |
| **Medium** | Specific error → known troubleshooting path | Concrete steps | SSL cert invalid → check cert, chain, trust |
| **Low** | General symptoms → multiple causes | General guidance or absent | Robot unresponsive → could be heartbeat, network, or machine issue |

Template and full guide: [templates/playbook-template.md](./templates/playbook-template.md) | [knowledge-base-guide.md](./knowledge-base-guide.md)

## No-signature routing

For no-exception/no-code silent failures, hangs, or wrong results, map the symptom to a domain and check its `summary.md` silent playbook:

| Symptom | Domain | Entry |
|---|---|---|
| Job/run Successful but action had no effect or output is wrong | Acting activity's package (ui-automation, classic, word, excel, gsuite, o365, database, system) | Activity trace logs: zero-count lines ("Replaced 0 occurrence"), Simulate/inert-verify settings, provider quirks |
| Job stuck Pending | orchestrator | `PendingReasons` on job record—codes are greppable signatures; re-grep after fetching |
| Job/instance stuck Running | orchestrator (plain job) / maestro (BPMN instance) | Child-job states + open incidents; Open Maestro incident blocks the instance until resolved |
| Works in Debug, fails deployed | maestro | Debug-vs-deploy silent playbook |
| Published API workflow "didn't run"—no job record | api-workflows | Check trigger and `uip or triggers history`, or caller one step upstream |
| API workflow stops without error, or loop returns short | api-workflows | Platform limit: Script 10 s budget, loop `limit` (logs `reached iteration limit`), or 15-minute serverless limit; `validate` cannot see them |
| API workflow call to firewalled host times out, connection pings healthy | api-workflows | Wrong outbound IP range; serverless robots and Integration Service use different routes |
| Duplicate task/element executions | maestro | Boundary-event silent playbook |
| Traces/evidence missing or disappearing | maestro / orchestrator retention | Silent playbooks; retention windows |
| Robot unresponsive, heartbeat gaps | orchestrator | Machine/session state via orchestrator investigation guide |
| Hang mid-activity, no fault, no timeout | Activity's package | Package overview common failure patterns (e.g., Word background modal dialogs, Python stdout flooding) |
| Reads/writes wrong files with no error | Activity's package | Relative-path quirks (e.g., Python per-package `WorkingFolder`) |
| Slowness/degradation without errors | Owning product | Product overview + `uip docsai ask` |

Cross-domain rule: the reporting surface may differ from ownership. Extract entity keys from fetched records, follow them one hop, then settle on a domain.
