# Classification Details — uipath-maestro-case

**Classification: Strong**

---

## What the Skill Teaches

UiPath Maestro Case Management authoring skill that builds `caseplan.json` from `sdd.md` through a 7-phase lifecycle (Planning→Prototyping→Implementation→Validate→Publish→Debug→Publish to Orchestrator).

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | Routing (greenfield vs brownfield, sdd.md detection) | No | Binary trigger: file exists/not; judgment determines journey |
| 2 | Design handoff to uipath-planner | No | Delegates to sibling skill; planner owns design |
| 3 | **Phase 1 — Planning: tasks.md from sdd.md** | **Yes — BUILD-MODEL/MATRIX** | Deterministic T-entry format from SDD declarations; every stage/task/condition/variable gets a T-number per Rule 6 |
| 4 | **Phase 2 — Prototyping: case structure assembly** | **Yes — TRANSFORM-PIPELINE** | Fixed sequence: solution init → triggers → variables → entry-points → stages → tasks (shape only) → SLA → conditions → validate |
| 5 | **Phase 3 — Implementation: I/O binding** | **Yes — TRANSFORM-PIPELINE** | Connector schema fetch → I/O binding → stub upgrade → xref resolution — all deterministic per plugin recipes |
| 6 | **Phase 4 — Validate: 12-check pass + CLI validate** | **Yes — VALIDATE/CHECK** | Step 12 Checks 1–12 are fully specified; CLI validate retry up to 3× |
| 7 | **Phase 5–7 — Lifecycle: publish/debug/deploy** | **Yes — TRANSFORM-PIPELINE** | Fixed command sequences with consent gates; commands and order specified exactly |
| 8 | Formal-arg slot ID minting | No | UUIDs are generated; format check is scripted-adjacent (Check 10 re-mints violations) |

---

## Codifiable Procedures (not yet scripted)

### 1. Phase 1 Planning: T-entry BUILD-MODEL from SDD — BUILD-MODEL/MATRIX

**Source:** `skills/uipath-maestro-case/SKILL.md` §Phase 1 — Planning, Critical Rule 6

**What it does:** Reads `sdd.md` and produces `tasks/tasks.md` by mapping every SDD declaration to a numbered T-entry. The mapping is deterministic: every stage → T-entry with `lane:`, `activation-mode:`, `entry-rule:`; every task → T-entry with `type:`, `displayName:`, `activation-mode:`, `entry-rule:`; every SLA rule → T-entry. Line 36: `"One T-entry per sdd.md declaration — every stage, task, trigger, condition, SLA rule, variable, and argument gets own T-number, even when value looks like default."` Output is a fully formed `tasks.md` traceable line-by-line to the SDD.

**Why it's mechanical:** The T-entry format, field names, and inclusion rules are all specified in Critical Rule 6; no design judgment is required after `sdd.md` is confirmed.

**Turn savings:** The agent currently walks the SDD and writes T-entries one at a time across 5–15 turns; a builder script could emit the whole `tasks.md` in one pass.

---

### 2. Phase 4 Validate: 12-Check Pass — VALIDATE/CHECK

**Source:** `skills/uipath-maestro-case/SKILL.md` §Phase 4 — Validate

**What it does:** Runs Step 12 Checks 1–12 against the assembled `caseplan.json` before invoking the CLI. Checks include: bindings sidecar parity (Check 7), global output-ID uniqueness (Check 8), resolved-resource emission/preservation (Check 9), formal-arg slot ID format (Check 10), resourceKey self-consistency (Check 11), connector node resolution completeness (Check 12). Then runs `uip maestro case validate` and retries up to 3×. Line 150: `"Run Step 12 once at the Phase 3 → Phase 4 boundary. It performs Checks 1–12, including bindings sidecar parity (Check 7), global output-ID uniqueness (Check 8), resolved-resource emission/preservation (Check 9), formal-arg slot ID format (Check 10), resourceKey self-consistency (Check 11), and connector node resolution completeness (Check 12)."` 

**Why it's mechanical:** Each check has explicit pass/fail criteria; the CLI validate result is parsed and fed back for repair until pass or retry exhaustion.

**Turn savings:** The agent currently performs each check manually in separate reads/inspections across 3–8 turns; a validation script could run all 12 checks plus CLI validate in one invocation.

---

### 3. Phase 5–7 Lifecycle Pipeline — TRANSFORM-PIPELINE

**Source:** `skills/uipath-maestro-case/SKILL.md` §Phase 5 — Publish, §Phase 6 — Debug, §Phase 7 — Publish to Orchestrator

**What it does:** Executes the fixed publish/debug/deploy command sequence with user-consent gates. Phase 5: `uip solution resources refresh` → `uip solution upload` (with `--output-filter`). Phase 7: `uip maestro case pack` → `uip solution pack` → `uip solution publish --wait`. Line 164: `"uip maestro case pack <SolutionDir>/<ProjectName> <SolutionDir>/dist --output json, then uip solution pack <SolutionDir> <SolutionDir>/dist --output json, then uip solution publish <packagePath> --wait --output json."` Gates are consent-only (AskUserQuestion); the actual command sequence is fixed.

**Why it's mechanical:** The commands, their order, and their flags are fully specified; only the user consent gates require non-scripted interaction.

**Turn savings:** The agent executes these phases over 4–6 turns with interleaved narration; a script handles the command sequence and pauses only at consent gates.

---

## Justification for Classification

**Strong** — not Partial, not None.

**Why not Partial:** Five of the eight teaching areas are codifiable (Phases 1, 2, 3, 4, 5–7). The two non-codifiable areas (design handoff and routing) are delegated to `uipath-planner` or are a simple binary check — they are not where the skill's teaching density lies. The 7-phase lifecycle, the 25 Critical Rules specifying exact JSON shapes, the plugin-driven authoring recipes, and the 12-check validation pass collectively represent the large majority of what the skill teaches agents to do.

**Why not None:** Three independent codifiable procedures exist: BUILD-MODEL/MATRIX (T-entry construction from SDD), VALIDATE/CHECK (12-check pass + CLI validate loop), and TRANSFORM-PIPELINE (Phase 5–7 lifecycle commands).

**Evidence locations:**
- BUILD-MODEL/MATRIX: `SKILL.md` Critical Rule 6 (line 36) §Phase 1 — Planning
- VALIDATE/CHECK 12 checks: `SKILL.md` §Phase 4 — Validate (lines 150–153)
- TRANSFORM-PIPELINE Phase 5–7: `SKILL.md` §Phase 5, §Phase 7 (lines 156–164)
- TRANSFORM-PIPELINE Phase 2–3: `SKILL.md` §Phase 2 — Prototyping, §Phase 3 — Implementation (lines 121–146)
