# RPA Product Guide

Load this guide when Level 1 of the [Product Selection Guide](product-selection-guide.md) selects **RPA**, or when a Level 1.75 Solution composition includes RPA projects.

RPA-specific levels/rules: **Level 1.5** — Process / Library / Test Automation; **Level 2** — XAML / Coded C# / Hybrid; **Level 2.5 Part A** — Single Project / Master Project; **R-07** — `<PROCESS_SHORT_NAME_PASCAL>_<ROLE_SUFFIX>`; **REFramework guidance** — REFramework / Sequence. Cross-product levels remain in the [Product Selection Guide](product-selection-guide.md): Level 1, Level 1.75, Level 2.5 Part B, and Level 3.

## Signals per RPA sub-type

Each RPA project has one subtype. Infer its default from these signals, then confirm at Level 1.5.

### RPA Library

Reusable component, shared standard activity, incomplete end-to-end process, public workflows exposed as activities, or NuGet distribution. Required PDD information: public workflow signatures (inputs, outputs), dependencies, and intended consumers.

### RPA Test Automation

Application-behavior validation, assertions, Test Manager integration, data-driven variations, or regression suite. Required PDD information: applications under test, test case list, and expected outcome per test.

### RPA Process (default)

UI-heavy web, desktop, Citrix, or virtual-desktop automation; Excel/Office or classic PDF operations (split, merge, non-AI text extraction); local/network files; on-prem database read/write via Database activities; terminal/mainframe automation (exclusive to RPA); desktop email clients; scheduled machine-local batch jobs; inter-application processing; attended or unattended execution; queue transactions; or a standard end-to-end business process. Use Process when no other subtype matches.

## Level 1.5 — RPA Sub-type Selection

Applies when Level 1 selects **RPA**, or Level 1.75 includes RPA projects; skip for non-RPA primaries without RPA in the composition.

### Recommended default

| Strongest Signal | Default Sub-type |
|---|---|
| Testing / assertions / Test Manager / regression pack | Test Automation |
| Reusable component / shared workflows / NuGet distribution | Library |
| Anything else | Process |

### User confirmation

Always confirm the sub-type with numbered-choice `AskUserQuestion`, even when only one signal set matches:

> This RPA project looks like a **<DEFAULT_SUBTYPE>**. Which sub-type should I use?
>
> 1. **<DEFAULT_SUBTYPE>** *(recommended)* — <ONE_LINE_REASON_FROM_PDD>
> 2. **<ALT_1>** — <ONE_LINE_DESCRIPTION>
> 3. **<ALT_2>** — <ONE_LINE_DESCRIPTION>

Accept a choice that disagrees with the signals and note the deviation in the recommendation's "Alternatives considered" block. In a Level 1.75 composition with two or more RPA projects, run Level 1.5 once per project; do not assume a shared subtype. The canonical example is *2 Libraries + 1 Test Automation*: three Level 1.5 confirmations, one per project.

## Level 2 — Authoring Mode

Applies to every RPA project (Process, Library, or Test Automation). This recommendation is directional; the workflow-building skill makes the final detailed decision.

| Process Characteristic | Recommended Mode |
|---|---|
| Primarily UI automation; simple linear or transactional flow (REFramework); heavy pre-built packages (SAP, Salesforce, Excel) | **XAML** |
| Significant transformation (parsing, regex, hashing, aggregation); REST APIs (HTTP, pagination, auth tokens); complex branching (5+ paths); custom typed DTOs or enums | **Coded C#** |
| UI automation plus complex data logic; multiple applications with different interaction patterns | **Hybrid** |

### Anti-pattern: picking Coded C# for UI-heavy automation

**Trigger:** the process is **>70% UI automation** against a browser, desktop app, or SaaS UI, with minimal HTTP/parsing/DTO/data-shaping work.

**Decision:** choose **XAML**, or **Hybrid** for a discrete non-trivial data-logic component. Do **NOT** choose Coded C# merely for cleaner control flow.

XAML provides Try/Catch, Retry Scope, If/Else, For Each, Sequence, and UIA activities (`Use Application/Browser`, `Click`, `Type Into`, `Get Text`). Studio's visual Indicate / `uia-configure-target` flow supplies selectors, attributes, content hashes, reference IDs, and Object Repository registration. Coded UI still requires OR registration plus `uiAutomation.Open` / `Attach`, `Descriptors.<App>.<Screen>.<Element>`, and screen-handle affinity rules, without capture-side productivity gain. Coded C# also requires manual `project.json` entry-point management, has no visual surface for non-coded contributors, and has no Studio designer canvas. Choose it for substantial data transforms, HTTP work, DTOs, or algorithms—not explicit if/else over UI activities.

Reserve Coded C# for:

- JSON deserialization, CSV parsing, LINQ aggregation, regex extraction, or hashing pipelines
- REST calls, pagination, transport retry/backoff, or auth-token refresh
- Custom DTOs, typed records, or enums (XAML cannot define types)
- Unit-testable pure functions exercised by Coded Test Cases
- Sorting, deduplication, fuzzy matching, or tree traversal

For mostly UI work with one non-trivial data step, use **Hybrid**: XAML orchestration/UI plus one Coded Workflow invoked with `Invoke Workflow File`.

For the full coded-vs-XAML decision flow, load the `uipath-rpa` skill and consult its coded-vs-XAML reference (architectural design only — final per-workflow decisions are made by the build skill).

### Selection checklist before recommending Coded C#

Before §13 Implementation Mode commits to Coded C#, confirm at least **two**:

- [ ] Significant data shaping / parsing / regex / hashing (more than one one-liner)
- [ ] HTTP / REST integration justifying a dedicated client
- [ ] Typed DTOs / records / enums used across multiple workflows
- [ ] Algorithmically non-trivial logic (LINQ aggregation, sorting, dedup, custom comparison)
- [ ] Unit-testable pure functions (exercised by Coded Test Cases on inputs the live system cannot easily reproduce)

If fewer than two are true and the body is >70% UI, recommend XAML. Do not use “cleaner control flow” in the §13 justification.

## Level 2.5 Part A — RPA Decomposition Signals

Apply to every RPA Process project; skip Library, Test Automation, and non-RPA products, which are always one project each. Signals are evidence: **2+ matches** makes a candidate Master Project only when each split has a **boundary**—independent scaling, independent failure recovery (queue-isolated per-stage retry/replay), separate ownership or deployment cadence, or independent scheduling. Otherwise use **Single Project** with internal phases. Transactional processing plus ordinary end-of-run reporting is usually one project. **0–1 matches** means Single Project.

Queue design is independent of decomposition: a Single Project that is queue-triggered, consumes an existing queue, or self-dispatches still fills §12 Queue Architecture; only a project with no queue involvement omits it.

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

For collection from email, folder, spreadsheet, or API followed by transactional processing:

```text
[Dispatcher] → Queue → [Performer] → Reporting Queue → [Reporting]
```

Dispatcher collects and queues required data using a simple Sequence. Performer handles one item with **REFramework**. Optional Reporting reads the reporting queue and runs on a schedule or after Performer completion.

#### Dispatcher / DU Performer / Output Performer

For Document Understanding with human validation:

```text
[Dispatcher] → DU Queue → [DU Performer] → Output Queue → [Output Performer]
                                ↓                              ↓
                          Action Centre                  Reporting Queue
                                                               ↓
                                                         [Reporting]
```

Dispatcher downloads and queues files/emails. DU Performer extracts, sends low-confidence items to Action Centre, and queues validated results using REFramework. Output Performer writes XML, CSV, API, or other outputs using REFramework. Reporting aggregates outcomes.

### RPA Process (single-product scope) — narrower project list

When the primary scope is RPA Process (not a Solution), Part A directly produces this list (Part B is trivial):

| # | Project Name | Role | Framework | Input Queue | Output Queue |
|---|---|---|---|---|---|
| 1 | `<NAME>_Dispatcher` | Collect items from source, dispatch to processing queue | Sequence | — | `<QUEUE_1>` |
| 2 | `<NAME>_Performer` | Process each transaction item | REFramework | `<QUEUE_1>` | `<REPORTING_QUEUE>` |
| 3 | `<NAME>_Reporting` | Generate reports from processing outcomes | Sequence | `<REPORTING_QUEUE>` | — |

Queue definitions for `<QUEUE_1>` and `<REPORTING_QUEUE>` are authored in §12 of the RPA template (`assets/templates/rpa-sdd-template.md`). §12 is the single source of truth: `Queue Definitions` table plus one `Queue Item Schema` subsection per queue. Do not invent another column layout in Part A or Part B.

For Solutions, feed Part A rows into Level 2.5 Part B of [product-selection-guide.md](product-selection-guide.md#part-b--merge-into-the-final-project-list) to merge with non-RPA projects.

### Sub-project naming convention (rule R-07)

Every project-list row uses:

```text
<PROCESS_SHORT_NAME_PASCAL>_<ROLE_SUFFIX>
```

`<PROCESS_SHORT_NAME_PASCAL>` is PascalCase from the PDD process name; strip filler words (`Process`, `Automation`, `RPA`) and version suffixes. Example: "Invoice Processing Automation v2" → `InvoiceProcessing`. `<ROLE_SUFFIX>` is one of the registered suffixes below; invent a new suffix only when no registered role covers it.

| Suffix | Role |
|---|---|
| `_Dispatcher` | Collects source items and pushes them to a queue |
| `_Performer` | Consumes queue items and processes each transactionally (REFramework) |
| `_DUPerformer` | Document Understanding extraction and validation Performer |
| `_OutputPerformer` | Consumes validated data and writes to an API, file, or message bus |
| `_Reporting` | Reads a reporting queue and generates reports, dashboards, or summary emails |
| `_SharedUtils` | RPA Library with reusable workflows called by Solution projects |

Worked example — PDD: "Weekly Vendor Invoice Ingestion". Short-name: `VendorInvoice`. Unified project list:

| # | Project Name | Role |
|---|---|---|
| 1 | `VendorInvoice_Dispatcher` | Download vendor emails + attachments, enqueue |
| 2 | `VendorInvoice_DUPerformer` | Classify + extract invoice fields, send to Action Centre on low confidence |
| 3 | `VendorInvoice_OutputPerformer` | Post validated invoices to the ERP API |
| 4 | `VendorInvoice_Reporting` | Aggregate outcomes into the weekly ops email |
| 5 | `VendorInvoice_SharedUtils` | Shared vendor lookup + currency conversion helpers |

For RPA Library and RPA Test Automation projects in a Solution that are not queue-connected Master Project sub-projects, use the same short-name prefix and a purpose-based suffix (for example, `_SharedUtils`, `_Regression`, `_SmokeTests`).

## REFramework guidance

REFramework is UiPath's standard framework for transactional processes: any process that iterates over discrete units of work where each unit can succeed or fail independently. It provides Init → Get Transaction → Process Transaction → End Process, with retry, exception handling, and logging.

### Use REFramework when…

Use it whenever items can fail, be retried independently, and be tracked separately, regardless of source: Orchestrator queue items (`GetTransactionData` pulls one at a time), in-memory lists, DataTables or collections, UI-table/grid rows, folder files, or paginated API records.

### Do NOT use REFramework when…

- The whole run is atomic, such as one SQL query plus one email with no per-item granularity.
- The process is a simple linear pipeline with no iteration or retry semantics.
- The project is a Library or Test Automation project, which has its own template.

### Framework selection per role

| Project Role | Framework | Rule |
|---|---|---|
| Performer (queue-based) | **REFramework** | Transaction retry, state management, exception routing |
| Performer (in-memory or UI-row iteration, no queue) | **REFramework** | Independent row/record success and failure; queue is not required |
| Dispatcher — atomic collect-then-commit | **Sequence** | One unit of work; no per-item retry |
| Dispatcher — retryable items (paginated API or flaky source) | **REFramework** | Retrieved items need per-item retry and state tracking |
| Reporting | **REFramework** *(default)* or Sequence | REFramework when per-item reporting failures must be tracked, or when the reporting queue can exceed ~10 items per run; Sequence only for atomic end-of-run aggregation of a small, fixed set where one failure may fail the whole run without loss |
| Single Project (no queues, discrete-item iteration) | **REFramework** | Init → GetTransactionData (memory/UI/file system) → Process → SetTransactionStatus |
| Single Project (no iteration) | **Sequence** | Linear pipeline without transactions or retry semantics |
| In-flight human approval / async wait (single process, not cross-product) | **Sequence or REFramework, + Persistence = YES** | Persistence modifies the selected framework; see [Long-running workflows](#long-running-workflows-persistence--action-center) |

**Rule R-04 — REFramework boundary:** use REFramework when the unit is an **item that can fail, be retried, and be tracked independently**, regardless of queue, memory, UI, file-system, or API source. Use Sequence when the unit is **atomic**.

**Proportionality note — REFramework is a template, not a mandate.** R-04 determines required semantics. For a genuinely trivial iteration—a 2-3 activity body, no per-item state beyond success/failure, and a safe, cheap full-run rerun—a Sequence with per-item Try/Catch and a documented rerun rule may provide equivalent semantics; record the deviation in §13's justification. Volume and queue absence never, by themselves, reject REFramework.

When selected, §11 of the RPA template must use the REFramework folder layout (Init, GetTransactionData, Process states), not a custom framework.

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

## Long-running workflows (persistence + Action Center)

RPA handles asynchronous human interaction **inside a single process**; do not escalate to Maestro or a separate HITL project solely because a human approves mid-run.

- **Mechanism:** use Studio long-running workflow Persistence activities—Create Form Task / Wait for Task and Resume. The job suspends, releases the robot without burning a license, and resumes, potentially on another robot, when the Action Center task completes.
- **Use when:** one process needs approval, validation, or an async wait (task completion, queue item, or job) and coordination remains within that process.
- **Do NOT use when:** the wait spans **multiple products** (RPA + agents + APIs) or needs formal gateways/events; use Maestro ([Product Selection Guide → Maestro disambiguation](product-selection-guide.md#maestro-disambiguation--bpmn-vs-flow-vs-case)).
- **Identities & licensing:** record the **start identity** (attended-user start is supported), **resume identity** (typically unattended robot; may differ from the start robot), and each licensing implication. Attended-start plus unattended-resume is valid and common (§11 Attendance column).
- **SDD impact:** set Persistence = YES in §11 Project Mode Decision while retaining Sequence/REFramework; mark suspend/resume points in the Workflow Inventory; flag the approval as an Action Center touchpoint, not a `uipath-human-in-the-loop` task.