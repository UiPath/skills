# Classification Details — uipath-troubleshoot

**Classification: Partial**

---

## What the Skill Teaches

Investigate UiPath runtime and configuration failures by anchoring an entity, extracting signals, routing to a playbook via grep, walking the playbook decision tree, completing a 6-item verification checklist, and presenting a root-cause diagnosis with fix recommendations.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | Anchor and entity classification | No | Requires interpreting user message and matching to domain — judgment-driven |
| 2 | **Signal extraction from raw CLI responses** | **Yes — EXTRACT** | Fixed field locations per signal kind documented in cheatsheet; deterministic unwrapping of wrapper exceptions |
| 3 | **Playbook routing via grep** | **Yes — DETECT** | Fixed-string grep of playbook corpus for extracted signals; explicit match-ranking rules |
| 4 | Playbook investigation (decision tree walk) | No | Requires causal reasoning, branch evaluation, and evidence interpretation — deeply judgment-based |
| 5 | **6-item verification checklist** | **Yes — VALIDATE/CHECK** | Fixed checklist with explicit pass/fail criteria for each of 6 items before presenting |
| 6 | Escalation trigger evaluation | **Yes — DETECT** | 6 explicit trigger conditions checked against investigation state |
| 7 | Result presentation | No | Assembling narrative, citing evidence, formatting — judgment about emphasis and scope |

---

## Codifiable Procedures (not yet scripted)

### 1. Signal extraction — EXTRACT

**Source:** `skills/uipath-troubleshoot/SKILL.md` §3. Extract signals

**What it does:** Reads raw CLI JSON responses from `.local/investigations/raw/` and extracts a fixed set of signal fields: exception class (FQN + leaf), friendly message, error code, HTTP status, faulting activity + package namespace, entity states, cross-product entity keys, and package versions. Also unwraps `System.AggregateException` wrappers to extract inner exception class and message. Output is a structured signal record written to notes.md. Line 44: "From the raw responses, record in notes.md one line per observed fact: exception class (FQN + leaf), friendly message / resource key, error code, HTTP status, faulting activity + owning package namespace, entity states, cross-product entity keys, package versions."

**Why it's mechanical:** Field locations are documented in the Signal-Extraction Cheatsheet; wrapper unwrapping follows a fixed pattern (extract inner exception from `System.AggregateException` / `--->`-chained stacks); no interpretation of field values is required for extraction itself.

**Turn savings:** Without a script the agent reads raw JSON files and extracts fields manually across several turns; a script parses the JSON and returns the structured signal record in one call.

---

### 2. Playbook routing via grep — DETECT

**Source:** `skills/uipath-troubleshoot/SKILL.md` §4. Route

**What it does:** For each extracted signal, runs `grep -rlF "<signal>" references/ --include="*.md"` to locate matching playbooks, ranks hits by the count of distinct matching signals, and applies tie-breaking rules (read `## Context` of tied hits, honor explicit redirects). Output is the winning playbook path or an escalation signal. Line 52: "Grep the playbook corpus for each extracted signal — fixed-string, filenames only (`grep -rlF \"<signal>\" references/ --include=\"*.md\"`): leaf exception class, error code, message fragments, resource keys."

**Why it's mechanical:** The grep command, ranking rule (most distinct hits wins), and tie-breaking procedure are fully specified; the script runs the commands and applies the ranking without needing to understand the signals' meaning.

**Turn savings:** Without a script the agent runs multiple grep commands and manually tallies hits across turns; a script returns the ranked playbook list in one call.

---

### 3. 6-item verification checklist — VALIDATE/CHECK

**Source:** `skills/uipath-troubleshoot/SKILL.md` §6. Verification checklist

**What it does:** Evaluates 6 explicit pass/fail criteria against the investigation state before allowing the agent to present a conclusion: (1) cause named verbatim from playbook, (2) evidence pinned to a specific raw datum, (3) runtime evidence present, (4) resolution aligned to the exact cause branch, (5) causal precedence chain answered, (6) fix scope limited to confirmed cause. Outputs pass/fail per item plus a list of blocking failures. Line 72: "Write the answers in notes.md; do not skip items, do not present without them"

**Why it's mechanical:** Each checklist item has explicit pass criteria stated in the skill; evaluating them against the notes.md investigation record requires reading structured data, not causal reasoning.

**Turn savings:** Without a script the agent re-reads the checklist and self-evaluates across prose turns; a script reads notes.md and returns a structured pass/fail verdict per item in one call.

---

### 4. Escalation trigger evaluation — DETECT

**Source:** `skills/uipath-troubleshoot/SKILL.md` §7. Escalation triggers

**What it does:** Checks 6 explicit conditions against the investigation state (no grep match, ≥2 co-equal matches with independent signatures, cross-domain chain deeper than one hop, decision tree exhausted, checklist fails after re-fetch, evidence contradicts matched playbook's core precondition) and returns whether escalation is required. Line 91: "Load `references/escalation.md` when ANY of: 1. **No playbook grep match** ... 2. **≥2 co-equal matches** ... 3. **Cross-domain chain deeper than one hop** ..."

**Why it's mechanical:** All 6 trigger conditions are enumerated with explicit criteria; evaluation against investigation state is deterministic given the grep results and checklist outputs.

**Turn savings:** Currently evaluated inline as prose logic; a script returns a boolean escalation signal in one call given the structured state from the routing and checklist scripts.

---

## Justification for Classification

**Partial** — not Strong, not None.

**Why not Strong:** The core of the skill — walking the playbook decision tree, interpreting evidence to confirm or reject branches, reasoning about causal precedence, and assembling the diagnosis — is deeply judgment-driven. Signal extraction, grep routing, checklist evaluation, and escalation detection are supporting scaffolding, not the primary teaching. The judgment work (steps §2, §5, §8 in the skill's workflow) dominates the total instruction surface.

**Why not None:** Signal extraction follows a documented cheatsheet with fixed field locations; playbook routing uses a deterministic grep command with explicit ranking rules; the verification checklist has 6 explicit pass/fail criteria; escalation triggers are fully enumerated conditions.

**Evidence locations:**
- Signal extraction cheatsheet: `skills/uipath-troubleshoot/SKILL.md` §3. Extract signals
- Grep routing and ranking rules: `skills/uipath-troubleshoot/SKILL.md` §4. Route
- 6-item verification checklist: `skills/uipath-troubleshoot/SKILL.md` §6. Verification checklist
- Escalation triggers: `skills/uipath-troubleshoot/SKILL.md` §7. Escalation triggers
- Judgment dominance (playbook walk, causal reasoning): `skills/uipath-troubleshoot/SKILL.md` §5. Walk the playbook, §1. Invariants
