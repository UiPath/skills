# Preferences: migration team

> Standing answers and development standards for every UiPath build of the migration team: each solution, process and library rebuilt from an existing automation. `uipath-planner` applies them while it writes a genome, and `uipath-genome` reads them before its first question. A preference that conflicts with a rule of either skill is put to you with both. Leave out a line to have it asked each time.

## Standing answers

The questions a build asks that this file answers for every genome, one line each.

- **Project template:** REFramework, used as designed.
- **Target framework and expression language:** Windows, Visual Basic.
- **Workflow type:** XAML; coded only for a step that cannot be done without code.
- **Library layout:** each library a package of its own, one per source component.
- **Log target:** Orchestrator's job log, not the source's logging components.
- **Source fidelity, in a migration:** the source's names and shape, all functionality kept, except where UiPath does the job better: its activities replace the source's utility components, several steps become one activity where one does them, and obsolete workarounds are dropped. Each difference is a row of the correspondence table.

## Standards

The standards the build follows beyond the genome.

1. **Naming:**
   - Workflows: the source step's or action's name in PascalCase, words joined, acronyms upper case, `&` written `And` (`Login Portal` → `LoginPortal.xaml`).
   - A step that now does something else: named after what it does, in its file name and display name (a step that added queue items and now writes sheet rows → `WriteSheetRecords.xaml`, "Write the sheet's records").
   - Projects and libraries: the source's words in order, separated by dots, each in PascalCase, acronyms upper case, `&` written `And` (`CRM INVOICES & CREDITS Process 2024` → `CRM.Invoices.And.Credits.Process.2024`).
2. **Project structure:**
   - Only what is used is migrated, libraries included: every workflow has a caller. Workflows that only look alike are not merged.
   - The projects of one source process in one folder named after it (`<Area>.<Number>.<Name>`).
   - In a process project, every workflow except `Main.xaml` in `Workflows\`; `Framework\`, `Tests\` and `Data\` where the template puts them.
   - Libraries stateless, every workflow public. A value a source component keeps between calls is a constant in the library's `Constants.cs` when it is the same on every call, and an argument the calling process keeps when it changes from call to call.
3. **Error handling:** catches route by exception type, never by message text; a Try Catch that only rethrows is removed. The source's error codes stay in the failure notifications.
4. **UI automation:**
   - Applications close softly through their Use Application/Browser card: close, wait up to `SoftCloseWaitSeconds` (default 5; a Config setting in processes, a constant in libraries) for the window to go, then kill only what is still open, in the robot's own session.
   - Excel is never driven through its window: clicks, keystrokes, menus and copy and paste on it are rebuilt with the Excel activities inside Use Excel File.
5. **Code:**
   - Activities: Word, Excel and Outlook work through UiPath's activities for that application wherever one does the step; mail through the Microsoft 365 activities, never desktop Outlook; Excel hidden whenever no step needs its window.
   - Modern activities (Excel, Take Screenshot), the REFramework's own files included; a classic activity only where no modern one does the step, with the reason in its annotation.
   - Annotations on every workflow, and on each activity where they help, saying in plain words what it does.
   - Workflow analyzer: variables nothing uses removed; deep-nesting warnings may stay. Switch in place of a chain of Ifs on one value.
6. **Packaging and versioning:** each project packed on its own, never assembled into a solution.
7. **Process design:**
   - Rows one robot works through in one run: a For Each, not a get-next over a "taken" flag; a queue only where items run in parallel or must survive a crash.
8. **Hand-off:**
   - Audience: the team that runs and maintains the automations, with general automation knowledge. Simple, friendly documents, without migration internals.
   - Format: one report per solution, as an HTML page and an Excel file, shaped as [handoff-report-example.html](handoff-report-example.html), whose opening comment says how to fill it: a tab per report, each with a filter, in UiPath's Apollo light and dark themes. Two Markdown files beside them: the Overview, and the open items (Deployment open items and the TODO list).
   - Reports, in this order:
     1. Overview: a one-page description of the process: how the source works, what it was migrated to and why.
     2. Workflow map: each source process and component to its UiPath workflow file.
     3. Design decisions: each with its reason.
     4. Defect register: each source defect carried over, with its source file and migrated workflow.
     5. TODO list: only what the migration could not do and a person must do, with the source place (file, process or component, step), the migrated place (project, workflow file, activity) and why; every TODO left in a project.
     6. Deployment open items: set-up, queues and entities, triggers, assets with the default values found in the source, credential assets, settings, deployment notes (robot software, live checks); each asset, setting and credential with the workflows that use it.
     7. Structural deviations: what differs in the UiPath implementation and why, by the source's workflow and step names, in Added, Removed (not migrated) and Changed.
     8. Process components, last: diagrams of the source's and the migration's processes and queues, each node by its real process name; for each Data Fabric entity, why it exists, what it holds and which projects use it.
   - Live checks: one row per UI library ("verify this library's screens on the live application"), not one per target.

## Left open

Settings store, Package feed.
