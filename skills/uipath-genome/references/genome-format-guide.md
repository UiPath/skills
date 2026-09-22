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
3. **Detail lives at the lowest level that owns it.** Component-specific workflow steps, business rules, error handling, and acceptance criteria go in the component genome. The process genome holds only what spans components: process map, handoffs, shared platform dependencies, the transactional shape (producers, consumers, mode), cross-cutting rules, end-to-end criteria, deployment.
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
One skill per row from [skill-mapping-guide.md](skill-mapping-guide.md). Rationale states why that skill and not the nearest alternative. The Type cell of an RPA component carries its transactional role word when the Recommendation applies the shape ([§ Transactional Shape](#transactional-shape) rule 2).

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
Whether the automation iterates over **units of work** — items that succeed, fail, are retried and are tracked independently of one another — and, when it does, how the work divides into producers, consumers and per-item outcomes. UiPath realises this shape with the **REFramework** (Robotic Enterprise Framework): a state machine that opens the applications once, takes one item at a time, classifies each item's outcome, retries system failures, records every item's status, closes the applications at the end, and reads its settings from a configuration workbook plus Orchestrator assets. The genome recommends the shape; execution asks the user whether to build it ([execution-guide.md § 1.3](execution-guide.md)). The behaviour written in Business Rules, Error Handling and Acceptance Criteria is owed whether or not the framework is used.

Layout when a unit of work exists:

```markdown
**Unit of work:** one {item}; reference {field(s) that identify it and prevent duplicates}; fields as in {Handoffs row N / Interface}; {volume and cadence}; chosen because {items fail, retry and are reported independently at this level; the reference exists; the retry cost is acceptable}.

| Producer | Reads | Writes items to | Reference rule | Trigger |
|---|---|---|---|---|
| {component or entry point} | {mailbox / folder / sheet / report / API} | {queue name, or "the consumer's own list" in direct mode} | {what makes an item unique; what happens to duplicates} | {schedule or event} |

| Consumer | Takes items from | Mode | Once per run | Per item | At the end |
|---|---|---|---|---|---|
| {component or entry point} | {queue name / the source} | queue \| direct — {reason} | steps {n, m} | steps {p–q} | steps {r} |

| Outcome | When | Effect |
|---|---|---|
| Success | every per-item step completed | item recorded as done with {result} |
| Business exception | Step {N} rules: {rule names} | no retry; item recorded with the reason; run continues |
| System exception | every other failure — Step {N} handlers: {names} | applications reopened, item retried {n}×, then recorded as failed with the reason; run stops after {m} consecutive |

**Configuration:** settings — questions {a, b}; constants — questions {c, d}; assets — every Credential and Text row of Platform Dependencies.
**Traceability:** {what is recorded per item and where; screenshot on system exception; run summary}.
**Recommendation:** {Apply — {reason}. | Not recommended — {reason}.}
**Alternative unit of work:** one {other item} — not chosen because {reason}; choose it when {condition}. *(only when a second granularity is viable)*
```

Rules:

1. **One test decides applicability: a unit of work exists.** A unit of work is a discrete item that can succeed, fail, be retried and be tracked independently of the others, and the automation iterates over such items. Sources of items: an Orchestrator queue, a mailbox, a folder of files, the rows of a spreadsheet or table, a work list on a screen, a page of API results, a database work table. **No unit of work:** a run that succeeds or fails as one (a poll, a report, a single posting); one item's work started per item by a caller — the caller owns the lifecycle and is the candidate consumer; an attended automation that waits on its user between items. A trigger that starts one job which then takes items until the source is empty **is** a consumer; a trigger configured to start one job per item is not — say which the source or description implies. **Component types that are never consumers** (they may still be producers): a library, a test-case group, a coordinator (Flow, BPMN, Case) — its per-item lifecycle is the orchestration's — an agent, an API workflow, a coded app, a function. Volume is never the criterion: fifteen independent items a day is a shape, ten thousand rows written into one file is not. When items nest — a folder of files each holding rows, a mailbox of mails each carrying several documents, a requisition with its lines — the unit of work is the level at which one item fails, retries and is reported on its own, has a natural reference, and whose retry cost is acceptable; the level above or below it is the alternative unit of work (rule 8).
2. **Producers and consumers are roles, not skills.** A producer creates items: reads the source, writes one item per unit with a unique reference. A consumer takes items one at a time and runs the per-item steps. A producer may be any component type; a consumer is an RPA process (`uipath-rpa`), the only component type the framework builds. One RPA project holds both roles as two entry points when they share a schedule and a robot pool; two projects when they run on different schedules, scale independently or are owned separately. Both roles keep their `uipath-rpa` row in Build With / Components. The role words are reserved vocabulary: when the Recommendation is `Apply`, every producer and consumer in the tables carries its word in the Components table's Type cell — `RPA process (dispatcher)` for a producer, `RPA process (performer)` or `RPA process (dispatcher + performer)` for a consumer — so the Components table alone tells a reader which projects the framework shapes; `performer` selects the framework template, `dispatcher` alone never does (a producer is built as a plain sequence). When the Recommendation declines, no Type cell carries a role word and the body does not call an entry point or component a `performer` — it names it by what it does. In `queue` mode every consumer has at least one producer and every producer a consumer — a queue nobody fills or nobody drains is an incomplete shape; in `direct` mode the consumer reads its own items and the Producer row names the consumer itself.
3. **Mode: queue or direct — pick one, say why.** `queue`: items pass through an Orchestrator queue; producer and consumer are separate jobs; several robots share the queue; every item's status and history are visible to operators and survive a run failure; an item is retried across runs. `direct`: the consumer fetches its own items from the source (rows read once at the start, files in a folder, a work list on a screen, an API page); one robot; nothing survives a run failure except what the consumer writes back. Choose `queue` when any of these holds: producer and consumer run on different schedules or robots; more than one robot must share the load; an item must survive a run failure or be retried in a later run; items come from several producers; operators need per-item visibility. Choose `direct` only when none holds and the whole run can be rerun safely; otherwise `queue`. One exception: when the source already keeps its work list in a **database the process owns** — hand-out per runner, per-item status and retry written back, operators reading the tables — those conditions are met by that database, the mode is `direct` with the database as the source, and the Orchestrator queue is offered as a Configuration Question rather than imposed (the framework source guide says when a source has this shape). The reason is one clause in the Mode cell.
4. **Outcomes classify the rules and handlers already written; they never restate them.** Three rows always, a fourth only under the condition at the end of this rule: **Success**; **Business exception** — the Business Rules that reject an item (missing or wrong data, a rule the item fails): no retry, the item is recorded with the reason, the run continues; **System exception** — every other failure (application unavailable, element not found, timeout): the applications are closed and reopened, the item is retried the configured number of times, then recorded as failed with the reason, and the run stops after the configured number of consecutive system exceptions. Name rules and handlers by step ("Step 7 rules: duplicate, no open PO"); never copy their text. The two counts are Configuration Questions with the source's values as defaults, or `(default: retried 2×; stop after 3 consecutive)` when authored. A fourth row, **Postponed**, exists only when the source or the description puts an item back for a later attempt without counting it as a failure — the record it targets does not exist yet, a cut-off time has passed. Its When names the rule by step; its Effect states the postpone time and the limit: in `queue` mode the item returns to the queue with a postpone time and its attempt count untouched, in `direct` mode it is written back as pending; past the limit it is a business exception. Postponement never replaces the system-exception retry, and a run that waits between polls is not postponing items.
5. **Once per run, per item, at the end.** Every Workflow step of a consumer belongs to exactly one group, named by step number: once per run (open and sign in to the applications, read configuration and reference data, read the source in `direct` mode), per item (the business steps), at the end (close the applications, write the summary or report). A step that fits no group is missing from Workflow, not from this section.
6. **Configuration: split, do not repeat.** Name which Configuration Questions are run settings (environment-specific: URLs, paths, mailbox, queue name, folder) and which are constants (thresholds, retry counts, formats), and state that the Credential and Text assets in Platform Dependencies are read at start. A secret is never a configuration value ([§ Platform Dependencies](#platform-dependencies)).
7. **Traceability: what is recorded per item, and where.** The reference, the outcome and its reason — as the queue item's status and history in `queue` mode; as a write-back column, a result file or a reporting queue in `direct` mode; a screenshot on every system exception; one run summary (items taken, succeeded, business exceptions, failed). These are what a reporting step or a digest reads; a reporting component reads them, never the consumer's log.
8. **Recommendation: one verdict, with its reason.** `Apply — <reason>.` or `Not recommended — <reason>.` The template goes to every consumer and never to a producer, and the mode is the Consumer table's, so the line names no components and no mode. Never a verdict without its reason. "Not recommended" is a full answer when the unit of work exists but the per-item lifecycle already lives elsewhere (a coordinator retries and tracks each item; a caller starts one job per item). **Alternative unit of work:** when a second granularity is viable — a file against its rows, a mail against its attachments, a requisition against its lines — one line `Alternative unit of work: one <item> — not chosen because <reason>; choose it when <condition>.` Never a mode or a project split as the alternative: the Mode cell's reason and the Recommendation's reason carry those.
9. **Levels.** The process genome carries the whole shape: unit of work, both tables, mode, outcomes across components, recommendation; when no RPA consumer exists, one sentence naming what takes the items (a coordinator's trigger, one job per item) replaces the Consumer table. A component genome inside a process carries its own role only — a producer: source, reference rule, what happens to the source item once it is queued; a consumer: its step groups, its outcomes table and counts, its configuration split and traceability; every other component: the stub, with the process genome's decision as the reason — and its Recommendation line reads `per the process genome — applied.` or `per the process genome — not applied.`, never a verdict the process genome did not give. A standalone component genome carries the whole shape for its one project and, having no Components table, states its role word in the first paragraph of its Overview — `dispatcher`, `performer`, `dispatcher + performer` — exactly when the Recommendation is `Apply` (rule 2).
10. **Extracted genomes.** A source already built on the framework fills the section from the source's configuration and framework files (the framework's source guide says which file feeds which row); the framework's plumbing — state transitions, retry counters, status updates, screenshots on exception — is not workflow steps and is listed in the Source Map as a `Framework files` row. A source with a queue producer or consumer, or a per-item loop, and no framework is a candidate: write the shape and mark the Recommendation `*[Inferred]*`.
11. **Two levels of items are still one unit of work.** A source that tracks a parent (a record, a file, a mail) in its own queue or status and the children it expands into (the record's line items, the file's rows, the mail's attachments) has two candidate levels; rule 1 picks one and rule 8 names the other as the alternative. The section is written at the chosen level and the other level is folded in — never a consumer that takes items from two queues, and never a step that is both a Producer row and a step of the consumer's per-item group (rule 5). Children chosen: the parent's population and its expansion into children are one producer (the parent queue, when the source has one, is that producer's own staging and de-duplication store, named in its Reference rule), the consumer takes children only, and parent completion, parent deferral and "complete when every child is final" are bookkeeping in the Effect column or a reporting component's work, never consumer steps. Parent chosen: the children are per-item sub-steps whose individual outcomes are recorded in the parent's outcome reason. Folding changes the run against the source — children produced up front instead of per parent taken, several robots on the children of one parent — so the Recommendation's reason states the change, marked `*[Inferred]*` in an extracted genome.

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
One row per edge between components: mechanism (queue item, start job, Flow invoke, event, file drop, Action Center task), data schema passed, and what happens when the receiving side fails. This table is the data contract; component Interface sections must agree with it. When the Transactional Shape's producer and consumer are two phases of one component exchanging items through a store (a database work table, a folder), add one row for that edge too, marked as intra-component: it is the data contract the shape cites.

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

## Write, Then Offer Edits

Every mode writes the file(s) to the working directory immediately — no preview, no confirmation — then says where they are and asks "Want to adjust anything?". Edits are targeted and in place, never a regeneration; edit tables: [authoring-guide.md](authoring-guide.md) Step 8 and [extraction-guide.md](extraction-guide.md) Step 7.

## Provenance

The body of a genome reads as a specification, not a report: no "the project contains", no file paths in Workflow or Business Rules, no activity or variable names anywhere. Provenance lives only in the Source Map section.
