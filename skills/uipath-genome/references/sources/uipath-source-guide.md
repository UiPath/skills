# UiPath Source Guide

Framework-specific knowledge for extracting a genome from UiPath artifacts. Follows the section contract in [source-framework-contract.md](source-framework-contract.md). The pipeline lives in [extraction-guide.md](../extraction-guide.md).

Read § Detection through § Component Detection, § Call Graph Rules, § Platform Resources, and § Framework Pitfalls in full. Read a § Signals section only for artifact types present in the inventory.

## Detection

| Signal | Meaning |
|---|---|
| `<Name>.uipx` in the root (JSON with `Projects[]`) | UiPath **solution** — multi-component. Process genome. Read `Projects[].Type` and `Projects[].ProjectRelativePath` for the component list. |
| Several sibling folders each with `project.json` / `project.uiproj` and no `.uipx` | Loose multi-project bundle — treat as a solution; flag `*[Inferred]*` in Deployment. |
| Single `project.json` (RPA) or `project.uiproj` (Flow, BPMN, Case, Api, Agent, AppV2) | One **component**. Component genome. |
| Only `.xaml` / `.cs` files, no manifest | RPA project with missing metadata — extract, flag name and settings `*[Inferred]*`. |
| `pyproject.toml` with `langgraph.json` / `llama_index.json` / `openai_agents.json` | Coded Python agent component. |
| `uipath.json` with a `functions` map | Coded Function component (Python if `pyproject.toml`, JS/TS if `package.json`). |
| `package.json` depending on `@uipath/uipath-typescript` or `@uipath/coded-action-app`, plus `webAppManifest.json` or `.uipath/app.config.json` | Coded app component. |

`.uipx` fields: `Projects[].{Id, Type, ProjectRelativePath}`, `SolutionId`, `StudioMinVersion`, `AutomationHubIdeaUrl`. `resources/solution_folder/**` mirrors `Projects[]` and is generated — do not read it for logic.

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
| `.objects/**` (Object Repository) | Application, screen, and element **names** only — never selectors | read for Target Applications and Source Map notes |
| `AGENTS.md`, `README.md`, `.claude/rules/project-context.md` | Author-written intent, known gotchas, run instructions | evidence for Overview and Error Handling; verify every claim against the code before using it |

Skip entirely: `.local/`, `.codedworkflows/`, `.settings/`, `.tmh/`, `.screenshots/`, `.project/`, `node_modules/`, `dist/`, `source/dist/`, `.venv/`, `__pycache__/`, `resources/solution_folder/`, `userProfile/`, `.git/`, `.app/` (generated trigger XAML), `*.Generated.xaml`.

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

Test projects (`.uipx` Type `Test`, `[TestCase]`-only `.cs`, `designOptions.outputType: Tests`) are not components. Record them in the Source Map as "test coverage present" and use their assertions as acceptance-criteria evidence.

## Signals — XAML

`project.json` fields first: `name`, `main`, `entryPoints[]` (`filePath`, `input`, `output`), `dependencies` (package IDs), `designOptions.outputType` (`Process` / `Library` / `Tests`), `expressionLanguage` (`VisualBasic` / `CSharp`), `targetFramework` (`Windows` / `Portable` / `Legacy`), `runtimeOptions.isAttended`, `runtimeOptions.requiresUserInteraction`, `globalHandler`.

| Signal | Where | Tells you | Example |
|---|---|---|---|
| Root element inside `<Activity>` | `<Sequence>`, `<Flowchart>`, `<StateMachine>` | Control-flow style; a StateMachine is usually a dispatcher/performer (REFramework) | `<StateMachine>` |
| `xmlns` declarations on `<Activity>` | root | Packages in use → target applications | `xmlns:umam="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail…"` |
| Activity elements in the body | e.g. `<ui:NTypeInto>`, `<umam:GetNewestEmail>`, `<p:ReadRange>`, `<ui:NClick>` | The business action of each step; `DisplayName` is the best plain-language hint | `DisplayName="Read invoice sheet"` |
| `<x:Members>` → `<x:Property Type="InArgument(x:String)">` | header | Workflow interface: In / Out / InOut arguments | `Name="in_InvoicePath"` |
| `<If Condition>`, `<Switch>`, `<FlowDecision Condition>`, `<FlowSwitch>` | body | Business rules and routing | `Condition="[Amount > 10000]"` |
| `<TryCatch>` + `<Catch x:TypeArguments>`, `<RetryScope NumberOfRetries>`, `<Rethrow>`, `<Throw>` | body | Error handling per step | `NumberOfRetries="3"` |
| `<ForEach>`, `<While>`, `<DoWhile>`, `<ForEachRow>`, `<ui:ForEachUiElement>` | body | Iteration over items, rows, elements | |
| `<InvokeWorkflowFile FileName>` + `<Argument>` children | body | Call-graph edge and data passed | `FileName="ProcessInvoice.xaml"` |
| `ConnectionId` attribute, `<isactr:ConnectorActivity UiPathActivityTypeId>` | body | Integration Service connector call; resolve the service from the namespace or type id | `uipath-salesforce-sfdc` |
| Queue activities (`AddQueueItem`, `GetTransactionItem`, `SetTransactionStatus`), asset activities (`GetAsset`, `GetCredential`), `StartJob`, `CreateFormTask` / `WaitForFormTaskAndResume`, `Persistence` activities | body | Platform resources and HITL waits | queue name attribute |
| `<Variable x:TypeArguments Name>` | `.Variables` blocks | Data flow hints only — never in the genome body | |
| Object Repository references (`uix:TargetAnchorable`, `uix:TargetApp`, `Descriptor` elements) | body | UI targets; name the screen and application, never the selector. `TargetApp Url` / `ScopeSelectorArgument url=` give the target system's base URL → Configuration Question | `Url="https://<org>.lightning.force.com/…"` |
| `uix:NApplicationCard` / `ui:OpenBrowser` / `ui:OpenApplication` | body | The application scope: browser type, attach vs launch, one scope per application session | `BrowserType="Chrome" AttachMode="ByInstance"` |
| `DelayBefore` / `DelayAfter`, `WaitForReadyArgument`, `EmptyFieldMode` | UIA activity attributes | Timing and field-clearing behaviour → Error Handling wording ("waits for the dialog to settle", "replaces the pre-filled value") — never the attribute names | `EmptyFieldMode="SingleLine"` |
| `SearchSteps="SemanticSelector"` with `SemanticSelectorArgument` | target | Element located by a natural-language description, usually because no stable selector exists → Source Map note | |

Skip `<sap2010:WorkflowViewState.ViewStateManager>` and every `sap:VirtualizedContainerService.HintSize` — designer layout, not logic.

## Signals — Coded C#

| Signal | Pattern | Tells you |
|---|---|---|
| `[Workflow]` on a method | entry point of a coded workflow |
| `[TestCase]` on a method | test — evidence for acceptance criteria, not a component step |
| Service properties: `system.`, `excel.`, `mail.`, `office365.`, `uiAutomation.`, `testing.` | Which UiPath service and therefore which application |
| `connections.<Connector>.<Connection>` | Integration Service connection; connector name is in the property chain |
| `workflows.<Name>(…)` | Call-graph edge to another workflow |
| `try` / `catch (<Type>)` / `finally`, `Polly`-style loops | Error handling |
| `if` / `switch` / `foreach` / `while` / LINQ `Where` | Business rules and iteration |
| Method signature and `.cs.json` `arguments[]` (`name`, `type`, `direction`) | Interface |
| `BuildClient("Orchestrator")`, `HttpClient` | Orchestrator API or external REST |
| `Descriptors.<Screen>.<Element>` | UI targets from the Object Repository |

## Signals — Flow

| Signal | Path | Tells you |
|---|---|---|
| Trigger node `type` | `nodes[].type`: `core.trigger.manual`, `core.trigger.scheduled` (`inputs.timerPreset`), `uipath.connector.trigger.*`, `core.trigger.voice` | How the flow starts |
| Resource node `type` | `uipath.core.rpa-workflow.<key>`, `uipath.core.agent.<key>`, `uipath.core.api-workflow.<key>`, `uipath.core.flow.<key>`, `uipath.core.agentic-process.<key>`, `uipath.core.human-task.<key>`, `core.subflow` | Which component kind is invoked — a handoff edge in a process genome |
| `definitions[].model.bindings.{resourceKey, resourceSubType, serviceType}` and top-level `bindings[]` (`name`, `folderPath`, `default`) | definitions / bindings | The concrete Orchestrator process, agent, or API workflow invoked |
| `core.logic.decision` (`inputs.expression`), `core.logic.switch` (`inputs.cases`), `core.logic.loop` (`inputs.collection`, `parallel`), `core.logic.merge` | nodes | Business rules and iteration |
| `uipath.human-in-the-loop.quick-form` (`inputs.schema.fields[]`, `outcomes[]`, `recipient`) | nodes | Inline approval — HITL checkpoint |
| `core.action.script` (`inputs.script`), `core.action.http.v2` (`method`, `url`, `branches`), `core.action.transform`, `core.action.queue.create[-and-wait]`, `core.datafabric.*`, `uipath.connector.*`, `uipath.ixp.*`, `uipath.agent.autonomous` | nodes | Embedded logic, HTTP targets, queue and Data Fabric use, connectors, inline agents |
| `core.logic.terminate` vs `core.control.end` (`outputs`) | nodes | Fatal abort vs normal completion and flow outputs |
| `edges[]` `{sourceNodeId, sourcePort, targetNodeId}`; ports `true`/`false`, `case-<id>`/`default`, `success`/`error`, `completed` | edges | Graph and branch semantics; an `error` port is an error-handling path |
| `inputs.errorHandlingEnabled: true` | action node | Step has an error escape path |
| `variables.nodes[]` (`<nodeId>.<outputId>`) | top level | Data flow between nodes |

## Signals — BPMN

Confirm `xmlns:uipath="http://uipath.org/schema/bpmn"` on `<bpmn:definitions>`.

| Signal | Where | Tells you |
|---|---|---|
| `<uipath:variables>` → `<uipath:inputOutput id name type>` | process `extensionElements` | Process data schema |
| `<uipath:type value="…">` inside a task's `extensionElements` | `Orchestrator.StartJob` (RPA), `Orchestrator.StartAgentJob` (agent), `Orchestrator.ExecuteApiWorkflowAsync`, `Actions.HITL`, `Intsvc.ActivityExecution` (connector), `Intsvc.UnifiedHttpRequest`, `A2A.AgentExecution`, `Orchestrator.StartAgenticProcess`, `Orchestrator.StartCaseMgmtProcess`, `BPMN.ScriptTask` | What the step invokes — each is a handoff edge to a component or an external system |
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
| `messages[role=system].content` | `agent.json` | The agent's instructions — the primary source of business rules; paraphrase, never quote verbatim |
| `messages[role=user].content` with `{{input.x}}`, `@{tools.X}`, `@{contexts.X}`, `@{escalations.X}` | `agent.json` | Inputs used and resources referenced |
| `inputSchema`, `outputSchema` (`$ref: job-attachment` = file) | `agent.json`, mirrored in `entry-points.json` | Interface |
| `settings.{model, maxIterations, temperature}` | `agent.json` | Model and loop budget → Configuration Questions |
| `resources/<Name>/resource.json` `$resourceType: "tool"`, `type`: `process`, `agent`, `api`, `processOrchestration`, `internal`; `location` (`solution` / `external`), `referenceKey`, `properties.{processName, folderPath}` | resources | Tools = handoff edges to other components; `external` = deployed dependency |
| `$resourceType: "escalation"` with `channel.type: actionCenter`, `channel.properties.folderName` | resources | HITL escalation |
| `$resourceType: "mcp"` (`availableTools`), `"context"` | resources | MCP servers and context-grounding indexes |
| `guardrails[]`, tool `guardrail.policies` | `agent.json`, resources | Policy checks → Business Rules |
| `features/<Name>/feature.json` | features | Memory spaces |

## Signals — Coded Agent

| Signal | File | Tells you |
|---|---|---|
| `langgraph.json` `graphs` (`"agent": "./main.py:graph"`), `llama_index.json`, `openai_agents.json` | root | Framework and where the graph starts |
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
| `call: "UiPath.Http"` + `with.bodyParameters.{method, url}` | HTTP task | The real verb and URL (outer `with.method` is always POST) → Target Applications |
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
| `action-schema.json` `inputs` / `outputs` / `inOuts` / `outcomes` | root | The human-task data contract → Interface, HITL handoff |
| `package.json` deps `@uipath/coded-action-app`, `@uipath/uipath-typescript` | root | App flavour |
| `sdk.processes.*`, `sdk.queues.*`, `sdk.entities.*`, `sdk.tasks.*`, `sdk.assets.*`, `sdk.buckets.*`, `sdk.maestro.*`, `sdk.conversations.*` | `src/**/*.ts(x)` | Platform data read and written → Platform Dependencies, handoffs |
| Route and page components, forms, tables | `src/**` | Workflow steps as user actions ("reviewer opens…, edits…, submits…") |
| Widget imports (Validation Station, PDF viewer, DataTable, chat) | `src/**` | Capabilities to name in Overview |
| `.uipath/app.config.json` `appType`, `appName` | root | Deployed identity |

## Target Resolution

1. **XAML activity → application:** resolve from the `xmlns` namespace (`UiPath.MicrosoftOffice365.Activities.Mail` → Outlook / Office 365; `UiPath.GSuite.Activities` → Gmail / Google Workspace; `UiPath.Excel.Activities` → Excel; `UiPath.Database.Activities` → the database named in the connection string; `UiPath.UIAutomation.Activities` → the application named in the target's `DisplayName` or Object Repository screen; `UiPath.PDF.Activities` / `UiPath.IntelligentOCR.Activities` / `UiPath.DocumentUnderstanding.*` → Document Understanding; `UiPath.Persistence.Activities` → Action Center; `UiPath.Web.Activities` → the REST endpoint host).
2. **Connector key → service:** `uipath-salesforce-sfdc` → Salesforce; `uipath-microsoft-outlook365` → Outlook; `uipath-atlassian-jira` → Jira; `uipath-servicenow` → ServiceNow; `uipath-slack` → Slack. Strip the `uipath-` prefix and use the vendor name when the key is not listed.
3. **`ConnectionId` GUID alone** → look up `bindings_v2.json` `resources[resource=connection].metadata.connector`; if absent, the activity's namespace decides; if still unknown, write "Integration Service connector *[Inferred]*" in Source Map notes and the best-guess service in the body.
4. **Process / release references** (`releaseKey`, `processName`, `resourceKey`, `referenceKey`) → the component with the matching project name inside the same solution; otherwise an external dependency listed in Platform Dependencies as `Deployed process: <name>`.
5. **Orchestrator folders** → the Platform Dependencies row's Notes; never a Target Application.

## Call Graph Rules

1. Entry point: `project.json` `main` (RPA), `entryPoints[]` for multi-entry processes; `.flow` trigger node with `isDefaultEntryPoint`; BPMN `startEvent`; Case trigger node; `langgraph.json` graph; `Workflow.json` root `do[]`; `uipath.json` `functions`.
2. Edges inside a component: `<InvokeWorkflowFile FileName>`, `workflows.<Name>()`, `core.subflow`, BPMN `callActivity`, Case sub-stages. Depth-first from the entry point; order siblings top-to-bottom (Sequence), left-to-right (Flowchart), by `edges[]` order (Flow), by `sequenceFlow` order (BPMN).
3. Edges across components (handoffs): Flow resource nodes, BPMN `uipath:type` values that start a job or agent, Case task types `process` / `rpa` / `agent` / `api-workflow` / `action`, agent tools with `type` `process` / `api` / `agent`, `sdk.processes.invoke`, `StartJob` activities, queue producers and consumers sharing a queue name, Action Center task creation and the coded app that renders it.
4. Missing entry point: `outputType: Library` → each public workflow is an independent capability, listed as separate steps; `Process` without `main` → `Main.xaml` / `Main.cs` by convention, else alphabetical with `*[Inferred]*`.
5. Unreachable workflows: list them in the Source Map as dead code; exclude from Workflow.
6. REFramework / StateMachine: map states to phases — Init → step "Initialize and read config", Get Transaction Data → "Fetch next item", Process → the business steps, End → "Close applications and report". The queue is a Platform Dependency; retries and business/system exception classification go under Error Handling.

## Expression Translation

Check `project.json` `expressionLanguage` before reading XAML. VisualBasic: `AndAlso` / `OrElse` / `&` / `=` / `<>` / `Not`. CSharp: `&&` / `||` / `+` / `==` / `!=` / `!`. Flow, BPMN, and API workflow expressions are JavaScript (`===`, `&&`, `||`, `?.`); BPMN predicates are `=`-prefixed. Case conditions are `=js:` prefixed. Translate all of them with the table in [genome-format-guide.md § Business Rules](../genome-format-guide.md). `DateTime.Now.AddDays(-30)` style arithmetic → "more than 30 days old". String concatenation → describe the resulting text.

## Platform Resources

| Where | Resource rows |
|---|---|
| `bindings_v2.json` `resources[]` (`resource`: `process`, `queue`, `asset`, `bucket`, `connection`, `app`, `index`, `mcpServer`, `Entity`; `key`; `value.*.defaultValue`; `metadata.connector`) | One Platform Dependencies row each, with the default name and folder as source value |
| `bindings.json` (coded agents) | Same mapping |
| `.flow` top-level `bindings[]` | Processes, agents, API workflows invoked; folders |
| XAML queue / asset / credential / bucket / StartJob activities; `.cs` `system.` calls | Queues, assets, credentials, buckets, jobs |
| BPMN `<uipath:context>` inputs (`folderPath`, `releaseKey`, `appId`, `connection`) | Processes, HITL apps, connections |
| `entry-points.json` | Interface inputs and outputs per component |
| Triggers: `.flow` scheduled/connector trigger nodes, BPMN start event types, Case trigger `serviceType`, `bindings_v2.json` `HttpTrigger` | Deployment → Entry points and triggers |

## UI Target Locators

UiPath sources already hold UiPath targets; nothing is translated, everything is carried over. The catalog `source/targets.json` lists, per project:

| Where | What | Carry-over at execution |
|---|---|---|
| `.objects/**` (Object Repository store) | applications, screens, elements with their descriptors (strict, fuzzy, anchors, CV, semantic) | copy the store into the rebuilt project, or consume the source UI library package; link activities by element reference. Confidence `high` (captured against the live application) |
| `uix:TargetAnchorable` / `uix:TargetApp` inline in `.xaml`, keyed by workflow and activity `IdRef` | targets that were never promoted to the Object Repository | promote to the Object Repository when the genome makes the workflow a library activity; otherwise carry inline. Confidence `high` |
| `Descriptors.<App>.<Screen>.<Element>` in coded workflows (resolved through `ObjectRepository.cs`) | coded references into the same store | the store copy covers them; the generated file is regenerated by the first validate |
| Legacy (`targetFramework: Legacy`) `Selector` attributes on classic activities | classic strict selectors | catalogued with confidence `medium`; the rebuild routes through the owning skill's legacy guidance, the genome flags the conversion `*[Inferred]*` |

Selectors never enter the genome body (inventory rule above still holds); they travel only in the catalog.

## Test Data

| Where | What | `source/test-data.json` / `process-data.json` |
|---|---|---|
| `.variations/*.json`, registered in `project.json` → `designOptions.fileInfoCollection[].dataVariationFilePath` | data rows per test case, keyed by argument name | one recordset per file, rows as-is; `process-data.json` maps test case → file |
| Test Data Queues (`test-data add-queue` argument named after the queue), Data Service entities | external data sources | Platform Dependencies rows (queue, entity), not rows in the artifact |
| `GetRobotCredential` / `GetRobotAsset` asset names, `GetCredential` | credentials and configuration already in Orchestrator | keep the asset names; one credential asset per account stays the rule; no secret is present in the source and none is written |
| Default values on test-case arguments (`this:<Class>.<Arg>` root attributes) | single-row data | the recordset's only row |

A variation row that holds a password-looking field (`*password*`, `*pwd*`, `*secret*`, `*token*`) is redacted and reported; the field is expected to become a credential asset name.

## Framework Pitfalls

1. `sap2010:WorkflowViewState` and `HintSize` attributes look like content and are layout only.
2. `xmlns` declarations are package imports, not steps. Many are declared and unused.
3. Flow resource-node instances carry no `model`; the resource is in `definitions[]` and `bindings[]`.
4. BPMN `uipath:type` decides what a task does; the BPMN element name (`serviceTask`) is only a hint.
5. Low-code agent tools are files under `resources/`, not an array in `agent.json`.
6. API workflow HTTP tasks: the real verb and URL are in `with.bodyParameters`, not the outer `with`.
7. `bindings.json` and `bindings_v2.json` are different files with different consumers; a coded agent may have both.
8. `.app/` and `*.Generated.xaml` are generated trigger plumbing for apps and Action Center — skip.
9. `resources/solution_folder/**` mirrors the manifest and is regenerated; read `.uipx` instead.
10. A `[TestCase]` `.cs` file or `Test` project is evidence, not a component.
