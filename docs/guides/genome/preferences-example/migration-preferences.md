# Migration preferences

Preferences for rebuilding a set of existing automations in UiPath. They apply to every solution, process and library of the migration. Only what is used is migrated, libraries included: at the end of the build, every workflow has a caller.

## 1. Activities

- **Office applications.** Word, Excel and Outlook work goes through UiPath's activities for that application wherever one does the step.
- **Excel through its activities, never its window.** Clicks, keystrokes, menus or copy and paste on the Excel window are rebuilt with the Excel activities inside Use Excel File, never as UI automation on Excel. Excel runs hidden whenever no step needs its window.
- **Starting and closing applications.** An application starts through its Use Application/Browser card, not Start Process. It closes softly through the card: close it, wait up to `SoftCloseWaitSeconds` (default 5; a Config setting in processes, a constant in libraries) for its window to go, then kill only what is still open, in the robot's own session.
- **Mail** goes through the Microsoft 365 activities; no desktop Outlook.
- **Modern activities** (Excel, Take Screenshot), the REFramework's own files included. A classic activity only where no modern one does the step, with the reason in its annotation.

## 2. Project layout

- Each project is packed on its own; projects are not assembled into solutions.
- The projects of one source process sit in one folder named after it, such as `<Area>.<Number>.<Name>`.
- In a process project every workflow except `Main.xaml` sits in `Workflows\`; `Framework\`, `Tests\` and `Data\` stay where the template puts them.

## 3. Languages and names

- Visual Basic expressions.
- XAML for most workflows; a coded workflow only where the step cannot be done without code.
- **Workflow file names**: the source step's or action's name in PascalCase, words joined, acronyms upper case, `&` written `And`: `Login Portal` → `LoginPortal.xaml`.
- **A step that now does something else** is named after what it does, in its file name and its display name: a step that added queue items and now writes sheet rows becomes `WriteSheetRecords.xaml`, "Write the sheet's records".
- **Project and library names**: the source's words in order, separated by dots, each in PascalCase, acronyms upper case, `&` written `And`: `CRM INVOICES & CREDITS Process 2024` → `CRM.Invoices.And.Credits.Process.2024`.

## 4. Workflow analyzer and readability

- **No leftovers**: variables nothing uses are removed. Deep-nesting warnings may stay.
- **Switch** in place of a chain of Ifs on one value.
- **Annotations**: every workflow, and each activity where it helps, says in plain words what it does.

## 5. Libraries

- Libraries are stateless, and every library workflow is public.
- A value a source component keeps between calls is one of two kinds:
  - a setting, the same on every call: a constant in the library's `Constants.cs`;
  - state that changes from call to call: kept by the calling process and passed in as an argument.

## 6. Configuration answers

- **Source fidelity**: the source's names, and its structure only where UiPath does not do the work in one or a few activities; all functionality kept. UiPath practice where it does the job better: UiPath activities replace the source's utility components (§ 1), several steps become one activity where one does them, obsolete workarounds are dropped, and the REFramework is used as designed. Each difference is a row of the correspondence table.
- **Library layout**: one library project per source component.
- Workflows that only look alike are not merged.

## 7. Processes and configuration

- **Logging** goes to the Orchestrator job log (Log Message), not through the source's logging components.
- **REFramework `Config.json`** has separate `Settings`, `Assets` and `Credential` sections; a section nothing uses is left out.
- **REFramework transactions**: the framework sets each item's outcome and handles its retries; the rebuild adds no mechanism of its own for either.
- **Workbook flows**: one queue item per workbook, its rows records in a Data Fabric entity. Flows of the same shape use the same model.
- **Lists worked in one run**: rows one robot works through in one run are a For Each, not a get-next over a "taken" flag; a queue only where items run in parallel or must survive a crash.
- **Robots coordinate through queues.** A queue item is locked while one robot works on it, so the automation keeps no locks of its own; a source component that coordinates robots with its own lock is split so the queue does it.
- **Exceptions**: a catch routes by exception type, never by message text; a Try Catch that only rethrows is removed. The source's error codes stay in the failure notifications.
- **Queries** filter on the server; a per-row loop reads once before it and writes in batch. A filter applied after the read is annotated with why.
- **Counts, limits and timeouts**: in Config in processes, in `Constants.cs` in libraries; a value fixed on purpose is annotated.

## 8. Hand-off

- **Audience**: the team that runs and maintains the automations, with general automation knowledge. The documents are simple and friendly and leave out migration internals.
- **Format**: one report per solution, as an HTML page and an Excel file. The HTML page has a tab per report, each with a filter, in a calm dark-blue theme. Two Markdown files sit beside them: the Overview, and the open items (Deployment open items and the TODO list).
- **Template**: [handoff-report-template.html](handoff-template/handoff-report-template.html); how to fill it: [README](handoff-template/README.md).
- **Reports**, in this order:
  1. **Overview**: a one-page Markdown description of the process: how the source works, what it was migrated to and why.
  2. **Workflow map**: each source process and component to its UiPath workflow file.
  3. **Variables**: per process and workflow, the scope and name in the source and in the migration.
  4. **Design decisions**: each design decision with its reason.
  5. **Defect register**: each source defect carried over, with its source file and migrated workflow.
  6. **TODO list**: only what the migration could not do and a person must do, with the source place (file, process or component, step), the migrated place (project, workflow file, activity) and why. Every TODO left in a project is listed.
  7. **Deployment open items**: set-up, queues and entities, triggers, assets with their default values (the values found in the source), credential assets, settings, and deployment notes (robot software, live checks); each asset, setting and credential names the workflows that use it.
  8. **Structural deviations**: what differs in the UiPath implementation and why, with the source's workflow and step names, split into Added, Removed (not migrated) and Changed.
  9. **Process components**, last: diagrams of the source's and the migration's processes and queues, each node named by its real process name; for each Data Fabric entity, why it exists, what it holds and which projects use it.
- **Live checks**: one row per UI library ("verify this library's screens on the live application"), not one per target.
