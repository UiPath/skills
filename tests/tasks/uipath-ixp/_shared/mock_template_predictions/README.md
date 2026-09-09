# uipath-ixp predictions overlay

Serves `ixp labellings get-predictions` with a real envelope carrying
**`ModelVersion: 7`**, so a task can grade whether the agent PINS the version it
read (`confirm -m 7`) without the prompt ever naming it.

Used by `smoke/confirm_all_predictions.yaml`.

```yaml
sandbox:
  mock_path_dirs: [mocks]
  template_sources:
    - {type: template_dir, path: ../_shared/mock_template}
    - {type: template_dir, path: ../_shared/mock_template_predictions}
```

Second entry wins — this `uip` PATH-shadows the base mock's.

## What it answers

| Verb | Result |
|------|--------|
| `ixp labellings get-predictions <project> <doc>` | `Predictions[0]` with `ModelVersion: 7`, `DocumentId` echoed from `$5` (any document id works), one `Invoice Header` occurrence (Invoice Number, Total Amount) |
| `ixp labellings confirm …` | `PredictionsConfirmed: 2`, `ModelVersion: 7` |
| `ixp projects get` | project metadata |
| anything else | base behaviour — stderr + exit 1 |

Field ids match `mock_template_taxonomy`'s fixture, so the two overlays
describe the same project.

## Why `confirm` succeeds here

The other smoke tasks fail every command and grade command shape. That is fine
until the graded write depends on a value from a read: the read returns nothing,
and an agent that will not invent a version correctly stops instead — the trap
`../mock_template/README.md` closes with. This overlay removes it by answering
the read, so the only thing left to measure is whether the agent carried the
version into the write. Letting `confirm` fail would reintroduce a different
confound (is the agent meant to carry on after the write errors?).

## One sink

Like the other `/bin/sh` overlays this appends to `calls.log` only;
`calls.jsonl` keeps its seeded-empty content. Grade from `calls.log`.
