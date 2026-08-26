# `mock_template_regression` — two-version metrics for the 2f decision

## Why

The improvement loop's hardest step is not diagnosing a field, it is deciding
what to do after a retrain: which edits to keep, which to roll back, and
whether anything it did **not** edit moved. Those decisions need two metrics
payloads, so this overlay serves the same project at two model versions.

List it SECOND in `template_sources` so its `mocks/uip` wins over the base
`mock_template`, whose mock fails every invocation.

## Fixture

Project `receipts_qa-7c2e11a4-ixp`, `ValidatedDocuments` 5. Version 40 is the
previous iteration; version 41 is the result of the iteration under test.

The mock serves only the two metric snapshots — **which instructions the
iteration edited is declared by each task's prompt**, so the same fixture
grades opposite branches of 2f: `metrics_regression_noise_floor` declares two
per-field edits, `metrics_group_rollback` declares one group edit.

| `FieldId` | group | edited? | `Ann` | v40 | v41 | drop | threshold | correct call |
|---|---|---|---|---|---|---|---|---|
| `bbbb000000000001` | Receipt | **yes** | 5 | 1.000 | 0.889 | 0.111 | 0.200 | keep — under its own floor |
| `bbbb000000000002` | Line Items | **yes** | 40 | 0.800 | 0.600 | 0.200 | 0.100 | **roll back** |
| `bbbb000000000003` | Line Items | no | 40 | 0.900 | 0.650 | 0.250 | 0.100 | **collateral** — report, don't roll back |
| `bbbb000000000004` | Receipt | no | 5 | 1.000 | 0.889 | 0.111 | 0.200 | ignore — under its own floor |

`threshold = max(0.1, 1 / Annotations)`, per
[Regression noise floor](../../../../../skills/uipath-ixp/references/improve-prompts-guide.md#regression-noise-floor).

`ProjectScore` (the unweighted mean of per-field `F1`) falls 0.925 → 0.757.

Every row derives from an explicit confusion matrix, so `Precision`, `Recall`
and `ErrorRate` are consistent with `F1` rather than hand-picked:

| `Ann` | `F1` | TP | FP | FN |
|---|---|---|---|---|
| 5 | 1.000 | 5 | 0 | 0 |
| 5 | 0.889 | 4 | 0 | 1 |
| 40 | 0.900 | 36 | 4 | 4 |
| 40 | 0.800 | 32 | 8 | 8 |
| 40 | 0.650 | 26 | 14 | 14 |
| 40 | 0.600 | 24 | 16 | 16 |

`ErrorRate` is `max(FP, FN) / Annotations` — a wrong value counts once, not as
a false positive plus a false miss.

## What it discriminates

Three separations, each needing a different part of the guidance:

- **Per-field thresholds, not one flat number.** `…0001` and `…0002` were both
  edited and both dropped, but only `…0002` cleared *its own* threshold. An
  agent applying a flat 0.1 rolls back both and throws away a change that did
  nothing measurable.
- **The diff has to cover every field.** `…0003` regressed hardest of all and
  was never edited. Checking only the edited fields cannot see it.
- **The collateral check respects noise floors too.** `…0004` is untouched
  *and* sub-threshold. An agent that reports every untouched field that moved
  flags it as damage.

`ProjectScore`'s 0.168 drop is served truthfully and graded by nothing. Most of
it comes from fields whose own thresholds say "keep", so an agent that gates on
`ProjectScore` instead of diffing `Fields[]` over-rolls-back — which is exactly
what the guide's collateral check tells it not to do.

Under `metrics_regression_noise_floor`'s history (per-field edits only), the
auto-rollback exception for collateral damage does not apply, so `…0003` is
reported rather than rolled back. Under `metrics_group_rollback`'s history
(one `groups update-prompts` edit), the same drops read the opposite way:
both Line Items fields were moved by the group edit, so the group's
instructions are rolled back and nothing is collateral — while the header
fields' 0.111 drops stay under their own 0.200 thresholds in both variants.

## Call log

Same as the base mock: one flat `uip <args>` line per invocation in
`calls.log`, CR/LF folded to spaces, so anchored `^uip\s+ixp …` criteria keep
working. `calls.jsonl` is not written by this overlay.
