# UiPath System Activities — Coded Workflow API

`UiPath.System.Activities`

Provides system-level automation capabilities for coded workflows: file and folder management, DataTable manipulation, text processing, date/time utilities, Orchestrator integration (jobs, queues, assets, credentials, storage buckets), and HTTP requests.

**Service accessor:** `system` (type `ISystemService`)

**Required package:** `"UiPath.System.Activities": "*"` in project.json dependencies

## Auto-Imported Namespaces

These namespaces are automatically available in coded workflows when this package is installed:

```
System
System.Collections.Generic
System.Data
UiPath.Core
UiPath.Core.Activities.Storage
UiPath.Orchestrator.Client.Models
UiPath.Activities.System.Jobs.Coded
```

## Service Overview

The `system` service provides direct method calls — no handles, no `using` blocks. Methods cover:

- **Process invocation** — invoke local processes or Orchestrator jobs synchronously or asynchronously
- **File & folder operations** — create, copy, move, delete, read, and write files and folders
- **Compression** — zip and unzip file archives
- **DataTable operations** — add/remove rows and columns, sort, merge, deduplicate, lookup
- **Text manipulation** — regex replace, extract patterns (emails, URLs, occurrences), split/join, case conversion
- **Date & time** — parse dates from text, format dates, add/subtract time
- **Orchestrator queues** — add, get, and manage queue items and transactions
- **Orchestrator assets & credentials** — read/write assets and credential assets
- **Storage buckets** — upload, download, list, read, and write Orchestrator storage files
- **Orchestrator HTTP** — make arbitrary REST calls to Orchestrator APIs
- **Alerts** — raise Orchestrator alerts

---

## Process Invocation

### `(OrchestratorJob JobData, string OutputJson) RunJob(string processName, string orchestratorFolderPath = null, object inputArguments = null, bool doNotWait = false, RunJobOptionalParameters runJobOptionalParameters = null)`

Runs a job in Orchestrator synchronously and returns the job data and output arguments.

**Parameters:**
- `processName` (`string`) — The name of the process to run
- `orchestratorFolderPath` (`string`) — Orchestrator folder path where the process resides (default: `null`)
- `inputArguments` (`object`) — Input arguments for the process; can be an anonymous object or dictionary (default: `null`)
- `doNotWait` (`bool`) — If `true`, fires the job without waiting for completion (default: `false`)
- `runJobOptionalParameters` (`RunJobOptionalParameters`) — Additional options: timeout, error handling (default: `null`)

**Returns:** `(OrchestratorJob JobData, string OutputJson)` — Tuple with the Orchestrator job entity and the process output arguments serialized as a JSON string.

---

### `Task<(OrchestratorJob JobData, string OutputJson)> RunJobAsync(string processName, string orchestratorFolderPath = null, object inputArguments = null, bool doNotWait = false, RunJobOptionalParameters runJobOptionalParameters = null)`

Asynchronous version of `RunJob`. Awaitable.

**Parameters:** Same as `RunJob`.

**Returns:** `Task<(OrchestratorJob JobData, string OutputJson)>` — Awaitable task yielding the same tuple as `RunJob`.

---

### `void InvokeProcess(string processName)`
### `void InvokeProcess(string processName, string folderPath)`

Invokes a process available on the current Robot. Blocking — returns only after the invoked process finishes.

**Parameters:**
- `processName` (`string`) — The name of the process to run
- `folderPath` (`string`) — Orchestrator folder where the process resides

**Returns:** `void` — Blocks until the invoked process completes.

---

### `Task<Dictionary<string, object>> InvokeProcessAsync(string processName)`
### `Task<Dictionary<string, object>> InvokeProcessAsync(string processName, string folderPath)`
### `Task<Dictionary<string, object>> InvokeProcessAsync(string processName, string folderPath = null, Dictionary<string, object> inArguments = null, Dictionary<string, object> inOutArguments = null, LogEntryType logEntry = LogEntryType.No, LogExitType logExit = LogExitType.No, UiPath.Core.Activities.LogLevel level = LogLevel.Info, InvokeProcessTargetSession targetSession = InvokeProcessTargetSession.Current, TimeSpan timeout = default)`

Invokes a process available on the current Robot asynchronously.

**Parameters (full overload):**
- `processName` (`string`) — Name of the process to run
- `folderPath` (`string`) — Orchestrator folder (default: `null`)
- `inArguments` (`Dictionary<string, object>`) — Input arguments (default: `null`)
- `inOutArguments` (`Dictionary<string, object>`) — In-out arguments; updated after execution (default: `null`)
- `logEntry` (`LogEntryType`) — What to log on entry (default: `LogEntryType.No`)
- `logExit` (`LogExitType`) — What to log on exit (default: `LogExitType.No`)
- `level` (`UiPath.Core.Activities.LogLevel`) — Log level for entry/exit messages (default: `LogLevel.Info`)
- `targetSession` (`InvokeProcessTargetSession`) — Session in which the child process starts (default: `InvokeProcessTargetSession.Current`)
- `timeout` (`TimeSpan`) — Maximum wait time before aborting (default: `default`)

**Returns:** `Task<Dictionary<string, object>>` — Awaitable task yielding the output arguments of the invoked process.

---

### `string StartJob(string processName)`
### `string StartJob(string processName, string folderPath)`
### `string StartJob(string processName, out string jobId)`
### `string StartJob(string processName, out string jobId, string folderPath)`
### `string StartJob(string processName, string folderPath, StartProcessDtoJobPriority jobPriority, bool resumeOnSameContext, out string jobId)`

Starts an Orchestrator job without waiting for it to complete.

**Parameters (full overload):**
- `processName` (`string`) — Name of the process
- `folderPath` (`string`) — Orchestrator folder
- `jobPriority` (`StartProcessDtoJobPriority`) — Job execution priority
- `resumeOnSameContext` (`bool`) — Whether to resume on the same context
- `jobId` (`out string`) — Receives the started job's ID

**Returns:** `string` — The Orchestrator job key/identifier.

---

### `void StopJob(OrchestratorJob job, StopStrategy strategy)`
### `void StopJob(OrchestratorJob job, StopStrategy strategy, string folderPath)`
### `void StopJob(OrchestratorJob job, StopStrategy strategy, string folderPath, int timeoutMS)`

Stops a running Orchestrator job.

**Parameters:**
- `job` (`OrchestratorJob`) — The job to stop
- `strategy` (`StopStrategy`) — How to stop the job (e.g., soft stop or kill)
- `folderPath` (`string`) — Orchestrator folder
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `void`

---

### `IEnumerable<OrchestratorJob> GetJobs()`
### `IEnumerable<OrchestratorJob> GetJobs(string filter, JobFilterSettings filterBuilder, string folderPath)`
### `IEnumerable<OrchestratorJob> GetJobs(string filter, JobFilterSettings filterBuilder, string folderPath, int top, int skip, int timeoutMS)`

Retrieves Orchestrator jobs matching the specified filter criteria.

**Parameters (full overload):**
- `filter` (`string`) — OData filter string
- `filterBuilder` (`JobFilterSettings`) — Structured filter settings
- `folderPath` (`string`) — Orchestrator folder
- `top` (`int`) — Maximum number of results to return
- `skip` (`int`) — Number of results to skip (paging)
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `IEnumerable<OrchestratorJob>` — Collection of matching job entities.

---

## File & Folder Operations

### `void CopyFile(string path, string destination, bool overwrite)`

Copies a file to another location.

**Parameters:**
- `path` (`string`) — Source file path
- `destination` (`string`) — Destination path
- `overwrite` (`bool`) — Whether to overwrite if destination exists

**Returns:** `void`

---

### `void CopyFolder(string from, string to)`
### `void CopyFolder(string from, string to, bool overwrite, bool includeSubfolder)`

Copies a folder to another location.

**Parameters:**
- `from` (`string`) — Source folder path
- `to` (`string`) — Destination folder path
- `overwrite` (`bool`) — Whether to overwrite existing folders at the destination
- `includeSubfolder` (`bool`) — Whether to include subfolders

**Returns:** `void`

---

### `ILocalResource CreateFile(string name, string path)`

Creates a new file at the specified location.

**Parameters:**
- `name` (`string`) — File name (including extension)
- `path` (`string`) — Directory path where the file will be created

**Returns:** `ILocalResource` — Resource handle for the newly created file, providing its `LocalPath`.

---

### `ILocalResource CreateFolder(string path)`

Creates a new folder at the specified path.

**Parameters:**
- `path` (`string`) — Full path of the folder to create

**Returns:** `ILocalResource` — Resource handle for the created folder.

---

### `void DeleteFileOrFolder(ILocalResource resourceFile)`

Deletes the file or folder represented by the given resource.

**Parameters:**
- `resourceFile` (`ILocalResource`) — Resource pointing to the file or folder to delete

**Returns:** `void`

---

### `void MoveFile(IResource pathResource, IResource destinationResource, bool overwrite)`

Moves a file or folder to a new location.

**Parameters:**
- `pathResource` (`IResource`) — Source resource
- `destinationResource` (`IResource`) — Destination resource
- `overwrite` (`bool`) — Whether to overwrite if destination exists

**Returns:** `void`

---

### `bool PathExists(string path)`
### `bool PathExists(string path, PathType pathType)`
### `bool PathExists(string path, out ILocalResource resource)`
### `bool PathExists(string path, PathType pathType, out ILocalResource resource)`

Checks whether a path exists on the file system.

**Parameters:**
- `path` (`string`) — Path to check
- `pathType` (`PathType`) — Whether to check for a file, folder, or either
- `resource` (`out ILocalResource`) — If the path exists, receives the corresponding resource

**Returns:** `bool` — `true` if the path exists, `false` otherwise.

---

### `bool FileExists(string path)`

Checks whether a file path exists.

**Parameters:**
- `path` (`string`) — Local file path to check

**Returns:** `bool` — `true` if the file exists.

---

### `bool FolderExists(string path)`

Checks whether a folder path exists.

**Parameters:**
- `path` (`string`) — Local folder path to check

**Returns:** `bool` — `true` if the folder exists.

---

### `IResource GetResourceForLocalPath(string path, PathType pathType)`

Constructs an `IResource` for the given local file or folder path.

**Parameters:**
- `path` (`string`) — Local path of the file or folder
- `pathType` (`PathType`) — Whether the path is a file or folder

**Returns:** `IResource` — Resource object wrapping the local path.

---

### `string ReadTextFile(IResource file)`
### `string ReadTextFile(IResource file, string encoding)`

Reads the contents of a text file.

**Parameters:**
- `file` (`IResource`) — The file to read
- `encoding` (`string`) — Text encoding (e.g., `"UTF-8"`); uses system default when omitted

**Returns:** `string` — The complete text content of the file.

---

### `void WriteTextFile(string text, ILocalResource file)`
### `void WriteTextFile(string text, ILocalResource file, string encoding)`

Writes text to a file, overwriting existing content.

**Parameters:**
- `text` (`string`) — Text to write
- `file` (`ILocalResource`) — Target file resource
- `encoding` (`string`) — Text encoding (e.g., `"UTF-8"`)

**Returns:** `void`

---

### `void AppendLine(string text, ILocalResource file)`
### `void AppendLine(string text, ILocalResource file, bool useDefaultEncoding, string encoding)`

Appends a line of text to a file.

**Parameters:**
- `text` (`string`) — Text to append
- `file` (`ILocalResource`) — Target file resource
- `useDefaultEncoding` (`bool`) — Whether to use the system default encoding
- `encoding` (`string`) — Explicit encoding to use when `useDefaultEncoding` is false

**Returns:** `void`

---

### `Task<ILocalResource> DownloadFileFromURLAsync(string url, string fileName = default, FileConflictBehavior conflictResolution = FileConflictBehavior.Rename, int timeout = DownloadFileFromUrl.DefaultTimeout, CancellationToken cancellationToken = default, string userAgentHeaderValue = null)`

Downloads a file from a URL asynchronously.

**Parameters:**
- `url` (`string`) — URL of the file to download
- `fileName` (`string`) — Local file name to save as; auto-detected from URL if omitted (default: `default`)
- `conflictResolution` (`FileConflictBehavior`) — What to do if the file already exists (default: `FileConflictBehavior.Rename`)
- `timeout` (`int`) — Download timeout in milliseconds (default: `DownloadFileFromUrl.DefaultTimeout`)
- `cancellationToken` (`CancellationToken`) — Cancellation token (default: `default`)
- `userAgentHeaderValue` (`string`) — Custom User-Agent header (default: `null`)

**Returns:** `Task<ILocalResource>` — Awaitable task yielding a resource pointing to the downloaded file.

---

## Compression

### `ILocalResource[] ExtractUnzipFiles(IResource file)`
### `ILocalResource[] ExtractUnzipFiles(IResource file, string destinationFolder)`
### `ILocalResource[] ExtractUnzipFiles(IResource file, string destinationFolder, bool extractToADedicatedFolder, string password, CodePages codePage)`

Extracts files from a ZIP archive.

**Parameters (full overload):**
- `file` (`IResource`) — The ZIP archive to extract
- `destinationFolder` (`string`) — Folder where extracted files are placed
- `extractToADedicatedFolder` (`bool`) — Whether to create a dedicated subfolder for the extracted contents
- `password` (`string`) — Archive password, if protected
- `codePage` (`CodePages`) — Code page for file name encoding

**Returns:** `ILocalResource[]` — Array of resources for each extracted file.

---

### `ILocalResource CompressZipFiles(IEnumerable<IResource> resourcesToArchive, string compressedFileName)`
### `ILocalResource CompressZipFiles(IEnumerable<IResource> resourcesToArchive, string compressedFileName, string password, ArchiveCompressionLevel compressionLevel, CodePages codePage, bool overrideExistingFile)`

Compresses files into a ZIP archive.

**Parameters (full overload):**
- `resourcesToArchive` (`IEnumerable<IResource>`) — Files and folders to compress
- `compressedFileName` (`string`) — Path and name of the output ZIP file
- `password` (`string`) — Password to protect the archive
- `compressionLevel` (`ArchiveCompressionLevel`) — Compression quality level
- `codePage` (`CodePages`) — Code page for file name encoding
- `overrideExistingFile` (`bool`) — Whether to overwrite an existing archive

**Returns:** `ILocalResource` — Resource pointing to the created ZIP file.

---

## DataTable Operations

### `void AddDataRow(ref DataTable dataTable, DataRow dataRow)`

Adds a row to a DataTable.

**Parameters:**
- `dataTable` (`ref DataTable`) — The DataTable to modify
- `dataRow` (`DataRow`) — The row to add

**Returns:** `void`

---

### `void RemoveDataRow(ref DataTable dataTable, int rowIndex)`

Removes a row at the specified index from a DataTable.

**Parameters:**
- `dataTable` (`ref DataTable`) — The DataTable to modify
- `rowIndex` (`int`) — Zero-based index of the row to remove

**Returns:** `void`

---

### `void ClearDataTable(ref DataTable dataTable)`

Removes all rows from a DataTable.

**Parameters:**
- `dataTable` (`ref DataTable`) — The DataTable to clear

**Returns:** `void`

---

### `void RemoveDataColumn(ref DataTable dataTable, string columnName)`

Removes a column from a DataTable by name.

**Parameters:**
- `dataTable` (`ref DataTable`) — The DataTable to modify
- `columnName` (`string`) — Name of the column to remove

**Returns:** `void`

---

### `string OutputDataTable(DataTable dataTable)`

Converts a DataTable to a string representation using CSV format.

**Parameters:**
- `dataTable` (`DataTable`) — The DataTable to convert

**Returns:** `string` — String representation of the DataTable contents.

---

### `DataTable SortDataTable(DataTable dataTable, string columnName)`
### `DataTable SortDataTable(DataTable dataTable, string columnName, SortOrder sortOrder)`

Sorts a DataTable by a specified column.

**Parameters:**
- `dataTable` (`DataTable`) — The DataTable to sort
- `columnName` (`string`) — Name of the column to sort by
- `sortOrder` (`SortOrder`) — Ascending or descending (default: ascending when omitted)

**Returns:** `DataTable` — A new sorted DataTable.

---

### `void MergeDataTable(DataTable sourceDataTable, ref DataTable destinationDataTable)`
### `void MergeDataTable(DataTable sourceDataTable, ref DataTable destinationDataTable, MissingSchemaAction missingSchemaAction)`

Merges a source DataTable into a destination DataTable.

**Parameters:**
- `sourceDataTable` (`DataTable`) — DataTable to merge from
- `destinationDataTable` (`ref DataTable`) — DataTable to merge into (modified in place)
- `missingSchemaAction` (`MissingSchemaAction`) — Specifies how to handle schema differences

**Returns:** `void`

---

### `DataTable RemoveDuplicateRows(DataTable dataTable)`

Removes duplicate rows from a DataTable, keeping only the first occurrence of each.

**Parameters:**
- `dataTable` (`DataTable`) — The DataTable to deduplicate

**Returns:** `DataTable` — A new DataTable with duplicate rows removed.

---

### `void UpdateRowItem(object value, DataRow row, string columnName)`

Sets the value of a cell in a DataRow by column name.

**Parameters:**
- `value` (`object`) — The value to set
- `row` (`DataRow`) — The target DataRow
- `columnName` (`string`) — Name of the column to update

**Returns:** `void`

---

### `object GetRowItem(DataRow row, string columnName)`

Gets the value of a cell from a DataRow by column name.

**Parameters:**
- `row` (`DataRow`) — The DataRow to read from
- `columnName` (`string`) — Name of the column

**Returns:** `object` — The value of the specified cell. Cast to the expected type as needed.

---

### `object LookupDataTable(DataTable dataTable, string lookupValue, string lookupColumnName, string targetColumnName)`
### `object LookupDataTable(DataTable dataTable, string lookupValue, string lookupColumnName, string targetColumnName, out int rowIndex)`

Searches for a value in a column and returns the corresponding cell value from a target column.

**Parameters:**
- `dataTable` (`DataTable`) — The DataTable to search
- `lookupValue` (`string`) — Value to search for
- `lookupColumnName` (`string`) — Column to search in
- `targetColumnName` (`string`) — Column from which to return the matched row's value
- `rowIndex` (`out int`) — Receives the zero-based index of the matching row

**Returns:** `object` — Value from `targetColumnName` in the matched row. Returns `null` if `targetColumnName` is not set.

---

## Text Manipulation

### `string Replace(string input, string pattern, string replacement)`
### `string Replace(string input, string pattern, string replacement, RegexOptions regexOption)`

Replaces occurrences of a regex pattern in a string.

**Parameters:**
- `input` (`string`) — The input string
- `pattern` (`string`) — Regex pattern to find
- `replacement` (`string`) — Replacement string
- `regexOption` (`RegexOptions`) — Regex matching options (e.g., `RegexOptions.IgnoreCase`)

**Returns:** `string` — The string with all matches replaced.

---

### `string FindAndReplace(string valueToFind, string source, string replaceWith, bool matchCase)`

Finds and replaces a literal string (not regex) within a source string.

**Parameters:**
- `valueToFind` (`string`) — The string to find
- `source` (`string`) — The source text
- `replaceWith` (`string`) — The replacement text
- `matchCase` (`bool`) — Whether the search is case-sensitive

**Returns:** `string` — The resulting string after replacement.

---

### `IEnumerable<string> ExtractTextOccurrences(string source, string startingText, string endingText, bool ignoreDuplicates = false, bool matchCase = false)`

Extracts all substrings between a pair of delimiter texts.

**Parameters:**
- `source` (`string`) — The text to search
- `startingText` (`string`) — Opening delimiter
- `endingText` (`string`) — Closing delimiter
- `ignoreDuplicates` (`bool`) — Whether to omit duplicate matches (default: `false`)
- `matchCase` (`bool`) — Whether delimiters are matched case-sensitively (default: `false`)

**Returns:** `IEnumerable<string>` — All substrings found between the delimiters.

---

### `IEnumerable<string> ExtractEmails(string source, bool ignoreDuplicates = false)`

Extracts all email addresses from a string.

**Parameters:**
- `source` (`string`) — The text to search
- `ignoreDuplicates` (`bool`) — Whether to omit duplicate results (default: `false`)

**Returns:** `IEnumerable<string>` — Collection of email address strings found in the source.

---

### `IEnumerable<string> ExtractUrls(string source, bool extractBaseURLOnly = false, bool ignoreDuplicates = false)`

Extracts all URLs from a string.

**Parameters:**
- `source` (`string`) — The text to search
- `extractBaseURLOnly` (`bool`) — Whether to return only the base URL (scheme + host) (default: `false`)
- `ignoreDuplicates` (`bool`) — Whether to omit duplicate results (default: `false`)

**Returns:** `IEnumerable<string>` — Collection of URL strings found in the source.

---

### `string ExtractTextFromHTML(string source)`

Strips HTML tags and returns plain text content.

**Parameters:**
- `source` (`string`) — HTML string to process

**Returns:** `string` — Plain text with HTML tags removed.

---

### `string CombineText(IEnumerable<string> source, string separator)`
### `string CombineText(IEnumerable<string> source, SeparatorOptions separatorKey)`

Joins a collection of strings into a single string.

**Parameters:**
- `source` (`IEnumerable<string>`) — Strings to join
- `separator` (`string`) — Separator to place between items
- `separatorKey` (`SeparatorOptions`) — Predefined separator (e.g., comma, newline)

**Returns:** `string` — Single concatenated string.

---

### `IEnumerable<string> SplitText(string source, string separator)`
### `IEnumerable<string> SplitText(string source, SeparatorOptions separatorKey)`

Splits a string into a collection of substrings.

**Parameters:**
- `source` (`string`) — The string to split
- `separator` (`string`) — Separator string
- `separatorKey` (`SeparatorOptions`) — Predefined separator

**Returns:** `IEnumerable<string>` — Collection of split substrings.

---

### `string ChangeCase(string source, ChangeCaseOptions changeCaseOptions)`

Converts a string to a different case.

**Parameters:**
- `source` (`string`) — The input string
- `changeCaseOptions` (`ChangeCaseOptions`) — Target case (e.g., upper, lower, title)

**Returns:** `string` — The string in the target case.

---

## Date & Time

### `IEnumerable<DateTime> ExtractDateAndTimeFromText(string format, string source, CultureInfo localizationCode)`

Extracts date/time values from a string using a format pattern.

**Parameters:**
- `format` (`string`) — Date/time format string (e.g., `"MM/dd/yyyy"`)
- `source` (`string`) — The text to search
- `localizationCode` (`CultureInfo`) — Culture to use for parsing

**Returns:** `IEnumerable<DateTime>` — All date/time values parsed from the source text.

---

### `string FormatDateAsText(DateTime source, string format, CultureInfo localizationCode)`

Formats a `DateTime` value as a string.

**Parameters:**
- `source` (`DateTime`) — The date/time to format
- `format` (`string`) — Format string (e.g., `"yyyy-MM-dd"`)
- `localizationCode` (`CultureInfo`) — Culture for formatting

**Returns:** `string` — The formatted date/time string.

---

### `DateTime AddOrSubtractFromDate(DateTime source, UnitsOfTime unitOfTime, int amountOfTime, UiPath.Activities.System.Date.AddOrSubtractFromDate.DateOperations selectedOperation)`

Adds or subtracts a time amount from a `DateTime`.

**Parameters:**
- `source` (`DateTime`) — The starting date/time
- `unitOfTime` (`UnitsOfTime`) — Time unit (e.g., days, months, years)
- `amountOfTime` (`int`) — Number of units to add or subtract
- `selectedOperation` (`DateOperations`) — Whether to add or subtract

**Returns:** `DateTime` — The resulting date/time after the operation.

---

## Queue & Transaction Management

### `void AddQueueItem(string queueType)`
### `void AddQueueItem(string queueType, string folderPath)`
### `void AddQueueItem(string queueType, string folderPath, Dictionary<string, object> itemInformationCollection)`
### `void AddQueueItem(string queueType, string folderPath, DateTime dueDate, Dictionary<string, object> itemInformationCollection, DateTime deferDate, QueueItemPriority priority, string reference, int timeoutMS)`

Adds a new queue item with status `New`.

**Parameters (full overload):**
- `queueType` (`string`) — Target queue name
- `folderPath` (`string`) — Orchestrator folder
- `dueDate` (`DateTime`) — The date before which the queue item should be processed. This is a prioritization criterion alongside Priority and Postpone
- `itemInformationCollection` (`Dictionary<string, object>`) — Additional data stored on the item
- `deferDate` (`DateTime`) — Earliest date the item may be processed
- `priority` (`QueueItemPriority`) — Processing priority
- `reference` (`string`) — Reference string for filtering
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `void`

---

### `QueueItem AddTransactionItem(string queueType)`
### `QueueItem AddTransactionItem(string queueType, string folderPath)`
### `QueueItem AddTransactionItem(string queueType, string folderPath, string reference, Dictionary<string, object> transactionInformation, int timeoutMS)`

Adds a new transaction item to an Orchestrator queue.

**Parameters (full overload):**
- `queueType` (`string`) — Target queue name
- `folderPath` (`string`) — Orchestrator folder
- `reference` (`string`) — Reference string
- `transactionInformation` (`Dictionary<string, object>`) — Data stored on the transaction
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `QueueItem` — The created transaction item entity.

---

### `DataTable BulkAddQueueItems(DataTable queueItemsDataTable, string queueName)`
### `DataTable BulkAddQueueItems(DataTable queueItemsDataTable, string queueName, string folderPath)`
### `DataTable BulkAddQueueItems(DataTable queueItemsDataTable, string queueName, string folderPath, UiPath.Core.Activities.BulkAddQueueItems.CommitTypeEnum commitType, int timeoutMS)`

Adds multiple queue items from a DataTable in a single operation.

**Parameters (full overload):**
- `queueItemsDataTable` (`DataTable`) — DataTable containing queue items to add
- `queueName` (`string`) — Target queue name
- `folderPath` (`string`) — Orchestrator folder
- `commitType` (`CommitTypeEnum`) — Whether to commit all at once or per item
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `DataTable` — DataTable reflecting the result of the bulk operation (e.g., failed items).

---

### `QueueItem GetTransactionItem(string queueType)`
### `QueueItem GetTransactionItem(string queueType, string folderPath)`
### `QueueItem GetTransactionItem(string queueType, string folderPath, ReferenceFilterStrategy filterStrategy, string reference, int timeoutMS)`

Gets an item from the queue and sets its status to `In Progress` (starts the transaction).

**Parameters (full overload):**
- `queueType` (`string`) — Source queue name
- `folderPath` (`string`) — Orchestrator folder
- `filterStrategy` (`ReferenceFilterStrategy`) — Strategy for filtering by reference
- `reference` (`string`) — Reference value to filter by
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `QueueItem` — The retrieved transaction item, now in `In Progress` state. Returns `null` if no item is available.

---

### `QueueItem GetQueueItem(string queueType)`
### `QueueItem GetQueueItem(string queueType, string folderPath)`
### `QueueItem GetQueueItem(string queueType, string folderPath, ReferenceFilterStrategy filterStrategy, string reference, int timeoutMS)`

Gets an item from the queue and sets its status to `In Progress`.

**Parameters:** Same pattern as `GetTransactionItem`.

**Returns:** `QueueItem` — The retrieved queue item.

---

### `IEnumerable<QueueItem> GetQueueItems(string queueName)`
### `IEnumerable<QueueItem> GetQueueItems(string queueName, string folderPath)`
### `IEnumerable<QueueItem> GetQueueItems(string queueName, string folderPath, int? duration, DateTime? from, int? priority, QueueItemStates queueItemStates, DateTime? to, ReferenceFilterStrategy filterStrategy, string reference, int skip, int top, int timeoutMS)`

Retrieves a filtered collection of queue items without claiming them for processing.

**Parameters (full overload):**
- `queueName` (`string`) — Queue name
- `folderPath` (`string`) — Orchestrator folder
- `duration` (`int?`) — Filter by duration
- `from` (`DateTime?`) — Start of date range filter
- `priority` (`int?`) — Priority filter
- `queueItemStates` (`QueueItemStates`) — Status filter
- `to` (`DateTime?`) — End of date range filter
- `filterStrategy` (`ReferenceFilterStrategy`) — Reference filter strategy
- `reference` (`string`) — Reference value to filter by
- `skip` (`int`) — Number of items to skip (paging)
- `top` (`int`) — Maximum items to return
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `IEnumerable<QueueItem>` — Collection of queue items matching the filter.

---

### `QueueItem WaitQueueItem(string queueName)`
### `QueueItem WaitQueueItem(string queueName, string folderPath)`
### `QueueItem WaitQueueItem(string queueName, string folderPath, int pollTimeMS, ReferenceFilterStrategy filterStrategy, string reference, int timeoutMS)`

Waits until an item becomes available in the queue, then returns it.

**Parameters (full overload):**
- `queueName` (`string`) — Queue name
- `folderPath` (`string`) — Orchestrator folder
- `pollTimeMS` (`int`) — Interval between polls in milliseconds
- `filterStrategy` (`ReferenceFilterStrategy`) — Reference filter strategy
- `reference` (`string`) — Reference value to filter by
- `timeoutMS` (`int`) — Total timeout in milliseconds

**Returns:** `QueueItem` — The first available queue item.

---

### `void DeleteQueueItems(IEnumerable<QueueItem> queueItems)`
### `void DeleteQueueItems(IEnumerable<QueueItem> queueItems, string folderPath)`
### `void DeleteQueueItems(IEnumerable<QueueItem> queueItems, string folderPath, int timeoutMS)`

Deletes queue items from Orchestrator.

**Parameters:**
- `queueItems` (`IEnumerable<QueueItem>`) — Items to delete
- `folderPath` (`string`) — Orchestrator folder
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `void`

---

### `void PostponeTransactionItem(QueueItem transactionItem, DateTime deferDate)`
### `void PostponeTransactionItem(QueueItem transactionItem, DateTime deferDate, string folderPath)`
### `void PostponeTransactionItem(QueueItem transactionItem, DateTime deferDate, string folderPath, DateTime dueDate, int timeoutMS)`

Postpones a transaction item to a future date.

**Parameters (full overload):**
- `transactionItem` (`QueueItem`) — The item to postpone
- `deferDate` (`DateTime`) — Earliest date the item may be processed again
- `folderPath` (`string`) — Orchestrator folder
- `dueDate` (`DateTime`) — Latest date the item should be processed
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `void`

---

### `void SetTransactionProgress(QueueItem transactionItem, string progress)`
### `void SetTransactionProgress(QueueItem transactionItem, string progress, string folderPath)`
### `void SetTransactionProgress(QueueItem transactionItem, string progress, string folderPath, int timeoutMS)`

Updates the progress text of a transaction item currently in progress.

**Parameters:**
- `transactionItem` (`QueueItem`) — The in-progress transaction item
- `progress` (`string`) — Progress message to set
- `folderPath` (`string`) — Orchestrator folder
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `void`

---

### `void SetTransactionStatus(QueueItem transactionItem, ProcessingStatus status)`
### `void SetTransactionStatus(QueueItem transactionItem, ProcessingStatus status, string folderPath)`
### `void SetTransactionStatus(QueueItem transactionItem, ProcessingStatus status, string folderPath, Dictionary<string, object> analytics, Dictionary<string, object> output, string details, ErrorType errorType, string reason, int timeoutMS)`

Sets the final status of a transaction item (success, failure, or exception).

**Parameters (full overload):**
- `transactionItem` (`QueueItem`) — The transaction item to update
- `status` (`ProcessingStatus`) — New status (e.g., Successful, Failed)
- `folderPath` (`string`) — Orchestrator folder
- `analytics` (`Dictionary<string, object>`) — Analytics data to attach
- `output` (`Dictionary<string, object>`) — Output data to attach
- `details` (`string`) — Status detail message
- `errorType` (`ErrorType`) — Type of error (for failure statuses)
- `reason` (`string`) — Failure reason
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `void`

---

## Orchestrator Assets & Credentials

### `object GetAsset(string assetName)`
### `object GetAsset(string assetName, string folderPath)`
### `object GetAsset(string assetName, string folderPath, CacheStrategyEnum cacheStrategy, int timeoutMS)`

Retrieves an Orchestrator asset value.

**Parameters (full overload):**
- `assetName` (`string`) — Name of the asset
- `folderPath` (`string`) — Orchestrator folder
- `cacheStrategy` (`CacheStrategyEnum`) — Caching behavior
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `object` — The asset value. Cast to the expected type (e.g., `string`, `int`, `bool`).

---

### `void SetAsset(object value, string assetName)`
### `void SetAsset(object value, string assetName, string folderPath)`
### `void SetAsset(object value, string assetName, string folderPath, int timeoutMS)`

Sets the value of an Orchestrator asset.

**Parameters:**
- `value` (`object`) — New value for the asset
- `assetName` (`string`) — Name of the asset
- `folderPath` (`string`) — Orchestrator folder
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `void`

---

### `(string userName, SecureString password) GetCredential(string assetName, string folderPath = null, int timeoutMS = 1000, CacheStrategyEnum cacheStrategy = CacheStrategyEnum.None)`

Retrieves a credential asset as a username/password tuple.

**Parameters:**
- `assetName` (`string`) — Name of the credential asset
- `folderPath` (`string`) — Orchestrator folder (default: `null`)
- `timeoutMS` (`int`) — Timeout in milliseconds (default: `1000`)
- `cacheStrategy` (`CacheStrategyEnum`) — Caching behavior (default: `CacheStrategyEnum.None`)

**Returns:** `(string userName, SecureString password)` — Tuple containing the username string and the password as a `SecureString`.

---

### `string GetCredential(string assetName, string folderPath, out SecureString password, CacheStrategyEnum cacheStrategy, int timeoutMS)`

Retrieves a credential asset, returning the username and providing the password via an `out` parameter.

**Parameters:**
- `assetName` (`string`) — Name of the credential asset
- `folderPath` (`string`) — Orchestrator folder
- `password` (`out SecureString`) — Receives the credential password
- `cacheStrategy` (`CacheStrategyEnum`) — Caching behavior
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `string` — The username from the credential asset.

---

### `void SetCredential(string userName, string password, string credentialName)`
### `void SetCredential(string userName, string password, string credentialName, string folderPath)`
### `void SetCredential(string userName, string password, string credentialName, string folderPath, int timeoutMS)`

Updates an Orchestrator credential asset with a new username and password.

**Parameters:**
- `userName` (`string`) — New username
- `password` (`string`) — New password (plain text; stored securely by Orchestrator)
- `credentialName` (`string`) — Name of the credential asset
- `folderPath` (`string`) — Orchestrator folder
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `void`

---

## Storage Buckets

### `void DeleteStorageFile(string path, string storageBucketName)`
### `void DeleteStorageFile(string path, string storageBucketName, string folderPath)`
### `void DeleteStorageFile(string path, string storageBucketName, string folderPath, int timeoutMS)`

Deletes a file from an Orchestrator storage bucket.

**Parameters:**
- `path` (`string`) — Path of the file within the bucket
- `storageBucketName` (`string`) — Name of the storage bucket
- `folderPath` (`string`) — Orchestrator folder
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `void`

---

### `ILocalResource DownloadStorageFile(string path, string storageBucketName)`
### `ILocalResource DownloadStorageFile(string path, string storageBucketName, string folderPath)`
### `ILocalResource DownloadStorageFile(string path, string storageBucketName, string folderPath, string destination, int timeoutMS)`

Downloads a file from an Orchestrator storage bucket to the local machine.

**Parameters (full overload):**
- `path` (`string`) — Path of the file within the bucket
- `storageBucketName` (`string`) — Name of the storage bucket
- `folderPath` (`string`) — Orchestrator folder
- `destination` (`string`) — Local destination path
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `ILocalResource` — Resource pointing to the downloaded local file.

---

### `IEnumerable<StorageFileInfo> ListStorageFiles(string directory, string storageBucketName)`
### `IEnumerable<StorageFileInfo> ListStorageFiles(string directory, string storageBucketName, string folderPath)`
### `IEnumerable<StorageFileInfo> ListStorageFiles(string directory, string storageBucketName, string folderPath, bool recursive, string filter, int timeoutMS)`

Lists files in a directory within an Orchestrator storage bucket.

**Parameters (full overload):**
- `directory` (`string`) — Directory path within the bucket (empty string for root)
- `storageBucketName` (`string`) — Name of the storage bucket
- `folderPath` (`string`) — Orchestrator folder
- `recursive` (`bool`) — Whether to list files in subdirectories
- `filter` (`string`) — File name filter pattern
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `IEnumerable<StorageFileInfo>` — Collection of file info objects with name, path, and size details.

---

### `void UploadStorageFile(string destination, IResource fileResource, string storageBucketName)`
### `void UploadStorageFile(string destination, IResource fileResource, string storageBucketName, string folderPath)`
### `void UploadStorageFile(string destination, IResource fileResource, string storageBucketName, string folderPath, int timeoutMS)`

Uploads a local file to an Orchestrator storage bucket.

**Parameters:**
- `destination` (`string`) — Target path within the bucket
- `fileResource` (`IResource`) — Local file resource to upload
- `storageBucketName` (`string`) — Name of the storage bucket
- `folderPath` (`string`) — Orchestrator folder
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `void`

---

### `string ReadStorageText(string path, string storageBucketName)`
### `string ReadStorageText(string path, string storageBucketName, string folderPath)`
### `string ReadStorageText(string path, string storageBucketName, string folderPath, string encoding, int timeoutMS)`

Reads the text content of a file directly from an Orchestrator storage bucket.

**Parameters (full overload):**
- `path` (`string`) — File path within the bucket
- `storageBucketName` (`string`) — Name of the storage bucket
- `folderPath` (`string`) — Orchestrator folder
- `encoding` (`string`) — Text encoding (e.g., `"UTF-8"`)
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `string` — Text content of the storage file.

---

### `void WriteStorageText(string path, string text, string storageBucketName)`
### `void WriteStorageText(string path, string text, string storageBucketName, string folderPath)`
### `void WriteStorageText(string path, string text, string storageBucketName, string folderPath, string encoding, int timeoutMS)`

Writes text content directly to a file in an Orchestrator storage bucket.

**Parameters (full overload):**
- `path` (`string`) — Target file path within the bucket
- `text` (`string`) — Text content to write
- `storageBucketName` (`string`) — Name of the storage bucket
- `folderPath` (`string`) — Orchestrator folder
- `encoding` (`string`) — Text encoding (e.g., `"UTF-8"`)
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `void`

---

## Orchestrator HTTP & Alerts

### `int OrchestratorHTTPRequest(OrchestratorAPIHttpMethods method, string relativeEndpoint)`
### `int OrchestratorHTTPRequest(OrchestratorAPIHttpMethods method, string relativeEndpoint, out Dictionary<string, string> responseHeaders, out string result)`
### `int OrchestratorHTTPRequest(OrchestratorAPIHttpMethods method, string relativeEndpoint, string jSONPayload, string folderPath)`
### `int OrchestratorHTTPRequest(OrchestratorAPIHttpMethods method, string relativeEndpoint, string jSONPayload, out Dictionary<string, string> responseHeaders, out string result, string folderPath)`
### `int OrchestratorHTTPRequest(OrchestratorAPIHttpMethods method, string relativeEndpoint, string jSONPayload, string folderPath, out Dictionary<string, string> responseHeaders, out string result, int timeoutMS)`

Makes an HTTP request to the Orchestrator API.

**Parameters (full overload):**
- `method` (`OrchestratorAPIHttpMethods`) — HTTP method: GET, POST, PUT, PATCH, or DELETE
- `relativeEndpoint` (`string`) — API endpoint path relative to the Orchestrator base URL (e.g., `"/odata/Jobs"`)
- `jSONPayload` (`string`) — Request body as a JSON string
- `folderPath` (`string`) — Orchestrator folder for the X-UIPATH-OrganizationUnitId header
- `responseHeaders` (`out Dictionary<string, string>`) — Receives the HTTP response headers
- `result` (`out string`) — Receives the HTTP response body as a string
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `int` — HTTP status code (e.g., `200`, `201`, `404`).

---

### `void RaiseAlert(AlertSeverity severity, string notification)`
### `void RaiseAlert(AlertSeverity severity, string notification, string folderPath)`
### `void RaiseAlert(AlertSeverity severity, string notification, string folderPath, int timeoutMS)`

Raises an alert in Orchestrator.

**Parameters:**
- `severity` (`AlertSeverity`) — Alert severity level
- `notification` (`string`) — Alert message text
- `folderPath` (`string`) — Orchestrator folder
- `timeoutMS` (`int`) — Timeout in milliseconds

**Returns:** `void`

---

## Options & Configuration Classes

### `RunJobOptionalParameters`

Additional optional parameters for `RunJob` and `RunJobAsync`. Namespace: `UiPath.Activities.System.Jobs.Coded` (auto-imported).

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `TimeoutMS` | `int` | `600000` | Maximum time to wait for job completion in milliseconds (10 minutes) |
| `ContinueOnError` | `bool` | `false` | Whether to continue workflow execution if the job fails |
| `FailWhenJobFails` | `bool` | `false` | Whether to mark this workflow as failed if the job fails |

---

## Enum Reference

**`OrchestratorAPIHttpMethods`**: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`

**`InvokeProcessTargetSession`**: `Current`, `ProcessDefault`, `Main`, `Child`

**`LogEntryType`**: `No`, `OnlyInvocation`, `WithArguments`

**`LogExitType`**: `No`, `OnlySuccessfulReturn`, `WithArguments`

**`AlertSeverity`**: `Info`, `Success`, `Warning`, `Error`, `Fatal`

**`StopStrategy`**: `Stop`, `Kill`

**`QueueItemStates`** (flags): `All`, `New`, `InProgress`, `Failed`, `Successful`, `Abandoned`, `Retried`, `Deleted`

**`ReferenceFilterStrategy`**: `StartsWith`, `Equals`

**`QueueItemPriority`**: `High`, `Normal`, `Low`

**`ProcessingStatus`**: `Successful`, `Failed`

**`ErrorType`**: `Business`, `Application`

**`FileConflictBehavior`**: `Replace`, `Fail`, `Rename`

**`ArchiveCompressionLevel`**: `None`, `Fast`, `Normal`, `Maximum`

**`CodePages`**: Encoding identifiers (94 values). Common: `Default`, `UTF_8`, `UTF_16`, `WINDOWS_1252`, `ISO_8859_1`

---

## Common Patterns

### Run an Orchestrator Job and Process Output

```csharp
[Workflow]
public void Execute()
{
    var opts = new RunJobOptionalParameters
    {
        TimeoutMS = 120000,
        FailWhenJobFails = true
    };

    var (jobData, outputJson) = system.RunJob(
        processName: "DataProcessingProcess",
        orchestratorFolderPath: "Finance/Automation",
        inputArguments: new { Month = "March", Year = 2026 },
        runJobOptionalParameters: opts
    );

    Log($"Job {jobData.Id} completed. Output: {outputJson}");
}
```

---

### Queue-Based Transaction Processing

```csharp
[Workflow]
public void Execute()
{
    // Get the next transaction item
    var item = system.GetTransactionItem("InvoiceQueue", "Finance");
    if (item == null) return;

    try
    {
        // Process the transaction
        var invoiceId = item.SpecificContent["InvoiceId"]?.ToString();
        system.SetTransactionProgress(item, $"Processing invoice {invoiceId}");

        // ... processing logic ...

        system.SetTransactionStatus(item, ProcessingStatus.Successful);
    }
    catch (Exception ex)
    {
        system.SetTransactionStatus(
            item,
            ProcessingStatus.Failed,
            folderPath: "Finance",
            analytics: null,
            output: null,
            details: ex.Message,
            errorType: ErrorType.Application,
            reason: "Invoice processing error"
        );
    }
}
```

---

### File Operations: Read, Process, and Write

```csharp
[Workflow]
public void Execute()
{
    // Check if the source file exists
    if (!system.FileExists(@"C:\Data\input.txt"))
    {
        Log("Input file not found");
        return;
    }

    var resource = system.GetResourceForLocalPath(@"C:\Data\input.txt", PathType.File);
    string content = system.ReadTextFile(resource);

    // Process: extract emails and replace sensitive data
    var emails = system.ExtractEmails(content, ignoreDuplicates: true);
    string sanitized = system.Replace(content, @"\d{4}-\d{4}-\d{4}-\d{4}", "****-****-****-****");

    // Write to output
    var outputFile = system.CreateFile("output.txt", @"C:\Data");
    system.WriteTextFile(sanitized, outputFile);

    Log($"Found {emails.Count()} email addresses. Output written.");
}
```

---

### Storage Bucket Workflow

```csharp
[Workflow]
public void Execute()
{
    const string bucket = "ReportsBucket";
    const string folder = "Finance";

    // List available reports
    var files = system.ListStorageFiles("reports/2026", bucket, folder, recursive: false, filter: "*.csv", timeoutMS: 30000);

    foreach (var file in files)
    {
        // Download each report
        var localFile = system.DownloadStorageFile(file.FileFullPath, bucket, folder);
        Log($"Downloaded: {localFile.LocalPath}");

        // Process the file content
        string csvContent = system.ReadTextFile(localFile);
        // ... processing ...

        // Upload processed version
        system.UploadStorageFile($"processed/{Path.GetFileName(file.FileFullPath)}", localFile, bucket, folder);
    }
}
```

---

### Asset and Credential Retrieval

```csharp
[Workflow]
public void Execute()
{
    // Get a plain asset
    string apiUrl = (string)system.GetAsset("ExternalAPIUrl", "SharedAssets");

    // Get credentials
    var (userName, password) = system.GetCredential("ExternalAPICredential", "SharedAssets");

    // Use credentials to authenticate (SecureString → plain text conversion where required)
    Log($"Connecting to {apiUrl} as {userName}");
    // ... use credentials ...

    // Update an asset after processing
    system.SetAsset("2026-03-23", "LastRunDate", "SharedAssets");
}
```
