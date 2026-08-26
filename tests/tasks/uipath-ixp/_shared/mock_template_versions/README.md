# uipath-ixp version-serving smoke mock

Overlay for smoke tasks whose correct path must resolve **which model version a
score belongs to** before reading the score. List it SECOND in
`template_sources` so it wins over the base mock:

```yaml
sandbox:
  mock_path_dirs: [mocks]
  template_sources:
    - {type: template_dir, path: ../_shared/mock_template}
    - {type: template_dir, path: ../_shared/mock_template_versions}
```

## Why it exists

`get-metrics` defaults to the **latest trained** version, which is routinely not
the **published/live** one (SKILL.md Critical Rule 21). The base mock fails every
invocation, so a task testing that rule is unwinnable on it: the correct path
reads `list-models` for the live version and carries it into `get-metrics -m <N>`,
and a failing read leaves nothing to carry.

## Fixture — project `my_invoices-f1afa9ef-ixp`

| Version | State | `ProjectScore` | `TrainedTime` |
|---------|-------|----------------|---------------|
| 30 | latest trained, not published | 0.91 | 2026-08-06 |
| 9 | published, tagged `live` | 0.98 | 2026-07-24 |

The live version scores **higher** than the latest. That inversion is deliberate:
a bare `get-metrics` returns 0.91 — a plausible number belonging to a version
nobody deployed — so the correct and incorrect paths differ in the graded
**artifact**, not merely in command shape.

`get-metrics` accepts `-m N`, `--model-version N`, and `--model-version=N`, in
either order relative to the positional project name. `latest` and `30` return
version 30; an unknown version returns the `not_found` failure envelope; every
other verb fails offline like the base mock.

## Call log

Writes `mocks/calls.log` only, in the base mock's exact format (same `uip `
prefix, same CR/LF folding), so anchored `^uip\s+ixp …` criteria keep matching.
It does not write `mocks/calls.jsonl` — same as `mock_template_taxonomy`. Grade
these tasks from `calls.log`.
