# Classification Details — uipath-test

**Classification: Strong**

---

## What the Skill Teaches

How to manage the full UiPath Test Manager lifecycle via `uip tm` — from CLI surface detection and project/test-case/test-set/execution CRUD through Playwright suite packaging, ingestion, and execution, and shareable report generation.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | **CLI surface probe (pre- vs post-rename verb detection)** | **Yes — VALIDATE/CHECK** | Fixed probe + binary result + pre-rename fallback translation table |
| 2 | **Test Manager CRUD operations (projects, cases, sets, executions)** | **Yes — TRANSFORM-PIPELINE** | Fully specified command sequences for each resource lifecycle |
| 3 | **Playwright first-mile pipeline (pack→upload→ingest→run)** | **Yes — TRANSFORM-PIPELINE** | Documented fixed sequence in playwright-first-mile-guide.md |
| 4 | **Pre-rename CLI fallback table** | **Yes — LOOKUP/REFERENCE-TABLE** | Fixed 8-row mapping from post-rename to pre-rename verbs |
| 5 | **Execution status wait and result extraction** | **Yes — VALIDATE/CHECK** | `uip tm wait` + exit-code branching (0=done, 2=timeout, 1=fault) |
| 6 | **Test result report generation** | **Yes — FORMAT-CONVERT** | Fixed report structure from `uip tm report get` + execution stats |
| 7 | Deciding what test cases to write or what assertions to add | No | QA design judgment |
| 8 | Go/no-go release decision from execution results | No | Release management judgment |

---

## Codifiable Procedures (not yet scripted)

### 1. CLI Surface Probe — VALIDATE/CHECK

**Source:** `skills/uipath-test/SKILL.md` §Critical Rules (Rule 2)

**What it does:** Runs `uip tm testcases --help --output json`, checks the exit code and result, and classifies the CLI surface as post-rename (proceed with documented commands) or pre-rename (translate via the Pre-rename fallbacks table before each call). Line 233: "Probe the CLI surface once per session, before the first `uip tm` command. Run `uip tm testcases --help --output json` (any flags accepted). Result `Success` → post-rename CLI; use the command tables above as-is. `unknown command` / non-zero exit → pre-rename CLI; translate via the [Pre-rename fallbacks](#pre-rename-fallbacks) table before each call."

**Why it's mechanical:** Two possible outcomes from one probe; the fallback mapping is a fixed 8-row table with no judgment required.

**Turn savings:** Without a script the agent probes and applies the verb translation manually before each session; a probe-and-translate script returns a surface flag and ready-translated verb map in one call.

---

### 2. Test Manager CRUD Lifecycle — TRANSFORM-PIPELINE

**Source:** `skills/uipath-test/SKILL.md` §Commands (Project, Test Cases, Test Sets, Executions)

**What it does:** Executes resource lifecycle sequences: create project → create test case → link automation → create test set → add test cases → run test set → list execution logs. Each command produces an ID consumed by downstream commands. The Quick Start section shows the canonical end-to-end sequence. Line 276: `"# Get project\n  uip tm project list --filter <PROJECT_NAME_OR_KEY> --output json"`

**Why it's mechanical:** The command sequence is enumerated in the skill's command tables; each step's required flags and ID-propagation rules are specified explicitly.

**Turn savings:** Without a script the agent issues each command in a separate turn and manually extracts IDs; a pipeline script accepts a project name and test set name, resolves IDs internally, and returns the execution ID in one turn.

---

### 3. Playwright First-Mile Pipeline — TRANSFORM-PIPELINE

**Source:** `skills/uipath-test/SKILL.md` §Pack Commands (Playwright), §Navigate to a workflow

**What it does:** Executes the four-step pipeline: (1) `uip tm pack --type playwright` to produce a `.nupkg`, (2) `uip or packages upload <nupkg>` to upload to Orchestrator, (3) wait for ingestion to auto-create test cases with `PW_Tag_*` / `PW_Suite_*` labels, (4) `uip tm testsets run` to execute. Line 167: "Pack a Playwright suite into a `.nupkg` external test package. Requires a lockfile and `@playwright/test` in the project."

**Why it's mechanical:** The four steps are ordered and specified; the ingestion step is automatic (no action required beyond upload); label filtering for adding test cases to a set is a fixed `--labels` flag.

**Turn savings:** Without a script the agent runs each of the four steps separately across multiple turns and manually tracks the package name and execution ID; a first-mile script accepts a project path and Test Manager project key and returns an execution ID.

---

### 4. Pre-Rename CLI Fallback Lookup — LOOKUP/REFERENCE-TABLE

**Source:** `skills/uipath-test/SKILL.md` §Pre-rename fallbacks

**What it does:** Maps a post-rename `uip tm` verb to its pre-rename equivalent for CLIs that predate the closed-verb-set renames. The table covers 8 verb translations including `testcases run` → `testcase execute`, `testsets run` → `testset execute`, and `executions testcaselogs list` → `execution list-testcaselogs`. Line 247: "If the probe in Rule #2 shows singular subjects, the CLI predates the closed-verb-set renames. Translate before running:"

**Why it's mechanical:** The mapping is a fixed 8-row table; lookup is a direct key→value resolution.

**Turn savings:** Without a script the agent reads the table in context and manually substitutes verbs; a translate script accepts a post-rename verb and returns the pre-rename form in one call.

---

### 5. Execution Wait and Status Check — VALIDATE/CHECK

**Source:** `skills/uipath-test/SKILL.md` §Wait Commands, §Critical Rules (Rule 11)

**What it does:** Runs `uip tm wait --execution-id <id> --timeout <seconds>`, inspects the exit code, and classifies the result: exit 0 = execution reached terminal state (pass to report step), exit 2 = bounded timeout (report non-finish and continue), exit 1 = real fault (stop and report). Line 241: "`uip tm wait` exiting with code 2 and `\"Timed out after <N>s waiting for execution '<EXECUTION_ID>'. Last status: <status>.\"` — the bounded `--timeout` working as designed; report the non-finish and carry on with the remaining steps."

**Why it's mechanical:** The branch logic is fully enumerated by exit code; no interpretation of execution content is needed.

**Turn savings:** Without a script the agent polls status and branches on result across 2–4 turns; a wait-and-classify script returns a structured outcome enum in one call.

---

### 6. Test Result Report Generation — FORMAT-CONVERT

**Source:** `skills/uipath-test/SKILL.md` §Report Commands, §Navigate to a workflow

**What it does:** Runs `uip tm report get --execution-id <id> (--project-key <key> | --test-set-key <key>) --output json`, optionally adds `uip tm executions get-stats` for aggregate metrics, and formats the result into a persona-tailored report (QA engineer / developer / release manager view) following the structure in `references/test-result-report-guide.md`. Line 148: "Get a summary report for a completed test execution. One of `--project-key`/`--test-set-key` is required to identify the project"

**Why it's mechanical:** The data is fetched from a fixed API; the report templates are persona-specific fixed formats; the conversion from JSON fields to report sections is deterministic.

**Turn savings:** Without a script the agent fetches report data and manually formats output across 2–3 turns; a report script accepts an execution ID and persona, and returns a formatted report in one turn.

---

## Justification for Classification

**Strong** — not Partial, not None.

**Why not Partial:** Six of eight distinct teaching areas are codifiable. The two non-codifiable areas (test design judgment and go/no-go decisions) are downstream human concerns; everything the skill teaches about operating Test Manager is mechanically scriptable.

**Why not None:** The skill's primary value is an extensive CRUD command surface with a documented Playwright pipeline, a binary CLI surface probe, and a fixed report generation workflow — all codifiable.

**Evidence locations:**
- CLI surface probe: `skills/uipath-test/SKILL.md` §Critical Rules rule 2 (lines 232–234)
- CRUD lifecycle: `skills/uipath-test/SKILL.md` §Commands + §Quick Start (lines 38–303)
- Playwright pipeline: `skills/uipath-test/SKILL.md` §Pack Commands (line 167), §Navigate to a workflow (line 321)
- Pre-rename fallbacks: `skills/uipath-test/SKILL.md` §Pre-rename fallbacks (lines 244–259)
- Wait/status check: `skills/uipath-test/SKILL.md` §Wait Commands (lines 172–174), §Critical Rules rule 11 (line 241)
- Report generation: `skills/uipath-test/SKILL.md` §Report Commands (line 148), §Navigate to a workflow (line 319)
