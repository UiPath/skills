# Skill Mapping Guide — populating Build With

Every genome component and every workflow step maps to exactly one UiPath build skill. Use when writing a **Build With** table (authoring, extraction) or planning skill groups (execution).

## Rules

1. **One skill per row.** A step that mixes concerns (UI interaction plus a long calculation, or an API call plus an LLM decision) is split into two steps, each with its own skill.
2. **Build skills only.** Build With lists skills that produce a deployable artifact. Skills that operate the platform (queues, assets, connections, folders, jobs) go under **Platform Dependencies**, never in Build With.
3. **One component = one project — except test components.** In a process genome each non-test component maps to one buildable project and therefore to one primary skill. Steps inside a component may still use a second skill when the project is hybrid (XAML + coded files in one RPA project both map to `uipath-rpa`, so a hybrid RPA project is still one skill). Test components all map to the *same* `uipath-rpa` test project ([genome-format-guide.md § Two Levels](genome-format-guide.md) rule 1). Producer and consumer are roles of the Transactional Shape, not Type cell words; a split chosen at execution may turn one `uipath-rpa` component into several `uipath-rpa` projects, and the skill does not change ([transactional-shape-guide.md](transactional-shape-guide.md)).
4. **Orchestration is a step, not an annotation.** When a process coordinates several automations, the coordinator (Flow, BPMN, or Case plan) is its own component with its own row.
5. **Do not invent skill names.** Use only the names in the tables below; a name that is not listed will not resolve at execution time — the retired `uipath-rpa-workflows`, `uipath-coded-workflows` and `uipath-coded-agents` included.

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

**Human approval or validation checkpoints** belong to the containing component's skill, which authors them itself: a BPMN process's user task (`uipath-maestro-bpmn`), a Case plan's action task (`uipath-maestro-case`), a coded agent's escalation (`uipath-agents`), an RPA process's Action Center task in a long-running workflow (`uipath-rpa`). Only inside a **Flow** is the checkpoint designed with `uipath-human-in-the-loop`: name it in that row's Rationale column so the builder consults it for gate design.

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

## Common Combinations

| Shape | Example | Level | Components — type (role): skill | Applications |
|---|---|---|---|---|
| One skill, one UI application | Excel rows keyed into a web form | component genome | RPA process: `uipath-rpa` | Excel, the web application |
| One skill, no UI application | API polled, mail sent on change | component genome | RPA process (coded steps for polling and mail): `uipath-rpa` | REST API, mail server |
| Several skills, no UI application | AI-assisted review | process genome | Flow (glue): `uipath-maestro-flow`; Agent (classifier): `uipath-agents`; Coded app (review screen): `uipath-coded-apps` | data through connectors or APIs |
| Several skills, several applications | Invoice processing | process genome | BPMN process (orchestrator; human validation designed with `uipath-human-in-the-loop`): `uipath-maestro-bpmn`; RPA process (mailbox intake, Document Understanding extraction, ERP posting): `uipath-rpa`; Agent (exception triage): `uipath-agents` | mailbox, ERP; Platform Dependencies: exception queue, credential assets |

## Skill Capability Map

High-level view of what each specialist owns, for the plans `plan` and `decompose` write. **Do not describe internal flows of any specialist in your plan** — each skill documents its own procedures and will drift out of sync if duplicated here.

| Skill | What it owns | Handles auth? | Handles deploy? |
|---|---|---|---|
| `uipath-rpa` | RPA workflows (XAML and C# coded): create, edit, build, run, debug. Owns **all** UI automation authoring end-to-end, including live-app exploration and probing. | No (relies on Studio) | **No** — defer to `uipath-solution` for `.uipx` multi-project, `uipath-platform` for single non-solution packages |
| `uipath-agents` | AI agents — code-based (LangGraph / LlamaIndex / OpenAI Agents) and low-code (`agent.json`) | Yes (`uip login`) | **Yes** — end-to-end |
| `uipath-coded-apps` | Web apps (`.uipath/` dir): build, sync, package, publish, deploy | Yes (`uip login`) | **Yes** — end-to-end |
| `uipath-functions` | Coded Functions — Python (`uip function new -l py`; Pydantic typed I/O) or TypeScript/JavaScript (`-l ts / js`, TypeScript default; `defineFunction` + schema-first typed I/O) — atomic deterministic logic: transforms, custom-auth API calls, ERP/IS-connection queries. Runs serverless or on an RPA robot; a JS/TS function is delivered as a run-as-job function or an HTTP endpoint (Coded App backends) — one calling mode per function. Invoked from Maestro (Flow/BPMN), agents-as-tools, Orchestrator API, or its HTTP trigger. No LLM/agent loop (that → `uipath-agents`) | Yes (`uip login`) | **Yes** — `uip function pack/publish` |
| `uipath-rules` | Business Rules projects — one `.dmn` decision table (DMN 1.5) per project: `uip rules init`, `refresh`, `validate`, `debug`. Called by BPMN business rule tasks, Case `business-rule` tasks, and RPA | Yes (`uip login` for `debug`) | **No** — `uip solution pack/publish/deploy` via `uipath-solution` |
| `uipath-maestro-flow` | `.flow` files orchestrating RPA, agents, apps | Yes (`uip login`) | **Partial** — Orchestrator deploy of `.uipx`-wrapped solutions → `uipath-solution`; non-solution single package → `uipath-platform` |
| `uipath-maestro-bpmn` | `.bpmn` files — standards-based BPMN 2.0 process orchestration (gateways, events, boundary timeouts, subprocesses, multi-instance) over RPA, agents, APIs, HITL. Authors its own inline userTask/HITL nodes. | Yes (`uip login`) | **Yes** — packages, uploads, publishes/deploys, and runs via `uip maestro bpmn`; Orchestrator deploy of `.uipx`-wrapped solutions → `uipath-solution` |
| `uipath-maestro-case` | Case Management authoring — `caseplan.case` from an SDD (`case pack` compiles it to `caseplan.case.bpmn`; authoring `.bpmn` directly is `uipath-maestro-bpmn`) | Yes (`uip login`) | **Partial** — publishes to Studio Web and Orchestrator itself; `.uipx` solution deploy → `uipath-solution` |
| `uipath-api-workflow` | API Workflows (JSON `document.dsl`): author, run locally (`uip api-workflow run`), connector activities | Yes (`uip login`) | **No** — `uip solution pack/publish` via `uipath-solution` |
| `uipath-human-in-the-loop` | HITL node authoring — approval gates, escalations, write-back validation inside **Flow** projects. Coded-agent HITL → `uipath-agents`; BPMN / Case / RPA own theirs inline (userTask / task type / Action Center) | No (authoring only) | **No** — ships inside the host project |
| `uipath-platform` | Auth (`uip login`), Orchestrator (folders, processes, jobs, machines, users, roles), resources (assets, queues, storage buckets + bucket files, libraries, webhooks, triggers), Integration Service (connectors, connections, activities, IS triggers), Data Fabric entities/records/files/choice-sets (`uip df`), traces, licensing | Yes (auth hub) | **Yes** — for non-solution single packages and Orchestrator-side post-deploy ops |
| `uipath-ixp` | Document Understanding / IXP — extraction from semi-structured documents (invoices, forms): taxonomy, model, classify / extract / validate. Standalone project, or the extraction step a primary consumes | Yes (`uip login`) | **Partial** — model publish/tag via `uip ixp`; consumed by the host project |
| `uipath-connector-builder` | Integration Service **custom connector** authoring (REST+JSON) on disk via `uip is connectors builder` — build a connector when the catalog has none for a required integration (needed by API Workflows / Maestro / Agents; RPA can call the API directly instead) | Yes (`uip login`) | **Yes** — import/publish is deployment (`uip is connectors`) |
| `uipath-mcp-servers` | UiPath AgentHub MCP server registration (6 types: `uipath`, `coded`, `command`, `remote`, `swagger`, `platform`) and resource-tool authoring on `uipath`-type servers (`automation`, `agent`, `agentic-process`, `api-workflow`). Wraps Orchestrator resources, external HTTP MCP endpoints, OpenAPI specs, published coded agents, local subprocess commands, or first-party UiPath services as MCP tools. NOT for FastMCP / Python `mcp` SDK work. | Yes (`uip login`) | **Yes** — registration is deployment (posts directly to AgentHub) |
| `uipath-solution` | `uip solution` lifecycle (init, pack, publish, deploy, activate) for `.uipx` solutions. Runs as the final skill in PDD-driven flows (deploy of `.uipx` solutions). | Yes (`uip login`) | **Yes** — for multi-project Solution (`.uipx`) deploys |
