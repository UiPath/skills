# Preferences: migration team

> Standing answers and development standards for rebuilding a set of existing automations in UiPath, for every solution, process and library of the migration. `uipath-planner` applies them while it writes a genome, and `uipath-genome` reads them before its first question. A preference that conflicts with a rule of either skill is put to you with both. Leave out a line to have it asked each time.

## Standing answers

- **Project template:** REFramework for processes, used as designed.
- **Target framework and expression language:** Windows, Visual Basic.
- **Workflow type:** XAML; a coded workflow only where the step cannot be done without code.
- **Library layout:** each library a package of its own, one library project per source component.
- **Log target:** Orchestrator's job log (Log Message), not the source's logging components.
- **Source fidelity, in a migration:** the source's names, and its structure only where UiPath does not do the work in one or a few activities; all functionality kept. UiPath practice where it does the job better: UiPath activities replace the source's utility components (Standards 3), several steps become one activity where one does them, obsolete workarounds are dropped. Each difference is a row of the correspondence table.

## Standards

1. **Naming:**
   - **Workflow files:** the source step's or action's name in PascalCase, words joined, acronyms upper case, `&` written `And`: `Login Portal` → `LoginPortal.xaml`.
   - **A step that now does something else** is named after what it does, in its file name and its display name: a step that added queue items and now writes sheet rows becomes `WriteSheetRecords.xaml`, "Write the sheet's records".
   - **Projects and libraries:** the source's words in order, separated by dots, each in PascalCase, acronyms upper case, `&` written `And`: `CRM INVOICES & CREDITS Process 2024` → `CRM.Invoices.And.Credits.Process.2024`.
2. **Project structure:**
   - Only what is used is migrated, libraries included: at the end of the build, every workflow has a caller. Workflows that only look alike are not merged.
   - Each project is packed on its own; projects are not assembled into solutions.
   - The projects of one source process sit in one folder named after it, such as `<Area>.<Number>.<Name>`.
   - In a process project every workflow except `Main.xaml` sits in `Workflows\`; `Framework\`, `Tests\` and `Data\` stay where the template puts them.
3. **Activities:**
   - **Office applications:** Word, Excel and Outlook work goes through UiPath's activities for that application wherever one does the step.
   - **Excel through its activities, never its window:** clicks, keystrokes, menus or copy and paste on the Excel window are rebuilt with the Excel activities inside Use Excel File, never as UI automation on Excel. Excel runs hidden whenever no step needs its window.
   - **Closing applications:** an application closes softly through its Use Application/Browser card: close it, wait up to `SoftCloseWaitSeconds` (default 5; a Config setting in processes, a constant in libraries) for its window to go, then kill only what is still open, in the robot's own session.
   - **Mail** goes through the Microsoft 365 activities; no desktop Outlook.
   - **Modern activities** (Excel, Take Screenshot), the REFramework's own files included. A classic activity only where no modern one does the step, with the reason in its annotation.
4. **Libraries:** stateless, every workflow public. A value a source component keeps between calls is either a setting, the same on every call, kept as a constant in the library's `Constants.cs`; or state that changes from call to call, kept by the calling process and passed in as an argument.
5. **Process design:**
   - **Workbook flows:** one queue item per workbook, its rows records in a Data Fabric entity. Flows of the same shape use the same model.
   - **Lists worked in one run:** rows one robot works through in one run are a For Each, not a get-next over a "taken" flag; a queue only where items run in parallel or must survive a crash.
6. **Error handling:** a catch routes by exception type, never by message text; a Try Catch that only rethrows is removed. The source's error codes stay in the failure notifications.
7. **Code:**
   - **No leftovers:** variables nothing uses are removed. Deep-nesting warnings may stay.
   - **Switch** in place of a chain of Ifs on one value.
   - **Annotations:** every workflow, and each activity where it helps, says in plain words what it does.
8. **Hand-off:**
   - **Audience:** the team that runs and maintains the automations, with general automation knowledge. The documents are simple and friendly and leave out migration internals.
   - **Format:** one report per solution, as an HTML page and an Excel file. The HTML page has a tab per report, each with a filter, in UiPath's Apollo light and dark themes as Orchestrator uses them. Two Markdown files sit beside them: the Overview, and the open items (Deployment open items and the TODO list).
   - **Template:** [handoff-report-template.html](handoff-template/handoff-report-template.html); how to fill it: [README](handoff-template/README.md).
   - **Reports**, in this order:
     1. **Overview:** a one-page Markdown description of the process: how the source works, what it was migrated to and why.
     2. **Workflow map:** each source process and component to its UiPath workflow file.
     3. **Design decisions:** each design decision with its reason.
     4. **Defect register:** each source defect carried over, with its source file and migrated workflow.
     5. **TODO list:** only what the migration could not do and a person must do, with the source place (file, process or component, step), the migrated place (project, workflow file, activity) and why. Every TODO left in a project is listed.
     6. **Deployment open items:** set-up, queues and entities, triggers, assets with their default values (the values found in the source), credential assets, settings, and deployment notes (robot software, live checks); each asset, setting and credential names the workflows that use it.
     7. **Structural deviations:** what differs in the UiPath implementation and why, with the source's workflow and step names, split into Added, Removed (not migrated) and Changed.
     8. **Process components**, last: diagrams of the source's and the migration's processes and queues, each node named by its real process name; for each Data Fabric entity, why it exists, what it holds and which projects use it.
   - **Live checks:** one row per UI library ("verify this library's screens on the live application"), not one per target.

## Left open

Settings store, Package feed.
