# Replace Text Failure - Multi-line Replacement Collapses / Loses Formatting

This scenario reproduces a `Replace Text` formatting issue where a
multi-line address built with `Environment.NewLine` collapses to a single
line / loses formatting in the output. The job completes **Successfully**.

## What this scenario uncovers

**Root Cause:** The `Replace` value is `String.Join(Environment.NewLine,
...)`. `Replace Text` inserts the text as a flat run, so OS line breaks do
not become Word paragraph breaks — the address collapses to one line. The
match succeeds (1 occurrence), so the job is Successful; only the layout is
wrong. Not a template, Search-value, or package problem.

This maps to:
`references/activity-packages/word-activities/playbooks/replace-text-multiline-formatting.md`

The correct agent behavior is to recognize a **Successful job with wrong
layout** as a real issue, tie it to `Environment.NewLine` in the `Replace`
expression, and recommend Bookmarks / Form Fields + `Set Bookmark Text` (or
object-model paragraph breaks) — not blaming the template/package or
dismissing the green job.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `Replace Text` with a `Replace` value built via `String.Join(Environment.NewLine, ...)` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** No faulted job (State=Successful) and no error logs;
> the trace shows the replacement succeeded (`Replaced 1 occurrence`). The
> agent diagnoses from the `Environment.NewLine` `Replace` expression in
> `Main.xaml` + the user's layout symptom — there is no error to grep.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `replace-text-multiline-formatting.md`
- Agent identified raw `Environment.NewLine` in the `Replace` value as the
  cause and recommended Bookmarks / Form Fields + `Set Bookmark Text` (or
  object-model paragraph breaks; keeping `Replace Text` plain) — without
  treating the green job as healthy or blaming the template/package
