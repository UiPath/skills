# uipath-ixp replace-taxonomy fixture

Stages `new-taxonomy.json` at the sandbox root for tasks that hand the agent a
taxonomy file and ask for the project to match it. Contains no `mocks/` — the
consuming task declares `sandbox.record_cli` and lets the framework generate
its recorders:

```yaml
sandbox:
  template_sources:
    - {type: template_dir, path: ../_shared/replace_taxonomy_fixture}
  record_cli:
    - tool: uip
      responses:
        - when: {verb: "ixp projects get-taxonomy"}
          exit_code: 0
          stdout: '…the project taxonomy this file is a diff against…'
```

## What the file is

`new-taxonomy.json` is the `{ entity_defs, label_groups }` import format — what
`projects get-taxonomy | jq .Data.dataset` produces, i.e. exactly the shape a
user lands on after dumping a taxonomy and hand-editing it.

It carries the **same `field_id`s** as the taxonomy the task's response rule
serves. That is what makes the two differences legible as an edit rather than a
new taxonomy:

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

Keep the `field_id` values in sync with the taxonomy the consuming task serves
from its `get-taxonomy` response rule — a mismatch turns the graded rename into
an add plus an orphan, and the task would grade a different behavior than it
describes. The old field name (`Total Amount`) must appear **only** in that
served response, never in this file or the prompt: a graded rename that asserts
the old name is what proves the agent diffed rather than applied the file
wholesale.
