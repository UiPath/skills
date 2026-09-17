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
| {Step N} | {Source framework}: {file or object name} | {ambiguity, dead code, or unresolved reference} |
