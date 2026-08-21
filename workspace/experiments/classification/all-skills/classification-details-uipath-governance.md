# Classification Details — uipath-governance

**Classification: Partial**

---

## What the Skill Teaches

Authoring, deploying, and diagnosing UiPath governance policies across three layers — AOps product policies (feature control in Studio/Robot/AI Trust Layer), Access ToolUsePolicies (caller→resource invocation rules), and Compliance Standards (ISO 42001 posture analysis and application).

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | **Intent disambiguation (AOps vs Access vs Compliance standard)** | **Yes — DETECT** | Rule-based routing using explicit phrase signals, file signals (`.uipolicy`), and standard names (`ISO 42001`); disambiguation question for ambiguous phrases |
| 2 | AOps policy authoring (content, rules, product targets) | No | Judgment; policy design, choosing which features to block/restrict/enforce and at what scope |
| 3 | AOps policy merging (`merge-overrides.mjs`) | No | Already scripted (`scripts/merge-overrides.mjs`) |
| 4 | Access ToolUsePolicy authoring (caller, resource, tag rules) | No | Judgment; rule design, actor/resource selection, condition logic |
| 5 | AOps policy deploy (`uip gov aops-policy create` + deploy) | No | Requires user confirmation gate (Critical Rule 5) — not a purely unscripted pipeline |
| 6 | **Compliance posture analysis (`uip gov compliance-packs state coverage`)** | **Yes — VALIDATE/CHECK** | Fixed command; compares current tenant settings against standard's recommended settings and returns gap report |
| 7 | Compliance formdata synthesis (`synthesize-formdata.mjs`) | No | Already scripted (`scripts/synthesize-formdata.mjs`) |
| 8 | Compliance full-apply and partial-apply | No | Requires user confirmation gate between posture analysis and `state enable` or `aops-policy create`; judgment governs which clauses to apply |
| 9 | Governance diagnostic investigation | No | Judgment; interpreting deployment precedence conflicts, evaluating access-policy rules against test scenarios |

---

## Codifiable Procedures (not yet scripted)

### 1. Intent Disambiguation — DETECT

**Source:** `skills/uipath-governance/SKILL.md` §Workflow (Step 1), §Disambiguation Question

**What it does:** Classifies an incoming governance request into one of three branches: AOps product policy, Access ToolUsePolicy, or Compliance standard. Uses explicit signal tables (phrase patterns, file signals like `.uipolicy`, standard names like `ISO 42001`) from `references/disambiguation-guide.md`. When a strong signal matches, routes silently; when the phrase is ambiguous (maps to both AOps and Access), presents the numbered disambiguation question and waits for digit reply. Inputs: user request text. Output: branch label (AOps / Access / Compliance). Line 61: `"If a strong signal matches, route silently. If the phrasing is ambiguous (matches AOps or Access), ask the disambiguation question and wait for a digit reply."`

**Why it's mechanical:** Strong signals are a closed enumerated list; the disambiguation question has exactly two outcomes (digits 1 or 2); compliance routing uses a fixed set of trigger phrases and standard names.

**Turn savings:** Without a script, the agent reasons about the signal table across a full turn before routing; a classification script could return the branch label in one call so the agent skips the disambiguation reasoning turn.

---

### 2. Compliance Posture Analysis — VALIDATE/CHECK

**Source:** `skills/uipath-governance/SKILL.md` §Reference Navigation

**What it does:** Runs `uip gov compliance-packs state coverage <packId> tenant <tenantId> --output json` to compare current tenant settings against the compliance standard's recommended settings, returning a gap report of which controls are configured vs missing. Must run before any full-apply or partial-apply flow (Critical Rule 5: show the plan before applying). Inputs: compliance pack ID (`iso-42001-2023`), tenant ID. Output: structured gap report. Line 107: `"Posture analysis — what settings are configured vs recommended → references/compliance-pack/coverage/impl.md"`

**Why it's mechanical:** The command, its inputs, and the structure of its output are fully defined; the check compares two states (current vs recommended) with no judgment about what constitutes a gap.

**Turn savings:** Without a script wrapper, the agent runs the command and then manually parses and formats the gap JSON; a script outputs a structured summary table in one call.

---

## Justification for Classification

**Partial** — not Strong, not None.

**Why not Strong:** Policy authoring — both AOps (choosing which product features to govern and at what scope) and Access (designing caller/resource/tag rules) — is judgment-driven and constitutes the majority of the skill's value. Diagnostic investigation is also judgment-heavy. The two codifiable procedures (disambiguation DETECT, posture VALIDATE/CHECK) are routing and pre-flight helpers, not the core authoring work. The scripts that exist (`merge-overrides.mjs`, `synthesize-formdata.mjs`) handle individual mechanics but the orchestration between them is interrupted by required user-confirmation gates (Critical Rule 5), preventing a fully unscripted TRANSFORM-PIPELINE.

**Why not None:** Intent disambiguation follows an explicit rule table that maps phrase patterns and file signals to branches — a DETECT procedure. Compliance posture analysis is a single deterministic CLI call that checks current state against a fixed standard — a VALIDATE/CHECK procedure. Two scripts already cover AOps override merging and compliance formdata synthesis.

**Evidence locations:**
- Disambiguation routing: `skills/uipath-governance/SKILL.md` §Workflow Step 1 (lines 61–62), §Disambiguation Question (lines 76–86)
- Posture analysis: `skills/uipath-governance/SKILL.md` §Reference Navigation (line 107)
- Confirmation gate preventing unscripted pipeline: `skills/uipath-governance/SKILL.md` §Critical Rules Rule 5 (line 53)
- Already-scripted merge: `skills/uipath-governance/scripts/merge-overrides.mjs`
- Already-scripted synthesis: `skills/uipath-governance/scripts/synthesize-formdata.mjs`
