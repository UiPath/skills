# UiPath System Activities

`UiPath.System.Activities`

Core general-purpose activities for every UiPath workflow. Covers file and folder operations, DataTable manipulation, text and date processing, collections, dialog boxes, credential management, environment interaction, workflow control, Orchestrator integration (queues, assets, jobs, storage), triggers, and scripting.

## Documentation

- [XAML Activities Reference](activities/) — Per-activity documentation for XAML workflows

## Activities

### Workflow

| Activity | File | Description |
|----------|------|-------------|
| [While](activities/While.md) | `While.md` | Repeatedly executes contained activities while a condition is `True`. |
| [Do While](activities/DoWhile.md) | `DoWhile.md` | Executes contained activities once, then repeats while a condition is `True`. |
| [For Each](activities/ForEach.md) | `ForEach.md` | Iterates over each element in a collection. |
| [Repeat Number of Times](activities/RepeatNumberOfTimesX.md) | `RepeatNumberOfTimesX.md` | Repeats contained activities a fixed number of times. |
| [Else If](activities/ElseIf.md) | `ElseIf.md` | Multi-branch conditional — executes the first branch whose condition is `True`. |
| [Retry Scope](activities/RetryScope.md) | `RetryScope.md` | Retries contained activities while a condition is not met or an error is thrown. |
| [Invoke Workflow File](activities/InvokeWorkflow.md) | `InvokeWorkflow.md` | Invokes another XAML workflow file with optional arguments. |
| [Invoke Process](activities/InvokeProcess.md) | `InvokeProcess.md` | Launches an external application or executable. |
| [Run Parallel Process](activities/BeginProcess.md) | `BeginProcess.md` | Starts an Orchestrator process in the background without waiting for it to complete. |
| [Evaluate Business Rule](activities/EvaluateBusinessRule.md) | `EvaluateBusinessRule.md` | Evaluates a DMN business rule file against input data. |
| [Get Current Job Info](activities/GetCurrentJobInfo.md) | `GetCurrentJobInfo.md` | Returns information about the currently running Orchestrator job. |
| [Comment](activities/Comment.md) | `Comment.md` | Design-time annotation; has no effect at runtime. |

### Workflow Control

| Activity | File | Description |
|----------|------|-------------|
| [Disabled Activities](activities/CommentOut.md) | `CommentOut.md` | Container whose contents are never executed at runtime. |
| [Break](activities/Break.md) | `Break.md` | Exits the enclosing loop or Trigger Scope. |
| [Continue](activities/Continue.md) | `Continue.md` | Skips the rest of the current loop iteration and starts the next. |
| [Return](activities/Return.md) | `Return.md` | Immediately exits the current workflow. |
| [Workflow Placeholder](activities/Placeholder.md) | `Placeholder.md` | Design-time placeholder for an activity to be added later. |

### Workflow Checkpoint

| Activity | File | Description |
|----------|------|-------------|
| [Check True](activities/CheckTrue.md) | `CheckTrue.md` | Asserts that a Boolean expression evaluates to `True`; throws on failure. |
| [Check False](activities/CheckFalse.md) | `CheckFalse.md` | Asserts that a Boolean expression evaluates to `False`; throws on failure. |

---

### Collections

| Activity | File | Description |
|----------|------|-------------|
| [Append Items to Collection](activities/AppendItemToCollection.md) | `AppendItemToCollection.md` | Appends one or more items to the end of a collection. |
| [Build Collection](activities/BuildCollection.md) | `BuildCollection.md` | Creates a new collection from a set of provided items. |
| [Collection to DataTable](activities/CollectionToDataTable.md) | `CollectionToDataTable.md` | Converts a collection to a DataTable. |
| [Exists In Collection](activities/ExistsInCollection.md) | `ExistsInCollection.md` | Checks whether an item exists in a collection; returns its index. |
| [Filter Collection](activities/FilterCollection.md) | `FilterCollection.md` | Filters a collection by a predicate, keeping or removing matching items. |
| [Merge Collections](activities/MergeCollections.md) | `MergeCollections.md` | Combines two collections into one. |
| [Remove From Collection](activities/RemoveFromCollection.md) | `RemoveFromCollection.md` | Removes an item, the item at an index, or all matching items from a collection. |
| [Read List Item](activities/ReadListItem.md) | `ReadListItem.md` | Reads the item at a specified index from a list. |
| [Update List Item](activities/UpdateListItem.md) | `UpdateListItem.md` | Updates the item at a specified index in a list. |

---

### DataTable

| Activity | File | Description |
|----------|------|-------------|
| [For Each Row in Data Table](activities/ForEachRow.md) | `ForEachRow.md` | Iterates over each row in a DataTable. |
| [Add Data Row](activities/AddDataRow.md) | `AddDataRow.md` | Adds a row to a DataTable from an array or a DataRow object. |
| [Remove Data Row](activities/RemoveDataRow.md) | `RemoveDataRow.md` | Removes a row from a DataTable by row object or index. |
| [Add Data Column](activities/AddDataColumn.md) | `AddDataColumn.md` | Adds a column to a DataTable with a specified name and data type. |
| [Remove Data Column](activities/RemoveDataColumn.md) | `RemoveDataColumn.md` | Removes a column from a DataTable by name or index. |
| [Clear Data Table](activities/ClearDataTable.md) | `ClearDataTable.md` | Removes all rows from a DataTable. |
| [Remove Duplicate Rows](activities/RemoveDuplicateRows.md) | `RemoveDuplicateRows.md` | Removes duplicate rows from a DataTable in-place. |
| [Sort Data Table](activities/SortDataTable.md) | `SortDataTable.md` | Sorts a DataTable by a specified column in ascending or descending order. |
| [Merge Data Table](activities/MergeDataTable.md) | `MergeDataTable.md` | Merges a source DataTable into a target DataTable. |
| [Filter Data Table](activities/FilterDataTable.md) | `FilterDataTable.md` | Filters a DataTable rows by one or more conditions. |
| [Join Data Tables](activities/JoinDataTables.md) | `JoinDataTables.md` | Joins two DataTables using Inner, Left, or Full join logic. |
| [Lookup Data Table](activities/LookupDataTable.md) | `LookupDataTable.md` | Looks up a value in a DataTable and returns the cell value and row index. |
| [Generate Data Table From Text](activities/GenerateDataTable.md) | `GenerateDataTable.md` | Parses delimited or fixed-width text into a DataTable. |
| [Output Data Table as Text](activities/OutputDataTable.md) | `OutputDataTable.md` | Converts a DataTable to a formatted text string. |
| [Get Row Item](activities/GetRowItem.md) | `GetRowItem.md` | Reads the value of a cell in a DataRow by column name or index. |
| [Update Row Item](activities/UpdateRowItem.md) | `UpdateRowItem.md` | Sets the value of a cell in a DataRow by column name or index. |

---

### Text & Formatting

| Activity | File | Description |
|----------|------|-------------|
| [Combine Text](activities/CombineText.md) | `CombineText.md` | Joins multiple text values with an optional separator. |
| [Split Text](activities/SplitText.md) | `SplitText.md` | Splits a string by a delimiter into a collection of substrings. |
| [Find and Replace](activities/FindAndReplace.md) | `FindAndReplace.md` | Finds and replaces all occurrences of a substring. |
| [Change Case](activities/ChangeCase.md) | `ChangeCase.md` | Changes the case of a string (upper, lower, title, sentence). |
| [Text to Left/Right](activities/TextToLeftRight.md) | `TextToLeftRight.md` | Extracts the text to the left or right of a delimiter. |
| [Extract Text](activities/ExtractText.md) | `ExtractText.md` | Extracts text between anchors, from URLs, emails, or HTML. |
| [Is Text Matching](activities/IsMatch.md) | `IsMatch.md` | Tests whether a string matches a regular expression pattern. |
| [Find Matching Patterns](activities/Matches.md) | `Matches.md` | Finds all regex matches within a string. |
| [Replace Matching Patterns](activities/Replace.md) | `Replace.md` | Replaces all regex matches in a string with a replacement. |
| [Format Date as Text](activities/FormatDateAsText.md) | `FormatDateAsText.md` | Formats a `DateTime` value as a string using a format pattern. |
| [Add or Subtract from Date](activities/AddOrSubtractFromDate.md) | `AddOrSubtractFromDate.md` | Adds or subtracts a duration from a date/time value. |
| [Extract Date and Time from Text](activities/ExtractDateTime.md) | `ExtractDateTime.md` | Parses a `DateTime` from a string using a format or culture. |

---

### File System

| Activity | File | Description |
|----------|------|-------------|
| [Copy File](activities/CopyFile.md) | `CopyFile.md` | Copies a file to a new location. |
| [Move File](activities/MoveFile.md) | `MoveFile.md` | Moves a file to a new location. |
| [Rename File](activities/RenameFileX.md) | `RenameFileX.md` | Renames a file. |
| [Delete File or Folder](activities/Delete.md) | `Delete.md` | Deletes a file or folder at the specified path. |
| [Create File](activities/CreateFile.md) | `CreateFile.md` | Creates a new file, optionally with initial content. |
| [Copy Folder](activities/CopyFolderX.md) | `CopyFolderX.md` | Copies a folder and all its contents to a new location. |
| [Create Folder](activities/CreateDirectory.md) | `CreateDirectory.md` | Creates a new directory at the specified path. |
| [Get Local File or Folder](activities/PathExists.md) | `PathExists.md` | Opens a browse dialog to select a file or folder path. |
| [Read Text File](activities/ReadTextFile.md) | `ReadTextFile.md` | Reads the entire content of a text file into a string. |
| [Write Text File](activities/WriteTextFile.md) | `WriteTextFile.md` | Writes text to a file, overwriting or creating it. |
| [Append Line](activities/AppendLine.md) | `AppendLine.md` | Appends a line of text to a file. |
| [Compress/Zip Files](activities/CompressFiles.md) | `CompressFiles.md` | Compresses files or folders into a ZIP or GZip archive. |
| [Extract/Unzip Files](activities/ExtractFiles.md) | `ExtractFiles.md` | Extracts files from a ZIP or GZip archive. |
| [Download File from URL](activities/DownloadFileFromUrl.md) | `DownloadFileFromUrl.md` | Downloads a file from a URL to a local path. |
| [Wait for Download](activities/GetLastDownloadedFile.md) | `GetLastDownloadedFile.md` | Waits for a file download to complete and returns the file path. **Windows only.** |

---

### System

| Activity | File | Description |
|----------|------|-------------|
| [Message Box](activities/MessageBox.md) | `MessageBox.md` | Displays a dialog box with a message and configurable buttons. **Windows only.** |
| [Get Username/Password](activities/GetUsernamePasswordX.md) | `GetUsernamePasswordX.md` | Displays a credential dialog and returns the entered username and password. **Windows only.** |
| [Get Environment Variable](activities/GetEnvironmentVariable.md) | `GetEnvironmentVariable.md` | Reads the value of an environment variable. |
| [Set Environment Variable](activities/SetEnvironmentVariable.md) | `SetEnvironmentVariable.md` | Sets the value of an environment variable. |
| [Get Environment Folder](activities/GetEnvironmentFolder.md) | `GetEnvironmentFolder.md` | Returns the path of a special system folder (Desktop, Temp, etc.). |
| [Beep](activities/Beep.md) | `Beep.md` | Plays the system beep sound. |
| [Get Processes](activities/GetProcesses.md) | `GetProcesses.md` | Returns the list of currently running processes. |
| [Kill Process](activities/KillProcess.md) | `KillProcess.md` | Terminates a running process by name or process object. |
| [Invoke VBScript](activities/InvokeVBScript.md) | `InvokeVBScript.md` | Executes a VBScript file or inline script. **Windows only.** |
| [Invoke Com Method](activities/InvokeComMethod.md) | `InvokeComMethod.md` | Invokes a method on a COM object. **Windows only.** |
| [Invoke Code](activities/InvokeCode.md) | `InvokeCode.md` | Executes inline C# or VB.NET code within the workflow. |
| [Change Type](activities/ChangeType.md) | `ChangeType.md` | Converts a value to a specified type `T`. |

### Timers

| Activity | File | Description |
|----------|------|-------------|
| [Timeout Scope](activities/TimeoutScope.md) | `TimeoutScope.md` | Executes contained activities within a time limit; throws on timeout. |
| [Start Timer](activities/StartTimer.md) | `StartTimer.md` | Starts a new timer and returns a timer handle. |
| [Stop Timer](activities/StopTimer.md) | `StopTimer.md` | Stops a running timer. |
| [Resume Timer](activities/ResumeTimer.md) | `ResumeTimer.md` | Resumes a previously stopped timer. |
| [Reset Timer](activities/ResetTimer.md) | `ResetTimer.md` | Resets a timer back to zero. |

### Logging

| Activity | File | Description |
|----------|------|-------------|
| [Log Message](activities/LogMessage.md) | `LogMessage.md` | Logs a message at a specified log level. |
| [Add Log Fields](activities/AddLogFields.md) | `AddLogFields.md` | Adds structured fields to all subsequent log entries. |
| [Remove Log Fields](activities/RemoveLogFields.md) | `RemoveLogFields.md` | Removes previously added structured log fields. |
| [Report Status](activities/ReportStatus.md) | `ReportStatus.md` | Sends a status message to Orchestrator for the current job. |

---

### Orchestrator — Queues

| Activity | File | Description |
|----------|------|-------------|
| [Add Queue Item](activities/AddQueueItem.md) | `AddQueueItem.md` | Adds a new item to an Orchestrator queue. |
| [Add Transaction Item](activities/AddTransactionItem.md) | `AddTransactionItem.md` | Adds an item to a queue and immediately sets it to In Progress. |
| [Bulk Add Queue Items](activities/BulkAddQueueItems.md) | `BulkAddQueueItems.md` | Adds multiple queue items from a DataTable in a single call. |
| [Get Transaction Item](activities/GetQueueItem.md) | `GetQueueItem.md` | Retrieves the next available item from a queue for processing. |
| [Get Queue Items](activities/GetQueueItems.md) | `GetQueueItems.md` | Retrieves a filtered list of queue items. |
| [Delete Queue Items](activities/DeleteQueueItems.md) | `DeleteQueueItems.md` | Deletes queue items matching specified criteria. |
| [Postpone Transaction Item](activities/PostponeTransactionItem.md) | `PostponeTransactionItem.md` | Postpones a transaction item to a future date. |
| [Set Transaction Progress](activities/SetTransactionProgress.md) | `SetTransactionProgress.md` | Updates the progress notes on a transaction item. |
| [Set Transaction Status](activities/SetTransactionStatus.md) | `SetTransactionStatus.md` | Marks a transaction item as Successful, Failed, or a Business Exception. |
| [Wait Queue Item](activities/WaitQueueItem.md) | `WaitQueueItem.md` | Waits for a specific queue item (by reference) to become available. |
| [New Item Added to Queue](activities/QueueTrigger.md) | `QueueTrigger.md` | Trigger scope that fires when a new item is added to a queue. |

### Orchestrator — Assets & Credentials

| Activity | File | Description |
|----------|------|-------------|
| [Get Asset](activities/GetRobotAsset.md) | `GetRobotAsset.md` | Retrieves an asset value from Orchestrator. |
| [Set Asset](activities/SetAsset.md) | `SetAsset.md` | Updates an asset value in Orchestrator. |
| [Get Credential](activities/GetRobotCredential.md) | `GetRobotCredential.md` | Retrieves a credential asset (username + password) from Orchestrator. |
| [Set Credential](activities/SetCredential.md) | `SetCredential.md` | Updates a credential asset in Orchestrator. |
| [Get Secret](activities/GetSecret.md) | `GetSecret.md` | Retrieves a secret value from Orchestrator. |
| [Set Secret](activities/SetSecret.md) | `SetSecret.md` | Updates a secret value in Orchestrator. |

### Orchestrator — Storage

| Activity | File | Description |
|----------|------|-------------|
| [Upload Storage File](activities/UploadStorageFile.md) | `UploadStorageFile.md` | Uploads a local file to an Orchestrator storage bucket. |
| [Download Storage File](activities/DownloadStorageFile.md) | `DownloadStorageFile.md` | Downloads a file from an Orchestrator storage bucket. |
| [List Storage Files](activities/ListStorageFiles.md) | `ListStorageFiles.md` | Lists files in an Orchestrator storage bucket. |
| [Delete Storage File](activities/DeleteStorageFile.md) | `DeleteStorageFile.md` | Deletes a file from an Orchestrator storage bucket. |
| [Read Storage Text](activities/ReadStorageText.md) | `ReadStorageText.md` | Reads text content from an Orchestrator storage bucket. |
| [Write Storage Text](activities/WriteStorageText.md) | `WriteStorageText.md` | Writes text content to an Orchestrator storage bucket. |

### Orchestrator — Jobs

| Activity | File | Description |
|----------|------|-------------|
| [Start Job](activities/StartJob.md) | `StartJob.md` | Starts an Orchestrator job (process execution) and returns job IDs. |
| [Stop Job](activities/StopJob.md) | `StopJob.md` | Stops one or more running Orchestrator jobs. |
| [Get Jobs](activities/GetJobs.md) | `GetJobs.md` | Retrieves a filtered list of Orchestrator jobs. |
| [Run Job](activities/RunJob.md) | `RunJob.md` | Starts a job and suspends the workflow until it completes (requires persistence). |
| [Should Stop](activities/ShouldStop.md) | `ShouldStop.md` | Checks whether a Stop command has been issued for the current job. |

### Orchestrator — Alerts & API

| Activity | File | Description |
|----------|------|-------------|
| [Raise Alert](activities/RaiseAlert.md) | `RaiseAlert.md` | Creates an alert in Orchestrator. |
| [Send Email Notification](activities/SendEmailNotification.md) | `SendEmailNotification.md` | Sends an email via the Orchestrator Notification Service. |
| [Orchestrator HTTP Request](activities/OrchestratorHttpRequest.md) | `OrchestratorHttpRequest.md` | Makes an authenticated HTTP request to the Orchestrator REST API. |

### Orchestrator — Process Tracking

| Activity | File | Description |
|----------|------|-------------|
| [Process Tracking Scope](activities/ProcessTrackingScope.md) | `ProcessTrackingScope.md` | Container scope for process/task tracking. |
| [Track Object](activities/TrackObject.md) | `TrackObject.md` | Records a business object interaction in process tracking. |
| [Set Task Status](activities/SetTaskStatus.md) | `SetTaskStatus.md` | Updates the status of a tracked task. |
| [Set Trace Status](activities/SetTraceStatus.md) | `SetTraceStatus.md` | Updates the status of a process trace. |

### Triggers

| Activity | File | Description |
|----------|------|-------------|
| [Manual Trigger](activities/RuntimeContext.md) | `RuntimeContext.md` | Trigger scope that fires on manual job start. |
| [Time Trigger](activities/TimeTrigger.md) | `TimeTrigger.md` | Trigger scope that fires on a cron schedule or simplified time interval. |
| [New Item Added to Queue](activities/QueueTrigger.md) | `QueueTrigger.md` | Trigger scope that fires when a new item is added to a queue. |
