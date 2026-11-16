# Genome Format Guide

Rules for genomes written by `author`, `extract`, and `edit`, or built by `uipath-genome`. Templates (`component-genome-template.md`, `process-genome-template.md`) live in `assets/templates/`.

## Writing Rules

`author`, `extract` and `edit` obey these on every write, beside the Critical Rules in SKILL.md. Each rule names its subject and the section that states it in full; the section's wording is the rule.

1. Choose level before writing: one buildable project is a component genome; two or more are a process genome with one component per project (§ Two Levels).
2. Infer complexity; never ask for it (§ Complexity).
3. Use replication-grade behavioral wording without activity names, variable names, paths, or code syntax in the body, except a case component's build input (§ Interface; § Workflow; § Provenance).
4. Configuration Questions contain only open values (§ Configuration Questions).
5. Include every template section, using its stub when inapplicable (§ Stub Lines).
6. Put one skill per Build With row, using only [skill-mapping-guide.md](skill-mapping-guide.md); put operate-only skills under Platform Dependencies.
7. The preamble and blueprint blockquote name `uipath-genome` as builder; the comment names `uipath-planner` as editor. Build With or Components precedes Workflow or Process Map (§ Two Levels rule 5).
8. Acceptance criteria are specific and testable (§ Acceptance Criteria).
9. Resolve ambiguity with the best interpretation plus `*[Inferred]*` (§ Ambiguity Marker).
10. Write immediately, then offer edits; edits are in place, never regeneration (§ Write, Then Offer Edits; [edit-guide.md](../edit/edit-guide.md)).
11. Composite source actions are genome contracts; `uipath-genome` turns them into patterns (§ Workflow).
12. Describe transactional shape, but record a split only when already decided. The genome asserts no split, store, template, or unit of its own. A flow's `Decided:` line records the split selected by the agreed SDD, user's request, or refactor answers ([transactional-shape-guide.md](transactional-shape-guide.md) rule 8); otherwise `uipath-genome` asks split questions.
13. After every write, review every rule, run the strict check, and fix every `FAIL` before offering edits ([SKILL.md](../../SKILL.md) § Check). `uipath-genome` builds as written.

## Two Levels

| Level | File | Scope | Use when |
|---|---|---|---|
| **Component genome** | `<slug>-genome.md` | One buildable project: RPA process, Flow, BPMN, agent, API workflow, coded app, function, IXP model, decision table, or case plan | One automation project; the only file for a standalone automation |
| **Process genome** | `<slug>-genome.md` plus `<slug>-genome/<component-slug>-genome.md` per component | Business process realized by two or more buildable projects | A solution with ≥2 projects, a coordinator (Flow / BPMN / Case) invoking automations, or a process clearly needing ≥2 components |

1. **Choose the level before writing, by projects needed to rebuild:** one → component only; two or more, or a coordinator plus anything it invokes → process plus one component per project. Source units do not decide this: parts the source guide's § Component Detection maps to different project types (for example, a Flow and the RPA process it starts) require a process genome. Never flatten multiple projects or split one.
   - **Test components are the one exception to "one component = one project".** Every test component of a process (a group of test cases over data rows for one business area) lives in a *single* `<ProcessName>.Tests` project with one configuration for constants. Each group retains its component genome (Interface, rules, criteria); the process lists groups as components; Deployment counts one test project; each Type cell names it (§ Build With (component) / Components (process)). Never emit one test project per business area. A UiPath test project that is the whole source takes the same shape when it holds ≥2 groups: a process genome of its groups plus one shared component for its execution template and helpers; one group is a component genome. The procedures the test cases of any other source share are a library component (rule 6).
2. Put `Part of:` immediately after a process component's blueprint blockquote and link the process genome; standalone components omit it.
3. Put detail at the lowest owner: components hold component workflow, rules, errors, and criteria; processes hold only cross-component map, handoffs, shared dependencies, transactional shape, cross-cutting rules, end-to-end criteria, and deployment.
4. Every template section appears in every genome; use its stub, never omit it.
5. **Preamble is mandatory, and it routes to `uipath-genome`.** Every genome starts with `<!-- UIPATH-AUTOMATION-GENOME: component|process | ... -->`, followed by the visible template-worded blueprint blockquote after the one-liner. Both name `uipath-genome` as builder: an agent handed the file reads it before it picks a skill. The comment also names `uipath-planner` as editor: `uipath-genome` never edits one, so without that line an agent asked for a small change edits the file directly, skipping the edit rules and the checker. The preamble also prevents an agent from executing the steps instead of building the automation. Build With or Components precedes Workflow or Process Map.
6. **Shared behavior is one library component.** Shared behavior requiring more than one or a few UiPath activities — run setup and cleanup, drive mapping, a document-store client, a mail built from templates and rules of its own — is one common library component: a separate project, published to a feed and installed as a package in consumers, never part of the solution's projects (§ Deployment). Consumers call it; do not duplicate or fold it into a consumer unless the user's Library layout answer says so. What one or a few activities do (close an application, append a line to the run's log) stays a step of each consumer. The source guide's § Component Detection defines shared forms.

## File Naming and Location

- Write in the user's current working directory unless another location is named.
- Slug: split CamelCase, lowercase, replace spaces with hyphens, and strip other characters. `Invoice Processing` → `invoice-processing-genome.md`; `InvoiceIntake` → `invoice-intake-genome.md`; `Email Triage & Routing` → `email-triage-routing-genome.md`.
- Extracted genomes use the source project or solution name, falling back to the directory name.
- Process components use `<process-slug>-genome/<component-slug>-genome.md`; derive the component slug from its project name and append its kind (`-process`, `-model`, `-agent`) when slugs collide.
- An SDD genome is beside the SDD: `<process-slug>-sdd.md` → `<process-slug>-genome.md`; `<solution-slug>-solution-sdd.md` → `<solution-slug>-genome.md`, with components in `<solution-slug>-genome/`.

## Section Rules

### Overview
State business purpose, users, and trigger as the automation's author, never as a file description or “this project contains…”. An extracted test suite's first sentence says it is a test and what it proves.

### Target Applications (component) / Actors and Systems (process)
Resolve infrastructure to the real system, not “Integration Service”: write “Salesforce”, “ServiceNow”. Process genomes also list human actors.

### Build With (component) / Components (process)
Use one skill per row from [skill-mapping-guide.md](skill-mapping-guide.md), with rationale over the nearest alternative. **A process genome's Components table links every component genome** in its Genome column, as a markdown link to `<process-slug>-genome/<component-slug>-genome.md`: the build finds the components only through those links.

For process test components, every Type is `Test-case group in project <ProcessName>.Tests`; the Process Map nests them in a subgraph for that test project.

### Platform Dependencies
List every Orchestrator or Integration Service resource touched—queues, assets, credentials, storage buckets, connections, folders, and triggers—with type and purpose. Extracted genomes retain source resource names; authored genomes propose names.

Use one credential asset per login account, named for account/persona plus environment or tenant; never collapse roles or tenants. The asset holds the secret; genomes, data rows, and reports never contain passwords, tokens, or secret values. Preserve account identity. Across component boundaries carry only the asset name in Interface arguments, Handoffs, and start arguments; the consumer reads the secret in its use scope unless an Integration Service connection holds it. A secret without an account (an API key, a token) is a Secret asset.

Identifiers are not credentials: client ID, tenant ID, service URL, and mailbox address are separate Text assets or configuration values, even in a credential vault. Name and declare them as Text assets. A credential's secret cannot be read back as text without a conversion rejected by the workflow analyzer.

A value the source platform holds outside the process and sets per environment — an environment variable, a global value — is one asset, named as the source names it and typed Text, Integer, Bool, Secret, or credential as appropriate. Open values become Configuration Questions naming the asset. A component whose type reads no assets keeps such a value in the variable its owning skill provides. A source configuration store is not such a value (§ Configuration Questions).

### Interface (component)
State inputs, outputs, and side effects. Mandatory inside a process; a standalone component may use: `Runs unattended with no arguments; outputs are the side effects listed in Workflow.` Do not use source direction prefixes (`in_`, `out_`, `io_`): `MailboxFolder`, not `in_MailboxFolder`. Qualify reserved Visual Basic/C# words and .NET namespaces/types (`To`, `Sub`, `Date`, `Type`, `Object`, `System`), e.g. `ToAddresses`, `KeyDate`, or `SapSystem`; expression language is chosen at build. Source arguments belong in Source Map.

A `uipath-maestro-case` component designed by a Case Management SDD names that SDD's path relative to the genome as build input: `uipath-genome` hands it unchanged to `uipath-maestro-case`, which builds from it without redesign.

**Library components** (a project other components consume as a package) carry, instead of the three bullets, one `Argument | Direction | Type | Description` table per public workflow — never one table shared by several, which hides each workflow's types and directions. Types are rebuild types (a flag is Boolean and a count is a number); descriptions include default, format, quoting side, consumer conventions, naming, defaults, and failed-final-check behavior. This is the pre-build contract; omissions become questions between build groups. Over the analyzer's argument cap (20), put optional switches and values in one options object with one In argument and a `Field | Type | Default | Description` table.

**State kept between calls.** Each library workflow starts from declared defaults; no global variables or constants. State one action stores for another, attached applications/handles, and called-component instances live in the consumer and cross each call as an argument: Out from the workflow that produces it, In to each that reads it, In/Out where one changes it. A coded library static field outlives a call only as one value shared by every caller in the job and none inside an isolated invoke; it is not shown in Interface and holds none of this state. An attached application crosses as the application handle the owning skill's public-workflow contract has workflows return and accept. Describe setup before first call and cleanup at run end, including after failure, as public workflows, naming holder and source work. Follow the source guide's § Call Graph Rules: an instance per caller is held by each caller (a process in its entry workflow for the run, passed to callers, and a calling library in its Interface); one instance per run is held by the entry workflow and passed to every caller, including libraries. An unchanged stored value is a fact or Configuration Question, not state.

**Test components** list each test case's varying row schema separately from project constants; credentials are credential-asset names, never values. Name each case's data set — a single row included — its row count, and source location, retaining that location: a data set kept in a store is the case's data source: the project's test-data entity filtered on the data set's name; shipped data is a variation file in the owning skill's format, named after the case, with fields within the analyzer's argument cap (20). A case without a data set uses configuration constants.

### Configuration Questions
Use `N. {Question}? ({setting | constant}; default: {value})`; every question states kind before default.

Authored genomes ask every described or open value, including paths, URLs, addresses, servers, credentials, queues, thresholds, columns, and application choice (“Which email provider? (constant; default: Outlook)”). Extracted genomes ask only source-open values; source-fixed values are facts. A source value is open when it is:

1. **Environment-bound:** hosts/URLs, paths/shares/folders, mailboxes, recipients/senders, domains, system/client entries, browser, credentials, assets, queues, buckets, Data Fabric entities, schedules, AI language model (the tenant decides which models exist), or cleanup reach beyond run setup (every window of the session, every certificate of the user, every mapped drive). Default is source value.
2. **Missing from export:** required configuration-file/table/vault value, key-selected caption, or initial state-file content (a last-used number). Default is key name and `not in the export`.
3. **A target choice absent from source:** e.g. an Integration Service connection beside a source token. Default is source method. The log defaults to the job's Orchestrator log while retaining the source log as an option ([extract-guide.md](../extract/extract-guide.md) Step 3, evidence policy). The mirror case—target lacks the source method, such as an inbound endpoint whose caller supplied a token while target authenticates callers—is open; default is the named target method.
4. **Read from the source configuration store:** config table, properties file, or workbook value the export holds, including host, timeout, poll interval, limit, or flag. Default is source value. A key naming another resource is a fact; a value only in code is also a fact.

All other values are facts where used: data values, comparisons, limits, lengths, and formats in Workflow or Business Rule; waits, timeouts, polls, and attempt counts in the step or Error Handling; item retry and consecutive-failure counts in Transactional Shape outcomes ([transactional-shape-guide.md](transactional-shape-guide.md) rule 4); start switches in Interface; applications and machine prerequisites in Target Applications; shipped files in their using step and Source Map. Changing a fact is a genome edit.

Every Orchestrator connection the automation is deployed to is its own environment — dev, UAT, prod — and the build is often made on another machine and tenant than the one it runs on. Mark a question `setting` when it differs by environment (hosts and URLs, mailboxes and recipients, shares and paths, credential, queue, bucket, asset and Data Fabric entity names, schedules, language models) or must change without a new version (item 4); mark it `constant` when identical across environments and changing it changes the automation (thresholds, limits, retry counts, message texts). Use exactly `(setting; default: …)` or `(constant; default: …)`. A configuration key is not by itself one setting: several keys that always carry the same value (one recipient list repeated per notification type) are one setting, and a key whose value only names another resource (a vault alias, a table name fixed by the setup) is a fact. The source configuration store is not a rebuilt Platform Dependency. Where rebuilt settings/constants live is decided by execution configuration questions.

When open values number dozens, group by theme and name every key before the question mark: `4. Which folders does the run use — the drive letter (row 5) and the in-process, processed and invalid folders (rows 6–8)? (setting; default: not in the export)`. Each group has one kind, so mixed themes become two questions. State when empty changes flow rather than fails (for example, `required: empty ends the run`). Do not write scaffolding questions—project location, target framework, expression language, package versions—or split questions (unit, split, store, template, triggers, runners) when Transactional Shape is not a stub.

### Workflow (component) / Process Map (process)
Write numbered steps in execution order as `N. **{Step name}** (input: …; output: …)`. The number keys the Source Map row; the bold name keys Business Rules and Error Handling. Steps may be grouped under `###` headings (one per entry point), each step keeping that form. Shared steps appear once under their own heading; each entry point's last step names its continuation. Use lettered substeps for multiple fields, conditions, validation, or transformations, with input/output annotations.

A step calling an automation not held by the source (another project's process, a workflow outside the export) names behavior, passed inputs, and used results, flags `*[Inferred]*` what the caller does not show, and treats the callee as a Platform Dependency rather than something built; Source Map records an unresolved invocation.

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

Test: if a builder cannot rebuild the step from the text alone, add detail. Never combine distinct steps to meet a count.

Test components use one `N. **Test case: <title>**` per case, with lettered case steps and assertions; Source Map has one row per case. Libraries use one numbered step per public workflow, grouped by screen/stage in user order, as independent entry points rather than one execution, with a lead-in saying so.

Composite interactions (type-ahead pick, menu or tree path, option list, find-row-then-act, keystrokes to the focused element) are full contracts: typed value, matching method (equals/contains/nth), confirming key, every path level, row rule, and other builder-required behavior. “Enter Voluntary into Primary Reason” is a data loss; “type Voluntary into Primary Reason and pick the suggestion that equals Voluntary” is the step. Use the source guide's composite-actions wording; execution builds each contract as a pattern.

A substep in a dialog, popup, or browser tab opened by an action names that window: “in the Select Vendor dialog, click OK”. If the source acts there without switching, infer the name from the opening action and mark `*[Inferred]*`.

A source-platform workaround is not behavior (a clipboard copy between two ranges, a temporary file written beside the input, a rename around a path the source's script cannot open, a user setting switched to steer a file format): state its produced result and identify the workaround in Source Map. It becomes data if a later step reads what it leaves behind.

### Business Rules
Use plain language, no code syntax, with fields and thresholds; group under `### Step N: {name}`, shared rules under a heading naming all steps (`### Steps 4, 10 and 15: …`), and cross-step rules under `### General`.

| Code construct | Genome wording |
|---|---|
| `If` / `FlowDecision` / `if` | `If {condition}, then {action}; otherwise {action}` |
| `Switch` / `FlowSwitch` / `switch` | `Route based on {field}: {case} → {action}, {case} → {action}` |
| `AndAlso` / `&&` | `and` |
| `OrElse` / `\|\|` | `or` |
| `>` `<` `=` `<>` `==` `!=` | `exceeds`, `is less than`, `is`, `is not` |

`Amount > 10000 AndAlso Category = "Premium"` → “If amount exceeds $10,000 and category is Premium”.

### Error Handling
Use the same step-associated layout plus `### Global`. State failure, outcome, and handling level behaviorally, including retry counts and routes: “Retries 3× on timeout, then routes the item to the exception queue” — never “RetryScope with NumberOfRetries=3”. A failure every UI step shares (“expected element not found: screenshot, stop naming the step”) is one Global entry; add a step entry only when handling differs. A Workflow substep confirming an action is that action's post-condition, not a separate check.

### Transactional Shape
State whether the automation iterates independently tracked units that succeed, fail, retry, and are tracked; if so, state each flow's handling and possible build division while asserting no split except a `Decided:` line records. Follow [transactional-shape-guide.md](transactional-shape-guide.md). No-unit genomes use the § Stub Lines stub.

### Acceptance Criteria
Use numbered criteria (`1. …`) so reports and run comparisons cite numbers. Write at least one criterion per source: every major workflow step, transformation/field mapping, business rule, error handler, plus empty, duplicate, and malformed-data edge cases. Patterns:

- "Given {specific input}, the automation {specific observable outcome}"
- "When {condition}, the automation {expected behaviour}"
- "{Specific action} produces {specific result}"

 never use “completes successfully”, “handles errors properly”, or code-level claims (“Uses ReadPDF activity”, “Calls Main.xaml”, “Assigns true to isValid”).

| Banned | Acceptable |
|---|---|
| "Uses ReadPDF to process InvoiceFile" | "Given an invoice PDF, extracts vendor_name, invoice_number, line items (description, qty, unit_price), tax, and total" |
| "SendMail sends to admin@company.com" | "When processing fails after retries, sends a notification to the configured administrator with invoice_number and failure reason" |

For language-model outcomes use one checkable form: (1) state the answer (“Given the model classifies the item as {category}, …”) and check against a supplied/recorded answer; (2) state an invariant independent of the answer (every record's status agrees with the classification it stores, every handled message has exactly one record); or (3) test quality against an answer computed outside the model (dates written out, a count derived from reference data, a value the input itself carries) over several runs, explicitly attributing misses to the model, not the build.

### Complexity
Use only `simple | medium | complex`; never ask the user. Component level comes from description, PDD, or SDD ([author-guide.md](../author/author-guide.md) § Step 3 — Infer complexity), or source signals ([extract-guide.md](../extract/extract-guide.md) § Step 5 — Infer complexity (component)); default lower when ambiguous and escalate when evidence requires. Process is `medium` with at most three **buildable projects**, no human lanes, and no `complex` component; otherwise `complex`. Test groups in one test project count as one project. A human lane is an actor the process waits on (approval, task, mailed decision), not a notification recipient.

### Tags
Comma-separated business domain, target applications, and platform features (document-understanding, queues, human-in-the-loop, …).

### Source Map (extraction only)
Record where every extracted genome element came from, including contract rows, step table, and framework migration contract: [extracted-genome-guide.md § Source Map](extracted-genome-guide.md). Authored genomes have none.

## Population Matrix (component genomes)

| Section | Simple | Medium | Complex |
|---|---|---|---|
| Overview | 1 paragraph | 2-3 paragraphs | 2-3 paragraphs |
| Target Applications, Build With, Platform Dependencies, Interface, Configuration Questions, Complexity, Tags | Full | Full | Full |
| Workflow | 3-5 steps minimum | 5+ steps, substeps where detailed | 8+ steps, substeps where detailed |
| Business Rules | Stub allowed | Step-associated | Step-associated |
| Error Handling | Stub allowed | Per applicable step | Per applicable step |
| Transactional Shape | Full when a unit exists ([transactional-shape-guide.md](transactional-shape-guide.md) rule 1), else stub | Full when a unit of work exists, else stub | Full when a unit of work exists, else stub |
| Acceptance Criteria | 3-4 minimum | 5+ including data checks | 7+ including data checks |

These are minimums, not ceilings. Preserve fifteen distinct source/description steps as fifteen genome steps. Test steps are cases and library steps are public workflows; their depth is in checkpoints and substeps, so Workflow minimums do not apply.

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

For unclear intent, write the best interpretation, append `*[Inferred]*`, and record uncertainty in Source Map. Never leave a section empty. Users remove markers with “Remove the inferred flags”.

## Write, Then Offer Edits

Every writing verb writes files to the working directory immediately—no preview or confirmation—then reports their location and asks “Want to adjust anything?”. Only the writing skill's `edit` verb makes targeted in-place edits; never regenerate.

## Provenance

Genome bodies are specifications, not reports: never write “the project contains”, file paths in Workflow or Business Rules, or activity/variable names anywhere. Provenance belongs only in Source Map. Source-written messages, log text, and text shown to people (a form's title, instruction or field label) are behavior and retain source spelling. If text embeds a variable/activity name, path, or source-project file name, describe it instead (for example, “the corrupt-register message”) and quote it fully in that step's Source Map row.

## Process Genome Sections

Only process genomes have these sections.

### Process Map diagrams (process)
Under `## Process Map`, after the numbered stage list and without a subheading, include one Mermaid `flowchart TB` component-view diagram. Sequence belongs in the stage list, not the diagram.

- Nodes are automation components and queues only: no people or outside systems. One node per queue, never grouped, using cylinder `[( )]` with no number. Component nodes carry their Components-table number in brackets.
- Prefix triggers: ⏰ time, 🔔 queue-consuming component. No mark means invoked by another component; several entry points carry each applicable mark. Mark source-absent schedules `*[Inferred]*`. Legend below names marks and arrows.
- Arrows show data/work direction; never double-headed; draw two. Solid means component→queue, queue→component, or caller→callee. Dotted means file/mail handoff. A queue inside one component is in its label, e.g. `2 InvoiceProcess<br/>Dispatcher → queue → Performer`, never a self-loop.
- Wrap labels with `<br/>` at about 34 characters and edge labels at about 26; never wrap subgraph titles. Test-project components may share a subgraph. If mermaid-cli is installed, render and inspect; otherwise use these widths.

Mermaid cannot render BPMN 2.0. For a formal model, add sidecar `<process-slug>-process.bpmn` authored from Process Map; `uipath-maestro-bpmn` knows the format, and link it here.

### Handoffs (process)
Use one row per component edge, giving mechanism (queue item, start job, Flow invoke, event, file drop, Action Center task, or shared store such as a Data Fabric entity/database table), schema, and receiving-failure behavior. Component Interface must agree. For a Transactional Shape flow whose producer and consumer are phases of one component that form a flow ([transactional-shape-guide.md](transactional-shape-guide.md) rule 12) exchanging items through a store (a database work table, a folder, an in-memory work list the job reads once and then works item by item), add an intra-component row naming stages/sub-projects from `Decided:`; every shape flow cites its Handoffs row.

Omit rows for people or systems merely read/acted on; retain human-task rows created by a component. Use one row per queue edge, naming queue(s), never “the queues”, and one per call and file/mail handoff.

### Deployment (process)
State packaging (one solution or independent packages), entry points/triggers, target folders/environments, and every buildable project explicitly. List each library separately with its feed, never as a solution project. With tests, name exactly one test project and one Test Manager test set per test component.

## Design Links

After the blueprint blockquote, optionally add one blockquote linking the process genome or standalone component to an existing source document; never invent it:

`> Designed in: [<SDD title>](<relative path to the SDD>) · sdd-sha256 <SDD_FINGERPRINT>`

The fingerprint is mandatory. Obtain it only after content is final by running `node "<SKILL_DIR>/scripts/sdd-fingerprint.mjs" "<SDD_PATH>"`, where `<SKILL_DIR>` contains this skill's `SKILL.md`. For a solution, `<SDD_PATH>` is the root SDD and the fingerprint covers root plus every listed child SDD. The SDD's `Genome` row and an older `Tasks file` row do not change it.

The build builds as written and hands a case SDD unchanged to `uipath-maestro-case`. `uipath-planner` keeps the genome current: an SDD change ends with `edit`'s “The SDD was revised” ([edit-guide.md](../edit/edit-guide.md)) and a new fingerprint ([sdd-writing-guide.md](../design/sdd-writing-guide.md) § Keeping the Genome Current). Strict check fails a `Designed in:` line whose fingerprint no longer matches its SDD (root plus every child for a solution), or whose SDD cannot be read.

Record SDD decisions—split and queue design, implementation mode, package pins, and refactor answers—in their owning sections: a flow's `Decided:` line, Configuration Questions defaults, or process Deployment. Restate the SDD's products and projects without contradiction; which changes to a designed genome go to `design` first is specified by [edit-guide.md](../edit/edit-guide.md) § Any genome.