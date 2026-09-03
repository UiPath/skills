# uipath-ixp metrics- and deployment-serving mock

Overlay for the **diagnose** smoke tasks under `../../smoke/`. Overlays the base
[`mock_template`](../mock_template/README.md) — list it SECOND so its
`mocks/uip` wins:

```yaml
sandbox:
  mock_path_dirs: [mocks]
  template_sources:
    - {type: template_dir, path: ../_shared/mock_template}
    - {type: template_dir, path: ../_shared/mock_template_drift}
```

## Why it exists

The base mock fails every invocation, and a diagnose task cannot be graded on
that. Diagnosis *is* reading real numbers, concluding which field or version is
at fault, and acting on the conclusion. With every read failing there is nothing
to reason from, and an agent that correctly declines to invent metrics stops —
graded as a fail. `mock_template_taxonomy` does not help here: it serves the
taxonomy but neither metrics nor deployment snapshots.

## Fixture

Project `my_invoices-f1afa9ef-ixp`, latest trained version **15** (tagged `live`).

| Source | Field group | Fields |
|---|---|---|
| `projects get-taxonomy` (current) | `Invoice Header` | Invoice Number, Invoice Date, Total Amount, Vendor Name, **Withholding Tax** |
| `deployments get-taxonomy --version 15` | `Invoice Header` | Invoice Number, Invoice Date, Total Amount, Vendor Name |
| `deployments get-taxonomy --version 14` | `Invoice Header` | Invoice Number, Invoice Date, Vendor Name |
| `projects get-metrics` (v15) | `Invoice Header` | 4 scored fields; **Vendor Name F1 0.34**, every other ≥ 0.93 |

Served: `projects list-models`, `projects get-metrics`, `projects get-taxonomy`,
`deployments get-taxonomy`. Everything else falls through to the base mock's
offline failure, so a task can still guard against unwanted verbs.

### `--version` is honored

`deployments get-taxonomy` reads `--version` in both forms (`--version N`,
`--version=N`) and answers differently per version: **15** is the as-trained
snapshot for the live model, **14** drops `Total Amount` as well, an unknown
version returns `ErrorCode: not_found`, and omitting the flag returns
`ErrorCode: missing_argument` — the real CLI requires it.

Comparing against v14 tells a visibly different story — two fields missing —
which cannot explain why *only* withholding tax comes back empty.

### `Withholding Tax` is unscored, not healthy

It has **no row at all** in `get-metrics`: it did not exist when v15 trained.
Anything describing it as "already scoring well" is false, and a guard forbidding
its re-instruction punishes the D10 reading of this same fixture. That is why
`diagnose_low_f1_field.yaml`'s guard lists only the three fields that genuinely
score ≥ 0.93.

### `Pinned: true` on version 15

The three signals the skill reads to find the published version agree:
`Pinned: true`, `Tags[] live=15`, `MaxPublished: 15` (SKILL.md:80).
Version 14 is unpinned: trained, never published.

## The two diagnoses it supports

One fixture, two independent and unambiguous root causes:

- **D9 — which field is dragging quality?** → `Vendor Name`. Metrics carry
  **no field name**, only `Fields[].FieldId`, so the answer is reachable only by
  joining that id against the taxonomy's `moon_form[].field_id`. An agent that
  skips the taxonomy read cannot name the field, and one that guesses from the
  prompt has nothing to guess from. Its `instructions` in the fixture are
  deliberately threadbare (`"The vendor."`) — the cause of the low score and the
  thing a fix must replace.
- **D10 — why does the live model never return withholding tax?** → the field
  exists in the project taxonomy but not in the snapshot v15 was trained on. The
  fix is to retrain/republish so a new version picks the field up; adding the
  field again is the wrong move (it already exists, and `import-taxonomy` merges
  rather than replaces, so re-posting it silently duplicates).

Both fields are scored/absent independently, so a task can target one without
the other becoming ambiguous.

## Constraints

`get-taxonomy` here is **stateless** — unlike `mock_template_taxonomy`, no task
using this overlay mutates the taxonomy and re-reads it. If one ever does, port
that overlay's marker-file approach rather than adding hidden state here.

Logging matches the base mock exactly — same `uip ` prefix, same newline
normalization — so anchored `^uip\s+ixp …` criteria keep matching. Change one
and change both. `mocks/uip` must stay mode `755`.

**One sink only.** This overlay is `/bin/sh` and writes `calls.log` alone, so
while it is active `calls.jsonl` keeps just the base template's seeded-empty
content — **a task on this overlay cannot be graded from `calls.jsonl`.**
Deliberate: the base mock is Python precisely because sh cannot emit correct JSON
without hand-rolled escaping, and a subtly-wrong `argv` record is worse than none.
Grade from `calls.log`, or port this overlay to Python first — see
[`mock_template_occurrence`](../mock_template_occurrence/README.md), which is
Python and writes both sinks plus its own `resolved.log`.

Do NOT assert static text in `mocks/uip`; grade CLI behavior from `calls.log`.
Log-based negative guards MUST pair with a positive control — a log line a
correct run is guaranteed to produce — or re-pointing the sink makes every
negative guard pass vacuously.
