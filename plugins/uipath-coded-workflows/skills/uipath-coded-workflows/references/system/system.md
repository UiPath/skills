# System Activities API Reference

Reference for the `system` service from `UiPath.System.Activities` package.

**Required package:** `"UiPath.System.Activities": "[25.12.2]"`

**Auto-imported namespaces:** `System`, `System.Collections.Generic`, `System.Data`, `UiPath.Core`, `UiPath.Core.Activities.Storage`, `UiPath.Orchestrator.Client.Models`, `UiPath.Activities.System.Jobs.Coded`

**Service accessor:** `system` (type `ISystemService`)

---

## Overview

The System API provides coded workflow access to system-level operations including file management, Orchestrator integration (queues, assets, credentials, jobs, storage buckets), DataTable manipulation, text processing, and date/time operations. The main entry point is `ISystemService`, accessed via the `system` service accessor.

### API Categories

| Category | Description | Reference |
|---|---|---|
| **File Operations** | Copy, create, delete, move, read, write files and folders | [windows-api.md - File Operations](windows-api.md#file-operations) |
| **Archive/Compression** | Zip and unzip files | [windows-api.md - Archive](windows-api.md#archivecompression) |
| **DataTable Operations** | Add/remove rows, sort, merge, lookup, output | [windows-api.md - DataTable](windows-api.md#datatable-operations) |
| **Text Operations** | Replace, extract, combine, split, change case, HTML strip | [windows-api.md - Text](windows-api.md#text-operations) |
| **DateTime Operations** | Format, extract, add/subtract | [windows-api.md - DateTime](windows-api.md#datetime-operations) |
| **Queue/Transaction Items** | Add, get, delete, postpone, set status, bulk operations | [windows-api.md - Queues](windows-api.md#queuetransaction-items) |
| **Assets & Credentials** | Get/set Orchestrator assets and credentials | [windows-api.md - Assets](windows-api.md#assets--credentials) |
| **Jobs & Processes** | Run, start, stop, get Orchestrator jobs; invoke processes | [windows-api.md - Jobs](windows-api.md#jobs--processes) |
| **Storage Buckets** | Upload, download, delete, list, read/write text in Orchestrator storage | [windows-api.md - Storage](windows-api.md#storage-buckets) |
| **Alerts & HTTP** | Raise Orchestrator alerts; perform Orchestrator HTTP requests | [windows-api.md - Alerts](windows-api.md#alerts--orchestrator-http) |
| **Network** | Download file from URL | [windows-api.md - Network](windows-api.md#network) |

For full coded workflow examples, see [examples.md](examples.md).

---

## Key Enum Reference Summary

| Enum | Values | Description |
|---|---|---|
| `PathType` | `File`, `Folder` | Type of file system path |
| `SortOrder` | `Ascending`, `Descending` | DataTable sort order |
| `MissingSchemaAction` | `Add`, `AddWithKey`, `Error`, `Ignore` | How to handle missing schema when merging DataTables |
| `QueueItemPriority` | `Low`, `Normal`, `High` | Priority for queue items |
| `ProcessingStatus` | `Successful`, `Failed` | Transaction item processing status |
| `ErrorType` | `ApplicationException`, `BusinessException` | Error type for failed transactions |
| `QueueItemStates` | `New`, `InProgress`, `Failed`, `Successful`, `Abandoned`, `Retried`, `Deleted` | Queue item state filter |
| `ReferenceFilterStrategy` | `Equals`, `StartsWith`, `Contains` | How to filter queue items by reference |
| `AlertSeverity` | `Info`, `Warn`, `Error`, `Fatal` | Orchestrator alert severity |
| `OrchestratorAPIHttpMethods` | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` | HTTP methods for Orchestrator API requests |
| `StopStrategy` | `Stop`, `Kill` | How to stop an Orchestrator job |
| `StartProcessDtoJobPriority` | `Low`, `Normal`, `High` | Priority for started jobs |
| `CacheStrategyEnum` | `None`, `PerRobot`, `Global` | Caching strategy for asset retrieval |
| `SeparatorOptions` | `NewLine`, `Tab`, `Comma`, `Semicolon`, `Space`, `Pipe` | Predefined text separators |
| `ChangeCaseOptions` | `UPPERCASE`, `lowercase`, `Title Case`, `Sentence case` | Case conversion options |
| `UnitsOfTime` | `Milliseconds`, `Seconds`, `Minutes`, `Hours`, `Days`, `Months`, `Years` | Time units for date arithmetic |
| `ArchiveCompressionLevel` | `Optimal`, `Fastest`, `NoCompression` | Zip compression level |
| `CodePages` | Various encoding options | Text encoding for zip file names |
| `FileConflictBehavior` | `Rename`, `Replace`, `Skip` | Behavior when downloaded file already exists |
| `InvokeProcessTargetSession` | `ProcessDefault`, `Current`, `Main`, `PictureInPicture` | Session for invoked processes |
| `LogEntryType` / `LogExitType` | `No`, `Arguments`, `ArgumentsAndVariables` | Logging on process entry/exit |
