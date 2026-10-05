# Skill Mapping Guide — populating Build With

Every genome component and every workflow step maps to exactly one UiPath build skill. Use when writing a **Build With** table (authoring, extraction) or planning skill groups (execution).

## Rules

1. **One skill per row.** A step that mixes concerns (UI interaction plus a long calculation, or an API call plus an LLM decision) is split into two steps, each with its own skill.
2. **Build skills only.** Build With lists skills that produce a deployable artifact. Skills that operate the platform (queues, assets, connections, folders, jobs) go under **Platform Dependencies**, never in Build With.
3. **One component = one project — except test components.** In a process genome each non-test component maps to one buildable project and therefore to one primary skill. Steps inside a component may still use a second skill when the project is hybrid (XAML + coded files in one RPA project both map to `uipath-rpa`, so a hybrid RPA project is still one skill). Test components all map to the *same* `uipath-rpa` test project ([genome-format-guide.md § Two Levels](genome-format-guide.md) rule 1). Producer and consumer are roles of the Transactional Shape, not Type cell words; a split chosen at execution may turn one `uipath-rpa` component into several `uipath-rpa` projects, and the skill does not change ([genome-format-guide.md § Transactional Shape](genome-format-guide.md)).
4. **Orchestration is a step, not an annotation.** When a process coordinates several automations, the coordinator (Flow, BPMN, or Case plan) is its own component with its own row.
5. **Do not invent skill names.** Use only the names in the tables below. These are the skills shipped in this plugin; a name that is not listed will not resolve at execution time.

## Build Skills

| Component / step type | Skill | Authoring signals (user says) | Extraction signals (source artifact) |
|---|---|---|---|
| RPA workflow: desktop or browser UI automation, Excel, mail, PDF, file system, Object Repository selectors, Document Understanding activities, Integration Service connector activities, C# coded business logic, test cases | `uipath-rpa` | "click", "type into", "read the spreadsheet", "download attachments", "scrape", "fill the form", "validate with C#", "call Salesforce connector" | `project.json` with `.xaml` files and/or `.cs` files carrying `[Workflow]` / `[TestCase]` |
| Maestro Flow: lightweight orchestration of deployed processes, agents, connectors; script and HTTP nodes; inline agent steps; approval nodes; connector triggers | `uipath-maestro-flow` | "when X happens in Slack/Jira, run Y", "chain these automations", "a flow that calls the agent then the process" | `.flow` file, `entry-points.json`, `bindings_v2.json` |
| BPMN process orchestration: long-running multi-lane process, gateways, events, human tasks, compensation | `uipath-maestro-bpmn` | "end-to-end process", "swim lanes", "wait for approval for days", "process with stages and gateways" | `.bpmn` file |
| Case management: case plan with stages, tasks, SLAs, ad-hoc human work | `uipath-maestro-case` | "case", "claims handling", "each case has stages and SLAs" | `caseplan.json` |
| Agent: LLM reasoning, tool selection, natural-language decisions, conversational | `uipath-agents` | "decide", "classify with AI", "summarize", "chatbot", "agent that reads the email and picks an action" | `agent.json` with `"type": "lowCode"`; or Python project with `pyproject.toml` plus `langgraph.json` / `main.py` and `uipath.json` without a `functions` map |
| Coded function: deterministic Python or TypeScript/JavaScript unit, no LLM | `uipath-functions` | "a function that computes", "pure transform", "rule-based scoring" | `uipath.json` with a `functions` map |
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

1. Step interacts with a screen (desktop or browser) → `uipath-rpa`.
2. Step reads or writes Excel, mail, PDF, files, or calls an Integration Service connector activity from a workflow → `uipath-rpa`.
3. Step needs an LLM to decide, classify, summarize, or converse → `uipath-agents` when the agent is a component of its own: a conversation, an agent several components call, an agent with its own evaluations. One reasoning step among a Flow's other steps, with its model, tools and answer contract, is the Flow's inline agent → `uipath-maestro-flow`.
4. Step is deterministic code with no UI and no LLM, invoked as a unit by other components → `uipath-functions`. If the same logic lives inside an RPA project as C#, keep `uipath-rpa`.
5. Step is a sequence of HTTP calls with no UI → `uipath-api-workflow` when standalone; `uipath-rpa` when it lives inside an RPA project.
6. Step coordinates other components: lightweight, event-driven, minutes-long → `uipath-maestro-flow`; long-running with human lanes and gateways → `uipath-maestro-bpmn`; case-centric with stages and SLAs → `uipath-maestro-case`.
7. Step is a user-facing screen → `uipath-coded-apps`.
8. Step trains or deploys an extraction model → `uipath-ixp`; the workflow that *uses* the model stays with its own skill.
9. Still ambiguous between `uipath-rpa` and anything else → `uipath-rpa`.

## Common Combinations

| Shape | Example | Level | Components — type (role): skill | Applications |
|---|---|---|---|---|
| One skill, one UI application | Excel rows keyed into a web form | component genome | RPA process: `uipath-rpa` | Excel, the web application |
| One skill, no UI application | API polled, mail sent on change | component genome | RPA process (coded steps for polling and mail): `uipath-rpa` | REST API, mail server |
| Several skills, no UI application | AI-assisted review | process genome | Flow (glue): `uipath-maestro-flow`; Agent (classifier): `uipath-agents`; Coded app (review screen): `uipath-coded-apps` | data through connectors or APIs |
| Several skills, several applications | Invoice processing | process genome | BPMN process (orchestrator; human validation designed with `uipath-human-in-the-loop`): `uipath-maestro-bpmn`; RPA process (mailbox intake, Document Understanding extraction, ERP posting): `uipath-rpa`; Agent (exception triage): `uipath-agents` | mailbox, ERP; Platform Dependencies: exception queue, credential assets |
