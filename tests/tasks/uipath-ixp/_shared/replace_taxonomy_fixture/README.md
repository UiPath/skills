# uipath-ixp replace-taxonomy fixture

Stages `new-taxonomy.json` at the sandbox root for tasks that hand the agent a
taxonomy file and ask for the project to match it. Overlay it alongside
[`mock_template`](../mock_template/README.md) and
[`mock_template_taxonomy`](../mock_template_taxonomy/README.md), whose
`get-taxonomy` serves the project state this file is a diff against:

```yaml
sandbox:
  mock_path_dirs: [mocks]
  template_sources:
    - {type: template_dir, path: ../_shared/mock_template}
    - {type: template_dir, path: ../_shared/mock_template_taxonomy}
    - {type: template_dir, path: ../_shared/replace_taxonomy_fixture}
```

## What the file is

`new-taxonomy.json` is the `{ entity_defs, label_groups }` import format — what
`projects get-taxonomy | jq .Data.dataset` produces, i.e. exactly the shape a
user lands on after dumping a taxonomy and hand-editing it.

It carries the **same `field_id`s** as the live fixture taxonomy. That is what
makes the two differences legible as an edit rather than a new taxonomy:

| vs. the project's current taxonomy | Difference | Targeted command |
|---|---|---|
| `Invoice Header` / `Total Amount` → `Invoice Total` (`field_id` `6e0b74a1f83c2d95` unchanged) | rename | `fields rename` |
| `Line Items` / `Purchase Order Number` (`field_id` `2f6b8d04e71a9c53`) | added | `fields add` |

Nothing is removed, so the whole diff is reachable with non-destructive
commands and "apply the file" has one unambiguous correct path.

## Why the rename is the point

`import-taxonomy` merges and ignores the file's `field_id`, so importing this
file mints a **new** field called `Invoice Total` and leaves `Total Amount`
exactly where it was — two fields where the user asked for one renamed. The
import reports `{"status":"ok"}`, which is what makes it worth grading against
(SKILL.md Critical Rule 22).

## Constraints

Contains no `mocks/` directory, so it can be listed in any order relative to
the mock templates without shadowing their `uip`. Keep the `field_id` values in
sync with `mock_template_taxonomy/mocks/uip` — a mismatch turns the graded
rename into an add plus an orphan.
