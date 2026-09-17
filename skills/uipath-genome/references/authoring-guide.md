# Authoring Guide — genome from a description

Turn a user's free-form description of an automation into a genome. The user describes; the agent infers, fills UiPath specifics, and writes. Content rules and templates: [genome-format-guide.md](genome-format-guide.md).

## Step 1 — Receive the description

Accept anything from one sentence to several pages. Do not ask the user to elaborate before attempting extraction.

- **One sentence:** infer what you can, then ask one focused round of follow-ups for the largest gaps.
- **Several paragraphs:** extract methodically; follow-ups are often unnecessary.
- **Contradictions:** name the specific conflict in the follow-up round. Do not guess which requirement wins.
- **Existing documents (SOP, PDD, process map, transcript):** treat the document as the description. A PDD or SDD that the user wants turned into a solution design belongs to `uipath-planner`, not here; a genome is the right output only when the user asks for a genome or blueprint.

## Step 2 — Choose the level

Count the buildable projects the description implies (see [skill-mapping-guide.md](skill-mapping-guide.md) rule 3). One → component genome. Two or more, or a coordinator plus the automations it invokes → process genome plus one component genome each.

Signals for a process genome: "end-to-end", "across departments", "the flow kicks off the robot then the agent", "human approval for days", separate schedules or triggers for different parts, more than one deployable unit named.

## Step 3 — Infer complexity

Never ask the user to declare complexity. Infer it, defaulting to the lower level when ambiguous; escalate if follow-ups reveal more.

| Signal | Complexity |
|---|---|
| One target app, straightforward input-to-output, single sentence or paragraph | simple |
| Multiple systems, field mappings, business rules, conditional logic, explicit "retry" or "exception handling", scheduled or event trigger, "multiple departments" | medium |
| Multi-phase workflow, human approval or escalation, several integrations, orchestration, multiple deployable units | complex |

"Read Excel, fill a web form" stays simple even when described in detail. Any human approval step is at least complex for a component and forces a process genome when the approval lives outside the automation.

## Step 4 — Extract

From the description, extract: target applications, human actors, workflow steps in order, business rules, error scenarios, input and output data, triggers and schedules, hardcoded values (paths, addresses, thresholds, names).

## Step 5 — Suggest platform capabilities

Add these to the genome even when the user did not name them:

| User mentions | Add |
|---|---|
| PDFs, scanned documents, forms | Document Understanding activities in an `uipath-rpa` step; an `uipath-ixp` component when a custom extraction model is needed |
| Clicking, typing, reading a screen, desktop app | UI automation in `uipath-rpa` |
| REST APIs, connectors, SaaS systems | Integration Service connector activities (`uipath-rpa`) or an `uipath-api-workflow` component when no UI is involved |
| Many items processed independently, retries, resilience | Orchestrator queue in Platform Dependencies; dispatcher/performer split as two workflow phases |
| Coordinating several automations, waiting on events | `uipath-maestro-flow` (short-lived) or `uipath-maestro-bpmn` (long-running, human lanes) coordinator component |
| Judgement, classification, summarisation, free-text decisions | `uipath-agents` component |
| Human review, approval, sign-off | Human-in-the-loop checkpoint in the coordinator, actor row in Actors and Systems |
| Screen for end users, dashboard | `uipath-coded-apps` component |

## Step 6 — Ask follow-ups (bounded)

Group every gap into one message per round. State what you already know so the user does not repeat it. Rounds by complexity: simple 0-1, medium 1-2, complex 2-3. After the last round, generate with defaults and stubs; never loop.

Ask only for gaps that change the build: missing target system, unknown trigger, undefined decision outcome, unspecified failure behaviour for a critical step, unclear ownership of a handoff. Do not ask for values that a Configuration Question can carry as a default.

## Step 7 — Generate

Populate every template section per the format guide's population matrix. Build With rows come from the skill mapping guide, one skill per step. Business rules and error handling attach to the step where they fire. Acceptance criteria derive one-to-one from steps, rules, transformations, and handlers.

Process genomes: write the process file first (Components table, Process Map, Handoffs), then each component genome with its `Part of:` line and an Interface that matches the Handoffs row.

## Step 8 — Write, then offer edits

Write the file(s) immediately. Do not preview or ask for confirmation. Then say where the file is and ask "Want to adjust anything?"

Edits are in-place, never a regeneration:

| Request | Update |
|---|---|
| "Add detail to step X" | Workflow step X; add acceptance criteria if the detail is testable |
| "Change complexity" | Complexity section, then section depth per the matrix |
| "Add/remove an application" | Target Applications, Workflow, Build With, Acceptance Criteria |
| "Use a different skill for step X" | Build With row and rationale, validated against the mapping guide |
| "Split this into components" | Promote to a process genome: create the process file, move component content into component files, add Handoffs |
