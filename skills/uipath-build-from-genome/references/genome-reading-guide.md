# Genome Reading Guide — what a genome's sections mean at build

`uipath-planner` writes every genome; `build` reads it. This guide states what each section the build relies on carries and how the build reads it. The genome's mechanical shape — the marker, the sections and their order, the step and question forms, the tables and the stub lines — is checked by `scripts/check-genome.mjs` before the build asks anything (SKILL.md § Check); what the checker cannot see, the meaning of each section, is stated here. A gap in the genome goes back to `uipath-planner` as an edit, never into the file.

## Two Levels

| Level | File | Scope |
|---|---|---|
| **Component genome** | `<slug>-genome.md` | One buildable project (RPA process, Flow, BPMN, agent, API workflow, coded app, function, IXP model, decision table, case plan) |
| **Process genome** | `<slug>-genome.md` plus `<slug>-genome/<component-slug>-genome.md` per component | Business process realised by two or more buildable projects |

Rules:

1. **One component genome is one buildable project.** Two or more projects, or one coordinator plus anything it invokes, are a process genome plus one component genome per project.
   - **Test components are the one exception to "one component = one project".** Every test component of a process (a group of test cases over data rows for one business area) lives in a *single* test project, `<ProcessName>.Tests`, with one configuration for constants. Each group keeps its own component genome (Interface, rules, criteria), so the process genome still lists them as components, but Deployment counts one test project, and each group's Type cell names it (§ Build With and Components). Never emit one test project per business area. A UiPath test project that is the whole source takes the same shape when it holds two or more groups: a process genome whose components are its groups, plus one shared component for the execution template and the helpers the cases share, which that project already holds; a single group is a component genome. The procedures the test cases of any other source share are a library component (rule 6).
2. **Component genomes inside a process carry the `Part of:` line** immediately after the blueprint blockquote, linking back to the process genome. Standalone component genomes omit it.
3. **Detail lives at the lowest level that owns it.** Component-specific workflow steps, business rules, error handling, and acceptance criteria are in the component genome. The process genome holds only what spans components: process map, handoffs, shared platform dependencies, the transactional shape (its flows, producers and consumers), cross-cutting rules, end-to-end criteria, deployment.
4. **Every section present, always.** A section that does not apply carries its stub line (§ Stub Lines), never an omission.
5. **The preamble routes to `uipath-build-from-genome`.** Every genome starts with the `<!-- UIPATH-AUTOMATION-GENOME: component|process | ... -->` comment and carries the visible blueprint blockquote after the one-liner. Both name `uipath-build-from-genome` as the skill that builds the genome, and the comment names `uipath-planner` as the skill that changes it. A genome written before the skill split names `uipath-genome`; it routes here, and the checker accepts it. Build With (component) or Components (process) appears before Workflow / Process Map, so the skill references come before the steps.
6. **Shared behaviour is one library component.** When several components run the same behaviour and the rebuild has to write it because no single UiPath activity performs it — run setup and cleanup, drive mapping, a mail or document-store client — that behaviour is one common library component, and each consumer's steps call it as they call any library. The library is a project of its own, published to a feed and installed in its consumers as a package; it is never a project of the solution (§ Deployment), and that is no reason to fold its workflows into a consumer; only the user's answer to execution's configuration questions folds one (Library layout). What one or a few activities do (close an application, append a line to the run's log) stays a step of each consumer.

## File Naming and Location

- Slug: split CamelCase on capitals, lowercase, hyphens for spaces, strip other characters. "Invoice Processing" → `invoice-processing`; "InvoiceIntake" → `invoice-intake`; "Email Triage & Routing" → `email-triage-routing`.
- Process genome components: `<process-slug>-genome/<component-slug>-genome.md`. Component slug from project name.

## Build With and Components

One skill per row: Build With (component) or Components (process) names the build skill that owns each component, with a rationale. **A process genome's Components table links every component genome** in its Genome column, as a markdown link to `<process-slug>-genome/<component-slug>-genome.md`: the build finds the components only through those links. In a process genome with test components, the Type column of every test component reads "Test-case group in project `<ProcessName>.Tests`".

- Build With lists only skills that produce a deployable artifact; skills that operate the platform (`uipath-platform`, `uipath-tasks`, `uipath-test`, `uipath-admin`) belong under Platform Dependencies, and the checker rejects them in Build With.
- A Type cell reads the component type (`RPA process`, never `dispatcher` or `performer`): producer and consumer are roles of the Transactional Shape, and a split chosen at build may turn one `uipath-rpa` component into several `uipath-rpa` projects with the skill unchanged.
- **A human approval or validation checkpoint** inside a Flow, BPMN process, Case plan or agent belongs to the containing component's skill; a Rationale naming `uipath-human-in-the-loop` means the builder consults it for the gate design.
- **Solution packaging** (`.uipx`) is not a Build With row: a process genome records it under Deployment with `uipath-solution`.
- **A retired skill name** — `uipath-rpa-workflows`, `uipath-coded-workflows` and `uipath-coded-agents` were folded into `uipath-rpa` — builds through `uipath-rpa`, and the report names the row for a `uipath-planner` edit. A row whose skill the host lacks is a blocking finding: name the skill, and build nothing that needs it.

## Platform Dependencies

Every Orchestrator or Integration Service resource touched: queues, assets, credentials, storage buckets, connections, folders, triggers. Each row names resource type and purpose. Extracted genomes keep the source resource name; authored genomes propose one.

**Credentials: one credential asset per login account**, named after the account or persona, with its environment or tenant. Scenarios often sign in as several accounts with different roles on different tenants; never collapse them onto one login. The asset holds the secret; the genome and the data rows name the asset — a password, token or secret value never appears in a genome, a data file or a report, and dropping the account identity along with the secret loses which role each scenario ran as. A secret crosses no component boundary: an Interface argument, a Handoffs row and a start argument carry the asset's name, and the component that uses the secret reads it in the scope that uses it, unless a connection holds the secret (an Integration Service connection). A secret with no account behind it (an API key, a token) is a Secret asset. Execution-side declaration: [execution-guide.md § 2.2](execution-guide.md), credentials; naming from a source's accounts: [source-migration-guide.md § Credentials](source-migration-guide.md).

**Identifiers are not credentials.** An application registration's client id and tenant id, a service URL or a mailbox address are Text assets (or configuration values), one per value, even when the source stored them in its credential vault: a credential asset's second half is a secret that a consumer cannot read back as text without a conversion the workflow analyzer rejects at build. The genome names them as Text assets; execution declares them the same way.

**Values the platform keeps per environment are assets.** A value the source platform holds outside the process and sets per environment — an environment variable, a global value — is one asset, named as the source names it, of the type its values take: Text, Integer or Bool, Secret for a secret, a credential asset for an account. When its value is open, the Configuration Question that asks it names the asset. A component whose type reads no assets keeps such a value in the variable its owning skill provides. A source's own configuration store is not such a value (§ Configuration Questions).

## Interface

Inputs, outputs, side effects. Mandatory content for a component inside a process genome (it is the contract the Handoffs table relies on). Standalone components may stub it: "Runs unattended with no arguments; outputs are the side effects listed in Workflow." Each input and output is named by its contract name, without the source's direction prefix (`in_`, `out_`, `io_`): `MailboxFolder`, not `in_MailboxFolder`. A contract name that is a reserved word of Visual Basic or C#, or a .NET namespace or type name (`To`, `Sub`, `Date`, `Type`, `Object`, `System`), takes a qualifier (`ToAddresses`, `KeyDate`, `SapSystem`): the expression language is chosen at execution, and such a name breaks the expressions of one of the two. The source argument is provenance and is in the Source Map. A `uipath-maestro-case` component whose case a Case Management SDD designed names that SDD's path, relative to the genome, as its build input: `uipath-build-from-genome` hands that SDD to `uipath-maestro-case` unchanged, and the case is built from it, never redesigned.

**Library components** (a project other components consume as a package) carry, instead of the three bullets, one table per public workflow: `Argument | Direction | Type | Description`. The Type is the one the rebuild gives the argument — a flag is a Boolean and a count a number, whatever text the source carried them in — and the description states the default and the value format (what a flag means, how a date is rendered, which side quotes a value), plus the conventions consumers rely on (naming, defaults, what a failed final check does). This table is the contract consumers are authored against before the library packs; every detail it omits becomes a question between two build groups. A workflow over the analyzer's argument cap (20) carries its optional switches and values in one options object — one In argument with its own table (`Field | Type | Default | Description`).

**State kept between calls.** A library workflow starts each call from its declared defaults, and a library project holds no global variables or constants, so state the source keeps from one call of its actions to the next — a value one action stores and another reads, an attached application or handle, its own instance of another component it calls — lives in the consumer and crosses each call as an argument: Out from the workflow that produces it, In to each that reads it, In/Out where one changes it. A coded library's static field does outlive a call, but as one value for every caller in the job and none inside an isolated invoke, and no Interface shows it, so it holds none of this state. An attached application crosses as the application handle the owning skill's public-workflow contract has workflows return and accept. The conventions name the holder and the work the source ran on its own — set-up before the first call, a close-down when the run ends, after a failure too — each a public workflow the holder calls at that point. An instance per caller is held by each caller — a process in its entry workflow for its whole run, passed to the workflows that call the library, and a calling library in its own Interface, since it holds nothing either; one instance per run is held by the run's entry workflow and passed to every caller, calling libraries included. A stored value no action changes is no state: it is a fact or a Configuration Question.

**Test components** (a group of test cases over data rows in the single test project) list the row schema per test case: the fields that vary per scenario, separately from the constants in the project's configuration. Credentials appear as the name of a credential asset per row, never as values. Each case names its data set — a single row included — with its row count and where the source keeps it, since the rebuild keeps it there ([test-execution-guide.md § Test data](test-execution-guide.md)): a data set kept in a store is the case's data source, the project's test-data entity filtered on the data set's name; one shipped with the project is a variation file in the owning skill's format, named after the case, whose fields stay within the analyzer's argument cap (above). A case with no data set takes its values from configuration constants.

## Configuration Questions

Format: `N. {Question}? ({setting | constant}; default: {value})` — every question names its kind before its default. An extracted genome asks only what the source leaves open — a value bound to the environment, missing from the export, a choice the source never faced, or read from the source's own configuration store; an authored genome asks every value the description gives or leaves open.

Every other value is a fact, written once where its reader looks: a value typed, posted, compared or checked, and a limit, length or format, in the Workflow substep or Business Rule that uses it; a wait, timeout, poll interval or attempt count in its step or that step's Error Handling; the item retry and consecutive-failure counts in the Transactional Shape's outcomes ([transactional-execution-guide.md § Shape Rules](transactional-execution-guide.md) rule 4); a switch a start argument sets in Interface; the application and a machine prerequisite (Excel installed) in Target Applications; a file the project ships in the step that uses it and the Source Map. Changing a fact is a genome edit, not a configuration answer.

**A setting depends on the environment.** Every Orchestrator connection the automation is deployed to is its own environment — dev, UAT, prod — and the build is often made on another machine and tenant than the one it runs on. A Configuration Question is a *setting* when its answer differs between environments (hosts and URLs, mailboxes and recipients, shares and paths, credential, queue, bucket, asset and Data Fabric entity names, schedules, language models) or must change without a new version (a key the source reads from its configuration store), and a *constant* when it is the same in every environment and a change to it is a change to the automation (thresholds, limits, retry counts, message texts). Several keys that always carry the same value are one setting, and a key whose value only names another resource is a fact. A source's own configuration store (a config table, a properties file, a workbook) is not a Platform Dependency of the rebuild: where the rebuild's settings and constants live is decided by execution's configuration questions.

A grouped question names every key inside it, before the question mark, so execution can map each key; it holds values of one kind. A question that says "required: empty ends the run" marks a value whose emptiness changes the flow instead of failing, and execution guards it. Questions execution asks itself are not in the genome: the scaffolding choices (project location, target framework, expression language, installed package versions), and the split questions when the Transactional Shape is not the stub.

## Workflow

Numbered steps in execution order, each `N. **{Step name}** (input: …; output: …)`: the number keys the step's row in the Source Map's step table, the bold name heads its Business Rules and Error Handling entries. Steps may be grouped under `###` headings (one per entry point); steps several entry points share are written once, under a heading of their own, and each entry point's last step names the step it continues into. A step that calls an automation the source does not hold (another project's process, a workflow outside the export) names it by what it does, states what the step passes to it and what it uses of the result; the callee is a Platform Dependency the rebuild calls but does not build, and the Source Map's unresolved-invocation row names it. Substeps (a, b, c) carry the fields, conditions, validations and transformations.

**Test components** list one numbered step per test case — `N. **Test case: <title>**` — with the case's steps as lettered substeps and its assertions named in them; the Source Map's step table then has one row per case. A **library** component lists one numbered step per public workflow, grouped by the screen (or stage) it acts on; the steps are independent entry points the consumers invoke, not one execution.

**Composite UI interactions carry their full contract.** Source frameworks and descriptions bundle a multi-step interaction into one step: type-ahead pick, menu or tree path, option list, find-row-then-act, keystrokes to the focused element. The substep states, in behavioural words, everything the builder needs to rebuild the interaction: what is typed, how the suggestion or option is matched (equals / contains / nth), which key confirms, each path level, the row rule. Execution builds each contract as a pattern ([ui-target-migration-guide.md § Composite interactions](ui-target-migration-guide.md)).

**A substep in a window an action opened names that window** ("in the Select Vendor dialog, click OK"); a name deduced from the action that opened the window carries `*[Inferred]*`.

**A source's workaround for its own platform is not behaviour.** A step states the result the workaround produced, and the Source Map names the workaround — unless a later step reads what it leaves behind, which makes it data.

**Business Rules and Error Handling** are grouped under `### Step N: {name}` headings for the step where the rule fires (several steps under one heading naming them, cross-step rules under `### General`, Error Handling's shared failures under `### Global`). An Error Handling entry states the failure, the outcome and the level that handles it; a step entry exists only where that step's handling differs from `### Global`. A Workflow substep's "confirm …" is a post-condition of the action before it, built as that action's verification, not a separate check.

## Acceptance Criteria

A numbered list (`1. …`): the execution report's verdicts and a comparison of two runs cite a criterion by its number. **A criterion whose outcome rests on a language model's answer** is in one of three checkable forms: it states the answer ("Given the model classifies the item as {category}, …") and is checked with a supplied or recorded answer, so it tests the build, not the model; it states an invariant that holds whatever the model answers; or, for the quality of the model's own answer, it gives an input whose right answer is computed outside the model, is checked over several runs, and a miss is a finding on the model, never on the build.

## Complexity

`simple | medium | complex`, inferred by the writer. Process genomes are `medium` with at most three **buildable projects**, no human lanes and no `complex` component, otherwise `complex`; the test-case groups of the single test project count as that one project.

## Stub Lines

| Section | Stub |
|---|---|
| Platform Dependencies | No Orchestrator or Integration Service resources required. |
| Interface | Runs unattended with no arguments; outputs are the side effects listed in Workflow. |
| Configuration Questions | No open values — no configuration needed. |
| Business Rules | No business rules beyond the Workflow substeps. |
| Error Handling | No error handling: a failure stops the run. |
| Transactional Shape | Not transactional: {reason — the run is one unit of work; one item's work started per item by {caller}; a library; a test-case group; a coordinator whose per-item lifecycle is the orchestration's; a {Flow, API workflow, agent} that works its items itself}. |

## Ambiguity Marker

A line ending `*[Inferred]*` is the writer's best interpretation where the source or the description was unclear; the Source Map records the uncertainty. The build builds the line as written and lists every `*[Inferred]*` line it relied on in the report.

## Process Genome Sections

### Handoffs

One row per edge between components: mechanism (queue item, start job, Flow invoke, event, file drop, Action Center task, a shared store one component writes and another reads when asked — a Data Fabric entity, a database table), data schema passed, and what happens when the receiving side fails. This table is the data contract; component Interface sections must agree with it. When the Transactional Shape's producer and consumer are two phases of one component that form a flow exchanging items through a store (a database work table, a folder), one row marked as intra-component carries that edge: it is the data contract the shape cites. Every flow of the Transactional Shape cites the Handoffs row that carries its items. The table has no rows for people or systems the automation only reads from or acts on; a human task a component creates (an Action Center task) keeps its row because it carries a data contract; one row per queue edge names the queue(s) by name, and one row per call and per file or mail handoff between components.

### Deployment

Packaging (one solution vs independent packages), entry points and triggers, target folders or environments. The buildable projects are named explicitly; a library is listed with the feed it is published to, apart from the solution's projects, since it is never one of them; when test components exist, Deployment names exactly one test project and one Test Manager test set per test component.

## Design Links

One optional blockquote line after the blueprint blockquote (the process genome's, or a standalone component's) ties a genome to the document it derives from. It is written only when that document exists; it is never invented.

- **`> Designed in: [<SDD title>](<relative path to the SDD>)`** — the genome was authored from that agreed SDD. The SDD's decisions — the split and queue design, the implementation mode, the package pins, the refactor answers — are recorded in the sections that hold them (a flow's `Decided:` line, Configuration Questions defaults, a process genome's Deployment) and execution reads them as answered. The genome restates the SDD's products and projects and never contradicts them; a change to them is an SDD change first.

## Source Map

Extracted genomes only: where every part of the genome came from — a table of contract rows (one row per component in a process genome) and, in each component genome, the step table below. It names files and source objects, never activity names or variables, and also records dead code, unresolved invocations and steps whose intent was inferred, plus `Related resources` and `Resource discrepancies` rows when the user gave resources. A genome shared without its Source Map can be built but not migrated: the build gets placeholders or a live capture, and the report says so.

**The step table.** Every extracted component genome carries, under a `### Steps` heading in its Source Map, one table pairing each Workflow step with what it was built from:

| Step | Source objects | Data sets | Captures | Notes |
|---|---|---|---|---|
| 3 | `Submit_Order` (482113, lines 29–40) | `Order_Rows` (1207) | 2 | The confirmation is sent by `Send_Confirmation` (529077), a step of its own; called by the run's root `Order_Main` (310045) |

1. **One row per Workflow step**, keyed by its number exactly as the Workflow numbers it. A test component's steps are its test cases. A step built from the same objects as another repeats them.
2. **Source objects** lists only the objects whose behaviour the step implements, separated by `; `, the step's primary object first: the one whose name a rebuild that keeps the source's names gives the step's file or workflow. A framework source writes each as `` `Name` (id) `` or `` `Name` (id, {locator}) ``: names repeat across folders in most frameworks, so the id is what identifies the copy, and the locator is the position inside the object (lines, a page, nodes, test steps). A UiPath source writes the workflow's project-relative path, `` `Folder/Workflow.xaml` ``, a test case with its `testCaseId` in the parentheses ([refactor-guide.md § Provenance](refactor-guide.md)). A caller, and a callee that is a step of its own, are in Notes; a window or a control never appears here — it is the target catalog's.
3. **Data sets** lists the data sets the step's own objects read, written like a source object, or `none`: a test case's own data set, and one it borrows from another case or a shared set (login rows, interface data). A library step's cell is `none` unless the library reads a data set itself. The column gives the kind, so a root and its data set that share a name, or a data set whose id equals a process id, are never mistaken for one another.
4. **Captures** is the number of screen captures the source takes inside the step, `0` when it takes none; the build checks the rebuild's evidence against it.
5. **Notes** is free text — callers, callees, lines, findings, quirks — and the only cell no check reads.

**Unused parts.** An uncalled library workflow, entry point or test case the extraction kept is written like any other part, and a workflow nothing invokes is a step whose first sentence says no step invokes it today, its row's Notes saying `no caller in the export`. Parts left out are in the `Not covered` row (live surface) or the `Unused` row, by name and id with what each does: a build leaves them out unless they are translated first.

**For a genome extracted from another framework the Source Map is also the migration contract.** The build regenerates every catalog it needs — UI target locators, data rows, process inventory — from the export, at its migration preflight ([source-migration-guide.md § Migration preflight](source-migration-guide.md)), into the build's working folder, never beside the genome. The process genome (or the single component genome) carries:

| Row | Content |
|---|---|
| Source framework | `UiPath` and the Studio / platform version for a UiPath source (the build is a refactor); otherwise the framework name as the framework migration pack's README spells it, and the version the export states (the build is a migration) |
| Requested change | present only when the refactor or migration request asked for a change: the user's words and each decision by topic (Split, Target, Retire, Fold); [refactor-guide.md § Refactor questions](refactor-guide.md) rule 2 and the flow's `Decided:` line take them as the user's answers |
| Source export | the export's root path as extraction read it, plus its identity (database or tenant, export date, process count) so a moved copy can be recognised |
| Steps | the step table above, in every component genome |
| Checkpoints | for every workflow step of a test component, and of a library a test component calls, the source's checkpoints inside it: source step id, what is asserted, the expected value (or the data column it comes from; for a library step, the Interface argument), and whether the source captured a screenshot there. The build makes one assertion and one evidence artifact per checkpoint and produces the result parity table from them ([test-execution-guide.md § Result parity](test-execution-guide.md)). One row, or one per step as `Checkpoints, step N` |
| Not covered | live behaviour the extracted projects or folders hold that no step is built from, by name and id, each with what it does |
| Inventory counts | what the export holds and the genome covers, as counts: processes, windows, controls (and how many have no locator), recordsets, rows, credential accounts, and the objects left out |
| Other rows as needed | excluded objects, dead code, unresolved references, steps whose intent was inferred, data files that are outputs rather than inputs, source-only constructs with no counterpart, findings — any label |

A Source Map that names the export but not the per-step objects has lost the migration: the build cannot find the locators and rows the export carried, and it says so in the report instead of shipping invented data.

## Source values

A genome is extracted through a rendering of the source — a framework's inventory output — and inherits every gap in it: a rendering can hide a typed value (a number, a flag stored as text, an option nested under another), and an extraction can paraphrase one. An empty value in a rendering is "not shown", never "not set". The build checks every fact of these kinds the genome cites against the source object before a group builds on it (its migration preflight), and follows the source where the two disagree:

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

An extracted genome carries a source's defect, confirmed in the source, where the behaviour lives — the step, rule or handler — in this form:

`**Source defect:** {what the source does, stated as fact} … Evident intent: {what it was meant to do} {*[Inferred]* when only the step's purpose shows it}`

- The defect itself is a fact read in the source and never carries `*[Inferred]*`; the evident intent carries it only when the step's purpose is all that shows it.
- The genome says which behaviour the rebuild follows. It follows the evident intent when the source states that intent. When only the step's purpose shows it, the rebuild carries the source's behaviour unless the user rules otherwise. A ruling sits at the step after the source fact it departs from, as `User ruling ({date}): …`, and the index row's Rebuild follows cell cites it.
- A defect whose result only the source runtime's internals reproduce cannot be carried: the rebuild follows the evident intent.
- What an evident intent leaves open is an open ruling, its options listed at the step; until the user rules, the genome names the option the rebuild builds and marks it `*[Inferred]*`.
- A process genome indexes every component's defects under Error Handling and Recovery in one table, `Defect | Component step | Rebuild follows`: one row each, stated in full only at its step.
- A defect's own Source Map row names the objects and lines that prove it.
- A behaviour that turns on semantics nobody documents is **unresolved**: both readings are stated and the chosen one is marked `*[Inferred]*`.
