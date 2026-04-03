---
name: uipath-genome-authoring
description: "Interview users about automation ideas and produce structured genome markdown files. TRIGGER when: user wants to describe an automation idea, plan an automation, create a genome, design a workflow specification, or says 'I want to automate...'. DO NOT TRIGGER when: user wants to build/code/edit an actual automation (use uipath-rpa-workflows, uipath-coded-workflows, uipath-coded-agents, uipath-coded-apps, or uipath-maestro-flow), user wants to extract a genome from an existing project (use uipath-genome-extraction), or user is asking about UiPath platform/CLI setup (use uipath-platform)."
---

# Genome Authoring

Interview users about their automation ideas and produce structured genome markdown specifications. The agent carries the weight — users describe what they want, the agent fills in the UiPath-specific details.

## When to Use This Skill

- User describes an automation idea ("I want to automate invoice processing")
- User asks to create a genome or automation spec
- User says "plan an automation" or "design a workflow"
- User wants to document what an automation should do before building it
- User provides a free-form description of a process they want automated

## Critical Rules

1. **User describes, agent infers.** The user provides a free-form description. The agent infers complexity (simple/medium/complex) from the description. Never ask the user to declare complexity.
2. **Extract first, ask second.** Parse the user's description and extract everything possible (target apps, workflow steps, business rules, error scenarios, input/output data). Only ask follow-up questions for genuine gaps — not for information already provided or inferable.
3. **Follow-up depth scales with complexity.** Simple: 0-1 follow-up rounds. Medium: 1-2 rounds. Complex: 2-3 rounds. After the last round, generate the genome with available information and offer edits. Never let the interview loop indefinitely.
4. **Proactively suggest UiPath features.** When the description mentions PDFs or documents, suggest Document Understanding. When it mentions web forms or desktop apps, suggest UI Automation. When it mentions third-party connectors, suggest Integration Service. When it mentions coordinating multiple automations, suggest Orchestrator queues or Maestro flows. Add these to the genome even if the user did not mention them.
5. **Every section present, always.** The genome must include all template sections. For simple genomes, sections that do not apply get a stub with guidance (e.g., "No explicit business rules — agent applies standard validation patterns."). Never omit a section entirely.
6. **Acceptance criteria must be specific and testable.** Each criterion references a concrete input, output, or observable behavior from the workflow. Pattern: "Given [specific input], the automation [specific observable outcome]." Ban generic criteria like "step completes successfully" or "errors handled properly."
7. **Write immediately, offer edits after.** Write the genome file to the user's CWD as `{slug}-genome.md` immediately after generating. Then ask "Want to adjust anything?" Do not show a preview or ask for confirmation before writing.
8. **One skill per workflow step in Build With.** Each workflow step maps to exactly one skill. Use [skill-mapping-guide.md](../shared/genome/skill-mapping-guide.md) for selection. Orchestration (queues, multi-step flows) is its own step with its own skill reference — not a top-level annotation.
9. **Always include the blueprint preamble.** Every genome must start with the HTML comment `<!-- UIPATH-AUTOMATION-GENOME: ... -->` and the visible blockquote "This is a UiPath automation blueprint..." immediately after the one-liner. This prevents AI agents from executing the workflow steps directly instead of building a UiPath project. Build With must appear before Workflow in the template so agents encounter the skill references before the steps.

## Workflow

### Step 1 — Receive Description

The user provides a free-form description of their automation idea. This can range from a single sentence to multiple paragraphs. Accept whatever they give.

Handle edge cases:
- **Very short description** (one sentence): Infer what you can, then ask one focused round of follow-ups to fill the biggest gaps. Do not reject or ask the user to elaborate before attempting extraction.
- **Very long description** (multiple paragraphs): Extract everything methodically. You may not need any follow-ups at all.
- **Contradictory requirements**: Note the contradiction in your follow-up questions and ask the user to clarify the specific conflict. Do not guess which requirement takes priority.

### Step 2 — Infer Complexity

Analyze the description against these signals:

| Signal | Complexity |
|--------|------------|
| Single sentence/paragraph, one target app, straightforward input-to-output | Simple |
| Multiple systems mentioned, field mappings, business rules, or conditional logic | Medium |
| Multi-phase workflow, error handling requirements, multiple integrations, orchestration needed, human-in-the-loop | Complex |

When ambiguous, default to the lower level. Follow-up questions may reveal higher complexity — escalate if so.

Additional complexity signals:
- Mentions "exception handling" or "retry" explicitly -> at least Medium
- Mentions human approval, review steps, or escalation -> Complex
- Mentions scheduled triggers or event-driven orchestration -> at least Medium
- Single app, single action (e.g., "read Excel, fill web form") -> Simple even if described in detail
- Mentions "multiple departments" or "end-to-end process" -> at least Medium

### Step 3 — Extract from Description

Parse the description and extract:
- **Target applications** — what systems are involved
- **Workflow steps** — what happens in what order
- **Business rules** — any validation, conditions, or decision logic mentioned
- **Error scenarios** — any failure handling mentioned
- **Input/output data** — what goes in, what comes out

### Step 4 — Identify Gaps and Suggest Features

Compare extracted information against the genome template sections. For each gap:
- If the section is mandatory for this complexity level (see population matrix in Step 6), prepare a follow-up question.
- If the user's description implies a UiPath capability they did not name, note the suggestion.

Proactively suggest these UiPath features when relevant:

| User Mentions | Suggest |
|---------------|---------|
| PDFs, scanned documents, images of forms | Document Understanding |
| Desktop app interaction, clicking, typing, reading screen | UI Automation (RPA workflows) |
| REST APIs, connectors, third-party services | Integration Service |
| Multiple automations coordinated, scheduling | Orchestrator queues, Maestro flows |
| Web forms or dashboards for end users | Coded Apps |
| AI/ML or LLM-powered decisions | Coded Agents |

### Step 5 — Ask Follow-up Questions (if needed)

Group related gaps into a single set of questions. Ask all at once — do not ask one at a time. State what you already know from the description so the user does not repeat themselves.

Follow-up limits by complexity:
- **Simple:** Skip follow-ups entirely if the description is sufficient, or ask at most 1 round.
- **Medium:** 1-2 rounds maximum.
- **Complex:** 2-3 rounds maximum.

After the final round, proceed to generation regardless of remaining gaps. Fill gaps with reasonable defaults and stub guidance.

If follow-up questions reveal the automation is more complex than initially inferred, escalate the complexity level before generating.

### Step 6 — Generate Genome

Read the genome template from [genome-template.md](../shared/genome/genome-template.md). Populate every section according to this population matrix:

| Section | Simple | Medium | Complex |
|---------|--------|--------|---------|
| Overview | Full (1 paragraph) | Full (2-3 paragraphs) | Full (2-3 paragraphs) |
| Target Applications | Full | Full | Full |
| Build With | Full | Full | Full |
| Configuration Questions | Stub | Full (3-5 questions minimum) | Full (5+ questions minimum) |
| Workflow | Full (3-5 steps minimum) | Full (5+ steps, substeps where detailed) | Full (8+ steps, substeps where detailed) |
| Business Rules | Stub | Full (step-associated) | Full (step-associated) |
| Error Handling | Stub | Full (per-step where applicable) | Full (per-step where applicable) |
| Acceptance Criteria | Full (3-4 criteria minimum) | Full (5+ criteria including data checks) | Full (7+ criteria including data checks) |
| Complexity | Full | Full | Full |
| Tags | Full | Full | Full |

**These are minimums, not ceilings.** If the user describes 15 workflow steps, write 15 steps. If they describe 10 business rules, write 10 rules. Capture everything the user provides at the depth they provide it.

**"Full"** means populated with specific content derived from the interview. **"Stub"** means the section heading is present with a one-line guidance note. Example stubs:
- Configuration Questions: "Description covers the scope — no additional configuration needed."
- Business Rules: "No explicit business rules — agent applies standard validation patterns."
- Error Handling: "Standard error handling — retry on transient failures, log and skip on permanent errors."

**Build With section:** Map each major workflow step to a skill using [skill-mapping-guide.md](../shared/genome/skill-mapping-guide.md). Include rationale for each choice. If a step mixes concerns (e.g., UI interaction and data processing), split it into two steps, each with its own skill.

**Workflow steps:** When the user describes detailed operations (field mappings, validation rules, data transformations), use substeps (a, b, c) to capture that detail. Associate business rules with the workflow step where they apply rather than listing them separately.

**Error handling:** When the user describes error handling for specific steps, associate each handler with its step rather than listing them generically.

**Acceptance Criteria:** Derive each criterion from a specific workflow step or business rule. Use these patterns:
- "Given [specific input], the automation [specific observable outcome]."
- "[Specific action] produces [specific result]."
- "When [condition], the automation [expected behavior]."

When the user describes field mappings or data transformations, include criteria that verify data fidelity (specific fields extracted, calculated, or mapped correctly). Every criterion must reference a concrete input, output, or workflow step. Ban vague criteria — if you cannot point to the specific step or data it validates, rewrite it.

### Step 7 — Write File

Write the genome to the user's current working directory as `{slug}-genome.md`.

Derive the slug from the automation name: lowercase, hyphens for spaces, strip special characters.
- "Invoice Processing" -> `invoice-processing-genome.md`
- "Email Triage & Routing" -> `email-triage-routing-genome.md`
- "Excel to Web Data Transfer" -> `excel-to-web-data-transfer-genome.md`

### Step 8 — Offer Edits

After writing, tell the user the file has been created and ask: "Want to adjust anything?" If they request changes, edit the file in place and confirm. Do not regenerate from scratch — apply targeted edits.

Common edit requests and how to handle them:
- **"Add more detail to step X"**: Expand that workflow step and update acceptance criteria if the new detail is testable.
- **"Change the complexity level"**: Update Complexity section, then adjust section depth to match the new level per the population matrix.
- **"Add/remove a target application"**: Update Target Applications, Workflow (add/remove relevant steps), Build With (add/remove skill mapping), and Acceptance Criteria.
- **"This should use a different skill for step X"**: Update Build With table with the new skill and rationale. Consult [skill-mapping-guide.md](../shared/genome/skill-mapping-guide.md) to validate the change.

## Reference Navigation

- **[genome-template.md](../shared/genome/genome-template.md)** — Full genome template with all sections. Read this when populating the genome output.
- **[skill-mapping-guide.md](../shared/genome/skill-mapping-guide.md)** — Which UiPath skill handles which automation type. Consult when populating the Build With section.

## Anti-patterns

1. **Asking the user to declare complexity.** The agent infers it from the description. Never say "Is this a simple, medium, or complex automation?"
2. **Showing a preview before writing.** Write the file first, then offer edits. No "Here's what I'll generate — look good?" step.
3. **Generic acceptance criteria.** "Completes successfully" and "handles errors" are banned. Every criterion must reference a specific input/output or workflow step.
4. **Omitting sections.** Even if a section does not apply, include it with a stub. The genome template must be complete.
5. **Asking too many questions.** Respect the follow-up limits per complexity level. Extract as much as possible from the initial description. When in doubt, generate with reasonable defaults and offer edits.
6. **Top-level orchestration annotation.** Orchestration is a workflow step like any other, with its own skill in Build With. Do not add a separate "Orchestration" section or top-level note outside the workflow.
7. **Asking questions one at a time.** Group all follow-up questions into a single message. State what you already know so the user does not repeat themselves.
8. **Compressing workflow steps to fit a target count.** The population matrix is a minimum. If the user describes 20 steps, write 20 steps. Never summarize multiple distinct steps into one.
9. **Flat workflow steps for detailed operations.** When the user describes field mappings, validation rules, or data transformations within a step, use substeps to capture that detail. "Validate the invoice" is too shallow when the user told you exactly what validation means.
10. **Disconnected business rules.** A flat list of rules forces the rebuilding agent to guess which step each rule belongs to. Associate every rule with its workflow step when the association is clear.
