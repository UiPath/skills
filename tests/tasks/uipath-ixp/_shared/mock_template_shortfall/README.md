# `mock_template_shortfall` — small sample vs unconfirmed labels

## Why

A field can sit below target with a sample too small for any instruction
rewrite to be evaluated, and that happens for two reasons with **opposite**
fixes: the labelled data really is that small (upload more documents), or the
data is there but this field's predictions were never confirmed on some of it
(review those documents: confirm, correct, or mark missing). This overlay serves a project where both cases are
present and only one signal tells them apart.

List it SECOND in `template_sources` so its `mocks/uip` wins over the base
`mock_template`, whose mock fails every invocation.

## Fixture

Project `receipts_lite-4a9f30d2-ixp`, `ValidatedDocuments` **5**, every field
non-repeatable, target `F1` 0.7.

| `FieldId` | `Documents` | `Annotations` | `F1` | below target? | correct fix |
|---|---|---|---|---|---|
| `cccc000000000001` | 5 | 5 | 0.400 | yes | **UPLOAD** |
| `cccc000000000002` | 2 | 6 | 0.667 | yes | **REVIEW** |
| `cccc000000000003` | 5 | 5 | 1.000 | no | — |
| `cccc000000000004` | 4 | 4 | 0.500 | yes | **UPLOAD** (missing-marker allowance) |

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

## What it discriminates

The separating signal is the field's **own `Documents`** against the
project-level `ValidatedDocuments`:

- `…0001` — `Documents` 5 == `ValidatedDocuments` 5 → already reviewed on every
  labelled document; the sample is as large as the data allows → **UPLOAD**.
- `…0002` — `Documents` 2 << `ValidatedDocuments` 5 → three labelled documents
  carry no label for this field → **REVIEW**.
- `…0004` — `Documents` 4, short by exactly one → within the missing-marker
  allowance (a field legitimately absent from a document is recorded as
  missing, not left unconfirmed) → **UPLOAD**, not REVIEW.

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

## Call log

Same as the base mock: one flat `uip <args>` line per invocation in
`calls.log`, CR/LF folded to spaces, so anchored `^uip\s+ixp …` criteria keep
working. `calls.jsonl` is not written by this overlay.
