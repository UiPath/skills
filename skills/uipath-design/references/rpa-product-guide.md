# RPA Product Guide

Load this guide when Level 1 of the [Product Selection Guide](product-selection-guide.md) selects **RPA**, or when a Solution composition at Level 1.75 includes one or more RPA projects.

This file is the **canonical home** for RPA-specific levels:

- **Level 1.5** — RPA sub-type selection (Process / Library / Test Automation)
- **Level 2** — Authoring mode (XAML / Coded C# / Hybrid)
- **Level 2.5 Part A** — RPA decomposition signals (Single Project vs Master Project)
- **R-07 naming convention** — `<PROCESS_SHORT_NAME_PASCAL>_<ROLE_SUFFIX>`
- **REFramework guidance** — when to use REFramework vs Sequence

Cross-product levels live in the [Product Selection Guide](product-selection-guide.md):

- Level 1 (primary scope)
- Level 1.75 (Solution composition)
- Level 2.5 Part B (merge into unified project list)
- Level 3 (capability add-ons)

## Signals per RPA sub-type

Each RPA project in the scope is one of three sub-types. Pick the default from signals, then confirm with the user via Level 1.5.

### RPA Library

**Signals the PDD is describing a Library:**
- "Reusable component" for other projects
- "Standard activity" used across multiple processes
- Not a complete end-to-end process
- Public workflows meant to appear as activities in other projects
- Distributed via NuGet

**Required PDD information:**
- Public workflow signatures (inputs, outputs)
- Dependencies
- Intended consumers

### RPA Test Automation

**Signals the PDD is describing Test Automation:**
- Primary goal is validating application behavior
- Test cases with assertions
- Test Manager integration
- Data-driven testing with variations
- Regression test suite

**Required PDD information:**
- Application(s) under test
- Test case list
- Expected outcomes per test

### RPA Process (default)

**Signals:**
- UI-heavy automation (web forms, desktop apps, Excel, email)
- Data processing between applications
- Attended or unattended execution
- Queue-based transactional processing
- Standard end-to-end business process

**This is the default when no other RPA sub-type matches.**

## Level 1.5 — RPA Sub-type Selection

Applies when Level 1 selected **RPA**, or when a Solution composition at Level 1.75 includes one or more RPA projects. Skip entirely for non-RPA primaries that do not include RPA in the composition.

### Recommended default

Pick the default from the sub-type signals above:

| Strongest Signal | Default Sub-type |
|---|---|
| Testing / assertions / Test Manager / regression pack | Test Automation |
| Reusable component / shared workflows / NuGet distribution | Library |
| Anything else | Process |

### User confirmation

Always confirm the sub-type via `AskUserQuestion` with the numbered-choice format, even when only one signal set matches:

> This RPA project looks like a **<DEFAULT_SUBTYPE>**. Which sub-type should I use?
>
> 1. **<DEFAULT_SUBTYPE>** *(recommended)* — <ONE_LINE_REASON_FROM_PDD>
> 2. **<ALT_1>** — <ONE_LINE_DESCRIPTION>
> 3. **<ALT_2>** — <ONE_LINE_DESCRIPTION>

If the user picks a sub-type that disagrees with the signals, accept the choice and note the deviation in the recommendation's "Alternatives considered" block.

### When the Solution includes multiple RPA projects

If the Level 1.75 composition has **two or more RPA projects**, run Level 1.5 **once per project** — do not assume all RPA projects share the same sub-type. The canonical example is *2 Libraries + 1 Test Automation*: three Level 1.5 confirmations, one per project.

## Level 2 — Authoring Mode

Applies to every RPA project in the scope (Process, Library, or Test Automation).

| Process Characteristic | Recommended Mode |
|---|---|
| Primarily UI automation (clicking, typing, reading screens) | **XAML** |
| Simple linear or transactional flow (REFramework) | **XAML** |
| Heavy use of pre-built activity packages (SAP, Salesforce, Excel) | **XAML** |
| Significant data transformation (parsing, regex, hashing, aggregation) | **Coded C#** |
| REST API integrations (HTTP calls, pagination, auth tokens) | **Coded C#** |
| Complex branching logic (5+ decision paths) | **Coded C#** |
| Custom data models needed (typed DTOs, enums) | **Coded C#** |
| UI automation AND complex data logic | **Hybrid** |
| Multiple applications with different interaction patterns | **Hybrid** |

The skill that builds the workflows owns the final, detailed decision — this is a directional recommendation.

### Anti-pattern: picking Coded C# for UI-heavy automation

**Trigger:** the process body is **>70% UI automation** against a browser, desktop app, or SaaS UI, with **minimal HTTP / parsing / DTO / data-shaping work**. The PDD describes "log in, navigate to a list, click each row, read fields, compute a derived value, write it back, close" — i.e. UI driving is the bulk of the work.

**Decision:** **XAML** (or **Hybrid** if a discrete piece of non-trivial data logic exists). Do **NOT** pick Coded C# on a "cleaner control flow" argument.

**Why:**

1. **XAML already has clean control-flow primitives for this shape.** Try/Catch, Retry Scope, If/Else, For Each, Sequence — wrapped around UIA activities (`Use Application/Browser`, `Click`, `Type Into`, `Get Text`) — covers retry, exception handling, looping, and branching with no code. Reaching for Coded C# to get "cleaner control flow" reinvents what XAML already provides.

2. **Studio's UI capture flow is significantly more productive than coded selectors.** The visual Indicate / `uia-configure-target` round-trip produces working selectors with proper attributes, content hashes, and reference IDs — and registers them in the Object Repository for reuse. The coded path requires the same OR registration plus extra ceremony (`uiAutomation.Open` / `Attach`, `Descriptors.<App>.<Screen>.<Element>` references, screen-handle affinity rules) without any productivity gain on the capture side.

3. **The "cleaner control flow" argument is not sufficient on its own.** It is also not what UI-heavy work actually benefits from. UI-heavy work benefits from: visual selectors, fast retake, drag-and-drop activity surface, Object Repository sharing across workflows. None of those favour Coded C#.

4. **Coded C# carries a tax that has to be earned.** Manual entry-point management in `project.json`, no visual surface for non-coded contributors, no Studio designer canvas — these costs are repaid by data transforms / HTTP work / DTOs / custom algorithms. They are **not** repaid by "I want explicit if/else" over UI activities.

**Reserve Coded C# for:**

- Substantial data transformation (JSON deserialization, CSV parsing, LINQ aggregation, regex extraction, hashing pipelines)
- REST API integration (HTTP calls, pagination, retry/backoff on transport, auth-token refresh)
- Custom DTOs / typed records / enums (XAML cannot define types)
- Unit-testable business logic (pure functions exercised by Coded Test Cases)
- Algorithm-heavy logic (sorting, deduplication, fuzzy matching, tree traversal)

**If the process is mostly UI with one non-trivial data step,** use **Hybrid**: XAML for orchestration + UI; one Coded Workflow invoked via `Invoke Workflow File` for the data step.

For the full coded-vs-XAML decision flow, see [coded-vs-xaml-guide.md](../../uipath-rpa/references/coded-vs-xaml-guide.md) in the `uipath-rpa` skill (architectural design only — final per-workflow decisions are made by the build skill).

### Selection checklist before recommending Coded C#

Before §13 Implementation Mode commits to Coded C#, confirm at least **two** of these are true:

- [ ] Process has significant data shaping / parsing / regex / hashing work (more than a single one-liner).
- [ ] Process integrates with HTTP / REST APIs that justify a dedicated client.
- [ ] Process defines typed DTOs / records / enums used across multiple workflows.
- [ ] Process has algorithmically non-trivial logic (LINQ aggregation, sorting, dedup, custom comparison).
- [ ] Process has unit-testable pure functions (exercised by Coded Test Cases on inputs the live system cannot easily reproduce).

If **fewer than two** are true and the body is >70% UI, recommend XAML. The "cleaner control flow" line of reasoning is explicitly insufficient — strike it from the §13 justification.

## Level 2.5 Part A — RPA Decomposition Signals

Apply these signals **to every RPA Process project** in the scope. Skip for RPA Library, RPA Test Automation, and non-RPA products — those are always one project each.

Walk through the signals. **If 2 or more signals match → Master Project.** If 0-1 match → Single Project.

| # | Signal in PDD | What it means |
|---|---|---|
| 1 | Process has distinct stages with different characteristics (e.g., email ingestion vs. data extraction vs. output generation) | Each stage becomes a separate project that can be developed, tested, and scaled independently |
| 2 | Transactional processing where items can fail independently and must be retried per item | Queue-based retry requires Performer projects consuming from Orchestrator queues using REFramework |
| 3 | Document Understanding or AI extraction with human validation (Action Centre) | DU + validation is a distinct processing stage that benefits from its own project and queue |
| 4 | Different processing speeds per stage (e.g., fast email download vs. slow DU extraction) | Independent projects allow different robot counts per stage for throughput balancing |
| 5 | Reporting requirements (Excel report, email summary, dashboard data) | Dedicated Reporting project reads from a reporting queue populated by all other stages |
| 6 | Multiple output channels from a single input (e.g., XML to MQ + files to FTP + report to email) | Separate Performer per output channel avoids coupling unrelated integrations |

### Common decomposition patterns

#### Dispatcher / Performer (most common)

Use when the process collects items from a source (email, folder, spreadsheet, API) and then processes each item transactionally.

```text
[Dispatcher] → Queue → [Performer] → Reporting Queue → [Reporting]
```

- **Dispatcher**: collects items, creates queue items with all required data. Runs as a simple sequence (no REFramework).
- **Performer**: processes one transaction item at a time. Uses **REFramework** for retry, logging, and state management.
- **Reporting** (optional): reads from a reporting queue, generates reports. Runs on a schedule or after Performer completes.

#### Dispatcher / DU Performer / Output Performer

Use when the process has Document Understanding with human validation as a middle stage.

```text
[Dispatcher] → DU Queue → [DU Performer] → Output Queue → [Output Performer]
                                ↓                              ↓
                          Action Centre                  Reporting Queue
                                                               ↓
                                                         [Reporting]
```

- **Dispatcher**: downloads emails/files, creates queue items.
- **DU Performer**: runs DU extraction, sends low-confidence items to Action Centre, pushes validated results to the output queue. Uses REFramework.
- **Output Performer**: generates output (XML, CSV, API calls), uploads to target systems. Uses REFramework.
- **Reporting**: aggregates outcomes from all stages.

### RPA Process (single-product scope) — narrower project list

When the primary scope is RPA Process (not a Solution), Part A directly produces this form of project list (Part B of the main guide is trivial in this case):

| # | Project Name | Role | Framework | Input Queue | Output Queue |
|---|---|---|---|---|---|
| 1 | `<NAME>_Dispatcher` | Collect items from source, dispatch to processing queue | Sequence | — | `<QUEUE_1>` |
| 2 | `<NAME>_Performer` | Process each transaction item | REFramework | `<QUEUE_1>` | `<REPORTING_QUEUE>` |
| 3 | `<NAME>_Reporting` | Generate reports from processing outcomes | Sequence | `<REPORTING_QUEUE>` | — |

Queue definitions for the `<QUEUE_1>` and `<REPORTING_QUEUE>` placeholders are authored in §12 of the RPA template (`assets/templates/rpa-sdd-template.md`). §12 is the single source of truth for queue shape — `Queue Definitions` table + one `Queue Item Schema` subsection per queue. Do not invent a different column layout in Part A or Part B.

For Solutions, feed the rows produced by Part A into Level 2.5 Part B of [product-selection-guide.md](product-selection-guide.md#part-b--merge-into-the-final-project-list) to merge with the non-RPA projects.

### Sub-project naming convention (rule R-07)

Every row in the project list uses the pattern:

```
<PROCESS_SHORT_NAME_PASCAL>_<ROLE_SUFFIX>
```

- `<PROCESS_SHORT_NAME_PASCAL>` — a PascalCase short-name derived from the PDD process name. Strip filler words (`Process`, `Automation`, `RPA`) and any version suffix. Example: "Invoice Processing Automation v2" → `InvoiceProcessing`.
- `<ROLE_SUFFIX>` — one of the registered suffixes below. Invent a new suffix only when a role is not covered.

| Suffix | Role |
|---|---|
| `_Dispatcher` | Collects items from a source and pushes them onto a queue |
| `_Performer` | Consumes queue items and processes each transactionally (REFramework) |
| `_DUPerformer` | Performer variant dedicated to Document Understanding extraction + validation |
| `_OutputPerformer` | Performer variant that consumes validated data and writes to a downstream system (API, file, message bus) |
| `_Reporting` | Reads a reporting queue and generates reports / dashboards / summary emails |
| `_SharedUtils` | RPA Library containing reusable workflows called by other projects in the Solution |

Worked example — PDD: "Weekly Vendor Invoice Ingestion". Short-name: `VendorInvoice`. Unified project list:

| # | Project Name | Role |
|---|---|---|
| 1 | `VendorInvoice_Dispatcher` | Download vendor emails + attachments, enqueue |
| 2 | `VendorInvoice_DUPerformer` | Classify + extract invoice fields, send to Action Centre on low confidence |
| 3 | `VendorInvoice_OutputPerformer` | Post validated invoices to the ERP API |
| 4 | `VendorInvoice_Reporting` | Aggregate outcomes into the weekly ops email |
| 5 | `VendorInvoice_SharedUtils` | Shared vendor lookup + currency conversion helpers |

For RPA Library and RPA Test Automation projects in a Solution that are **not** queue-connected sub-projects of a Master Project, use the same short-name prefix but pick a role suffix that reflects the project's purpose (e.g., `_SharedUtils`, `_Regression`, `_SmokeTests`).

## REFramework guidance

REFramework is the standard UiPath framework for **transactional processes** — any process that iterates over discrete units of work where each unit can succeed or fail independently. It provides: Init → Get Transaction → Process Transaction → End Process states, with built-in retry, exception handling, and logging.

### Use REFramework when…

**Use REFramework whenever the process iterates over discrete units of work with independent per-item success/failure.** Queue presence is **NOT** a precondition. The source of the transactions can be:

- **Orchestrator queue items** — the canonical case; `GetTransactionData` pulls one item at a time.
- **In-memory transactions** — a list, DataTable, or collection loaded once and processed per row (e.g., a CSV read into memory, then iterated row by row).
- **Rows / records read from a UI** — items extracted from a web app's work-item list, a desktop grid, or a SaaS UI's table. The Performer reads the source UI itself to populate transactions on each iteration; no Orchestrator queue is involved.
- **Files in a folder** — each file is a transaction; the framework iterates over the folder contents.
- **Records returned by an API page** — paginated API results where individual records can fail independently.

The defining criterion is **per-item independence**: one failing item must not block the others, must be retryable on its own, and must be tracked separately. Any source that satisfies this — queue, memory, UI, file system, API — justifies REFramework.

### Do NOT use REFramework when…

- The unit of work is **atomic** (the whole run succeeds or fails as one) — e.g., a single SQL query + single email, no per-item granularity.
- The process is a **simple linear pipeline** with no iteration and no retry semantics.
- The process is a **Library** or **Test Automation** project (those have their own templates).

### Framework selection per role

| Project Role | Framework | Why |
|---|---|---|
| Performer (queue-based) | **REFramework** | Built-in transaction retry, state management, exception routing |
| Performer (in-memory transactions or UI-row iteration, no Orchestrator queue) | **REFramework** | Each row / record is a transaction with independent success/failure; queue presence is not required to justify the framework |
| Dispatcher — atomic collect-then-commit (e.g., single SQL query, single folder scan) | **Sequence** | Collection is one unit of work; no per-item retry semantics required |
| Dispatcher — retryable items (e.g., paginated API, flaky source where individual pages/items can fail) | **REFramework** | Each retrieved item is itself a transaction; per-item retry + state tracking justify REFramework |
| Reporting (reads queue, generates output) | **REFramework** *(default)* or Sequence | Use REFramework when per-item reporting failures must be tracked, or when the reporting queue can exceed ~10 items per run (typical for daily/weekly aggregation over a Master Project). Use Sequence only for atomic end-of-run aggregation of a small, fixed set of items where a single failure can fail the whole run without loss. |
| Single Project (no queues, but iterates discrete items) | **REFramework** | REFramework gives per-item retry + state tracking even without a queue. Lifecycle just becomes Init → GetTransactionData (loads from memory / UI / file system) → Process → SetTransactionStatus. |
| Single Project (no iteration at all) | **Sequence** | Linear pipeline, no transactions, no retry semantics. |

**Rule R-04 — REFramework boundary:** a project uses REFramework when its unit of work is an **item that can fail, be retried, and be tracked independently** — regardless of whether the items come from a queue, memory, UI, file system, or API. A project uses Sequence when its unit of work is **atomic** (the whole run succeeds or fails as one).

When REFramework is selected for a project, the project structure in §11 of the RPA template must use the REFramework folder layout (Init, GetTransactionData, Process states) instead of a custom framework.

### Worked example — Performer reading WI rows from a web UI, no queue

**Scenario:** A web app shows a list of Work Items. The robot logs in, filters the list, then for each row: opens the WI, reads fields, computes an output, writes the result back, marks the WI processed. No Orchestrator queue. Volume is small (~15 items/day).

**Decision:** **REFramework.** Justification:
- Each WI row is a discrete unit of work with independent success/failure.
- A failed WI must not block the remaining items — REFramework's per-transaction exception handling delivers this for free.
- Per-item retry on system errors (selector failure, browser glitch) is the right behaviour — REFramework retries the failed transaction without restarting the run.
- Lower volume does not change the analysis. "Only 15 items" is irrelevant; the question is whether items are independent, not how many there are.

**Anti-pattern:** picking Sequence with a custom try/catch loop around the iteration. The custom loop will re-implement state tracking, retry counts, exception routing, and Init/teardown — all of which REFramework provides out of the box, more robustly.

**Sources of transactions per the Performer's `GetTransactionData`:**
- For this scenario: read the next row from the web UI's WI list (via UIA `NGetText` or table extraction).
- No queue dependency: `GetTransactionData` returns the next un-processed WI from the UI's current state.

### Anti-pattern: "no queue, so no REFramework"

Reasoning along the lines of "this process has ~15 items/day, no Orchestrator queue, no peak load — REFramework is overkill" is wrong on every count:

- Volume is not the criterion — independence is.
- Queue is not the criterion — independence is.
- REFramework's overhead is fixed (folder layout + states). The per-item benefits — retry, exception isolation, state tracking — apply whether items come from a queue or the UI.

If you find yourself rejecting REFramework on volume or queue-absence grounds, re-read the "Use REFramework when…" criteria above before committing to Sequence + custom loop.
