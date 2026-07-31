# Estimation Accelerator

Size the **build effort** of a prioritized opportunity register: opportunity →
complexity band → pack-hours → adjustment factors → contingency → total. Runs
after Phase 4 (the report already carries the register + per-opportunity
confidence). This is delivery/pre-sales sizing, not the ROI/hours-saved impact
in the report.

Load when the user asks to estimate, size, cost, or produce pack-hours /
effort / a delivery estimate for discovered opportunities.

## Hard rule — never invent pack-hours

The band→hours numbers and the complexity-matrix thresholds are **authoritative
UiPath references the user supplies** — the Core RPA complexity matrix, the
Agentic complexity matrix, and the Pack-Hours catalogue. Do NOT recall,
approximate, or fabricate them. Unverified numbers are the exact failure this
accelerator exists to prevent.

1. If the user has not supplied the Pack-Hours catalogue and the complexity
   matrices, STOP and ask for them (file paths or pasted tables). Do not
   proceed with guessed hours.
2. Every band→hours value written to the worksheet cites its catalogue source.
3. Adjustment-factor and contingency percentages below are **not** authoritative
   — they are `[CALIBRATE]` defaults the user tunes against the org's actuals
   before the estimate is final.
4. Show the math for every opportunity (base → factors → contingency → total)
   so each number is auditable.

## Inputs

| Input | Source | Notes |
|---|---|---|
| Opportunity register | Phase 4 report, or user `.xlsx` | Per opportunity: apps touched, variations / decision points, data & exception complexity, agentic vs deterministic, rebuild-of-existing?, deploy entity count |
| Core RPA complexity matrix | **User-supplied** | Band thresholds (apps, variations, data, exceptions) |
| Agentic complexity matrix | **User-supplied** | Band thresholds for reasoning steps, tools, autonomy, HITL |
| Pack-Hours catalogue | **User-supplied** | Band × grain → hours |
| Benchmark (optional) | Delivery Summary / official estimate | For reconciliation |

## Procedure — per opportunity

1. **Determine grain.** Is the unit a **Process-Automation** (end-to-end
   process) or a **Tool** (reusable component / pack invoked by processes)?
   Price at the matching grain — a decomposed sub-unit is often Tool-grain.
   Grain ambiguity was a root cause of the estimate divergence; resolve it
   explicitly and record it.
2. **Classify complexity** on the matrix dimensions: deterministic RPA work →
   Core RPA matrix; agentic/reasoning components → Agentic matrix. A hybrid
   opportunity carries both a Core RPA band and an Agentic add-on.
3. **Assign band** (Simple / Medium / High) from the matrix — unless the
   above-ceiling rule fires.
4. **Above-ceiling / decompose rule.** If an opportunity exceeds the matrix
   ceiling — **> 7 applications OR > 8 variations / decision points** — do NOT
   clamp it to "High". Decompose into sub-automations (by sub-process or
   application cluster), classify and size each at its own grain, and sum.
   Record the decomposition. Clamping oversized clusters at "High" is the
   single largest source of under-estimation — this rule is the primary fix.
5. **Map band → base pack-hours** from the supplied catalogue at the resolved
   grain. Cite the catalogue row.
6. **Apply adjustment factors** (`[CALIBRATE]` defaults — confirm against
   actuals):
   - **Multi-entity redeploy:** same automation deployed across N legal
     entities / regions → do NOT count each as a full build. `base + (N-1) ×
     [CALIBRATE ~15-30%] × base` per additional entity; raise it when per-entity
     localization or regulatory variation is significant.
   - **Existing-automation rebuild discount:** rebuilding / migrating an
     automation that already exists (known logic, documented process) →
     `[CALIBRATE ~20-40%]` reduction vs greenfield, scaled by reuse and
     documentation quality.
7. **Add confidence-tiered contingency**, keyed to the opportunity's discovery
   confidence: High `[CALIBRATE ~10-15%]`, Medium `[~20-30%]`, Low / ambiguous
   scope / unknown systems `[~40%+]`.
8. **Total** = (base ± factors) × (1 + contingency). Write base, each factor,
   contingency, and total to the worksheet.

## Unified band→hours mapping (ask #3)

Replace the disconnected matrix-image + catalogue pair with one table so band,
grain, and hours live together. Fill values from the user's catalogue:

| Complexity band | Grain | Core RPA hours | Agentic add-on hours | Catalogue source |
|---|---|---|---|---|
| Simple | Process-Automation | `[FROM CATALOGUE]` | `[FROM CATALOGUE]` | `<ref>` |
| Simple | Tool | `[FROM CATALOGUE]` | — | `<ref>` |
| Medium | … | … | … | … |
| High | … | … | … | … |
| Above-ceiling | (decompose) | sum of sub-units | sum of sub-units | — |

## Scenarios & reconciliation

- Produce ≥ 2 scenarios (e.g. **Option 1** conservative full-build; **Option 2**
  with decomposition + rebuild discount + redeploy factor applied). The source
  engagement delivered three (16.2k / 12.1k / 10.7k h) — the spread comes from
  these factors, not from different base numbers.
- When a benchmark estimate exists, reconcile the portfolio total against it and
  attribute each material delta to a band, factor, or decomposition decision.

## Output

Use [assets/templates/estimation-worksheet-template.md](../assets/templates/estimation-worksheet-template.md):
per-opportunity estimate table, the unified band→hours mapping, the
decomposition log, the calibration register (every `[CALIBRATE]` value awaiting
confirmation), and the scenario roll-up. Append an **Estimation** section to the
Phase 4 report, or emit a standalone worksheet.
