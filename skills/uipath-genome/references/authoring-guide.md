# Authoring Guide — genome from a description

Turn a user's free-form automation description, or a goal the agent proposes a scenario for, into a genome. User describes or picks; agent infers, fills UiPath specifics, writes. Content rules and templates: [genome-format-guide.md](genome-format-guide.md).

## Step 1 — Receive the description

Accept anything from one sentence to several pages. Do not ask the user to elaborate before attempting extraction.

- **One sentence:** infer what you can, then ask one focused round of follow-ups for the largest gaps.
- **Several paragraphs:** extract methodically; follow-ups often unnecessary.
- **Contradictions:** name the specific conflict in the follow-up round. Do not guess which requirement wins.
- **Existing documents (SOP, PDD, process map, transcript):** treat the document as the description — when the user asked for a genome or blueprint; otherwise it is `uipath-planner`'s ([SKILL.md § Mode Detection](../SKILL.md)).
- **A goal, not a process** (a self-paced workshop, a demo, trying a product or an application): propose scenarios first (Step 1a); the picked scenario is the description.

## Step 1a — Propose scenarios for a goal

1. **Ask one round:** one `AskUserQuestion` batch of two multi-select questions, each skipped when the request already answers it.
   - **Products to exercise:** RPA, agents, orchestration (Maestro Flow, BPMN, Case), document extraction, human review and apps.
   - **Systems within reach, grouped by the setup they need:** none (local files, Excel, public APIs); a tenant connection (mail, chat, a SaaS system); an application installed or hosted for the user (SAP, an internal web application).

   Group the systems by setup because every connection, account or installation is one more thing that can fail before the scenario runs; the grouping lets the user trade reach against setup.
2. **Propose up to three scenarios** built for the answers, using only the systems within reach plus sources that need no setup. Each is a card:
   - storyline, one sentence: what arrives, what is decided or done, where the result lands
   - Components table, `# | Component | Type | Skill | Summary`, skills per Step 5 and [skill-mapping-guide.md](skill-mapping-guide.md); one row makes a component genome
   - applications and the setup each needs (connection, account, installation)
   - input source (item 3)
   - what it exercises: products and skills

   Cover different shapes of [skill-mapping-guide.md § Common Combinations](skill-mapping-guide.md) where the answers allow — one skill on one application, no UI application, several skills across applications — so the pick sets the scope while complexity is still inferred (Step 3). Invent the storyline for the answers: the combinations and [assets/examples/](../assets/examples/) give shapes and depth, not stories. Present the cards as one single-select `AskUserQuestion`, each card in its option's preview; the user merges or amends cards through Other.
3. **An invented scenario names where its input comes from:** a public source, sample files the build writes as data files, or a generator component in the Components table. A described process brings its inputs; an invented one has none until the scenario gives them. The genome names the source in Target Applications (Actors and Systems in a process genome), and the acceptance criteria take their inputs from it.
4. **The pick is the description.** Continue at Step 2 with the chosen, merged or amended card.

## Step 2 — Choose the level

Count the buildable projects the description implies and apply [genome-format-guide.md § Two Levels](genome-format-guide.md). Process-genome signals: "end-to-end", "across departments", "the flow kicks off the robot then the agent", "human approval for days", separate schedules or triggers for different parts, more than one deployable unit named.

## Step 3 — Infer complexity

Never ask ([genome-format-guide.md § Complexity](genome-format-guide.md)). Signals:

| Signal | Complexity |
|---|---|
| One target app, straightforward input-to-output, single sentence or paragraph | simple |
| Multiple systems, field mappings, business rules, conditional logic, explicit "retry" or "exception handling", scheduled or event trigger, "multiple departments" | medium |
| Multi-phase workflow, human approval or escalation, several integrations, orchestration, multiple deployable units | complex |

"Read Excel, fill a web form" stays simple even when described in detail. A human approval step weighs toward complex without deciding the level alone: the level is where most signals land. It forces a process genome when the approval lives outside the automation.

## Step 4 — Extract

From the description, extract: target applications, human actors, workflow steps in order, business rules, error scenarios, input and output data, triggers and schedules, hardcoded values (paths, addresses, thresholds, names), and:

- **Who signs in.** Every persona or account that logs into a target system (administrator, recruiter, integration user, a proxied approver) is one credential asset in Platform Dependencies ([genome-format-guide.md § Platform Dependencies](genome-format-guide.md)).
- **What varies per scenario.** When the description implies data-driven runs (per country, per organisation type, per integration, per worker), separate the fields that change per row from the constants; the row schema is what the Interface of a test component lists ([genome-format-guide.md § Interface](genome-format-guide.md)), the constants go to configuration.
- **Whether the application is reachable at build time.** Note it; execution captures UI targets live when it is and ships placeholders when it is not (an authored genome has no source target catalog).
- **What the unit of work is.** When the description iterates over items (each invoice, each row, each ticket, each file), name the item, its identifying reference, the daily volume, what produces the items and what consumes them as described, where they live, whether several robots or several sources are involved, and which other granularities are viable; when items are handed on again as items of their own (a second stage, on its own schedule or robot, consumes what the first produces) or several independent item streams exist, each is its own flow — an item's children (a mail's attachments, a file's rows) are a level of that item, not a flow; this is the Transactional Shape ([genome-format-guide.md § Transactional Shape](genome-format-guide.md)) — it describes the as-is and lists the split options with their evidence; the split itself is chosen at execution. A run that succeeds or fails as one has none — the stub.

## Step 5 — Suggest platform capabilities

Add these even when the user did not name them:

| User mentions | Add |
|---|---|
| PDFs, scanned documents, forms | Document Understanding activities in `uipath-rpa` step; `uipath-ixp` component when custom extraction model needed |
| Clicking, typing, reading a screen, desktop app | UI automation in `uipath-rpa` |
| REST APIs, connectors, SaaS systems | Integration Service connector activities (`uipath-rpa`) or `uipath-api-workflow` component when no UI involved |
| Many items processed independently, retries, resilience, several robots | Transactional Shape with the As-is, the split options and the evidence ([genome-format-guide.md § Transactional Shape](genome-format-guide.md)); an Orchestrator queue under Platform Dependencies only when the description itself shares items across robots or runs — otherwise the store follows the split chosen at execution, not imposed |
| Coordinating several automations, waiting on events | `uipath-maestro-flow` (short-lived) or `uipath-maestro-bpmn` (long-running, human lanes) coordinator component |
| Judgement, classification, summarisation, free-text decisions | `uipath-agents` component |
| Human review, approval, sign-off | Human-in-the-loop checkpoint in coordinator; actor row in Actors and Systems |
| Screen for end users, dashboard | `uipath-coded-apps` component |
| Several automations or test suites drive the same application's screens | One `uipath-rpa` library component (screens and shared actions, Interface as per-workflow argument tables) plus consumer components; process genome states the library builds and packs first |
| Regression or test scenarios, "per release", "verify that", data-driven cases | One `uipath-rpa` test-case-group component per business area with data variations, all folders of the single test project ([genome-format-guide.md § Two Levels](genome-format-guide.md) rule 1); Test Manager under Platform Dependencies (`uipath-test`), never in Build With |
| Approvals performed as another user, "proxy as", "impersonate", "on behalf of" | Library step that switches user and stops the switch afterwards; one credential asset per persona that can be proxied |

## Step 6 — Ask follow-ups (bounded)

Group every gap into one message per round. State what you already know so the user does not repeat it. Rounds by complexity: simple 0-1, medium 1-2, complex 2-3. A scenario picked from proposals (Step 1a) gets none: the agent invented every detail, so no gap is left that only the user can fill, and the values left open are Configuration Questions. After the last round, generate with defaults and stubs; never loop.

Ask only for gaps that change the build: missing target system, unknown trigger, undefined decision outcome, unspecified failure behaviour for a critical step, unclear ownership of a handoff, which persona signs in for a scenario when several are implied, whether items must be shared across robots or survive a run failure when the description leaves it open (evidence for the Transactional Shape's split options; the split itself is chosen at execution), and whether the UI application is reachable at build time (live capture) or not (placeholders, indicated later). Do not ask for values a Configuration Question can carry as a default.

## Step 7 — Generate

Populate every template section per the format guide's population matrix. Build With rows come from the skill mapping guide, one skill per step. Business rules and error handling attach to the step where they fire. The Transactional Shape classifies those rules and handlers into per-item outcomes, describes the as-is roles, store and coordination, and lists the split options for the unit of work and each alternative unit, with what each requires and changes and the evidence — or carries its stub ([genome-format-guide.md § Transactional Shape](genome-format-guide.md)). Acceptance criteria derive one-to-one from steps, rules, transformations, and handlers.

Process genomes: write the process file first (Components table, Process Map, Handoffs), then each component genome with its `Part of:` line and an Interface matching the Handoffs row.

Interface by component type ([genome-format-guide.md § Interface](genome-format-guide.md)): a library component gets one argument table per public workflow; a test component gets its per-scenario row schema and, separately, its constants; credentials appear as asset names, never values. Deployment records how UI targets will be obtained ("captured at build time against <environment>" or "placeholders until indicated") and that libraries pack before their consumers.

## Step 8 — Write, then offer edits

Write the file named by the slug rule ([genome-format-guide.md § File Naming and Location](genome-format-guide.md)), then check it:

```bash
python3 "<SKILL_DIR>/scripts/check-genome.py" <process|component> "<GENOME_MD>" --profile strict
```

Use `python` on Windows. A process genome takes the checker to every component genome it links. Fix every `FAIL` line and run it again, at most three rounds, then offer edits ([genome-format-guide.md § Write, Then Offer Edits](genome-format-guide.md)), naming what is left. Edits are in-place, never a regeneration, and each is checked the same way before answering:

| Request | Update |
|---|---|
| "Add detail to step X" | Workflow step X; add acceptance criteria if detail is testable |
| "Change complexity" | Complexity section, then section depth per matrix |
| "Add/remove an application" | Target Applications, Workflow, Build With, Acceptance Criteria |
| "Use a different skill for step X" | Build With row and rationale, validated against mapping guide |
| "Split this into components" | Promote to process genome: create process file, move component content into component files, add Handoffs |
| "Scenario X signs in as persona Y" | Platform Dependencies (credential asset for Y), test component's row schema (asset name per row), Configuration Questions |
| "Make it transactional" / "drop the transactional shape" | Transactional Shape (unit of work, As-is, outcomes, split options, evidence) or its stub; Platform Dependencies (the store the As-is names); Configuration Questions (retry counts) |
| "Step X should be a business exception" | Transactional Shape outcomes table; the rule under Business Rules for step X; an acceptance criterion for the recorded reason |
| "One row per transaction instead of one file" (change the unit of work) | Transactional Shape (Unit of work, Alternative units of work, As-is, outcomes, split options); Interface; Handoffs data passed; Platform Dependencies (store); Acceptance Criteria (duplicate and retry cases) |
| "Split the dispatcher into its own component" / "use one queue" / "apply the REFramework" | Not a genome edit: the split, the store and the template are chosen at execution from the Split options ([transactional-execution-guide.md § Split questions](transactional-execution-guide.md)). Edit the genome only when the described process itself changes — a new source, a new item kind, items that must now be shared — and then the As-is, the Evidence and the options |
| Edits to an extracted genome (rename / reorder / remove steps, "drop the Source Map") | [extraction-guide.md](extraction-guide.md) Step 7 |
