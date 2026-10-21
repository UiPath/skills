# Genome Format Guide

Content rules for every genome, however produced (authored, extracted, edited). Templates: [component-genome-template.md](../assets/templates/component-genome-template.md), [process-genome-template.md](../assets/templates/process-genome-template.md). Worked examples: [assets/examples/](../assets/examples/).

## Two Levels

| Level | File | Scope | Use when |
|---|---|---|---|
| **Component genome** | `<slug>-genome.md` | One buildable project (RPA process, Flow, BPMN, agent, API workflow, coded app, function, case plan) | Automation is one project. Only file for a standalone automation. |
| **Process genome** | `<slug>-genome.md` plus `<slug>-genome/<component-slug>-genome.md` per component | Business process realised by two or more buildable projects | Solution with ≥2 projects, coordinator (Flow / BPMN / Case) invoking other automations, or described process clearly needing ≥2 components |

Rules:

1. **Choose the level before writing, by the buildable projects the rebuild needs.** One project → component genome only. Two or more projects, or one coordinator plus anything it invokes → process genome plus one component genome per project. The source's own units do not decide it: a single source workflow or bot whose parts the source guide's § Component Detection maps to different project types (a Flow and the RPA process it starts) is a process genome. Never flatten a multi-project process into one component genome; never split a single project into a process genome.
   - **Test components are the one exception to "one component = one project".** Every test component of a process (a group of test cases over data rows for one business area) lives in a *single* test project, `<ProcessName>.Tests`, with one configuration for constants. Each group keeps its own component genome (Interface, rules, criteria), so the process genome still lists them as components, but Deployment counts one test project, and each group's Type cell names it (§ Build With (component) / Components (process)). Never emit one test project per business area. A UiPath test project that is the whole source takes the same shape when it holds two or more groups: a process genome whose components are its groups, plus one shared component for the execution template and the helpers the cases share, which that project already holds; a single group is a component genome. The procedures the test cases of any other source share are a library component (rule 6).
2. **Component genomes inside a process carry the `Part of:` line** immediately after the blueprint blockquote, linking back to the process genome. Standalone component genomes omit it.
3. **Detail lives at the lowest level that owns it.** Component-specific workflow steps, business rules, error handling, and acceptance criteria go in the component genome. The process genome holds only what spans components: process map, handoffs, shared platform dependencies, the transactional shape (its flows, producers and consumers), cross-cutting rules, end-to-end criteria, deployment.
4. **Every section present, always.** Each template section appears in every genome. A section that does not apply gets its stub line (below), never an omission.
5. **Preamble is mandatory, and it routes to this skill.** Every genome starts with the `<!-- UIPATH-AUTOMATION-GENOME: component|process | ... -->` comment and carries the visible blueprint blockquote after the one-liner, both worded as the template words them. Both name `uipath-genome` as the skill that builds the genome: an agent handed the file reads it before it picks a skill, and a preamble naming only the Build With skills sends it straight to them, past the configuration questions and the execution guide. The preamble also prevents an agent from executing the steps instead of building the automation. Build With (component) or Components (process) appears before Workflow / Process Map so an agent meets the skill references before the steps.
6. **Shared behaviour is one library component.** When several components run the same behaviour and the rebuild has to write it because no single UiPath activity performs it — run setup and cleanup, drive mapping, a mail or document-store client — that behaviour is one common library component, and each consumer's steps call it as they call any library. The library is a project of its own, published to a feed and installed in its consumers as a package; it is never a project of the solution (§ Deployment), and that is no reason to fold its workflows into a consumer; only the user's answer at execution folds one ([execution-guide.md § 1.3](execution-guide.md), Library layout). Described in each consumer instead, it is built once per project and the copies drift apart. What one or a few activities do (close an application, append a line to the run's log) stays a step of each consumer. The source guide's § Component Detection names the forms shared behaviour takes in a source.

## File Naming and Location

- Write to user's current working directory unless they name a location.
- Slug: split CamelCase on capitals, lowercase, hyphens for spaces, strip other characters. "Invoice Processing" → `invoice-processing-genome.md`; "InvoiceIntake" → `invoice-intake-genome.md`; "Email Triage & Routing" → `email-triage-routing-genome.md`.
- Extracted genomes take slug from source project or solution name; fall back to directory name.
- Process genome components: `<process-slug>-genome/<component-slug>-genome.md`. Component slug from project name.

## Section Rules

### Overview
Business purpose, who it serves, what triggers it. Write as the author of the automation, never as a describer of files ("this project contains…" is banned). An extracted test suite says in its first sentence that it is a test and what it proves.

### Target Applications (component) / Actors and Systems (process)
Resolve infrastructure to the real system. "Integration Service" is not an application; write "Salesforce", "ServiceNow". Process genomes also list human actors.

### Build With (component) / Components (process)
One skill per row from [skill-mapping-guide.md](skill-mapping-guide.md). Rationale states why that skill and not the nearest alternative. **A process genome's Components table links every component genome** in its Genome column, as a markdown link to `<process-slug>-genome/<component-slug>-genome.md`: execution finds the components only through those links ([execution-guide.md § 1.1](execution-guide.md)).

**Process genomes with test components:** the Type column of every test component reads "Test-case group in project `<ProcessName>.Tests`", and the component diagram nests the test components inside a subgraph for the test project.

### Platform Dependencies
Every Orchestrator or Integration Service resource touched: queues, assets, credentials, storage buckets, connections, folders, triggers. Each row names resource type and purpose. Extracted genomes keep the source resource name; authored genomes propose one.

**Credentials: one credential asset per login account**, named after the account or persona, with its environment or tenant. Scenarios often sign in as several accounts with different roles on different tenants; never collapse them onto one login. The asset holds the secret; the genome and the data rows name the asset — a password, token or secret value never appears in a genome, a data file or a report, and dropping the account identity along with the secret loses which role each scenario ran as. Execution-side declaration: [execution-guide.md § 2.2](execution-guide.md), credentials; naming from a source's accounts: [source-migration-guide.md § Credentials](source-migration-guide.md).

**Identifiers are not credentials.** An application registration's client id and tenant id, a service URL or a mailbox address are Text assets (or configuration values), one per value, even when the source stored them in its credential vault: a credential asset's second half is a secret that a consumer cannot read back as text without a conversion the workflow analyzer rejects at build. The genome names them as Text assets; execution-side rule: [execution-guide.md § 2.2](execution-guide.md), credentials.

### Interface (component)
Inputs, outputs, side effects. Mandatory content for a component inside a process genome (it is the contract the Handoffs table relies on). Standalone components may stub it: "Runs unattended with no arguments; outputs are the side effects listed in Workflow." Name each input and output by its contract name, without the source's direction prefix (`in_`, `out_`, `io_`): `MailboxFolder`, not `in_MailboxFolder`. The source argument is provenance and goes to the Source Map.

**Library components** (a project other components consume as a package) carry, instead of the three bullets, one table per public workflow — never one table shared by several, which hides each workflow's types and directions: `Argument | Direction | Type | Description`. The Type is the one the rebuild gives the argument — a flag is a Boolean and a count a number, whatever text the source carried them in — and the description states the default and the value format (what a flag means, how a date is rendered, which side quotes a value), plus the conventions consumers rely on (naming, defaults, what a failed final check does). This table is the contract consumers are authored against before the library packs; every detail it omits becomes a question between two build groups. A workflow over the analyzer's argument cap (20) carries its optional switches and values in one options object — one In argument with its own table (`Field | Type | Default | Description`).

**State kept between calls.** A library workflow starts each call from its declared defaults, and a library project holds no global variables or constants, so state the source keeps from one call of its actions to the next — a value one action stores and another reads, an attached application or handle, its own instance of another component it calls — lives in the consumer and crosses each call as an argument: Out from the workflow that produces it, In to each that reads it, In/Out where one changes it. A coded library's static field does outlive a call, but as one value for every caller in the job and none inside an isolated invoke, and no Interface shows it, so it holds none of this state. An attached application crosses as the application handle the owning skill's public-workflow contract has workflows return and accept. The conventions name the holder and the work the source ran on its own — set-up before the first call, a close-down when the run ends, after a failure too — each a public workflow the holder calls at that point. The holder follows the source's instances, as the source guide's § Call Graph Rules state them: an instance per caller is held by each caller — a process in its entry workflow for its whole run, passed to the workflows that call the library, and a calling library in its own Interface, since it holds nothing either; one instance per run is held by the run's entry workflow and passed to every caller, calling libraries included. A stored value no action changes is no state: it is a fact or a Configuration Question (§ Configuration Questions).

**Test components** (a group of test cases over data rows in the single test project) list the row schema per test case: the fields that vary per scenario, separately from the constants in the project's configuration. Credentials appear as the name of a credential asset per row, never as values. Each case names its data set — a single row included — with its row count and where the source keeps it, since the rebuild keeps it there ([test-execution-guide.md § Test data](test-execution-guide.md)): a data set kept in a store is the case's data source, the project's test-data entity filtered on the data set's name; one shipped with the project is a variation file in the owning skill's format, named after the case, whose fields stay within the analyzer's argument cap (above). A case with no data set takes its values from configuration constants.

### Configuration Questions
Format: `N. {Question}? ({setting | constant}; default: {value})` — every question names its kind (below) before its default.

**Authored genomes** ask every value the description gives or leaves open: paths, URLs, addresses, server names, credential and queue names, thresholds, column names, and the application choice itself ("Which email provider? (constant; default: Outlook)").

**Extracted genomes ask only what the source leaves open.** The source is the ground truth and a migration keeps its rules, so a value the source fixes has one right answer; asked, it can only be answered with its default. A value is open when it is:

1. **Bound to the environment** the rebuild runs in — hosts and URLs, paths, shares and folders, mailboxes, recipients and senders, domains, system and client entries, the browser, credential, asset, queue, bucket and Data Fabric entity names, schedules, the language model an AI step uses (the tenant decides which models exist), the reach of a clean-up that acts beyond what the run set up (every window of the session, every certificate of the user, every mapped drive). Default: the source's value.
2. **Missing from the export** — a value the build needs that the export does not hold: a setting the source reads from a configuration file, table or vault left out of the export, a caption the source picks only by its key, the starting content of a state file the source reads before it first writes it (a last-used number). Default: the key name and "not in the export".
3. **A choice the source never faced** — the target platform offers a way the source had no counterpart for: an Integration Service connection beside the source's token, the job's log in Orchestrator beside the source's log file. Default: the source's way. The mirror case is open too: the target lacks the source's way, as for an inbound endpoint that took the caller's own token where the target authenticates every caller itself. Default: the target's way, named.
4. **Read from the source's own configuration store** — a key the source reads from a config table, properties file or workbook the export holds, whatever it carries (a host, a timeout, a poll interval, a limit, a flag): the source's owners change it without a release, so the rebuild keeps it changeable. Default: the source's value. A key that only names another resource is a fact (below); the same value written only in the code is a fact.

Every other value is a fact, written once where its reader looks: a value typed, posted, compared or checked, and a limit, length or format, in the Workflow substep or Business Rule that uses it; a wait, timeout, poll interval or attempt count in its step or that step's Error Handling; the item retry and consecutive-failure counts in the Transactional Shape's outcomes ([transactional-shape-guide.md](transactional-shape-guide.md) rule 4); a switch a start argument sets in Interface; the application and a machine prerequisite (Excel installed) in Target Applications; a file the project ships in the step that uses it and the Source Map. Changing a fact is a genome edit, not a configuration answer.

**A setting depends on the environment.** Every Orchestrator connection the automation is deployed to is its own environment — dev, UAT, prod — and the build is often made on another machine and tenant than the one it runs on. Mark each Configuration Question as a *setting* when its answer differs between environments (hosts and URLs, mailboxes and recipients, shares and paths, credential, queue, bucket, asset and Data Fabric entity names, schedules, language models) or must change without a new version (a key the source reads from its configuration store, item 4 above), and as a *constant* when it is the same in every environment and a change to it is a change to the automation (thresholds, limits, retry counts, message texts). The kind is written in the question's parenthesis, before the default: `(setting; default: …)` or `(constant; default: …)`. A configuration key is not by itself one setting: several keys that always carry the same value (one recipient list repeated per notification type) are one setting, and a key whose value only names another resource (a vault alias, a table name fixed by the setup) is a fact. A source's own configuration store (a config table, a properties file, a workbook) is not a Platform Dependency of the rebuild: its keys become questions or facts, and where the rebuild's settings and constants live is decided at execution ([execution-guide.md § 1.3](execution-guide.md)).

Both modes: when the open values run to dozens (a configuration table or procedure), group them by theme into one question per theme and name every key inside its question, before the question mark, so the list stays readable and execution can still map each key: `4. Which folders does the run use — the drive letter (row 5) and the in-process, processed and invalid folders (rows 6–8)? (setting; default: not in the export)`. A grouped question holds values of one kind; a theme whose values are settings and constants is two questions. When an empty value would change the flow instead of failing (an end time that compares as reached, a list matched by containment), the question says so — "required: empty ends the run" — so execution guards it ([execution-guide.md § 1.3](execution-guide.md) rule 8). Questions execution asks itself are not written into the genome: the scaffolding choices (project location, target framework, expression language, installed package versions), and the split questions (unit, split, store, template, triggers and runners) when the Transactional Shape is not the stub ([transactional-execution-guide.md § Split questions](transactional-execution-guide.md)).

### Workflow (component) / Process Map (process)
Numbered steps in execution order, each `N. **{Step name}** (input: …; output: …)`: the number keys the step's row in the Source Map's step table, the bold name heads its Business Rules and Error Handling entries. Steps may be grouped under `###` headings (one per entry point), each step keeping that form. Steps several entry points share are written once, under a heading of their own, and each entry point's last step names the step it continues into. A step that calls an automation the source does not hold (another project's process, a workflow outside the export) names it by what it does, states what the step passes to it and what it uses of the result, and flags `*[Inferred]*` what the caller does not show; the callee is a Platform Dependency the rebuild calls but does not build, and the Source Map's unresolved-invocation row names it. A step involving several fields, a condition, validation, or a transformation gets substeps (a, b, c) and a data annotation `(input: …; output: …)`.

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

**Test components** list one numbered step per test case — `N. **Test case: <title>**` — with the case's steps as lettered substeps and its assertions named in them; the Source Map's step table then has one row per case. A **library** component lists one numbered step per public workflow, grouped by the screen (or stage) it acts on, in the order a user meets the screens; the steps are independent entry points the consumers invoke, not one execution, and a lead-in sentence says so.

**Composite UI interactions carry their full contract.** Source frameworks and descriptions bundle a multi-step interaction into one step: type-ahead pick, menu or tree path, option list, find-row-then-act, keystrokes to the focused element. The substep states, in behavioural words, everything the builder needs to rebuild the interaction: what is typed, how the suggestion or option is matched (equals / contains / nth), which key confirms, each path level, the row rule. "Enter Voluntary into Primary Reason" is a data loss; "type Voluntary into Primary Reason and pick the suggestion that equals Voluntary" is the step. A source guide's composite-actions table gives the wording per source action; execution builds each contract as a pattern ([ui-target-migration-guide.md § Composite interactions](ui-target-migration-guide.md)).

**A source's workaround for its own platform is not behaviour.** A clipboard copy between two ranges, a temporary file written beside the input, a rename around a path the source's script cannot open, a user setting switched to steer a file format: the step states the result the workaround produced, and the Source Map names the workaround — unless a later step reads what it leaves behind, which makes it data.

### Business Rules
Plain language, no code syntax, specific fields and thresholds kept. Group under `### Step N: {name}` headings for the step where the rule fires; a rule or handler several steps share goes once under a heading naming them (`### Steps 4, 10 and 15: …`); cross-step rules under `### General`.

| Code construct | Genome wording |
|---|---|
| `If` / `FlowDecision` / `if` | "If {condition}, then {action}; otherwise {action}" |
| `Switch` / `FlowSwitch` / `switch` | "Route based on {field}: {case} → {action}, {case} → {action}" |
| `AndAlso` / `&&` | "and" |
| `OrElse` / `\|\|` | "or" |
| `>` `<` `=` `<>` `==` `!=` | "exceeds", "is less than", "is", "is not" |

`Amount > 10000 AndAlso Category = "Premium"` → "If amount exceeds $10,000 and category is Premium".

### Error Handling
Same step-associated layout as Business Rules, plus `### Global`. Behavioural wording: "Retries 3× on timeout, then routes the item to the exception queue" — never "RetryScope with NumberOfRetries=3". An entry states the failure, the outcome and the level that handles it; a failure that every UI step shares ("expected element not found: screenshot, stop naming the step") is written once under `### Global`, not repeated per step, and a step entry exists only where that step's handling differs. A Workflow substep's "confirm …" is a post-condition of the action before it, not a separate check (execution builds it as that action's verification).

### Transactional Shape
Whether the automation iterates over units of work — items that succeed, fail, are retried and are tracked independently of one another — and, when it does, per flow how the work is handled today and how it could be divided at build, asserting no split: [transactional-shape-guide.md](transactional-shape-guide.md). A genome with no unit of work carries the stub line (§ Stub Lines).

### Acceptance Criteria
A numbered list (`1. …`), so the execution report's verdicts and a comparison of two runs cite a criterion by its number. Patterns:
- "Given {specific input}, the automation {specific observable outcome}"
- "When {condition}, the automation {expected behaviour}"
- "{Specific action} produces {specific result}"

Sources, one criterion each minimum: every major workflow step, every data transformation or field mapping, every business rule, every error handler, plus edge cases (empty input, duplicate, malformed data).

**A criterion whose outcome rests on a language model's answer is written in one of three checkable forms.** (1) It states the answer: "Given the model classifies the item as {category}, …" — checked with a supplied or recorded answer, so it tests the build, not the model. (2) It states an invariant that holds whatever the model answers: every record's status agrees with the classification it stores, every handled message has exactly one record. (3) For the quality of the model's own answer, it gives an input whose right answer is computed outside the model — dates written out, a count derived from reference data, a value the input itself carries — is checked over several runs, and says it rests on the model, so a miss is a finding on the model, never on the build.

Banned: "completes successfully", "handles errors properly", and anything code-level ("Uses ReadPDF activity", "Calls Main.xaml", "Assigns true to isValid").

| Banned | Acceptable |
|---|---|
| "Uses ReadPDF to process InvoiceFile" | "Given an invoice PDF, extracts vendor_name, invoice_number, line items (description, qty, unit_price), tax, and total" |
| "SendMail sends to admin@company.com" | "When processing fails after retries, sends a notification to the configured administrator with invoice_number and failure reason" |

### Process Map diagrams (process)
Two diagrams, never merged into one:
- **Process view:** BPMN-style swimlane rendered as Mermaid `flowchart TB`, drawn from the Process Map list: one task per stage that routes an item or a case, the stage's exit condition as the gateway or end event after it, one end event per terminal outcome. A stage on a timer or at every run's end (a report, a clean-up) may stay out, since the list carries it. One `subgraph` per party that acts: each human actor, each system whose records the process reads or changes, any party outside the automation, and the automation. A component with its own trigger gets its own lane, in handoff order, with a human lane between the components it sits between; a coordinator's lane holds the tasks of the components it invokes. A mailbox, share or queue that only carries a handoff between two drawn parties is the label of the arrow between them, not a lane. When a component works several items in one run, its per-item loop is drawn: the take-next task, the per-item work, and a back edge from an items-left gateway ([transactional-shape-guide.md](transactional-shape-guide.md)). BPMN shapes: `((Start))` and `(((End)))` events, `[Task]` rectangles prefixed with the component number in brackets, `{Gateway?}` diamonds with labelled yes/no edges, solid arrows for sequence flow inside a lane, dashed arrows (`-.->`) with a label for message or data flow across lanes. Every gateway must have a corresponding rule under Business Rules or Error Handling.
- **Component view:** `flowchart LR` with the solution as a subgraph. Solid arrows are build-time dependencies: an invocation labelled with its mechanism (start job, agent job), a package dependency unlabelled. When every consumer depends on every library, the libraries sit in one nested subgraph with one arrow per consumer. Dashed arrows carry the run-time data passed between components, labelled with it; items handed through a store (a queue, a bucket, a share) run from the producer to the store and on to the consumer. Only platform resources shared by two or more components are drawn, as plain nodes; one that carries no handoff between them is joined by undirected lines (`---`). Target systems belong to the process view.
Mermaid cannot render BPMN 2.0 itself; when the customer wants a formal model, add a sidecar `<process-slug>-process.bpmn` authored from the Process Map (the `uipath-maestro-bpmn` skill knows the format) and link it from this section.

### Handoffs (process)
One row per edge between components: mechanism (queue item, start job, Flow invoke, event, file drop, Action Center task, a shared store one component writes and another reads when asked — a Data Fabric entity, a database table), data schema passed, and what happens when the receiving side fails. This table is the data contract; component Interface sections must agree with it. When the Transactional Shape's producer and consumer are two phases of one component that form a flow ([transactional-shape-guide.md](transactional-shape-guide.md) rule 12) exchanging items through a store (a database work table, a folder), add one row for that edge too, marked as intra-component: it is the data contract the shape cites. Every flow of the Transactional Shape cites the Handoffs row that carries its items.

### Deployment (process)
Packaging (one solution vs independent packages), entry points and triggers, target folders or environments. Name the buildable projects explicitly; a library is listed with the feed it is published to, apart from the solution's projects, since it is never one of them ([execution-guide.md § 1.4](execution-guide.md)); when test components exist, Deployment names exactly one test project and one Test Manager test set per test component.

### Complexity
`simple | medium | complex`. Never ask the user to declare it. Component genomes: inferred from the description ([authoring-guide.md](authoring-guide.md) Step 3) or from source signals ([extraction-guide.md](extraction-guide.md) Step 5); both default to the lower level when ambiguous and escalate when later evidence demands it. Process genomes are `medium` with at most three **buildable projects** and no human lanes, otherwise `complex`; the test-case groups of the single test project count as that one project, not one component each. A human lane is a human actor whose action the process **waits on** (an approval, a task, a mailed decision); recipients of notifications are not lanes.

### Tags
Comma-separated: business domain, target applications, platform features (document-understanding, queues, human-in-the-loop, …).

### Source Map (extraction only)
Where every part of an extracted genome came from — its contract rows, the step table and, for a framework source, the migration contract: [extracted-genome-guide.md § Source Map](extracted-genome-guide.md). Authored genomes have no Source Map.

## Population Matrix (component genomes)

| Section | Simple | Medium | Complex |
|---|---|---|---|
| Overview | 1 paragraph | 2-3 paragraphs | 2-3 paragraphs |
| Target Applications, Build With, Platform Dependencies, Interface, Configuration Questions, Complexity, Tags | Full | Full | Full |
| Workflow | 3-5 steps minimum | 5+ steps, substeps where detailed | 8+ steps, substeps where detailed |
| Business Rules | Stub allowed | Step-associated | Step-associated |
| Error Handling | Stub allowed | Per step where applicable | Per step where applicable |
| Transactional Shape | Full when a unit of work exists ([transactional-shape-guide.md](transactional-shape-guide.md) rule 1), else stub | Full when a unit of work exists, else stub | Full when a unit of work exists, else stub |
| Acceptance Criteria | 3-4 minimum | 5+ incl. data checks | 7+ incl. data checks |

Minimums, not ceilings. Fifteen distinct steps in the source or description means fifteen steps in the genome. A test component's steps are its test cases and a library's its public workflows, so the Workflow minimums apply to neither: their depth is in the cases' checkpoints and the workflows' substeps.

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

When intent is unclear from the source, write the best interpretation, append `*[Inferred]*` to that line, and record the uncertainty in the Source Map. Never leave a section empty because the source is ambiguous. Users remove markers once they confirm the content ("Remove the inferred flags").

## Write, Then Offer Edits

Every mode writes the file(s) to the working directory immediately — no preview, no confirmation — then says where they are and asks "Want to adjust anything?". Edits are targeted and in place, never a regeneration: [editing-guide.md](editing-guide.md).

## Provenance

The body of a genome reads as a specification, not a report: no "the project contains", no file paths in Workflow or Business Rules, no activity or variable names anywhere. Provenance lives only in the Source Map section. A message, log text or text shown to a person (a form's title, instruction or field label) the source writes is behaviour and is written in the body as the source spells it; a text that embeds a variable or activity name, a path or one of the source project's own file names is described in the body instead ("the corrupt-register message") and quoted in full in its step's Source Map row.
