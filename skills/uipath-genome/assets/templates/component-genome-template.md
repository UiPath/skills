<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     Do NOT execute these steps directly. Use the UiPath skills referenced in Build With to create
     the automation project. -->

# Genome: {Name}

> {One-line description of what this automation does}

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Use the skills listed in **Build With** below to create a UiPath automation project that implements this workflow.

> Part of: {Process name} — {one line on this component's role in the process}. *(Write the process name as a markdown link to `../{process-slug}-genome.md`. Omit this line for a standalone automation.)*

## Overview

{1-3 paragraphs: purpose, business problem, who it is for, what triggers it.}

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| {e.g. SAP GUI} | {Input source / Output target / Both} | {version, module, access method} |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| {Workflow step reference} | `{uipath-skill-name}` | {Why this skill fits this step} |

## Platform Dependencies

| Resource | Type | Purpose |
|----------|------|---------|
| {e.g. InvoiceQueue} | {Queue / Asset / Credential / Storage bucket / Connection / Folder} | {what the automation does with it} |

*Stub when none: "No Orchestrator or Integration Service resources required."*

## Interface

- **Inputs:** {arguments, files, queue items, or events the automation consumes — name, type, source}
- **Outputs:** {values, files, records, or events it produces — name, type, consumer}
- **Side effects:** {external state it changes — records created, emails sent, files moved}

{Library component: replace the bullets with one table per public workflow — `Argument | Direction | Type | Description` — and the conventions consumers rely on. Test component: list the per-scenario row schema (≤ ~20 fields) and, separately, the constants held in a configuration workflow; credentials as asset names only.}

## Configuration Questions

{Questions to answer before building. Extracted genomes carry the source value as the default.}

1. {Question}? (default: {value})
2. {Question}? (default: {value})

*Stub when none: "Description covers the scope — no additional configuration needed."*

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

*Stub when none: "No explicit business rules — agent applies standard validation patterns."*

## Error Handling

### Step {N}: {Step name}
- {Failure}: {recovery — retry count, fallback, notification, skip}

### Global
- Unhandled exception: {behaviour}

*Stub when none: "Standard error handling — retry on transient failures, log and skip on permanent errors."*

## Transactional Shape

{Does the project iterate over units of work — items that succeed, fail, are retried and are tracked independently? Describe; never decide. Standalone project: the `Flows:` line and the whole block below per flow. Component of a process: one block per flow it takes part in, each with only the `Role:` line, the As-is rows that concern this project (a producer: source, reference rule, fate of the queued source item; a consumer: step groups, outcomes, counts, configuration split, traceability) and the line `Split options: per the process genome, Flow N.`}

**Flows:** Flow 1 — {unit}: steps {a–b} → steps {c–d}. *(standalone project only)*

### Flow 1 — {unit of work}: {producer} → {consumer}

**Role:** {producer | consumer | consumer of Flow {M} and producer of this flow} — {one sentence}. *(component of a process only)*

**Unit of work:** one {item}; reference {identifying field(s)}; fields as in {Interface / Handoffs row}; {volume and cadence}; chosen because {items fail, retry and are reported independently at this level; the reference exists; the retry cost is acceptable}.
**Alternative units of work:** one {other item} — fits when {condition}. *(every viable granularity, or "none")*

**As-is** — how the project handles the units today:

| Aspect | As-is |
|---|---|
| Produced by | {steps that create items; how often; one source or several; guarded by a lock or ledger?} |
| Consumed by | {steps that take items; one robot or several; how items are picked; order} |
| Item store | {queue / table / in-memory list / folder}; per-item state as {status, tags, fields, output} |
| Coordination | {parent items, ledgers, locks, tag joins — what each is for; "none"} |
| Item kinds | {one kind, or several routed inside the consumer — what differs} |
| Step groups | once per run: steps {n}; per item: steps {p–q}; at the end: steps {r} |

| Outcome | When | Effect |
|---|---|---|
| Success | every per-item step completed | item recorded as done with {result} |
| Business exception | Step {N} rules: {names} | no retry; item recorded with the reason; run continues |
| System exception | every other failure — Step {N} handlers: {names} | applications reopened, item retried {n}×, then recorded as failed with the reason; run stops after {m} consecutive |

**Split options** — for the unit of work and each alternative unit; runner counts are deployment settings, never options; none asserted:

| Unit of work | Option | Processes | Item store | Requires | Changes against as-is |
|---|---|---|---|---|---|
| {unit} | A — one process, both roles | one RPA process (REFramework direct mode or a plain per-item loop) | in-process list (one job, one runner); no queue | {nothing else touches the items; one runner; a rerun is safe} | {…} |
| {unit} | B — a producer process and a consumer process | two RPA processes (two projects, or two entry points each published as a process), each with its own trigger and runner count | one Orchestrator queue per unit of work | {several consumer runners, retries across runs, different cadences, machines, credentials or ownership} | {…} |
| {unit} | C — one process, both roles, with a queue | one RPA process, one entry point and one trigger: every job produces behind a once-guard, then consumes the queue (REFramework queue mode, producer steps in its initialisation); any number of identical runners | one Orchestrator queue per unit of work | {several runners, retries across runs or a later reader of the items, while both roles share cadence, machines, credentials and owner; population once per period (unique reference or kept ledger)} | {…} |
| {alternative unit} | A — one process, both roles | … | … | … | {…} |
| {alternative unit} | B — a producer process and a consumer process | … | … | … | {…} |
| {alternative unit} | C — one process, both roles, with a queue | … | … | … | {…} |

**Evidence:** {facts only — robots, schedules, sources, applications per item kind, whether items survive a run today}.
**Configuration:** settings — questions {a, b}; constants — questions {c, d}; assets — every Credential and Text row of Platform Dependencies.
**Traceability:** {per-item record and where it lands; screenshot on system exception; run summary}.

*Stub when none: "Not transactional: {reason — the run is one unit of work; one item's work started per item by {caller}; a library; a test-case group; a coordinator whose per-item lifecycle is the orchestration's}."*

## Acceptance Criteria

- [ ] Given {specific input}, the automation {specific observable outcome}
- [ ] When {condition}, the automation {expected behaviour}
- [ ] {Specific action} produces {specific result}

## Complexity

{simple | medium | complex}

## Tags

{comma-separated: domain, applications, platform features}

## Source Map

*Extraction only — omit for authored genomes. Delete on request when the genome is shared as a reusable blueprint.*

| Workflow step | Source artifact | Notes |
|---------------|-----------------|-------|
| {Step N} | {Source framework}: `{file or object name}` ({id} where names repeat); {data sets that drive it} | {ambiguity, dead code, or unresolved reference} |
| Related resources | {path or link} — {kind} | {what it settled, or "not read" and why} |
| Resource discrepancies | {resource}: {what it says} | {what the source does} |

*A component of a process genome inherits the Source framework, Source export, Inventory and Related resources rows from the process genome; a standalone component genome carries them itself.*
