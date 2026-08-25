# uipath-ixp metrics-serving smoke mock

Overlay for smoke tasks that must **diagnose from the full `get-metrics`
payload**, not from `F1` alone. List it SECOND in `template_sources` so it wins
over the base mock:

```yaml
sandbox:
  mock_path_dirs: [mocks]
  template_sources:
    - {type: template_dir, path: ../_shared/mock_template}
    - {type: template_dir, path: ../_shared/mock_template_metrics}
```

The base mock fails every invocation, so a diagnosis task is unwinnable on it:
the correct path reads metrics and carries the numbers into a written artifact,
and a failing read leaves nothing to diagnose.

## Fixture — project `my_invoices-f1afa9ef-ixp`, ModelVersion 12

Every row is derived from an explicit confusion matrix, so the numbers are
internally consistent rather than hand-picked:

| Field | `FieldId` | TP | FP | FN | F1 | Prec | Rec | `ErrorRate` | Docs | `Annotations` | `Quality` | Correct call |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Invoice Number | `aaaa000000000001` | 30 | 30 | 10 | 0.600 | 0.500 | 0.750 | 0.750 | 40 | 40 | average | **PRECISION** |
| Vendor Address | `aaaa000000000002` | 12 | 4 | 12 | 0.600 | 0.750 | 0.500 | 0.500 | 24 | 24 | average | **RECALL** |
| Bill-To Name | `aaaa000000000003` | 40 | 0 | 0 | 1.000 | 1.000 | 1.000 | 0.000 | 40 | 40 | good | no work needed |
| Freight Charge | `aaaa000000000004` | 4 | 0 | 1 | 0.889 | 1.000 | 0.800 | 0.200 | 5 | 5 | good | above target, tiny sample |

Project: `ProjectScore` 0.772 (the unweighted mean of the per-field `F1` values, matching the live API), `ProjectScoreQuality` `good`, `ValidatedDocuments` 40.

## What it discriminates

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

## Call log

Writes `mocks/calls.log` only, in the base mock's exact format (same `uip `
prefix, same CR/LF folding), so anchored `^uip\s+ixp …` criteria keep matching.
It does not write `mocks/calls.jsonl` — same as `mock_template_taxonomy`. Grade
these tasks from `calls.log`.
