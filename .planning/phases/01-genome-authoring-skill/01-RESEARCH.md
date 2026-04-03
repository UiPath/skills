# Phase 1: Genome Authoring Skill - Research

**Researched:** 2026-04-02
**Domain:** UiPath agent skill authoring (markdown-only, no code)
**Confidence:** HIGH

## Summary

This phase creates a new skill (`uipath-genome-authoring`) that interviews users about automation ideas and outputs structured genome markdown files. The entire deliverable is markdown documentation — no code, no build system, no external dependencies. The "stack" is the repo's own conventions: YAML frontmatter in SKILL.md, kebab-case references, prescriptive agent instructions, and the genome template format from `.genome_spec/TEMPLATE.md`.

The core challenge is designing an interview flow that adapts to complexity (simple ideas need minimal questions, complex ones need a full interview) and produces genome files with testable acceptance criteria. The skill must also add a new "Build With" section to the template that maps workflow steps to existing UiPath skills.

**Primary recommendation:** Follow the established skill pattern (SKILL.md + references/) closely. The interview logic, complexity inference rules, and template population rules go into SKILL.md. The genome template (with Build section added) and the skill-mapping reference go into `references/`. Keep SKILL.md focused on workflow and critical rules; extract the full template into a reference file.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- User provides free-form description first; agent infers complexity (simple/medium/complex) — user does not declare it
- Agent extracts what it can, then asks targeted follow-ups only for gaps (GSD discuss-phase style)
- Agent proactively suggests UiPath-specific features the user might not know about
- Simple genomes: Overview, Target Applications, Workflow, Acceptance Criteria, Tags, Complexity mandatory; other sections get stubs with guidance
- Medium/Complex: All sections populated, depth proportional to complexity
- Sections that don't apply are never omitted — always stub with guidance
- Acceptance criteria must be specific and testable, derived from workflow steps
- Add explicit Build With section to genome template — single recommended skill per workflow step with rationale
- Each workflow step can reference its own skill; orchestration is treated as its own step
- Agent infers the right skill based on workflow type, target apps, and complexity
- Genome file written to user's CWD as `{slug}-genome.md` — no preview, write immediately then offer edits
- Embed genome template inside `skills/uipath-genome-authoring/references/` — fully self-contained
- No example genomes needed as references — template + interview instructions are sufficient
- Use /skill-creator skill when building to ensure quality and repo conventions

### Claude's Discretion
- Exact follow-up question phrasing and ordering
- How to structure the interview for edge cases (very short descriptions, contradictory requirements)
- Whether to group follow-up questions or ask one at a time

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AUTH-01 | User can describe an automation idea and receive a complete genome markdown file | Interview flow design + template population rules + file output conventions |
| AUTH-02 | Agent asks configuration questions adapted to genome complexity | Complexity inference rules + per-level question depth guidelines |
| AUTH-03 | Genome output follows TEMPLATE.md format with all applicable sections populated | Template format from `.genome_spec/TEMPLATE.md` + stub rules for unused sections |
| AUTH-04 | Agent generates testable acceptance criteria derived from described workflow | Acceptance criteria generation rules + examples from genome spec |
| AUTH-05 | Agent handles all three complexity levels | Complexity spectrum definition + section population matrix |
</phase_requirements>

## Standard Stack

This is a documentation-only project. There are no libraries, packages, or build tools.

### Core
| Asset | Location | Purpose | Why Standard |
|-------|----------|---------|--------------|
| SKILL.md | `skills/uipath-genome-authoring/SKILL.md` | Skill entry point | Required by plugin system; only file the agent reads at discovery |
| YAML frontmatter | Top of SKILL.md | Skill metadata (name, description, trigger conditions) | Plugin system parses this for skill activation |
| references/ | `skills/uipath-genome-authoring/references/` | Supporting docs | Repo convention for extracted reference material |

### Supporting
| Asset | Purpose | When to Use |
|-------|---------|-------------|
| `.genome_spec/TEMPLATE.md` | Source of truth for genome format | Embed (with Build section added) into skill's references |
| `.genome_spec/examples/*.md` | Reference examples for complexity levels | Inform interview rules and section population logic |
| Existing skills (rpa-workflows, coded-workflows, maestro-flow, coded-agents, coded-apps) | Build With section targets | Skill must know which skill maps to which automation type |

### Alternatives Considered
None applicable — this is a markdown-documentation-only deliverable within an established repo structure.

## Architecture Patterns

### Recommended Skill Structure
```
skills/uipath-genome-authoring/
├── SKILL.md                          # Skill definition: frontmatter + interview workflow + critical rules
└── references/
    ├── genome-template.md            # Embedded genome template (TEMPLATE.md + Build With section)
    └── skill-mapping-guide.md        # Which UiPath skill handles which automation type
```

### Pattern 1: Interview-Driven Skill (SKILL.md body)
**What:** A skill whose primary workflow is a multi-turn conversation that produces a file artifact.
**When to use:** When the agent needs to gather information iteratively before producing output.

The SKILL.md body should follow this structure:
1. Frontmatter (name, description with TRIGGER/DO NOT TRIGGER)
2. Title and "When to Use" section
3. Critical Rules (numbered, highest-priority constraints)
4. Interview Workflow (step-by-step: intake → infer complexity → extract → follow-up → generate → write)
5. Reference Navigation (links to genome-template.md, skill-mapping-guide.md)
6. Anti-patterns

This mirrors existing skills like `uipath-report-issue` which also follows an intake → process → output pattern with minimal user interactions.

### Pattern 2: Complexity-Adaptive Behavior
**What:** The agent adjusts its behavior based on inferred complexity of the user's input.
**When to use:** For AUTH-02 and AUTH-05 — different complexity levels need different interview depth.

The complexity inference should be rule-based (not ambiguous). Define concrete signals:

| Signal | Points toward |
|--------|--------------|
| Single sentence / paragraph, one target app | Simple |
| Multiple systems, field mappings, or business rules mentioned | Medium |
| Multi-phase workflow, error handling requirements, multiple integrations, orchestration needed | Complex |

### Pattern 3: Template Population Matrix
**What:** A decision table specifying which genome sections get populated vs. stubbed for each complexity level.
**When to use:** For AUTH-03 and AUTH-05 — ensures consistent output regardless of complexity.

| Section | Simple | Medium | Complex |
|---------|--------|--------|---------|
| Overview | Full | Full | Full |
| Target Applications | Full | Full | Full |
| Configuration Questions | Stub | Full | Full |
| Workflow | Full | Full | Full (detailed) |
| Business Rules | Stub | Full | Full |
| Error Handling | Stub | Full | Full |
| Acceptance Criteria | Full | Full | Full (detailed) |
| Build With | Full | Full | Full |
| Complexity | Full | Full | Full |
| Tags | Full | Full | Full |

"Stub" means: section heading present with a one-line guidance note (e.g., "No explicit business rules — agent uses standard validation patterns"). Never omit a section entirely.

### Pattern 4: Build With Section
**What:** A new genome section that maps workflow steps to UiPath skills.
**When to use:** Every genome output must include this section.

Format (derived from CONTEXT.md decisions):
```markdown
## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| 1. Extract invoice data | `uipath-rpa-workflows` | Document Understanding activities are XAML-based |
| 2. Validate against PO | `uipath-coded-workflows` | Business logic with API calls suits coded C# |
| 3. Orchestrate end-to-end | `uipath-maestro-flow` | Multi-step orchestration with queues |
```

### Anti-Patterns to Avoid
- **Asking the user to declare complexity.** The agent infers it from the description. Never ask "Is this simple, medium, or complex?"
- **Omitting sections.** Even if a section doesn't apply, it gets a stub. The genome template must be complete.
- **Generic acceptance criteria.** "Step completes successfully" is banned. Criteria must reference specific observable outcomes from the workflow (e.g., "Correctly extracts invoice number from sample PDF").
- **Showing a preview before writing.** The agent writes the file immediately, then offers edits. No "here's what I'll generate" step.
- **Cross-skill references in SKILL.md.** The skill must be self-contained. The genome template is embedded in references/, not imported from `.genome_spec/`.
- **Overly long SKILL.md.** The template and skill-mapping details should be in reference files, not inlined in SKILL.md. SKILL.md stays focused on workflow and rules.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Genome template format | A new template format | `.genome_spec/TEMPLATE.md` + Build With addition | Template is already designed and has working examples |
| Skill structure | Custom folder layout or frontmatter | Repo conventions from CONTRIBUTING.md + skill-structure.md rules | Plugin system expects exact conventions; deviation breaks discovery |
| TRIGGER/DO NOT TRIGGER conditions | Vague description field | Pattern from existing skills (rpa-workflows, coded-workflows) | Specific trigger/exclusion conditions prevent false activations |
| Acceptance criteria patterns | Ad-hoc criteria generation rules | Patterns from genome examples (email-triage.md, invoice-processing.md) | Examples demonstrate the specificity and testability standard |

## Common Pitfalls

### Pitfall 1: Frontmatter YAML Breakage
**What goes wrong:** Invalid YAML in SKILL.md frontmatter (tabs instead of spaces, unquoted colons in strings, missing dashes).
**Why it happens:** Description fields contain colons and special characters.
**How to avoid:** Always quote the `description` field. Test that the frontmatter parses as valid YAML.
**Warning signs:** Plugin system fails to discover the skill.

### Pitfall 2: TRIGGER Conditions Too Broad or Too Narrow
**What goes wrong:** Skill activates for unrelated requests (too broad) or fails to activate for valid genome requests (too narrow).
**Why it happens:** The description field controls activation. "genome" is not a term users commonly know.
**How to avoid:** Trigger on user-facing language: "describe an automation", "plan an automation", "create a genome", "design a workflow spec". Exclude: actual building/coding requests (those go to rpa-workflows/coded-workflows), project structure questions (uipath-platform), flow editing (.flow files — maestro-flow).
**Warning signs:** Users get the wrong skill or no skill activation.

### Pitfall 3: Interview That Never Converges
**What goes wrong:** The agent keeps asking follow-up questions without producing output.
**Why it happens:** No explicit convergence rule — the agent doesn't know when it has enough information.
**How to avoid:** Define a maximum follow-up count per complexity level (e.g., simple: 0-1 rounds, medium: 1-2 rounds, complex: 2-3 rounds). After the last round, generate the genome with what's available and offer edits.
**Warning signs:** User frustration, abandoned conversations.

### Pitfall 4: Acceptance Criteria That Are Not Testable
**What goes wrong:** Generated acceptance criteria are vague ("works correctly", "handles errors").
**Why it happens:** The agent doesn't anchor criteria to specific workflow steps and observable outcomes.
**How to avoid:** Critical rule: each acceptance criterion must reference a specific input/output or workflow step. Provide examples in the skill instructions. Pattern: "Given [input], the automation [observable outcome]".
**Warning signs:** Criteria that could apply to any automation, not this specific one.

### Pitfall 5: Build With Section Maps to Wrong Skill
**What goes wrong:** Genome recommends `uipath-coded-workflows` for something that needs `uipath-rpa-workflows` (or vice versa).
**Why it happens:** The mapping logic doesn't account for the actual capabilities of each skill.
**How to avoid:** Create a clear skill-mapping reference that documents what each skill handles. Key distinctions: XAML/RPA (UI automation, Document Understanding, activities-heavy) vs. coded workflows (C# business logic, API integration, complex data processing) vs. maestro-flow (orchestration of multiple automations) vs. coded-agents (Python AI agents) vs. coded-apps (web applications).
**Warning signs:** Users build with the wrong skill and hit dead ends.

### Pitfall 6: Embedded Template Drifts from Source of Truth
**What goes wrong:** The genome template in `references/genome-template.md` diverges from `.genome_spec/TEMPLATE.md` over time.
**Why it happens:** Someone updates the spec but forgets the embedded copy (or vice versa).
**How to avoid:** Document in the skill that `.genome_spec/TEMPLATE.md` is the canonical source. The embedded version adds the Build With section but otherwise must match. Add a note in the template file header pointing to the source.
**Warning signs:** Generated genomes don't match the expected format.

## Code Examples

These are not "code" in the traditional sense — this is a markdown-only project. Examples below show the expected content patterns.

### SKILL.md Frontmatter Pattern
```yaml
---
name: uipath-genome-authoring
description: "Interview users about automation ideas and produce structured genome markdown files. TRIGGER when: user wants to describe an automation idea, plan an automation, create a genome, design a workflow specification, or says 'I want to automate...'. DO NOT TRIGGER when: user wants to build/code/edit an actual automation (use uipath-rpa-workflows, uipath-coded-workflows, uipath-coded-agents, uipath-coded-apps, or uipath-maestro-flow), or wants to extract a genome from an existing project (Phase 2 skill), or is asking about UiPath platform/CLI setup (use uipath-platform)."
---
```
Source: Derived from existing skill frontmatter patterns (rpa-workflows, coded-workflows, maestro-flow, servo, report-issue).

### Genome Template with Build With Section
```markdown
# Genome: {Name}

> {One-line description of what this automation does}

## Overview
{1-3 paragraphs...}

## Target Applications
| Application | Role | Notes |
|-------------|------|-------|
| {app} | {role} | {notes} |

## Configuration Questions
{Questions the agent should ask the user before building...}

## Workflow
1. **Trigger**: {What starts the automation}
2. **Step**: {What happens}
3. **Output**: {What the automation produces}

## Business Rules
{Key rules, validations, or decision logic...}

## Error Handling
{Retry logic, notifications, fallback paths...}

## Acceptance Criteria
- [ ] {Specific, testable criterion derived from workflow steps}
- [ ] {Another specific criterion}

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| {Workflow step} | `{uipath-skill-name}` | {Why this skill fits} |

## Complexity
{simple | medium | complex}

## Tags
{Comma-separated tags}
```
Source: `.genome_spec/TEMPLATE.md` with Build With section added per CONTEXT.md decisions.

### Skill-to-Automation-Type Mapping
```markdown
| Automation Type | Skill | When to Recommend |
|-----------------|-------|-------------------|
| UI automation, desktop apps, browser interaction, Document Understanding, activity-based workflows | `uipath-rpa-workflows` | XAML/RPA workflow generation using UiPath activities |
| Business logic, API calls, data processing, complex C# logic, Integration Service connectors from code | `uipath-coded-workflows` | Coded C# automation lifecycle |
| Orchestration of multiple automations, queue management, multi-step flows, scheduling | `uipath-maestro-flow` | Flow authoring and orchestration |
| AI/ML agents, Python-based automation, LLM integration | `uipath-coded-agents` | Python agent lifecycle |
| Web applications, user-facing forms and dashboards | `uipath-coded-apps` | Coded web application lifecycle |
```
Source: Derived from existing skill descriptions and CONTEXT.md canonical references.

### Acceptance Criteria Generation Pattern
Good (specific, testable, derived from workflow):
```markdown
- [ ] Correctly extracts invoice number, date, vendor, and total from a sample PDF invoice
- [ ] Rejects invoices where total exceeds PO amount by more than the configured tolerance
- [ ] Routes failed validations to the exception queue with extraction results and failure reason
```

Bad (generic, not testable):
```markdown
- [ ] Invoice processing completes successfully
- [ ] Errors are handled properly
- [ ] Data is extracted correctly
```
Source: `.genome_spec/examples/invoice-processing.md` acceptance criteria patterns.

## State of the Art

| Aspect | Current State | Impact |
|--------|--------------|--------|
| Genome format | Established in `.genome_spec/TEMPLATE.md` with 3 working examples | Template is stable; Build With section is the only addition needed |
| Skill conventions | Mature — 8 existing skills follow consistent patterns | Strong precedent for structure, frontmatter, and reference organization |
| Plugin system | Reads SKILL.md frontmatter for discovery; description field controls activation | Frontmatter must be valid YAML with specific TRIGGER/DO NOT TRIGGER format |
| Available build skills | 5 skills cover the UiPath automation spectrum | Complete coverage for the Build With section mapping |

## Open Questions

1. **Exact complexity inference thresholds**
   - What we know: Three levels (simple/medium/complex) with qualitative signals defined in CONTEXT.md
   - What's unclear: Precise cutoff criteria when a description falls between levels
   - Recommendation: Default to the lower complexity level when ambiguous. The agent can always escalate if follow-up questions reveal more complexity. Document the signals as a numbered decision tree, not prose.

2. **Interaction with `/skill-creator` during implementation**
   - What we know: CONTEXT.md says "Use /skill-creator skill when building to ensure quality and repo conventions"
   - What's unclear: Whether `/skill-creator` is an existing tool/skill in this repo or an external workflow
   - Recommendation: The planner should note this as an implementation detail. The skill itself must pass the 6-dimension review framework from `.claude/rules/skill-review.md` regardless of how it's built.

3. **CODEOWNERS entry for the new skill**
   - What we know: CODEOWNERS must be updated per repo rules
   - What's unclear: Which GitHub handle(s) own this skill
   - Recommendation: Flag as a task that requires user input during implementation.

## Sources

### Primary (HIGH confidence)
- `.genome_spec/TEMPLATE.md` — Canonical genome format (all sections, placeholder syntax)
- `.genome_spec/DISCUSSION.md` — Design decisions: complexity spectrum, agent-carries-weight philosophy
- `.genome_spec/examples/email-triage.md` — Simple genome example with acceptance criteria pattern
- `.genome_spec/examples/invoice-processing.md` — Medium genome example with full sections populated
- `.genome_spec/examples/simple-data-transfer.md` — Minimal "hello world" genome example
- `CONTRIBUTING.md` — Repo contribution rules, skill structure requirements
- `.claude/rules/skill-structure.md` — Canonical folder layout, frontmatter rules, naming patterns
- `.claude/rules/skill-review.md` — 6-dimension scoring framework (Structure, Consistency, Logic, Duplication, LLM Usability, Marketplace)
- `.claude/rules/content-quality.md` — Writing for AI agents, markdown standards
- `skills/uipath-rpa-workflows/SKILL.md` — Mature skill pattern: discovery-first, reference navigation
- `skills/uipath-coded-workflows/SKILL.md` — Mature skill pattern: precondition checks, quick start
- `skills/uipath-report-issue/SKILL.md` — Interview-style workflow pattern (intake → process → output)
- `skills/uipath-maestro-flow/SKILL.md` — Complex skill with numbered critical rules and reference extraction
- `.planning/phases/01-genome-authoring-skill/01-CONTEXT.md` — All locked decisions for this phase

### Secondary (MEDIUM confidence)
- Skill-to-automation-type mapping — derived from existing skill descriptions; mapping logic is reasonable but not formally documented anywhere

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — repo conventions are well-documented and consistent across 8 existing skills
- Architecture: HIGH — direct precedent from existing skills (especially report-issue for interview pattern, rpa-workflows for reference extraction pattern)
- Pitfalls: HIGH — pitfalls derived from actual repo constraints (frontmatter parsing, trigger conditions) and CONTEXT.md explicit anti-patterns

**Research date:** 2026-04-02
**Valid until:** Indefinite for repo conventions; genome spec may evolve but is stable for now
