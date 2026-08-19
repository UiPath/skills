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

| Field | `FieldId` | F1 | Prec | Rec | `ErrorRate` | Docs | `Annotations` | `Quality` | Correct call |
|---|---|---|---|---|---|---|---|---|---|
| Invoice Number | `aaaa000000000001` | 0.60 | 0.45 | 0.95 | 0.55 | 40 | 40 | average | **PRECISION** |
| Vendor Address | `aaaa000000000002` | 0.60 | 0.95 | 0.45 | 0.05 | 40 | 40 | average | **RECALL** |
| Bill-To Name | `aaaa000000000003` | 1.00 | 1.00 | 1.00 | 0.00 | 40 | 40 | good | no work needed |
| Freight Charge | `aaaa000000000004` | 0.889 | 0.80 | 1.00 | 0.20 | 5 | 5 | good | above target, tiny sample |

Project: `ProjectScore` 0.77, `ProjectScoreQuality` `good`, `ValidatedDocuments` 40.

## What it discriminates

**Invoice Number and Vendor Address carry the same `F1` and need opposite
rewrites.** An agent reading only `F1` cannot tell them apart and must guess; one
reading the `Precision`/`Recall` split gets both right. That is the point of the
fixture — the two paths differ in the graded artifact, not in command shape.

Two further traps, both faithful to real API behaviour:

- **`ErrorRate` is exactly `1 - Precision`** on every row. It is not a second
  opinion on precision and must not be diagnosed from.
- **Field `Quality` and `ProjectScoreQuality` do not share a scale.** Bill-To
  Name has `F1` 1.00 yet reads `good`, the same label the project earns at 0.77.
  An agent gating on the label rather than the number flags a perfect field.

`get-taxonomy` is served so field ids resolve to names; graded artifacts are
keyed by field id, which needs no join.

## Call log

Writes `mocks/calls.log` only, in the base mock's exact format (same `uip `
prefix, same CR/LF folding), so anchored `^uip\s+ixp …` criteria keep matching.
It does not write `mocks/calls.jsonl` — same as `mock_template_taxonomy`. Grade
these tasks from `calls.log`.
