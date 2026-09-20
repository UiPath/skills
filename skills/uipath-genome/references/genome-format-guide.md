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
3. **Detail lives at the lowest level that owns it.** Component-specific workflow steps, business rules, error handling, and acceptance criteria go in the component genome. The process genome holds only what spans components: process map, handoffs, shared platform dependencies, cross-cutting rules, end-to-end criteria, deployment.
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

**Process genomes with test components:** the Type column of every test component reads "Test-case group in project `<ProcessName>.Tests`", and a **Project layout** block follows the Components table: one sentence stating the solution has N buildable projects (non-test components plus one test project), then a table `Folder | Component | Test cases | Data file(s)` with one row per test component and one row for the shared `Config/` folder (constants from the Configuration Questions, credential-asset name → environment URL map). The component genomes' Build With rationale names their folder in that project. The component diagram nests the test components inside a subgraph for the test project.

### Platform Dependencies
Every Orchestrator or Integration Service resource touched: queues, assets, credentials, storage buckets, connections, folders, triggers. Each row names resource type and purpose. Extracted genomes keep the source resource name; authored genomes propose one.

**Credentials: one credential asset per login account**, named after the account or persona, with its environment or tenant. Scenarios often sign in as several accounts with different roles on different tenants; never collapse them onto one login. The asset holds the secret; the genome and the data rows name the asset — a password, token or secret value never appears in a genome, a data file or a report, and dropping the account identity along with the secret loses which role each scenario ran as. Execution-side naming and declaration: [source-migration-guide.md](source-migration-guide.md) rule 4.

### Interface (component)
Inputs, outputs, side effects. Mandatory content for a component inside a process genome (it is the contract the Handoffs table relies on). Standalone components may stub it: "Runs unattended with no arguments; outputs are the side effects listed in Workflow."

**Library components** (a project other components consume as a package) carry, instead of the three bullets, one table per public workflow: `Argument | Direction | Type | Description`, plus the conventions consumers rely on (naming, defaults, what a failed final check does). This table is the contract consumers are authored against before the library packs.

**Test components** (a group of test cases over data rows, one folder of the single test project) list the row schema per test case: the fields that vary per scenario (at most about 20 — an analyzer rule caps workflow arguments), separately from the constants in the project's shared configuration workflow. Credentials appear as the name of a credential asset per row, never as values.

### Configuration Questions
Format: `N. {Question}? (default: {value})`. Every hardcoded value in the source or description becomes a question: paths, URLs, addresses, server names, credential and queue names, thresholds, column names, and the application choice itself ("Which email provider? (default: Outlook)"). Scaffolding choices (project location, target framework, expression language, installed package versions) belong to the executing environment, not the automation: execution asks them itself ([execution-guide.md § 1.3](execution-guide.md)); do not write them into the genome.

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
One row per edge between components: mechanism (queue item, start job, Flow invoke, event, file drop, Action Center task), data schema passed, and what happens when the receiving side fails. This table is the data contract; component Interface sections must agree with it.

### Deployment (process)
Packaging (one solution vs independent packages), entry points and triggers, target folders or environments. Name the buildable projects explicitly; when test components exist, Deployment names exactly one test project and one Test Manager test set per folder of it.

### Complexity
`simple | medium | complex`. Never ask the user to declare it. Component genomes: inferred from the description ([authoring-guide.md](authoring-guide.md) Step 3) or from source signals ([extraction-guide.md](extraction-guide.md) Step 5); both default to the lower level when ambiguous and escalate when later evidence demands it. Process genomes are `medium` with 2-3 components and no human lanes, otherwise `complex`.

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

## Ambiguity Marker

When intent is unclear from the source, write the best interpretation, append `*[Inferred]*` to that line, and record the uncertainty in the Source Map. Never leave a section empty because the source is ambiguous. Users remove markers once they confirm the content ("Remove the inferred flags").

## Write, Then Offer Edits

Every mode writes the file(s) to the working directory immediately — no preview, no confirmation — then says where they are and asks "Want to adjust anything?". Edits are targeted and in place, never a regeneration; edit tables: [authoring-guide.md](authoring-guide.md) Step 8 and [extraction-guide.md](extraction-guide.md) Step 7.

## Provenance

The body of a genome reads as a specification, not a report: no "the project contains", no file paths in Workflow or Business Rules, no activity or variable names anywhere. Provenance lives only in the Source Map section.
