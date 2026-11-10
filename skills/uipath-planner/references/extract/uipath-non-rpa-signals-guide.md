# UiPath Source Guide — Non-RPA Signals

Read after [uipath-source-guide.md](uipath-source-guide.md); read the § Signals sections below whose artifact type the inventory holds.

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
