# Genome Format Guide

Content rules for every genome, however produced — `author`, `extract` and `edit` write genomes; `uipath-genome` builds them. Templates (`component-genome-template.md`, `process-genome-template.md`) live in `assets/templates/`. The sections only a process genome has: [process-genome-sections-guide.md](process-genome-sections-guide.md).

## Writing Rules

`author`, `extract` and `edit` obey these on every write, beside the Critical Rules in SKILL.md. Each rule names its subject and the section that states it in full; the section's wording is the rule.

1. **Choose the genome level before writing**: one buildable project is a component genome, two or more a process genome with one component genome per project — § Two Levels.
2. **Infer complexity, never ask for it** — § Complexity.
3. **Replication-grade detail in behavioural wording**, with formulas kept and no activity names, variable names, file paths or code syntax in the body (a component built from its SDD excepted — § Components Built from the SDD) — § Workflow, § Business Rules and § Provenance.
4. **Configuration Questions carry only the values left open** — [genome-questions-guide.md § Configuration Questions](genome-questions-guide.md).
4a. **Every point left to a person is an Open Decisions entry**, named where the genome marks it — [genome-questions-guide.md § Open Decisions](genome-questions-guide.md).
5. **Every template section present, always** — the Source Map in extracted genomes only — with a stub line where one does not apply — § Stub Lines.
6. **One skill per Build With row, from the mapping guide only**; operate-only skills belong under Platform Dependencies — [skill-mapping-guide.md](skill-mapping-guide.md).
7. **The preamble and the blueprint blockquote name `uipath-genome` as the skill that builds the genome, and the comment names `uipath-planner` as the skill that changes it**, and Build With (or Components) precedes Workflow (or Process Map) — § Two Levels rule 5.
8. **Acceptance criteria are specific and testable** — § Acceptance Criteria.
9. **Flag ambiguity, never leave gaps**: the best interpretation plus `*[Inferred: D<n>]*`, naming the entry that asks it — [genome-questions-guide.md § Ambiguity Marker](genome-questions-guide.md).
10. **Write immediately, offer edits after**; edits are in place, never a regeneration — § Write, Then Offer Edits; [edit-guide.md](../edit/edit-guide.md).
11. **Composite source actions are contracts in the genome** — § Workflow; `uipath-genome` turns them into patterns.
12. **The transactional shape is described, never decided**: the genome asserts no split, store, template or unit of its own; a split already decided is the flow's `Decided:` line ([transactional-shape-guide.md](transactional-shape-guide.md) rule 8).
13. **Checked after every write**: the writer reviews every write against these rules, then runs [SKILL.md § Check](../../SKILL.md#check) before offering edits.

## Two Levels

| Level | File | Scope | Use when |
|---|---|---|---|
| **Component genome** | `<slug>-genome.md` | One buildable project (RPA process, Flow, BPMN, agent, API workflow, coded app, function, IXP model, decision table, case plan) | Automation is one project. Only file for a standalone automation. |
| **Process genome** | `<slug>-genome.md` plus `<slug>-genome/<component-slug>-genome.md` per component | Business process realised by two or more buildable projects | Solution with ≥2 projects, coordinator (Flow / BPMN / Case) invoking other automations, or described process clearly needing ≥2 components |

Rules:

1. **Choose the level before writing, by the buildable projects the rebuild needs.** One project → component genome only. Two or more projects, or one coordinator plus anything it invokes → process genome plus one component genome per project. A dispatcher and the performer that works its queue are one project for this count: one `uipath-rpa` component, the split recorded in its Transactional Shape. The source's own units do not decide it: a single source workflow or bot whose parts the source guide's § Component Detection maps to different project types (a Flow and the RPA process it starts) is a process genome. Never flatten a multi-project process into one component genome; never split a single project into a process genome.
   - **Test components are the one exception to "one component = one project".** Every test component of a process (a group of test cases over data rows for one business area) lives in a *single* test project, `<ProcessName>.Tests`, with one configuration for constants. Each group keeps its own component genome (Interface, rules, criteria), so the process genome still lists them as components, but Deployment counts one test project, and each group's Type cell names it (§ Build With (component) / Components (process)). Never emit one test project per business area. A UiPath test project that is the whole source takes the same shape when it holds two or more groups: a process genome whose components are its groups, plus one shared component for the execution template and the helpers the cases share, which that project already holds. A single group is a component genome. The procedures the test cases of any other source share are a library component (rule 6).
2. **Component genomes inside a process carry the `Part of:` line** immediately after the blueprint blockquote, linking back to the process genome. Standalone component genomes omit it.
3. **Detail lives at the lowest level that owns it.** Component-specific workflow steps, business rules, error handling, and acceptance criteria go in the component genome. The process genome holds only what spans components: process map, handoffs, shared platform dependencies, the transactional shape (its flows, producers and consumers), cross-cutting rules, end-to-end criteria, deployment. A standalone component genome has no Deployment: its entry point and whether it runs attended are in Interface, how it starts in the Triggers table, and the data kept out of its logs is a Business Rule.
4. **Every section present, always.** Every template section except the Source Map (extraction only) appears in every genome. A section that does not apply gets its stub line (below), never an omission.
5. **Preamble is mandatory, and it routes to `uipath-genome`.** Every genome starts with the `<!-- UIPATH-AUTOMATION-GENOME: component|process | ... -->` comment and carries the visible blueprint blockquote after the one-liner, both worded as the template words them. Both name `uipath-genome` as the skill that builds the genome, so an agent handed the file never starts from a Build With skill or executes the steps. The comment also names `uipath-planner` as the skill that changes the genome, so an agent asked for a change never edits the file directly. Build With (component) or Components (process) appears before Workflow / Process Map.
6. **Shared behaviour is one library component.** When several components run the same behaviour and the rebuild has to write it because it is more than one or a few UiPath activities do, that behaviour is one common library component. Examples: run setup and cleanup, drive mapping, a document-store client, a mail built from templates and rules of its own. Each consumer's steps call it as they call any library. The library is a project of its own, published to a feed and installed in its consumers as a package. Where the source delivers its modules to each consumer without a feed — copied into the consumer's project or into the package it packs, or imported by a path the consumer's build resolves — the library is a folder of modules the rebuild delivers the same way. Its Build With rationale names the route and the consumers. It is never a project of the solution ([process-genome-sections-guide.md § Deployment (process)](process-genome-sections-guide.md)), and that is no reason to fold its workflows into a consumer. Only the user's answer to the build's configuration questions folds one (Library layout). Described in each consumer instead, it is built once per project and the copies drift apart. What one or a few activities do (close an application, append a line to the run's log) stays a step of each consumer. Shared code a refactor keeps, because consumers outside its scope still use it, is no component: the rebuild calls it as the source does, each calling step states what the call does, and the Source Map names the module and function. The source guide's § Component Detection names the forms shared behaviour takes in a source.

## File Naming and Location

- Write to user's current working directory unless they name a location.
- Slug: split CamelCase on capitals, lowercase, hyphens for spaces and underscores, strip other characters. "Invoice Processing" → `invoice-processing-genome.md`; "InvoiceIntake" → `invoice-intake-genome.md`; "Email Triage & Routing" → `email-triage-routing-genome.md`.
- Extracted genomes take slug from source project or solution name; fall back to directory name.
- Process genome components: `<process-slug>-genome/<component-slug>-genome.md`; the process genome `<process-slug>-genome.md` sits beside that folder, never inside it. Component slug from project name; when two components would share a slug, each adds its kind (`-process`, `-model`, `-agent`).
- A genome authored from an SDD is written beside it, named after it: `<process-slug>-sdd.md` → `<process-slug>-genome.md`. A solution SDD gets one genome, named after its root and written beside it: `<solution-slug>-solution-sdd.md` → `<solution-slug>-genome.md`, its component genomes in `<solution-slug>-genome/`.

## Section Rules

### Overview
Business purpose, who it serves, what triggers it. Write as the author of the automation, never as a describer of files ("this project contains…" is banned). An extracted test suite says in its first sentence that it is a test and what it proves.

### Target Applications (component) / Actors and Systems (process)
Resolve infrastructure to the real system. "Integration Service" is not an application; write "Salesforce", "ServiceNow". Process genomes also list human actors. A genome with UI steps names the environment its targets were taken from, `UI targets: <environment>`: a process genome on a line after its Deployment bullets ([process-genome-sections-guide.md § Deployment (process)](process-genome-sections-guide.md)), a component genome in its Target Applications row's Notes cell, so the build can offer it.

### Build With (component) / Components (process)
One skill per row from [skill-mapping-guide.md](skill-mapping-guide.md). Rationale states why that skill and not the nearest alternative. **A process genome's Components table links every component genome** in its Genome column, as a markdown link to `<process-slug>-genome/<component-slug>-genome.md`: the build finds the components only through those links.

**Process genomes with test components:** the Type column of every test component reads "Test-case group in project `<ProcessName>.Tests`", and the Process Map diagram nests the test components inside a subgraph for the test project.

### Platform Dependencies
Every Orchestrator, Integration Service and other UiPath service resource the automation touches, laid out so that a reader sees what the build declares and hands over for the target environment: one `###` table per kind the automation uses, in this order, a kind it does not use left out. Extracted genomes keep the source resource name and take each field from the source — a UiPath source's from its deployed state ([uipath-source-guide.md § Deployed State](../extract/uipath-source-guide.md)); authored genomes propose names. A field the source or the description does not show is classed as [genome-questions-guide.md § Open Decisions](genome-questions-guide.md) classes a point, a value bound to the environment being the Configuration Question that asks it. *Used by* names steps in a component genome, components in a process genome.

| Kind | Columns |
|---|---|
| Queues | Queue · One item is · Item fields (name: type) · Unique reference · Retries · Added by · Worked by |
| Assets | Asset · Type (Text, Integer, Bool, Secret) · Value (the fixed value, or the Configuration Question that asks it; never a secret) · Used by · Purpose |
| Credentials | Asset · Account or persona · Signs in to · Used by |
| Storage buckets | Bucket · Holds · Written by · Read by |
| Connections | Connection · Connector · Signs in as · Used by |
| Data Fabric entities | Entity · Fields (name: type) · Written by · Read by |
| Triggers | Trigger · Starts · Kind (time, queue, event, API) · When (schedule and time zone, the queue, the event, or the API endpoint) · Runners |
| each other service (Action Center, Document Understanding, Test Manager, Context Grounding) | Resource · Used by · Purpose |

A transactional flow's queues and triggers are its As-is: the split answers can change them ([transactional-shape-guide.md](transactional-shape-guide.md)).

**Credentials: one credential asset per login account**, named after the account or persona, with its environment or tenant. Scenarios often sign in as several accounts with different roles on different tenants; never collapse them onto one login. The asset holds the secret; the genome and the data rows name the asset — a password, token or secret value never appears in a genome, a data file or a report, and dropping the account identity along with the secret loses which role each scenario ran as. A secret crosses no component boundary: an Interface argument, a Handoffs row and a start argument carry the asset's name, and the component that uses the secret reads it in the scope that uses it, unless a connection holds the secret (an Integration Service connection). A secret with no account behind it (an API key, a token) is a Secret asset.

**Identifiers are not credentials.** An application registration's client id and tenant id, a service URL or a mailbox address are Text assets (or configuration values), one per value, even when the source stored them in its credential vault. Reason: a credential asset's second half is a secret that a consumer cannot read back as text without a conversion the workflow analyzer rejects at build. The genome names them as Text assets; execution declares them the same way.

A value the source platform keeps per environment: [extracted-genome-guide.md § Source Constructs](extracted-genome-guide.md).

### Interface (component)
Inputs, outputs, side effects. Mandatory content for a component inside a process genome (it is the contract the Handoffs table relies on). Standalone components may stub it: "Runs unattended with no arguments; outputs are the side effects listed in Workflow." Name each input and output by the contract name its callers bind to, spelled as the source spells it, without the source's direction prefix (`in_`, `out_`, `io_`): `MailboxFolder`, not `in_MailboxFolder`. A contract name that is a reserved word of Visual Basic or C#, or a .NET namespace or type name (`To`, `Sub`, `Date`, `Type`, `Object`, `System`), takes a qualifier (`ToAddresses`, `KeyDate`, `SapSystem`). Reason: the expression language is chosen at build, and such a name breaks the expressions of one of the two. The source argument is provenance and goes to the Source Map. A component built from its SDD: § Components Built from the SDD.

**Library components** (a project other components consume as a package, or modules delivered to them without a feed) carry, instead of the three bullets, one table per public workflow — never one table shared by several, which hides each workflow's types and directions: `Argument | Direction | Type | Description`. The Type is the one the rebuild gives the argument — a flag is a Boolean and a count a number, whatever text the source carried them in. The description states the default and the value format (what a flag means, how a date is rendered, which side quotes a value), plus the conventions consumers rely on (naming, defaults, what a failed final check does). This table is the contract consumers are authored against before the library packs; every detail it omits becomes a question between two build groups. A workflow over the analyzer's argument cap (20) carries its optional switches and values in one options object — one In argument with its own table (`Field | Type | Default | Description`).

**State kept between calls.** A library workflow starts each call from its declared defaults, and a library project holds no global variables or constants. State the source keeps from one call of its actions to the next therefore lives in the consumer and crosses each call as an argument. Such state is a value one action stores and another reads, an attached application or handle, or its own instance of another component it calls. The argument is Out from the workflow that produces it, In to each that reads it, In/Out where one changes it. A coded library's static field does outlive a call, but as one value for every caller in the job and none inside an isolated invoke, and no Interface shows it, so it holds none of this state. An attached application crosses as the application handle the owning skill's public-workflow contract has workflows return and accept. The conventions name the holder and the work the source ran on its own — set-up before the first call, a close-down when the run ends, after a failure too — each a public workflow the holder calls at that point. The holder follows the source's instances, as the source guide's § Call Graph Rules state them:

- An instance per caller is held by each caller: a process in its entry workflow for its whole run, passed to the workflows that call the library, and a calling library in its own Interface, since it holds nothing either.
- One instance per run is held by the run's entry workflow and passed to every caller, calling libraries included.

A stored value no action changes is no state: it is a fact or a Configuration Question ([genome-questions-guide.md § Configuration Questions](genome-questions-guide.md)).

**A value passed down only to reach its reader is the reader's own read.** A value is read by the step that uses it, and is no argument of the workflows it passes through, when both hold:

- It is the same wherever and whenever the run reads it — the machine name, the user name, the robot's name.
- The source reads it once and passes it through calls only to reach that step.

A value the caller computes or changes, or one that must hold the value of one moment for the whole run (the run's start time), stays an argument.

**Test components** (a group of test cases over data rows in the single test project) list the row schema per test case: the fields that vary per scenario, separately from the constants in the project's configuration. Credentials appear as the name of a credential asset per row, never as values. Each case names its data set — a single row included — with its row count and where the source keeps it, since the rebuild keeps it there:

- A data set kept in a store is the case's data source, the project's test-data entity filtered on the data set's name.
- One shipped with the project is a variation file in the owning skill's format, named after the case, whose fields stay within the analyzer's argument cap (above).

A case with no data set takes its values from configuration constants.

### Components Built from the SDD
A component whose build skill takes the designed SDD as its build input ([skill-mapping-guide.md § Build Skills](skill-mapping-guide.md#build-skills), "Built from the SDD"):
- its Interface names that SDD's path, relative to the genome, as the component's build input — the one path a genome body carries (Writing Rule 3);
- `uipath-genome` hands that SDD to the build skill unchanged, and the component is built from it, never redesigned.

### Configuration Questions
The values left open: [genome-questions-guide.md § Configuration Questions](genome-questions-guide.md).

### Open Decisions
The points left to a person: [genome-questions-guide.md § Open Decisions](genome-questions-guide.md).

### Workflow (component) / Process Map (process)
Numbered steps in execution order, each `N. **{Step name}** (input: …; output: …)`: the number keys the step's row in the Source Map's step table, the bold name heads its Business Rules and Error Handling entries. Steps may be grouped under `###` headings (one per entry point), each step keeping that form. Steps several entry points share are written once, under a heading of their own, and each entry point's last step names the step it continues into. A step that calls an automation the source does not hold (another project's process, a workflow outside the export) names it by what it does, states what the step passes to it and what it uses of the result, and flags `*[Inferred]*` what the caller does not show. The callee is a Platform Dependency the rebuild calls but does not build, and the Source Map's unresolved-invocation row names it. A step involving several fields, a condition, validation, or a transformation gets substeps (a, b, c) and a data annotation `(input: …; output: …)`.

Shallow, insufficient for replication:
```markdown
3. **Validate**: Check the invoice against the purchase order.
```

Sufficient:
```markdown
3. **Validate invoice against purchase order** (input: extracted invoice record; output: validation result with discrepancies):
   a. Match vendor_id to the vendor master
   b. Match PO number to open POs for that vendor
   c. The line items whose description, quantity or unit_price differ from their PO line
   d. Verify quantity × unit_price sums to the invoice subtotal, and subtotal + tax = total within the configured tolerance (default 1%)
   e. If any mismatch exceeds tolerance, flag the invoice with the field, expected value, and actual value
```

Test: if a builder cannot rebuild the step from the text alone, add detail. Never compress distinct steps to hit a count.

**Test components** list one numbered step per test case — `N. **Test case: <title>**` — with the case's steps as lettered substeps and its assertions named in them. The Source Map's step table then has one row per case. A **library** component lists one numbered step per public workflow, grouped by the screen (or stage) it acts on, in the order a user meets the screens. The steps are independent entry points the consumers invoke, not one execution, and a lead-in sentence says so. A **coded app** lists one numbered step per screen, and per mode a screen switches between, with its sections, the fields each shows and leaves out, and the user's actions on it as substeps. The steps are screens a user opens, not one execution, and a lead-in sentence says so. What several screens or modes share is one step of its own, which each of them names. Such a step is how a field saves and how a submit is checked, a view of the data the screens read (with its joins, the row it keeps when several match and its order), or a write, with what it changes and what is read again after it.

**Composite UI interactions carry their full contract.** Source frameworks and descriptions bundle a multi-step interaction into one step: type-ahead pick, menu or tree path, option list, find-row-then-act, keystrokes to the focused element. The substep states, in behavioural words, everything the builder needs to rebuild the interaction:

- what is typed
- how the suggestion or option is matched (equals / contains / nth)
- which key confirms
- each path level
- the row rule

"Enter Voluntary into Primary Reason" is a data loss; "type Voluntary into Primary Reason and pick the suggestion that equals Voluntary" is the step. A source guide's composite-actions table gives the wording per source action; execution builds each contract as a pattern.

**A substep in a window an action opened names that window.** When an action opens a window (a dialog, a popup, a browser tab) and the next substep acts inside it, that substep names the window: "in the Select Vendor dialog, click OK". A source that acts in the new window without first switching to it never names it: deduce the name from the action that opened it and flag it `*[Inferred]*`.

**A loop that only computes, selects or tests is its result.** A loop whose body only computes, filters or tests rows is written as what it produces, not as a loop. Such a body has no read from or action on an application, a file or a queue, and no call to another step.

A source's workaround for its own platform, and an attach before acting, in an extracted genome: [extracted-genome-guide.md § Source Constructs](extracted-genome-guide.md).

### Business Rules
Plain language, no code syntax, specific fields and thresholds kept. A computation is written as its formula, in arithmetic with each operand named by what it holds, with its rounding and boundaries: "the share is paid amount ÷ open amount × 100, rounded half away from zero to a whole number, and 0 when the open amount is 0". Code syntax is the source's statements and calls, never its arithmetic: a formula and a boundary are not code syntax, and neither is a record's field name (§ Provenance). Group under `### Step N: {name}` headings for the step where the rule fires; a rule or handler several steps share goes once under a heading naming them (`### Steps 4, 10 and 15: …`); cross-step rules under `### General`.

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

**A handler that only rethrows is no handling.** A catch that raises the failure it caught again — unchanged, or with only its message reworded — handles nothing, and no Error Handling entry describes it. Where that message is what the run reports (an item's exception reason, a failure notice), the step states the message. Two catches still are entries: one that changes the failure's type, and a rethrow-only catch whose block has a broader catch that does handle — its entry states what the narrower failure is spared ("a business-rule failure is not retried"). A handler that logs, cleans up, retries or chooses between outcomes before it rethrows is an entry, stated by what it does.

### Transactional Shape
Whether the automation iterates over units of work — items that succeed, fail, are retried and are tracked independently of one another. When it does, also per flow: how the work is handled today and how it could be divided at build, asserting no split except one a `Decided:` line records. Full rules: [transactional-shape-guide.md](transactional-shape-guide.md). A genome with no unit of work carries the stub line (§ Stub Lines).

### Acceptance Criteria
A numbered list (`1. …`), so the build report's verdicts and a comparison of two runs cite a criterion by its number. Patterns:
- "Given {specific input}, the automation {specific observable outcome}"
- "When {condition}, the automation {expected behaviour}"
- "{Specific action} produces {specific result}"

Sources, one criterion each minimum: every major workflow step, every data transformation or field mapping, every business rule, every error handler, plus edge cases (empty input, duplicate, malformed data).

**A criterion whose outcome rests on a language model's answer is written in one of three checkable forms.** (1) It states the answer: "Given the model classifies the item as {category}, …" — checked with a supplied or recorded answer, so it tests the build, not the model. (2) It states an invariant that holds whatever the model answers: every record's status agrees with the classification it stores, every handled message has exactly one record. (3) For the quality of the model's own answer, it gives an input whose right answer is computed outside the model — dates written out, a count derived from reference data, a value the input itself carries. It is checked over several runs and says it rests on the model, so a miss is a finding on the model, never on the build.

Banned: "completes successfully", "handles errors properly", and anything code-level ("Uses ReadPDF activity", "Calls Main.xaml", "Assigns true to isValid").

| Banned | Acceptable |
|---|---|
| "Uses ReadPDF to process InvoiceFile" | "Given an invoice PDF, extracts vendor_name, invoice_number, line items (description, qty, unit_price), tax, and total" |
| "SendMail sends to admin@company.com" | "When processing fails after retries, sends a notification to the configured administrator with invoice_number and failure reason" |

### Complexity
`simple | medium | complex`. Never ask the user to declare it. Component genomes: inferred from the description, PDD or SDD ([author-guide.md](../author/author-guide.md) § Step 5 — Infer complexity) or from source signals ([extract-guide.md](../extract/extract-guide.md) § Step 7 — Infer complexity (component)); both default to the lower level when ambiguous and escalate when later evidence demands it. Process genomes are `medium` with at most three **buildable projects**, no human lanes and no `complex` component, otherwise `complex`; the test-case groups of the single test project count as that one project, not one component each. A human lane is a human actor whose action the process **waits on** (an approval, a task, a mailed decision); recipients of notifications are not lanes.

### Tags
Comma-separated: business domain, target applications, platform features (document-understanding, queues, human-in-the-loop, …).

### Source Map (extraction only)
Where every part of an extracted genome came from — its contract rows, the step table and, for a framework source, the migration contract: [extracted-genome-guide.md § Source Map](extracted-genome-guide.md). Authored genomes have no Source Map.

## Population Matrix (component genomes)

| Section | Simple | Medium | Complex |
|---|---|---|---|
| Overview | 1 paragraph | 2-3 paragraphs | 2-3 paragraphs |
| Target Applications, Build With, Platform Dependencies, Interface, Configuration Questions, Open Decisions, Complexity, Tags | Full | Full | Full |
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
| Open Decisions | No open decisions. |
| Business Rules | No business rules beyond the Workflow substeps. |
| Error Handling | No error handling: a failure stops the run. |
| Transactional Shape | Not transactional: {reason — the run is one unit of work; one item's work started per item by {caller}; a library; a test-case group; a coordinator whose per-item lifecycle is the orchestration's; a {Flow, API workflow, agent} that works its items itself}. |

## Write, Then Offer Edits

Every writing verb writes the file(s) to the working directory immediately — no preview, no confirmation — then says where they are and asks "Want to adjust anything?". Edits are targeted and in place, never a regeneration, and made only by the `edit` verb of the skill that writes genomes.

## Provenance

The body of a genome reads as a specification, not a report: no "the project contains", no file paths in Workflow or Business Rules, no activity or variable names anywhere. Provenance lives only in the Source Map section. A message, log text, failure message or text shown to a person (a form's title, instruction or field label) the source writes is behaviour and is written in the body as the source spells it. Each value it inserts is named in braces by what it holds: "logs `Order {order number} posted ({line count} lines)`". A text that embeds an activity name, a path or one of the source project's own file names is described in the body instead ("the corrupt-register message") and quoted in full in its step's Source Map row. A field name of a record, event, request or response the run reads or writes is data, not a variable name, and is written as the source spells it.

## Design Links

Optional blockquote lines after the blueprint blockquote (the process genome's, or a standalone component's) tie a genome to the documents it derives from or was written to. Each is written only when that document exists; none is invented.

- **`> Preferences: [<title>](<relative path>)`** — the preferences file the user named when the genome was written. It answers the questions it covers, and its rules apply wherever they shape the genome: the component layout, the names of projects and resources, the template. `uipath-genome` reads the same file as standing answers. A team starts one from [preferences-template.md](../../assets/templates/preferences-template.md). A preference that conflicts with a rule of this skill is put to the user with both statements, and the genome follows the ruling.

- **`> Designed in: [<SDD title>](<relative path to the SDD>) · sdd-sha256 <SDD_FINGERPRINT>`** — the genome was authored from that agreed SDD. The fingerprint is required on every `Designed in:` line. `<SDD_FINGERPRINT>` is what `node "<SKILL_DIR>/scripts/sdd-fingerprint.mjs" "<SDD_PATH>"` prints once the genome's content is final (`<SKILL_DIR>` is the folder holding this skill's `SKILL.md`); for a solution `<SDD_PATH>` is the root SDD, and the fingerprint covers the root and every child SDD it lists. The SDD's `Genome` row, and an older SDD's `Tasks file` row, do not change it. The build builds the genome as written (a component built from its SDD: § Components Built from the SDD). `uipath-planner` keeps the genome current: an SDD change ends with `edit`'s "The SDD was revised" ([edit-guide.md](../edit/edit-guide.md)) and a new fingerprint ([sdd-writing-guide.md](../design/sdd-writing-guide.md) § Keeping the Genome Current). The strict check fails a `Designed in:` line whose fingerprint no longer matches its SDD (root plus every child for a solution) or whose SDD cannot be read, so a stale genome never passes. The SDD's decisions — the split and queue design, the implementation mode, the package pins, the refactor answers — are recorded in the sections that hold them (a flow's `Decided:` line, Configuration Questions defaults, a process genome's Deployment). The genome restates the SDD's products and projects and never contradicts them; which changes to a designed genome go to `design` first: [edit-guide.md](../edit/edit-guide.md) § Any genome.

The SDD written from the genome is no line of it: `<slug>-sdd.md` beside a component genome with no `Designed in:` line, or `<slug>-solution-sdd.md` with one SDD per project beside a process genome, its handoff's `Genome` row carrying the genome's fingerprint ([sdd-from-genome-guide.md](sdd-from-genome-guide.md)). The genome is the source and the SDD its rendering for people; the strict check fails an SDD whose fingerprint no longer matches the genome, so a stale SDD never passes.
