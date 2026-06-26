# Troubleshooting Reference Router

Start here. Find the product or package that matches the user's issue, then follow the links to drill down into playbooks.

## Orchestrator

Manages automation resources, robots, processes, and execution. Handles job scheduling, queue management, asset storage, triggers, storage buckets, and folder-based access control. Issues here involve failed jobs, stuck jobs, queue item failures, trigger problems, robot connectivity, permissions, and platform availability.

CLI: `uip or --help`

- [products/orchestrator/overview.md](./products/orchestrator/overview.md) — Product overview, features, and dependencies
- [products/orchestrator/summary.md](./products/orchestrator/summary.md) — All playbooks for Orchestrator issues

## Runtime Exceptions

General .NET runtime exceptions originating from the user's own workflow code — not from activity packages or platform internals. Covers null references, null arguments, and similar errors in workflow logic, variable handling, and data processing.

- [runtime-exceptions/overview.md](./runtime-exceptions/overview.md) — Scope boundary, investigation sources (local logs and Orchestrator jobs)
- [runtime-exceptions/summary.md](./runtime-exceptions/summary.md) — All playbooks for runtime exception issues

## Maestro

CLI: `uip maestro --help`

Agentic orchestration platform built on Orchestrator. BPMN-based process design with human-in-the-loop tasks, AI agent tasks, and service tasks. Processes are designed in Studio Web, deployed as solutions, and managed through Maestro Instance Management. Issues here involve deployment failures, debug-vs-deploy mismatches, expression/variable errors, file handling, boundary events, parallel markers, stuck instances, and service availability.

- [products/maestro/overview.md](./products/maestro/overview.md) — Product overview, dependencies, key concepts, and features
- [products/maestro/summary.md](./products/maestro/summary.md) — All playbooks for Maestro issues

## Integration Service

Connector platform for third-party integrations (Salesforce, Outlook, SAP, Slack, etc.). Manages OAuth connections, exposes activities for automations and BPMN processes, and provides event-based triggers. Issues here involve connection failures, expired authentication, triggers not firing, and operation errors. Connection errors from Integration Service often surface through Maestro or Orchestrator as the calling product. Also covers the runtime exceptions thrown by the connector activities (`ConnectorActivity`, `ConnectorTriggerActivity`, `ConnectorHttpActivity`): `GeneralException`/`RuntimeException` with `DAP-GE-*`/`DAP-RT-*` codes, and `UiPath.Ipc`/`UiPath.CoreIpc` `RemoteException`.

Namespaces: `UiPath.IntegrationService.Activities`, `UiPath.IntegrationService.Activities.Runtime.Exceptions`

CLI: `uip is --help`

- [products/integration-service/overview.md](./products/integration-service/overview.md) — Product overview, connectors, connections, and CLI commands
- [products/integration-service/summary.md](./products/integration-service/summary.md) — All playbooks for Integration Service issues

## Agents

Low-code agents built with `uip agent`. Issues here involve LLM call failures, context grounding index misconfigurations, and input schema validation errors. Primary investigation surface: `uip traces spans get <traceId> --output json` — spans carry the full error text including error codes and field-level detail.

CLI: `uip agent run status`, `uip traces spans get`, `uip agent context`, `uip context-grounding`, `uip agent validate`, `uip agent publish`

- [products/agents/summary.md](./products/agents/summary.md) — All playbooks for Agents issues

## LLM Gateway

Service that routes agent / product LLM calls to a model — platform default or tenant-owned (BYO) provider key. Issues here involve BYO LLM product configurations failing at runtime, server-side validation probes failing on `create` / `update`, and routing being bypassed (call hits the platform default despite an active BYO record). LLM Gateway failures often surface through the consuming agent / product (agents, agenthub, jarvis, IXP) or as auth-shaped errors referencing the vendor directly (OpenAI, Azure OpenAI, Bedrock, Vertex, Anthropic). The gateway does **not** expose per-request invocation logs via CLI — diagnosis is current-state + trace-evidence only.

CLI: `uip llm-configuration --help`, `uip traces spans get`, `uip gov aops-policy deployed-policy resolve`

- [products/llm-gateway/overview.md](./products/llm-gateway/overview.md) — Service model, dependencies, CLI surface, and what the CLI does NOT expose
- [products/llm-gateway/summary.md](./products/llm-gateway/summary.md) — All playbooks for LLM Gateway / BYO LLM issues

## UI Automation

Activities for interacting with desktop and web application UIs. Robots use selectors (XML descriptors) to find and interact with UI elements. Issues here involve selector failures, element not found exceptions, timeout issues, Healing Agent problems, and data validation errors during UI interactions.

Namespaces: `UiPath.UIAutomationNext.Activities`, `UiPath.UIAutomation.Activities`, `UiPath.Core.Activities`

- [activity-packages/ui-automation/overview.md](./activity-packages/ui-automation/overview.md) — Package overview, selector mechanics, exception types, and dependencies
- [activity-packages/ui-automation/summary.md](./activity-packages/ui-automation/summary.md) — All playbooks for UI Automation issues

## Computer Vision (CV) Activities

Activities that target UI elements by visual analysis of a screenshot instead of selectors — for virtualized/Citrix/RDP, image-based, and remote desktops. Every CV activity runs inside a CV Screen Scope (`CVScope`) that screenshots the target window; a CV server (cloud or local) plus an OCR engine detects elements, the descriptor (target + anchors) is matched, and the action fires at the matched coordinates. Issues here involve element-not-found / descriptor-match failures, invalid descriptors, table cell-targeting errors, scroll-search failures, CV server auth/throttling/network errors, scope setup failures, post-find action failures, and silent/false results (`ContinueOnError` / `InRegion` suppression).

Namespaces: `UiPath.CV.Activities` (exceptions: `UiPath.CV`)

- [activity-packages/cv-activities/overview.md](./activity-packages/cv-activities/overview.md) — Package overview, CV targeting mechanics, exception types, and common failure patterns
- [activity-packages/cv-activities/summary.md](./activity-packages/cv-activities/summary.md) — All playbooks for Computer Vision Activities issues

## System Activities

Core workflow activities from `UiPath.System.Activities` that interact with Orchestrator resources at runtime — asset retrieval, credential lookup, queue operations, and storage buckets. Issues here involve asset-not-found errors, permission denied, folder scope mismatches, external vault failures, and package version bugs.

Namespaces: `UiPath.Core.Activities`

- [activity-packages/system-activities/overview.md](./activity-packages/system-activities/overview.md) — Package overview, activity types, and common failure patterns
- [activity-packages/system-activities/summary.md](./activity-packages/system-activities/summary.md) — All playbooks for System Activities issues

## Classic Activities

The classic (non-"modern"/non-"Next") activities under `UiPath.Core.Activities`. Two groups: classic UI Automation — `Click`, `Type Into`, `Send Hotkey`, `Open Browser`, `Close Tab`, `Open Application`, `Attach Browser`/`Window`, `Take Screenshot`, `Wait Image Vanish`, `Wait UI Element Appear` (selector/image based, `SelectorNotFoundException` / `ActivityTimeoutException` / `ElementOperationException` / `BrowserOperationException`); and System/Core — `Invoke Workflow File`, `Invoke Code`, `Add Queue Item`, `Rename File`, `Move File`, `Append Line`, `Log Message`, `Kill Process`, `Start Triggers`, `For Each Row` (file/process/code/queue/workflow failures). Use this package when the faulted activity is one of the classic types above. For the modern UI "Next" activities (`NClick`, `Use Application/Browser`, Healing Agent) use **UI Automation**; for `Get Asset`/`Get Credential`/`Get Robot Asset` use **System Activities**.

Namespaces: `UiPath.Core.Activities`, `UiPath.UIAutomation.Activities`, `UiPath.System.Activities`

- [activity-packages/classic-activities/overview.md](./activity-packages/classic-activities/overview.md) — Package overview, classic activity groups, and failure families
- [activity-packages/classic-activities/summary.md](./activity-packages/classic-activities/summary.md) — All playbooks for classic activity issues

## Google Workspace Activities

Activities for interacting with Google Workspace including Google Calendar, Google Drive, Google Sheets, Gmail, Google Docs, Google Tasks, and Google Forms. Issues here involve files not found, sheet name conflicts, multiple items name conflicts, emails not found, sheet cell limit exceeded, sheets invalid ranges, upload storage quota exceeded.

Namespaces: `UiPath.GSuite.Activities`

- [activity-packages/gsuite-activities/overview.md](./activity-packages/gsuite-activities/overview.md) — Package overview, activity types, and common failure patterns
- [activity-packages/gsuite-activities/summary.md](./activity-packages/gsuite-activities/summary.md) — All playbooks for Google Workspace Activities issues

## Microsoft Office 365 Activities

Activities for interacting with Microsoft Office 365 through Graph API. Issues here involve multiple items name conflicts, drive items not found, mail folders not found, emails not matching the filters, already existing item names.

Namespaces: `UiPath.MicrosoftOffice365.Activities`

- [activity-packages/o365-activities/overview.md](./activity-packages/o365-activities/overview.md) — Package overview, activity types, and common failure patterns
- [activity-packages/o365-activities/summary.md](./activity-packages/o365-activities/summary.md) — All playbooks for Microsoft Office 365 Activities issues

## Excel Activities

Desktop Excel activities from `UiPath.Excel.Activities` — read, write, delete, and manipulate `.xlsx` / `.xls` workbooks, run VBA macros (`Invoke VBA`, `Execute Macro`), and look up ranges on the host filesystem via Excel COM (Excel installed) or the OpenXML provider (Excel not required). Issues here involve workbooks locked by other processes, sheet names not found, range parsing failures, provider-specific parsing errors on heavily formatted or sensitivity-labeled files, Trust Center macro blocks, entry-method / parameter marshaling errors, COM-interop instability (`0x80010100 RPC_E_SYS_CALL_FAILED` and related HRESULTs), and Application Scope / Use Excel File container failures. For cloud Excel via Microsoft Graph, see Microsoft Office 365 Activities above.

Namespaces: `UiPath.Excel.Activities`

- [activity-packages/excel-activities/overview.md](./activity-packages/excel-activities/overview.md) — Package overview, providers, scopes, execution models, and common failure patterns
- [activity-packages/excel-activities/summary.md](./activity-packages/excel-activities/summary.md) — All playbooks for Excel Activities issues

## Word Activities

Activities for automating Microsoft Word documents on Windows. Operations run inside a `Use Word File` (`WordProcessScope`) or classic `Word Application Scope` container and drive a real WINWORD.EXE through Office Interop (COM), requiring desktop Word on the execution host. Issues span package-wide COM / host failures common to all Word activities (type library / class not registered `0x8002801D` / `0x80040154` / `REGDB_E_CLASSNOTREG`, bitness mismatch, Word busy/blocked `0x8001010A`, `WINWORD.EXE` crashing mid-operation with `RPC_E_WRONG_THREAD` `0x8001010E`); `Word Application Scope` failures (corrupted-file errors, indefinite hangs on background modal dialogs, "cannot create unknown type" load errors, document-path resolution); and `Add Picture` (`WordAddImage`)-specific failures (activity placed outside a Word scope, insertion target text/bookmark not found, invalid image path / unusable image input).

Namespaces: `UiPath.Word.Activities`

- [activity-packages/word-activities/overview.md](./activity-packages/word-activities/overview.md) — Package overview, execution models, and common failure patterns
- [activity-packages/word-activities/summary.md](./activity-packages/word-activities/summary.md) — All playbooks for Word Activities issues

## Python Activities

Activities for invoking Python from a workflow. `UiPath.Python.Activities` does not run Python in-process — `Python Scope` launches a separate Python host process and marshals objects over an IPC pipe; `Load Python Script` / `Run Python Script` / `Invoke Python Method` / `Get Python Object` call into that host. Issues here involve `Pipe is broken` / `Error invoking Python method` (the out-of-process host died — a pip module missing from the scope's interpreter, an unhandled exception, a hard `sys.exit`, or stdout flooding), `The specified Python path is not valid` (`Path` points at `python.exe` instead of the install folder, or the `WindowsApps\python` Store alias), `One or more errors occurred` / engine-init failures (`Target` bitness, `Version`, or `Library path` mismatch, or a missing .NET Desktop Runtime), and scripts that run but read/write the wrong files (relative paths resolving against the robot's per-package `WorkingFolder`).

Namespaces: `UiPath.Python.Activities`

- [activity-packages/python-activities/overview.md](./activity-packages/python-activities/overview.md) — Package overview, out-of-process execution model, and common failure patterns
- [activity-packages/python-activities/summary.md](./activity-packages/python-activities/summary.md) — All playbooks for Python Activities issues

## Database Activities

Activities for querying and modifying relational databases over ADO.NET (SQL Server, Oracle, MySQL, ODBC, OLE DB). A `DatabaseConnection` opened by `Connect to Database` / `Start Transaction` is consumed by `Execute Query`, `Execute Non Query`, `Run Command`, and the bulk/insert activities. Issues here involve null/out-of-scope connections, provider/driver mismatches after Windows-Legacy → Windows migration, SQL syntax / unsafe concatenation, query text in the connection-string field, command timeouts, `0xE0434352` CLR crashes, and using the wrong activity for the statement type.

Namespaces: `UiPath.Database.Activities`

- [activity-packages/database-activities/overview.md](./activity-packages/database-activities/overview.md) — Package overview, connection model, key activities, and common failure patterns
- [activity-packages/database-activities/summary.md](./activity-packages/database-activities/summary.md) — All playbooks for Database Activities issues

## Python Activities

Activities for running Python code from a UiPath workflow via the `UiPath.Python.Activities` package. A `Python Scope` initializes an out-of-process Python engine (bound through Python.NET) that its child activities — `Load Python Script`, `Invoke Python Method`, `Get Python Object` — run against. Issues here involve engine-initialization failures (invalid `Path`, `Target` bitness mismatch, `Library path` missing for Python > 3.9 on Windows, unsupported Python version, missing .NET Desktop Runtime 6+), script load/import errors (`ModuleNotFoundError`, top-level syntax/exception, unresolved local imports), and hangs / oversized return data. Engine-config and module errors often surface only on the robot host — the scope uses the interpreter at `Path` and Windows environment variables, not the IDE's venv/conda env.

Namespaces: `UiPath.Python.Activities`

- [activity-packages/python-activities/overview.md](./activity-packages/python-activities/overview.md) — Package overview, Python Scope execution model and properties, and common failure patterns
- [activity-packages/python-activities/summary.md](./activity-packages/python-activities/summary.md) — All playbooks for Python Activities issues

## Web Activities

Activities for outbound HTTP calls and payload deserialization. `HttpClient` (legacy, RestSharp) and `NetHttpRequest` (modern, `System.Net.Http`) issue HTTP requests; `DeserializeJson`, `DeserializeJsonArray`, and `DeserializeXml` parse a string into a typed object / `JArray` / `XDocument`. Issues here involve HTTP request failures (`System.Net.WebException` — status / DNS / connection / SSL), request timeouts (`System.TimeoutException`), null request inputs (`System.NullReferenceException`), modern-activity faults wrapped in `System.AggregateException`, malformed JSON/XML payloads (`Newtonsoft.Json.JsonReaderException` / `System.Xml.XmlException`), JSON type mismatches (`Newtonsoft.Json.JsonSerializationException`), and null/empty payloads (`System.ArgumentNullException`). These activities propagate raw framework exceptions — the faulted activity class + exception class is the discriminator. A malformed/null deserialize fault is frequently a symptom of an upstream HTTP call.

Namespaces: `UiPath.Web.Activities`

- [activity-packages/web-activities/overview.md](./activity-packages/web-activities/overview.md) — Package overview, activity families, and common failure patterns
- [activity-packages/web-activities/summary.md](./activity-packages/web-activities/summary.md) — All playbooks for Web Activities issues

## CSV Activities

The CSV file activities — `Read CSV`, `Write CSV`, `Append To CSV` (namespace `UiPath.Core.Activities`, shipped in `UiPath.System.Activities`) — read/write delimited files to and from a `DataTable` against a local path, using the bundled `CsvHelper` library. Issues here involve `CsvHelper` version conflicts (`Method not found: 'CsvHelper...'` from a `UiPath.System.Activities` ↔ `UiPath.Excel.Activities` version split — both bundle `CsvHelper`), file-access failures (`The process cannot access the file because it is being used by another process` when the CSV is open in Excel; `The filename, directory name, or volume label syntax is incorrect` from an invalid or raw `https://` cloud path — these activities are local-file only), and `DataTable` shape problems (uninitialized table, or a column count/header mismatch vs the existing file).

Namespaces: `UiPath.Core.Activities`

- [activity-packages/csv-activities/overview.md](./activity-packages/csv-activities/overview.md) — Package overview, execution model, and common failure patterns
- [activity-packages/csv-activities/summary.md](./activity-packages/csv-activities/summary.md) — All playbooks for CSV Activities issues


## Playbooks

All playbooks use the same headers: `## Context`, `## Investigation` (optional), `## Resolution` (optional). They vary by confidence level:

| Confidence | What you know | Investigation | Example |
|---|---|---|---|
| **High** | Exact error → exact cause | Quick verification | "GetAsset" error → asset missing |
| **Medium** | Specific error → known troubleshooting path | Concrete steps | SSL cert invalid → check cert, chain, trust |
| **Low** | General symptoms → multiple causes | General guidance or absent | Robot unresponsive → could be heartbeat, network, or machine issue |

Template and full guide: [templates/playbook-template.md](./templates/playbook-template.md) | [knowledge-base-guide.md](./knowledge-base-guide.md)
