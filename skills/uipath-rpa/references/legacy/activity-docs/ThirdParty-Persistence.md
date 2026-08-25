# UiPath Persistence Activities - Legacy Reference

## Overview
Long-running workflow persistence: suspend, wait for human/external input, resume. Package: `UiPath.Persistence.Activities`. **#28 by adoption (1.1%)**. Official UiPath package. Source: [UiPath Docs](https://docs.uipath.com/action-center/automation-cloud/latest/user-guide/persistence-activities).

---

## All Activities (20 total, from official docs)

### Form Tasks (Action Center)
| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `Create Form Task` | Create human task with form | TaskTitle, TaskPriority, TaskCatalog, FormData (Dict\<String,Argument\>), Reference, Labels, GenerateInputFields, OrchestratorFolderPath -> TaskObject (FormTaskData) |
| `Wait For Form Task And Resume` | **SUSPEND** until form completed | TaskObject (req), StatusMessage, TimeoutMS (def 30000) -> TaskAction (string), TaskObject (updated) |
| `Create Form` | Design form in Studio | (form designer integration) |

### External Tasks
| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `Create External Task` | Create task for external system | TaskTitle, TaskPriority, TaskCatalog, TaskData (JSON) -> TaskObject |
| `Wait For External Task And Resume` | **SUSPEND** until external completion | TaskObject -> TaskAction, TaskData |

### App Tasks
| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `Create App Task` | Create app-level task | TaskTitle, TaskPriority -> TaskObject |
| `Wait For App Task And Resume` | **SUSPEND** until app task done | TaskObject -> TaskAction |

### Job/Queue Persistence
| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `Start Job And Get Reference` | Start job, get tracking ref | ProcessName, InputArguments -> JobReference |
| `Wait For Job And Resume` | **SUSPEND** until job completes | JobReference -> OutputArguments |
| `Add Queue Item And Get Reference` | Add to queue, get ref | QueueName, Priority, ItemInformation -> QueueItemReference |
| `Wait For Queue Item And Resume` | **SUSPEND** until queue item processed | QueueItemReference -> QueueItemData |

### Timer
| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `Resume After Delay` | **SUSPEND** for duration, release robot | ResumeTime (DateTime) OR Delay (TimeSpan) |

### Task Management (non-suspending)
| Activity | Purpose |
|----------|---------|
| `Assign Tasks` | Assign tasks to users/groups |
| `Complete Task` | Mark task as finished |
| `Forward Task` | Route task to another user |
| `Get Form Tasks` | Retrieve form tasks |
| `Get Task Data` | Get task details |
| `Get App Tasks` | Retrieve app tasks |
| `Add Task Comment` | Append notes to task |
| `Update Task Labels` | Modify task tags |
| `Configure Task Timer` | Set time constraints |

---

## How Suspension Works
1. Workflow hits `Wait For * And Resume` activity
2. **Entire workflow state serialized** to Orchestrator database
3. **Robot license released** - robot freed for other jobs
4. External condition met (human completes form, job finishes, timer expires)
5. Orchestrator triggers resume - **can be on a different machine**
6. State deserialized, execution continues

---

## Create Form Task - Detailed Arguments (from docs)

### Input
| Argument | Type | Description |
|----------|------|-------------|
| `TaskTitle` | String | Title shown in Action Center |
| `TaskPriority` | TaskPriority | Low, Medium, High, Critical |
| `TaskCatalog` | String | Catalog for grouping tasks |
| `FormData` | Dictionary\<String, Argument\> | In/Out/InOut arguments mapped to form fields. **Out and InOut arguments are mapped back after completion.** |
| `Reference` | String | Reference ID for grouping related actions |
| `Labels` | String | Tags for filtering (naming restrictions apply) |
| `GenerateInputFields` | Boolean | Auto-generate form fields from FormData entries |
| `EnableBulkEdit` | Boolean | Enable bulk completion from Action Center |
| `OrchestratorFolderPath` | String | Orchestrator folder (empty = current) |

### Output
| Argument | Type | Description |
|----------|------|-------------|
| `TaskObject` | FormTaskData | Pass to Wait For Form Task And Resume |

---

## Critical Gotchas (Docs + Community Verified)

### Orchestrator Required
1. **Only works when running from Orchestrator** - Studio debug simulates suspension, not real persist/resume
2. **Process must be "Orchestration Process"** (long-running background type) - set in Studio project settings
3. **Requires Orchestrator 2020.10+** for full support
4. **Action Center licensing** required for form tasks

### Serialization (THE #1 FAILURE CAUSE)
5. **ALL variables in scope at suspension must be serializable** - this breaks most first attempts
6. **NOT serializable**: UiElement, Browser, Application handles, COM objects, open file handles
7. **Cannot have open Application/Browser Scope** across a suspension point
8. **DataTable is serializable** but fails with non-serializable column types (e.g., Image columns)
9. **Custom .NET objects** must be `[Serializable]` or implement `ISerializable`

### State Across Suspension
10. **No UI context preserved** - logged-in apps, browser sessions, open windows all lost
11. **Must re-authenticate** everything after resume
12. **Local file paths may not exist** on resume machine - use Orchestrator storage buckets
13. **Resume After Delay releases robot license** - unlike regular Delay which holds it

### Form Tasks
14. **FormData uses Dictionary\<String, Argument\>** not Dictionary\<String, Object\> - Argument type has Direction (In/Out/InOut)
15. **Out/InOut arguments mapped back** to workflow after task completion - this is how you get user input
16. **GenerateInputFields** auto-creates form fields from FormData - convenient but limited customization
17. **Form schema changes break pending tasks** - plan schema updates carefully
18. **StatusMessage** displayed in Orchestrator alongside suspended workflow

### Best Practices
19. **Save data to Orchestrator assets/queues** before suspension - not to local variables
20. **Keep variables minimal at suspension points** - fewer serialization issues
21. **Use Reference field** to group related tasks for easier management
22. **Test in Orchestrator** (not just Studio) - suspension behavior is fundamentally different

### Persistence Trigger Types (from source code)
- `QueueItem` (1) - Resume when queue item processed
- `Job` (2) - Resume when child job completes
- `Task` (3) - Resume when Action Center task completed
- `Timer` (4) - Resume at specific time

### Design-Time Rules
23. **ST-DBP-027**: Warning when persistence activities inside ForEach loops - loop iterator state complicates serialization
24. **NoPersistScope constraint**: Persistence activities CANNOT be inside NoPersistScope/Retry Scope - design-time validation error
25. **Task title max 512 characters** - validated by FormTaskCreateRequest
26. **Debug mode skips persistence** - Studio detects platform ("Studio", "StudioX", "StudioPro", "CommandLine") and polls instead of persisting

### Serializable Types That Work
`String`, `Int32`, `Int64`, `Boolean`, `DateTime`, `Double`, `Decimal`, `DataTable`, `Dictionary<string, object>`, `JObject`, `JArray`, `String[]`, basic .NET collections

### Run Job with Suspend Mode
- RunJob activity has `ExecutionMode` enum: None (fire-and-forget), Busy (poll, robot stays), Suspend (persist, robot freed)
- Suspend mode internally uses `StartJobAndGetReference` + `WaitForJobAndResume` with `TriggerType = Job`
