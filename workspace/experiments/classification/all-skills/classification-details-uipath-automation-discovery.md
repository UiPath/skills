# Classification Details — uipath-automation-discovery

**Classification: Partial**

---

## What the Skill Teaches

A 5-phase investigation workflow to mine organizational data sources for automation opportunities, analyze behavioral patterns and SPOFs, produce a 4-tier prioritized report, optionally size build effort, and map findings to UiPath implementation paths.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | Phase 0: Intake — gather context, verify access, agree scope | No | Fully interactive; requires judgment about jurisdiction constraints, privacy scope, and scope agreement |
| 2 | Phase 1: Mine — collect raw data from verified sources | No | Source prioritization and search strategy require judgment; access verification is a simple read-only probe |
| 3 | Phase 2: Analyze — behavioral patterns, SPOFs, replicable models, department map | No | Pattern recognition, SPOF identification, and replicable model discovery are judgment-heavy interpretation tasks |
| 4 | Phase 3: Reflect — strategic gap analysis against business context | No | Requires web research and strategic interpretation of company priorities vs observed gaps |
| 5 | **Phase 4: Report — produce 4-tier prioritized opportunity report** | **Yes — FORMAT-CONVERT** | Fixed report structure with explicit tier definitions, evidence standards, and table schemas provided in `report-template.md` |
| 6 | **Phase 4.5: Estimate — band→hours→contingency sizing** | **Yes — COMPUTE/FORMULA** | Fixed formula: opportunity → complexity band → pack-hours → adjustment factors → contingency → total; constants are user-supplied from authoritative catalogue |
| 7 | **Phase 5: Handoff — map findings to UiPath implementation skills** | **Yes — LOOKUP/REFERENCE-TABLE** | Fixed table mapping opportunity types to implementation skills (RPA, Flow, Agents, HITL, Platform) |

---

## Codifiable Procedures (not yet scripted)

### 1. Opportunity-to-Skill Handoff Lookup — LOOKUP/REFERENCE-TABLE

**Source:** `skills/uipath-automation-discovery/SKILL.md` §Phase 5: HANDOFF

**What it does:** Maps each discovered automation opportunity to a UiPath implementation skill and artifact type based on the opportunity's category (desktop automation → uipath-rpa, multi-step orchestration → uipath-maestro-flow, agent-based → uipath-agents, approval gate → uipath-human-in-the-loop, cross-system integration → uipath-platform). Input: opportunity type label. Output: recommended skill + artifact type. Line 219: `"Map each Tier 1-2 opportunity to a UiPath implementation path. Add a 'Next Step' column to the report's Tier 1-2 tables."`

**Why it's mechanical:** The mapping table has explicit rows with no ambiguity; the output is fully determined by the input category label.

**Turn savings:** Without a script, the agent looks up the table manually each time an opportunity needs routing; a lookup script eliminates this repeated inline reference.

### 2. Build Effort Estimation — COMPUTE/FORMULA

**Source:** `skills/uipath-automation-discovery/SKILL.md` §Phase 4.5: ESTIMATE

**What it does:** Applies the user-supplied complexity matrix to map each opportunity to a band (Simple/Medium/Complex/High), then multiplies by pack-hours from the catalogue, applies adjustment factors (multi-entity redeploy factor, existing-automation rebuild discount), and adds confidence-tiered contingency to produce a total delivery estimate. Inputs: opportunity description + user-supplied matrices. Outputs: band, pack-hours, adjusted total with contingency. Line 205: `"The band→hours numbers and matrix thresholds are authoritative references the user supplies (Core RPA + Agentic complexity matrices, Pack-Hours catalogue) — never invented (Critical Rule 6)."`

**Why it's mechanical:** Once the matrices and catalogue are supplied, each step is an arithmetic lookup and multiplication with no judgment; the above-ceiling decompose rule (>7 apps / >8 variations) is also an explicit threshold check.

**Turn savings:** Without a script, the agent mentally works through the formula and matrix lookups across multiple reasoning steps; a script takes matrices and opportunities as inputs and produces a complete sizing table.

---

## Justification for Classification

**Partial** — not Strong, not None.

**Why not Strong:** Phases 0–3 constitute the bulk of the skill and are judgment-intensive — interviewing stakeholders, choosing which sources to mine, interpreting behavioral signals, identifying SPOFs, and mapping patterns to strategic priorities. The three codifiable procedures (handoff lookup, estimation formula, report formatting) are small helpers at the end of a predominantly judgment-driven investigation workflow.

**Why not None:** Phase 4.5 contains an explicit COMPUTE/FORMULA procedure (band→hours→contingency) with documented arithmetic steps; Phase 5 contains a LOOKUP/REFERENCE-TABLE (opportunity type → skill); Phase 4 references a fixed report template that is FORMAT-CONVERT.

**Evidence locations:**
- Estimation formula: `skills/uipath-automation-discovery/SKILL.md` §Phase 4.5: ESTIMATE (lines 196–212)
- Handoff table: `skills/uipath-automation-discovery/SKILL.md` §Phase 5: HANDOFF (lines 218–229)
- Judgment dominance: Phases 0–3 (lines 46–178) cover intake, mining, analysis, and reflection — all interactive or interpretive
