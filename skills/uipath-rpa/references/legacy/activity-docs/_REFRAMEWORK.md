# UiPath REFramework (Robotic Enterprise Framework) - Complete Reference

## Overview
The REFramework is UiPath's official **State Machine-based project template** for building production-grade automation. It provides built-in retry logic, exception handling, configuration management, and application lifecycle control. It's the standard for transactional, unattended automation.

**Source**: [github.com/UiPath/ReFrameWork](https://github.com/UiPath/ReFrameWork)
**Current Desktop Template**: Studio 25.10 (verified from `C:\Users\alexandru.roman\Documents\UiPath\legacy_tests\`)
**Available in**: VB.NET (`RoboticEnterpriseFramework-VB`) and C# (`RoboticEnterpriseFramework-Csharp`)

---

## 1. File Structure

```
Project Root/
├── Main.xaml                              # Entry point — State Machine (DO NOT rename)
├── project.json                           # Project configuration
├── project.uiproj                         # Studio project file
├── README.md                              # Template readme
├── LICENSE                                # License file
│
├── Data/
│   ├── Config.xlsx                        # Configuration file (Settings/Constants/Assets)
│   ├── Input/                             # Input data files
│   ├── Output/                            # Output data files
│   └── Temp/                              # Temporary files (cleared on init)
│
├── Framework/                             # Core framework workflows
│   ├── InitAllSettings.xaml               # Reads Config.xlsx → Dictionary
│   ├── InitAllApplications.xaml           # Opens/authenticates apps
│   ├── GetTransactionData.xaml            # Gets next transaction item
│   ├── Process.xaml                       # YOUR business logic (CUSTOMIZE THIS)
│   ├── SetTransactionStatus.xaml          # Sets Success/Failed/BusinessException (Flowchart)
│   ├── RetryCurrentTransaction.xaml       # Retry logic with MaxRetryNumber check (Flowchart)
│   ├── CloseAllApplications.xaml          # Gracefully closes apps
│   ├── KillAllProcesses.xaml              # Force-kills app processes
│   └── TakeScreenshot.xaml                # Captures error screenshot
│
├── Exceptions_Screenshots/                # Error screenshots stored here
│
├── Documentation/
│   └── REFramework Documentation-EN.pdf   # Official documentation
│
└── Tests/                                 # Built-in test cases
    ├── GeneralTestCase.xaml               # General test case
    ├── GetTransactionDataTestCase.xaml     # Test GetTransactionData
    ├── InitAllApplicationsTestCase.xaml    # Test InitAllApplications
    ├── InitAllSettingsTestCase.xaml        # Test InitAllSettings
    ├── MainTestCase.xaml                   # Test Main workflow
    ├── ProcessTestCase.xaml               # Test Process workflow
    ├── WorkflowTestCaseTemplate.xaml       # Test template
    └── Tests.xlsx                         # Test data
```

> **Note**: Current template (Studio 25.10) moved `Process.xaml` into `Framework/` folder and added `RetryCurrentTransaction.xaml` as a separate Flowchart workflow for retry logic. Older GitHub version had `Process.xaml` at root and `GetAppCredentials.xaml` (removed in current).

### File Roles

| File | Role | Modify? |
|------|------|---------|
| `Main.xaml` | State Machine orchestrating all states/transitions | RARELY — only to add custom transitions |
| `Framework/Process.xaml` | **YOUR business logic** — called for each transaction | YES — this is where your automation goes |
| `Config.xlsx` | Settings, constants, Orchestrator asset names | YES — add your configuration here |
| `InitAllSettings.xaml` | Reads Config.xlsx into `in_Config` dictionary | RARELY — add custom init logic if needed |
| `InitAllApplications.xaml` | Opens apps (credential retrieval built-in now) | YES — add your app open/login logic |
| `GetTransactionData.xaml` | Gets next queue item or data row to process | YES — configure your transaction source |
| `SetTransactionStatus.xaml` | Updates transaction status (Flowchart: Success/BRE/SE branches) | YES if not using Orchestrator queues |
| `RetryCurrentTransaction.xaml` | Retry logic Flowchart: checks MaxRetryNumber, manages retry counter | RARELY — logic is self-contained |
| `CloseAllApplications.xaml` | Gracefully closes applications | YES — add your app close/logout logic |
| `KillAllProcesses.xaml` | Force-kills processes (fallback cleanup) | YES — list all app processes to kill |
| `TakeScreenshot.xaml` | Captures screenshot on error | RARELY |

---

## 2. State Machine Architecture

### States (4)

```
┌──────────┐     Success      ┌─────────────────────┐
│          │ ──────────────── │                     │
│   INIT   │                  │  GET TRANSACTION    │
│          │ ←─── System ──── │       DATA          │
└──────────┘   Exception      └─────────────────────┘
     │                              │          │
     │ System Exception             │          │ No Data
     │ (max retries)                │          │
     ▼                              ▼          ▼
┌──────────┐                  ┌──────────────────────┐
│   END    │ ←─────────────── │                      │
│ PROCESS  │   No More Data   │  PROCESS TRANSACTION │
│ (Final)  │                  │                      │
└──────────┘ ←─── System ──── └──────────────────────┘
              Exception             │         ▲
              (max consecutive)     │         │
                                    └─────────┘
                                   Success / Business
                                   Exception → next item
```

### Transitions (7)

| # | From | To | Condition |
|---|------|----|-----------|
| 1 | Init | Get Transaction Data | Initialization successful |
| 2 | Init | End Process | System exception during init (max retries exceeded) |
| 3 | Get Transaction Data | Process Transaction | Transaction item retrieved |
| 4 | Get Transaction Data | End Process | No more items (TransactionItem is Nothing) |
| 5 | Process Transaction | Get Transaction Data | Transaction succeeded (get next item) |
| 6 | Process Transaction | Init | System exception → reinitialize apps, retry |
| 7 | Process Transaction | End Process | Max consecutive system exceptions reached |

---

## 3. Config.xlsx — Configuration File

### Three Sheets

#### Settings Sheet
| Name | Value | Description |
|------|-------|-------------|
| `logF_BusinessProcessName` | "MyProcess" | Process name for logging |
| `MaxRetryNumber` | 3 | Max retries per transaction on System Exception |
| `MaxConsecutiveSystemExceptions` | 3 | Max consecutive system exceptions before abort |
| `TransactionNumber` | 1 | Starting transaction number (for non-queue sources) |
| `OrchestratorQueueName` | "MyQueue" | Orchestrator queue name (queue-based processing) |
| `OrchestratorQueueFolder` | "" | Orchestrator folder for queue |
| Custom settings | | Add your own rows: URLs, file paths, thresholds |

#### Constants Sheet
| Name | Value | Description |
|------|-------|-------------|
| Values that never change | | Timeouts, static URLs, format strings |

#### Assets Sheet
| Name | Value | Description |
|------|-------|-------------|
| Asset names from Orchestrator | | Values fetched via Get Asset at runtime |
| Credential asset names | | Fetched via Get Credential |

### How Config Is Loaded
1. `InitAllSettings.xaml` reads all three sheets
2. Settings and Constants stored directly in `in_Config` dictionary
3. Assets sheet values fetched from Orchestrator via Get Asset
4. Entire config accessible throughout workflow as `in_Config("KeyName")`

---

## 4. Exception Handling — The Core Principle

### Two Exception Types

| | Business Rule Exception | System Exception |
|---|------------------------|------------------|
| **Class** | `UiPath.Core.BusinessRuleException` | `System.Exception` (any other) |
| **Cause** | Invalid data, business rule violation, missing input | App crash, timeout, element not found, network error |
| **Retry?** | **NO** — data problem won't fix itself | **YES** — transient issue may resolve |
| **Action** | Skip transaction, mark as Business Exception | Retry transaction, reinitialize apps |
| **Queue Status** | Failed (reason: business rule message) | Retry (up to MaxRetryNumber) |
| **Example** | "Invoice amount is negative", "Missing customer ID" | "Selector not found", "Application not responding" |

### How to Throw Business Exceptions in Process.xaml
```vb
' In your Process.xaml, throw when business data is invalid:
Throw New BusinessRuleException("Invoice amount cannot be negative")
```

### Exception Flow

**Business Exception in Process.xaml:**
1. Caught by SetTransactionStatus
2. Transaction marked as **Failed** with business reason
3. No retry — moves to Get Transaction Data for next item
4. `ConsecutiveSystemExceptions` counter **reset to 0**

**System Exception in Process.xaml:**
1. Caught by SetTransactionStatus
2. `RetryNumber` incremented
3. If `RetryNumber < MaxRetryNumber`: transition to **Init** (reinitialize apps, retry same item)
4. If `RetryNumber >= MaxRetryNumber`: transaction marked as **Failed**, move to next item
5. `ConsecutiveSystemExceptions` incremented
6. If `ConsecutiveSystemExceptions >= MaxConsecutiveSystemExceptions`: transition to **End Process** (abort)

**System Exception in Init:**
1. `ConsecutiveSystemExceptions` incremented
2. If limit reached: transition to **End Process**
3. Otherwise: retry Init

---

## 5. MaxRetryNumber vs MaxConsecutiveSystemExceptions

This is the **most confusing aspect** of REFramework. Here's the definitive explanation:

### MaxRetryNumber (per transaction)
- **Controls**: How many times a SINGLE transaction is retried after System Exceptions
- **Scope**: Resets for each new transaction
- **Default**: 3
- **Behavior**: After 3 system exceptions on the same transaction, it's marked Failed and the next transaction is fetched
- **Works with Orchestrator**: Queue items have their own retry count — REFramework MaxRetryNumber is IN ADDITION to queue retry settings

### MaxConsecutiveSystemExceptions (across transactions)
- **Controls**: How many System Exceptions in a ROW (across ALL transactions) before the robot stops entirely
- **Scope**: Global counter, reset to 0 on any successful transaction or business exception
- **Default**: 3
- **Behavior**: If 3 different transactions all fail with system exceptions consecutively (no successes in between), robot assumes environment is broken and goes to End Process
- **Purpose**: Safety net — if the app is down, don't keep retrying forever

### Example Scenario
```
Transaction 1: System Exception → Retry 1 (ConsecutiveSystemExceptions = 1)
Transaction 1: System Exception → Retry 2 (ConsecutiveSystemExceptions = 2)
Transaction 1: System Exception → Retry 3 → FAILED (MaxRetryNumber reached)
Transaction 2: System Exception → Retry 1 (ConsecutiveSystemExceptions = 3) → END PROCESS
                                              (MaxConsecutiveSystemExceptions reached!)
```

```
Transaction 1: System Exception → Retry 1 (ConsecutiveSystemExceptions = 1)
Transaction 1: SUCCESS → (ConsecutiveSystemExceptions = 0, reset!)
Transaction 2: System Exception → Retry 1 (ConsecutiveSystemExceptions = 1)
Transaction 2: System Exception → Retry 2 (ConsecutiveSystemExceptions = 2)
Transaction 2: SUCCESS → (ConsecutiveSystemExceptions = 0, reset!)
  ← Robot continues processing normally
```

---

## 6. Processing Lifecycle (Step by Step)

### 1. INIT State
```
1. InitAllSettings.xaml
   ├── Read Config.xlsx → in_Config dictionary
   ├── Read Settings sheet (key-value pairs)
   ├── Read Constants sheet (key-value pairs)
   └── Read Assets sheet → Get Asset from Orchestrator for each row

2. KillAllProcesses.xaml
   └── Force-kill any lingering app processes (clean slate)

3. InitAllApplications.xaml
   ├── GetAppCredentials.xaml → Get credentials from Orchestrator/CredentialManager
   └── Open and authenticate all required applications

4. On Success → Transition to "Get Transaction Data"
5. On System Exception → Increment ConsecutiveSystemExceptions
   ├── If under limit → Retry Init
   └── If limit reached → Transition to "End Process"
```

### 2. GET TRANSACTION DATA State
```
1. Check ShouldStop signal from Orchestrator
   ├── If ShouldStop = True → Set TransactionItem = Nothing → End Process
   └── If ShouldStop = False → Continue

2. Try GetTransactionData.xaml
   ├── Queue mode: Get Transaction Item from Orchestrator queue
   │   └── Returns QueueItem or Nothing
   ├── DataTable mode: Get row at TransactionNumber index
   │   └── Returns DataRow or Nothing
   └── Other: Custom data source

3. Catch Exception → Log Fatal, Set TransactionItem = Nothing → End Process

4. If TransactionItem is Nothing → Transition to "End Process" (no more data)
5. If TransactionItem has value → Transition to "Process Transaction"
```

> **Current template detail**: Get Transaction Data state first calls `ShouldStop` activity to check if Orchestrator requested a graceful stop. This allows the robot to finish cleanly between transactions instead of being force-killed.

### 3. PROCESS TRANSACTION State
```
1. Process.xaml (YOUR code)
   └── Process the current TransactionItem

2. SetTransactionStatus.xaml
   ├── On Success:
   │   ├── Set Transaction Status = Successful
   │   ├── Reset RetryNumber = 0
   │   ├── Reset ConsecutiveSystemExceptions = 0
   │   └── Transition to "Get Transaction Data" (next item)
   │
   ├── On BusinessRuleException:
   │   ├── Set Transaction Status = Failed (business reason)
   │   ├── Reset ConsecutiveSystemExceptions = 0  ← important!
   │   ├── DO NOT retry
   │   └── Transition to "Get Transaction Data" (next item)
   │
   └── On System Exception:
       ├── Take Screenshot → Exceptions_Screenshots/
       ├── Increment RetryNumber
       ├── Increment ConsecutiveSystemExceptions
       ├── If RetryNumber < MaxRetryNumber:
       │   └── Transition to "Init" (reinitialize, retry same item)
       ├── If RetryNumber >= MaxRetryNumber:
       │   ├── Set Transaction Status = Failed
       │   └── Transition to "Get Transaction Data" (next item)
       └── If ConsecutiveSystemExceptions >= Max:
           └── Transition to "End Process" (abort)
```

### 4. END PROCESS State (Final)
```
1. CloseAllApplications.xaml
   └── Gracefully close all applications

2. Workflow ends
```

---

## 7. Key Variables in Main.xaml

### Main.xaml Arguments (new in current template)
| Argument | Direction | Type | Purpose |
|----------|-----------|------|---------|
| `in_OrchestratorQueueName` | In | String | Allows queue name to be passed as argument (overrides Config) |
| `in_OrchestratorQueueFolder` | In | String | Allows queue folder to be passed as argument (overrides Config) |

### State Machine Variables
| Variable | Type | Purpose |
|----------|------|---------|
| `Config` | Dictionary\<String, Object\> | All configuration from Config.xlsx |
| `TransactionItem` | QueueItem | Current transaction being processed |
| `TransactionNumber` | Int32 | Current transaction index |
| `RetryNumber` | Int32 | Current retry count for this transaction |
| `ConsecutiveSystemExceptions` | Int32 | Consecutive system exception counter |
| `dt_TransactionData` | DataTable | Transaction data source (non-queue mode) |
| `SystemException` | Exception | Last caught system exception |
| `BusinessException` | BusinessRuleException | Last caught business exception |
| `TransactionField1` | String | Optional transaction info for logging |
| `TransactionField2` | String | Optional transaction info for logging |
| `TransactionID` | String | Unique transaction identifier for logging |

### GetTransactionData.xaml Arguments
| Argument | Direction | Type | Purpose |
|----------|-----------|------|---------|
| `in_TransactionNumber` | In | Int32 | Sequential counter of transactions |
| `in_Config` | In | Dictionary\<String, Object\> | Config dictionary |
| `out_TransactionItem` | Out | QueueItem | Transaction item to process |
| `out_TransactionField1` | Out | String | Optional transaction info |
| `out_TransactionField2` | Out | String | Optional transaction info |
| `out_TransactionID` | Out | String | Unique transaction ID for logging |
| `io_dt_TransactionData` | InOut | DataTable | DataTable source for non-queue mode |

### SetTransactionStatus.xaml Arguments
| Argument | Direction | Type | Purpose |
|----------|-----------|------|---------|
| `in_BusinessException` | In | BusinessRuleException | Business exception (Nothing if success/system error) |
| `in_SystemException` | In | Exception | System exception (Nothing if success/business error) |
| `in_TransactionItem` | In | QueueItem | Current transaction item |
| `in_TransactionField1` | In | String | Additional transaction info |
| `in_TransactionField2` | In | String | Additional transaction info |
| `in_TransactionID` | In | String | Transaction ID for logging |
| `in_Config` | In | Dictionary\<String, Object\> | Config dictionary |
| `io_RetryNumber` | InOut | Int32 | Retry counter |
| `io_TransactionNumber` | InOut | Int32 | Transaction counter |
| `io_ConsecutiveSystemExceptions` | InOut | Int32 | Consecutive system exception counter |

### RetryCurrentTransaction.xaml Arguments (NEW in current template)
| Argument | Direction | Type | Purpose |
|----------|-----------|------|---------|
| `in_Config` | In | Dictionary\<String, Object\> | Config dictionary |
| `io_RetryNumber` | InOut | Int32 | Retry counter |
| `io_TransactionNumber` | InOut | Int32 | Transaction counter |
| `in_SystemException` | In | Exception | The system exception that occurred |
| `in_QueueRetry` | In | Boolean | Whether retry is managed by Orchestrator queue |

---

## 8. Queue-Based vs Non-Queue Processing

### Queue-Based (Default/Recommended)
- `GetTransactionData.xaml` calls `Get Transaction Item` from Orchestrator
- `SetTransactionStatus.xaml` calls `Set Transaction Status`
- Orchestrator manages: retry count, defer dates, deadlines, progress
- Supports Dispatcher/Performer pattern

### Non-Queue (DataTable/File/Custom)
- `GetTransactionData.xaml` reads from DataTable, file, database, etc.
- `TransactionNumber` tracks current position (incremented manually)
- No Orchestrator queue integration
- Must implement your own retry tracking
- `SetTransactionStatus.xaml` may write to Excel, database, or log

### Non-Queue Mode: Tabular Data (Detailed)

When processing data from Excel/CSV/DataTable without Orchestrator queues, modify the REFramework as follows:

**Config.xlsx Modifications:**

| Setting | Value | Action |
|---|---|---|
| `OrchestratorQueueName` | (empty or remove) | Not used in tabular mode |
| `DataSourcePath` | Path to Excel/CSV file | **Add this row** — or use an Orchestrator Text asset |
| `DataSourceSheet` | Sheet name (Excel only) | **Add this row** — e.g., `"Sheet1"` |

**GetTransactionData.xaml Modifications:**

1. In the **Init** state, load the data source ONCE into `io_dt_TransactionData`:
   ```vb
   ' Read Excel in InitAllSettings or a custom Init step:
   ' Read Range: in_Config("DataSourcePath"), Sheet: in_Config("DataSourceSheet") → io_dt_TransactionData
   ```

2. In `GetTransactionData.xaml`, use `in_TransactionNumber` as a row counter:
   ```vb
   ' Check if more rows exist:
   If in_TransactionNumber >= io_dt_TransactionData.Rows.Count Then
       out_TransactionItem = Nothing   ' Signals "no more data" → End Process
   Else
       ' Return current row as the transaction item:
       out_TransactionItem = io_dt_TransactionData.Rows(in_TransactionNumber)
   End If
   ```

   > **Note:** `out_TransactionItem` type changes from `QueueItem` to `DataRow`. Update the variable type in Main.xaml accordingly, or use a separate `out_TransactionRow` argument.

3. **Access data in Process.xaml** — use DataRow syntax instead of QueueItem:
   ```vb
   ' Queue mode:    transactionItem.SpecificContent("FieldName").ToString()
   ' Tabular mode:  in_TransactionItem("ColumnName").ToString()
   ```

**SetTransactionStatus.xaml Modifications:**

Without Orchestrator queues, status tracking is manual:

| Approach | Implementation |
|---|---|
| **Status column in source DataTable** | Add "Status" column, set to "Success"/"Failed"/"Business Exception" per row |
| **Output file** | Write processed rows + status to a separate output Excel/CSV |
| **Log only** | Log Message with transaction ID and result (simplest) |

**Load Data Once Principle:**
- Read the Excel/CSV file **once** during Init, store in `io_dt_TransactionData`
- Do NOT re-read the file for each transaction — this is wasteful and can cause file lock issues
- The `io_` prefix on `dt_TransactionData` means it is InOut — loaded in Init, read in GetTransactionData

**When to Use Tabular vs Queue Mode:**

| Factor | Tabular Data | Orchestrator Queue |
|---|---|---|
| Robot count | Single robot | Multiple robots in parallel |
| Orchestrator available | Not required | Required |
| Auto-retry | Manual (REFramework handles via RetryNumber) | Built-in (Orchestrator + REFramework) |
| Progress monitoring | Manual (log/file-based) | Dashboard, SLA tracking |
| Data volume | Small to medium (fits in memory) | Any size (streamed one at a time) |
| Best for | Offline processing, standalone robots, small datasets | Production enterprise processing |

---

## 9. Dispatcher/Performer Pattern

### Dispatcher (separate workflow)
1. Read input data (Excel, email, database, API)
2. For each item: `Add Queue Item` to Orchestrator queue
3. Done — dispatcher is typically simple and linear (no REFramework needed)

### Performer (REFramework)
1. `GetTransactionData` → `Get Transaction Item` from queue
2. `Process.xaml` → Process the item using `TransactionItem.SpecificContent("FieldName")`
3. `SetTransactionStatus` → Mark Success/Failed
4. Repeat until queue empty

### Benefits
- Multiple robots can process the same queue in parallel
- Failed items automatically retried by Orchestrator
- Progress visible in Orchestrator dashboard
- Audit trail for every item

---

## 10. Common Gotchas & Mistakes

### Configuration
1. **Config.xlsx must be closed** before running — Excel file lock causes "file in use" error
2. **Asset names in Assets sheet must match Orchestrator exactly** (case-sensitive)
3. **Config values are all Strings** in the dictionary — must convert: `CInt(in_Config("MaxRetryNumber"))`
4. **Missing config keys** throw KeyNotFoundException — always check `in_Config.ContainsKey()` or add defaults

### Exception Handling
5. **Business exceptions should NOT be caught in Process.xaml** — let them propagate to SetTransactionStatus
6. **System exceptions in Process.xaml should NOT be caught** either — the framework handles them
7. **Wrapping everything in Try-Catch in Process.xaml defeats the purpose** — only catch exceptions you explicitly want to handle differently
8. **MaxRetryNumber in Config.xlsx is SEPARATE from Orchestrator queue retry** — both apply; total retries = REF retries × queue retries
9. **ConsecutiveSystemExceptions counter reset on BusinessRuleException** — a business exception proves the environment works, just the data was bad

### State Machine
10. **Init runs KillAllProcesses then InitAllApplications** — your apps WILL be killed and reopened on every system exception retry
11. **Init is NOT just for first run** — it's called again on every system exception to reinitialize apps
12. **End Process always runs** — even on successful completion (it closes apps)
13. **Don't add activities directly to Main.xaml** — put business logic in Process.xaml and sub-workflows

### Queue Processing
14. **Get Transaction Item returns Nothing when queue empty** — this is the normal exit signal, not an error
15. **QueueItem.SpecificContent returns Object** — always .ToString() or convert explicitly
16. **Queue item retry count in Orchestrator is independent** — an item failing in REF gets requeued by Orchestrator with its own retry logic

### Common Mistakes
17. **Not throwing BusinessRuleException for data issues** — using generic Exception causes unnecessary retries
18. **Leaving Process.xaml empty** — it must contain your actual automation logic
19. **Not implementing CloseAllApplications** — apps remain open between runs, causing resource leaks
20. **Not implementing KillAllProcesses** — stale app instances interfere with reinitializationF
21. **Using REFramework for simple linear processes** — overkill for non-transactional workflows; use a simple Sequence instead

### Debugging
22. **Hard to debug in Studio** — state machine jumps are confusing; use Log Message extensively
23. **Set MaxRetryNumber to 0 during development** — prevents infinite retry loops while testing
24. **Screenshots land in Exceptions_Screenshots/ folder** — check there for error context
25. **Orchestrator logs show state transitions** — filter by Log Level to trace framework behavior

---

## 11. When to Use REFramework

### Use REFramework When:
- Processing multiple similar items (transactions)
- Items are independent (failure of one doesn't affect others)
- Need retry logic for transient errors
- Running unattended on Orchestrator
- Need audit trail and error reporting
- Multiple robots should process same workload

### DON'T Use REFramework When:
- Simple linear process (read file → do one thing → done)
- Attended automation (user interaction throughout)
- No transaction concept (single operation, not batch)
- Quick proof-of-concept or prototype
- Process takes <30 seconds total

---

## 12. Current Template Dependencies (Studio 25.10)

```json
{
  "UiPath.Excel.Activities": "[2.24.4]",
  "UiPath.System.Activities": "[24.10.8]",
  "UiPath.Testing.Activities": "[25.10.1]",
  "UiPath.UIAutomation.Activities": "[25.10.26]"
}
```

- **targetFramework**: `"Legacy"` (.NET Framework 4.6.1)
- **expressionLanguage**: `"VisualBasic"` (VB template) or `"CSharp"` (C# template)
- **studioVersion**: `"25.10.7.0"`
- Both VB and C# templates have identical structure and logic

---

## 13. Built-In Test Cases (NEW in current template)

The template includes pre-built test case workflows:

| Test Case | Purpose |
|-----------|---------|
| `GeneralTestCase.xaml` | General test template |
| `InitAllSettingsTestCase.xaml` | Tests Config.xlsx loading |
| `InitAllApplicationsTestCase.xaml` | Tests app initialization |
| `GetTransactionDataTestCase.xaml` | Tests transaction data retrieval |
| `ProcessTestCase.xaml` | Tests Process.xaml business logic |
| `MainTestCase.xaml` | End-to-end test of Main workflow |
| `WorkflowTestCaseTemplate.xaml` | Template for creating new tests |
| `Tests.xlsx` | Test data file |

---

## 14. Customization Checklist

When starting a new REFramework project:

- [ ] **Config.xlsx**: Add your settings (URLs, paths, thresholds, queue name)
- [ ] **Config.xlsx Assets**: Add Orchestrator asset names for credentials
- [ ] **InitAllApplications.xaml**: Add logic to open/login to your apps
- [ ] **CloseAllApplications.xaml**: Add logic to logout/close your apps
- [ ] **KillAllProcesses.xaml**: List all app process names to force-kill
- [ ] **GetTransactionData.xaml**: Configure your data source (queue, DataTable, etc.)
- [ ] **Framework/Process.xaml**: Implement your business logic
- [ ] **SetTransactionStatus.xaml**: Configure status reporting (if not using queues)
- [ ] Test with MaxRetryNumber=0 first, then increase
- [ ] Test Business Exception path (throw BusinessRuleException)
- [ ] Test System Exception path (simulate app crash)
- [ ] Test empty queue/data path (verify clean exit)
- [ ] Run built-in test cases (Tests/ folder) to verify framework integrity

---

## Sources
- [UiPath REFramework GitHub Repository](https://github.com/UiPath/ReFrameWork)
- [UiPath Studio Documentation - Robotic Enterprise Framework](https://docs.uipath.com/studio/standalone/2024.10/user-guide/robotic-enterprise-framework)
- [UiPath Forum - MaxRetryNumber vs MaxConsecutiveSystemExceptions](https://forum.uipath.com/t/re-framwork-maxretrynumber-vs-maxconsecutivesystemexceptions/453279)
- [UiPath Forum - How would you improve ReFramework?](https://forum.uipath.com/t/how-would-you-improve-reframework/770451)
- [UiPath Forum - REFramework Best Practices](https://forum.uipath.com/t/reframework-best-practices/182867)
- [UiPath Forum - REFramework in 2026: Still Best Practice?](https://forum.uipath.com/t/reframework-in-2026-still-best-practice-or-due-for-modernization/5730782)
- [UiPath Academy - Introduction to REFramework](https://academy.uipath.com/courses/introduction-to-robotic-enterprise-framework)
