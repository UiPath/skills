# Classification Details — uipath-api-workflow

**Classification: Strong**

---

## What the Skill Teaches

Build, validate, run, package, publish, and diagnose UiPath API Workflows (JSON files conforming to the CNCF Serverless Workflow DSL 1.0.0 with UiPath activity-type extensions).

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | Workflow file authoring (activity types, nesting structure, key uniqueness) | No | Requires judgment on which activities to use, variable naming, control flow design |
| 2 | **Connector activity discovery (registry resolve + stub)** | **Yes — EXTRACT** | Fixed 3-step flow: resolve keyword → stub activity → wire into workflow |
| 3 | **Validate→fix→re-validate loop** | **Yes — VALIDATE/CHECK** | `uip api-workflow validate` is the autonomous closure step; loop until `Data.Status: "Valid"` |
| 4 | **Project scaffolding and build/deploy lifecycle** | **Yes — TRANSFORM-PIPELINE** | `init` → validate → run (with consent) → `solution pack` → `solution publish`; fixed sequenced steps |
| 5 | **Error triage order** | **Yes — DETECT** | Fixed priority ladder: Structure > Expression > Activity Config > Logic |
| 6 | Run mode selection (--no-auth vs with-auth) | No | Requires judgment on workflow content and user consent; not purely rule-driven |
| 7 | Debugging published workflow (cloud logs, traces) | No | Requires cross-skill judgment (delegates to uipath-platform, uipath-troubleshoot) |

---

## Codifiable Procedures (not yet scripted)

### 1. Connector Activity Discovery Flow — EXTRACT

**Source:** `skills/uipath-api-workflow/SKILL.md` §Critical Rules → Rule 16

**What it does:** When a connector or HTTP activity is needed, the skill prescribes a fixed 3-step flow: (1) run `uip api-workflow registry resolve "<keywords>"` to find a matching curated activity, (2) if a miss, fall back to `uip is connectors list --filter "<product>"` then `uip is activities list <connector-key>` to locate the connector key, (3) run `uip api-workflow registry stub <activityId>` to generate the correctly-shaped JSON fragment (computing `metadata.configuration`, `kind`, endpoint, `SlotKey`, `ExportBucketKey`). The stub output is used verbatim. Line 81: "The stub computes `metadata.configuration`, the kind (`UiPath.Http` vs `UiPath.IntSvc`), the endpoint (with hub prefix), `SlotKey`, and `ExportBucketKey` (which can differ — HTTP slot `HttpRequest_1` vs bucket `http_request_1`). Use all of them verbatim; NEVER invent a `uiPathActivityTypeId`, hand-author `metadata.configuration`, or reconstruct a key from `objectName`."

**Why it's mechanical:** The fallback sequence (resolve → connector list → activities list → stub) and the rule against hand-authoring any field are explicit with no decision points that require judgment.

**Turn savings:** The agent currently runs each discovery command separately, interprets results, and manually assembles connector JSON across several turns; a script that accepts a keyword or connector key and emits a ready-to-paste stub collapses this to one call.

---

### 2. Validate→Fix→Re-validate Loop — VALIDATE/CHECK

**Source:** `skills/uipath-api-workflow/SKILL.md` §Critical Rules → Rules 20, 3

**What it does:** After every authoring or edit cycle, the skill mandates running `uip api-workflow validate <Workflow.json> --output json` and looping until `Data.Status: "Valid"` (exit 0). On failure (exit 1), the agent reads `Instructions`, locates the offending activity by JSON path, fixes `Workflow.json`, and re-validates. The loop runs autonomously with no user interaction until validation passes. Line 112: "`uip api-workflow validate <Workflow.json>` is the autonomous closure step for every authoring or edit cycle. Run it as the LAST command before asking the user anything about runtime."

**Why it's mechanical:** The loop termination condition (`Data.Status: "Valid"`), the error-reading strategy (focus on semantic-tail errors, not AJV schema fanout), and the autonomous character of the loop are all fixed in the skill.

**Turn savings:** The agent currently runs validate, reads the output, and loops across multiple turns; a validate-and-fix loop script compresses the entire validate-until-green cycle into one invocation.

---

### 3. Project Scaffolding and Deployment Lifecycle — TRANSFORM-PIPELINE

**Source:** `skills/uipath-api-workflow/SKILL.md` §Quick Start (CREATE from scratch) and Rule 19

**What it does:** The skill prescribes a fixed ordered sequence: `uip solution init` (if no solution) → `cd ./MySolution && uip api-workflow init <name>` → edit `Workflow.json` → `uip api-workflow validate` → (user consent) `uip api-workflow run` → `uip solution pack` → `uip solution publish`. Each step has explicit flags and success conditions. Line 97: "Scaffold with `uip api-workflow init`; publish goes through the solution packager. Create every API workflow project with `uip api-workflow init <name>` (rule 19a) — never hand-assemble the project files."

**Why it's mechanical:** The command sequence, the required flags (`--output json`, correct working directory for `init`, `--skip-solution-registration` only for explicit opt-out), and the prohibition on hand-assembling project files are all fixed rules.

**Turn savings:** The agent currently executes each lifecycle step as a separate turn and must remember flags and sequencing; a lifecycle orchestration script compresses the full scaffold-to-publish pipeline into a parameterized single call.

---

## Justification for Classification

**Strong** — not Partial, not None.

**Why not Partial:** Four of seven teaching areas are codifiable: connector discovery, the validate loop, the deployment lifecycle pipeline, and the error triage order. These three codifiable areas — particularly the validate loop and the deployment lifecycle — represent the majority of the prescriptive, action-oriented content in the skill. The non-codifiable areas (authoring choices, run mode selection, post-publish debugging) are secondary to the mechanical scaffolding and validation pipeline.

**Why not None:** The validate→fix→re-validate loop (Rule 20) and the project scaffolding lifecycle (Rule 19/19a) are explicit, deterministic, multi-step sequences with fixed commands, flags, and termination conditions.

**Evidence locations:**
- Connector activity discovery: `SKILL.md` §Critical Rules → Rule 16 (lines 81–88)
- Validate→fix→re-validate loop: `SKILL.md` §Critical Rules → Rule 20 (lines 112–120)
- Project scaffolding + deployment lifecycle: `SKILL.md` §Quick Start (CREATE from scratch) (lines 244–271) and Rule 19/19a (lines 97–109)
- Error triage order: `SKILL.md` §Core Principles → "Fix errors by category" (line 44)
