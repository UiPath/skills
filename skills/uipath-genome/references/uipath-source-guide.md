# UiPath Source Guide

Read § Reading the Project through § Component Detection, § Call Graph Rules, § Platform Resources, § Provenance and § Framework Pitfalls in full. Read a § Signals section only for artifact types present in the inventory.

## Reading the Project

A UiPath project is its own raw form. No inventory script renders it: extraction reads the files, and a suspected source defect is verified in one pass — the cited workflow re-read in full with its disabled activities, both directions of its argument bindings and the workflow it invokes ([extraction-guide.md](extraction-guide.md) Step 4b). Read in this order:

1. **Manifest** — `project.json` (fields: § Signals — XAML; test registrations: § Signals — Test projects), or the solution's `.uipx` (§ Detection) and each project's manifest.
2. **Inventory** with Glob per § Inventory and Exclusions — files per folder and per artifact type, the counts § Provenance names.
3. **Project activity defaults** in `.settings/` (§ Signals — Project settings), before any workflow: they decide every property a workflow leaves unset.
4. **Every workflow in full** — `.xaml`, `.cs` with its `.cs.json`. Designer data fills up to half of an older project's XAML. A large corpus may be read through this filter, which drops view state, namespace and assembly lists and layout sizes only, keeping every activity, property, annotation, `IdRef` and `xmlns`:

   ```bash
   sed -e '/<TextExpression.NamespacesForImplementation>/,/<\/TextExpression.NamespacesForImplementation>/d' \
       -e '/<TextExpression.ReferencesForImplementation>/,/<\/TextExpression.ReferencesForImplementation>/d' \
       -e '/<sap:WorkflowViewStateService.ViewState>/,/<\/sap:WorkflowViewStateService.ViewState>/d' \
       -e '/<sap2010:WorkflowViewState.ViewStateManager>/,/<\/sap2010:WorkflowViewState.ViewStateManager>/d' \
       -e 's/ sap:VirtualizedContainerService.HintSize="[^"]*"//g' "<XAML_FILE>"
   ```

5. **Object Repository** by its node files, never its descriptors: every node folder under `.objects/` holds `.type` (`Library`, `App`, `AppVersion`, `Screen`, `Element`) and `.metadata` (JSON: `Name`, `Id`, `Reference`) — application, screen and element names for Target Applications, counts for the Source Map.

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
| `*.xaml` | XAML workflow | § Signals — XAML |
| `*.cs` with `[Workflow]` / `[TestCase]` | Coded workflow | § Signals — Coded C# |
| `*.cs.json` | Coded workflow argument metadata | read with the `.cs` |
| `*.flow` | Maestro Flow | § Signals — Flow |
| `*.bpmn` | Maestro BPMN process | § Signals — BPMN |
| `caseplan.json` | Maestro Case plan | § Signals — Case |
| `agent.json` (`"type": "lowCode"`) + `resources/*/resource.json` | Low-code agent | § Signals — Low-code Agent |
| `langgraph.json` / `llama_index.json` / `openai_agents.json` + `*.py` | Coded agent | § Signals — Coded Agent |
| `Workflow.json` (`document.dsl`) | API workflow | § Signals — API Workflow |
| `uipath.json` `functions` map + `*.py` or `functions/*.ts` | Coded Function | § Signals — Coded Function |
| `webAppManifest.json`, `action-schema.json`, `src/**/*.ts(x)` | Coded app | § Signals — Coded App |
| `bindings_v2.json`, `entry-points.json`, `project.json` `dependencies` | Platform resources and interfaces | § Platform Resources |
| `.objects/**` (Object Repository) | Application, screen, and element **names** only — never selectors | read for Target Applications and Source Map notes (§ Reading the Project) |
| `.settings/<profile>/settings-*.json` | Project activity defaults | § Signals — Project settings |
| `.templates/*.xaml`, `designOptions.fileInfoCollection[]` in `project.json` | Test execution template, test-case registrations | § Signals — Test projects |
| `AGENTS.md`, `README.md`, `.claude/rules/project-context.md` | Author-written intent, known gotchas, run instructions | evidence for Overview and Error Handling; verify every claim against code before use |

Skip entirely: `.local/`, `.codedworkflows/`, `.storage/` (UI Automation's target-image and ancestry caches), `.tmh/`, `.screenshots/`, `.project/`, `node_modules/`, `dist/`, `source/dist/`, `.venv/`, `__pycache__/`, `resources/solution_folder/`, `userProfile/`, `.git/`, `.app/` (generated trigger XAML), `*.Generated.xaml`.

Generated boilerplate, never a source of logic: `CodedWorkflow.cs`, `ConnectionsManager.cs`, `ConnectionsFactory.cs`, `ObjectRepository.cs`, `WorkflowRunnerService.cs`, `Triggers.Generated.xaml`, `AppsRequestTrigger.xaml`.

## Component Detection

| Marker | Component Type | Skill | Rationale |
|---|---|---|---|
| `project.json` with `.xaml` and/or `[Workflow]` `.cs` (`.uipx` Type `Process`, `Library`, `Test`) | RPA process / library | `uipath-rpa` | Owns both XAML and coded workflows |
| `project.uiproj` + `.flow` (`.uipx` Type `Flow`) | Flow | `uipath-maestro-flow` | |
| `project.uiproj` + `.bpmn` (`.uipx` Type `ProcessOrchestration`) | BPMN process | `uipath-maestro-bpmn` | |
| `caseplan.json` | Case plan | `uipath-maestro-case` | |
| `agent.json` lowCode (`.uipx` Type `Agent`) | Low-code agent | `uipath-agents` | |
| `pyproject.toml` + framework json | Coded agent | `uipath-agents` | |
| `Workflow.json` (`.uipx` Type `Api`) | API workflow | `uipath-api-workflow` | |
| `uipath.json` `functions` map | Coded Function | `uipath-functions` | |
| `project.uiproj` `ProjectType: "AppV2"` or standalone coded app markers | Coded app (Web or Action per `webAppManifest.json` `config.isActionApp`) | `uipath-coded-apps` | |
| `element.json` + `element-metadata.json` | Custom connector | `uipath-connector-builder` | |

A test project (`.uipx` Type `Test`, `[TestCase]`-only `.cs`, `designOptions.outputType: Tests`) beside the projects it tests is evidence, not a component: record "test coverage present" in the Source Map and use its assertions as acceptance-criteria evidence. When the source holds only test projects, the suite is what the genome documents: its test-case groups are test components, and its execution template with the helpers the cases share is one shared component of the same project ([genome-format-guide.md § Two Levels](genome-format-guide.md) rule 1; signals: § Signals — Test projects).

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

Designer view state and layout sizes are not logic (§ Reading the Project).

### REFramework projects

A project built on the Robotic Enterprise Framework template is recognised by its shape, not by a manifest flag: `Main.xaml` is a `<StateMachine>` whose states are Init, Get Transaction Data, Process Transaction and End Process; a `Framework/` folder holds the framework workflows; `Data/Config.xlsx` has the sheets Settings, Constants and Assets. The framework **is** the Transactional Shape ([genome-format-guide.md § Transactional Shape](genome-format-guide.md)); the business logic is the Workflow. Which file feeds which row:

| Source | Feeds | How |
|---|---|---|
| `Data/Config.xlsx` Settings sheet: `OrchestratorQueueName`, `OrchestratorQueueFolder` | Transactional Shape As-is item store; Platform Dependencies (queue) | A queue name that the item-fetch workflow actually reads → `queue` mode, name kept as the source value. Blank, or the template's sample `ProcessABCQueue` beside a customised item fetch → `direct` mode, data source from that fetch |
| Settings and Constants rows — `MaxRetryNumber`, `MaxConsecutiveSystemExceptions`, and every custom row (URLs, paths, thresholds) | Sorted per [genome-format-guide.md § Configuration Questions](genome-format-guide.md): an environment row (URL, path, mailbox, folder) is a Configuration Question with the sheet value as default; the two counts go in the outcomes table; every other row goes in the step or rule that uses it | `logF_BusinessProcessName`, `TransactionNumber`, `RetryNumberGetTransactionItem`, `RetryNumberSetTransactionStatus` are framework plumbing — no question |
| Assets sheet rows | Platform Dependencies | One row per asset name; Credential when the description or the consuming activity says so, otherwise Text |
| `Framework/InitAllApplications.xaml` (`GetAppCredentials.xaml` in older templates) | Once-per-run steps; credential assets | Open and sign-in per application |
| `Framework/Process.xaml` (root `Process.xaml` in older templates) and every workflow it invokes | Per-item steps — the Workflow's numbered steps | The call graph starts here, not at `Main.xaml` |
| `Throw` of a `BusinessRuleException` inside the per-item workflows | Business Rules (the condition) and the business-exception row of the outcomes table | The exception message is the reason wording |
| `Framework/GetTransactionData.xaml` when customised — a table row, a file, a screen list instead of the queue item | Mode `direct` and its source; the once-per-run read | The shipped queue fetch is plumbing |
| `Framework/SetTransactionStatus.xaml` when customised — write-back to a column, a file, a reporting queue | Traceability line of the Transactional Shape | The shipped three status updates are plumbing |
| `Framework/CloseAllApplications.xaml`, `Framework/KillAllProcesses.xaml` | At-the-end steps; Error Handling § Global (forced close between retries) | |
| `Main.xaml` and its transitions, `InitAllSettings.xaml`, `RetryCurrentTransaction.xaml`, `TakeScreenshot.xaml`, the template's `Tests/`, `Exceptions_Screenshots/`, `Documentation/` | **Not steps.** Source Map row `Framework files` listing them; `Tests/` is test-coverage evidence | Execution recreates them from the template when the shape is applied |

A **dispatcher** is recognised the other way round: a plain project (Sequence or Flowchart root) whose loop reads a source and adds one queue item per row with a reference; the queue name — a literal or a configuration value — joins it to the performer that consumes it (§ Call Graph Rules rule 3). A REFramework project whose initialisation adds the items its own item fetch then takes from the same queue is both at once: its producer steps are the initialisation's reads and adds, its consumer is the rest of the framework, and the As-is is one process holding both roles over a queue — the shape Split option C keeps ([genome-format-guide.md § Transactional Shape](genome-format-guide.md) rule 3). A guard in that initialisation (a unique reference, a check that the day's items already exist) is the Coordination row's once-guard.

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
| Timeout, delays before and after, wait-for-ready, delay between keys, check-state timeout, hover and highlight time | Waits and budgets of steps that set none | Where they act ([genome-format-guide.md § Configuration Questions](genome-format-guide.md)) |
| Click before typing, field emptying, typing through the clipboard, post-action verification | How type and click steps behave | The steps they shape |
| Application scope open, close, attach and resize modes, runtime browser, browser user data folder | How application scopes start and end | The scope steps |
| Browser dialog handling (dismiss alerts, confirms, prompts; default answers) | What happens to a dialog no step answers | Error Handling, or the step that opens the page |
| Model per semantic or agent activity, iteration limit, trace settings | Which model and budget each AI step uses | A Configuration Question, since the tenant decides which models exist |
| Service endpoints and keys (OCR, AI services) | An external service the project calls | Target Applications; the key is a secret, never copied — a Credential asset per [genome-format-guide.md § Platform Dependencies](genome-format-guide.md) |

## Signals — Test projects

`designOptions.outputType: Tests` in `project.json` (`ProjectType: Tests` in `project.uiproj`), or test cases registered in a process project.

| Signal | Where | Tells you |
|---|---|---|
| `designOptions.fileInfoCollection[]` entries with `testCaseType: TestCase` — `fileName`, `testCaseId`, `executionTemplatePath`, `executionTemplateInvokeIsolated`, `dataVariationFilePath` | `project.json` | The test cases a test run starts, one entry point each, identified by `testCaseId` (§ Provenance); a file carrying `[TestCase]` with no entry is never started — dead code |
| Execution template: a workflow holding a placeholder activity, named by the entries' `executionTemplatePath` | `.templates/*.xaml` | Steps each case whose entry names it runs around its own — preparation, finalization, a timeout, a skip — written once in the shared component, never per case; an entry naming no template runs its case bare |
| A skip or filter deciding by the case's name, folder, machine or Orchestrator folder | the template or a helper it calls | Where each case runs: replay the rule over every registered case and state the outcome per group of cases; the folder then carries behaviour, and a rebuild that moves a case changes where it runs |
| Verification activities (Verify Expression, Verify Control Attribute, …), `testing.Verify…` calls, xUnit `Assert` in coded cases, a throw under a condition | case bodies, helpers | Checkpoints: what is asserted, the operator and the expected literal |
| Attach Document, `testing.AttachDocument`, screenshot activities | case bodies, template | Evidence policy ([extraction-guide.md](extraction-guide.md) Step 3) |
| Data variations | `.variations/` | § Test Data |

## Signals — Flow

| Signal | Path | Tells you |
|---|---|---|
| Trigger node `type` | `nodes[].type`: `core.trigger.manual`, `core.trigger.scheduled` (`inputs.timerPreset`), `uipath.connector.trigger.*`, `core.trigger.voice` | How the flow starts |
| Resource node `type` | `uipath.core.rpa-workflow.<key>`, `uipath.core.agent.<key>`, `uipath.core.api-workflow.<key>`, `uipath.core.flow.<key>`, `uipath.core.agentic-process.<key>`, `uipath.core.human-task.<key>`, `core.subflow` | Component kind invoked — handoff edge in process genome |
| `definitions[].model.bindings.{resourceKey, resourceSubType, serviceType}` and top-level `bindings[]` (`name`, `folderPath`, `default`) | definitions / bindings | Concrete Orchestrator process, agent, or API workflow invoked |
| `core.logic.decision` (`inputs.expression`), `core.logic.switch` (`inputs.cases`), `core.logic.loop` (`inputs.collection`, `parallel`), `core.logic.merge` | nodes | Business rules and iteration |
| `uipath.human-in-the-loop.quick-form` (`inputs.schema.fields[]`, `outcomes[]`, `recipient`) | nodes | Inline approval — HITL checkpoint |
| `core.action.script` (`inputs.script`), `core.action.http.v2` (`method`, `url`, `branches`), `core.action.transform`, `core.action.queue.create[-and-wait]`, `core.datafabric.*`, `uipath.connector.*`, `uipath.ixp.*`, `uipath.agent.autonomous` | nodes | Embedded logic, HTTP targets, queue and Data Fabric use, connectors, inline agents |
| `core.logic.terminate` vs `core.control.end` (`outputs`) | nodes | Fatal abort vs normal completion and flow outputs |
| `edges[]` `{sourceNodeId, sourcePort, targetNodeId}`; ports `true`/`false`, `case-<id>`/`default`, `success`/`error`, `completed` | edges | Graph and branch semantics; `error` port is an error-handling path |
| `inputs.errorHandlingEnabled: true` | action node | Step has an error escape path |
| `variables.nodes[]` (`<nodeId>.<outputId>`) | top level | Data flow between nodes |

## Signals — BPMN

Confirm `xmlns:uipath="http://uipath.org/schema/bpmn"` on `<bpmn:definitions>`.

| Signal | Where | Tells you |
|---|---|---|
| `<uipath:variables>` → `<uipath:inputOutput id name type>` | process `extensionElements` | Process data schema |
| `<uipath:type value="…">` inside a task's `extensionElements` | `Orchestrator.StartJob` (RPA), `Orchestrator.StartAgentJob` (agent), `Orchestrator.ExecuteApiWorkflowAsync`, `Actions.HITL`, `Intsvc.ActivityExecution` (connector), `Intsvc.UnifiedHttpRequest`, `A2A.AgentExecution`, `Orchestrator.StartAgenticProcess`, `Orchestrator.StartCaseMgmtProcess`, `BPMN.ScriptTask` | What the step invokes — each a handoff edge to a component or external system |
| `<uipath:context>` → `<uipath:input name value>` | inside the activity | Bound resource: `releaseKey` / `folderPath` / `name`, `appId`, `connectorKey` / `connection` / `operation` |
| `<uipath:input target="bodyField">`, `<uipath:output var source>` | inside the activity | Argument mapping in and out |
| `bpmn:userTask` / `serviceTask` / `sendTask` / `receiveTask` / `scriptTask` / `businessRuleTask` / `callActivity` | process children | Coarse step class: user = HITL, service = job/agent/API, receive = wait for event, callActivity = another Maestro process |
| `bpmn:lane` / `laneSet` | process | Actors (human lanes) and system lanes → Actors and Systems |
| `startEvent` with `Intsvc.EventTrigger` / `Intsvc.TimerTrigger`; `endEvent` with `terminateEventDefinition` | process | Triggers and terminal outcomes |
| `exclusiveGateway default=`, `parallelGateway`, `inclusiveGateway`, `eventBasedGateway` | process | Branch semantics |
| `sequenceFlow sourceRef targetRef` + `conditionExpression` (`=vars.X == "…"`) | process | Graph edges and branch predicates → Business Rules |
| `boundaryEvent attachedToRef cancelActivity` + `timerEventDefinition` / `errorEventDefinition` (`errorRef` → `<bpmn:error errorCode>`) | process | Timeouts and error paths per step |
| `<uipath:retry maxRetryCount retryBackoff>`, `<uipath:errorMapping>` | activity | Retry policy per step |
| `subProcess triggeredByEvent`, `multiInstanceLoopCharacteristics isSequential` + `<uipath:loopCharacteristics inputCollection inputElement>` | process | Event subprocesses and batch loops |

Skip `bpmndi:` diagram elements.

## Signals — Case

| Signal | Path | Tells you |
|---|---|---|
| `metadata.caseIdentifier`, `caseIdentifierType` | top | Case ID scheme |
| `nodes[type=uipath.case.trigger].data.inputs.serviceType` | trigger | `None` (manual), `Intsvc.EventTrigger`, `timer` |
| `nodes[type=case-management:Stage]`, `data.stageType` (`secondary` = exception stage) | nodes | Stages → Process Map |
| `data.tasks` (2-D array: inner = parallel, consecutive = sequential) | stage | Task order and parallelism |
| task `type`: `process`, `rpa`, `agent`, `api-workflow`, `action` (human), `case-management`, `execute-connector-activity`, `wait-for-connector`, `wait-for-timer` | tasks | Component kind invoked — handoff edges |
| `isRequired`, `skipCondition`, `shouldRunOnlyOnce`, `entryConditions[].rules` (DNF), `exitConditions[].{type, exitToStageId}` | tasks / stage | Business rules and gating |
| `metadata.slaRules[]`, `nodes[].data.slaRules[]` (`count`, `unit`, `escalationRule[]` with `triggerInfo.type`, `atRiskPercentage`, `recipients`) | metadata / stage | SLAs and escalation → Business Rules and Error Handling |
| `metadata.caseExitRules[].marksCaseComplete` | metadata | Case completion |
| `variables.{inputs, outputs, inputOutputs}`, `bindings[]` | top | Interface and platform resources |

## Signals — Low-code Agent

| Signal | Path | Tells you |
|---|---|---|
| `"type": "lowCode"`, `metadata.isConversational`, `settings.engine` | `agent.json` | Autonomous vs conversational |
| `messages[role=system].content` | `agent.json` | Agent instructions — primary source of business rules; paraphrase, never quote verbatim |
| `messages[role=user].content` with `{{input.x}}`, `@{tools.X}`, `@{contexts.X}`, `@{escalations.X}` | `agent.json` | Inputs used and resources referenced |
| `inputSchema`, `outputSchema` (`$ref: job-attachment` = file) | `agent.json`, mirrored in `entry-points.json` | Interface |
| `settings.{model, maxIterations, temperature}` | `agent.json` | Model → Configuration Question, since the tenant decides which models are available; loop budget and temperature → Business Rules |
| `resources/<Name>/resource.json` `$resourceType: "tool"`, `type`: `process`, `agent`, `api`, `processOrchestration`, `internal`; `location` (`solution` / `external`), `referenceKey`, `properties.{processName, folderPath}` | resources | Tools = handoff edges to other components; `external` = deployed dependency |
| `$resourceType: "escalation"` with `channel.type: actionCenter`, `channel.properties.folderName` | resources | HITL escalation |
| `$resourceType: "mcp"` (`availableTools`), `"context"` | resources | MCP servers and context-grounding indexes |
| `guardrails[]`, tool `guardrail.policies` | `agent.json`, resources | Policy checks → Business Rules |
| `features/<Name>/feature.json` | features | Memory spaces |

## Signals — Coded Agent

| Signal | File | Tells you |
|---|---|---|
| `langgraph.json` `graphs` (`"agent": "./main.py:graph"`), `llama_index.json`, `openai_agents.json` | root | Framework and where graph starts |
| `StateGraph`, `add_node`, `add_edge`, `add_conditional_edges` | graph module | Step topology and branching |
| `Input` / `Output` / `State` Pydantic or TypedDict classes | graph module | Interface (also in `entry-points.json`) |
| `sdk.processes.invoke`, `sdk.queues.*`, `sdk.assets.retrieve`, `sdk.buckets.*`, `sdk.tasks.create`, `sdk.context_grounding.*`, `sdk.connections.retrieve`, `sdk.mcp.*` | any `.py` | Tools and side effects → handoff edges, platform resources |
| `interrupt(InvokeProcess / CreateTask / CreateEscalation(...))`, `EscalateAction(app_name=…)` | any `.py` | HITL checkpoints |
| System prompt strings passed to the model | any `.py` | Business rules — paraphrase |
| `bindings.json` `resources[]` (`resource`: `asset`, `queue`, `process`, `bucket`, `app`, `index`, `connection`, `mcpServer`) | root | Platform resources |
| `evaluations/eval-sets/*.json`, `evaluations/evaluators/*.json` | evaluations | Expected behaviour → acceptance criteria |
| `pyproject.toml` `[project].dependencies` | root | Framework packages |

## Signals — API Workflow

| Signal | Path | Tells you |
|---|---|---|
| `document.dsl`, `evaluate.language` | top | Serverless Workflow 1.0, JavaScript expressions |
| `input.schema.document`, `output.schema.document` | top | Interface |
| `document.metadata.variables.schema.document.properties` | top | Variables and defaults |
| `do[]` single-key tasks; `metadata.activityType`: `Sequence`, `Assign`, `JsInvoke`, `If`, `ForEach`, `DoWhile`, `Break`, `TryCatch`, `Wait`, `Response`, `Connector`, `FileToBase64`, `Base64ToFile` | top | Steps and control flow |
| `metadata.isTransparent: true` (`WorkflowStart`) | first task | Generated — skip |
| `call: "UiPath.Http"` + `with.bodyParameters.{method, url}` | HTTP task | Real verb and URL (outer `with.method` is always POST) → Target Applications |
| `call: "UiPath.IntSvc"` + `with.{connector, connectionId, endpoint}` | connector task | Integration Service connector and operation |
| `run.script.code` | JsInvoke | Embedded logic → Business Rules |
| `try` / `catch` blocks | TryCatch | Error handling |
| `response` on the final task | Response | Output |
| `httpRetryConfig` | top | Retry policy |

## Signals — Coded Function

| Signal | File | Tells you |
|---|---|---|
| `functions` map (`"main": "main.py:my_function"`) | `uipath.json` | Entry points |
| Pydantic `Input` / `Output` (Python) or `defineFunction({ input: defineSchema<Input>(), output: … })` (TS/JS) | entry module | Interface |
| `method` + `path` on `defineFunction` | TS/JS | HTTP endpoint vs run-as-job |
| `UiPath()` SDK calls (Python), `ctx.platform.*` (TS/JS) | code | Platform side effects |
| Body logic (conditions, calculations) | code | Business rules |
| `entry-points.json` `entryPoints[].{type: "function", input, output}`, `bindings_v2.json` `HttpTrigger` | generated | Confirms interface and trigger |

## Signals — Coded App

| Signal | File | Tells you |
|---|---|---|
| `project.uiproj` `ProjectType: "AppV2"`; `webAppManifest.json` `config.isActionApp` | root | In-solution app; Action app vs Web app |
| `action-schema.json` `inputs` / `outputs` / `inOuts` / `outcomes` | root | Human-task data contract → Interface, HITL handoff |
| `package.json` deps `@uipath/coded-action-app`, `@uipath/uipath-typescript` | root | App flavour |
| `sdk.processes.*`, `sdk.queues.*`, `sdk.entities.*`, `sdk.tasks.*`, `sdk.assets.*`, `sdk.buckets.*`, `sdk.maestro.*`, `sdk.conversations.*` | `src/**/*.ts(x)` | Platform data read and written → Platform Dependencies, handoffs |
| Route and page components, forms, tables | `src/**` | Workflow steps as user actions ("reviewer opens…, edits…, submits…") |
| Widget imports (Validation Station, PDF viewer, DataTable, chat) | `src/**` | Capabilities to name in Overview |
| `.uipath/app.config.json` `appType`, `appName` | root | Deployed identity |

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
5. Unreachable workflows: list in Source Map as dead code; exclude from Workflow.
6. Test project: the execution template invokes every registered case through its placeholder, so its steps are shared steps of every case (§ Signals — Test projects). A workflow belongs to the component whose folder holds it; a call from another component's case is a cross-component edge, never a copy of the callee.
7. REFramework / StateMachine: the Workflow's call graph starts at the per-item process workflow and adds the once-per-run and at-the-end workflows as steps of their own (§ Signals — XAML › REFramework projects); the state machine, its transitions and the framework's retry and status workflows are not steps. The queue is a Platform Dependency; the business/system outcome classification and the counts go to the Transactional Shape ([genome-format-guide.md § Transactional Shape](genome-format-guide.md)).

## Expression Translation

Check `project.json` `expressionLanguage` before reading XAML. VisualBasic: `AndAlso` / `OrElse` / `&` / `=` / `<>` / `Not`. CSharp: `&&` / `||` / `+` / `==` / `!=` / `!`. Flow, BPMN, and API workflow expressions are JavaScript (`===`, `&&`, `||`, `?.`); BPMN predicates are `=`-prefixed. Case conditions are `=js:` prefixed. Translate all with the table in [genome-format-guide.md § Business Rules](genome-format-guide.md). `DateTime.Now.AddDays(-30)` style arithmetic → "more than 30 days old". String concatenation → describe resulting text.

## Platform Resources

| Where | Resource rows |
|---|---|
| `bindings_v2.json` `resources[]` (`resource`: `process`, `queue`, `asset`, `bucket`, `connection`, `app`, `index`, `mcpServer`, `Entity`; `key`; `value.*.defaultValue`; `metadata.connector`) | One Platform Dependencies row each, default name and folder as source value |
| `bindings.json` (coded agents) | Same mapping |
| `.flow` top-level `bindings[]` | Processes, agents, API workflows invoked; folders |
| XAML queue / asset / credential / bucket / StartJob activities; `.cs` `system.` calls | Queues, assets, credentials, buckets, jobs |
| `project.json` `dependencies` that are libraries (packages published from another automation project, not activity packages); feeds in the project's `NuGet.config` | One row per library: package, version, feed. Steps describe the library workflows they call by behaviour, from their arguments; a library's bodies are read only when its project is given as a related resource |
| `Data/Config.xlsx` Assets sheet (REFramework) | One Platform Dependencies row per asset name; Credential when the sheet's description or the consuming activity says so, otherwise Text |
| BPMN `<uipath:context>` inputs (`folderPath`, `releaseKey`, `appId`, `connection`) | Processes, HITL apps, connections |
| `entry-points.json` | Interface inputs and outputs per component |
| Triggers: `.flow` scheduled/connector trigger nodes, BPMN start event types, Case trigger `serviceType`, `bindings_v2.json` `HttpTrigger` | Deployment → Entry points and triggers |

## UI Target Locators

UiPath sources already hold UiPath targets; nothing translated, everything carried over. Execution reads them from the source project the Source Map names; the derived catalog lists, per project:

| Where | What | Carry-over at execution |
|---|---|---|
| `.objects/**` (Object Repository store) | applications, screens, elements with their descriptors (strict, fuzzy, anchors, CV, semantic) | copy store into rebuilt project, or consume source UI library package; link activities by element reference. Confidence `high` (captured against live application) |
| `uix:TargetAnchorable` / `uix:TargetApp` inline in `.xaml`, keyed by workflow and activity `IdRef` | targets never promoted to Object Repository | promote to Object Repository when genome makes the workflow a library activity; otherwise carry inline. Confidence `high` |
| `Descriptors.<App>.<Screen>.<Element>` in coded workflows (resolved through `ObjectRepository.cs`) | coded references into same store | store copy covers them; generated file is regenerated by first validate |
| Legacy (`targetFramework: Legacy`) `Selector` attributes on classic activities | classic strict selectors | catalogued with confidence `medium`; rebuild routes through owning skill's legacy guidance; genome flags conversion `*[Inferred]*` |

Selectors never enter genome body (inventory rule above holds); they travel only in the catalog.

## Test Data

| Where | What | Data catalog derived at execution |
|---|---|---|
| `.variations/*.json`, registered in `project.json` → `designOptions.fileInfoCollection[].dataVariationFilePath` | data rows per test case, keyed by argument name | one recordset per file, rows as-is; process inventory maps test case → file |
| Test Data Queues (`test-data add-queue` argument named after the queue), Data Service entities | external data sources | Platform Dependencies rows (queue, entity), not rows in artifact |
| `GetRobotCredential` / `GetRobotAsset` asset names, `GetCredential` | credentials and configuration already in Orchestrator | keep asset names ([genome-format-guide.md § Platform Dependencies](genome-format-guide.md)); no secret present in source, none written |
| Default values on test-case arguments (`this:<Class>.<Arg>` root attributes) | single-row data | recordset's only row |

Variation row holding a password-looking field (`*password*`, `*pwd*`, `*secret*`, `*token*`) is redacted and reported; field is expected to become a credential asset name.

## Provenance

What the Source Map rows of [genome-format-guide.md § Source Map](genome-format-guide.md) carry for a UiPath source:

| Identity of | Carried as |
|---|---|
| The source | Project path, `projectId`, `projectVersion`; a solution's `.uipx` `SolutionId` with each project's `projectId`; the repository commit when the project sits in one |
| A workflow step | The workflow's project-relative path — unique in a project; a solution prefixes the project folder: `` `Folder/Workflow.xaml` `` in the step table's Source objects cell |
| A test case | Its path plus `testCaseId`, `` `Tests/Case.xaml` (<testCaseId>) ``; a checkpoint inside it by its activity `IdRef` |
| A step's data set | The data variation file's project-relative path, `` `.variations/<Case>.json` ``, in the step table's Data sets cell |
| Inventory | Workflows per artifact type, test cases, data files and rows, Object Repository applications, screens and elements, accounts |

No inventory script derives a process inventory or a recordset list, so the genome check runs without the export check, and [extraction-guide.md](extraction-guide.md) Step 6b's Glob check takes its place.

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
11. The REFramework template's sample values survive customisation: `ProcessABCQueue` in the settings sheet of a project whose item fetch reads rows, the template's own `Tests/` cases, `Exceptions_Screenshots/`. A queue is evidence only when the item fetch actually reads it (§ Signals — XAML › REFramework projects).
12. Framework workflows look like logic and are the template: the state machine, the retry counter, the three status updates and the screenshot on exception describe the Transactional Shape, not steps — transcribing them doubles the shape in the genome.
