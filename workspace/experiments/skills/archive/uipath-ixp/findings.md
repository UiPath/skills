# Codifiable Procedure Findings — uipath-ixp

Four deterministic procedures identified in the improve-prompts-guide and label-documents-guide. All operate on local JSON files produced by `uip ixp` commands with `--output json`.

---

## Procedure 1 — Field Diagnosis (`COMPUTE` + `LOOKUP`)

**Source:** improve-prompts-guide.md §2a

**What it does:** Given a metrics JSON and taxonomy JSON, compute for every field: (a) its human-readable name (join `field_id` from metrics → `field_id` in taxonomy), (b) whether to SKIP or REFINE (based on `Documents` count and F1 threshold 0.7), and (c) the problem type (PRECISION / RECALL / BOTH based on which score lags). Also diagnoses each field group's aggregate score.

**Why it's mechanical:** Every decision is a comparison against numeric thresholds and keyword rules with no agent judgment involved:
- `Documents == 0 AND F1 == 0` → SKIP
- `Documents < 1` → SKIP
- `F1 >= 0.7` → OK (no action)
- `Precision < Recall - 0.1` → PRECISION
- `Recall < Precision - 0.1` → RECALL
- otherwise → BOTH

**Script:** `scripts/diagnose_fields.py`
- Input: `--metrics <json-file>` `--taxonomy <json-file>` `[--threshold 0.7]` `[--json]`
- Output: text table to stdout (add `--json` for JSON too); exit 0

**Example:**
```bash
python3 scripts/diagnose_fields.py \
  --metrics /tmp/ixp/my_project/metrics_baseline.json \
  --taxonomy /tmp/ixp/my_project/taxonomies/v1.json
# => per-field table with SKIP/OK/REFINE + PRECISION/RECALL/BOTH
```

**Tests:** `script-tests/diagnose_fields/` — covers SKIP (documents=0), OK (F1≥0.7), and all three REFINE problem types (PRECISION, RECALL, BOTH).

---

## Procedure 2 — Metrics Comparison + Regression Detection (`COMPUTE` + `DETECT`)

**Source:** improve-prompts-guide.md §2f and Step 3 (Final Report)

**What it does:** Given two metrics JSON files (baseline and current), join by field_id (using taxonomy for names), compute per-field F1 change, flag regressions (drop > 0.1), output a comparison table. Also computes overall ProjectScore change. Used after every iteration and for the final summary report.

**Why it's mechanical:** Pure arithmetic — subtract baseline F1 from current F1 per field, flag if delta < -0.1. No judgment.

**Script:** `scripts/compare_metrics.py`
- Input: `--baseline <json-file>` `--current <json-file>` `--taxonomy <json-file>` `[--regression-threshold 0.1]` `[--out <file>]`
- Output: comparison table to stdout + JSON to `--out <file>` if given; exit 1 if any field regressed, exit 0 if none

**Example:**
```bash
python3 scripts/compare_metrics.py \
  --baseline /tmp/ixp/my_project/metrics_baseline.json \
  --current  /tmp/ixp/my_project/metrics_iter1.json \
  --taxonomy /tmp/ixp/my_project/taxonomies/v1.json \
  --out      /tmp/ixp/my_project/delta_iter1.json
# exit 0 → no regressions; exit 1 → roll back regressed fields
```

**Tests:** `script-tests/compare_metrics/` — `current.json` (exit 1: Vendor Address regresses); `current_no_regression.json` (exit 0: all fields improve or hold).

---

## Procedure 3 — Taxonomy Field-Count Delta Check (`VALIDATE`)

**Source:** improve-prompts-guide.md §2c (post-update verification)

**What it does:** Given two taxonomy JSON files (before and after a prompt update), verify that no label_def lost fields. The guide mandates: "STOP the workflow immediately" if any fields go missing. This is a pure count comparison per label_def.

**Why it's mechanical:** Count `len(label_def.field_defs)` per group in old vs new; report groups where count dropped; exit 1 if any.

**Script:** `scripts/check_taxonomy_delta.py`
- Input: `--old <json-file>` `--new <json-file>`
- Output: per-group table to stdout; exit 0 if all groups intact, exit 1 if any lost fields

**Example:**
```bash
python3 scripts/check_taxonomy_delta.py \
  --old /tmp/ixp/my_project/taxonomies/v1.json \
  --new /tmp/ixp/my_project/taxonomies/v2.json
# exit 0 → safe to continue; exit 1 → STOP, restore from v1.json
```

**Tests:** `script-tests/check_taxonomy_delta/` — `new_taxonomy_ok.json` (exit 0: field counts unchanged); `new_taxonomy_corrupted.json` (exit 1: "Vendor Address" lost from Invoice group).

---

## Procedure 4 — Instruction Quality Validation (`VALIDATE`)

**Source:** improve-prompts-guide.md §2b (Instruction quality standards)

**What it does:** Given a field-updates JSON (`[{"name": ..., "instructions": ...}]`), validate each instruction against the explicit rules: min 120 chars, at least one location-hint keyword ("section", "header", "table", "top of", "labeled", "label", "near", "found"), no format-pattern strings ("Format:", "MM/DD", "DD/MM", "YYYY-MM"), presence of "Example:" (warn only). Exit 1 if any instruction fails a hard rule.

**Why it's mechanical:** All rules are explicit and deterministic. Keyword list and length threshold are stated verbatim in the skill.

**Script:** `scripts/validate_instructions.py`
- Input: `--updates <json-file>` `[--min-length 120]`
- Output: per-instruction pass/fail table to stdout; exit 0 if all pass hard rules, exit 1 if any fail

**Example:**
```bash
python3 scripts/validate_instructions.py \
  --updates /tmp/ixp/my_project/prompts/field_updates.json
# exit 0 → safe to run `fields update-prompts`; exit 1 → fix ERRORs first
```

**Tests:** `script-tests/validate_instructions/` — `good_updates.json` (exit 0: two valid instructions); `bad_updates.json` (exit 1: one instruction too short and missing location hint; one with "Format:" warning).

---

## How they chain

The agent calls scripts in this order within the improve-prompts loop:

```
diagnose_fields.py          → pick which fields need REFINE (saves ~2 turns of JSON parsing + analysis)
[agent writes instructions]
validate_instructions.py    → catch bad instructions before sending to API (saves ~1 turn per bad instruction)
[agent runs fields update-prompts / groups update-prompts]
check_taxonomy_delta.py     → verify no fields were lost (saves ~2 turns of taxonomy comparison)
[wait ~2 min, get new metrics]
compare_metrics.py          → detect regressions, build summary table (saves ~2 turns of manual comparison)
```

No orchestrator needed — they are fast independent checks that the agent calls explicitly between API calls.
