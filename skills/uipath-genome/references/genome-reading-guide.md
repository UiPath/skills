# Genome Reading Guide — what a genome's sections mean at build

The genome is read-only at build: the build reads it as written, and a gap in it goes back to `uipath-planner` as an edit, never into the file. A section holding its stub line does not apply, and the build makes nothing for it.

## Two Levels

| Level | File | Scope |
|---|---|---|
| **Component genome** | `<slug>-genome.md` | One buildable project (RPA process, Flow, BPMN, agent, API workflow, coded app, function, IXP model, decision table, case plan) |
| **Process genome** | `<slug>-genome.md` plus `<slug>-genome/<component-slug>-genome.md` per component | Business process realised by two or more buildable projects |

Rules:

1. **One component genome is one buildable project**, except test components: every test component of a process (a group of test cases over data rows for one business area) is built into a *single* test project, `<ProcessName>.Tests`, with one configuration for constants. Each group keeps its own component genome (Interface, rules, criteria) and its own folder in that project; never build one test project per business area. A process genome whose components are the groups of one UiPath test project, plus one shared component for its execution template and helpers, rebuilds that one project.
2. **A component genome's `Part of:` line links its process genome**: the build takes the component's source framework from that process genome. A component reached through a process genome's links is inside it, with or without the line.
3. **Detail lives at the lowest level that owns it.** The build reads a component's steps, rules, error handling and criteria in its component genome, and what spans components (process map, handoffs, shared platform dependencies, the transactional shape, cross-cutting rules, end-to-end criteria, deployment) in the process genome.
4. **Every section is present**: a section the build cannot find is an edit for `uipath-planner` ([execution-guide.md § 1.1](execution-guide.md)), never a section to infer.
5. **A genome whose preamble names `uipath-genome`** instead of `uipath-genome` builds here.
6. **Shared behaviour is one library component**: a project of its own, published to a feed and installed in its consumers as a package, never a project of the solution (§ Deployment). The build packs it before its consumers, and each consumer's steps call it as they call any library; only the Library layout answer of execution's configuration questions folds it into a consumer. What one or a few activities do (close an application, append a line to the run's log, send one mail) stays a step of each consumer.

## File Naming and Location

- Slug: split CamelCase on capitals, lowercase, hyphens for spaces, strip other characters. "Invoice Processing" → `invoice-processing`; "InvoiceIntake" → `invoice-intake`; "Email Triage & Routing" → `email-triage-routing`.
- A process genome's components are at `<process-slug>-genome/<component-slug>-genome.md`.

## Build With and Components

One skill per row names the build skill that owns each component. **The build finds a process genome's components only through the Components table's Genome links.** A test component's Type cell names the shared test project.

- A Type cell names the component type (`RPA process`), never a role: a split chosen at build may turn one `uipath-rpa` component into several `uipath-rpa` projects with the skill unchanged.
- **A human approval or validation checkpoint** inside a Flow, BPMN process, Case plan or agent is built by the containing component's skill; a Rationale naming `uipath-human-in-the-loop` means the builder consults it for the gate design.
- **Solution packaging** (`.uipx`) is under Deployment with `uipath-solution`, never a Build With row.
- **A retired skill name** — `uipath-rpa-workflows`, `uipath-coded-workflows`, `uipath-coded-agents` — builds through `uipath-rpa`, and the report names the row for a `uipath-planner` edit.
- **A skill the host lacks**: [build-guide.md § Start](build-guide.md) (name it and stop).

## Platform Dependencies

Every Orchestrator or Integration Service resource the build declares or reads: queues, assets, credentials, storage buckets, connections, folders, triggers. The build declares each under the name the genome gives it.

**Credentials: one credential asset per login account**, named after the account or persona, with its environment or tenant; never collapse several accounts onto one login. The genome and the data rows name the asset — a password, token or secret value never appears in a genome, a data file or a report. A secret crosses no component boundary: an Interface argument, a Handoffs row and a start argument carry the asset's name, and the component that uses the secret reads it in the scope that uses it, unless a connection holds the secret (an Integration Service connection). A secret with no account behind it (an API key, a token) is a Secret asset. Execution-side declaration: [execution-guide.md § 2.2](execution-guide.md), credentials; naming from a source's accounts: [source-migration-guide.md § Credentials](source-migration-guide.md).

**Identifiers are not credentials.** A client id, tenant id, service URL or mailbox address is a Text asset (or configuration value), one per value, even when the source stored it in its credential vault: a consumer cannot read a credential asset's secret half back as text without a conversion the workflow analyzer rejects.

**Values the platform keeps per environment are assets** (an environment variable, a global value), of the type their values take — Text, Integer, Bool, Secret, or a credential asset for an account. A component whose type reads no assets keeps such a value in the variable its owning skill provides.

## Interface

Inputs, outputs and side effects: the contract the Handoffs table relies on. Each argument carries its contract name without the source's direction prefix (`in_`, `out_`, `io_`); a contract name that is a Visual Basic or C# reserved word, or a .NET namespace or type name, breaks one expression language's expressions and is renamed as an Interface deviation. A `uipath-maestro-case` component whose case a Case Management SDD designed names that SDD's path, relative to the genome: the build hands that SDD to `uipath-maestro-case` unchanged, and the case is built from it, never redesigned.

**Library components** carry one table per public workflow, `Argument | Direction | Type | Description`: the type the rebuild gives the argument, its default and value format, and the conventions consumers rely on. Consumers are written against this table before the library packs. A workflow over the analyzer's argument cap (20) takes its optional switches and values in one options object — one In argument with its own table (`Field | Type | Default | Description`).

**State kept between calls lives in the consumer.** A library workflow starts each call from its declared defaults and a library project holds no global variables or constants, so state one action stores and another reads (a value, an attached application, its own instance of another component) crosses each call as an argument: Out from the workflow that produces it, In to each that reads it, In/Out where one changes it. A coded library's static field holds none of it. An attached application crosses as the application handle the owning skill's public-workflow contract has workflows return and accept. An instance per caller is held by each caller; one instance per run is held by the run's entry workflow and passed to every caller.

**Test components** list each test case's row schema (the fields that vary per scenario) apart from the test project's configuration constants, with credentials as asset names per row. Where each case's data set is built: [test-execution-guide.md § Test data](test-execution-guide.md); a case with no data set takes its values from configuration constants.

## Configuration Questions

Each question names its kind, `setting` or `constant`, before its default; the Settings store answer places each kind ([configuration-questions-guide.md](configuration-questions-guide.md)). A setting differs between environments or changes without a new version; a constant is the same in every environment. A source's own configuration store is not a Platform Dependency of the rebuild.

Every other value is a fact, built where the genome writes it (the Workflow substep, Business Rule, Error Handling entry, Transactional Shape outcome, Interface or Target Applications that uses it); changing a fact is a genome edit, not a configuration answer.

A grouped question names every key it holds, and execution maps each key. A question saying "required: empty ends the run" marks a value whose emptiness changes the flow instead of failing, and execution guards it. Execution asks its own questions (scaffolding, and the split questions when the Transactional Shape is not the stub); the genome holds none of them.

## Workflow

Each step `N. **{Step name}**` keys its row in the Source Map's step table by number and heads its Business Rules and Error Handling entries by name. A `###` heading is one entry point; a shared step under its own heading is built once, and each entry point continues into the step its last step names. A step that calls an automation the source does not hold calls a Platform Dependency the rebuild does not build. Substeps carry the fields, conditions, validations and transformations.

**Test components** build one test case per numbered step (`N. **Test case: <title>**`), its substeps the case's steps and assertions. A **library** component's steps are its public workflows: independent entry points, not one execution.

**Composite UI interactions carry their full contract** in the substep (what is typed, how the option is matched, which key confirms, each path level, the row rule); execution builds each as a pattern ([composite-interactions-guide.md](composite-interactions-guide.md)).

**A substep in a window an action opened names that window**; the build targets that window.

**A source's workaround for its own platform is not behaviour.** The build builds the result the step states, unless a later step reads what the workaround leaves behind.

**Business Rules and Error Handling** fire at the step their `### Step N` heading names (`### General` across steps, Error Handling's `### Global` for shared failures, overridden only where a step entry exists). An Error Handling entry gives the failure, the outcome and the level that handles it. A substep's "confirm …" is built as the verification of the action before it, not a separate check.

## Acceptance Criteria

The execution report's verdicts and a comparison of two runs cite each criterion by its number. **A criterion resting on a language model's answer** is checked as written: with a supplied or recorded answer (it tests the build, not the model), as an invariant whatever the model answers, or over several runs on an input whose right answer is computed outside the model — a miss there is a finding on the model, never on the build.

## Complexity

`simple | medium | complex`. A process genome's own level is the one the build reads, not its components'.

## Ambiguity Marker

A line ending `*[Inferred]*` is the writer's best interpretation where the source or the description was unclear. The build builds the line as written and lists every `*[Inferred]*` line it relied on in the report.

## Process Genome Sections

### Handoffs

One row per edge between components — mechanism, data schema passed, and what happens when the receiving side fails — is the data contract: every component Interface agrees with it, and every flow of the Transactional Shape cites the row that carries its items. A row marked intra-component carries the edge between two phases of one component that exchange items through a store. A human task a component creates (an Action Center task) keeps its row.

### Deployment

Packaging, entry points, triggers and target folders or environments; the buildable projects are named explicitly. A library is listed with the feed it is published to, apart from the solution's projects. With test components, Deployment names exactly one test project and one Test Manager test set per test component.

## Design Links

`> Designed in: [{SDD title}]({relative path to the SDD}) · sdd-sha256 {SDD_FINGERPRINT}` ties the genome to the SDD it derives from. The build reads no SDD content for it: the SDD's decisions are already in the sections that hold them and are read as answered. The build does not compare the fingerprint: `uipath-planner` keeps a designed genome current ([execution-guide.md](execution-guide.md) § 1.1).

## Source Map

Extracted genomes only: where every part of the genome came from. A genome without its Source Map is built but not migrated — placeholders or a live capture, and the report says so. A Source Map that names the export but not the per-step objects has lost the migration: the build cannot find the export's locators and rows, and it says so in the report instead of shipping invented data.

**The step table** (`### Steps`, every extracted component genome), one row per Workflow step keyed by its number:

| Step | Source objects | Data sets | Captures | Notes |
|---|---|---|---|---|
| 3 | `Submit_Order` (482113, lines 29–40) | `Order_Rows` (1207) | 2 | The confirmation is sent by `Send_Confirmation` (529077), a step of its own; called by the run's root `Order_Main` (310045) |

1. **One row per Workflow step**; a test component's steps are its test cases.
2. **Source objects** are the objects whose behaviour the step implements, primary first: a rebuild that keeps the source's names names the step's file or workflow after it. A framework source's object is `` `Name` (id) `` or `` `Name` (id, {locator}) `` — the id identifies the copy; a UiPath source's is its project-relative path, a test case with its `testCaseId` ([refactor-guide.md § Provenance](refactor-guide.md)).
3. **Data sets** are the data sets the step's own objects read, or `none`.
4. **Captures** is the number of screen captures the source takes in the step; the build checks the rebuild's evidence against it.
5. **Notes** is free text no check reads.

**Unused parts.** A kept workflow nothing invokes is built like any other step. Parts in the `Not covered` or `Unused` row are left out of the build unless translated first.

**The Source Map is the migration contract.** The build regenerates every catalog it needs — UI target locators, data rows, process inventory — from the export at its migration preflight ([source-migration-guide.md § Migration preflight](source-migration-guide.md)), into the build's working folder, never beside the genome. Rows the build reads:

| Row | What the build does with it |
|---|---|
| Source framework | `UiPath` makes the build a refactor; any other framework name, spelled as its migration pack's README spells it, makes it a migration |
| Requested change | the user's words and decisions by topic; [refactor-guide.md § Refactor questions](refactor-guide.md) rule 2 takes them as the user's answers |
| Source export | the export's root path and identity (database or tenant, export date, process count), so a moved copy is recognised |
| Steps | the step table above |
| Checkpoints | per test-component step (and per step of a library a test component calls): the source's checkpoints. The build makes one assertion and one evidence artifact per checkpoint and the result parity table from them ([test-execution-guide.md § Result parity](test-execution-guide.md)) |
| Not covered | live behaviour no step is built from |
| Inventory counts | what the export holds and the genome covers |

## Source values

A genome is extracted through a rendering of the source and inherits every gap in it: a rendering can hide a typed value and an extraction can paraphrase one. An empty value in a rendering is "not shown", never "not set". The build checks every fact of these kinds the genome cites against the source object before a group builds on it (its migration preflight), and follows the source where the two disagree:

1. **Comparison literals, operators and case rules** — contains / equals / starts with, case-sensitive or not, line breaks ignored or not, whitespace normalised or not, a pattern that must match the whole text or one that searches it — spelled exactly, spacing and punctuation included.
2. **Counts, attempts and loop bounds**, and whether the loop tests before or after its body.
3. **Lengths, positions and occurrences** in text operations (a cut to 20 characters, the second `|`-field).
4. **Waits, pauses and timeouts** in the unit the source states, and a check's budget: its own timeout, or, for a check or an action with no timeout of its own, the framework's default budget the source guide names (a source check that waits its framework's default is not an activity waiting the activity's default).
5. **Set or typed:** whether a field is set (replaced) or typed into (appended, key by key).
6. **Flags that change control flow** (continue on error, a do-while, a skip switch, a failure the source tolerates or logs as a pass, a call made from a failure route). A check whose failure the source logs as a pass or ignores is a decision or an optional wait, not a hard check, and a check that passes when its target is absent asserts absence.
7. **Formats** a date or number is typed or compared in (a mask, a pattern, one part of a date per segment): the format is part of the value.
8. **Values bound to a built-in** (the run date, the user's folder), computed at run time — never the stored default a same-named project variable carries.
9. **A parameter's unit, its default, and which of two filled parameters overrides the other**, read from the source's own documentation of that parameter before they are called unknown.
10. **Log texts** of each step, with their literal wording and variable substitutions.
11. **Which file and which field**: the kind of each file the process reads or writes, by its extension, and which of several dates or fields a filter, sort or window uses.

## Source Defects

An extracted genome states a source's defect at the step, rule or handler where the behaviour lives, as `**Source defect:** {what the source does} … Evident intent: {what it was meant to do}`. A process genome indexes every component's defects under Error Handling and Recovery (`Defect | Component step | Rebuild follows`), and the defect's Source Map row names the objects and lines that prove it.

- The rebuild follows the evident intent when the source states that intent. When only the step's purpose shows it (the intent marked `*[Inferred]*`), the rebuild carries the source's behaviour unless the user rules otherwise; a `User ruling ({date}): …` at the step, cited by the index row's Rebuild follows cell, decides.
- A defect whose result only the source runtime's internals reproduce cannot be carried: the rebuild follows the evident intent.
- An open ruling builds the option the genome names, marked `*[Inferred]*`, until the user rules.
- An **unresolved** behaviour (semantics nobody documents) builds the reading the genome marks `*[Inferred]*`.
