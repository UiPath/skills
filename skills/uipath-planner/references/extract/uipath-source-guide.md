# UiPath Source Guide

Read this guide whole, and every § Signals section of the two files below, except a § Signals section whose artifact type is absent from the inventory:

| Artifact types (§ Inventory and Exclusions) | § Signals sections | File |
|---|---|---|
| XAML, coded C# workflows, project activity defaults, test projects | Signals — XAML (with REFramework projects), Coded C#, Project settings, Test projects | [uipath-rpa-signals-guide.md](uipath-rpa-signals-guide.md) |
| Flow, BPMN, Case, low-code agent, coded agent, API workflow, coded function, coded app | Signals — Flow, BPMN, Case, Low-code Agent, Coded Agent, API Workflow, Coded Function, Coded App | [uipath-non-rpa-signals-guide.md](uipath-non-rpa-signals-guide.md) |

## Reading the Project

A UiPath project is its own raw form. No inventory script renders it: extraction reads the files, and a suspected source defect is verified in one pass — the cited workflow re-read in full with its disabled activities, both directions of its argument bindings and the workflow it invokes (extraction's defect verification). Read in this order:

1. **Manifest** — `project.json` (fields: [uipath-rpa-signals-guide.md § Signals — XAML](uipath-rpa-signals-guide.md); test registrations: [uipath-rpa-signals-guide.md § Signals — Test projects](uipath-rpa-signals-guide.md)), or the solution's `.uipx` (§ Detection) and each project's manifest.
2. **Inventory** with Glob per § Inventory and Exclusions — files per folder and per artifact type, the counts § Provenance names.
3. **Project activity defaults** in `.settings/` ([uipath-rpa-signals-guide.md § Signals — Project settings](uipath-rpa-signals-guide.md)), before any workflow: they decide every property a workflow leaves unset.
4. **Every workflow in full** — `.xaml`, `.cs` with its `.cs.json`. Designer data fills up to half of an older project's XAML, and an Integration Service connector activity carries its connector's cached object schema — every field of the object with its search operators and picklist values — which can fill nine tenths of a connector-heavy file. Read the files through this filter, which drops view state, namespace and assembly lists, layout sizes, the cached schemas and the compressed design configuration only, keeping every activity, property, annotation, `IdRef`, `xmlns`, expression and every field the activity sets (a field it sets carries a child value element, so its line is never a self-closed one):

   ```bash
   sed -e '/<TextExpression.NamespacesForImplementation>.*<\/TextExpression.NamespacesForImplementation>/d; /<TextExpression.NamespacesForImplementation>/,/<\/TextExpression.NamespacesForImplementation>/d' \
       -e '/<TextExpression.ReferencesForImplementation>.*<\/TextExpression.ReferencesForImplementation>/d; /<TextExpression.ReferencesForImplementation>/,/<\/TextExpression.ReferencesForImplementation>/d' \
       -e '/<sap:WorkflowViewStateService.ViewState>.*<\/sap:WorkflowViewStateService.ViewState>/d; /<sap:WorkflowViewStateService.ViewState>/,/<\/sap:WorkflowViewStateService.ViewState>/d' \
       -e '/<sap2010:WorkflowViewState.ViewStateManager>.*<\/sap2010:WorkflowViewState.ViewStateManager>/d; /<sap2010:WorkflowViewState.ViewStateManager>/,/<\/sap2010:WorkflowViewState.ViewStateManager>/d' \
       -e '/<uibi:BusinessEntity.SearchableFields>.*<\/uibi:BusinessEntity.SearchableFields>/d; /<uibi:BusinessEntity.SearchableFields>/,/<\/uibi:BusinessEntity.SearchableFields>/d' \
       -e '/<uibi:BusinessEntity.EntityMetadata>.*<\/uibi:BusinessEntity.EntityMetadata>/d; /<uibi:BusinessEntity.EntityMetadata>/,/<\/uibi:BusinessEntity.EntityMetadata>/d' \
       -e '/<uiisi:OperationEntityField.EnumValues>.*<\/uiisi:OperationEntityField.EnumValues>/d; /<uiisi:OperationEntityField.EnumValues>/,/<\/uiisi:OperationEntityField.EnumValues>/d' \
       -e '/^ *<uiisi:OperationEntityField [^>]*\/> *$/d' \
       -e 's/ Configuration="H4sI[^"]*"/ Configuration="(compressed)"/g' \
       -e 's/ sap:VirtualizedContainerService.HintSize="[^"]*"//g' "<XAML_FILE>"
   ```

   A generic connector activity (`isactr:ConnectorActivity`) names its connector, object, operation, path and page size only inside that compressed configuration (base64 of gzip JSON). Print them, one line per activity in file order, leaving out the schema it also holds:

   ```bash
   node -e "const fs=require('fs'),zlib=require('zlib');for(const m of fs.readFileSync(process.argv[1],'utf8').matchAll(/Configuration=\"(H4sI[^\"]+)\"/g)){const c=JSON.parse(zlib.gunzipSync(Buffer.from(m[1],'base64')));delete c.FieldsContainer;console.log(JSON.stringify(c))}" "<XAML_FILE>"
   ```

5. **Object Repository** by its node files, never its descriptors: every node folder under `.objects/` holds `.type` (`Library`, `App`, `AppVersion`, `Screen`, `Element`) and `.metadata` (JSON: `Name`, `Id`, `Reference`) — application, screen and element names for Target Applications, counts for the Source Map.
6. **Deployed state**, when the user gave its folder or an export of it, or the bindings name a folder of the signed-in tenant (§ Deployed State).

## Detection

| Signal | Meaning |
|---|---|
| `<Name>.uipx` in the root (JSON with `Projects[]`) | UiPath **solution** — multi-component. Process genome. Component list: `Projects[].Type` and `Projects[].ProjectRelativePath`. |
| Several sibling folders each with `project.json` / `project.uiproj` and no `.uipx` | Loose multi-project bundle — treat as a solution; flag `*[Inferred]*` in Deployment. |
| Single `project.json` (RPA) or `project.uiproj` (Flow, BPMN, Case, Api, Agent, AppV2) | One **component**. Component genome — except a test project holding several test-case groups (§ Component Detection). |
| Only `.xaml` / `.cs` files, no manifest | RPA project with missing metadata — extract, flag name and settings `*[Inferred]*`. |
| `pyproject.toml` with `langgraph.json` / `llama_index.json` / `openai_agents.json` | Coded Python agent component. |
| `uipath.json` with a `functions` map | Coded Function component (Python if `pyproject.toml`, JS/TS if `package.json`). |
| `package.json` depending on `@uipath/uipath-typescript` or `@uipath/coded-action-app`, plus `webAppManifest.json` or `.uipath/app.config.json` | Coded app component. |

`.uipx` fields: `Projects[].{Id, Type, ProjectRelativePath}`, `SolutionId`, `StudioMinVersion`, `AutomationHubIdeaUrl`. `resources/solution_folder/**` mirrors `Projects[]`, generated — never read for logic.

## Inventory and Exclusions

| Pattern | Artifact type | Signals section |
|---|---|---|
| `*.xaml` | XAML workflow | [uipath-rpa-signals-guide.md § Signals — XAML](uipath-rpa-signals-guide.md) |
| `*.cs` with `[Workflow]` / `[TestCase]` | Coded workflow | [uipath-rpa-signals-guide.md § Signals — Coded C#](uipath-rpa-signals-guide.md) |
| `*.cs.json` | Coded workflow argument metadata | read with the `.cs` |
| `*.flow` | Maestro Flow | [uipath-non-rpa-signals-guide.md § Signals — Flow](uipath-non-rpa-signals-guide.md) |
| `*.bpmn` | Maestro BPMN process | [uipath-non-rpa-signals-guide.md § Signals — BPMN](uipath-non-rpa-signals-guide.md) |
| `caseplan.case` / `caseplan.json` | Maestro Case plan | [uipath-non-rpa-signals-guide.md § Signals — Case](uipath-non-rpa-signals-guide.md) |
| `agent.json` (`"type": "lowCode"`) + `resources/*/resource.json` | Low-code agent | [uipath-non-rpa-signals-guide.md § Signals — Low-code Agent](uipath-non-rpa-signals-guide.md) |
| `langgraph.json` / `llama_index.json` / `openai_agents.json` + `*.py` | Coded agent | [uipath-non-rpa-signals-guide.md § Signals — Coded Agent](uipath-non-rpa-signals-guide.md) |
| `Workflow.json` (`document.dsl`) | API workflow | [uipath-non-rpa-signals-guide.md § Signals — API Workflow](uipath-non-rpa-signals-guide.md) |
| `uipath.json` `functions` map + `*.py` or `functions/*.ts` | Coded Function | [uipath-non-rpa-signals-guide.md § Signals — Coded Function](uipath-non-rpa-signals-guide.md) |
| `webAppManifest.json`, `action-schema.json`, `src/**/*.ts(x)` | Coded app | [uipath-non-rpa-signals-guide.md § Signals — Coded App](uipath-non-rpa-signals-guide.md) |
| `bindings_v2.json`, `entry-points.json`, `project.json` `dependencies` | Platform resources and interfaces | § Platform Resources |
| `.objects/**` (Object Repository) | Application, screen, and element **names** only — never selectors | read for Target Applications and Source Map notes (§ Reading the Project) |
| `.settings/<profile>/settings-*.json` | Project activity defaults | [uipath-rpa-signals-guide.md § Signals — Project settings](uipath-rpa-signals-guide.md) |
| `.templates/*.xaml`, `designOptions.fileInfoCollection[]` in `project.json` | Test execution template, test-case registrations | [uipath-rpa-signals-guide.md § Signals — Test projects](uipath-rpa-signals-guide.md) |
| `AGENTS.md`, `README.md`, `.claude/rules/project-context.md` | Author-written intent, known gotchas, run instructions | evidence for Overview and Error Handling; verify every claim against code before use |

Skip entirely: `.local/`, `.codedworkflows/`, `.storage/` (UI Automation's target-image and ancestry caches), `.tmh/`, `.screenshots/`, `.project/`, `node_modules/`, `dist/`, `source/dist/`, `.venv/`, `__pycache__/`, `resources/solution_folder/`, `userProfile/`, `.git/`, `.app/` (generated trigger XAML), `*.Generated.xaml`.

Generated boilerplate, never a source of logic: `CodedWorkflow.cs`, `ConnectionsManager.cs`, `ConnectionsFactory.cs`, `ObjectRepository.cs`, `WorkflowRunnerService.cs`, `Triggers.Generated.xaml`, `AppsRequestTrigger.xaml`.

## Component Detection

| Marker | Component Type | Skill | Rationale |
|---|---|---|---|
| `project.json` with `.xaml` and/or `[Workflow]` `.cs` (`.uipx` Type `Process`, `Library`, `Test`) | RPA process / library | `uipath-rpa` | Owns both XAML and coded workflows |
| `project.uiproj` + `.flow` (`.uipx` Type `Flow`) | Flow | `uipath-maestro-flow` | |
| `project.uiproj` + `.bpmn` (`.uipx` Type `ProcessOrchestration`) | BPMN process | `uipath-maestro-bpmn` | |
| `caseplan.case` / `caseplan.json` | Case plan | `uipath-maestro-case` | |
| `agent.json` lowCode (`.uipx` Type `Agent`) | Low-code agent | `uipath-agents` | |
| `pyproject.toml` + framework json | Coded agent | `uipath-agents` | |
| `Workflow.json` (`.uipx` Type `Api`) | API workflow | `uipath-api-workflow` | |
| `uipath.json` `functions` map | Coded Function | `uipath-functions` | |
| `project.uiproj` `ProjectType: "AppV2"` or standalone coded app markers | Coded app (Web or Action per `webAppManifest.json` `config.isActionApp`) | `uipath-coded-apps` | |
| `element.json` + `element-metadata.json` | Custom connector | `uipath-connector-builder` | |

The project folder is the part of a workflow's path the project stands for; the rest, the project-relative path the step table's Source objects cell carries (§ Provenance), is the workflow's path in the rebuild.

A test project (`.uipx` Type `Test`, `[TestCase]`-only `.cs`, `designOptions.outputType: Tests`) beside the projects it tests is evidence, not a component: record "test coverage present" in the Source Map and use its assertions as acceptance-criteria evidence. When the source holds only test projects, the suite is what the genome documents: its test-case groups are test components, and its execution template with the helpers the cases share is one shared component of the same project ([genome-format-guide.md § Two Levels](../shared/genome-format-guide.md) rule 1; signals: [uipath-rpa-signals-guide.md § Signals — Test projects](uipath-rpa-signals-guide.md)).

## Target Resolution

1. **XAML activity → application:** resolve from `xmlns` namespace (`UiPath.MicrosoftOffice365.Activities.Mail` → Outlook / Office 365; `UiPath.GSuite.Activities` → Gmail / Google Workspace; `UiPath.Excel.Activities` → Excel; `UiPath.Database.Activities` → database named in connection string; `UiPath.UIAutomation.Activities` → application named in target's `DisplayName` or Object Repository screen; `UiPath.PDF.Activities` / `UiPath.IntelligentOCR.Activities` / `UiPath.DocumentUnderstanding.*` → Document Understanding; `UiPath.Persistence.Activities` → Action Center; `UiPath.Web.Activities` → REST endpoint host).
2. **Connector key → service:** `uipath-salesforce-sfdc` → Salesforce; `uipath-microsoft-outlook365` → Outlook; `uipath-atlassian-jira` → Jira; `uipath-servicenow` → ServiceNow; `uipath-slack` → Slack. Key not listed: strip `uipath-` prefix, use vendor name.
3. **`ConnectionId` GUID alone** → look up `bindings_v2.json` `resources[resource=connection].metadata.connector`; if absent, activity's namespace decides; if still unknown, write "Integration Service connector *[Inferred]*" in Source Map notes and best-guess service in body.
4. **Process / release references** (`releaseKey`, `processName`, `resourceKey`, `referenceKey`) → component with matching project name in same solution; otherwise external dependency listed in Platform Dependencies as `Deployed process: <name>`.
5. **Orchestrator folders** → Platform Dependencies row's Notes; never a Target Application.

## Call Graph Rules

1. Entry point: `project.json` `main` (RPA), `entryPoints[]` for multi-entry processes; `.flow` trigger node with `isDefaultEntryPoint`; BPMN `startEvent`; Case trigger node; `langgraph.json` graph; `Workflow.json` root `do[]`; `uipath.json` `functions`.
2. Edges inside a component: `<InvokeWorkflowFile FileName>`, `workflows.<Name>()` (`<Name>` is the workflow's file name without extension, whatever its class is called), `core.subflow`, BPMN `callActivity`, Case sub-stages. Depth-first from entry point; order siblings top-to-bottom (Sequence), left-to-right (Flowchart), by `edges[]` order (Flow), by `sequenceFlow` order (BPMN).
3. Edges across components (handoffs): Flow resource nodes, BPMN `uipath:type` values that start a job or agent, Case task types `process` / `rpa` / `agent` / `api-workflow` / `action`, agent tools with `type` `process` / `api` / `agent`, `sdk.processes.invoke`, `StartJob` activities, queue producers and consumers sharing a queue name, Action Center task creation and the coded app that renders it.
4. Missing entry point: `outputType: Library` → each public workflow is an independent capability, listed as separate steps; `Process` without `main` → `Main.xaml` / `Main.cs` by convention, else alphabetical with `*[Inferred]*`.
5. Unreachable workflows are unused parts: steps or the Source Map's `Unused` row, as the Unused parts answer decides ([extract-guide.md](extract-guide.md) Step 1).
6. Test project: the execution template invokes every registered case through its placeholder, so its steps are shared steps of every case ([uipath-rpa-signals-guide.md § Signals — Test projects](uipath-rpa-signals-guide.md)). A workflow belongs to the component whose folder holds it; a call from another component's case is a cross-component edge, never a copy of the callee.
7. REFramework / StateMachine: the Workflow's call graph starts at the per-item process workflow and adds the once-per-run and at-the-end workflows as steps of their own ([uipath-rpa-signals-guide.md § Signals — XAML › REFramework projects](uipath-rpa-signals-guide.md)); the state machine, its transitions and the framework's retry and status workflows are not steps. The queue is a Platform Dependency; the business/system outcome classification and the counts go to the Transactional Shape ([transactional-shape-guide.md](../shared/transactional-shape-guide.md)).

## Expression Translation

Check `project.json` `expressionLanguage` before reading XAML. VisualBasic: `AndAlso` / `OrElse` / `&` / `=` / `<>` / `Not`. CSharp: `&&` / `||` / `+` / `==` / `!=` / `!`. Flow, BPMN, and API workflow expressions are JavaScript (`===`, `&&`, `||`, `?.`); BPMN predicates are `=`-prefixed. Case conditions are `=js:` prefixed. Translate all with the table in [genome-format-guide.md § Business Rules](../shared/genome-format-guide.md). `DateTime.Now.AddDays(-30)` style arithmetic → "more than 30 days old". String concatenation → describe resulting text. The text is what sits inside the quotes: in `"exists for "  + name` the second space stands between the closing quote and the operator, so it is code, and the logged text has one space.

## Platform Resources

| Where | Resource rows |
|---|---|
| `bindings_v2.json` `resources[]` (`resource`: `process`, `queue`, `asset`, `bucket`, `connection`, `app`, `index`, `mcpServer`, `Entity`; `key`; `value.*.defaultValue`; `metadata.connector`) | One Platform Dependencies row each, default name and folder as source value |
| `bindings.json` (coded agents) | Same mapping |
| `.flow` top-level `bindings[]` | Processes, agents, API workflows invoked; folders |
| XAML queue / asset / credential / bucket / StartJob activities; `.cs` `system.` calls | Queues, assets, credentials, buckets, jobs |
| `project.json` `dependencies` that are libraries (packages published from another automation project, not activity packages); feeds in the project's `NuGet.config` | One row per library: package, version, feed. Steps describe the library workflows they call by behaviour, from their arguments; a library's bodies are read only when its project is given as a related resource |
| Assets a REFramework configuration lists | One Platform Dependencies row per asset name; Credential when the configuration's description or the consuming activity says so, otherwise Text |
| BPMN `<uipath:context>` inputs (`folderPath`, `releaseKey`, `appId`, `connection`) | Processes, HITL apps, connections |
| `entry-points.json` | Interface inputs and outputs per component |
| Triggers: `.flow` scheduled/connector trigger nodes, BPMN start event types, Case trigger `serviceType`, `bindings_v2.json` `HttpTrigger` | Deployment → Entry points and triggers |

## Deployed State

A package runs as Orchestrator processes, and what runs is the process: each binds one package version, can override any binding of the package, and owns its triggers. When the user names the folder that runs it — or the package's bindings name it and this session is signed in to that tenant, which a refactor or migration needs, since what runs decides the split — read it with `uipath-platform`'s read commands — or, without that skill, the read-only `uip or processes list|get`, `uip or triggers list`, `uip or queues list|get` and `uip or assets list` with `--output json` — each process record with all its fields (its binding overrides are among them), the triggers, the assets and queues the workflows name, the job history, the other processes sharing them — and write nothing; an export of those records the user gives is read the same way.

| Read | Tells you | Genome |
|---|---|---|
| Processes per package: entry point, package version, runtime, job priority | which entry points run, and where; two processes of one package bound to different versions run different code | Deployment; a version difference is a Source Map row naming the files that differ, and each process's steps are described from the version it runs |
| Binding overrides of each process | the connection, folder, file, queue or asset each binding resolves to at run time — one package binding can resolve differently in two processes | the override is the value that runs: an environment-bound value's default is the override, the package's value goes to the Source Map |
| The connection behind each binding: connector, the account it signs in as, its folder | the identity every read and write runs as; a connection's name in the XAML is its name at design time | Platform Dependencies, identity in the purpose; a person's account is a Source Map finding |
| Triggers: type, schedule and time zone, queue and its job limits, event (connector, object, event, filter) | how each entry point starts | Workflow step 1, Deployment. An event trigger is read here and never inferred from the entry point's event arguments, which show only that an event starts it |
| Assets the workflows read, the queues' settings | values (never a credential's secret); unique reference, retries, retention | Configuration Question defaults; the Transactional Shape's As-is |
| Job history of a window: runs, faults grouped by message and step, durations, items per run | whether an entry point is used, its volumes, what a fault does on real data | the Source Map's runtime row; a consequence the history shows is a fact, not `*[Inferred]*` |
| The other processes of the folder and of each folder a binding resolves to: their declared resources, their triggers, and their packages' workflows when the declared resources leave a name blank or the package declares none | who else adds items to each queue the component uses or reads them, starts it or is started by it, and uses its assets, buckets and connections; a name another package builds from an expression is unresolved, never matched to one | each Platform Dependencies row names the processes sharing it and how; the processes read and the unresolved names go to the Source Map's deployed-state row |

Without the deployed state, Platform Dependencies and Deployment come from the package, a trigger the package does not hold is `*[Inferred]*`, and the Source Map's deployed-state row says it was not read.

## Test Data

| Where | What | Data catalog derived at execution |
|---|---|---|
| `.variations/*.json`, registered in `project.json` → `designOptions.fileInfoCollection[].dataVariationFilePath` | data rows per test case, keyed by argument name | one recordset per file, rows as-is; process inventory maps test case → file |
| Test Data Queues (`test-data add-queue` argument named after the queue), Data Service entities | external data sources | Platform Dependencies rows (queue, entity), not rows in artifact |
| `GetRobotCredential` / `GetRobotAsset` asset names, `GetCredential` | credentials and configuration already in Orchestrator | keep asset names ([genome-format-guide.md § Platform Dependencies](../shared/genome-format-guide.md)); no secret present in source, none written |
| Default values on test-case arguments (`this:<Class>.<Arg>` root attributes) | single-row data | recordset's only row |

Variation row holding a password-looking field (`*password*`, `*pwd*`, `*secret*`, `*token*`) is redacted and reported; field is expected to become a credential asset name.

## Provenance

What the Source Map rows of [extracted-genome-guide.md § Source Map](../shared/extracted-genome-guide.md) carry for a UiPath source:

| Identity of | Carried as |
|---|---|
| The source | Project path, `projectId`, `projectVersion`; a solution's `.uipx` `SolutionId` with each project's `projectId`; the repository commit when the project sits in one |
| A workflow step | The workflow's project-relative path — unique in a project; a solution prefixes the project folder: `` `Folder/Workflow.xaml` `` in the step table's Source objects cell |
| A test case | Its path plus `testCaseId`, `` `Tests/Case.xaml` (<testCaseId>) ``; a checkpoint inside it by its activity `IdRef` |
| A step's data set | The data variation file's project-relative path, `` `.variations/<Case>.json` ``, in the step table's Data sets cell |
| Inventory | Workflows per artifact type, test cases, data files and rows, Object Repository applications, screens and elements, accounts |
| Deployed state | The folder and the date read; per process its package version, runtime and triggers, and each binding override with the package value it replaces; the other processes read, and each name another package builds from an expression; or "not read" (§ Deployed State) |
| Runtime | The job-history window: per process the runs, the faults grouped by message and step, the durations; an entry point with no run named |

No inventory script derives a process inventory or a recordset list, so a UiPath source gets no mechanical export check, and extraction's Step 6b file-search check takes its place.

## Framework Pitfalls

1. Designer view state and `HintSize` attributes look like content and are layout only (§ Reading the Project).
2. `xmlns` declarations are package imports, not steps. Many are declared and unused.
3. Flow resource-node instances carry no `model`; the resource is in `definitions[]` and `bindings[]`.
4. BPMN `uipath:type` decides what a task does; the BPMN element name (`serviceTask`) is only a hint.
5. Low-code agent tools are files under `resources/`, not an array in `agent.json`.
6. API workflow HTTP tasks: the real verb and URL are in `with.bodyParameters`, not the outer `with`.
7. `bindings.json` and `bindings_v2.json` are different files with different consumers; a coded agent may have both.
8. `.app/` and `*.Generated.xaml` are generated trigger plumbing for apps and Action Center — skip.
9. `resources/solution_folder/**` mirrors the manifest and is regenerated; read `.uipx` instead.
10. A `[TestCase]` `.cs` file or `Test` project beside the projects it tests is evidence, not a component (§ Component Detection).
11. The REFramework template's sample values survive customisation: `ProcessABCQueue` in the settings sheet of a project whose item fetch reads rows, the template's own `Tests/` cases, `Exceptions_Screenshots/`. A queue is evidence only when the item fetch actually reads it ([uipath-rpa-signals-guide.md § Signals — XAML › REFramework projects](uipath-rpa-signals-guide.md)).
12. Framework workflows look like logic and are the template: the state machine, the retry counter, the three status updates and the screenshot on exception describe the Transactional Shape, not steps — transcribing them doubles the shape in the genome.
13. A `DisplayName` is a hint the author may have copied with the activity: a branch named after a sibling's test ("check if vendor form" on a test of another field) describes the sibling. The condition decides what the step does, and a container with no `DisplayName` (an `If` around a whole file) can hold its structure — a search by names misses it, a full read does not.
14. The connection and folder names a connector activity shows are the ones it was designed with. The deployed process's overrides decide what runs (§ Deployed State).
