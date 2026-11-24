<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     To build it, invoke the uipath-genome skill: it asks the configuration questions,
     then invokes the skills referenced in Build With. Do NOT execute these steps directly, and do NOT
     start from a Build With skill. To change it, invoke the uipath-planner skill. -->

# Genome: {Name}

> {One-line description of what this automation does}

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Build it with the **uipath-genome** skill, which hands each part to the skill listed in **Build With** below.

> Part of: {Process name} — {one line on this component's role in the process}. *(Write the process name as a markdown link to `../{process-slug}-genome.md`. Omit this line for a standalone automation.)*

> Designed in: [{SDD title}]({relative path to the SDD}) · sdd-sha256 {SDD_FINGERPRINT} *(Only when the genome is authored from an agreed SDD; omit otherwise.)*

> Preferences: [{title}]({relative path to the preferences file}) *(Only when the user named one; omit otherwise. A component of a process genome omits it: the process genome's line holds.)*

## Overview

{1-3 paragraphs: purpose, business problem, who it is for, what triggers it.}

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| {e.g. SAP GUI} | {Input source / Output target / Both} | {version, module, access method; for an application driven through its UI, `UI targets: <environment>`} |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| {Workflow step reference} | `{uipath-skill-name}` | {Why this skill fits this step} |

## Platform Dependencies

{One table per kind of resource the automation uses, in this order; leave out a kind it does not use. Used by names the steps. A value the source or description does not show is classed as the genome questions guide's § Open Decisions classes a point.}

### Queues

| Queue | One item is | Item fields | Unique reference | Retries | Added by | Worked by |
|-------|-------------|-------------|------------------|---------|----------|-----------|
| {e.g. InvoiceQueue} | {one invoice} | {InvoiceNumber: Text, Amount: Number} | {InvoiceNumber, on} | {2} | {step 3} | {steps 4–7} |

### Assets

| Asset | Type | Value | Used by | Purpose |
|-------|------|-------|---------|---------|
| {e.g. ErpBaseUrl} | {Text / Integer / Bool / Secret} | {fixed value, or Configuration Question N; never a secret} | {steps} | {what it is for} |

### Credentials

| Asset | Account or persona | Signs in to | Used by |
|-------|--------------------|-------------|---------|
| {e.g. ErpApprover} | {the approver account} | {SAP, production} | {steps} |

### Storage buckets

| Bucket | Holds | Written by | Read by |
|--------|-------|------------|---------|

### Connections

| Connection | Connector | Signs in as | Used by |
|------------|-----------|-------------|---------|

### Data Fabric entities

| Entity | Fields | Written by | Read by |
|--------|--------|------------|---------|

### Triggers

| Trigger | Starts | Kind | When | Runners |
|---------|--------|------|------|---------|
| {e.g. DailyIntake} | {this process} | {Time / Queue / Event / API} | {weekdays 07:00, Europe/Berlin; or the queue; or the event; or the API endpoint} | {1} |

### {Other service: Action Center, Document Understanding, Test Manager, Context Grounding}

| Resource | Used by | Purpose |
|----------|---------|---------|

*Stub when none: "No Orchestrator or Integration Service resources required."*

## Interface

- **Inputs:** {arguments, files, queue items, or events the automation consumes — name, type, source}
- **Outputs:** {values, files, records, or events it produces — name, type, consumer}
- **Side effects:** {external state it changes — records created, emails sent, files moved}

{Library component: replace the bullets with one table per public workflow — `Argument | Direction | Type | Description` — and the conventions consumers rely on. Test component: list the per-scenario row schema (≤ ~20 fields) and, separately, the constants held in the project's configuration; credentials as asset names only.}

## Configuration Questions

{Questions to answer before building. Extracted genomes ask only the values the source leaves open, with the source value as the default. A value bound to the environment (host, mailbox, recipient, path or share, queue, asset or credential name) is always open. Every value the source fixes stays in the section where it acts (genome questions guide § Configuration Questions). Authored genome whose Transactional Shape is not the stub: one constant asks the item retry count and the consecutive-failure stop (transactional shape guide rule 4). Each question names its kind — setting or constant (genome questions guide § Configuration Questions).}

1. {Question}? ({setting | constant}; default: {value})
2. {Question}? ({setting | constant}; default: {value})

*Stub when none: "No open values — no configuration needed."*

## Open Decisions

{Every point left to a person, numbered once and never renumbered: an entry stays when decided or withdrawn (genome questions guide § Open Decisions). Each marked line names its entry: `*[Inferred: D1]*`.}

1. {The decision as a question}? ({business outcome}; answered by: {the process owner}; builds now: {what the genome builds}; instead: {the other option}) — step {N}, {step name}
2. {The point as a question}? ({run behaviour}; answered by: {the process owner}; recommended: {the evident intent, in words}; builds now: {the source's behaviour}) — step {N}, {step name}
3. {The reading as a question}? ({reading}; answered by: {whoever knows the process}; reading: {what the genome takes it to be, and why it is inferred}) — step {N}, {step name}
4. {What to supply}? ({material}; answered by: {whoever holds the source}; until answered: {a placeholder, a stop}) — step {N}, {step name}
5. {A decided question}? (decided {YYYY-MM-DD}: {the answer})

*Stub when the genome has never had one: "No open decisions."*

## Workflow

1. **Trigger**: {What starts the automation}
2. **{Step name}** (input: {data in}; output: {data out}):
   a. {Substep with specific field/data detail}
   b. {Conditional: if {condition}, then {action}; otherwise {action}}
3. **Output**: {What the automation produces}

## Business Rules

### Step {N}: {Step name}
- {Rule in plain language with specific fields, thresholds, and conditions}

### General
- {Rule that applies across steps}

*Stub when none: "No business rules beyond the Workflow substeps."*

## Error Handling

### Step {N}: {Step name}
- {Failure}: {recovery — retry count, fallback, notification, skip}

### Global
- Unhandled exception: {behaviour}

*Stub when none: "No error handling: a failure stops the run."*

## Transactional Shape

{Describe, never decide: layout and rules per the transactional shape guide (§ Layout, § Rules). A component of a process keeps, per flow it takes part in, only the `Role:` line, the As-is rows of its role and `Split options: per the process genome, Flow N.`}

**Flows:** Flow 1 — {unit}: steps {a–b} → steps {c–d}. *(standalone project only)*

### Flow 1 — {unit of work}: {producer} → {consumer}

**Role:** {producer | consumer | producer and consumer | consumer of Flow {M} and producer of this flow} — {one sentence}. *(component of a process only)*

**Unit of work:** one {item}; reference {identifying field(s)}; {volume and cadence}; chosen because {reason}.
**Alternative units of work:** one {other item} — fits when {condition}.

**As-is:**

| Aspect | As-is |
|---|---|
| Produced by | {steps that read the source and create the items; how often; one source or several; how a second population is prevented — lock, ledger, "once per date" — or not} |
| Consumed by | {steps that work the items; one robot or several; how a robot picks its items — any, by parent, by kind — and in which order} |
| Item store | {where items live today: framework work queue, Orchestrator queue, database table, in-memory list, folder}; per-item state kept as {which of: status text, tags, data fields, output} |
| Coordination | {what keeps runs and item levels from colliding — parent items, ledgers, locks, tag joins — and what each is for; "none" when absent} |
| Item kinds | {one kind, or the kinds the consumer routes between and what differs per kind: payload, work, outcomes} |
| Step groups | once per run: steps {n}; per item: steps {p–q}; at the end: steps {r} |

| Outcome | When | Effect |
|---|---|---|
| Success | every per-item step completed | item recorded as done with {result} |
| Business exception | Step {N} rules: {names} | {business effect} |
| System exception | Step {N} handlers: {names} | retried {n}×; the run stops after {m} consecutive |

**Split options:**

| Unit of work | Option | Requires | Changes against as-is |
|---|---|---|---|
| {unit} | A | {what this flow needs to produce and work its items in one job — or "excluded: <the fact that rules it out>"} | {what changes against as-is: projects and schedules, retry granularity, where per-item state is visible} |
| {unit} | B | {what this flow needs for a producer process and a consumer process with one queue between them — or "excluded: <fact>"} | {what changes against as-is: projects and schedules, retry granularity, where per-item state is visible} |
| {unit} | C | {what this flow needs for one process that fills and works its own queue, and the once-guard its population uses — or "excluded: <fact>"} | {what changes against as-is: projects and schedules, retry granularity, where per-item state is visible} |
| {alternative unit} | A | {what this flow needs to produce and work its items in one job — or "excluded: <the fact that rules it out>"} | {what changes against as-is: projects and schedules, retry granularity, where per-item state is visible} |
| {alternative unit} | B | {what this flow needs for a producer process and a consumer process with one queue between them — or "excluded: <fact>"} | {what changes against as-is: projects and schedules, retry granularity, where per-item state is visible} |
| {alternative unit} | C | {what this flow needs for one process that fills and works its own queue, and the once-guard its population uses — or "excluded: <fact>"} | {what changes against as-is: projects and schedules, retry granularity, where per-item state is visible} |

**Evidence:** {facts that bear on the split, never a verdict: robot count, schedules, sources, applications per item kind, whether items survive a run today}
**Decided:** {option, unit — source} *(only when already decided)*
**Configuration:** settings — questions {a, b}; constants — questions {c, d}; assets — every asset row of Platform Dependencies.
**Traceability:** {what is recorded per item today and where — reference, outcome and reason; screenshot on system exception; run summary}

*Stub when none: "Not transactional: {reason}."*

## Acceptance Criteria

1. Given {specific input}, the automation {specific observable outcome}
2. When {condition}, the automation {expected behaviour}
3. {Specific action} produces {specific result}

## Complexity

{simple | medium | complex}

## Tags

{comma-separated: domain, applications, platform features}

## Source Map

*Extraction only — omit for authored genomes. Delete on request when the genome is shared as a reusable blueprint.*

| Row | Source artifact | Notes |
|-----|-----------------|-------|
| {Dead code / Unresolved invocation / Inferred / a finding} | {Source framework}: `{Name}` ({id}) | {what it is, the lines that show it} |
| Requested change | {for a refactor or migration request: the user's words; otherwise —} | {each refactor-question decision — `Target: <component> → <product>`, `Retire: <entry point>`, `Fold: <reader> into <writer>`; a split decision is that flow's `Decided:` line alone} |
| Related resources | {path or link} — {kind} | {what it settled, or "not read" and why} |
| Resource discrepancies | {resource}: {what it says} | {what the source does} |

*A component of a process genome inherits the Source framework, Source export, Requested change, Inventory, Not covered, Unused and Related resources rows from the process genome; a standalone component genome carries them itself.*

### Steps

| Step | Source objects | Data sets | Captures | Notes |
|------|----------------|-----------|----------|-------|
| {N} | `{Name}` ({id}[, {locator}]); … — the primary object first; a UiPath source: `{Folder/Workflow.xaml}` | `{Name}` ({id}); … or none | {n} | {callers, callees that are steps of their own, lines, quirks} |

*One row per Workflow step, keyed by its number (extracted genome guide § Source Map, the step table).*
