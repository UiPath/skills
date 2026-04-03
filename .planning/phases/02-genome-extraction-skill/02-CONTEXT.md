# Phase 2: Genome Extraction Skill - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Agent reads an existing UiPath Studio project directory and produces a genome markdown spec that captures what the solution does. The output genome follows TEMPLATE.md format and is indistinguishable from one created by the authoring skill. The skill generalizes business-specific details into configuration questions so the genome is reusable beyond the original project.

</domain>

<decisions>
## Implementation Decisions

### Interaction model
- Fully autonomous: agent reads the project, produces a complete genome, then offers edits — mirrors authoring skill's "write immediately, offer edits after" pattern
- When the agent encounters ambiguity (unclear business logic, multiple entry points), it flags low-confidence sections in the genome with a visible marker (e.g., "Inferred") rather than asking the user upfront
- Agent infers project complexity (simple/medium/complex) from project signals (file count, dependency count, entry points, orchestration patterns) and adjusts section depth per the same population matrix as the authoring skill
- File name derived from project.json `name` field, slugified (e.g., "InvoiceProcessing" -> `invoice-processing-genome.md`)

### Extraction depth
- Structural + obvious logic: extract what's structurally visible (workflow steps, target apps, error handling patterns, conditional branches) and infer business rules from if/switch conditions and validation logic, but don't speculate on business intent beyond what the code expresses
- Generalize hardcoded values AND application choices into Configuration Questions — email addresses, folder paths, URLs, threshold values, column names, credential names, queue names, AND the specific applications used (e.g., "Outlook" becomes "Which email provider?" in config questions)
- Original hardcoded values appear as defaults in Configuration Questions (e.g., "Which email provider? (source project used: Outlook)")
- Detect platform features from dependencies and activity usage — map to Target Applications (Document Understanding, Integration Service) and note Orchestrator dependencies in Configuration Questions (satisfies EXTR-04)
- Acceptance criteria describe what a fresh build from this genome should achieve — functional outcomes, not code-level assertions ("Given an invoice PDF, extracts vendor and amount" not "Uses ReadPDF activity")

### Project scope
- User specifies a directory; agent scans for project.json, and if not found, looks for .xaml/.cs files directly
- Read all relevant files: project.json, all .xaml, all .cs (excluding .local/, .objects/, auto-generated files in .codedworkflows/), .cs.json metadata, .flow files
- Read everything even in large projects — no file count limit or summarization of helper workflows
- Handle mixed XAML + coded workflow projects as a unified genome — Build With maps each step to the appropriate skill (uipath-rpa-workflows for XAML steps, uipath-coded-workflows for coded steps)

### Output fidelity
- Error handling extraction uses pattern detection: identify TryCatch blocks, retry loops, GlobalHandler, exception types caught; map to genome Error Handling section as behavioral descriptions ("retries 3x on timeout"), not code-level detail
- Overview section contains generalized purpose and context — the genome reads like it was authored, not extracted
- Output genome is indistinguishable from one created by the authoring skill — no extraction markers or provenance notes

### Claude's Discretion
- Specific complexity inference heuristics and thresholds for extracted projects
- How to order workflow steps when the call graph has parallel branches
- Exact format of the ambiguity flag markers
- How to handle projects with no clear entry point (no `main` in project.json)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Genome format
- `skills/shared/genome/genome-template.md` — Canonical genome template with all sections (Build With before Workflow)
- `.genome_spec/TEMPLATE.md` — Original genome template spec
- `.genome_spec/DISCUSSION.md` — Genome design philosophy and key decisions

### Genome examples
- `.genome_spec/examples/invoice-processing.md` — Medium-complexity genome example
- `.genome_spec/examples/email-triage.md` — Genome example with email/classification
- `.genome_spec/examples/simple-data-transfer.md` — Simple genome example

### Authoring skill (pattern to follow)
- `skills/uipath-genome-authoring/SKILL.md` — Authoring skill patterns: complexity inference, population matrix, critical rules, anti-patterns, "write immediately, offer edits after" pattern
- `skills/uipath-genome-authoring/references/skill-mapping-guide.md` — Skill mapping table and decision tree for Build With section

### UiPath project structure (extraction sources)
- `skills/uipath-rpa-workflows/references/project-structure.md` — Project directory layout, project.json schema, common activity packages
- `skills/uipath-rpa-workflows/references/xaml-basics-and-rules.md` — XAML file anatomy, workflow types, activity structure
- `skills/uipath-coded-workflows/references/codedworkflow-reference.md` — Coded workflow patterns, service properties, Integration Service connections

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `skills/shared/genome/genome-template.md` — Same template used by authoring skill; extraction skill reads it to populate genome output
- `skills/uipath-genome-authoring/references/skill-mapping-guide.md` — Reuse for Build With section mapping; extraction skill references the same guide
- Phase 1 authoring skill SKILL.md — Patterns for complexity inference, section population matrix, and critical rules can be adapted for extraction

### Established Patterns
- Authoring skill uses "write immediately, offer edits after" — extraction follows the same pattern
- Authoring skill infers complexity from user description — extraction infers from project signals instead
- Every genome section present (stubs for inapplicable) — same rule applies to extraction output
- Blueprint preamble required on all genomes — extraction must include it
- Build With section before Workflow — same ordering

### Integration Points
- Extraction skill folder: `skills/uipath-genome-extraction/`
- Shared genome template at `skills/shared/genome/genome-template.md`
- Skill mapping guide referenced from authoring skill's references directory
- CODEOWNERS needs an entry for the new skill

</code_context>

<specifics>
## Specific Ideas

- Extracted genomes should be reusable: business-specific values become Configuration Questions with original values as defaults, application choices become configurable rather than hardcoded
- The genome should read as if it were authored from scratch — a genome is a genome regardless of how it was created
- Ambiguity in source code gets flagged visibly in the genome so the user can review, but the agent always writes its best interpretation rather than leaving gaps

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-genome-extraction-skill*
*Context gathered: 2026-04-02*
