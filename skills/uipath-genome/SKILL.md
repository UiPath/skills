---
name: uipath-genome
description: "UiPath automation genome — portable markdown blueprint (`*-genome.md`) that documents an automation at process and component level: purpose, workflow steps, business rules, data handoffs, platform resources, acceptance criteria, and the UiPath skill that builds each part. EXTRACT a genome from an existing UiPath project or solution (`.xaml`/`.cs`, `.flow`, `.bpmn`, `agent.json`, `Workflow.json`, `caseplan.json`, `.uipx`) as ground truth for documentation or migration; AUTHOR one from a described idea; EXECUTE one to build the automation. Triggers: 'genome', 'blueprint', 'document this automation/solution/process', 'reverse-engineer what this project does', 'build/implement this genome'. PDD/SDD design & task derivation→uipath-planner. Build without a genome→the artifact's skill (uipath-rpa, uipath-maestro-flow, uipath-agents…). Quality review→uipath-review. Finding what to automate→uipath-automation-discovery."
when_to_use: "User says 'genome', 'blueprint', 'document what this automation does', 'extract a spec from this project/solution', 'reverse-engineer this process', 'describe this solution at high and low level', 'I want a spec before we build', or points at a *-genome.md and asks to build/execute/implement it. NOT for PDD/SDD (→uipath-planner), not for building or fixing an automation without a genome (→the artifact's skill), not for code review (→uipath-review)."
---

# UiPath Genome — document, author, and execute automation blueprints

A genome is a markdown specification of an automation that an AI agent can consume to rebuild it: what it does, the business rules, the data that moves between parts, the platform resources it needs, how to verify it, and which UiPath skill builds each part. Genomes stay thin because the build skills carry the UiPath know-how; a genome describes *what*, the skills know *how*.

> **Read the referenced guide in full before acting.** This file routes; the guides carry the rules. Open the guide for the detected mode and the format guide, and read each whole file — do not grep them or work from memory.

## When to Use This Skill

- User has an existing UiPath project or solution and wants it documented, understood, or prepared for migration ("what does this solution do", "extract a genome", "document this process at high and low level")
- User describes an automation idea and wants a specification before anything is built
- User points at a `*-genome.md` file and wants the automation built from it
- User wants an existing genome updated, split into components, or re-extracted after the source changed

## Mode Detection

Determine the mode from the input, in this order:

1. **A `*-genome.md` path plus build intent** ("build", "execute", "implement", "follow") → **Execute**. Read [execution-guide.md](references/execution-guide.md).
2. **A directory, project file, or solution manifest** (`project.json`, `project.uiproj`, `.uipx`, `.flow`, `.bpmn`, `agent.json`, `Workflow.json`, `caseplan.json`, `uipath.json`) → **Extract**. Read [extraction-guide.md](references/extraction-guide.md) and the matching source guide it names.
3. **A description, idea, SOP, or process narrative** with no source project → **Author**. Read [authoring-guide.md](references/authoring-guide.md).
4. **A `*-genome.md` path plus edit intent** ("update", "add a step", "split", "remove the inferred flags") → **Edit** in place per the edit tables in the authoring guide; re-extract instead when the user says the source changed.

A PDD or SDD, or a request to design a solution and derive tasks, is `uipath-planner`'s job, not a genome. Say so and stop.

Every mode reads [genome-format-guide.md](references/genome-format-guide.md) for content rules and [skill-mapping-guide.md](references/skill-mapping-guide.md) for Build With.

## Critical Rules

1. **Choose the genome level before writing.** One buildable project produces a component genome. Two or more projects, or a coordinator plus the automations it invokes, produce a process genome with one component genome per project. Never flatten a multi-project solution into one file and never split a single project into a process genome. Level rules: [genome-format-guide.md § Two Levels](references/genome-format-guide.md).
2. **Read the source, do not ask about it.** In Extract mode read every non-generated file of every project before writing anything. Never ask the user what the automation does; the artifacts tell you. Ask only when a linked component is missing from disk.
3. **Infer complexity, never ask for it.** Authoring infers it from the description, extraction from source signals, both defaulting to the lower level when ambiguous. Escalate when later evidence demands it.
4. **Replication-grade detail, behavioural wording.** The genome must let a builder recreate the automation without seeing the source: field names, mappings, thresholds, conditions, substeps, and data in/out for every non-trivial step. Activity names, variable names, file paths, and code syntax are banned from the body; they belong only in the Source Map.
5. **Generalize hardcoded values into Configuration Questions.** Every path, URL, address, server, credential, queue, threshold, column name, and application choice becomes a numbered question with the source value as its default.
6. **Every section present, always.** Use the stub lines from the format guide for sections that do not apply. Never omit a section.
7. **One skill per Build With row, from the mapping guide only.** Use only skill names listed in [skill-mapping-guide.md](references/skill-mapping-guide.md). Operate-only skills (queues, assets, connections) go under Platform Dependencies, not Build With.
8. **Preamble and blueprint blockquote are mandatory** in every genome file, and Build With (or Components) precedes Workflow (or Process Map). This is what stops an agent from executing the steps instead of building the automation.
9. **Acceptance criteria are specific and testable.** Each names a concrete input, condition, or output from a workflow step, rule, transformation, or error handler. "Completes successfully" and "handles errors" are banned.
10. **Flag ambiguity, never leave gaps.** Write the best interpretation and append `*[Inferred]*`. Record the uncertainty in the Source Map.
11. **Write immediately, offer edits after.** Write the file(s) to the working directory, then ask "Want to adjust anything?". No previews, no confirmation before writing. Edits are targeted, in place, never a regeneration.
12. **Execution never edits the genome.** During Execute the genome is read-only; configuration questions are asked before any code is written; skill groups advance without pausing; every acceptance criterion is assessed at the end.

## Workflows

### Extract (project or solution → genome)

1. Detect the source framework and the deployment unit with the source guide's Detection section. A `.uipx` or a folder of several projects is a solution → process genome.
2. Inventory every project; skip generated directories per the source guide.
3. Extract signals file by file with the source guide's signal tables: steps, control flow, error handling, data, targets, invocation edges, triggers, platform resources.
4. Build the call graph per project and the handoff graph across projects.
5. Infer complexity from the signal counts in the extraction guide.
6. Map signals to genome sections per the extraction guide; write the process genome first, then each component genome with `Part of:`, Interface, and Source Map.
7. Write, then offer edits. Common follow-ups: "remove the inferred flags", "drop the Source Map for sharing", "this step is wrong".

Full procedure: [extraction-guide.md](references/extraction-guide.md). UiPath signals: [sources/uipath-source-guide.md](references/sources/uipath-source-guide.md). Adding another framework: [sources/source-framework-contract.md](references/sources/source-framework-contract.md).

### Author (description → genome)

Receive → choose level → infer complexity → extract → suggest platform capabilities → bounded follow-ups (simple 0-1, medium 1-2, complex 2-3 rounds, all questions of a round in one message) → generate → write → offer edits. Full procedure: [authoring-guide.md](references/authoring-guide.md).

### Execute (genome → automation)

Parse and validate the genome → ask every configuration question (`AskUserQuestion`, ≤4 per batch; autonomous runs take defaults) → resolve one project (component) or one solution with one project per component (process) → plan skill groups → build each group by invoking the owning skill with the assembled context → wire handoffs → assess every acceptance criterion → report. Full procedure: [execution-guide.md](references/execution-guide.md).

## Reference Navigation

| File | Read when |
|---|---|
| [references/genome-format-guide.md](references/genome-format-guide.md) | Every mode — section rules, population matrix, stubs, wording, file layout |
| [references/skill-mapping-guide.md](references/skill-mapping-guide.md) | Filling Build With / Components or planning execution groups |
| [references/extraction-guide.md](references/extraction-guide.md) | Extract mode — pipeline, signal→section mapping, complexity from signals |
| [references/sources/uipath-source-guide.md](references/sources/uipath-source-guide.md) | Extract mode on a UiPath source — per-artifact signal tables |
| [references/sources/source-framework-contract.md](references/sources/source-framework-contract.md) | Adding extraction support for another automation framework |
| [references/authoring-guide.md](references/authoring-guide.md) | Author and Edit modes |
| [references/execution-guide.md](references/execution-guide.md) | Execute mode |
| [assets/templates/component-genome-template.md](assets/templates/component-genome-template.md) | Writing a component genome |
| [assets/templates/process-genome-template.md](assets/templates/process-genome-template.md) | Writing a process genome |
| [assets/examples/](assets/examples/) | Calibrating depth — one component (RPA, medium), one hybrid coded+XAML component, one process genome with components |

## Anti-patterns

1. **Asking the user what the project does, or which complexity it is.** Read and infer.
2. **Previewing before writing.** Write, then offer edits.
3. **Code in the body.** "Uses ReadPDF", "Calls Main.xaml", `Amount > 10000 AndAlso …`, file paths in Workflow. Translate to behaviour; provenance goes to the Source Map.
4. **Treating Integration Service as an application.** Resolve to Salesforce, ServiceNow, SAP.
5. **Compressing steps to hit a count, or flat one-liners for multi-field operations.** Minimums are floors; substeps carry the detail a builder needs.
6. **Disconnected rules and handlers.** Attach every business rule and error handler to its step.
7. **Retired skill names in Build With** (`uipath-rpa-workflows`, `uipath-coded-workflows`, `uipath-coded-agents`). Use the mapping guide's names; a stale name will not resolve at execution.
8. **Process genome without Handoffs, or component Interface that disagrees with Handoffs.** The handoff table is the contract that makes the components composable.
9. **Stopping between execution groups, or building before configuration answers exist.**
10. **Producing a genome when the user brought a PDD/SDD or asked for a solution design.** That is `uipath-planner`.
