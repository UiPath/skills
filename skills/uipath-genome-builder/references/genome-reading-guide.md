# Genome Reading Guide — what each part of a genome means to the build

The reading contract of a genome: what execution takes from each section, the Transactional Shape, the Source Map, a UiPath source and the Build With skills. The genome is written by `uipath-planner`, whose format guides hold the writing rules; this guide holds only what a build reads, so it is read by section, as § Read Plans and the execution guides point into it. The genome is read-only: anything it gets wrong is a `uipath-planner` edit, then re-execution.

## Levels and Files

1. **Component genome** — one buildable project (RPA process, Flow, BPMN, agent, API workflow, coded app, function, case plan): `<slug>-genome.md`. **Process genome** — two or more projects: `<slug>-genome.md` plus `<slug>-genome/<component-slug>-genome.md` per component. The preamble comment `<!-- UIPATH-AUTOMATION-GENOME: component|process | … -->` names the level.
2. **A process genome's Components table links every component genome** in its Genome column; execution finds the components only through those links. A component inside a process carries a `Part of:` line linking back.
3. **Test components share one test project.** Every test component of a process (a group of test cases over data rows for one business area) lives in the single test project `<ProcessName>.Tests`, with one configuration for constants. Each group keeps its own component genome, so the process genome lists it as a component, but Deployment counts one test project and each group's Type cell reads "Test-case group in project `<ProcessName>.Tests`". Never build one test project per business area.
4. **A library component is a project of its own**, published to a feed and installed in its consumers as a package; it is never a project of the solution, and only the user's Library layout answer folds its workflows into a consumer. When several components run the same behaviour and the genome holds no library for it, the Shared steps question offers one.
5. **Detail lives at the lowest level that owns it**: component steps, rules, handlers and criteria in the component genome; what spans components — process map, handoffs, shared platform dependencies, the transactional shape's flows, cross-cutting rules, end-to-end criteria, deployment — in the process genome.
6. **File slugs** (open-items files, report names): split CamelCase on capitals, lowercase, hyphens for spaces, strip other characters — "InvoiceIntake" → `invoice-intake`.

## Design Links

Two optional blockquote lines after the blueprint blockquote; each is written only when its document exists:

- **`> Designed in:`** followed by a markdown link to the SDD — the genome was authored from that agreed SDD. The SDD's decisions — the split and queue design, the implementation mode, the package pins, the refactor answers — are recorded in the sections that hold them (Transactional Shape evidence, Deployment, Configuration Questions defaults) and are read as answered. The genome restates the SDD's products and projects and never contradicts them.
- **`> Map binding: <snapshot id>`** — the genome derives from that Map of Work snapshot. Each step, rule, exception and decision a Map record holds ends with the record's id in square brackets (`[RULE-012]`). The Map's schema and records belong to the Cartographer MCP; the genome cites ids only.

## Sections

**Every section is present.** A section that does not apply carries its stub line, never an omission: a stubbed Platform Dependencies needs no resources; a stubbed Interface runs unattended with no arguments; a stubbed Configuration Questions has no open values — the scaffolding questions are still asked; a stubbed Transactional Shape (`Not transactional: …`) means no split questions. **`*[Inferred]*`** marks a line the writer interpreted; it is built as written and named in the report when a criterion rests on it.

### Build With (component) / Components (process)

One skill per row from § Build Skills; Build With (or Components) precedes Workflow (or Process Map). Producer and consumer are roles of the Transactional Shape, never Type-cell words: a split may turn one `uipath-rpa` component into several `uipath-rpa` projects and the skill does not change. Solution packaging is never a row; Deployment names it with `uipath-solution`.

### Platform Dependencies

Every Orchestrator or Integration Service resource the automation touches, with type and purpose; an extracted genome keeps the source's resource names.

- **One credential asset per login account**, named after the account or persona, with its environment or tenant. The asset holds the secret; a password, token or secret value never appears in a genome, a data file or a report, and the account identity is never dropped with it.
- **Identifiers are not credentials.** A client id, tenant id, service URL or mailbox address is a Text asset (or configuration value), one per value, even when the source kept it in its credential vault: a credential's secret half cannot be read back as text without a conversion the workflow analyzer rejects at build.

### Interface (component)

Inputs, outputs and side effects, named by contract without the source's direction prefixes. Inside a process genome it is the contract the Handoffs table relies on.

- **Library component:** one table per public workflow, `Argument | Direction | Type | Description`, the Type the one the rebuild gives the argument; consumers are authored against it before the library packs. A workflow over the analyzer's argument cap (20) carries its optional switches in one options object — one In argument with its own `Field | Type | Default | Description` table.
- **Test component:** the row schema per test case, separately from the constants in the project's configuration; credentials as an asset name per row. Each case names its data set with its row count and where the source keeps it: a data set kept in a store is the case's data source (the project's test-data entity filtered on the data set's name); one shipped with the project is a variation file in the owning skill's format, named after the case. A case with no data set takes its values from configuration constants.

### Configuration Questions

`N. {Question}? ({setting | constant}; default: {value})`. A **setting** differs between environments (hosts and URLs, mailboxes and recipients, shares and paths, credential, queue, bucket, asset and Data Fabric entity names, schedules, language models) or must change without a new version; a **constant** is the same everywhere and a change to it is a change to the automation (thresholds, limits, retry counts, message texts). The kind decides where execution's Settings store answer puts the value. A grouped question names every key it holds; "required: empty ends the run" means the build guards the empty value. The genome never writes the questions execution asks itself — scaffolding choices and the split questions. A value the genome states as a fact in a step, rule or handler is built as written, never asked.

### Workflow (component) / Process Map (process)

- `N. **{Step name}** (input: …; output: …)`; the number keys the step's row in the Source Map's step table, the bold name heads its Business Rules and Error Handling entries. `###` headings group steps per entry point; steps several entry points share are written once and each entry point's last step names the step it continues into.
- A step that calls an automation the source does not hold names it by what it does; the callee is a Platform Dependency the rebuild calls but does not build.
- A **test component** lists one step per test case (`N. **Test case: <title>**`), its assertions named in the substeps; a **library** lists one step per public workflow — independent entry points, not one execution.
- **Composite UI interactions carry their full contract** — type-ahead pick, menu or tree path, option list, find-row-then-act, keystrokes to the focused element: what is typed, how the suggestion or option is matched (equals / contains / nth), which key confirms, each path level, the row rule. Execution builds each contract as a pattern (ui-target-migration-guide § Composite interactions).
- A substep's "confirm …" is a post-condition of the action before it, built as that action's verification.

### Business Rules, Error Handling

Grouped under `### Step N: {name}` (or a heading naming several steps), cross-step rules under `### General`, shared failure handling under `### Global`; a step entry exists only where that step's handling differs from Global. Each handler states the failure, the outcome and the level that handles it.

### Handoffs (process), Deployment (process)

Handoffs: one row per edge between components — mechanism, data passed, failure behaviour; component Interfaces agree with it, and every flow of the Transactional Shape cites the row that carries its items (an intra-component row when a flow's two phases sit in one component). Deployment: packaging, entry points and triggers, folders or environments, each library with its feed apart from the solution's projects, exactly one test project and one Test Manager test set per test component.

### Acceptance Criteria

A numbered list; the report's verdicts cite each criterion by its number. A criterion whose outcome rests on a language model's answer takes one of three forms, each verified as it says: (1) it states the answer — checked with a supplied or recorded answer, testing the build, not the model; (2) it states an invariant that holds whatever the model answers; (3) it gives an input whose right answer is computed outside the model, checked over several runs — a miss is a finding on the model, never on the build.

## Transactional Shape

The section **describes** per flow how items are handled today and how the roles could be divided; it asserts no split, store, template or unit — those are the split questions' answers (transactional-execution-guide). The behaviour in Business Rules, Error Handling and Acceptance Criteria is owed whatever the answers.

**Layout.** A `**Flows:**` line lists every flow (`Flow 1 — {unit}: {producer} → {consumer} (Handoffs row n)`, chains and independent flows named), then one `### Flow N` block per flow: **Unit of work** (the item, its reference, volume), **Alternative units of work** (each with its fit condition, or "none"), the **As-is** table (Produced by, Consumed by, Item store, Coordination, Item kinds, Step groups), the outcomes table, the **Split options** table (rows A, B, C per unit of work and per alternative unit, each with Requires and Changes cells), **Evidence**, **Configuration**, **Traceability**. A component inside a process carries, per flow it takes part in, a `Role:` line, the As-is rows of its role and `Split options: per the process genome, Flow N.`

**The options.**

- **A keeps the items in the job**: one job takes its items end to end on one runner — the REFramework's direct mode, or a plain loop over an in-process list — with no Orchestrator queue.
- **B and C keep them in an Orchestrator queue**, which items need whenever they are shared across jobs (several runners, retries or postponements across runs, another process reading them after the run), with exactly **one queue per unit of work** shared by any number of producers, consumers and runners. **C keeps both roles in one process**: one entry point and one trigger, every job produces behind a once-guard and then consumes. **B separates them** into processes with their own triggers; two entry points of one project are B, never C.
- When a flow's producer and consumer are **different genome components**, B is their as-is, and A or C materialises one project holding both components' roles (under C with the queue between them kept); the Components table is not changed.
- The **number of runners** is a deployment setting of each resulting process, never an option. A source's own coordination stores (parent queue, ledger, lock) are kept only when the chosen split still needs them and the user keeps them. A source that keeps its work list in a **database the process owns** may keep it as the store under B and C.
- `Split options: none — the consumer (or producer) is outside this genome` means execution builds only the side the genome holds and asks no split question for that flow.

**Roles.** A consumer is always an RPA process (`uipath-rpa`). A library, a test-case group, a Flow, BPMN process or Case, an agent, an API workflow, a coded app or a function is never a consumer; a genome whose As-is names one has a defect: report it.

**Outcomes.** Three rows always — **Success**; **Business exception** (the Business Rules that reject an item, named by step: no retry, recorded with the reason, the run continues); **System exception** (every other failure: applications reopened, the item retried the stated number of times, then recorded as failed; the run stops after the stated number of consecutive failures — 0 and 1 included, never the framework's defaults). A fourth, **Postponed**, only when the source puts an item back for later without counting a failure: in a queue the item returns with a postpone time and its attempt count untouched; past the limit it is a business exception.

**Step groups.** Every consumer step is once per run (open and sign in, read configuration and reference data), per item (the business steps) or at the end (close, summary); a producer's steps are never in the consumer's once-per-run group, and in a chain the steps that create the downstream items are per-item steps of the upstream consumer.

**Levels and chains.** Items that expand into children (a mail into attachments, a file into rows) are one flow with nested levels: the unit of work is one level, the other an Alternative unit of work, and how the parent's end-of-parent work learns its children are final is stated in the Split options cells. A chain (the consumer of Flow N produces Flow N+1) carries the upstream reference on the downstream item; when the automation creates the downstream item, its creation is a per-item step of the upstream item, retried with it, so the downstream reference makes a second creation a duplicate the store refuses.

**Derivation table** — the signals the recommended split option is prepared from:

| Signal in the As-is or Evidence | Split options it enables or excludes |
|---|---|
| One job works items end to end, nothing else touches them, a rerun is harmless | A viable |
| Several robots run the same process on the same items; an item must survive a run failure; a postponement or retry crosses runs | A excluded; B and C viable — C while both roles share cadence, machines, credentials and owner |
| Another process reads the items after the run | A excluded unless the job writes a per-item record the reader can use |
| Population and consumption differ in cadence, machines, credentials or owners | B favoured; C excluded |
| Several independent sources feed the items | B with one producer per source, or A or C reading every source in its producer steps |
| Item kinds need different applications, machines, attempt limits or SLAs | B with one consumer and one queue per kind; otherwise one consumer with a route step |
| The source guards population with a lock or a ledger | C's shape; C keeps a once-guard in its place (a unique reference the queue refuses twice, or the kept ledger) |
| Work happens once per parent when its children are final | at the child unit: each option names how that work learns its children are final; at the parent unit: it is the transaction's last step |

## Source Map

Present only in an extracted genome; its presence makes the execution a migration (and, for a UiPath source, a refactor).

**Contract rows** (process genome, or the single component genome): **Source framework** (the framework name as read-plan-guide.md § Source Frameworks spells it, and its version) · **Source export** (root path and identity: database or tenant, export date, process count) · **Steps** (the step table, in every component genome) · **Checkpoints** (per test-case step and per library step a test component calls: source step id, what is asserted, the expected value or its data column, whether a screenshot was captured — one assertion and one evidence artifact each) · **Not covered** (live behaviour no step is built from: left out of the build unless translated by a `uipath-planner` edit) · **Inventory counts** · other rows (dead code, excluded objects, unresolved invocations, inferred intent, findings).

**The step table**, under `### Steps`: `Step | Source objects | Data sets | Captures | Notes`, one row per Workflow step keyed by its number.

- **Source objects** — the objects whose behaviour the step implements, primary first: a framework source as `` `Name` (id) `` or `` `Name` (id, {locator}) ``; a UiPath source as the workflow's project-relative path, a test case with its `testCaseId`.
- **Data sets** — the data sets the step's own objects read, or `none`.
- **Captures** — the screen captures the source takes inside the step; the rebuild's evidence is checked against it.
- **Notes** — free text no check reads.

Recognition data (locators), data rows and process inventories never sit in or beside the genome: execution re-derives them from the export at its migration preflight. A genome shared without its Source Map is built with placeholders or live capture, never migrated.

**Source values.** An empty value in the rendering the genome was extracted through is "not shown", never "not set". Before a group builds on a step, every fact of these kinds that the step cites is checked in the source: comparison literals, operators and case rules; counts, attempts and loop bounds; lengths, positions and occurrences; waits, timeouts and a check's budget; set or typed; flags that change control flow (continue on error, a failure tolerated or logged as a pass); formats; values bound to a built-in; a parameter's unit, default and override order; log texts. Where the source and the genome disagree, the build follows the source and reports the difference.

**Source defects.** A verified defect is written at its step as `**Source defect:** {what the source does} … Evident intent: {what it was meant to do}`. The genome says which behaviour the rebuild follows: the evident intent when the source states it; otherwise the source's behaviour, unless a `User ruling ({date}): …` line at the step says otherwise. A process genome indexes every defect in one table, `Defect | Component step | Rebuild follows`. A defect only the source runtime's internals reproduce follows the evident intent.

## UiPath Source

What a build reads from a UiPath source the Source Map names: its UI targets, its test data and its deployed state.

**Identity** (as the Source Map carries it): the project path, `projectId` and `projectVersion` (a solution's `SolutionId` with each project's `projectId`); a step by its workflow's project-relative path; a test case by path plus `testCaseId`, a checkpoint by its activity `IdRef`; a data set by its `.variations/<Case>.json` path; the deployed state by folder and date read; the runtime by its job-history window.

**UI targets** — carried over, never translated:

| Where | What | At execution |
|---|---|---|
| `.objects/**` (Object Repository store) | applications, screens, elements with their descriptors | copy the store into the rebuilt project, or consume the source UI library package; link activities by element reference; confidence `high` |
| `uix:TargetAnchorable` / `uix:TargetApp` inline in `.xaml`, keyed by workflow and activity `IdRef` | targets never promoted to the Object Repository | promote when the genome makes the workflow a library activity; otherwise carry inline; confidence `high` |
| `Descriptors.<App>.<Screen>.<Element>` in coded workflows | coded references into the same store | the store copy covers them; the generated file is regenerated by the first validate |
| Legacy `Selector` attributes on classic activities | classic strict selectors | confidence `medium`; rebuilt through the owning skill's legacy guidance |

**Test data:**

| Where | What | Data catalog at execution |
|---|---|---|
| `.variations/*.json`, registered in `project.json` → `designOptions.fileInfoCollection[].dataVariationFilePath` | data rows per test case, keyed by argument name | one recordset per file, rows as-is |
| Test Data Queues, Data Service entities | external data sources | Platform Dependencies rows, not rows |
| `GetRobotCredential` / `GetRobotAsset` / `GetCredential` asset names | credentials and configuration in Orchestrator | asset names kept; no secret written |
| Default values on test-case arguments | single-row data | the recordset's only row |

A variation field that looks like a password (`*password*`, `*pwd*`, `*secret*`, `*token*`) is redacted and reported; it becomes a credential asset name.

**Deployed state is source: what runs is the process.** Each Orchestrator process binds one package version, can override any binding of the package and owns its triggers. The binding a process overrides is the value that runs — the override is the default of an environment-bound value; two processes of one package bound to different versions run different code, each described from the version it runs. A connection's identity is the account it signs in as. An event trigger is read from the deployed state, never inferred from the entry point's event arguments. The job history says whether an entry point is used and what a fault does on real data. When the deployed state was not read, the Source Map says so and a trigger the package does not hold is `*[Inferred]*`.

## Build Skills

The only skill names a Build With row may carry: `uipath-rpa`, `uipath-maestro-flow`, `uipath-maestro-bpmn`, `uipath-maestro-case`, `uipath-agents`, `uipath-functions`, `uipath-rules`, `uipath-api-workflow`, `uipath-coded-apps`, `uipath-connector-builder`, `uipath-ixp`, `uipath-process-mining`, `uipath-mcp-servers`. A row naming any other skill — the retired `uipath-rpa-workflows`, `uipath-coded-workflows` and `uipath-coded-agents` included — or one the host lacks does not resolve: report it as a genome defect for `uipath-planner`, and type the step with the decision tree below to say which skill the fixed row would name. Operate-only skills (`uipath-platform`, `uipath-tasks`, `uipath-test`, `uipath-admin`) belong under Platform Dependencies, never in a build group. A human approval or validation checkpoint is built by the containing component's skill; only inside a Flow is it designed with `uipath-human-in-the-loop`.

**Decision tree** — the product that runs each kind of step, used when a refactor types the steps to choose a target:

1. Interacts with a screen, or with what only a robot's machine reaches (Excel and Office files, local or network files, an on-premises database, desktop mail, a terminal) → `uipath-rpa`.
2. Reads or writes Excel, mail, PDF, files, or calls an Integration Service connector activity from a workflow → `uipath-rpa`.
3. Reads fields from semi-structured documents → a document-extraction step of the component that uses it; training or deploying the model → `uipath-ixp`.
4. Decides by a threshold, eligibility or routing table the business maintains → a decision table of its own → `uipath-rules`.
5. Needs an LLM to decide, classify, summarize or converse → `uipath-agents` when the agent is a component of its own; one reasoning step among a Flow's steps is the Flow's inline agent → `uipath-maestro-flow`; a fixed generation step with no decision is an LLM activity of the component that runs it.
6. Deterministic code with no UI and no LLM, invoked as a unit by other components → `uipath-functions`; the same logic inside an RPA project as C# stays `uipath-rpa`.
7. HTTP or connector calls with no UI, to systems the cloud reaches → `uipath-api-workflow` when standalone; `uipath-rpa` inside an RPA project.
8. Waits for a person: inside one RPA process, an Action Center task in a long-running workflow → `uipath-rpa`; inside a coordinator, that coordinator's human task.
9. Coordinates other components → `uipath-maestro-flow` (a pipeline with branches), `uipath-maestro-bpmn` (formal gateways, events, timers, subprocesses) or `uipath-maestro-case` (stages with SLAs) — only for coordination one component cannot hold: state that outlives a run, parallel branches, several automations that run on their own, per-step visibility end to end.
10. A user-facing screen → `uipath-coded-apps`.
11. Data several components share is a Data Fabric entity: a Platform Dependency, never a step's skill.
12. Still ambiguous between `uipath-rpa` and anything else → `uipath-rpa`.
