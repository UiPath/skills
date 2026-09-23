# Genome Format Guide

Content rules for every genome, however produced (authored, extracted, edited). Templates: [component-genome-template.md](../assets/templates/component-genome-template.md), [process-genome-template.md](../assets/templates/process-genome-template.md). Worked examples: [assets/examples/](../assets/examples/).

## Two Levels

| Level | File | Scope | Use when |
|---|---|---|---|
| **Component genome** | `<slug>-genome.md` | One buildable project (RPA process, Flow, BPMN, agent, API workflow, coded app, function, case plan) | Automation is one project. Only file for a standalone automation. |
| **Process genome** | `<slug>-genome.md` plus `<slug>-genome/<component-slug>-genome.md` per component | Business process realised by two or more buildable projects | Solution with ≥2 projects, coordinator (Flow / BPMN / Case) invoking other automations, or described process clearly needing ≥2 components |

Rules:

1. **Choose the level before writing.** One project → component genome only. Two or more projects, or one coordinator plus anything it invokes → process genome plus one component genome per project. Never flatten a multi-project process into one component genome; never split a single project into a process genome.
   - **Test components are the one exception to "one component = one project".** Every test component of a process (a group of test cases over data rows for one business area) lives in a *single* test project, `<ProcessName>.Tests`, as one folder per component with its own test cases and data file(s), plus a shared `Config/` workflow for constants. Each group keeps its own component genome (Interface, rules, criteria), so the process genome still lists them as components, but Deployment counts one test project, and the process genome carries a **Project layout** table (see § Build With / Components). Never emit one test project per business area.
2. **Component genomes inside a process carry the `Part of:` line** immediately after the blueprint blockquote, linking back to the process genome. Standalone component genomes omit it.
3. **Detail lives at the lowest level that owns it.** Component-specific workflow steps, business rules, error handling, and acceptance criteria go in the component genome. The process genome holds only what spans components: process map, handoffs, shared platform dependencies, the transactional shape (its flows, producers and consumers), cross-cutting rules, end-to-end criteria, deployment.
4. **Every section present, always.** Each template section appears in every genome. A section that does not apply gets its stub line (below), never an omission.
5. **Preamble is mandatory.** Every genome starts with the `<!-- UIPATH-AUTOMATION-GENOME: component|process | ... -->` comment and carries the visible blueprint blockquote after the one-liner. This prevents an agent from executing the steps instead of building the automation. Build With (component) or Components (process) appears before Workflow / Process Map so an agent meets the skill references before the steps.

## File Naming and Location

- Write to user's current working directory unless they name a location.
- Slug: split CamelCase on capitals, lowercase, hyphens for spaces, strip other characters. "Invoice Processing" → `invoice-processing-genome.md`; "InvoiceIntake" → `invoice-intake-genome.md`; "Email Triage & Routing" → `email-triage-routing-genome.md`.
- Extracted genomes take slug from source project or solution name; fall back to directory name.
- Process genome components: `<process-slug>-genome/<component-slug>-genome.md`. Component slug from project name.

## Section Rules

### Overview
Business purpose, who it serves, what triggers it. Write as the author of the automation, never as a describer of files ("this project contains…" is banned).

### Target Applications / Actors and Systems
Resolve infrastructure to the real system. "Integration Service" is not an application; write "Salesforce", "ServiceNow". Process genomes also list human actors.

### Build With / Components
One skill per row from [skill-mapping-guide.md](skill-mapping-guide.md). Rationale states why that skill and not the nearest alternative.

**Process genomes with test components:** the Type column of every test component reads "Test-case group in project `<ProcessName>.Tests`", and a **Project layout** block follows the Components table: one sentence stating the solution has N buildable projects (non-test components plus one test project), then a table `Folder | Component | Test cases | Data file(s)` with one row per test component and one row for the shared `Config/` folder (constants from the Configuration Questions, credential-asset name → environment URL map). Data files are one per data-driven test case, in the owning skill's variation format (`uipath-rpa`: a JSON file under `.variations/` per case), named after the case with its row count; a case with a single scenario and no variations lists none — its values are argument defaults or configuration constants. The component genomes' Build With rationale names their folder in that project. The component diagram nests the test components inside a subgraph for the test project.

### Platform Dependencies
Every Orchestrator or Integration Service resource touched: queues, assets, credentials, storage buckets, connections, folders, triggers. Each row names resource type and purpose. Extracted genomes keep the source resource name; authored genomes propose one.

**Credentials: one credential asset per login account**, named after the account or persona, with its environment or tenant. Scenarios often sign in as several accounts with different roles on different tenants; never collapse them onto one login. The asset holds the secret; the genome and the data rows name the asset — a password, token or secret value never appears in a genome, a data file or a report, and dropping the account identity along with the secret loses which role each scenario ran as. Execution-side naming and declaration: [source-migration-guide.md](source-migration-guide.md) rule 4.

**Identifiers are not credentials.** An application registration's client id and tenant id, a service URL or a mailbox address are Text assets (or configuration values), one per value, even when the source stored them in its credential vault: a credential asset's second half is a secret that a consumer cannot read back as text without a conversion the workflow analyzer rejects at build. The genome names them as Text assets; execution-side rule: [source-migration-guide.md](source-migration-guide.md) rule 4.

### Interface (component)
Inputs, outputs, side effects. Mandatory content for a component inside a process genome (it is the contract the Handoffs table relies on). Standalone components may stub it: "Runs unattended with no arguments; outputs are the side effects listed in Workflow."

**Library components** (a project other components consume as a package) carry, instead of the three bullets, one table per public workflow — never one table shared by several, which hides each workflow's types and directions: `Argument | Direction | Type | Description`, the description stating the default and the value format (what a flag means, how a boolean or a date is rendered, which side quotes a value), plus the conventions consumers rely on (naming, defaults, what a failed final check does). This table is the contract consumers are authored against before the library packs; every detail it omits becomes a question between two build groups.

**Test components** (a group of test cases over data rows, one folder of the single test project) list the row schema per test case: the fields that vary per scenario (at most about 20 — an analyzer rule caps workflow arguments), separately from the constants in the project's shared configuration workflow. Credentials appear as the name of a credential asset per row, never as values.

### Configuration Questions
Format: `N. {Question}? (default: {value})`. Every hardcoded value in the source or description becomes a question: paths, URLs, addresses, server names, credential and queue names, thresholds, column names, and the application choice itself ("Which email provider? (default: Outlook)"). When a source holds dozens of configuration keys (a configuration table or procedure), group them by theme into one question per theme and name every key inside its question, so the list stays readable and execution can still map each key; a key whose value is not in the export gets the key name and "not in the export" as its default, and when an empty value would change the flow instead of failing (an end time that compares as reached, a list matched by containment), the question says so — "required: empty ends the run" — so execution guards it ([execution-guide.md § 1.3](execution-guide.md) rule 8). Scaffolding choices (project location, target framework, expression language, installed package versions) belong to the executing environment, not the automation: execution asks them itself ([execution-guide.md § 1.3](execution-guide.md)); do not write them into the genome.

### Workflow (component) / Process Map (process)
Numbered steps in execution order. A step involving several fields, a condition, validation, or a transformation gets substeps (a, b, c) and a data annotation `(input: …; output: …)`.

Shallow, insufficient for replication:
```markdown
3. **Validate**: Check the invoice against the purchase order.
```

Sufficient:
```markdown
3. **Validate invoice against purchase order** (input: extracted invoice record; output: validation result with discrepancies):
   a. Match vendor_id to the vendor master
   b. Match PO number to open POs for that vendor
   c. For each line item verify description, quantity, and unit_price against the PO line
   d. Verify quantity × unit_price sums to the invoice subtotal, and subtotal + tax = total within the configured tolerance (default 1%)
   e. If any mismatch exceeds tolerance, flag the invoice with the field, expected value, and actual value
```

Test: if a builder cannot rebuild the step from the text alone, add detail. Never compress distinct steps to hit a count.

**Test components** list one numbered step per test case — `N. **Test case: <title>**` — with the case's steps as lettered substeps and its assertions named in them; the Source Map then has one row per case. A **library** component lists one numbered step per public workflow, grouped by the screen (or stage) it acts on, in the order a user meets the screens; the steps are independent entry points the consumers invoke, not one execution, and a lead-in sentence says so.

**Composite UI interactions carry their full contract.** Source frameworks and descriptions bundle a multi-step interaction into one step: type-ahead pick, menu or tree path, option list, find-row-then-act, keystrokes to the focused element. The substep states, in behavioural words, everything the builder needs to rebuild the interaction: what is typed, how the suggestion or option is matched (equals / contains / nth), which key confirms, each path level, the row rule. "Enter Voluntary into Primary Reason" is a data loss; "type Voluntary into Primary Reason and pick the suggestion that equals Voluntary" is the step. A source guide's composite-actions table gives the wording per source action; execution builds each contract as a pattern ([source-migration-guide.md § Composite interactions](source-migration-guide.md)).

### Business Rules
Plain language, no code syntax, specific fields and thresholds kept. Group under `### Step N: {name}` headings for the step where the rule fires; cross-step rules under `### General`.

| Code construct | Genome wording |
|---|---|
| `If` / `FlowDecision` / `if` | "If {condition}, then {action}; otherwise {action}" |
| `Switch` / `FlowSwitch` / `switch` | "Route based on {field}: {case} → {action}, {case} → {action}" |
| `AndAlso` / `&&` | "and" |
| `OrElse` / `\|\|` | "or" |
| `>` `<` `=` `<>` `==` `!=` | "exceeds", "is less than", "is", "is not" |

`Amount > 10000 AndAlso Category = "Premium"` → "If amount exceeds $10,000 and category is Premium".

### Error Handling
Same step-associated layout as Business Rules, plus `### Global`. Behavioural wording: "Retries 3× on timeout, then routes the item to the exception queue" — never "RetryScope with NumberOfRetries=3".

### Transactional Shape

Whether the automation iterates over **units of work** — items that succeed, fail, are retried and are tracked independently of one another — and, when it does, how the work is handled today and how it could be divided at build. UiPath realises per-item work with the **REFramework** (Robotic Enterprise Framework): a state machine that opens the applications once, takes one item at a time, classifies each item's outcome, retries system failures, records every item's status, closes the applications at the end, and reads its settings from a configuration workbook plus Orchestrator assets. An automation can hold several such streams — a **flow** is one kind of item handed from the steps or component that produce it to the steps or component that consume it, independently of any other item (the children an item expands into are levels of that item, not a flow of their own — rule 12); a process genome may have one flow between components 1 and 2, another between 2 and 3, and an independent one between 5 and 6. This section **describes**, per flow: the unit of work and the other viable granularities, how the process produces and consumes items as it is (or as described), where the items and their state live, which coordination the source used, and — for the unit of work and for every alternative unit — which ways of splitting the roles are possible, with what each requires and changes. It **asserts no split, no store, no template and no unit** — those are configuration answers at execution ([execution-guide.md § 1.3](execution-guide.md)). The behaviour written in Business Rules, Error Handling and Acceptance Criteria is owed whatever the user chooses.

Layout when at least one unit of work exists — one `### Flow N` block per flow, numbered in the order the items first arise, even when there is only one:

```markdown
**Flows:** Flow 1 — {unit}: {producer steps or component} → {consumer steps or component} (Handoffs row {n}); Flow 2 — {unit}: … ; chains: {component x} consumes Flow 1 and produces Flow 2; independent: Flow 3. *(process genome and standalone component; a single flow: "Flow 1 — {unit}: steps {a–b} → steps {c–d}")*

### Flow 1 — {unit of work}: {producer} → {consumer}

**Unit of work:** one {item}; reference {field(s) that identify it and prevent duplicates}; fields as in {Handoffs row N / Interface}; {volume and cadence}; chosen because {items fail, retry and are reported independently at this level; the reference exists; the retry cost is acceptable}.
**Alternative units of work:** one {other item} — fits when {condition}; one {third item} — fits when {condition}. *(every viable granularity, or "none")*

**As-is** — how the process handles the units today:

| Aspect | As-is |
|---|---|
| Produced by | {steps — and, in a process genome, the component — that read the source(s) and create items; how often; one source or several; whether the population is guarded: lock, ledger, "once per date"} |
| Consumed by | {steps / component that take items; one robot or several; how a robot picks its items — any, by parent, by kind; in which order} |
| Item store | {framework work queue, Orchestrator queue, database table, in-memory list, folder}; per-item state kept as {status text, tags, data fields, output} |
| Coordination | {parent items, ledgers, locks, tag joins between item levels} and what each is for — described, not prescribed; "none" when absent |
| Item kinds | {one kind, or several kinds routed inside the consumer, with what differs per kind — payload, work, outcomes} |
| Step groups | once per run: steps {n, m}; per item: steps {p–q}; at the end: steps {r} |

| Outcome | When | Effect |
|---|---|---|
| Success | every per-item step completed | item recorded as done with {result} |
| Business exception | Step {N} rules: {rule names} | no retry; item recorded with the reason; run continues |
| System exception | every other failure — Step {N} handlers: {names} | applications reopened, item retried {n}×, then recorded as failed with the reason; run stops after {m} consecutive |
| Postponed *(only when the source or the description puts items back for later)* | Step {N} rule | {postpone time and limit; past the limit a business exception} |

**Split options** — for the unit of work and for each alternative unit of work, the ways the roles can be divided at build; each states what it requires and what it changes against as-is; the number of runners is a deployment setting of each resulting process, never an option; none is asserted:

| Unit of work | Option | Processes | Item store | Requires | Changes against as-is |
|---|---|---|---|---|---|
| {unit} | A — one process, both roles | one RPA process holding the producer and consumer steps: the REFramework in direct mode or a plain per-item loop over an in-process list | in-process list — one job takes its items end-to-end on one runner; no Orchestrator queue | nothing else touches the items, one runner works them and a rerun is safe; excluded when items are shared by several runners or must survive a run | {what changes here: projects and schedules, where per-item state is visible, retry granularity, what the end-of-parent work needs} |
| {unit} | B — a producer process and a consumer process | two RPA processes — two projects, or one project with a producer and a consumer entry point, each published as its own process — each with its own trigger, schedule and number of runners; one producer per independent source or one consumer per item kind when the As-is shows several (sub-choices asked at execution) | one Orchestrator queue per unit of work (or per consumer kind) | the items are shared by several consumer runners, retries or postponements cross runs, or the two roles need different cadences, machines, credentials or ownership | {…} |
| {unit} | C — one process, both roles, with a queue | one RPA process with one entry point and one trigger: every job runs the producer steps behind a once-guard, then takes items from the queue — the REFramework in queue mode with the producer steps in its initialisation, or a plain loop over the queue; any number of identical runners | one Orchestrator queue per unit of work, filled and worked by the same process | the items are shared by several runners, retries or postponements cross runs, or another process reads the items after the run, while both roles share one cadence, one machine and account set and one owner; the population happens once per period whatever the number of runners (a unique reference the queue refuses twice, or a kept ledger); excluded when the two roles need different cadences, machines, credentials or owners | {…} |
| {alternative unit} | A — one process, both roles | … | … | … | {…} |
| {alternative unit} | B — a producer process and a consumer process | … | … | … | {…} |
| {alternative unit} | C — one process, both roles, with a queue | … | … | … | {…} |

When the flow's producer and consumer are **different genome components**, B is their as-is, A reads "the two components' roles in one process" and C "the two components' roles in one process that keeps the queue between them": the executor materialises one project for both, records it in the completion report, and leaves the Components table unchanged; each Requires cell names what the merge needs (one schedule, one machine and account set for both; under C also the once-guard).

**Evidence:** {facts that bear on the choice, no verdict — several robots run the same process today; the folder source is independent of the export; item kind X needs application Y that kind Z does not; …}
**Configuration:** settings — questions {a, b}; constants — questions {c, d}; assets — every Credential and Text row of Platform Dependencies.
**Traceability:** {what is recorded per item today and where; the upstream reference the item carries when it is produced by the consumer of another flow; screenshot on system exception; run summary}.

### Flow 2 — …
```

Layout in a component genome inside a process — one block per flow the component takes part in, the stub when it takes part in none:

```markdown
### Flow {N} — {unit of work}: {producer} → {consumer}

**Role:** {producer | consumer | consumer of Flow {M} and producer of this flow (chain)} — {one sentence: what this component does with the items}.
{the As-is rows that concern the role (rule 9), the outcomes table and counts for a consumer, its configuration split and traceability}
Split options: per the process genome, Flow {N}.
```

Rules:

1. **One test decides applicability: a unit of work exists — per flow.** Each flow is tested on its own; the section carries one block per flow that passes and the stub only when none does. A unit of work is a discrete item that can succeed, fail, be retried and be tracked independently of the others, and the automation iterates over such items. Sources of items: an Orchestrator queue, a mailbox, a folder of files, the rows of a spreadsheet or table, a work list on a screen, a page of API results, a database work table. **No unit of work:** a run that succeeds or fails as one (a poll, a report, a single posting); one item's work started per item by a caller — the caller owns the lifecycle and is the candidate consumer; an attended automation that waits on its user between items. A trigger that starts one job which then takes items until the source is empty **is** a consumer; a trigger configured to start one job per item is not — say which the source or description implies. **Component types that are never consumers** (they may still be producers): a library, a test-case group, a coordinator (Flow, BPMN, Case) — its per-item lifecycle is the orchestration's — an agent, an API workflow, a coded app, a function. Volume is never the criterion: fifteen independent items a day is a shape, ten thousand rows written into one file is not. When items nest — a folder of files each holding rows, a mailbox of mails each carrying several documents, a requisition with its lines — the unit of work is the level at which one item fails, retries and is reported on its own, has a natural reference, and whose retry cost is acceptable; the levels above or below it are Alternative units of work (rule 8).
2. **Roles are described, never assigned.** "Produced by" and "Consumed by" name the steps — and, in a process genome, the components — that create and take items today. A producer may be any component type; a consumer is an RPA process (`uipath-rpa`), the only component type the framework builds; the component types rule 1 lists are never consumers. The words `dispatcher` and `performer` are execution vocabulary: they name the projects a chosen split materialises and appear in the Split options table and in the completion report — never in the Components table's Type cell, which reads `RPA process`, and never as a claim about what the rebuild is. A component genome inside a process states its as-is role per flow in one sentence (its `Role:` line) and carries the As-is rows that concern it; a component that consumes one flow and produces the next says so in both blocks.
3. **The item store follows the split.** The As-is row says where items and their state live today; each Split option says which store it needs. **Option A keeps the items in the job**: one job takes its items end-to-end on one runner — the REFramework's direct mode, or a plain loop over an in-process list — and needs no Orchestrator queue. **Options B and C keep them in an Orchestrator queue**, which items need whenever they are shared across jobs — several runners, retries or postponements across runs, another process reading them after the run — with exactly **one queue per unit of work**, which any number of producers and consumers, and any number of runners of each, share. **C keeps both roles in one process**: one entry point and one trigger, every job produces behind a once-guard and then consumes, and every runner runs the same process — the shape of a source that runs one process on several robots and guards its population with a lock or a ledger. **B separates them** into processes with their own triggers, which the roles need when their cadences, machines, credentials or owners differ; a producer entry point with its own trigger is a producer process, so two entry points of one project are B, never C. A source's own coordination stores — a parent queue, a populate ledger, a lock, a tag join — are facts of the Coordination row; they are carried into a build only when the chosen split still needs them and the user keeps them ([execution-guide.md § 1.3](execution-guide.md)). One standing case: a source that keeps its work list in a **database the process owns** (hand-out per runner, per-item status written back, operators reading the tables) already has a shared store; the As-is says so and every Split option can then name that database as its store, with an Orchestrator queue offered as a Configuration Question rather than imposed.
4. **Outcomes classify the rules and handlers already written; they never restate them.** Three rows always, a fourth only under the condition at the end of this rule: **Success**; **Business exception** — the Business Rules that reject an item (missing or wrong data, a rule the item fails): no retry, the item is recorded with the reason, the run continues; **System exception** — every other failure (application unavailable, element not found, timeout): the applications are closed and reopened, the item is retried the configured number of times, then recorded as failed with the reason, and the run stops after the configured number of consecutive system exceptions. Name rules and handlers by step ("Step 7 rules: duplicate, no open PO"); never copy their text. The two counts are Configuration Questions with the source's values as defaults, or `(default: retried 2×; stop after 3 consecutive)` when authored. A fourth row, **Postponed**, exists only when the source or the description puts an item back for a later attempt without counting it as a failure — the record it targets does not exist yet, a cut-off time has passed. Its When names the rule by step; its Effect states the postpone time and the limit: in a queue store the item returns to the queue with a postpone time and its attempt count untouched, in an in-process store it is written back as pending; past the limit it is a business exception. Postponement never replaces the system-exception retry, and a run that waits between polls is not postponing items.
5. **Once per run, per item, at the end.** Every Workflow step of a consumer belongs to exactly one group, named by step number in the As-is Step groups row: once per run (open and sign in to the applications, read configuration and reference data, read the source when the store is in-process), per item (the business steps), at the end (close the applications, write the summary or report). A step that fits no group is missing from Workflow, not from this section. A producer's steps are never in the consumer's once-per-run group: they are the Produced by row's own steps. In a chain the steps that create the downstream flow's items are **per-item** steps of the upstream flow's consumer, named in both flows' blocks (rule 13).
6. **Configuration: split, do not repeat.** Name which Configuration Questions are run settings (environment-specific: URLs, paths, mailbox, queue name, folder) and which are constants (thresholds, retry counts, formats), and state that the Credential and Text assets in Platform Dependencies are read at start. A secret is never a configuration value ([§ Platform Dependencies](#platform-dependencies)).
7. **Traceability: what is recorded per item, and where.** The reference, the outcome and its reason — as the queue item's status, progress and output when the store is a queue; as a write-back column, a result file or a reporting queue when it is not; a screenshot on every system exception; one run summary (items taken, succeeded, business exceptions, failed). These are what a reporting step or a digest reads; a reporting component reads them, never the consumer's log.
8. **Split options and evidence replace any verdict.** Options A, B and C are listed whenever a unit of work exists — once for the unit of work and once for every Alternative unit of work — each with its requirements and its changes against as-is; an option the evidence excludes is still listed, with the reason in its Requires cell ("excluded: several robots work the items and postponements cross days"). Two things are never options: **the number of runners**, a deployment setting of each resulting process (A runs on one runner per job; several runners mean B or C), and **several producers or several consumers**, sub-choices of B the execution asks when the As-is shows several independent sources or several item kinds. A Requires or Changes cell states facts in this automation's terms — projects and schedules to operate, parallelism, retry granularity, where per-item state is visible, what the end-of-parent work needs (rule 11) — and never ranks the options ("recommended", "best", "simplest"); generic trade-offs that hold for any automation are not written. The Evidence line carries facts only — robot count, schedules, sources, applications per item kind, whether items survive a run today. The **Alternative units of work** line lists every viable granularity with the condition under which it fits, never a choice; a mode or a project split is never an alternative unit — those are Split options. Derivation table (authoring and extraction):

   | Signal in the source or the description | Split options it enables or excludes |
   |---|---|
   | One job works items end-to-end, nothing else touches them, a rerun is harmless | A viable |
   | Several robots run the same process on the same items; an item must survive a run failure; a postponement or retry crosses runs | A excluded; B and C viable — C while both roles share cadence, machines, credentials and owner |
   | Another process reads the items after the run (a report, an audit, an operator view) | A excluded unless the job writes a per-item record the reader can use; B and C keep the items where the reader finds them |
   | Population and consumption have different natural cadences (an export published once a day, files dropped all day), or need different machines, credentials or owners | B favoured; C excluded |
   | Several independent sources feed the items | B with one producer per source, or A or C reading every source in its producer steps |
   | Item kinds need different applications or machines, or different attempt limits or SLAs | B with one consumer per kind and one queue per kind; otherwise one consumer with a route step |
   | The source guards population with a lock or a ledger | evidence that several identical jobs ran the process, which is C's shape; C keeps a once-guard in its place (a unique reference the queue refuses twice, or the kept ledger); B with one producer job removes the need for it |
   | Work happens once per parent when its children are final (a summary, a report, a close-out per file or mail) | at the child unit: every option names how that work learns its children are final (rule 11); at the parent unit: it is the transaction's last step |

9. **Levels.** The process genome carries the `Flows:` line and one full block per flow: unit of work and alternatives, the As-is across the components the flow joins, outcomes, split options per unit of work, evidence, configuration, traceability; when a flow has no RPA consumer, one sentence naming what takes its items (a coordinator's trigger, one job per item) replaces its Consumed by row. A component genome inside a process carries one block per flow it takes part in (layout above): its `Role:` line, the As-is rows that concern the role (a producer: source, reference rule, what happens to the source item once it is queued; a consumer: its step groups, its outcomes table and counts, its configuration split and traceability), and the line `Split options: per the process genome, Flow N.`; a component in no flow carries the stub with the reason (a library, a coordinator, one item's work started per item by component N). A standalone component genome carries the `Flows:` line and every block in full for its one project.
10. **Extracted genomes.** A source built on a framework fills the As-is table from the framework's configuration and files (the framework's source guide says which file feeds which row); the framework's plumbing — state transitions, retry counters, status updates, screenshots on exception — is not workflow steps and is listed in the Source Map as a `Framework files` row. A source with a queue producer or consumer, or a per-item loop, and no framework is a candidate: write the unit of work and its alternatives, the As-is, and the Split options for each unit, marking `*[Inferred]*` what the source does not show. The As-is is the source's truth — its coordination stores, its item levels, its robot count — exactly as they are.
11. **Several levels of items are one unit of work and one description.** A source whose items expand into children (a record into its line items, a file into its rows, a mail into its attachments, a report into the work list built from it and that list into its rows) has one candidate level per generation, whether the parent is tracked in its own queue or status or only exists as the file or store the children came from — and whatever store (a staging folder, a work list) sits between the generations; rule 1 picks the unit of work and the other level is an Alternative unit of work. The As-is describes both levels as they are — Coordination row: "one parent item per reference, children joined by the parent key, one robot works one parent's children in sequence, the parent is completed when its children are final". Whether a level is folded at build — children produced up front, several robots on one parent's children, the parent's fate derived from its children instead of kept as an item — is an execution decision recorded in the completion report ([execution-guide.md § 3.3](execution-guide.md)), never a claim of this section. What the section does state is the consequence per level, in the Split options rows' Requires and Changes cells: at the child level, how the parent's end-of-parent work learns that its children are final — a parent item on its own queue postponed until they are, a reporting step over the children's records with a guard against sending twice, the consumer that finishes the last child — and what that costs with several runners, under B and C alike; at the parent level, that this work is the transaction's last step, that the children are worked inside the transaction, and what a parent retry redoes (only the unfinished children, when the children's state survives the retry).
12. **Flows come from the handoffs.** Every edge that hands items one by one from producer to consumer is a candidate flow: a queue item between components, a file drop, a database work table, a mailbox, a work-list workbook — the Handoffs row (or its intra-component row, § Handoffs) names it, and the `Flows:` line cites that row. Two edges carrying the same kind of item between the same roles are one flow; items handed on a second time (component 2 → 3 after 1 → 2) are a second flow when the second consumer takes items the first consumer produces, even when the payload is similar. A flow keeps its own unit of work, alternatives, store, outcomes, split options and evidence; two flows never share a queue, since each unit of work has its own (rule 3). Independent flows (5 → 6 beside 1 → 2 → 3) are separate blocks the `Flows:` line lists as independent. **A store between two phases starts a flow of its own only when both tests hold — otherwise the items it holds are a level of the upstream item, and the two phases are producer and consumer steps of one flow (rule 11):** (a) **independence** — a downstream item does not belong to one upstream item whose end-of-parent work waits on it (a summary, a close-out, a status or notification per parent) and is not the upstream item itself carried to its next stage; (b) **separation** — the two phases differ in run, cadence, robot, account or owner, or another producer or consumer touches the store. A folder or work list that the same job fills and then empties, where each upstream item turns into its own downstream items (a mail into its attachments, a report into its work list, the list into its rows), is one flow with nested levels — never a chain. A second flow inside one component exists only when both tests hold (a drop folder filled all day by one entry point and drained by another on its own schedule).
13. **Chains.** When the consumer of Flow N produces the items of Flow N+1 — items of their own by rule 12's two tests, not the children of the Flow N item: creating the downstream item is a per-item step of the upstream item, and its failure is a system exception of the upstream item — retried with it, so the downstream reference must make a second creation a duplicate the store refuses (derive it from the upstream reference); the downstream item carries the upstream reference, so traceability follows an item end-to-end; the upstream item succeeds only when its downstream item exists. Each flow's Split options are listed on their own, and each flow's Changes cells state what taking option A or C for two adjacent flows changes (their components' roles in one process; under A the intermediate store gone only when the downstream work can run inside the upstream transaction, under C the intermediate queue kept). Folding a chain into one flow — the downstream work done inside the upstream item — is an Alternative unit of work of the upstream flow, listed with its fit condition when it fits.

### Acceptance Criteria
Patterns:
- "Given {specific input}, the automation {specific observable outcome}"
- "When {condition}, the automation {expected behaviour}"
- "{Specific action} produces {specific result}"

Sources, one criterion each minimum: every major workflow step, every data transformation or field mapping, every business rule, every error handler, plus edge cases (empty input, duplicate, malformed data).

Banned: "completes successfully", "handles errors properly", and anything code-level ("Uses ReadPDF activity", "Calls Main.xaml", "Assigns true to isValid").

| Banned | Acceptable |
|---|---|
| "Uses ReadPDF to process InvoiceFile" | "Given an invoice PDF, extracts vendor_name, invoice_number, line items (description, qty, unit_price), tax, and total" |
| "SendMail sends to admin@company.com" | "When processing fails after retries, sends a notification to the configured administrator with invoice_number and failure reason" |

### Process Map diagrams (process)
Two diagrams, never merged into one:
- **Process view:** BPMN-style swimlane rendered as Mermaid `flowchart TB`. One `subgraph` per actor or system lane (automation, each human actor, each system, any party outside the automation). BPMN shapes: `((Start))` and `(((End)))` events, `[Task]` rectangles prefixed with the component number in brackets, `{Gateway?}` diamonds with labelled yes/no edges, solid arrows for sequence flow inside a lane, dashed arrows (`-.->`) with a label for message or data flow across lanes. Every gateway must have a corresponding rule under Business Rules or Error Handling.
- **Component view:** `flowchart LR` with the solution as a subgraph; solid arrows for build-time dependencies ("depends on / invokes"), dashed arrows for run-time data passed between components, shared platform resources as plain nodes.
Mermaid cannot render BPMN 2.0 itself; when the customer wants a formal model, add a sidecar `<process-slug>-process.bpmn` authored from the Process Map (the `uipath-maestro-bpmn` skill knows the format) and link it from this section.

### Handoffs (process)
One row per edge between components: mechanism (queue item, start job, Flow invoke, event, file drop, Action Center task), data schema passed, and what happens when the receiving side fails. This table is the data contract; component Interface sections must agree with it. When the Transactional Shape's producer and consumer are two phases of one component that form a flow (§ Transactional Shape rule 12) exchanging items through a store (a database work table, a folder), add one row for that edge too, marked as intra-component: it is the data contract the shape cites. Every flow of the Transactional Shape cites the Handoffs row that carries its items.

### Deployment (process)
Packaging (one solution vs independent packages), entry points and triggers, target folders or environments. Name the buildable projects explicitly; when test components exist, Deployment names exactly one test project and one Test Manager test set per folder of it.

### Complexity
`simple | medium | complex`. Never ask the user to declare it. Component genomes: inferred from the description ([authoring-guide.md](authoring-guide.md) Step 3) or from source signals ([extraction-guide.md](extraction-guide.md) Step 5); both default to the lower level when ambiguous and escalate when later evidence demands it. Process genomes are `medium` with 2-3 **buildable projects** and no human lanes, otherwise `complex`; the test-case groups of the single test project count as that one project, not one component each. A human lane is a human actor whose action the process **waits on** (an approval, a task, a mailed decision); recipients of notifications are not lanes.

### Tags
Comma-separated: business domain, target applications, platform features (document-understanding, queues, human-in-the-loop, …).

### Source Map (extraction only)
One row per workflow step (component) or per component (process): the source framework and the file, object, or workflow it came from. Names files and workflow objects, never activity names or variables. Also records dead code found, unresolved invocations, and steps whose intent was inferred. Authored genomes have no Source Map. Remove the section on request when the genome is redistributed as a reusable blueprint.

**For a genome extracted from another framework the Source Map is also the migration contract.** Execution regenerates every catalog it needs — UI target locators, data rows, process inventory, step map — from the export, and the Source Map is the only place that says where the export is and which source objects each step came from. It must therefore carry, in the process genome (or the single component genome):

| Row | Content |
|---|---|
| Source framework | the framework name exactly as [SKILL.md § Source Frameworks](../SKILL.md) spells it, and the framework version the export states |
| Source export | the export's root path as extraction read it, plus its identity (database or tenant, export date, process count) so a moved copy can be recognised |
| Per-step rows | for every workflow step, the source objects it was built from, each as `` `Name` (id) `` — names repeat across folders in most frameworks, so the id is what identifies the copy — and the data sets (recordsets, sheets) that drive it |
| Checkpoints | for every workflow step of a test component, the source's checkpoints inside it: source step id, what is asserted, the expected value (or the data column it comes from), and whether the source captured a screenshot there. Execution builds one assertion and one evidence artifact per checkpoint and produces the result parity table from them ([source-migration-guide.md § Result parity](source-migration-guide.md)) |
| Inventory counts | what the export holds and the genome covers: processes, windows, controls (and how many have no locator), recordsets, rows, credential accounts; excluded and unreachable objects by name |
| Other rows as needed | dead code, unresolved references, steps whose intent was inferred, data files that are outputs rather than inputs, source-only constructs with no counterpart — any label; only rows keyed by a **step number or step name** are read as steps by `scripts/genome-step-map.py`, every other row is contract |

**The genome files are the only output of extraction.** Recognition data (locators), data rows and process inventories never enter the genome body and are not written beside it either: they are the export's, a copy next to the genome goes stale and says nothing the export does not, and execution re-derives them from the export with the source guide's script into the build's working folder ([source-migration-guide.md § Migration preflight](source-migration-guide.md)). What the Source Map must record is everything execution needs to find them again — the rows above. A Source Map that names the export but not the per-step objects has lost the migration: execution cannot find the locators and rows the export carried and ships placeholders and invented data. A genome shared without its Source Map can be built but not migrated: the reader gets placeholders or a live capture, and the redistribution note says so.

## Population Matrix (component genomes)

| Section | Simple | Medium | Complex |
|---|---|---|---|
| Overview | 1 paragraph | 2-3 paragraphs | 2-3 paragraphs |
| Target Applications, Build With, Platform Dependencies, Interface, Complexity, Tags | Full | Full | Full |
| Configuration Questions | Stub allowed | 3-5 minimum | 5+ minimum |
| Workflow | 3-5 steps minimum | 5+ steps, substeps where detailed | 8+ steps, substeps where detailed |
| Business Rules | Stub allowed | Step-associated | Step-associated |
| Error Handling | Stub allowed | Per step where applicable | Per step where applicable |
| Transactional Shape | Full when a unit of work exists (rule 1), else stub | Full when a unit of work exists, else stub | Full when a unit of work exists, else stub |
| Acceptance Criteria | 3-4 minimum | 5+ incl. data checks | 7+ incl. data checks |

Minimums, not ceilings. Fifteen distinct steps in the source or description means fifteen steps in the genome.

## Stub Lines

| Section | Stub |
|---|---|
| Platform Dependencies | No Orchestrator or Integration Service resources required. |
| Interface | Runs unattended with no arguments; outputs are the side effects listed in Workflow. |
| Configuration Questions | Description covers the scope — no additional configuration needed. |
| Business Rules | No explicit business rules — agent applies standard validation patterns. |
| Error Handling | Standard error handling — retry on transient failures, log and skip on permanent errors. |
| Transactional Shape | Not transactional: {reason — the run is one unit of work; one item's work started per item by {caller}; a library; a test-case group; a coordinator whose per-item lifecycle is the orchestration's}. |

## Ambiguity Marker

When intent is unclear from the source, write the best interpretation, append `*[Inferred]*` to that line, and record the uncertainty in the Source Map. Never leave a section empty because the source is ambiguous. Users remove markers once they confirm the content ("Remove the inferred flags").

## Source Defects

An extracted genome carries a source's defect only once [extraction-guide.md](extraction-guide.md) Step 4b has confirmed it in the full rendering and in the framework's source itself. It is written where the behaviour lives — the step, rule or handler — in this form:

`**Source defect:** {what the source does, stated as fact} … Evident intent: {what it was meant to do} *[Inferred]*`

- The defect itself is a fact read in the source and never carries `*[Inferred]*`.
- Only the evident intent carries the marker. So does any consequence that depends on data, configuration, platform or package behaviour the export does not hold.
- The genome says which behaviour the rebuild follows. The evident intent is followed only where the genome says so; otherwise the source's behaviour is carried.
- A defect's own Source Map row names the objects and lines that prove it.
- A behaviour the source's comments or design show as intended is a rule, not a defect.
- A behaviour that turns on semantics nobody documents is **unresolved**: state both readings and mark the chosen one `*[Inferred]*`.
- The word "suspected" never appears in a written genome: a finding is verified or not written as a defect.

## Write, Then Offer Edits

Every mode writes the file(s) to the working directory immediately — no preview, no confirmation — then says where they are and asks "Want to adjust anything?". Edits are targeted and in place, never a regeneration; edit tables: [authoring-guide.md](authoring-guide.md) Step 8 and [extraction-guide.md](extraction-guide.md) Step 7.

## Provenance

The body of a genome reads as a specification, not a report: no "the project contains", no file paths in Workflow or Business Rules, no activity or variable names anywhere. Provenance lives only in the Source Map section.
