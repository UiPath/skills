# Authoring Guide — genome from an idea, a PDD, a TO-BE or an SDD

The planner's **Author** lane writes a genome — the coding-agent spec `uipath-genome` builds from — when no source automation exists. Input: a free-form description, an SOP or transcript, a PDD, a change proposal's TO-BE, an agreed SDD, or a goal the planner proposes scenarios for. User describes or picks; the planner infers, selects the products, fills UiPath specifics, writes. Content rules and templates: [genome-format-guide.md](genome-format-guide.md).

The planner never builds: the written genome goes to `uipath-genome` (Step 9).

## Step 1 — Receive the input

Accept anything from one sentence to several pages. Do not ask the user to elaborate before attempting extraction.

- **One sentence:** infer what you can, then ask one focused round of follow-ups for the largest gaps.
- **Several paragraphs:** extract methodically; follow-ups often unnecessary.
- **Contradictions:** name the specific conflict in the follow-up round. Do not guess which requirement wins.
- **Existing documents (SOP, PDD, process map, transcript, TO-BE):** treat the document as the description. A PDD is read with the [pdd-analysis-guide.md](pdd-analysis-guide.md) sections `SKILL.md` § Read Plans names; it is input only — the planner never writes a PDD.
- **An agreed SDD** (`## Planner Handoff` with `Status: ready`): the SDD is the design — Step 1b.
- **A goal, not a process** (a self-paced workshop, a demo, trying a product or an application): propose scenarios first (Step 1a); the picked scenario is the description.

## Step 1a — Propose scenarios for a goal

1. **Ask one round:** one `AskUserQuestion` batch of two multi-select questions, each skipped when the request already answers it.
   - **Products to exercise:** RPA, agents, orchestration (Maestro Flow, BPMN, Case), document extraction, human review and apps.
   - **Systems within reach, grouped by the setup they need:** none (local files, Excel, public APIs); a tenant connection (mail, chat, a SaaS system); an application installed or hosted for the user (SAP, an internal web application).

   Group the systems by setup because every connection, account or installation is one more thing that can fail before the scenario runs; the grouping lets the user trade reach against setup. When the delivery model is known, run the [Constraint Gate](product-selection-guide.md#constraint-gate) on the products picked; a blocked product is not offered.
2. **Propose up to three scenarios** built for the answers, using only the systems within reach plus sources that need no setup. Each is a card:
   - storyline, one sentence: what arrives, what is decided or done, where the result lands
   - Components table, `# | Component | Type | Skill | Summary`, skills per Step 5 and [skill-mapping-guide.md](skill-mapping-guide.md); one row makes a component genome
   - applications and the setup each needs (connection, account, installation)
   - input source (item 3)
   - what it exercises: products and skills

   Cover different shapes of [skill-mapping-guide.md § Common Combinations](skill-mapping-guide.md) where the answers allow — one skill on one application, no UI application, several skills across applications — so the pick sets the scope while complexity is still inferred (Step 3). Invent the storyline for the answers: the combinations and [assets/examples/](../assets/examples/) give shapes and depth, not stories. Present the cards as one single-select `AskUserQuestion`, each card in its option's preview; the user merges or amends cards through Other.
3. **An invented scenario names where its input comes from:** a public source, sample files the build writes as data files, or a generator component in the Components table. A described process brings its inputs; an invented one has none until the scenario gives them. The genome names the source in Target Applications (Actors and Systems in a process genome), and the acceptance criteria take their inputs from it.
4. **The pick is the description.** Continue at Step 2 with the chosen, merged or amended card. A prototype or workshop has no sign-off, so it gets no SDD.

## Step 1b — Author from an agreed SDD

The SDD decided the architecture; the genome restates it as the coding-agent spec and adds what only the genome holds (replication-grade substeps, composite UI contracts, the configuration questions, numbered acceptance criteria).

1. **Read the SDD whole**, with its Planner Handoff, and for a solution SDD every per-project SDD it lists.
2. **The SDD's products and projects are the genome's.** Its project list sets the level (Step 2) and the Build With / Components rows; Steps 3–5 never re-select a product the SDD placed. Its delivery model holds for every row.
3. **The SDD's decisions are recorded, not reopened.** The split and queue design, the implementation mode, the package pins and, for a refactor, the refactor answers go into the sections that hold them (Transactional Shape evidence, Deployment, Configuration Questions defaults), so `uipath-genome` reads them as answered.
4. **Gaps carry over.** Every `[SME REVIEW]` or `[DEFAULT]` item of the SDD that touches a section is written there with `*[Inferred]*` and the item's wording; Step 6 asks nothing the SDD already left to an SME.
5. **The SDD is never edited by this lane.** A contradiction between the SDD and what the genome needs is named when edits are offered (Step 8).
6. **Name the genome after the SDD** (`<PROCESS_NAME_KEBAB>-genome.md` beside the SDD) and record it in the SDD's Planner Handoff as `| **Genome** | <path> |` after `Tasks file`.

Continue at Step 2.

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
- **What the unit of work is.** When the description iterates over items (each invoice, each row, each ticket, each file), name the item, its identifying reference, the daily volume, what produces the items and what consumes them as described, where they live, whether several robots or several sources are involved, and which other granularities are viable; when items are handed on again as items of their own (a second stage, on its own schedule or robot, consumes what the first produces) or several independent item streams exist, each is its own flow — an item's children (a mail's attachments, a file's rows) are a level of that item, not a flow; this is the Transactional Shape ([transactional-shape-guide.md](transactional-shape-guide.md)) — it describes the as-is and lists the split options with their evidence; the split itself is chosen at execution, or recorded by the SDD (Step 1b). A run that succeeds or fails as one has none — the stub.

## Step 5 — Select the products

Every authored genome runs the planner's product selection, so a genome never names a product the customer's platform cannot run. With an SDD (Step 1b) this step only checks the SDD's rows; without one it places them:

1. **Constraint Gate** — [product-selection-guide.md § Constraint Gate](product-selection-guide.md#constraint-gate), with the delivery model from [platform-availability-guide.md](platform-availability-guide.md). Ask the delivery model only when the request, the PDD or the SDD does not state it; a prototype on an unknown tenant takes Automation Cloud as its default, written as `*[Inferred]*` in Deployment.
2. **Per-step placement** — [product-selection-guide.md § Per-task component placement](product-selection-guide.md#per-task-component-placement-the-to-be-per-step); orchestration through [§ Maestro disambiguation](product-selection-guide.md#maestro-disambiguation--bpmn-vs-flow-vs-case).
3. **Integration Service reuse** — [product-selection-guide.md § Integration Service](product-selection-guide.md#integration-service) before any UI step on a SaaS system.
4. **Tenant libraries** — [tenant-library-search-guide.md](tenant-library-search-guide.md) when a step repeats behaviour a deployed library may already hold and the tenant is reachable.

Then add these capabilities even when the user did not name them:

| User mentions | Add |
|---|---|
| PDFs, scanned documents, forms | Document Understanding activities in `uipath-rpa` step; `uipath-ixp` component when custom extraction model needed |
| Clicking, typing, reading a screen, desktop app | UI automation in `uipath-rpa` |
| REST APIs, connectors, SaaS systems | Integration Service connector activities (`uipath-rpa`) or `uipath-api-workflow` component when no UI involved |
| Many items processed independently, retries, resilience, several robots | Transactional Shape with the As-is, the split options and the evidence ([transactional-shape-guide.md](transactional-shape-guide.md)); an Orchestrator queue under Platform Dependencies only when the description itself shares items across robots or runs — otherwise the store follows the split chosen at execution, not imposed |
| Coordinating several automations, waiting on events | `uipath-maestro-flow` (short-lived) or `uipath-maestro-bpmn` (long-running, human lanes) coordinator component |
| Judgement, classification, summarisation, free-text decisions | `uipath-agents` component |
| Human review, approval, sign-off | Human-in-the-loop checkpoint in coordinator; actor row in Actors and Systems |
| Screen for end users, dashboard | `uipath-coded-apps` component |
| Several automations or test suites drive the same application's screens | One `uipath-rpa` library component (screens and shared actions, Interface as per-workflow argument tables) plus consumer components; process genome states the library builds and packs first |
| Regression or test scenarios, "per release", "verify that", data-driven cases | One `uipath-rpa` test-case-group component per business area with data variations, all folders of the single test project ([genome-format-guide.md § Two Levels](genome-format-guide.md) rule 1); Test Manager under Platform Dependencies (`uipath-test`), never in Build With |
| Approvals performed as another user, "proxy as", "impersonate", "on behalf of" | Library step that switches user and stops the switch afterwards; one credential asset per persona that can be proxied |

## Step 6 — Ask follow-ups (bounded)

Group every gap into one message per round. State what you already know so the user does not repeat it. Rounds by complexity: simple 0-1, medium 1-2, complex 2-3. A scenario picked from proposals (Step 1a) gets none: the agent invented every detail, so no gap is left that only the user can fill, and the values left open are Configuration Questions. An SDD (Step 1b) gets none for what its SME items already carry. After the last round, generate with defaults and stubs; never loop.

Ask only for gaps that change the build: missing target system, unknown trigger, undefined decision outcome, unspecified failure behaviour for a critical step, unclear ownership of a handoff, which persona signs in for a scenario when several are implied, whether items must be shared across robots or survive a run failure when the description leaves it open (evidence for the Transactional Shape's split options; the split itself is chosen at execution), and whether the UI application is reachable at build time (live capture) or not (placeholders, indicated later). Do not ask for values a Configuration Question can carry as a default.

## Step 7 — Generate

Populate every template section per the format guide's population matrix. Build With rows come from Step 5 and the skill mapping guide, one skill per step. Business rules and error handling attach to the step where they fire. The Transactional Shape classifies those rules and handlers into per-item outcomes, describes the as-is roles, store and coordination, and lists the split options for the unit of work and each alternative unit, with what each requires and changes and the evidence — or carries its stub ([transactional-shape-guide.md](transactional-shape-guide.md)). Acceptance criteria derive one-to-one from steps, rules, transformations, and handlers.

Process genomes: write the process file first (Components table, Process Map, Handoffs), then each component genome with its `Part of:` line and an Interface matching the Handoffs row.

Interface by component type ([genome-format-guide.md § Interface](genome-format-guide.md)): a library component gets one argument table per public workflow; a test component gets its per-scenario row schema and, separately, its constants; credentials appear as asset names, never values. Deployment records how UI targets will be obtained ("captured at build time against <environment>" or "placeholders until indicated") and that libraries pack before their consumers.

## Step 8 — Write, then offer edits

Write the file named by the slug rule ([genome-format-guide.md § File Naming and Location](genome-format-guide.md)), then check it:

```bash
python3 "<SKILL_DIR>/scripts/check-genome.py" <process|component> "<GENOME_MD>" --profile strict
```

Use `python` on Windows. A process genome takes the checker to every component genome it links. Fix every `FAIL` line and run it again, at most three rounds, then offer edits ([genome-format-guide.md § Write, Then Offer Edits](genome-format-guide.md)), naming what is left. Edits: [editing-guide.md](editing-guide.md).

## Step 9 — Hand the genome to the build

When the request asks for a build ("build", "implement", "create the automation"), hand the written genome path to `uipath-genome` (Execute) on the next turn, once the user's edits are in; an unattended run hands it over straight away. The planner never builds and never writes a workflow file. When `uipath-genome` is not installed, stop after Step 8 and say that the build needs `uipath-genome`.
