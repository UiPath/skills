# Phase 1: Genome Authoring Skill - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Create the `uipath-genome-authoring` skill that interviews a user about their automation idea and produces a self-contained genome markdown file. The skill follows repo conventions (SKILL.md with frontmatter, references/, kebab-case naming). The genome output follows the established template format with an added Build section referencing which skill(s) to use.

</domain>

<decisions>
## Implementation Decisions

### Interview flow
- User provides a free-form description of their automation idea first
- Agent infers complexity (simple/medium/complex) from the description — user does not declare it
- Agent extracts what it can from the description, then asks targeted follow-up questions only for gaps (GSD discuss-phase style)
- Agent proactively suggests UiPath-specific features the user might not know about (e.g., PDFs → Document Understanding, web forms → UI Automation, connectors → Integration Service)

### Template sections per complexity
- **Simple**: Overview, Target Applications, Workflow, Acceptance Criteria, Tags, Complexity — mandatory. Other sections get a stub with guidance (e.g., "No explicit rules — agent uses standard validation patterns")
- **Medium/Complex**: All sections populated, depth proportional to complexity
- Sections that don't apply are never omitted entirely — always stub with guidance so the template stays complete
- Acceptance criteria must be specific and testable, derived from workflow steps (e.g., "Correctly extracts invoice number from sample PDF") — not generic "step completes successfully"

### Build section (new template addition)
- Add an explicit **Build With** section to the genome template
- Single recommended skill per workflow step, with rationale
- Each step in the Workflow section can reference its own skill (e.g., Step 1: `uipath-rpa-workflows` for DU extraction, Step 2: `uipath-coded-workflows` for API calls)
- Orchestration (Maestro flows, queues) is treated as its own step with its own skill reference — not a top-level annotation
- Agent infers the right skill based on workflow type, target apps, and complexity

### Output handling
- Genome file written to the user's current working directory
- Naming convention: `{slug}-genome.md` (e.g., `invoice-processing-genome.md`)
- Agent writes the file immediately, then offers edits ("Want to adjust anything?") — no preview step

### Skill references (internal structure)
- Embed the genome template inside `skills/uipath-genome-authoring/references/` — fully self-contained
- No example genomes needed as references — the template + interview instructions are sufficient
- Use /skill-creator skill when building to ensure quality and repo conventions

### Claude's Discretion
- Exact follow-up question phrasing and ordering
- How to structure the interview for edge cases (very short descriptions, contradictory requirements)
- Whether to group follow-up questions or ask one at a time

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Genome specification
- `.genome_spec/TEMPLATE.md` — Canonical genome format with all sections. The skill embeds this but the spec is the source of truth.
- `.genome_spec/DISCUSSION.md` — Key design decisions: complexity spectrum, agent carries the weight, verification matters.
- `.genome_spec/examples/email-triage.md` — Simple genome example for reference.
- `.genome_spec/examples/invoice-processing.md` — Medium genome example for reference.
- `.genome_spec/examples/simple-data-transfer.md` — Simple genome example (hello world of RPA).

### Skill conventions
- `CONTRIBUTING.md` — Repo contribution rules, SKILL.md requirements, naming conventions.
- `.claude/rules/skill-structure.md` — Canonical skill layout, frontmatter rules, naming patterns.
- `.claude/rules/skill-review.md` — 6-dimension scoring framework the skill must pass.
- `.claude/rules/content-quality.md` — Writing for AI agents, markdown standards, CLI documentation.

### Existing skill patterns (for structural reference)
- `skills/uipath-rpa-workflows/SKILL.md` — Mature skill example: discovery-first approach, reference navigation, core principles.
- `skills/uipath-coded-workflows/SKILL.md` — Another mature skill: precondition checks, quick start pattern, reference structure.

### Available build skills (genome must reference these)
- `skills/uipath-rpa-workflows/` — XAML/RPA workflow generation
- `skills/uipath-coded-workflows/` — Coded C# automation lifecycle
- `skills/uipath-maestro-flow/` — Flow authoring and orchestration
- `skills/uipath-coded-agents/` — Python agent lifecycle
- `skills/uipath-coded-apps/` — Coded web application lifecycle

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.genome_spec/TEMPLATE.md`: Genome format to embed in skill references (with Build section addition)
- 8 existing SKILL.md files: Structural patterns for YAML frontmatter, Critical Rules, Reference Navigation
- `.claude/rules/`: Repo-wide conventions that constrain skill structure

### Established Patterns
- Skills use SKILL.md as entry point with YAML frontmatter (name, description with TRIGGER/DO NOT TRIGGER)
- Reference files in `references/` subdirectory, kebab-case naming with `-guide.md` or `-template.md` suffixes
- Skills are self-contained — no cross-skill imports
- Mature skills (rpa-workflows, coded-workflows) follow: Core Principles → CLI Quick Reference → Supporting References → Workflow steps

### Integration Points
- The new skill folder: `skills/uipath-genome-authoring/`
- CODEOWNERS needs updating for the new skill path
- The genome template embedded in references needs the new Build section added

</code_context>

<specifics>
## Specific Ideas

- Interview flow inspired by GSD discuss-phase: free description dump, then targeted follow-ups for gaps
- Proactive UiPath feature suggestions are a key differentiator — the agent adds value beyond just formatting the user's words
- Orchestration as "just another step" — not special-cased, each workflow step owns its skill reference

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-genome-authoring-skill*
*Context gathered: 2026-04-02*
