# Skill Mapping Guide — populating Build With

Every genome component and every workflow step maps to exactly one UiPath build skill. Use when writing a **Build With** table (authoring, extraction) or planning skill groups (the build).

## Rules

1. **One skill per row.** A step that mixes concerns (UI interaction plus a long calculation, or an API call plus an LLM decision) is split into two steps, each with its own skill.
2. **Build skills only.** Build With lists skills that produce a deployable artifact. Skills that operate the UiPath platform (queues, assets, connections, folders, jobs) go under **Platform Dependencies**, never in Build With.
3. **One component = one project — except test components.** In a process genome each non-test component maps to one buildable project and therefore to one primary skill. Steps inside a component may still use a second skill when the project is hybrid (XAML + coded files in one RPA project both map to `uipath-rpa`, so a hybrid RPA project is still one skill). Test components all map to the *same* `uipath-rpa` test project ([genome-format-guide.md § Two Levels](genome-format-guide.md) rule 1). Producer and consumer are roles of the Transactional Shape, not Type cell words; a split chosen at build may turn one `uipath-rpa` component into several `uipath-rpa` projects, and the skill does not change ([transactional-shape-guide.md](transactional-shape-guide.md)).
4. **Orchestration is a step, not an annotation.** When a process coordinates several automations, the coordinator (Flow, BPMN, or Case plan) is its own component with its own row.
5. **Do not invent skill names.** Use only the names in the tables below; a name that is not listed will not resolve at build time — the retired `uipath-rpa-workflows`, `uipath-coded-workflows` and `uipath-coded-agents` included.

## Build Skills

| Component / step type | Skill | Authoring signals (user says) | Extraction signals (source artifact) |
|---|---|---|---|
| RPA workflow: desktop or browser UI automation, Excel, mail, PDF, file system, Object Repository selectors, Document Understanding activities, Integration Service connector activities, C# coded business logic, test cases | `uipath-rpa` | "click", "type into", "read the spreadsheet", "download attachments", "scrape", "fill the form", "validate with C#", "call Salesforce connector" | `project.json` with `.xaml` files and/or `.cs` files carrying `[Workflow]` / `[TestCase]` |
| Maestro Flow: lightweight orchestration of deployed processes, agents, connectors; script and HTTP nodes; inline agent steps; approval nodes; connector triggers | `uipath-maestro-flow` | "when X happens in Slack/Jira, run Y", "chain these automations", "a flow that calls the agent then the process" | `.flow` file, `entry-points.json`, `bindings_v2.json` |
| BPMN process orchestration: long-running multi-lane process, gateways, events, human tasks, compensation | `uipath-maestro-bpmn` | "end-to-end process", "swim lanes", "wait for approval for days", "process with stages and gateways" | `.bpmn` file |
| Case management: case plan with stages, tasks, SLAs, ad-hoc human work | `uipath-maestro-case` | "case", "claims handling", "each case has stages and SLAs" | `caseplan.case` / `caseplan.json` |
| Agent: LLM reasoning, tool selection, natural-language decisions, conversational | `uipath-agents` | "decide", "classify with AI", "summarize", "chatbot", "agent that reads the email and picks an action" | `agent.json` with `"type": "lowCode"`; or Python project with `pyproject.toml` plus `langgraph.json` / `main.py` and `uipath.json` without a `functions` map |
| Coded function: deterministic Python or TypeScript/JavaScript unit, no LLM | `uipath-functions` | "a function that computes", "pure transform", "rule-based scoring" | `uipath.json` with a `functions` map |
| Business rule: one DMN decision table that a process, flow or case evaluates | `uipath-rules` | "decision table", "the business maintains these rules", "look up the approval level by amount and region" | `.dmn` file beside `project.uiproj` |
| API workflow: JSON-defined HTTP and connector sequences | `uipath-api-workflow` | "call these REST endpoints in sequence", "API integration without UI" | `Workflow.json` with `document.dsl`, project type `Api` |
| Coded app: React/TypeScript web app or action app for end users | `uipath-coded-apps` | "a screen where users review", "dashboard", "form for the team" | `.uipath/` folder, `app.config.json`, `action-schema.json`, `package.json` depending on `@uipath/uipath-typescript` |
| Custom Integration Service connector | `uipath-connector-builder` | "connect to our internal REST API as a connector" | `element.json`, `element-metadata.json`, `standard-resources/` |
| Document extraction model (IXP): taxonomy, training, model deployment | `uipath-ixp` | "train a model to extract fields from these documents" | IXP project reference, taxonomy files |
| Process Mining app | `uipath-process-mining` | "analyse the event log", "process app" | dbt models, process-app data mapping |
| MCP server / resource tools | `uipath-mcp-servers` | "expose these as MCP tools" | `uipath`-type MCP server registration |

**Human approval or validation checkpoints** inside a Flow, BPMN process, Case plan, or agent belong to the containing component's skill. Name `uipath-human-in-the-loop` in the Rationale column so the builder consults it for gate design.

**Solution packaging** (`.uipx`) is not a Build With row. A process genome records it under **Deployment** with `uipath-solution`.

## Platform Dependencies (not Build With)

| Resource | Skill that operates it |
|---|---|
| Orchestrator queues, assets, storage buckets, folders, triggers, jobs | `uipath-platform` |
| Integration Service connections | `uipath-platform` |
| Data Fabric entities | `uipath-platform` |
| Action Center tasks at runtime | `uipath-tasks` |
| Test Manager cases, sets, reports | `uipath-test` |
| Identity, roles, tenants, audit | `uipath-admin` |

## Decision Tree for Ambiguous Steps

1. Step interacts with a screen (desktop or browser), or with what only a robot's machine reaches — Excel and Office files, files and folders on local or network storage, an on-premises database, desktop mail, a terminal → `uipath-rpa`.
2. Step reads or writes Excel, mail, PDF, files, or calls an Integration Service connector activity from a workflow → `uipath-rpa`.
3. Step reads fields from semi-structured documents (invoices, forms, contracts) → a document-extraction step of the component that uses it; training or deploying the extraction model is its own row → `uipath-ixp`.
4. Step decides by a threshold, eligibility or routing table the business maintains → a decision table of its own, which the step evaluates → `uipath-rules`.
5. Step needs an LLM to decide, classify, summarize, or converse → `uipath-agents` when the agent is a component of its own: a conversation, an agent several components call, an agent with its own evaluations. One reasoning step among a Flow's other steps, with its model, tools and answer contract, is the Flow's inline agent → `uipath-maestro-flow`. A fixed generation step with no decision (summarize, draft) is an LLM activity of the component that runs it.
6. Step is deterministic code with no UI and no LLM, invoked as a unit by other components → `uipath-functions`. If the same logic lives inside an RPA project as C#, keep `uipath-rpa`.
7. Step is a sequence of HTTP or connector calls with no UI, to systems the cloud reaches → `uipath-api-workflow` when standalone; `uipath-rpa` when it lives inside an RPA project.
8. Step waits for a person — an approval, a review, missing data: inside one RPA process, a task in Action Center and a long-running workflow → `uipath-rpa`; inside a coordinator, that coordinator's human-task node or task (Rationale names `uipath-human-in-the-loop`).
9. Step coordinates other components → `uipath-maestro-flow` for a pipeline of automations with branches; `uipath-maestro-bpmn` for formal gateways, events, timers or subprocesses; `uipath-maestro-case` for a case moving through stages with SLAs. A coordinator is chosen only for coordination one component cannot hold — state that outlives a run (waits of days, events, timers), parallel branches, several automations that run on their own, per-step visibility end to end. A component that calls another automation and uses its result in the same run keeps the call as a step, and starting one dispatcher and its performer needs no coordinator.
10. Step is a user-facing screen → `uipath-coded-apps`.
11. Data several components share is a Data Fabric entity: a Platform Dependency, never a step's skill; the step that reads or writes it takes the skill of the component that runs it.
12. Still ambiguous between `uipath-rpa` and anything else → `uipath-rpa`.

## Refactor Targets

The Target answer of a refactor or migration ([extract-guide.md](../extract/extract-guide.md) Step 6c) is chosen per component in two moves: type each step with § Decision Tree for Ambiguous Steps, then give the component one host, the simplest product that holds every step. A host keeps as steps the calls it makes and uses within one run — an RPA process calls connectors, document models, an LLM, an agent or a published automation; an API workflow calls connectors and other API workflows; a coordinator calls them all as its nodes.

| The component's steps | Recommended host |
|---|---|
| Any step on a screen or on what only a robot's machine reaches | RPA process, Portable unless an activity the steps need exists only for Windows |
| Connector and HTTP calls only, a short run of few steps | API workflow |
| Connector and HTTP calls only, a long run, waits, or many steps whose every run must be inspectable step by step | Maestro flow |
| Items worked one by one, each retried and reported on its own after the reads are batched (rule 2) | an RPA process that consumes the queue, starting each item's connector and HTTP work as an API workflow, so only the queue work needs a robot |
| Coordination one host cannot hold (Decision Tree item 9) | Maestro flow, BPMN process or case, each automation it calls a component of its own |
| A threshold or routing table, an extraction model, judgment no rule decides, code several components call | a component of its own — decision table, extraction model, agent, function — only when the business maintains it apart, it is trained, or several components call it; otherwise a step of the host |

1. **A product is chosen for the shape, never as an upgrade.** A coordinator, an agent, a function or a queue is Recommended only when the steps need what it adds. The source's own product is always an option; a Windows project's other option is the same project kind on Portable.
2. **Batch before counting items.** A per-item fan-out the source built because it read one item at a time is counted again after the reads are batched (one query for all rows, matched in memory, the decision's filters moved into the query). A few writes per run left → the host works them in its own loop and the queue goes; retries across runs, parallel workers or per-item status people read → the queue stays. The result is that flow's `Decided:` line ([transactional-shape-guide.md](transactional-shape-guide.md) rule 8).
3. **Coordination is replaced, not copied or dropped.** A lock on running jobs, a second pass over the same items or a ledger keeps its protection by the target's own means — a queue item per unit of work with a unique reference, a fresh read of each item before its writes; the source's mechanism stays only when the target's means cannot hold it. A coordinator is judged on what the whole chain needs, never on whether it takes the source's queue items.
4. **An event trigger stays an event trigger.** The target is one the source's event can start, directly or through a component it starts.
5. **A target the delivery model cannot run is never offered.** The delivery model is the one the genome records, or the Step 1 answer; the [Constraint Gate](product-selection-guide.md#constraint-gate) filters every option, and a product the matrix leaves unconfirmed is a later option naming the gap.
6. **Check the target before recommending it.** Each connector operation, trigger and limit the steps rely on is confirmed through the target's owning skill and its discovery commands (`uip is connectors list --output json`); an operation the registry does not list is confirmed when the owning skill documents an HTTP step through the connection and the vendor's API documentation has the call. A capability nothing confirms makes that target a later option, the gap named in its label.

## Common Combinations

| Shape | Example | Level | Components — type (role): skill | Applications |
|---|---|---|---|---|
| One skill, one UI application | Excel rows keyed into a web form | component genome | RPA process: `uipath-rpa` | Excel, the web application |
| One skill, no UI application | API polled, mail sent on change | component genome | RPA process (coded steps for polling and mail): `uipath-rpa` | REST API, mail server |
| Several skills, no UI application | AI-assisted review | process genome | Flow (glue): `uipath-maestro-flow`; Agent (classifier): `uipath-agents`; Coded app (review screen): `uipath-coded-apps` | data through connectors or APIs |
| Several skills, several applications | Invoice processing | process genome | BPMN process (orchestrator; human validation designed with `uipath-human-in-the-loop`): `uipath-maestro-bpmn`; RPA process (mailbox intake, Document Understanding extraction, ERP posting): `uipath-rpa`; Agent (exception triage): `uipath-agents` | mailbox, ERP; Platform Dependencies: exception queue, credential assets |
