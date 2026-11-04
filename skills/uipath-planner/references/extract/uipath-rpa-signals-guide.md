# UiPath Source Guide — RPA Signals

Split out of [uipath-source-guide.md](uipath-source-guide.md), which is read first and whole; read the § Signals sections below whose artifact type the inventory holds.

## Signals — XAML

`project.json` fields first: `name`, `main`, `entryPoints[]` (`filePath`, `input`, `output`), `dependencies` (package IDs), `designOptions.outputType` (`Process` / `Library` / `Tests`), `expressionLanguage` (`VisualBasic` / `CSharp`), `targetFramework` (`Windows` / `Portable` / `Legacy`), `runtimeOptions.isAttended`, `runtimeOptions.requiresUserInteraction`, `globalHandler`.

| Signal | Where | Tells you | Example |
|---|---|---|---|
| Root element inside `<Activity>` | `<Sequence>`, `<Flowchart>`, `<StateMachine>` | Control-flow style; a `<StateMachine>` root in `Main.xaml` beside a `Framework/` folder is the REFramework (§ REFramework projects below) | `<StateMachine>` |
| `xmlns` declarations on `<Activity>` | root | Packages in use → target applications | `xmlns:umam="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail…"` |
| Activity elements in the body | e.g. `<ui:NTypeInto>`, `<umam:GetNewestEmail>`, `<p:ReadRange>`, `<ui:NClick>` | Business action of each step; `DisplayName` is best plain-language hint | `DisplayName="Read invoice sheet"` |
| `<x:Members>` → `<x:Property Type="InArgument(x:String)">` | header | Workflow interface: In / Out / InOut arguments | `Name="in_InvoicePath"` |
| `<If Condition>`, `<Switch>`, `<FlowDecision Condition>`, `<FlowSwitch>` | body | Business rules and routing | `Condition="[Amount > 10000]"` |
| `<TryCatch>` + `<Catch x:TypeArguments>`, `<RetryScope NumberOfRetries>`, `<Rethrow>`, `<Throw>` | body | Error handling per step | `NumberOfRetries="3"` |
| `<ForEach>`, `<While>`, `<DoWhile>`, `<ForEachRow>`, `<ui:ForEachUiElement>` | body | Iteration over items, rows, elements | |
| `<InvokeWorkflowFile FileName>` + `<Argument>` children | body | Call-graph edge and data passed | `FileName="ProcessInvoice.xaml"` |
| `ConnectionId` attribute, `<isactr:ConnectorActivity UiPathActivityTypeId>` | body | Integration Service connector call; resolve service from namespace or type id | `uipath-salesforce-sfdc` |
| Queue activities (`AddQueueItem`, `GetTransactionItem`, `SetTransactionStatus`), asset activities (`GetAsset`, `GetCredential`), `StartJob`, `CreateFormTask` / `WaitForFormTaskAndResume`, `Persistence` activities | body | Platform resources and HITL waits | queue name attribute |
| `<Variable x:TypeArguments Name>` | `.Variables` blocks | Data flow hints only — never in genome body | |
| Object Repository references (`uix:TargetAnchorable`, `uix:TargetApp`, `Descriptor` elements) | body | UI targets; name screen and application, never selector. `TargetApp Url` / `ScopeSelectorArgument url=` give target system's base URL → Configuration Question | `Url="https://<org>.lightning.force.com/…"` |
| `uix:NApplicationCard` / `ui:OpenBrowser` / `ui:OpenApplication` | body | Application scope: browser type, attach vs launch, one scope per application session | `BrowserType="Chrome" AttachMode="ByInstance"` |
| `DelayBefore` / `DelayAfter`, `WaitForReadyArgument`, `EmptyFieldMode` | UIA activity attributes | Timing and field-clearing behaviour → Error Handling wording ("waits for the dialog to settle", "replaces the pre-filled value") — never attribute names | `EmptyFieldMode="SingleLine"` |
| `SearchSteps="SemanticSelector"` with `SemanticSelectorArgument` | target | Element located by natural-language description, usually because no stable selector exists → Source Map note | |

Designer view state and layout sizes are not logic ([uipath-source-guide.md § Reading the Project](uipath-source-guide.md)).

### REFramework projects

A project built on the Robotic Enterprise Framework template is recognised by its shape, not by a manifest flag: `Main.xaml` is a `<StateMachine>` whose states are Init, Get Transaction Data, Process Transaction and End Process; a `Framework/` folder holds the framework workflows. The framework **is** the Transactional Shape ([transactional-shape-guide.md](../shared/transactional-shape-guide.md)); the business logic is the Workflow. Which file feeds which row:

| Source | Feeds | How |
|---|---|---|
| The queue and folder *Get Transaction Item* reads in `Framework/GetTransactionData.xaml`, set on the activity or from the configuration's settings | Transactional Shape As-is item store; Platform Dependencies (queue) | A queue name that the item-fetch workflow actually reads → `queue` mode, name kept as the source value. Blank, or the template's sample `ProcessABCQueue` beside a customised item fetch → `direct` mode, data source from that fetch |
| Settings and Constants rows — `MaxRetryNumber`, `MaxConsecutiveSystemExceptions`, and every custom row (URLs, paths, thresholds) | Sorted per [genome-format-guide.md § Configuration Questions](../shared/genome-format-guide.md): an environment row (URL, path, mailbox, folder) is a Configuration Question with the file's value as default; the two counts go in the outcomes table; every other row goes in the step or rule that uses it | `logF_BusinessProcessName`, `TransactionNumber`, `RetryNumberGetTransactionItem`, `RetryNumberSetTransactionStatus` are framework plumbing — no question |
| Assets the configuration lists, and the asset and credential activities | Platform Dependencies | One row per asset name; Credential when the description or the consuming activity says so, otherwise Text |
| `Framework/InitAllApplications.xaml` (`GetAppCredentials.xaml` in older templates) | Once-per-run steps; credential assets | Open and sign-in per application |
| `Framework/Process.xaml` (root `Process.xaml` in older templates) and every workflow it invokes | Per-item steps — the Workflow's numbered steps | The call graph starts here, not at `Main.xaml` |
| `Throw` of a `BusinessRuleException` inside the per-item workflows | Business Rules (the condition) and the business-exception row of the outcomes table | The exception message is the reason wording |
| `Framework/GetTransactionData.xaml` when customised — a table row, a file, a screen list instead of the queue item | Mode `direct` and its source; the once-per-run read | The shipped queue fetch is plumbing |
| `Framework/SetTransactionStatus.xaml` when customised — write-back to a column, a file, a reporting queue | Traceability line of the Transactional Shape | The shipped three status updates are plumbing |
| `Framework/CloseAllApplications.xaml`, `Framework/KillAllProcesses.xaml` | At-the-end steps; Error Handling § Global (forced close between retries) | |
| `Main.xaml` and its transitions, `InitAllSettings.xaml`, `RetryCurrentTransaction.xaml`, `TakeScreenshot.xaml`, the template's `Tests/`, `Exceptions_Screenshots/`, `Documentation/` | **Not steps.** Source Map row `Framework files` listing them; `Tests/` is test-coverage evidence | Execution recreates them from the template when the shape is applied |

A **dispatcher** is recognised the other way round: a plain project (Sequence or Flowchart root) whose loop reads a source and adds one queue item per row with a reference; the queue name — a literal or a configuration value — joins it to the performer that consumes it ([uipath-source-guide.md § Call Graph Rules](uipath-source-guide.md) rule 3). A REFramework project whose initialisation adds the items its own item fetch then takes from the same queue is both at once: its producer steps are the initialisation's reads and adds, its consumer is the rest of the framework, and the As-is is one process holding both roles over a queue — the shape Split option C keeps ([transactional-shape-guide.md](../shared/transactional-shape-guide.md) rule 3). A guard in that initialisation (a unique reference, a check that the day's items already exist) is the Coordination row's once-guard.

## Signals — Coded C#

| Signal | Pattern | Tells you |
|---|---|---|
| `[Workflow]` on a method | entry point of a coded workflow |
| `[TestCase]` on a method | test — evidence for acceptance criteria, not a component step |
| Service properties: `system.`, `excel.`, `mail.`, `office365.`, `uiAutomation.`, `testing.` | Which UiPath service, hence which application |
| `connections.<Connector>.<Connection>` | Integration Service connection; connector name in property chain |
| `workflows.<Name>(…)` | Call-graph edge to another workflow |
| `try` / `catch (<Type>)` / `finally`, `Polly`-style loops | Error handling |
| `if` / `switch` / `foreach` / `while` / LINQ `Where` | Business rules and iteration |
| Method signature and `.cs.json` `arguments[]` (`name`, `type`, `direction`) | Interface |
| `BuildClient("Orchestrator")`, `HttpClient` | Orchestrator API or external REST |
| `Descriptors.<Screen>.<Element>` | UI targets from Object Repository |

## Signals — Project settings

`.settings/<profile>/settings-<hash>.json`, one file per activity package; each key `<package>.<activity or group>.<property>` holds the project's value for that property. An activity that sets the property itself overrides it; every activity that leaves it unset takes it. Profiles: `Release` is the Run scenario (a published or unattended run), `Debug` applies when debugging from Studio, `Design` holds the values Studio writes into an activity or target when it is added — the workflow already carries them. Read `Release`, and `Debug` only where the source's behaviour is described for Studio runs.

| Setting group | Tells you | Genome |
|---|---|---|
| Input method per technology (web, Edge, desktop window, Java, SAP) | How each UI step without its own input method acts | The step, or one cross-cutting rule when most steps rely on it |
| Timeout, delays before and after, wait-for-ready, delay between keys, check-state timeout, hover and highlight time | Waits and budgets of steps that set none | Where they act ([genome-format-guide.md § Configuration Questions](../shared/genome-format-guide.md)) |
| Click before typing, field emptying, typing through the clipboard, post-action verification | How type and click steps behave | The steps they shape |
| Application scope open, close, attach and resize modes, runtime browser, browser user data folder | How application scopes start and end | The scope steps |
| Browser dialog handling (dismiss alerts, confirms, prompts; default answers) | What happens to a dialog no step answers | Error Handling, or the step that opens the page |
| Model per semantic or agent activity, iteration limit, trace settings | Which model and budget each AI step uses | A Configuration Question, since the tenant decides which models exist |
| Service endpoints and keys (OCR, AI services) | An external service the project calls | Target Applications; the key is a secret, never copied — a Credential asset per [genome-format-guide.md § Platform Dependencies](../shared/genome-format-guide.md) |

## Signals — Test projects

`designOptions.outputType: Tests` in `project.json` (`ProjectType: Tests` in `project.uiproj`), or test cases registered in a process project.

| Signal | Where | Tells you |
|---|---|---|
| `designOptions.fileInfoCollection[]` entries with `testCaseType: TestCase` — `fileName`, `testCaseId`, `executionTemplatePath`, `executionTemplateInvokeIsolated`, `dataVariationFilePath` | `project.json` | The test cases a test run starts, one entry point each, identified by `testCaseId` ([uipath-source-guide.md § Provenance](uipath-source-guide.md)); a file carrying `[TestCase]` with no entry is never started — dead code |
| Execution template: a workflow holding a placeholder activity, named by the entries' `executionTemplatePath` | `.templates/*.xaml` | Steps each case whose entry names it runs around its own — preparation, finalization, a timeout, a skip — written once in the shared component, never per case; an entry naming no template runs its case bare |
| A skip or filter deciding by the case's name, folder, machine or Orchestrator folder | the template or a helper it calls | Where each case runs: replay the rule over every registered case and state the outcome per group of cases; the folder then carries behaviour, and a rebuild that moves a case changes where it runs |
| Verification activities (Verify Expression, Verify Control Attribute, …), `testing.Verify…` calls, xUnit `Assert` in coded cases, a throw under a condition | case bodies, helpers | Checkpoints: what is asserted, the operator and the expected literal |
| Attach Document, `testing.AttachDocument`, screenshot activities | case bodies, template | Evidence policy (extraction's Step 3) |
| Data variations | `.variations/` | [uipath-source-guide.md § Test Data](uipath-source-guide.md) |
