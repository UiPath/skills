# Classification Details — uipath-connector-builder

**Classification: Strong**

---

## What the Skill Teaches

Author UiPath Integration Service connectors on disk with `uip is connectors builder` — from init through auth configuration, activity/field creation, validation, import, and publish.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | **New connector lifecycle (init → auth → activity → validate → import → publish)** | **Yes — TRANSFORM-PIPELINE** | Fully specified ordered sequence with copy-paste-ready commands at each step |
| 2 | **Inspect-before-edit rule** | **Yes — VALIDATE/CHECK** | `builder inspect` always runs first; never edit without reading state |
| 3 | **Activity creation with field schema** | **Yes — TRANSFORM-PIPELINE** | `activity create` → `activity field create` (per Rule 11, always required); fixed ordering |
| 4 | **Validate→fix→re-validate loop** | **Yes — VALIDATE/CHECK** | `builder validate` at end of every workflow; fix one error at a time; 3-attempt cap |
| 5 | **State inspection and patch discipline** | **Yes — VALIDATE/CHECK** | `state query` → edit → `state patch` complete object (REPLACES node — never partial patch) |
| 6 | Connection design (host templating, per-connection value sourcing) | No | Judgment required: choosing between TEXTFIELD vs COMBO, direct config vs hook vs onProvision |
| 7 | Authentication type selection (19 types) | No | Requires judgment based on vendor API docs; `auth set` is codifiable, type selection is not |
| 8 | **Polling trigger setup** | **Yes — TRANSFORM-PIPELINE** | `activity list` → `trigger create --event-kind polling --updated-date-field ... --id-field ...` → validate |

---

## Codifiable Procedures (not yet scripted)

### 1. New Connector Lifecycle — TRANSFORM-PIPELINE

**Source:** `skills/uipath-connector-builder/SKILL.md` §Workflows → New connector (full lifecycle)

**What it does:** The skill prescribes a fixed ordered sequence: (0) verify login with `uip login status`, (1) scaffold with `uip is connectors builder init` (deriving the connector key from the login org), (2) add an activity with `activity create`, (3) author field schema with `activity field create` or `--fields-file`, (4) run `builder validate` (must be 0 errors AND no unresolved warnings), (5) `uip is connectors import`, (6) `uip is connectors publish --wait`. Re-publishing requires a higher version in `element-metadata.json:latestVersion`. Line 84 (in the workflow block comment): "4. Validate — must be 0 errors AND no unresolved warnings (fieldless activity, broken SR link) before import."

**Why it's mechanical:** The command order, the login-first gate (Rule 8), the field-schema requirement after `activity create` (Rule 11), and the version-bump requirement for re-publish are all fixed rules with no judgment gaps.

**Turn savings:** Without a script, the agent executes each lifecycle step as a separate turn remembering flags and sequencing; a connector lifecycle orchestrator script compresses the full init-to-publish pipeline into parameterized single calls.

---

### 2. Validate→Fix→Re-validate Loop — VALIDATE/CHECK

**Source:** `skills/uipath-connector-builder/SKILL.md` §Critical Rules → Rule 2

**What it does:** After any edit, the skill requires running `builder validate` — which runs the full periodic check set and exits non-zero on failure. On failure, the agent reads the reported field, fixes that one entry, and re-validates. After 3 failed attempts on the same error the agent stops and surfaces the full `validate` output. Warnings about fieldless activities are treated as must-fix. Line 22: "Run `builder validate` at the end of every workflow and after each fix — it runs the full periodic check set and exits non-zero on failure. On failure, read the reported field, fix that one entry, re-validate. After 3 failed attempts on the same error, stop and surface the `validate` output."

**Why it's mechanical:** The retry cap (3 attempts), the one-fix-per-iteration rule, the warning-as-must-fix stance, and the stop condition are all fixed in the skill.

**Turn savings:** The agent currently runs validate, interprets each error, and loops across multiple turns; a validate-and-fix loop script compresses the loop with the 3-attempt cap into one invocation.

---

### 3. State Inspect-and-Patch Discipline — VALIDATE/CHECK

**Source:** `skills/uipath-connector-builder/SKILL.md` §Critical Rules → Rule 5

**What it does:** Before any `state patch`, the skill mandates running `state query <pointer>` to retrieve the entire current node, editing only the target field within it, then patching back the complete object. `state patch` replaces the whole node at the pointer with no merge. Activity paths in pointers must be URL-encoded (e.g., `/contacts` → `%2Fcontacts`). `element-metadata.json` has no addressable sub-paths — the entire file must be round-tripped. Line 27: "`state patch` REPLACES the whole node at a pointer (no merge). To change one field: `state query` the entry, edit it, then `state patch` the COMPLETE object back."

**Why it's mechanical:** The query-first requirement, the URL-encoding rule, and the element-metadata.json whole-file round-trip are fixed rules with no decision points.

**Turn savings:** The agent currently performs query and patch as separate turns while manually managing the URL encoding; a state-update helper script that accepts a pointer + field + value and applies the safe round-trip automatically reduces this to one call.

---

## Justification for Classification

**Strong** — not Partial, not None.

**Why not Partial:** Six of eight teaching areas are codifiable. The dominant teaching content — the connector lifecycle pipeline, the validate loop, the activity-plus-field creation sequence, the inspect-before-edit rule, and the state-patch discipline — are all mechanically structured with explicit sequencing, retry caps, and fixed commands. The two non-codifiable areas (auth type selection and connection design pattern choices) are smaller portions of what the skill teaches.

**Why not None:** The new connector lifecycle (TRANSFORM-PIPELINE), the validate loop (VALIDATE/CHECK), and the state query/patch discipline (VALIDATE/CHECK) are all explicit, deterministic multi-step procedures with fixed CLI commands and constants.

**Evidence locations:**
- New connector lifecycle: `SKILL.md` §Workflows → New connector (lines 49–94)
- Validate loop: `SKILL.md` §Critical Rules → Rule 2 (lines 22–24)
- Inspect-before-edit: `SKILL.md` §Critical Rules → Rule 1 (line 22)
- State patch discipline: `SKILL.md` §Critical Rules → Rule 5 (lines 27–28)
- Field schema requirement: `SKILL.md` §Critical Rules → Rule 11 (lines 33–34)
