# Orchestrator Integration Guide

Orchestrator concepts and integration patterns for legacy UiPath workflows: queues, assets, logging, triggers, and environment management.

For Dispatcher/Performer REFramework pattern, see [activity-docs/_REFRAMEWORK.md](./activity-docs/_REFRAMEWORK.md) section 9.
For Asset access VB.NET code, see [activity-docs/_PATTERNS.md](./activity-docs/_PATTERNS.md) Orchestrator Integration Patterns.

---

## 1. Queue Item Lifecycle

Queue items progress through defined states. Understanding the lifecycle is critical for designing robust dispatcher/performer workflows.

```
                    ┌─────────────┐
                    │    NEW       │  ← Add Queue Item creates this
                    └──────┬──────┘
                           │ Get Transaction Item
                           ▼
                    ┌─────────────┐
         ┌────────│ IN PROGRESS  │────────┐
         │         └─────────────┘         │
         │                                 │
         ▼                                 ▼
┌─────────────┐                   ┌─────────────┐
│ SUCCESSFUL  │                   │   FAILED    │
└─────────────┘                   └──────┬──────┘
                                         │ Auto-retry enabled?
                                         ▼
                                  ┌─────────────┐
                                  │   RETRIED   │──→ Back to NEW
                                  └─────────────┘
                                         │ Max retries exceeded
                                         ▼
                                  ┌─────────────┐
                                  │   FAILED    │ (final)
                                  └─────────────┘

Other states:
  ABANDONED — item was In Progress but robot disconnected (timeout)
  DELETED   — manually removed from queue
```

### State Transitions

| From | To | Triggered By |
|---|---|---|
| (none) | New | `Add Queue Item` activity |
| New | In Progress | `Get Transaction Item` activity |
| In Progress | Successful | `Set Transaction Status` → Success |
| In Progress | Failed | `Set Transaction Status` → Failed |
| In Progress | Abandoned | Robot disconnected/crashed while processing |
| Failed | New (Retried) | Auto-retry enabled, retry count < max |
| New | Deleted | Manual deletion from Orchestrator UI |

---

## 2. Queue Item Properties

### Add Queue Item — Configuration

| Property | Type | Purpose | Required |
|---|---|---|---|
| **QueueName** | String | Target queue name | YES |
| **Reference** | String | Unique business key for idempotency | Recommended |
| **Priority** | Enum | High, Normal (default), Low | No |
| **DeferDate** | DateTime | Earliest processing time (item is invisible until then) | No |
| **Deadline** | DateTime | Must be processed by this time (SLA tracking) | No |
| **SpecificContent** | Dictionary(Of String, Object) | Business data payload (key-value pairs) | YES (carries the data) |

### Rules for Queue Item Creation (Dispatcher)

1. **ALWAYS set a unique Reference** — enables deduplication and item lookup. Use a business key: invoice number, order ID, customer + date combination.
2. **Set Priority based on business rules** — High for urgent items (approaching deadline), Normal for standard processing, Low for batch/background.
3. **Set Deadline for SLA-tracked items** — Orchestrator reports overdue items in dashboards.
4. **Use DeferDate for scheduled processing** — items with future DeferDate are invisible to performers until the date arrives.
5. **Keep SpecificContent values as strings** — convert numbers and dates to strings in the dispatcher. Parse them in the performer. This avoids serialization issues.

### Accessing Queue Item Data (Performer)

```vb
' Get Transaction Item returns a QueueItem object
' Access SpecificContent fields:
transactionItem.SpecificContent("InvoiceNumber").ToString()
transactionItem.SpecificContent("Amount").ToString()
transactionItem.SpecificContent("CustomerName").ToString()

' Safe access with null check (for optional fields):
If transactionItem.SpecificContent.ContainsKey("Notes") Then
    Dim notes = transactionItem.SpecificContent("Notes").ToString()
End If

' Access queue item metadata:
transactionItem.Reference            ' Unique reference string
transactionItem.Priority             ' High, Normal, Low
transactionItem.DeferDate            ' Nullable DateTime
transactionItem.Deadline             ' Nullable DateTime
transactionItem.RetryNo              ' Current retry count
```

### Setting Transaction Status (Performer)

```vb
' On success — pass output data for reporting:
Set Transaction Status: Success
  Output: New Dictionary(Of String, Object) From {
    {"ProcessedAmount", totalAmount.ToString()},
    {"ConfirmationNumber", confirmNo}
  }

' On business failure:
Set Transaction Status: Failed
  Reason: businessException.Message
  ErrorType: Business

' On system failure (REFramework handles this automatically):
Set Transaction Status: Failed
  Reason: systemException.Message
  ErrorType: Application
```

---

## 3. Asset Types

Assets store configuration values in Orchestrator. Use assets for values that differ between environments or contain secrets.

| Type | Value | Use Case | Access Pattern |
|---|---|---|---|
| **Text** | String | URLs, file paths, email addresses | `Get Asset "AssetName"` → String |
| **Bool** | True/False | Feature flags, toggles | `Get Asset "AssetName"` → cast to Boolean |
| **Integer** | Whole number | Thresholds, batch sizes, port numbers | `Get Asset "AssetName"` → cast to Int32 |
| **Credential** | Username + Password | Login credentials, API tokens | `Get Credential "AssetName"` → String + SecureString |

### Per-Robot vs Global Assets

| Type | Behavior | Use When |
|---|---|---|
| **Global** | Same value for all robots | Shared URLs, thresholds, feature flags |
| **Per-Robot** | Different value per robot | Machine-specific paths, per-machine credentials, environment-specific settings |

### Rules

1. **Get Asset returns Object** — ALWAYS cast to the expected type: `CStr(getAssetResult)`, `CInt(getAssetResult)`, `CBool(getAssetResult)`
2. **Get Credential returns two values** — `username` (String) and `password` (SecureString). Use separate output variables.
3. **NEVER log credential values** — not even in Verbose mode
4. **Use Credential assets for ALL secrets** — API keys, tokens, passwords. Never use Text assets for sensitive data.
5. **Name assets consistently** — `ProcessName_SettingName` pattern: `InvoiceBot_PortalURL`, `InvoiceBot_Credentials`

---

## 4. Logging Best Practices

### Log Levels

| Level | When to Use | Examples |
|---|---|---|
| **Verbose** | Detailed diagnostic data (variable values, loop counters) | "Processing row 42 of 100", "Variable X = 'abc'" |
| **Trace** | Step-by-step execution flow | "Entering ProcessInvoice", "Opening browser" |
| **Info** | Key business events and transaction lifecycle | "Transaction started: INV-12345", "Invoice submitted successfully" |
| **Warn** | Recoverable issues that don't stop execution | "Retry 2 of 3 for INV-12345", "Fallback value used for missing field" |
| **Error** | Failures that stop a transaction | "System exception in ProcessInvoice: Selector not found" |
| **Fatal** | Failures that stop the entire process | "Max consecutive exceptions reached — aborting", "Init failed — cannot continue" |

### Rules

1. **Log at transaction boundaries** — Info level at transaction start and end, include transaction identifier
2. **Include identifiers in log messages** — "Processing INV-12345" not "Processing invoice". This makes Orchestrator log search useful.
3. **Log before and after key actions** — "Submitting invoice INV-12345" then "Invoice INV-12345 submitted, confirmation: CONF-789"
4. **Use Warn for retries** — "Retry 2/3 for INV-12345: selector not found"
5. **Use Error only for actual failures** — not for expected business exceptions
6. **Don't log sensitive data** — no passwords, SSNs, credit card numbers, even at Verbose level
7. **Use Log Fields for structured data** — key-value pairs that appear as structured data in Orchestrator, not just in the message string

---

## 5. Robot Types

| Type | Triggered By | Interaction | Use Cases |
|---|---|---|---|
| **Attended** | User (from Assistant/tray) | CAN interact with user's desktop | User-triggered tasks, human-in-the-loop, data entry assistance |
| **Unattended** | Orchestrator (triggers/schedules) | CANNOT interact with user desktop | Batch processing, scheduled tasks, queue processing |

### Execution Modes

| Mode | Behavior | Use When |
|---|---|---|
| **Foreground** | Takes control of the screen, interacts with UI | UI automation (Click, TypeInto, selectors) |
| **Background** | Runs without UI interaction | API calls, data processing, file operations only |

### Rules

1. **Attended robots should NOT use long-running loops** — they block the user's desktop
2. **Unattended robots MUST NOT show dialog boxes** — no one is watching to click OK. Use `InputDialog` only in attended mode.
3. **Background processes CANNOT use UI activities** — no Click, TypeInto, or selector-based activities
4. **Design workflows to work as both when possible** — use config flags to switch between interactive (InputDialog) and headless (Orchestrator asset) modes

---

## 6. Trigger Types

Triggers start processes automatically in Orchestrator.

| Trigger | Fires When | Best For |
|---|---|---|
| **Time Trigger** | Cron schedule (e.g., "0 8 * * MON-FRI" = 8 AM weekdays) | Daily/weekly batch processing, report generation |
| **Queue Trigger** | New items appear in a queue | Dispatcher/Performer pattern, event-driven processing |
| **Event Trigger** | External event (webhook, API call) | Integration-triggered automation |

### Queue Trigger Configuration

| Setting | Description |
|---|---|
| **Minimum items to trigger** | Don't start unless N+ items are waiting |
| **Maximum jobs allowed** | Cap concurrent performers (prevents resource exhaustion) |
| **Job priority** | Priority of the triggered job |

### Rules

1. **Use Queue Triggers for performer processes** — not Time Triggers. Queue Triggers scale with demand.
2. **Use Time Triggers for dispatchers** — run the dispatcher on schedule to load items into the queue.
3. **Set max concurrent jobs** based on infrastructure capacity — too many parallel robots can overwhelm target applications.

---

## 7. Environment Separation

### Folder Strategy

| Environment | Folder | Purpose |
|---|---|---|
| **Dev** | `/Development` | Active development, frequent deployments |
| **Test/UAT** | `/Testing` | User acceptance testing, stable versions |
| **Prod** | `/Production` | Live execution, change-controlled |

### Per-Environment Configuration

| Configuration Item | How to Separate |
|---|---|
| URLs (portal, API) | Per-environment Text assets: `InvoiceBot_PortalURL` with different values per folder |
| Credentials | Per-environment Credential assets: `InvoiceBot_Credentials` |
| File paths | Per-environment Text assets or per-robot assets |
| Queue names | Same name in each folder (Orchestrator scopes queues to folders) |
| Thresholds/batch sizes | Per-environment Text or Integer assets |

### Rules

1. **Same queue name across environments** — Orchestrator scopes queues to their folder automatically
2. **Different asset values per environment** — same asset name, different value in each folder
3. **Package versioning across environments** — deploy specific version to Test, promote exact same version to Prod after approval
4. **Never deploy directly to Prod** — always go through Dev → Test → Prod pipeline
5. **Use per-robot assets for machine-specific paths** — different robots may have different local folder structures
