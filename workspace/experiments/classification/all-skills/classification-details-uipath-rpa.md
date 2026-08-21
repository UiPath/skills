# Classification Details — uipath-rpa

**Classification: Partial**

---

## What the Skill Teaches

Create, edit, validate, build, run, and debug UiPath RPA automations in both XAML and C# coded workflow modes, including UI automation target capture and Integration Service connector usage.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | Project type detection (Legacy vs Modern, coded vs XAML) | **Yes — DETECT** | Reads `targetFramework` from `project.json`; counts `.cs` / `.xaml` files against fixed thresholds |
| 2 | **Project context freshness check** | **Yes — VALIDATE/CHECK** | Computes percentage drift on cs/xaml/deps counts; triggers discovery when any count diffs ≥60–70% |
| 3 | **Two-phase validation loop (per-file validate + project-level build)** | **Yes — VALIDATE/CHECK** | Fixed sequence: `uip rpa validate --file-path` until 0 errors, then `uip rpa build`; 5-attempt caps per loop |
| 4 | XAML workflow authoring | No | Activity selection, data flow design, error-handling strategy — all judgment |
| 5 | Coded workflow authoring | No | C# code design, service injection, data model decisions — all judgment |
| 6 | UI automation target capture | No | Interactive, app-state-sensitive; involves selector strategy and UIA indication — judgment and live app access |
| 7 | Authoring mode selection (XAML vs coded) | No | Decision table exists but final selection often requires contextual judgment about project goals |
| 8 | Activity discovery and selection | Marginal | `uip rpa activities find` lookup is codifiable; choosing the right activity requires domain judgment |
| 9 | Session pre-warm | **Yes — TRANSFORM-PIPELINE** | Fixed background command sequence to hide Studio cold-start behind planning; no judgment |
| 10 | Template selection for `uip rpa init` | **Yes — DETECT** | Rule tree with explicit match conditions for Official vs Marketplace templates |

---

## Codifiable Procedures (not yet scripted)

### 1. Project type detection — DETECT

**Source:** `skills/uipath-rpa/SKILL.md` §Project Type Detection

**What it does:** Reads `project.json` for `targetFramework` to classify Legacy vs Modern, then globs for `.cs` and `.xaml` workflow files to classify coded vs XAML vs hybrid vs new-project. Output is a project mode label that determines which reference files to load. Line 112: "After establishing `PROJECT_DIR`, **first check `project.json` for `targetFramework`**"

**Why it's mechanical:** All branch conditions are explicit file reads and glob counts with stated thresholds; no content interpretation is required.

**Turn savings:** Without a script the agent reads `project.json` and runs multiple globs across turns; a script returns the mode label plus counts in one call.

---

### 2. Project context freshness check — VALIDATE/CHECK

**Source:** `skills/uipath-rpa/SKILL.md` §Precondition: Project Context

**What it does:** Reads the metadata comment from `.claude/rules/project-context.md`, counts current `.cs` / `.xaml` files and `project.json` dependency keys, computes percentage drift for each count, and returns whether the context is fresh or stale. Line 75: "For each count (cs, xaml, deps), compute the percentage difference: `abs(current - stored) / max(stored, 1) * 100`"

**Why it's mechanical:** The staleness formula and 60–70% threshold are stated explicitly; all inputs are file reads and glob counts.

**Turn savings:** Currently the agent performs three separate reads/globs and arithmetic across multiple steps; a script returns a fresh/stale verdict in one call.

---

### 3. Two-phase validation loop — VALIDATE/CHECK

**Source:** `skills/uipath-rpa/SKILL.md` §Critical Rules Rule 3

**What it does:** Runs `uip rpa validate --file-path` on each modified file until 0 errors (up to 5 attempts), then runs `uip rpa build` at project level until clean (up to 5 attempts), parsing JSON output to detect errors and reporting the validation verdict. Line 207: "**Per-file** (after every create or edit): `uip rpa validate --file-path \"<FILE>\" --project-dir \"<PROJECT_DIR>\" --output json` until 0 errors."

**Why it's mechanical:** The loop structure, attempt caps, and error-detection logic are fully specified; the script executes the commands and parses the output with no judgment.

**Turn savings:** Without a script the agent runs validate and build manually across multiple turns, reading JSON output each time; a script runs the full loop and returns pass/fail + error list in one call.

---

### 4. Template selection for `uip rpa init` — DETECT

**Source:** `skills/uipath-rpa/SKILL.md` §Critical Rules Rule 2

**What it does:** Runs `uip rpa templates search` with a user-supplied query, applies a match rule tree (Official vs Marketplace, single vs multiple matches, user-named non-Official qualifier), and returns either the selected `--template-package-id` argument or a list of candidates requiring user confirmation. Line 199: "Selection rule against `Data[*]`: **User named a specific non-Official template** ... → ask the user ... **Exactly one `source == \"Official\"` match** ... → use it"

**Why it's mechanical:** The selection rule tree has fully enumerated branch conditions; template metadata fields (`source`, `title`, `packageId`) are parsed from JSON output.

**Turn savings:** The agent currently reruns the search and applies the rule tree inline; a script returns the selected template args or a prompt in one call.

---

## Justification for Classification

**Partial** — not Strong, not None.

**Why not Strong:** The dominant teaching of the skill is XAML and coded workflow authoring — activity selection, data flow design, error-handling strategy, UI automation target capture, and selector strategy. These are judgment-intensive and constitute the overwhelming majority of what the skill instructs the agent to do. The codifiable procedures (type detection, context freshness, validation loop, template selection) are setup and gating steps, not the core authoring work.

**Why not None:** Two-phase validation is a fully scripted loop with explicit attempt caps and JSON parsing; project type detection and context freshness checks follow deterministic formulas stated in the skill; template selection applies an explicit rule tree to structured search output.

**Evidence locations:**
- Project type detection rule tree: `skills/uipath-rpa/SKILL.md` §Project Type Detection
- Context freshness formula: `skills/uipath-rpa/SKILL.md` §Precondition: Project Context
- Two-phase validation loop: `skills/uipath-rpa/SKILL.md` §Critical Rules Rule 3
- Template selection rule tree: `skills/uipath-rpa/SKILL.md` §Critical Rules Rule 2
- XAML/coded authoring as judgment: `skills/uipath-rpa/SKILL.md` §Authoring Mode Selection, §UI Automation Capabilities
