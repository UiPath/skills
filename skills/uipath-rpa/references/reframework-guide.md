# REFramework Guide

Patterns for building and customizing Robotic Enterprise Framework projects on Windows, Portable, or Legacy targets. State-machine internals are in [legacy/activity-docs/_REFRAMEWORK.md](legacy/activity-docs/_REFRAMEWORK.md) — that guide's architecture sections are mode-agnostic.

## When to Use REFramework

Use:
- Multi-item transactional processing (invoices, queue items, data rows).
- Production-grade retry, logging, and exception handling.
- Multi-robot horizontal scaling on a shared Orchestrator queue.

Don't use:
- Simple linear processes (read → do one thing → exit). Plain `Sequence` is enough.
- Attended automations with continuous user interaction.
- Single-call jobs under ~30 seconds total. The four-state ceremony costs more than it saves.

## The Four States

| State | Role |
|-------|------|
| `Init` | `InitAllSettings.xaml` reads `Config.xlsx` → `Config` dictionary; `KillAllProcesses.xaml`; `InitAllApplications.xaml` opens/authenticates apps. |
| `Get Transaction Data` | `GetTransactionData.xaml` returns the next item or `Nothing`. `Nothing` → End Process. |
| `Process Transaction` | `Process.xaml` (your business logic) → `SetTransactionStatus.xaml` (Success / BusinessRuleException / System Exception). |
| `End Process` | `CloseAllApplications.xaml` runs on every exit (success or abort). |

Full state machine, transitions, and per-state counter semantics: [legacy/activity-docs/_REFRAMEWORK.md § State Machine Architecture](legacy/activity-docs/_REFRAMEWORK.md).

## Execution Mode: Queue-Driven (Canonical)

The default and most common mode. Dispatcher project populates an Orchestrator queue; this Performer project consumes one item per transaction. Multi-robot parallelism comes for free via queue locking.

**Wiring — keep the template as-is.** The shipped REFramework is built for this mode end-to-end.

1. `Config.xlsx` Settings sheet: set `OrchestratorQueueName` (case-sensitive, must match the queue in Orchestrator) and optionally `OrchestratorQueueFolder`.
2. `Framework\GetTransactionData.xaml`: uses the `Get Transaction Item` activity. Returns a `QueueItem` or `Nothing` (queue empty → End Process).
3. `Framework\Process.xaml`: implement business logic. Access fields via:
   ```vb
   in_TransactionItem.SpecificContent("FieldName").ToString()
   in_TransactionItem.Reference
   in_TransactionItem.Priority
   in_TransactionItem.DueDate
   ```
4. `Framework\SetTransactionStatus.xaml`: keep the three Set Transaction Status calls — they update item status in Orchestrator.

**Dispatcher pattern (separate project).** Read input data, then for each row emit `Add Queue Item` with a unique `Reference`, optional `Priority` / `DueDate`, and the fields as `SpecificContent`. Dispatcher does not need REFramework — a simple `Sequence` is sufficient.

**Concurrency.** Orchestrator locks each item to one robot for the duration of processing. Design `Process.xaml` **stateless** so any robot can pick up any item. To scale throughput, add robots — do not add intra-robot parallelism.

## Execution Mode: Tabular Data

Single robot, no Orchestrator queue. Source data is an Excel/CSV/DataTable. The Academy course "REFramework with Tabular Data" (v2024.10) is the reference pattern.

**Wiring — customize these surfaces.**

1. `Config.xlsx` Settings sheet: blank or remove `OrchestratorQueueName`; add `DataSourcePath` and `DataSourceSheet`.
2. `Framework\InitAllSettings.xaml` (or a custom init step): Read Range → `io_dt_TransactionData`. **Read the source once**, not per transaction — repeated reads cause file locks and waste cycles.
3. `Framework\GetTransactionData.xaml`:
   ```vb
   If in_TransactionNumber > io_dt_TransactionData.Rows.Count Then
     out_TransactionItem = Nothing                  ' signals "no more data"
   Else
     out_TransactionItem = io_dt_TransactionData.Rows(in_TransactionNumber - 1)
   End If
   ```
   Assumes `TransactionNumber` is 1-indexed (Config.xlsx default `TransactionNumber = 1`, incremented by `SetTransactionStatus.xaml`). If your template starts at 0, use `>=` and drop the `- 1`.
4. `Framework\Process.xaml`: access fields via `in_TransactionItem("ColumnName").ToString()`.
5. `Framework\SetTransactionStatus.xaml`: **delete the three Set Transaction Status activities.** They target Orchestrator queues and have no purpose here. Replace with a status-column write-back to the source DataTable, an output Excel/CSV, or `Log Message` calls keyed by row index.

**Type migration.** Changing `TransactionItem`'s type from `QueueItem` to `DataRow` cascades across every `TransactionItem` argument in the Framework workflows and every matching `InvokeWorkflowFile` binding in `Main.xaml`. Update them together or `InvokeWorkflowFile` reports argument-mismatch errors at design time. See [Gotchas § type migration](#gotchas) for the file/argument list.

## Execution Mode: Single-Shot

One execution, no transaction loop. Useful for scheduled jobs that just need REFramework's init/cleanup discipline (open apps, do one thing, close apps).

**Wiring.**

1. `Config.xlsx`: blank `OrchestratorQueueName`.
2. `Framework\GetTransactionData.xaml`: return a sentinel on call 1, `Nothing` on call 2:
   ```vb
   If in_TransactionNumber = 1 Then
     out_TransactionItem = New Object()             ' placeholder, NOT New QueueItem()
   Else
     out_TransactionItem = Nothing
   End If
   ```
3. `Framework\Process.xaml`: implement the single unit of work. `in_TransactionItem` is a sentinel — ignore it.
4. `Framework\SetTransactionStatus.xaml`: **delete the three Set Transaction Status activities** (same reason as tabular). Log-only is fine.

**Type migration.** Type `TransactionItem` as `System.Object` across every Framework workflow and every `InvokeWorkflowFile` binding. See [Gotchas § type migration](#gotchas).

## Exception Handling Strategy

| Exception | Class | Retry? | Counter behavior |
|-----------|-------|--------|------------------|
| Business Rule Exception | `UiPath.Core.BusinessRuleException` | No — data won't fix itself | `ConsecutiveSystemExceptions` resets to 0 |
| System Exception | `System.Exception` (any other) | Yes — retry per transaction up to `MaxRetryNumber`; re-initialize apps between retries | `ConsecutiveSystemExceptions` increments; hitting `MaxConsecutiveSystemExceptions` aborts to End Process |

Throw business exceptions explicitly in `Process.xaml`:

```vb
Throw New BusinessRuleException("Invoice amount cannot be negative")
```

Do NOT wrap `Process.xaml` in a catch-all `TryCatch` — the framework's outer handler is what classifies and routes the exception. Catch only exceptions you intend to translate to a `BusinessRuleException`.

Counter semantics — `MaxRetryNumber` (per transaction, resets per item) vs `MaxConsecutiveSystemExceptions` (global, resets on any success or BusinessRuleException): see [legacy/activity-docs/_REFRAMEWORK.md § MaxRetryNumber vs MaxConsecutiveSystemExceptions](legacy/activity-docs/_REFRAMEWORK.md).

## Configuration Management

- Store all configurable values in `Config.xlsx` — three sheets: `Settings` (key-value, edited per environment), `Constants` (rarely change), `Assets` (Orchestrator asset names, fetched at runtime).
- Sensitive values (credentials, API keys, tokens) → **Orchestrator Assets**, never `Config.xlsx` cell values (Common Rule 5a). Retrieval forms, `SecureString` handling, log masking: [orchestrator-resources-guide.md](orchestrator-resources-guide.md).
- Asset names on the Assets sheet must match Orchestrator exactly (case-sensitive).
- Config values come back as `String` — convert explicitly: `CInt(in_Config("MaxRetryNumber"))`, `CDate(in_Config("Deadline"))`.
- Guard missing keys: check `in_Config.ContainsKey(<name>)` or set defaults before first read.
- Never hardcode paths, URLs, credentials, or environment-specific settings in workflows. Always indirect through `in_Config(<name>)`.

## Idempotency and Concurrency (Queue-Driven)

Performer workflows must be safe to retry. The framework re-executes `Process.xaml` after a System Exception with the same `TransactionItem`.

- Avoid double-posting (check-then-act, or use idempotency tokens from the source system).
- Avoid relying on in-memory state from a prior transaction — design stateless.
- Orchestrator handles queue-item locking; do not add custom locking logic.
- Multiple robots on the same queue: each locks one item while processing. To scale throughput, add robots — not intra-robot parallelism.
- Validate `SpecificContent` fields at the start of `Process.xaml` — don't trust the Dispatcher.

## Gotchas

### Don't return `New QueueItem()` as a sentinel in non-queue modes

`Framework\SetTransactionStatus.xaml` gates its Orchestrator calls on `in_TransactionItem.GetType is GetType(UiPath.Core.QueueItem)`. `New QueueItem()` satisfies this check — so a synthetic empty `QueueItem` returned from a tabular or single-shot `GetTransactionData.xaml` cascades into 6 retries × 3 branches of `OrchestratorHttpException: 404 (Not Found)`.

**Right fix:** delete the Set Transaction Status activities from `SetTransactionStatus.xaml` for non-queue modes (see the per-mode wiring above) and return `Nothing` / non-`QueueItem` sentinels from `GetTransactionData.xaml`.

### `Config.xlsx OrchestratorQueueName="ProcessABCQueue"` template leftover

The shipped template ships with the sample value `OrchestratorQueueName = "ProcessABCQueue"`. Tabular and single-shot users rarely overwrite it. A Config-string check (e.g., `Not String.IsNullOrEmpty(in_Config("OrchestratorQueueName").ToString())`) is therefore insufficient on its own — the leftover sample value passes. **Blank or remove the row** in non-queue projects.

### Type migration cascade

If you migrate `TransactionItem`'s type away from `QueueItem` (tabular → `DataRow` or `Object`; single-shot → `Object`), update every site, not just `Main.xaml`'s variable:

| File | Argument |
|------|----------|
| `Main.xaml` | `TransactionItem` variable |
| `Framework\GetTransactionData.xaml` | `out_TransactionItem` |
| `Framework\Process.xaml` | `in_TransactionItem` |
| `Framework\SetTransactionStatus.xaml` | `in_TransactionItem` |
| `Framework\RetryCurrentTransaction.xaml` | `in_TransactionItem` (if present) |
| `Main.xaml` `InvokeWorkflowFile` bindings | every `in_/out_/io_TransactionItem` binding |

Updating one file but not the others surfaces as `InvokeWorkflowFile` argument-mismatch errors at design time.

### Advanced: one `SetTransactionStatus.xaml` for all modes

If you want a single `SetTransactionStatus.xaml` that handles all three modes (rare — usually it's cleaner to delete the Orchestrator calls in non-queue modes), type `in_TransactionItem` as `System.Object` and replace the three FlowDecision conditions with a type-safe guard:

```vb
TypeOf in_TransactionItem Is UiPath.Core.QueueItem AndAlso DirectCast(in_TransactionItem, UiPath.Core.QueueItem).QueueDefinitionId > 0
```

`TypeOf ... Is` short-circuits on non-`QueueItem` references; `QueueDefinitionId > 0` filters out empty `New QueueItem()` instances. Requires the full `Object`-typed migration above.

## Customization Checklist

Before first run:

- [ ] **Pick execution mode** — queue-driven / tabular / single-shot.
- [ ] **Set or blank `OrchestratorQueueName`** in `Config.xlsx` per mode. Sample value `ProcessABCQueue` must not survive into non-queue projects.
- [ ] **Configure `GetTransactionData.xaml`** for the chosen mode. Never return `New QueueItem()` as a sentinel in non-queue modes — return `Nothing` (terminating) or a non-`QueueItem` value.
- [ ] **For tabular / single-shot:** delete the three Set Transaction Status activities from `SetTransactionStatus.xaml`. Replace with status-column write-back or log-only.
- [ ] **For tabular / single-shot:** migrate every `TransactionItem` argument type (see [Gotchas § type migration](#type-migration-cascade)).
- [ ] **`InitAllApplications.xaml`** — implement app-open/login for every application the process touches.
- [ ] **`CloseAllApplications.xaml`** + **`KillAllProcesses.xaml`** — graceful close + force-kill fallback for every app process name.
- [ ] **Classify exceptions in `Process.xaml`** — throw `BusinessRuleException` for data issues; let everything else propagate.
- [ ] **Move secrets to Orchestrator Assets** — credentials, API keys, environment-specific URLs.
- [ ] **Set `MaxRetryNumber = 0` during development** to surface failures fast; restore the production value before deployment.
- [ ] **Verify**: run a synthetic transaction through every exit branch (Success, BusinessRuleException, System Exception → retry, System Exception → abort).
