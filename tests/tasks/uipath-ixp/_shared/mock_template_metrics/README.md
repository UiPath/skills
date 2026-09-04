# `mock_template_metrics` — the metrics fixtures, one overlay

One overlay serves every metrics smoke: the mock dispatches on the project
name found in the arguments, so each task picks its fixture by naming its
project instead of carrying a near-identical overlay of its own.

| project | fixture | used by |
|---|---|---|
| `my_invoices-f1afa9ef-ixp` | diagnosis payload, one version | `metrics_full_signal_diagnosis` |
| `receipts_qa-7c2e11a4-ixp` | two versions (40 → 41) | `metrics_regression_noise_floor`, `metrics_group_rollback` |
| `receipts_lite-4a9f30d2-ixp` | `Documents` variance, one version | `metrics_annotations_shortfall` |
| `parcel_docs-6e2b91c8-ixp` | group-vs-field routing, one version | `metrics_group_routing` |

List it SECOND in `template_sources` so its `mocks/uip` wins over the base
`mock_template`, whose mock fails every invocation. `fields update-prompts`
is accepted (logged, `Success`, stateless) for the execution variants; any
other verb, and any unknown project, fails offline like the base mock.

Every row of every fixture derives from an explicit confusion matrix;
`ErrorRate` is an integer error count over `Annotations`; `ProjectScore` is
the unweighted mean of per-field `F1`, matching the live API.

## Call log

Same as the base mock: one flat `uip <args>` line per invocation in
`calls.log`, CR/LF folded to spaces, so anchored `^uip\s+ixp ...` criteria
keep matching. `calls.jsonl` is not written by this overlay.

## Fixture: `my_invoices-f1afa9ef-ixp` (diagnosis) — project `my_invoices-f1afa9ef-ixp`, ModelVersion 12

Every row is derived from an explicit confusion matrix, so the numbers are
internally consistent rather than hand-picked:

| Field | `FieldId` | TP | FP | FN | F1 | Prec | Rec | `ErrorRate` | Docs | `Annotations` | `Quality` | Correct call |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Invoice Number | `aaaa000000000001` | 30 | 30 | 10 | 0.600 | 0.500 | 0.750 | 0.750 | 40 | 40 | average | **PRECISION** |
| Vendor Address | `aaaa000000000002` | 12 | 4 | 12 | 0.600 | 0.750 | 0.500 | 0.500 | 24 | 24 | average | **RECALL** |
| Bill-To Name | `aaaa000000000003` | 40 | 0 | 0 | 1.000 | 1.000 | 1.000 | 0.000 | 40 | 40 | good | no work needed |
| Freight Charge | `aaaa000000000004` | 4 | 0 | 1 | 0.889 | 1.000 | 0.800 | 0.200 | 5 | 5 | good | above target, tiny sample |

Project: `ProjectScore` 0.772 (the unweighted mean of the per-field `F1` values, matching the live API), `ProjectScoreQuality` `good`, `ValidatedDocuments` 40.

### What it discriminates

**Invoice Number and Vendor Address carry the same `F1` and need opposite
rewrites.** An agent reading only `F1` cannot tell them apart and must guess; one
reading the `Precision`/`Recall` split gets both right. That is the point of the
fixture — the two paths differ in the graded artifact, not in command shape.

Two further traps, both faithful to real API behaviour:

- **`ErrorRate` is `errors / Annotations`, not `1 - Precision`.** A wrong value
  counts once, not as a false positive plus a false miss, so `ErrorRate x
  Annotations` is a whole number on every row (30, 12, 0, 1). It differs from
  `1 - Precision` on three of the four rows. **Freight Charge is the sharp
  case:** `Precision` 1.000 — the model emitted nothing wrong — yet `ErrorRate`
  0.200, because it missed one of five. A miss cannot lower precision but is
  still an error the user has to fix.
- **Field `Quality` and `ProjectScoreQuality` do not share a scale.** Bill-To
  Name has `F1` 1.00 yet reads `good`, the same label the project earns at 0.75.
  An agent gating on the label rather than the number flags a perfect field.

`get-taxonomy` is served so field ids resolve to names; graded artifacts are
keyed by field id, which needs no join.

## Fixture: `receipts_qa-7c2e11a4-ixp` (two versions)

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

### What it discriminates

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

## Fixture: `receipts_lite-4a9f30d2-ixp` (Documents variance)

Project `receipts_lite-4a9f30d2-ixp`, `ValidatedDocuments` **5**, every field
non-repeatable, target `F1` 0.7.

| `FieldId` | `Documents` | `Annotations` | `F1` | below target? | correct fix |
|---|---|---|---|---|---|
| `cccc000000000001` | 5 | 5 | 0.400 | yes | **UPLOAD** |
| `cccc000000000002` | 2 | 6 | 0.667 | yes | **REVIEW** |
| `cccc000000000003` | 5 | 5 | 1.000 | no | — |
| `cccc000000000004` | 4 | 4 | 0.500 | yes | **REVIEW** |

Every below-target field is genuinely unmeasurable-by-rewrite — their
regression thresholds (`max(0.1, 1/Annotations)`) are 0.2, 0.167 and 0.25 — so
the premise "a rewrite cannot be evaluated here" holds for all three and the
task is purely about which remedy applies.

Rows derive from explicit confusion matrices, so `Precision`, `Recall` and
`ErrorRate` are consistent with `F1` rather than hand-picked:

| `FieldId` | TP | FP | FN | `Ann` |
|---|---|---|---|---|
| `cccc000000000001` | 2 | 3 | 3 | 5 |
| `cccc000000000002` | 4 | 2 | 2 | 6 |
| `cccc000000000003` | 5 | 0 | 0 | 5 |
| `cccc000000000004` | 2 | 2 | 2 | 4 |

`ErrorRate` is an integer error count over `Annotations`, so
`ErrorRate x Annotations` is a whole number on every row (3, 2, 0, 2). The
group row aggregates the matrices (TP 13, FP 7, FN 7 → `F1` 0.65, `ErrorRate`
0.35); `ProjectScore` is the unweighted mean of per-field `F1` (0.642).

### What it discriminates

The separating signal is the field's **own `Documents`** against the
project-level `ValidatedDocuments`:

- `…0001` — `Documents` 5 == `ValidatedDocuments` 5 → already reviewed on every
  labelled document; the sample is as large as the data allows → **UPLOAD**.
- `…0002` — `Documents` 2 << `ValidatedDocuments` 5 → three labelled documents
  carry no label for this field → **REVIEW**.
- `…0004` — `Documents` 4, short by exactly one → still **REVIEW**: the payload
  cannot say what that one document is — unreviewed, or reviewed and skipped —
  and only the review can. Rounding a small shortfall up to "complete" silently
  caps the field if the document was in fact never reviewed.

**`Annotations` is the trap, not the signal.** `…0002` carries the **largest**
`Annotations` (6) of the three flagged fields while being reviewed on the
fewest documents, because `Annotations` counts reviewed *extractions*
(`num_reviewed_entities` in the API) and this field averages three per
document. An agent that compares `Annotations` against a document count — or
takes the smallest `Annotations` as the smallest sample — prescribes the fixes
the wrong way round. `Annotations / Documents` is the occurrences-per-document
ratio (1.0 vs 3.0 here), which is how `Annotations` has to be read.

`Recall` is not the discriminator either: `…0002` sits at `Recall` 0.667, well
above the 0.5 gate on step 2a-check, so an agent relying on that gate alone
never probes it. `Quality` reads `average` for all three flagged fields, so it
cannot separate anything.

`get-taxonomy` is served (all fields non-repeatable) and `documents list`
reports `Total` 5, so the document count is reachable two ways. Graded
artifacts are keyed by field id, which needs no join.

## Fixture: `parcel_docs-6e2b91c8-ixp` (group vs field)

Project `parcel_docs-6e2b91c8-ixp`, `ValidatedDocuments` **10**, target `F1`
0.7, two non-repeatable groups. Every `Annotations` is 10, so each field's
regression threshold collapses to the flat 0.1 — no noise-floor interference
with the routing question.

| group | `FieldId` | field | TP | FP | FN | `F1` | correct rewrite |
|---|---|---|---|---|---|---|---|
| Shipping Address | `dddd000000000001` | Street | 4 | 6 | 6 | 0.400 | **group** |
| Shipping Address | `dddd000000000002` | City | 5 | 5 | 5 | 0.500 | **group** |
| Shipping Address | `dddd000000000003` | Postal Code | 4 | 6 | 6 | 0.400 | **group** |
| Invoice Header | `dddd000000000004` | Reference Number | 2 | 8 | 8 | 0.200 | **field** |
| Invoice Header | `dddd000000000005` | Issue Date | 8 | 2 | 2 | 0.800 | — |
| Invoice Header | `dddd000000000006` | Carrier Name | 10 | 0 | 0 | 1.000 | — |

Group rows aggregate the matrices: Shipping Address TP 13, FP 17, FN 17 →
`F1` 0.433; Invoice Header TP 20, FP 10, FN 10 → `F1` 0.667. `ProjectScore` is
the unweighted mean of per-field `F1` (0.550).

### What it discriminates

**Both group rows sit below the 0.7 target — that is the point.** Neither
level of the payload answers alone:

- An agent routing on **group-row `F1` alone** reads both groups as "entire
  group low" and rewrites Invoice Header's group instructions to fix what is
  one field's problem — disturbing two fields at 0.800 and 1.000.
- An agent routing on **per-field `F1` alone** emits four field rewrites and
  misses that the three Shipping fields fail *together* — the shared-cause
  case the guide routes to `--groups`.

The correct read is the guide's 2a order: check `FieldGroups` first, then look
*inside* a low group — every field low means the group instructions, one field
low means that field.

`get-taxonomy` is served (field names and existing group instructions);
graded artifacts are keyed by group name and field id, which need no join.
