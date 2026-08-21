# Classification Details — uipath-solution

**Classification: Strong**

---

## What the Skill Teaches

How to manage the full UiPath Solution package lifecycle via the `uip solution` CLI — from CLI version detection and solution initialization through multi-environment pack, publish, deploy, and activate.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | **CLI surface probe (pre- vs post-rename verb detection)** | **Yes — VALIDATE/CHECK** | Fixed probe command + binary result + fallback translation table |
| 2 | **Solution lifecycle pipeline (init→refresh→pack→publish→deploy→activate)** | **Yes — TRANSFORM-PIPELINE** | Documented fixed sequence with no judgment between steps |
| 3 | **Post-mutation artifact verification** | **Yes — VALIDATE/CHECK** | Explicit rule to re-read `.uipx`/deploy status after every mutation |
| 4 | **Multi-environment promotion pattern** | **Yes — TRANSFORM-PIPELINE** | Fixed: tenant switch + `--config-file`; same `.uipx`, different target |
| 5 | AppV2 coded app authoring (inside vs standalone routing) | No | Judgment required to identify project type and choose the correct init path |
| 6 | Failure diagnosis (error code lookup, manual-edit sync recovery) | No | Root-cause analysis is judgment-based investigation |

---

## Codifiable Procedures (not yet scripted)

### 1. CLI Surface Probe — VALIDATE/CHECK

**Source:** `skills/uipath-solution/SKILL.md` §CLI Surface Probe

**What it does:** Runs `uip solution init --help --output json`, parses the result, and classifies the CLI surface as post-rename (default) or pre-rename. If post-rename, commands proceed as documented. If pre-rename (`unknown command`), every subsequent `solution` call is translated via the three-row fallback table before execution. If the CLI is not found at all, the agent aborts and tells the user to install. Line 30: "Before the first `uip solution …` command in a session, probe the `solution` surface to detect pre- vs post-rename CLI:"

**Why it's mechanical:** The decision tree has exactly three branches on a binary probe result; the fallback translation is a fixed lookup table with three rows.

**Turn savings:** Without a script the agent spends 1–2 turns probing, parsing prose output, and applying the mapping manually before every session; a script collapses this to one call returning a `surface` enum + ready-translated verbs.

---

### 2. Solution Lifecycle Pipeline — TRANSFORM-PIPELINE

**Source:** `skills/uipath-solution/SKILL.md` §Workflow

**What it does:** Executes an 8-step fixed sequence: (1) `init` / `project add`, (2) `resources refresh`, (3) optional `restore`, (4) `pack`, (5) `login`, (6) `publish`, (7) `deploy run`, (8) optional `activate`. Each step produces an artifact consumed by the next. Steps 2–4 must run in order before publish; login must precede publish. Line 65: `"1. init / project add → Create solution, register projects (.uipx + resources/solution_folder/)"`.

**Why it's mechanical:** The ordering is prescribed and invariant; conditions for skipping optional steps (restore, activate) are explicit flags (`--skip-activate`), not judgment.

**Turn savings:** Without a script the agent issues each CLI command in a separate turn, checking output before proceeding; an orchestrator script completes the whole pipeline (or up to a named phase) in one turn.

---

### 3. Post-Mutation Artifact Verification — VALIDATE/CHECK

**Source:** `skills/uipath-solution/SKILL.md` §Critical Rules

**What it does:** After every CLI mutation, reads the affected artifact (`project.json`, `.uipx`, or `uip solution deploy status --output json`) and compares it against the expected post-mutation state. Returns pass if the artifact reflects the change, fail with a diff if it does not. Line 57: "Verify the artifact after every CLI mutation. Read `project.json`, `.uipx`, or `uip solution deploy status` output — exit codes lie."

**Why it's mechanical:** The check is a deterministic comparison of a known field against an expected value; no interpretation is required.

**Turn savings:** Without a script the agent reads and parses the artifact in 1–2 additional turns after each mutation; a verify script collapses this to a single idempotent call that returns pass/fail.

---

### 4. Multi-Environment Promotion — TRANSFORM-PIPELINE

**Source:** `skills/uipath-solution/SKILL.md` §Critical Rules

**What it does:** Promotes a single packed `.uipx` to multiple environments by (a) switching tenant with `uip login tenant set <tenant>` and (b) passing a per-environment config file via `--config-file <path>` to `deploy run`. Line 58: "For multi-environment promotion, switch tenants with `uip login tenant set <tenant>` and pass a per-environment deploy config via `--config-file <path>`."

**Why it's mechanical:** The promotion sequence is fully specified; environment identity is expressed by tenant name and config file path, both external inputs.

**Turn savings:** Without a script the agent issues tenant-switch and deploy commands separately per environment across multiple turns; a promotion script accepts a list of (tenant, config-path) pairs and runs the sequence once per environment.

---

## Justification for Classification

**Strong** — not Partial, not None.

**Why not Partial:** Four of six distinct teaching areas are codifiable VALIDATE/CHECK or TRANSFORM-PIPELINE procedures. The two non-codifiable areas (AppV2 routing judgment and failure diagnosis) are secondary appendages; the primary value of the skill is the lifecycle pipeline and its associated checks, all of which are mechanical.

**Why not None:** The skill's core is an explicitly documented, step-ordered CLI pipeline with a binary version-detection gate and a mandatory post-mutation verification step — all three are unambiguously codifiable.

**Evidence locations:**
- CLI surface probe: `skills/uipath-solution/SKILL.md` §CLI Surface Probe (lines 30–47)
- Solution lifecycle: `skills/uipath-solution/SKILL.md` §Workflow (lines 64–83)
- Post-mutation verification: `skills/uipath-solution/SKILL.md` §Critical Rules rule 8 (line 57)
- Multi-environment promotion: `skills/uipath-solution/SKILL.md` §Critical Rules rule 9 (line 58)
