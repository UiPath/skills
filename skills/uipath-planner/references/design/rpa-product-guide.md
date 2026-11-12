# RPA Product Guide

Load this guide when Level 1 of the [Product Selection Guide](../shared/product-selection-guide.md) selects **RPA**, or when a Solution composition at Level 1.75 includes one or more RPA projects.

This file is the **canonical home** for RPA-specific levels:

- **Level 1.5** — RPA sub-type selection (Process / Library / Test Automation)
- **Level 2** — Authoring mode (XAML / Coded C# / Hybrid)
- **Level 2.5 Part A** — RPA decomposition signals (Single Project vs Master Project)
- **R-07 naming convention** — `<PROCESS_SHORT_NAME_PASCAL>_<ROLE_SUFFIX>`
- **REFramework guidance** — when to use REFramework vs Sequence

Cross-product levels live in the [Product Selection Guide](../shared/product-selection-guide.md), [Solution Composition Guide](solution-composition-guide.md) and [Component Placement Guide](../shared/component-placement-guide.md):

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
- UI-heavy automation (web forms, desktop apps, Citrix / virtual desktop)
- Excel / Office automation; classic PDF operations (split, merge, non-AI text extraction)
- File & folder operations on local or network storage (move, rename, archive, watch folders)
- On-prem database read/write via Database activities (behind-the-firewall SQL)
- Terminal / mainframe (green-screen) automation — exclusive to RPA; no other product drives terminals
- Desktop email clients (Outlook); scheduled batch jobs over machine-local resources
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

In interactive mode, confirm the sub-type via a structured question with the numbered-choice format, even when only one signal set matches (autonomous mode takes the recommended sub-type and records it in Decisions Made):

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

For the full coded-vs-XAML decision flow, load the `uipath-rpa` skill and consult its coded-vs-XAML reference (architectural design only — final per-workflow decisions are made by the build skill).

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

**Start from one project; every split earns its boundary.** A sub-project exists only when §10 can name the fact that requires it: (a) **scaling** — the §16 sizing needs a different robot count per stage; (b) **failure isolation** — a stage's retry or replay must not repeat another stage's side effect (a costly re-extraction, a posting, a sent message); (c) **a long wait** — a stage holds an item for hours (a person's validation) while the other stages must keep moving; (d) **ownership or cadence** — another team, schedule or release cycle. The signals below are where to look, counted once per fact (a DU validation wait is one fact, not two signals), never a boundary by themselves. A shape the PDD itself names — its scheduling table lists `X_Dispatcher` and `X_Performer` — is the starting point; departing from it is a Decisions Made row. No boundary → **Single Project** with internal phases.

**Reporting is never a reason to split.** A report reads the outcomes the processing stage already records (queue item status and output, a run record); a reporting queue filled only to be read back once a day is a data store, not a hand-off.

> Queue design is independent of decomposition: a **Single Project** that is queue-triggered, consumes an existing queue, or self-dispatches still fills §12 Queue Architecture in the RPA template — only a project with no queue involvement omits it.

| # | Signal in PDD | What it means |
|---|---|---|
| 1 | Process has distinct stages with different characteristics (e.g., email ingestion vs. data extraction vs. output generation) | Each stage becomes a separate project that can be developed, tested, and scaled independently |
| 2 | Transactional processing where items can fail independently and must be retried per item | Queue-based retry requires Performer projects consuming from Orchestrator queues using REFramework |
| 3 | Document Understanding or AI extraction with human validation (Action Centre) | DU + validation is a distinct processing stage that benefits from its own project and queue |
| 4 | Different processing speeds per stage (e.g., fast email download vs. slow DU extraction) | Independent projects allow different robot counts per stage for throughput balancing |
| 5 | Multiple output channels from a single input (e.g., XML to MQ + files to FTP + report to email) | Separate Performer per output channel avoids coupling unrelated integrations |

### Common decomposition patterns

#### Dispatcher / Performer (most common)

Use when the process collects items from a source (email, folder, spreadsheet, API) and then processes each item transactionally.

```text
[Dispatcher] → Queue → [Performer]
```

- **Dispatcher**: collects items, creates queue items with all required data. Runs as a simple sequence (no REFramework).
- **Performer**: processes one transaction item at a time. Uses **REFramework** for retry, logging, and state management; its end-of-run step writes any report from the items' outcomes.

#### Dispatcher / DU Performer

Use when the process extracts documents with human validation (boundary (c)).

```text
[Dispatcher] → DU Queue → [DU Performer] ─ Action Center
```

- **Dispatcher**: downloads emails/files, creates queue items.
- **DU Performer**: extracts, sends low-confidence items to Action Center, then writes the output. Uses REFramework.
- A separate **Output Performer** behind an output queue only when boundary (b) holds — the output's retry must not repeat the extraction or the validation.

### RPA Process (single-product scope) — narrower project list

When the primary scope is RPA Process (not a Solution), Part A directly produces this form of project list (Part B of the main guide is trivial in this case):

| # | Project Name | Role | Framework | Input Queue | Output Queue |
|---|---|---|---|---|---|
| 1 | `<NAME>_Dispatcher` | Collect items from source, dispatch to processing queue | Sequence | — | `<QUEUE_1>` |
| 2 | `<NAME>_Performer` | Process each transaction item | REFramework | `<QUEUE_1>` | — |

Queue definitions for the `<QUEUE_1>` placeholder are authored in §12 of the RPA template (`assets/templates/rpa-sdd-template.md`). §12 is the single source of truth for queue shape — `Queue Definitions` table + one `Queue Item Schema` subsection per queue. Do not invent a different column layout in Part A or Part B.

For Solutions, feed the rows produced by Part A into Level 2.5 Part B of [solution-composition-guide.md](solution-composition-guide.md#part-b--merge-into-the-final-project-list) to merge with the non-RPA projects.

### Sub-project naming convention (rule R-07)

Every row of a Master Project's project list uses the pattern (a Single Project takes the short name alone):

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
| `_SharedUtils` | RPA Library containing reusable workflows called by other projects in the Solution |

Worked example — PDD: "Weekly Vendor Invoice Ingestion". Short-name: `VendorInvoice`. Unified project list:

| # | Project Name | Role |
|---|---|---|
| 1 | `VendorInvoice_Dispatcher` | Download vendor emails + attachments, enqueue |
| 2 | `VendorInvoice_DUPerformer` | Classify + extract invoice fields, send to Action Centre on low confidence |
| 3 | `VendorInvoice_OutputPerformer` | Post validated invoices to the ERP API |
| 4 | `VendorInvoice_SharedUtils` | Shared vendor lookup + currency conversion helpers |

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
| Single Project (no queues, but iterates discrete items) | **REFramework** | REFramework gives per-item retry + state tracking even without a queue. Lifecycle just becomes Init → GetTransactionData (loads from memory / UI / file system) → Process → SetTransactionStatus. |
| Single Project (no iteration at all) | **Sequence** | Linear pipeline, no transactions, no retry semantics. |
| Process with an in-flight human approval / async wait (single process, not cross-product) | **Sequence or REFramework, + Persistence = YES** | Persistence is a modifier on the chosen framework, not a framework: suspend the job, release the robot, resume on Action Center completion — see [Long-running workflows](#long-running-workflows-persistence--action-center) |

**Rule R-04 — REFramework boundary:** a project uses REFramework when its unit of work is an **item that can fail, be retried, and be tracked independently** — regardless of whether the items come from a queue, memory, UI, file system, or API. A project uses Sequence when its unit of work is **atomic** (the whole run succeeds or fails as one).

**Proportionality note — REFramework is a template, not a mandate.** R-04 decides the *semantics* the project needs (per-item retry, isolation, tracking); REFramework is the standard way to get them. For a genuinely trivial iteration — a 2-3 activity body, no per-item state beyond success/failure, and a full-run rerun that is safe and cheap — a Sequence with a per-item Try/Catch and a documented rerun rule delivers the same semantics with less scaffolding; record that deviation in §13's justification. This does NOT reopen the anti-patterns below: volume and queue-absence are never, by themselves, reasons to reject REFramework.

When REFramework is selected for a project, the project structure in §11 of the RPA template must use the REFramework folder layout (Init, GetTransactionData, Process states) instead of a custom framework.

### Independence, not volume or queues, decides

A robot that works ~15 work items a day from a web UI list, with no Orchestrator queue, is still REFramework: each item fails, retries and is tracked on its own, and `GetTransactionData` reads the next unprocessed item from the source itself. Rejecting REFramework on volume or queue absence and hand-writing a try/catch loop re-implements the framework's state tracking, retry counts, exception routing and Init / teardown, less robustly.

## Long-running workflows (persistence + Action Center)

RPA handles asynchronous human interaction **inside a single process** — do not escalate to Maestro or a separate HITL project just because a human approves mid-run.

- **Mechanism:** Studio long-running workflow (Persistence activities — Create Form Task / Wait for Task and Resume). The job **suspends**, the robot is **released** (no license burned while waiting), and the job **resumes** — potentially on a different robot — when the Action Center task completes.
- **Use when:** one process needs an in-flight approval, data validation, or async wait (task completion, queue item, job) and the rest of the coordination is within that process.
- **Do NOT use when:** the wait spans **multiple products** (RPA + agents + APIs) or needs formal gateways/events — that is Maestro territory ([Product Selection Guide → Maestro disambiguation](../shared/product-selection-guide.md#maestro-disambiguation--bpmn-vs-flow-vs-case)).
- **A waiting job works one item.** A suspended job keeps every queue item it took In Progress, so a queue-triggered performer that can suspend takes one item per job, and its retry is the queue's: the item stays In Progress until the job resumes and finishes it — never mark it Successful before the wait. Several waits on one item (two validations in sequence) stay in one job; a wait on a stage the item has already left is a split (boundary (c)).
- **Identities & licensing:** record three separate decisions — the **start identity** (an attended user start is supported, not just unattended), the **resume identity** (typically an unattended robot; resume may land on a different robot than the start), and the **licensing implication** of each. Attended-start + unattended-resume is a valid, common shape (§11 Attendance column).
- **SDD impact:** Persistence = YES in §11 Project Mode Decision (framework stays Sequence/REFramework); mark suspend/resume points in the Workflow Inventory; the approval task is flagged as an Action Center touchpoint, not a `uipath-human-in-the-loop` task.
