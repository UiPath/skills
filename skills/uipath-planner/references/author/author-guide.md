# Authoring Guide — genome from an idea, a PDD, a TO-BE or an SDD

The `author` verb writes a genome — the coding-agent spec `uipath-genome` builds from — when no source automation exists. Input: a free-form description, an SOP or transcript, a PDD, a change proposal's TO-BE, an agreed SDD, or a goal the planner proposes scenarios for. User describes or picks; the planner infers, selects the products, fills UiPath specifics, writes. Content rules and templates: [genome-format-guide.md](../shared/genome-format-guide.md).

`author` never builds: the written genome goes to `uipath-genome` (Step 9). Inside `design`, `author` runs Step 1b on the `ready` SDD: [sdd-writing-guide.md](../design/sdd-writing-guide.md) § Step 3.

## Verb Rules

The writing rules of [genome-format-guide.md § Writing Rules](../shared/genome-format-guide.md) and the Critical Rules in [SKILL.md](../../SKILL.md) apply; `author` adds:

1. **Every authored genome rests on the planner's product selection.** Without an SDD, Step 5 runs it: Constraint Gate, platform availability, Maestro disambiguation, Integration Service reuse and tenant library search. An agreed SDD has already made it ([genome-from-sdd-guide.md](genome-from-sdd-guide.md)).
2. **Follow-ups are bounded** (Step 6): one round for the largest gaps, then write.

## Read Plan

| Phase | Condition | Read |
|---|---|---|
| start | — | this guide; [genome-format-guide.md](../shared/genome-format-guide.md) every section before § Process Genome Sections |
| start | the input is not an agreed SDD | [skill-mapping-guide.md](../shared/skill-mapping-guide.md) whole |
| the input is received | the input is an agreed SDD (Step 1b) | [genome-from-sdd-guide.md](genome-from-sdd-guide.md) whole; its § Read Plan names the rest of this path's reads |
| the input is received | the input is a goal, not a process (Step 1a) | [scenario-proposal-guide.md](scenario-proposal-guide.md) whole; its § Read Plan names the rest of this path's reads |
| the input is received | the input is a PDD (not an agreed SDD — inside `design` the input is the SDD) | [pdd-analysis-guide.md](../shared/pdd-analysis-guide.md) by section — every section except § Accepted process-knowledge sources and § Gap Detection Checklist; the genome's gaps follow genome-format-guide.md |
| the level is chosen (Step 2) | — | the template of that level ([component](../../assets/templates/component-genome-template.md), [process](../../assets/templates/process-genome-template.md)) |
| the level is chosen (Step 2) | a process genome | [genome-format-guide.md](../shared/genome-format-guide.md) § Process Genome Sections |
| products are selected (Step 5) | no SDD | [product-selection-guide.md](../shared/product-selection-guide.md) § Constraint Gate and [component-placement-guide.md](../shared/component-placement-guide.md) § Per-task component placement, opened by name (no heading list); [platform-availability-guide.md](../shared/platform-availability-guide.md) (both not re-read when scenario-proposal-guide.md already opened them); § Maestro disambiguation — BPMN vs Flow vs Case only when the genome has two or more components or a coordinator; component-placement-guide.md § Integration Service only when a step acts on a SaaS system |
| products are selected (Step 5) | no SDD, a step repeats behaviour a deployed library may already hold, and the tenant is reachable | [tenant-library-search-guide.md](../shared/tenant-library-search-guide.md) |
| the unit of work is assessed | no SDD, and the description iterates over items | [transactional-shape-guide.md](../shared/transactional-shape-guide.md) |
| the genome is written (Step 8) | — | [prebuild-guide.md](../shared/prebuild-guide.md) |

Each phase's reads go out in at most three turns: turn 1 every file read whole, every section this plan names, and the heading list of every other file read by section; turn 2 the sections chosen; turn 3 only what turn 2 routed to.

## Step 1 — Receive the input

Accept anything from one sentence to several pages. Do not ask the user to elaborate before attempting extraction.

- **One sentence:** infer what you can, then ask one focused round of follow-ups for the largest gaps.
- **Several paragraphs:** extract methodically; follow-ups often unnecessary.
- **Contradictions:** name the specific conflict in the follow-up round. Do not guess which requirement wins.
- **Existing documents (SOP, PDD, process map, transcript, TO-BE):** treat the document as the description. A PDD is read with the [pdd-analysis-guide.md](../shared/pdd-analysis-guide.md) sections § Read Plan names; it is input only — the planner never writes a PDD.
- **An agreed SDD** (`## Planner Handoff` with `Status: ready`): the SDD is the design — Step 1b.
- **A goal, not a process** (a self-paced workshop, a demo, trying a product or an application): propose scenarios first (Step 1a); the picked scenario is the description.

## Step 1a — Propose scenarios for a goal

Run [scenario-proposal-guide.md](scenario-proposal-guide.md); the picked scenario is the description, and authoring continues at Step 2.

## Step 1b — Author from an agreed SDD

Run [genome-from-sdd-guide.md](genome-from-sdd-guide.md); it continues at Step 2.

## Step 2 — Choose the level

Count the buildable projects the description implies and apply [genome-format-guide.md § Two Levels](../shared/genome-format-guide.md). From an SDD, the count is [genome-from-sdd-guide.md](genome-from-sdd-guide.md) item 3's. Process-genome signals for a description: "end-to-end", "across departments", "the flow kicks off the robot then the agent", "human approval for days", separate schedules or triggers for different parts, more than one deployable unit named.

## Step 3 — Infer complexity

Never ask ([genome-format-guide.md § Complexity](../shared/genome-format-guide.md)). Signals:

| Signal | Complexity |
|---|---|
| One target app, straightforward input-to-output, single sentence or paragraph | simple |
| Multiple systems, field mappings, business rules, conditional logic, explicit "retry" or "exception handling", scheduled or event trigger, "multiple departments" | medium |
| Multi-phase workflow, human approval or escalation, several integrations, orchestration, multiple deployable units | complex |

"Read Excel, fill a web form" stays simple even when described in detail. A human approval step weighs toward complex without deciding the level alone: the level is where most signals land. It forces a process genome when the approval lives outside the automation.

## Step 4 — Extract

From the description, extract: target applications, human actors, workflow steps in order, business rules, error scenarios, input and output data, triggers and schedules, hardcoded values (paths, addresses, thresholds, names), and:

- **Who signs in.** Every persona or account that logs into a target system (administrator, recruiter, integration user, a proxied approver) is one credential asset in Platform Dependencies ([genome-format-guide.md § Platform Dependencies](../shared/genome-format-guide.md)).
- **What varies per scenario.** When the description implies data-driven runs (per country, per organisation type, per integration, per worker), separate the fields that change per row from the constants; the row schema is what the Interface of a test component lists ([genome-format-guide.md § Interface](../shared/genome-format-guide.md)), the constants go to configuration.
- **What the unit of work is.** When the description iterates over items (each invoice, each row, each ticket, each file), name the item, its identifying reference, the daily volume, what produces the items and what consumes them as described, where they live, whether several robots or several sources are involved, and which other granularities are viable; when items are handed on again as items of their own (a second stage, on its own schedule or robot, consumes what the first produces) or several independent item streams exist, each is its own flow — an item's children (a mail's attachments, a file's rows) are a level of that item, not a flow; this is the Transactional Shape ([transactional-shape-guide.md](../shared/transactional-shape-guide.md)) — it describes the as-is and lists the split options with their evidence; the split itself is chosen at build, or recorded by the SDD ([genome-from-sdd-guide.md](genome-from-sdd-guide.md)). A run that succeeds or fails as one has none — the stub.

## Step 5 — Select the products

Without an SDD, this step runs the planner's product selection, so a genome never names a product the customer's platform cannot run. With an SDD, skip it ([genome-from-sdd-guide.md](genome-from-sdd-guide.md) item 3). Without one, place them:

1. **Constraint Gate** — [product-selection-guide.md § Constraint Gate](../shared/product-selection-guide.md#constraint-gate), with the delivery model from [platform-availability-guide.md](../shared/platform-availability-guide.md). Ask the delivery model only when the request, the PDD or the SDD does not state it; a prototype on an unknown tenant takes Automation Cloud as its default, written as `*[Inferred]*` in Deployment.
2. **Per-step placement** — [component-placement-guide.md § Per-task component placement](../shared/component-placement-guide.md#per-task-component-placement-the-to-be-per-step); orchestration through [§ Maestro disambiguation](../shared/product-selection-guide.md#maestro-disambiguation--bpmn-vs-flow-vs-case).
3. **Integration Service reuse** — [component-placement-guide.md § Integration Service](../shared/component-placement-guide.md#integration-service) before any UI step on a SaaS system.
4. **Tenant libraries** — [tenant-library-search-guide.md](../shared/tenant-library-search-guide.md) when a step repeats behaviour a deployed library may already hold and the tenant is reachable.

Then add these capabilities even when the user did not name them:

| User mentions | Add |
|---|---|
| PDFs, scanned documents, forms | Document Understanding activities in `uipath-rpa` step; `uipath-ixp` component when custom extraction model needed |
| Clicking, typing, reading a screen, desktop app | UI automation in `uipath-rpa` |
| REST APIs, connectors, SaaS systems | Integration Service connector activities (`uipath-rpa`) or `uipath-api-workflow` component when no UI involved |
| Many items processed independently, retries, resilience, several robots | Transactional Shape with the As-is, the split options and the evidence ([transactional-shape-guide.md](../shared/transactional-shape-guide.md)); an Orchestrator queue under Platform Dependencies only when the description itself shares items across robots or runs — otherwise the store follows the split chosen at execution, not imposed |
| Coordinating several automations, waiting on events | `uipath-maestro-flow` (short-lived) or `uipath-maestro-bpmn` (long-running, human lanes) coordinator component |
| Judgement, classification, summarisation, free-text decisions | `uipath-agents` component |
| Human review, approval, sign-off | Human-in-the-loop checkpoint in coordinator; actor row in Actors and Systems |
| Screen for end users, dashboard | `uipath-coded-apps` component |
| Several automations or test suites drive the same application's screens | One `uipath-rpa` library component (screens and shared actions, Interface as per-workflow argument tables) plus consumer components; process genome states the library builds and packs first |
| Regression or test scenarios, "per release", "verify that", data-driven cases | One `uipath-rpa` test-case-group component per business area with data variations, all folders of the single test project ([genome-format-guide.md § Two Levels](../shared/genome-format-guide.md) rule 1); Test Manager under Platform Dependencies (`uipath-test`), never in Build With |
| Approvals performed as another user, "proxy as", "impersonate", "on behalf of" | Library step that switches user and stops the switch afterwards; one credential asset per persona that can be proxied |

## Step 6 — Ask follow-ups (bounded)

Group every gap into one message per round. State what you already know so the user does not repeat it. Rounds by complexity: simple 0-1, medium 1-2, complex 2-3. A scenario picked from proposals (Step 1a) gets none: the agent invented every detail, so no gap is left that only the user can fill, and the values left open are Configuration Questions. An SDD's rounds: [genome-from-sdd-guide.md](genome-from-sdd-guide.md) items 2 and 5. After the last round, generate with defaults and stubs; never loop.

Ask only for gaps that change the build: missing target system, unknown trigger, undefined decision outcome, unspecified failure behaviour for a critical step, unclear ownership of a handoff, which persona signs in for a scenario when several are implied, whether items must be shared across robots or survive a run failure when the description leaves it open (evidence for the Transactional Shape's split options; the split itself is chosen at build). Do not ask for values a Configuration Question can carry as a default.

## Step 7 — Generate

Populate every template section per the format guide's population matrix. Build With rows come from Step 5 and the skill mapping guide, one skill per step. Business rules and error handling attach to the step where they fire. The Transactional Shape classifies those rules and handlers into per-item outcomes, describes the as-is roles, store and coordination, and lists the split options for the unit of work and each alternative unit, with what each requires and changes and the evidence — or carries its stub ([transactional-shape-guide.md](../shared/transactional-shape-guide.md)). Acceptance criteria derive one-to-one from steps, rules, transformations, and handlers.

Process genomes: write the process file first (Components table, Process Map, Handoffs), then each component genome with its `Part of:` line and an Interface matching the Handoffs row.

Interface by component type ([genome-format-guide.md § Interface](../shared/genome-format-guide.md)): a library component gets one argument table per public workflow; a test component gets its per-scenario row schema and, separately, its constants; credentials appear as asset names, never values. Deployment records the environment the UI targets come from ("UI targets: <environment>") and that libraries pack before their consumers; a component genome, which has no Deployment, records the environment in its Target Applications row's Notes cell, so the build can offer it.

## Step 8 — Write, then offer edits

Write the file named by the slug rule ([genome-format-guide.md § File Naming and Location](../shared/genome-format-guide.md)), then review it, and every component genome a process genome links, against [genome-format-guide.md § Writing Rules](../shared/genome-format-guide.md) and fix what breaks a rule. Then run the strict check on the genome ([SKILL.md](../../SKILL.md) § Check) — `node "<SKILL_DIR>/scripts/check-genome.mjs" <component|process> "<GENOME_MD>" --profile strict` — fix every `FAIL` and run it again, at most three rounds. Then write the pre-build file ([prebuild-guide.md](../shared/prebuild-guide.md)) and offer edits ([genome-format-guide.md § Write, Then Offer Edits](../shared/genome-format-guide.md)), naming the file, how many items each of its sections holds and every `FAIL` left after the third round. From an SDD whose `Execution autonomy` is `autonomous`, the edits are offered in the closing summary without waiting for them ([genome-from-sdd-guide.md](genome-from-sdd-guide.md) item 2). Edits: [edit-guide.md](../edit/edit-guide.md).

## Step 9 — Hand the genome to the build

When the request asks for a build ("build", "implement", "create the automation"), invoke `uipath-genome` with `build "<GENOME_MD>"` and the user's build request quoted verbatim on the next turn, once the user's edits are in; an unattended run hands it over straight away. `author` never writes a workflow file. When `uipath-genome` is not installed, stop after Step 8 and say that the build needs it. A genome written from an SDD inside `design` follows [sdd-writing-guide.md](../design/sdd-writing-guide.md) § Step 3 item 4 instead.
