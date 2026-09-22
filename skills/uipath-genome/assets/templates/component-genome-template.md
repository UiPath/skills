<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     Do NOT execute these steps directly. Use the UiPath skills referenced in Build With to create
     the automation project. -->

# Genome: {Name}

> {One-line description of what this automation does}

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Use the skills listed in **Build With** below to create a UiPath automation project that implements this workflow.

> Part of: {Process name} — {one line on this component's role in the process}. *(Write the process name as a markdown link to `../{process-slug}-genome.md`. Omit this line for a standalone automation.)*

## Overview

{1-3 paragraphs: purpose, business problem, who it is for, what triggers it. Standalone project whose Transactional Shape applies the shape: the first paragraph names its role — dispatcher, performer, dispatcher + performer.}

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

{Does the project iterate over units of work — items that succeed, fail, are retried and are tracked independently? Standalone project: the whole shape below, and the role word in the Overview when the Recommendation applies it. Component of a process: this project's role only (producer: source, reference rule, fate of the queued source item; consumer: step groups, outcomes, counts, configuration split, traceability) and the Recommendation `per the process genome — applied.` or `per the process genome — not applied.`; the process genome carries the tables across components.}

**Unit of work:** one {item}; reference {identifying field(s)}; fields as in {Interface / Handoffs row}; {volume and cadence}; chosen because {items fail, retry and are reported independently at this level; the reference exists; the retry cost is acceptable}.

| Producer | Reads | Writes items to | Reference rule | Trigger |
|---|---|---|---|---|
| {entry point} | {source} | {queue name / the consumer's own list} | {uniqueness; duplicates} | {schedule or event} |

| Consumer | Takes items from | Mode | Once per run | Per item | At the end |
|---|---|---|---|---|---|
| {entry point} | {queue name / the source} | {queue \| direct} — {reason} | steps {n} | steps {p–q} | steps {r} |

| Outcome | When | Effect |
|---|---|---|
| Success | every per-item step completed | item recorded as done with {result} |
| Business exception | Step {N} rules: {names} | no retry; item recorded with the reason; run continues |
| System exception | every other failure — Step {N} handlers: {names} | applications reopened, item retried {n}×, then recorded as failed with the reason; run stops after {m} consecutive |

**Configuration:** settings — questions {a, b}; constants — questions {c, d}; assets — every Credential and Text row of Platform Dependencies.
**Traceability:** {per-item record and where it lands; screenshot on system exception; run summary}.
**Recommendation:** {Apply — {reason}. | Not recommended — {reason}.}
**Alternative unit of work:** one {other item} — not chosen because {reason}; choose it when {condition}. *(only when a second granularity is viable)*

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

*A component of a process genome inherits the Source framework, Source export and Inventory rows from the process genome; a standalone component genome carries them itself.*
