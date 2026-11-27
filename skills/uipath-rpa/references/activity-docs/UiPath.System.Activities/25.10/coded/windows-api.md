# System — Full API Reference

Complete reference for `ISystemService` accessed via the `system` service accessor. For general info see [system.md](system.md).

---

## File Operations

### CopyFile

Copies a file to another location.

```csharp
void CopyFile(string path, string destination, bool overwrite);
```

| Parameter | Type | Description |
|---|---|---|
| `path` | `string` | Path of the file to copy |
| `destination` | `string` | Destination folder |
| `overwrite` | `bool` | Overwrite existing file in destination |

### CreateFile

Creates a file in the specified location. Returns an `ILocalResource` reference.

```csharp
ILocalResource CreateFile(string name, string path);
```

| Parameter | Type | Description |
|---|---|---|
| `name` | `string` | Name of the file to create |
| `path` | `string` | Folder where the file is created |

### CreateFolder

Creates a folder. Returns an `ILocalResource` reference.

```csharp
ILocalResource CreateFolder(string path);
```

### DeleteFileOrFolder

Deletes a file or folder.

```csharp
void DeleteFileOrFolder(ILocalResource resourceFile);
```

### MoveFile

Moves a file to another location.

```csharp
void MoveFile(IResource pathResource, IResource destinationResource, bool overwrite);
```

### CopyFolder

Copies a folder to another location.

```csharp
void CopyFolder(string from, string to, bool overwrite, bool includeSubfolder);
void CopyFolder(string from, string to);  // defaults: overwrite=false, no subfolders
```

### PathExists

Checks if a file or folder path exists.

```csharp
bool PathExists(string path, PathType pathType, out ILocalResource resource);
bool PathExists(string path, PathType pathType);
bool PathExists(string path, out ILocalResource resource);
bool PathExists(string path);
```

### FileExists / FolderExists

Convenience methods to check file or folder existence.

```csharp
bool FileExists(string path);
bool FolderExists(string path);
```

### GetResourceForLocalPath

Builds an `IResource` from a local path.

```csharp
IResource GetResourceForLocalPath(string path, PathType pathType);
```

### ReadTextFile

Reads all text from a file.

```csharp
string ReadTextFile(IResource file, string encoding);
string ReadTextFile(IResource file);  // auto-detects encoding
```

### WriteTextFile

Writes text to a file, replacing existing content.

```csharp
void WriteTextFile(string text, ILocalResource file, string encoding);
void WriteTextFile(string text, ILocalResource file);
```

### AppendLine

Appends text to a file. Creates the file if it doesn't exist.

```csharp
void AppendLine(string text, ILocalResource file, bool useDefaultEncoding, string encoding);
void AppendLine(string text, ILocalResource file);
```

---

## Archive/Compression

### ExtractUnzipFiles

Extracts all contents of a zip file. Returns references to extracted files.

```csharp
ILocalResource[] ExtractUnzipFiles(IResource file, string destinationFolder, bool extractToADedicatedFolder, string password, CodePages codePage);
ILocalResource[] ExtractUnzipFiles(IResource file, string destinationFolder);
ILocalResource[] ExtractUnzipFiles(IResource file);
```

| Parameter | Type | Description |
|---|---|---|
| `file` | `IResource` | The zip file to extract |
| `destinationFolder` | `string` | Extraction destination |
| `extractToADedicatedFolder` | `bool` | Create a subfolder named after the zip |
| `password` | `string` | Password for protected archives |
| `codePage` | `CodePages` | Text encoding for file names |

### CompressZipFiles

Compresses files into a zip archive. Returns reference to the created file.

```csharp
ILocalResource CompressZipFiles(IEnumerable<IResource> resourcesToArchive, string compressedFileName, string password, ArchiveCompressionLevel compressionLevel, CodePages codePage, bool overrideExistingFile);
ILocalResource CompressZipFiles(IEnumerable<IResource> resourcesToArchive, string compressedFileName);
```

| Parameter | Type | Description |
|---|---|---|
| `resourcesToArchive` | `IEnumerable<IResource>` | Files/folders to compress |
| `compressedFileName` | `string` | Output zip file name |
| `password` | `string` | Password protection |
| `compressionLevel` | `ArchiveCompressionLevel` | `Optimal`, `Fastest`, or `NoCompression` |
| `codePage` | `CodePages` | Text encoding for file names |
| `overrideExistingFile` | `bool` | Replace existing zip file |

---

## DataTable Operations

### AddDataRow

Adds a row to a DataTable.

```csharp
void AddDataRow(ref DataTable dataTable, DataRow dataRow);
```

### RemoveDataRow

Removes a row at the specified index.

```csharp
void RemoveDataRow(ref DataTable dataTable, int rowIndex);
```

### RemoveDataColumn

Removes a column by name.

```csharp
void RemoveDataColumn(ref DataTable dataTable, string columnName);
```

### ClearDataTable

Clears all data from a DataTable.

```csharp
void ClearDataTable(ref DataTable dataTable);
```

### OutputDataTable

Writes a DataTable to a CSV-formatted string.

```csharp
string OutputDataTable(DataTable dataTable);
```

### SortDataTable

Sorts a DataTable by a column. Returns the sorted DataTable.

```csharp
DataTable SortDataTable(DataTable dataTable, string columnName, SortOrder sortOrder);
DataTable SortDataTable(DataTable dataTable, string columnName);  // ascending
```

### MergeDataTable

Merges a source DataTable into a destination DataTable.

```csharp
void MergeDataTable(DataTable sourceDataTable, ref DataTable destinationDataTable, MissingSchemaAction missingSchemaAction);
void MergeDataTable(DataTable sourceDataTable, ref DataTable destinationDataTable);
```

### RemoveDuplicateRows

Removes duplicate rows, keeping only the first occurrence.

```csharp
DataTable RemoveDuplicateRows(DataTable dataTable);
```

### LookupDataTable

Searches for a value in a DataTable column and returns the corresponding value from a target column.

```csharp
object LookupDataTable(DataTable dataTable, string lookupValue, string lookupColumnName, string targetColumnName, out int rowIndex);
object LookupDataTable(DataTable dataTable, string lookupValue, string lookupColumnName, string targetColumnName);
```

### GetRowItem

Gets a value from a DataRow by column name.

```csharp
object GetRowItem(DataRow row, string columnName);
```

### UpdateRowItem

Sets a value in a DataRow by column name.

```csharp
void UpdateRowItem(object value, DataRow row, string columnName);
```

---

## Text Operations

### Replace (Regex)

Replaces text using a regular expression pattern.

```csharp
string Replace(string input, string pattern, string replacement, RegexOptions regexOption);
string Replace(string input, string pattern, string replacement);
```

### FindAndReplace

Searches for text and replaces all occurrences.

```csharp
string FindAndReplace(string valueToFind, string source, string replaceWith, bool matchCase);
```

### ExtractTextOccurrences

Extracts all text between two specified strings.

```csharp
IEnumerable<string> ExtractTextOccurrences(string source, string startingText, string endingText, bool ignoreDuplicates = false, bool matchCase = false);
```

### ExtractEmails

Extracts email addresses from text.

```csharp
IEnumerable<string> ExtractEmails(string source, bool ignoreDuplicates = false);
```

### ExtractUrls

Extracts URLs from text.

```csharp
IEnumerable<string> ExtractUrls(string source, bool extractBaseURLOnly = false, bool ignoreDuplicates = false);
```

### ExtractTextFromHTML

Removes HTML tags and returns plain text.

```csharp
string ExtractTextFromHTML(string source);
```

### CombineText

Combines a collection of strings using a separator.

```csharp
string CombineText(IEnumerable<string> source, SeparatorOptions separatorKey);
string CombineText(IEnumerable<string> source, string separator);
```

### SplitText

Splits text into substrings using a separator.

```csharp
IEnumerable<string> SplitText(string source, SeparatorOptions separatorKey);
IEnumerable<string> SplitText(string source, string separator);
```

### ChangeCase

Converts text to a specified case.

```csharp
string ChangeCase(string source, ChangeCaseOptions changeCaseOptions);
```

`ChangeCaseOptions`: `UPPERCASE`, `lowercase`, `TitleCase`, `SentenceCase`

---

## DateTime Operations

### FormatDateAsText

Formats a DateTime as a string.

```csharp
string FormatDateAsText(DateTime source, string format, CultureInfo localizationCode);
```

| Parameter | Type | Description |
|---|---|---|
| `source` | `DateTime` | Source date |
| `format` | `string` | Format string (e.g., `"dd-MM-yyyy"`, `"yyyy-MM-dd HH:mm:ss"`) |
| `localizationCode` | `CultureInfo` | Localization (e.g., `CultureInfo.InvariantCulture`) |

### ExtractDateAndTimeFromText

Extracts all DateTime occurrences from text matching a format.

```csharp
IEnumerable<DateTime> ExtractDateAndTimeFromText(string format, string source, CultureInfo localizationCode);
```

### AddOrSubtractFromDate

Adds or subtracts a time unit from a date.

```csharp
DateTime AddOrSubtractFromDate(DateTime source, UnitsOfTime unitOfTime, int amountOfTime, DateOperations selectedOperation);
```

| Parameter | Type | Description |
|---|---|---|
| `source` | `DateTime` | Source date |
| `unitOfTime` | `UnitsOfTime` | Milliseconds, Seconds, Minutes, Hours, Days, Months, Years |
| `amountOfTime` | `int` | Amount to add/subtract |
| `selectedOperation` | `DateOperations` | `Add` or `Subtract` (full type: `UiPath.Activities.System.Date.AddOrSubtractFromDate.DateOperations`) |

---

## Queue/Transaction Items

### AddQueueItem

Adds a new item to an Orchestrator queue with status `New`.

```csharp
void AddQueueItem(string queueType, string folderPath, DateTime dueDate, Dictionary<string, object> itemInformationCollection, DateTime deferDate, QueueItemPriority priority, string reference, int timeoutMS);
void AddQueueItem(string queueType, string folderPath, Dictionary<string, object> itemInformationCollection);
void AddQueueItem(string queueType, string folderPath);
void AddQueueItem(string queueType);
```

| Parameter | Type | Description |
|---|---|---|
| `queueType` | `string` | Queue name |
| `folderPath` | `string` | Orchestrator folder path |
| `dueDate` | `DateTime` | Deadline date for processing |
| `itemInformationCollection` | `Dictionary<string, object>` | Custom data for the queue item |
| `deferDate` | `DateTime` | Postpone date (do not process before this) |
| `priority` | `QueueItemPriority` | `Low`, `Normal`, or `High` |
| `reference` | `string` | Reference string for the queue item |
| `timeoutMS` | `int` | Timeout in milliseconds (default 30000) |

### AddTransactionItem

Adds a new item and immediately starts a transaction (status = `InProgress`). Returns the `QueueItem`.

```csharp
QueueItem AddTransactionItem(string queueType, string folderPath, string reference, Dictionary<string, object> transactionInformation, int timeoutMS);
QueueItem AddTransactionItem(string queueType, string folderPath);
QueueItem AddTransactionItem(string queueType);
```

### GetTransactionItem

Gets the next available item from a queue and sets its status to `InProgress`.

```csharp
QueueItem GetTransactionItem(string queueType, string folderPath, ReferenceFilterStrategy filterStrategy, string reference, int timeoutMS);
QueueItem GetTransactionItem(string queueType, string folderPath);
QueueItem GetTransactionItem(string queueType);
```

### GetQueueItem

Gets an item from the queue and sets its status to `InProgress`.

```csharp
QueueItem GetQueueItem(string queueType, string folderPath, ReferenceFilterStrategy filterStrategy, string reference, int timeoutMS);
QueueItem GetQueueItem(string queueType, string folderPath);
QueueItem GetQueueItem(string queueType);
```

### GetQueueItems

Retrieves a list of queue items matching filters. Maximum 100 items.

```csharp
IEnumerable<QueueItem> GetQueueItems(string queueName, string folderPath, int? duration, DateTime? from, int? priority, QueueItemStates queueItemStates, DateTime? to, ReferenceFilterStrategy filterStrategy, string reference, int skip, int top, int timeoutMS);
IEnumerable<QueueItem> GetQueueItems(string queueName, string folderPath);
IEnumerable<QueueItem> GetQueueItems(string queueName);
```

| Parameter | Type | Description |
|---|---|---|
| `queueName` | `string` | Queue name |
| `folderPath` | `string` | Orchestrator folder path |
| `duration` | `int?` | Min time (seconds) spent in previous attempt |
| `from` | `DateTime?` | Min creation date filter |
| `priority` | `int?` | Priority filter |
| `queueItemStates` | `QueueItemStates` | State filter |
| `to` | `DateTime?` | Max creation date filter |
| `filterStrategy` | `ReferenceFilterStrategy` | `Equals`, `StartsWith`, or `Contains` |
| `reference` | `string` | Reference filter value |
| `skip` | `int` | Number of items to skip |
| `top` | `int` | Number of items to retrieve (max 100) |
| `timeoutMS` | `int` | Timeout in milliseconds |

### BulkAddQueueItems

Adds multiple queue items from a DataTable. Returns a DataTable with any errors.

```csharp
DataTable BulkAddQueueItems(DataTable queueItemsDataTable, string queueName, string folderPath, CommitTypeEnum commitType, int timeoutMS);
DataTable BulkAddQueueItems(DataTable queueItemsDataTable, string queueName, string folderPath);
DataTable BulkAddQueueItems(DataTable queueItemsDataTable, string queueName);
```

### DeleteQueueItems

Deletes queue items that are in the `New` state.

```csharp
void DeleteQueueItems(IEnumerable<QueueItem> queueItems, string folderPath, int timeoutMS);
void DeleteQueueItems(IEnumerable<QueueItem> queueItems, string folderPath);
void DeleteQueueItems(IEnumerable<QueueItem> queueItems);
```

### SetTransactionStatus

Sets the status of a transaction item to `Successful` or `Failed`.

```csharp
void SetTransactionStatus(QueueItem transactionItem, ProcessingStatus status, string folderPath, Dictionary<string, object> analytics, Dictionary<string, object> output, string details, ErrorType errorType, string reason, int timeoutMS);
void SetTransactionStatus(QueueItem transactionItem, ProcessingStatus status, string folderPath);
void SetTransactionStatus(QueueItem transactionItem, ProcessingStatus status);
```

| Parameter | Type | Description |
|---|---|---|
| `transactionItem` | `QueueItem` | The transaction item to update |
| `status` | `ProcessingStatus` | `Successful` or `Failed` |
| `folderPath` | `string` | Orchestrator folder path |
| `analytics` | `Dictionary<string, object>` | Analytics data |
| `output` | `Dictionary<string, object>` | Output data |
| `details` | `string` | Details about the failure |
| `errorType` | `ErrorType` | `ApplicationException` (retries) or `BusinessException` (no retry) |
| `reason` | `string` | Reason for failure |
| `timeoutMS` | `int` | Timeout in milliseconds |

### SetTransactionProgress

Sets a custom progress string on an in-progress transaction.

```csharp
void SetTransactionProgress(QueueItem transactionItem, string progress, string folderPath, int timeoutMS);
void SetTransactionProgress(QueueItem transactionItem, string progress, string folderPath);
void SetTransactionProgress(QueueItem transactionItem, string progress);
```

### PostponeTransactionItem

Postpones a transaction item with defer and/or due dates.

```csharp
void PostponeTransactionItem(QueueItem transactionItem, DateTime deferDate, string folderPath, DateTime dueDate, int timeoutMS);
void PostponeTransactionItem(QueueItem transactionItem, DateTime deferDate, string folderPath);
void PostponeTransactionItem(QueueItem transactionItem, DateTime deferDate);
```

### WaitQueueItem

Waits for an item to become available in a queue, polling periodically.

```csharp
QueueItem WaitQueueItem(string queueName, string folderPath, int pollTimeMS, ReferenceFilterStrategy filterStrategy, string reference, int timeoutMS);
QueueItem WaitQueueItem(string queueName, string folderPath);
QueueItem WaitQueueItem(string queueName);
```

---

## Assets & Credentials

### GetAsset

Gets an Orchestrator asset value. Returns `object` — cast to the expected type.

```csharp
object GetAsset(string assetName, string folderPath, CacheStrategyEnum cacheStrategy, int timeoutMS);
object GetAsset(string assetName, string folderPath);
object GetAsset(string assetName);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `assetName` | `string` | — | Name of the asset |
| `folderPath` | `string` | `null` | Orchestrator folder path |
| `cacheStrategy` | `CacheStrategyEnum` | `None` | `None`, `PerRobot`, or `Global` |
| `timeoutMS` | `int` | 30000 | Timeout in milliseconds |

### SetAsset

Updates an existing Orchestrator asset value.

```csharp
void SetAsset(object value, string assetName, string folderPath, int timeoutMS);
void SetAsset(object value, string assetName, string folderPath);
void SetAsset(object value, string assetName);
```

### GetCredential

Gets a credential asset (username + secure password).

```csharp
// Returns a tuple
(string userName, SecureString password) GetCredential(string assetName, string folderPath = null, int timeoutMS = 1000, CacheStrategyEnum cacheStrategy = CacheStrategyEnum.None);

// Returns username, outputs password
string GetCredential(string assetName, string folderPath, out SecureString password, CacheStrategyEnum cacheStrategy, int timeoutMS);
```

### SetCredential

Updates an existing credential asset.

```csharp
void SetCredential(string userName, string password, string credentialName, string folderPath, int timeoutMS);
void SetCredential(string userName, string password, string credentialName, string folderPath);
void SetCredential(string userName, string password, string credentialName);
```

---

## Jobs & Processes

### RunJob

Runs a job in Orchestrator and optionally waits for completion. Returns the job data and output as JSON.

```csharp
(OrchestratorJob JobData, string OutputJson) RunJob(string processName, string orchestratorFolderPath = null, object inputArguments = null, bool doNotWait = false, RunJobOptionalParameters runJobOptionalParameters = null);

Task<(OrchestratorJob JobData, string OutputJson)> RunJobAsync(string processName, string orchestratorFolderPath = null, object inputArguments = null, bool doNotWait = false, RunJobOptionalParameters runJobOptionalParameters = null);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `processName` | `string` | — | Name of the process to run |
| `orchestratorFolderPath` | `string` | `null` | Orchestrator folder path |
| `inputArguments` | `object` | `null` | Input arguments for the process |
| `doNotWait` | `bool` | `false` | If `true`, fire-and-forget mode |
| `runJobOptionalParameters` | `RunJobOptionalParameters` | `null` | Additional job parameters |

### InvokeProcess

Invokes a process on the current Robot. Blocking — waits for completion.

```csharp
void InvokeProcess(string processName);
void InvokeProcess(string processName, string folderPath);

// Async variant with full options
Task<Dictionary<string, object>> InvokeProcessAsync(string processName);
Task<Dictionary<string, object>> InvokeProcessAsync(string processName, string folderPath);
Task<Dictionary<string, object>> InvokeProcessAsync(string processName, string folderPath = null, Dictionary<string, object> inArguments = null, Dictionary<string, object> inOutArguments = null, LogEntryType logEntry = LogEntryType.No, LogExitType logExit = LogExitType.No, LogLevel level = LogLevel.Info, InvokeProcessTargetSession targetSession = InvokeProcessTargetSession.Current, TimeSpan timeout = default);
```

### StartJob

Starts a job on Orchestrator and continues execution without waiting.

```csharp
string StartJob(string processName, string folderPath, StartProcessDtoJobPriority jobPriority, bool resumeOnSameContext, out string jobId);
string StartJob(string processName, string folderPath);
string StartJob(string processName, out string jobId, string folderPath);
string StartJob(string processName);
string StartJob(string processName, out string jobId);
```

Returns the process unique identifier. The `jobId` out parameter returns the job unique identifier.

### GetJobs

Retrieves Orchestrator jobs matching a filter.

```csharp
IEnumerable<OrchestratorJob> GetJobs(string filter, JobFilterSettings filterBuilder, string folderPath, int top, int skip, int timeoutMS);
IEnumerable<OrchestratorJob> GetJobs(string filter, JobFilterSettings filterBuilder, string folderPath);
IEnumerable<OrchestratorJob> GetJobs();
```

| Parameter | Type | Description |
|---|---|---|
| `filter` | `string` | OData filter (e.g., `"State eq 'Running'"`) |
| `filterBuilder` | `JobFilterSettings` | Structured filter builder |
| `top` | `int` | Max jobs to retrieve (max 100) |
| `skip` | `int` | Number of jobs to skip |

### StopJob

Stops or kills an Orchestrator job.

```csharp
void StopJob(OrchestratorJob job, StopStrategy strategy, string folderPath, int timeoutMS);
void StopJob(OrchestratorJob job, StopStrategy strategy, string folderPath);
void StopJob(OrchestratorJob job, StopStrategy strategy);
```

`StopStrategy`: `Stop` (graceful) or `Kill` (immediate).

---

## Storage Buckets

### UploadStorageFile

Uploads a local file to an Orchestrator storage bucket.

```csharp
void UploadStorageFile(string destination, IResource fileResource, string storageBucketName, string folderPath, int timeoutMS);
void UploadStorageFile(string destination, IResource fileResource, string storageBucketName, string folderPath);
void UploadStorageFile(string destination, IResource fileResource, string storageBucketName);
```

| Parameter | Type | Description |
|---|---|---|
| `destination` | `string` | Path in the storage bucket |
| `fileResource` | `IResource` | Local file to upload |
| `storageBucketName` | `string` | Name of the storage bucket |
| `folderPath` | `string` | Orchestrator folder path |

### DownloadStorageFile

Downloads a file from a storage bucket. Returns an `ILocalResource` reference.

```csharp
ILocalResource DownloadStorageFile(string path, string storageBucketName, string folderPath, string destination, int timeoutMS);
ILocalResource DownloadStorageFile(string path, string storageBucketName, string folderPath);
ILocalResource DownloadStorageFile(string path, string storageBucketName);
```

### DeleteStorageFile

Deletes a file from a storage bucket.

```csharp
void DeleteStorageFile(string path, string storageBucketName, string folderPath, int timeoutMS);
void DeleteStorageFile(string path, string storageBucketName, string folderPath);
void DeleteStorageFile(string path, string storageBucketName);
```

### ListStorageFiles

Lists files in a storage bucket directory. Returns `IEnumerable<StorageFileInfo>`.

```csharp
IEnumerable<StorageFileInfo> ListStorageFiles(string directory, string storageBucketName, string folderPath, bool recursive, string filter, int timeoutMS);
IEnumerable<StorageFileInfo> ListStorageFiles(string directory, string storageBucketName, string folderPath);
IEnumerable<StorageFileInfo> ListStorageFiles(string directory, string storageBucketName);
```

| Parameter | Type | Description |
|---|---|---|
| `directory` | `string` | Starting directory |
| `storageBucketName` | `string` | Storage bucket name |
| `recursive` | `bool` | Include subdirectories |
| `filter` | `string` | File filter pattern (e.g., `"*.pdf"`) |

### WriteStorageText

Writes text to a file in a storage bucket.

```csharp
void WriteStorageText(string path, string text, string storageBucketName, string folderPath, string encoding, int timeoutMS);
void WriteStorageText(string path, string text, string storageBucketName, string folderPath);
void WriteStorageText(string path, string text, string storageBucketName);
```

### ReadStorageText

Reads text content from a file in a storage bucket.

```csharp
string ReadStorageText(string path, string storageBucketName, string folderPath, string encoding, int timeoutMS);
string ReadStorageText(string path, string storageBucketName, string folderPath);
string ReadStorageText(string path, string storageBucketName);
```

---

## Alerts & Orchestrator HTTP

### RaiseAlert

Raises an alert in Orchestrator.

```csharp
void RaiseAlert(AlertSeverity severity, string notification, string folderPath, int timeoutMS);
void RaiseAlert(AlertSeverity severity, string notification, string folderPath);
void RaiseAlert(AlertSeverity severity, string notification);
```

`AlertSeverity`: `Info`, `Warn`, `Error`, `Fatal`

### OrchestratorHTTPRequest

Performs authenticated HTTP requests against the Orchestrator API. Returns the HTTP status code.

```csharp
int OrchestratorHTTPRequest(OrchestratorAPIHttpMethods method, string relativeEndpoint, string jSONPayload, string folderPath, out Dictionary<string, string> responseHeaders, out string result, int timeoutMS);
int OrchestratorHTTPRequest(OrchestratorAPIHttpMethods method, string relativeEndpoint, string jSONPayload, string folderPath);
int OrchestratorHTTPRequest(OrchestratorAPIHttpMethods method, string relativeEndpoint, string jSONPayload, out Dictionary<string, string> responseHeaders, out string result, string folderPath);
int OrchestratorHTTPRequest(OrchestratorAPIHttpMethods method, string relativeEndpoint);
int OrchestratorHTTPRequest(OrchestratorAPIHttpMethods method, string relativeEndpoint, out Dictionary<string, string> responseHeaders, out string result);
```

| Parameter | Type | Description |
|---|---|---|
| `method` | `OrchestratorAPIHttpMethods` | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` |
| `relativeEndpoint` | `string` | Endpoint relative to the base URI |
| `jSONPayload` | `string` | JSON body for the request |
| `folderPath` | `string` | Orchestrator folder path |
| `responseHeaders` | `out Dictionary<string, string>` | Response headers |
| `result` | `out string` | JSON response body |
| `timeoutMS` | `int` | Timeout in milliseconds |

---

## Network

### DownloadFileFromURLAsync

Downloads a file from a URL. Returns an `ILocalResource` reference.

```csharp
Task<ILocalResource> DownloadFileFromURLAsync(string url, string fileName = default, FileConflictBehavior conflictResolution = FileConflictBehavior.Rename, int timeout = 30000, CancellationToken cancellationToken = default, string userAgentHeaderValue = null);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `url` | `string` | — | URL to download from |
| `fileName` | `string` | auto | File name to save as |
| `conflictResolution` | `FileConflictBehavior` | `Rename` | `Rename`, `Replace`, or `Skip` |
| `timeout` | `int` | 30000 | Timeout in milliseconds |
| `cancellationToken` | `CancellationToken` | `default` | Cancellation token |
| `userAgentHeaderValue` | `string` | `null` | User-Agent header value |
