# RPA Product Guide

Load this guide when Level 1 of the [Product Selection Guide](product-selection-guide.md) selects **RPA**, or when a Level 1.75 Solution composition includes one or more RPA projects.

Canonical home for:

- **Level 1.5** — RPA sub-type: Process / Library / Test Automation
- **Level 2** — Authoring mode: XAML / Coded C# / Hybrid
- **Level 2.5 Part A** — RPA decomposition: Single Project / Master Project
- **R-07** — `<PROCESS_SHORT_NAME_PASCAL>_<ROLE_SUFFIX>` naming
- REFramework versus Sequence guidance

Cross-product levels remain in the [Product Selection Guide](product-selection-guide.md): Level 1, Level 1.75, Level 2.5 Part B, and Level 3.

## Signals per RPA sub-type

### RPA Library

Use Library for reusable components, shared standard activities, public workflows consumed by other projects, or NuGet distribution rather than a complete end-to-end process. Required information: public workflow signatures (inputs and outputs), dependencies, and intended consumers.

### RPA Test Automation

Use Test Automation for application validation through test cases and assertions, Test Manager integration, data-driven variations, or regression suites. Required information: applications under test, test-case list, and expected outcomes per test.

### RPA Process (default)

Use Process for UI-heavy automation; Excel/Office or classic PDF operations; local or network file operations; on-premises Database activities; terminal/mainframe automation; Outlook or scheduled machine-local jobs; application-to-application data processing; attended or unattended execution; queue-based transactions; and standard end-to-end business processes. Terminal/mainframe automation is exclusive to RPA.

## Level 1.5 — RPA Sub-type Selection

Apply to every RPA project selected at Level 1 or included at Level 1.75. Skip only when the scope contains no RPA.

| Strongest signal | Recommended sub-type |
|---|---|
| Testing, assertions, Test Manager, or regression pack | Test Automation |
| Reusable component, shared workflows, or NuGet distribution | Library |
| Anything else | Process |

Always confirm with `AskUserQuestion`, using numbered choices, even when one signal set matches:

> This RPA project looks like a **<DEFAULT_SUBTYPE>**. Which sub-type should I use?
>
> 1. **<DEFAULT_SUBTYPE>** *(recommended)* — <ONE_LINE_REASON_FROM_PDD>
> 2. **<ALT_1>** — <ONE_LINE_DESCRIPTION>
> 3. **<ALT_2>** — <ONE_LINE_DESCRIPTION>

Accept a choice that disagrees with the signals and record the deviation in the recommendation's **Alternatives considered** block. For two or more RPA projects in a Solution, run Level 1.5 once per project; do not assume a shared sub-type.

## Level 2 — Authoring Mode

Apply to every RPA project, including Libraries and Test Automation.

| Characteristic | Recommended mode |
|---|---|
| Primarily UI automation | **XAML** |
| Simple linear or transactional flow, including REFramework | **XAML** |
| Heavy use of pre-built SAP, Salesforce, or Excel packages | **XAML** |
| Significant transformation: parsing, regex, hashing, or aggregation | **Coded C#** |
| REST/API integration: HTTP, pagination, or auth tokens | **Coded C#** |
| Complex branching with 5+ decision paths | **Coded C#** |
| Custom DTOs, typed records, or enums | **Coded C#** |
| UI automation plus complex data logic | **Hybrid** |
| Multiple applications with different interaction patterns | **Hybrid** |

This is directional; the skill that builds the workflows makes the final detailed decision.

### UI-heavy anti-pattern

If the body is **>70% UI automation** against a browser, desktop app, or SaaS UI, with minimal HTTP, parsing, DTO, or data-shaping work, choose **XAML**, or **Hybrid** for one discrete non-trivial data-logic component. Do not choose Coded C# merely for cleaner control flow.

XAML provides Try/Catch, Retry Scope, If/Else, For Each, and Sequence around UIA activities such as `Use Application/Browser`, `Click`, `Type Into`, and `Get Text`. Studio's visual Indicate / `uia-configure-target` flow produces selectors, content hashes, reference IDs, and Object Repository registrations. Coded UI still requires the same OR registration plus `uiAutomation.Open` / `Attach`, `Descriptors.<App>.<Screen>.<Element>` references, and screen-handle affinity management; it also adds manual `project.json` entry-point management, no visual surface, and no Studio designer canvas. These costs are justified by substantial data, HTTP, typed-model, testing, or algorithmic work—not UI orchestration.

Reserve Coded C# for JSON deserialization, CSV parsing, LINQ aggregation, regex extraction, hashing pipelines, other substantial data transformation, REST calls, pagination, transport retry/backoff, auth-token refresh, DTOs, typed records, enums, pure functions covered by Coded Test Cases, sorting, deduplication, fuzzy matching, tree traversal, or other algorithm-heavy logic.

For UI plus one non-trivial data step, use Hybrid: XAML for orchestration/UI and one Coded Workflow invoked with `Invoke Workflow File`.

For the full coded-vs-XAML decision flow, load the `uipath-rpa` skill and consult its coded-vs-XAML reference (architectural design only; final per-workflow decisions belong to the build skill).

### Selection checklist before recommending Coded C#

Before §13 Implementation Mode commits to Coded C#, confirm at least **two**:

- [ ] Significant data shaping, parsing, regex, or hashing work beyond a one-liner
- [ ] HTTP/REST integration that justifies a dedicated client
- [ ] Typed DTOs, records, or enums used across multiple workflows
- [ ] Algorithmically non-trivial aggregation, sorting, deduplication, or custom comparison
- [ ] Unit-testable pure functions exercised by Coded Test Cases on inputs the live system cannot easily reproduce

If fewer than two are true and the body is >70% UI, recommend XAML. Do not use “cleaner control flow” in the §13 justification.

## Level 2.5 Part A — RPA Decomposition Signals

Apply to every **RPA Process** project. Skip Libraries, Test Automation, and non-RPA products; each is one project.

Treat signals as evidence. **2+ matches** make a Master Project a candidate, but every proposed split must have at least one boundary: independent scaling (different robot counts/speeds), independent failure recovery (queue-isolated retry/replay), separate ownership or deployment cadence, or independent scheduling. Without a boundary, use one project with internal phases. Transactional processing plus ordinary end-of-run reporting is usually one project. **0–1 matches** means Single Project.

Queue design is independent of decomposition: a Single Project that is queue-triggered, consumes an existing queue, or self-dispatches still fills §12 Queue Architecture. Omit §12 only when there is no queue involvement.

| # | PDD signal | Implication |
|---|---|---|
| 1 | Distinct stages with different characteristics | Consider independently developed, tested, and scaled projects |
| 2 | Independently failing transactional items | Consider queue-based retry and Performer projects using REFramework |
| 3 | Document Understanding or AI extraction with Action Centre validation | Consider a distinct DU processing stage and queue |
| 4 | Different processing speeds per stage | Consider independent robot counts for throughput balancing |
| 5 | Excel report, email summary, or dashboard-data requirements | Consider a Reporting project reading a reporting queue |
| 6 | Multiple output channels from one input | Consider separate Performers for unrelated integrations |

### Common patterns

**Dispatcher / Performer:**

```text
[Dispatcher] → Queue → [Performer] → Reporting Queue → [Reporting]
```

- Dispatcher collects source items and enqueues complete data; use a simple Sequence.
- Performer processes one transaction with REFramework.
- Reporting is optional and reads the reporting queue on schedule or after the Performer.

**Dispatcher / DU Performer / Output Performer:**

```text
[Dispatcher] → DU Queue → [DU Performer] → Output Queue → [Output Performer]
                                ↓                              ↓
                          Action Centre                  Reporting Queue
                                                               ↓
                                                         [Reporting]
```

The Dispatcher downloads and enqueues; the DU Performer extracts, sends low-confidence items to Action Centre, and pushes validated data; the Output Performer writes to downstream systems; Reporting aggregates outcomes. Use REFramework for the transactional Performers.

### RPA Process single-product project list

When the primary scope is RPA Process rather than a Solution, Part A directly produces this list; Part B is trivial:

| # | Project Name | Role | Framework | Input Queue | Output Queue |
|---|---|---|---|---|---|
| 1 | `<NAME>_Dispatcher` | Collect items and dispatch | Sequence | — | `<QUEUE_1>` |
| 2 | `<NAME>_Performer` | Process each transaction | REFramework | `<QUEUE_1>` | `<REPORTING_QUEUE>` |
| 3 | `<NAME>_Reporting` | Generate reports | Sequence | `<REPORTING_QUEUE>` | — |

Queue definitions for `<QUEUE_1>` and `<REPORTING_QUEUE>` belong in §12 of the RPA template, `assets/templates/rpa-sdd-template.md`. §12 is the single source of truth: use its `Queue Definitions` table and one `Queue Item Schema` subsection per queue. Do not create another column layout in Part A or Part B.

For Solutions, pass Part A rows to Level 2.5 Part B of [product-selection-guide.md](product-selection-guide.md#part-b--merge-into-the-final-project-list) to merge with non-RPA projects.

## Rule R-07 — Sub-project naming

Every project-list row uses:

```text
<PROCESS_SHORT_NAME_PASCAL>_<ROLE_SUFFIX>
```

Derive the PascalCase short name from the PDD process name; strip filler words (`Process`, `Automation`, `RPA`) and version suffixes. Use a registered suffix when applicable; invent one only when no role is covered.

| Suffix | Role |
|---|---|
| `_Dispatcher` | Collects source items and pushes them to a queue |
| `_Performer` | Consumes queue items transactionally with REFramework |
| `_DUPerformer` | Performs Document Understanding extraction and validation |
| `_OutputPerformer` | Consumes validated data and writes to an API, file, or message bus |
| `_Reporting` | Reads a reporting queue and generates reports, dashboards, or summary emails |
| `_SharedUtils` | RPA Library with reusable workflows used by Solution projects |

For Library or Test Automation projects in a Solution that are not queue-connected Master Project sub-projects, use the same short-name prefix and a purpose-specific suffix such as `_SharedUtils`, `_Regression`, or `_SmokeTests`.

## REFramework guidance

REFramework is the standard framework for transactional processes: discrete units of work that can independently succeed or fail. It provides Init → Get Transaction → Process Transaction → End Process, with retry, exception handling, and logging.

### Use REFramework when

Use it whenever per-item independence is required: a failure must not block other items, and each item must be retryable and tracked separately. Sources may be Orchestrator queue items; in-memory lists, DataTables, or collections; rows/records read from a UI grid or SaaS table; files in a folder; or records from paginated API results. Queue presence is not required.

### Do not use REFramework when

- The unit of work is atomic, such as one SQL query plus one email with no per-item granularity.
- The process is a simple linear pipeline with no iteration or retry semantics.
- The project is a Library or Test Automation project.

### Framework selection by role

| Role | Framework | Rule |
|---|---|---|
| Queue-based Performer | **REFramework** | Transaction retry, state management, and exception routing |
| In-memory/UI-row/file/API-item Performer | **REFramework** | Independent per-item success/failure; no queue required |
| Atomic Dispatcher | **Sequence** | One collection unit; no per-item retry needed |
| Dispatcher with independently retryable pages/items | **REFramework** | Per-item retry and tracking justify it |
| Reporting | **REFramework** by default, or Sequence | Use REFramework when reporting failures require per-item tracking or the reporting queue can exceed ~10 items per run; use Sequence only for atomic aggregation of a small, fixed set where one failure may fail the run without loss |
| Single Project with discrete-item iteration | **REFramework** | Init → GetTransactionData → Process → SetTransactionStatus, even without a queue |
| Single Project with no iteration | **Sequence** | Atomic linear pipeline |
| Single process with an in-flight human approval/async wait | **Sequence or REFramework, + Persistence = YES** | Persistence modifies the selected framework; see [Long-running workflows](#long-running-workflows-persistence--action-center) |

**Rule R-04 — REFramework boundary:** use REFramework when the unit of work is an item that can fail, be retried, and be tracked independently, regardless of source. Use Sequence when the unit is atomic.

REFramework is a template, not a mandate. For a genuinely trivial iteration—a 2-3 activity body, no per-item state beyond success/failure, and a safe, cheap full-run rerun—a Sequence with per-item Try/Catch and a documented rerun rule may deliver the same semantics with less scaffolding. Record that deviation in §13's justification. Volume and queue absence alone never justify rejecting REFramework.

When REFramework is selected, §11 of the RPA template must use its Init, GetTransactionData, and Process folder/state layout rather than a custom framework.

Do not reject REFramework because there is no queue or the volume is low (for example, ~15 items/day). Independence—not volume or queue presence—is the criterion; otherwise a custom loop merely reimplements state tracking, retry counts, exception routing, and setup/teardown.

## Long-running workflows (persistence + Action Center)

Handle asynchronous human interaction inside one RPA process. Do not escalate to Maestro or create a separate HITL project merely because a human approves mid-run.

- **Mechanism:** use Studio long-running workflows and Persistence activities (`Create Form Task` / `Wait for Task and Resume`). The job suspends, releases the robot, and resumes—possibly on another robot—when the Action Center task completes.
- **Use when:** one process needs approval, validation, or an asynchronous task/queue/job wait, with coordination contained within that process.
- **Do not use when:** the wait spans multiple products (RPA + agents + APIs) or requires formal gateways/events; use Maestro, as described in [Product Selection Guide → Maestro disambiguation](product-selection-guide.md#maestro-disambiguation--bpmn-vs-flow-vs-case).
- **Record identities and licensing separately:** start identity (including supported attended-user starts), resume identity (typically unattended; may be a different robot), and the licensing implication of each. Attended-start plus unattended-resume is valid and common; record it in §11's Attendance column.
- **SDD impact:** set Persistence = YES in §11 Project Mode Decision; keep Sequence or REFramework as the framework; mark suspend/resume points in the Workflow Inventory; and flag the approval as an Action Center touchpoint, not a `uipath-human-in-the-loop` task.