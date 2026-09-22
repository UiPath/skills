# Authoring Guide — genome from a description

Turn a user's free-form automation description into a genome. User describes; agent infers, fills UiPath specifics, writes. Content rules and templates: [genome-format-guide.md](genome-format-guide.md).

## Step 1 — Receive the description

Accept anything from one sentence to several pages. Do not ask the user to elaborate before attempting extraction.

- **One sentence:** infer what you can, then ask one focused round of follow-ups for the largest gaps.
- **Several paragraphs:** extract methodically; follow-ups often unnecessary.
- **Contradictions:** name the specific conflict in the follow-up round. Do not guess which requirement wins.
- **Existing documents (SOP, PDD, process map, transcript):** treat the document as the description. A PDD or SDD the user wants turned into a solution design belongs to `uipath-planner`, not here; a genome is the right output only when the user asks for a genome or blueprint.

## Step 2 — Choose the level

Count the buildable projects the description implies and apply [genome-format-guide.md § Two Levels](genome-format-guide.md). Process-genome signals: "end-to-end", "across departments", "the flow kicks off the robot then the agent", "human approval for days", separate schedules or triggers for different parts, more than one deployable unit named.

## Step 3 — Infer complexity

Never ask ([genome-format-guide.md § Complexity](genome-format-guide.md)). Signals:

| Signal | Complexity |
|---|---|
| One target app, straightforward input-to-output, single sentence or paragraph | simple |
| Multiple systems, field mappings, business rules, conditional logic, explicit "retry" or "exception handling", scheduled or event trigger, "multiple departments" | medium |
| Multi-phase workflow, human approval or escalation, several integrations, orchestration, multiple deployable units | complex |

"Read Excel, fill a web form" stays simple even when described in detail. Any human approval step is at least complex for a component and forces a process genome when the approval lives outside the automation.

## Step 4 — Extract

From the description, extract: target applications, human actors, workflow steps in order, business rules, error scenarios, input and output data, triggers and schedules, hardcoded values (paths, addresses, thresholds, names), and:

- **Who signs in.** Every persona or account that logs into a target system (administrator, recruiter, integration user, a proxied approver) is one credential asset in Platform Dependencies ([genome-format-guide.md § Platform Dependencies](genome-format-guide.md)).
- **What varies per scenario.** When the description implies data-driven runs (per country, per organisation type, per integration, per worker), separate the fields that change per row from the constants; the row schema is what the Interface of a test component lists ([genome-format-guide.md § Interface](genome-format-guide.md)), the constants go to configuration.
- **Whether the application is reachable at build time.** Note it; execution captures UI targets live when it is and ships placeholders when it is not (an authored genome has no source target catalog).
- **What the unit of work is.** When the description iterates over items (each invoice, each row, each ticket, each file), name the item, its identifying reference, the daily volume, what produces the items and what consumes them; this is the Transactional Shape ([genome-format-guide.md § Transactional Shape](genome-format-guide.md)). A run that succeeds or fails as one has none — the stub.

## Step 5 — Suggest platform capabilities

Add these even when the user did not name them:

| User mentions | Add |
|---|---|
| PDFs, scanned documents, forms | Document Understanding activities in `uipath-rpa` step; `uipath-ixp` component when custom extraction model needed |
| Clicking, typing, reading a screen, desktop app | UI automation in `uipath-rpa` |
| REST APIs, connectors, SaaS systems | Integration Service connector activities (`uipath-rpa`) or `uipath-api-workflow` component when no UI involved |
| Many items processed independently, retries, resilience, several robots | Orchestrator queue in Platform Dependencies; Transactional Shape with producers, consumers and mode ([genome-format-guide.md § Transactional Shape](genome-format-guide.md)) |
| Coordinating several automations, waiting on events | `uipath-maestro-flow` (short-lived) or `uipath-maestro-bpmn` (long-running, human lanes) coordinator component |
| Judgement, classification, summarisation, free-text decisions | `uipath-agents` component |
| Human review, approval, sign-off | Human-in-the-loop checkpoint in coordinator; actor row in Actors and Systems |
| Screen for end users, dashboard | `uipath-coded-apps` component |
| Several automations or test suites drive the same application's screens | One `uipath-rpa` library component (screens and shared actions, Interface as per-workflow argument tables) plus consumer components; process genome states the library builds and packs first |
| Regression or test scenarios, "per release", "verify that", data-driven cases | One `uipath-rpa` test-case-group component per business area with data variations, all folders of the single test project ([genome-format-guide.md § Two Levels](genome-format-guide.md) rule 1); Test Manager under Platform Dependencies (`uipath-test`), never in Build With |
| Approvals performed as another user, "proxy as", "impersonate", "on behalf of" | Library step that switches user and stops the switch afterwards; one credential asset per persona that can be proxied |

## Step 6 — Ask follow-ups (bounded)

Group every gap into one message per round. State what you already know so the user does not repeat it. Rounds by complexity: simple 0-1, medium 1-2, complex 2-3. After the last round, generate with defaults and stubs; never loop.

Ask only for gaps that change the build: missing target system, unknown trigger, undefined decision outcome, unspecified failure behaviour for a critical step, unclear ownership of a handoff, which persona signs in for a scenario when several are implied, whether items must be shared across robots or survive a run failure when the description leaves it open (decides `queue` against `direct` in the Transactional Shape), and whether the UI application is reachable at build time (live capture) or not (placeholders, indicated later). Do not ask for values a Configuration Question can carry as a default.

## Step 7 — Generate

Populate every template section per the format guide's population matrix. Build With rows come from the skill mapping guide, one skill per step. Business rules and error handling attach to the step where they fire. The Transactional Shape classifies those rules and handlers into per-item outcomes and names producers, consumers and mode — or carries its stub ([genome-format-guide.md § Transactional Shape](genome-format-guide.md)). Acceptance criteria derive one-to-one from steps, rules, transformations, and handlers.

Process genomes: write the process file first (Components table, Process Map, Handoffs), then each component genome with its `Part of:` line and an Interface matching the Handoffs row.

Interface by component type ([genome-format-guide.md § Interface](genome-format-guide.md)): a library component gets one argument table per public workflow; a test component gets its per-scenario row schema and, separately, its constants; credentials appear as asset names, never values. Deployment records how UI targets will be obtained ("captured at build time against <environment>" or "placeholders until indicated") and that libraries pack before their consumers.

## Step 8 — Write, then offer edits

Write, then offer edits ([genome-format-guide.md § Write, Then Offer Edits](genome-format-guide.md)). Edits are in-place, never a regeneration:

| Request | Update |
|---|---|
| "Add detail to step X" | Workflow step X; add acceptance criteria if detail is testable |
| "Change complexity" | Complexity section, then section depth per matrix |
| "Add/remove an application" | Target Applications, Workflow, Build With, Acceptance Criteria |
| "Use a different skill for step X" | Build With row and rationale, validated against mapping guide |
| "Split this into components" | Promote to process genome: create process file, move component content into component files, add Handoffs |
| "Scenario X signs in as persona Y" | Platform Dependencies (credential asset for Y), test component's row schema (asset name per row), Configuration Questions |
| "Make it transactional" / "drop the transactional shape" / "queue instead of direct" | Transactional Shape (Recommendation, mode, tables); Components Type cell role words; Platform Dependencies (queue); Configuration Questions (retry counts) |
| "Step X should be a business exception" | Transactional Shape outcomes table; the rule under Business Rules for step X; an acceptance criterion for the recorded reason |
| "One row per transaction instead of one file" (change the unit of work) | Transactional Shape (Unit of work, Alternative unit of work, both tables, outcomes); Interface; Handoffs data passed; Platform Dependencies (queue); Acceptance Criteria (duplicate and retry cases) |
| "Split the dispatcher into its own component" | Promote to a process genome (row above); the producer becomes its own component with a `dispatcher` Type cell; Handoffs row for the queue |
| Edits to an extracted genome (rename / reorder / remove steps, "drop the Source Map") | [extraction-guide.md](extraction-guide.md) Step 7 |
