# Replace Text Failure - Placeholder Consumed After First Loop Iteration

This scenario reproduces a `Replace Text` loop failure where the workflow
edits the template **in place** each iteration, so the first row consumes
the `[Name]` placeholder and every later row comes out unchanged. The job
completes **Successfully** with no error.

## What this scenario uncovers

**Root Cause:** The `For Each` loop's `Use Word File` scope points at the
template and saves it in place every iteration. Iteration 1 replaces
`[Name]` and persists it, so the placeholder no longer exists; iterations
2+ replace 0 occurrences. The per-iteration trace `Replaced 1` → `Replaced
0` → `Replaced 0` is the diagnostic tell. Distinct from
`replace-text-silent-no-substitution` (run-split, fails row 1 too) and
`replace-text-file-locked` (Auto Save `IOException`).

This maps to:
`references/activity-packages/word-activities/playbooks/replace-text-loop-template-overwrite.md`

The correct agent behavior is to recognize a **Successful job with wrong
output on rows 2+** as a silent failure, tie it to in-place template editing
via the 1→0 logs, and recommend a fresh `Copy File` per iteration — not
dismiss the green job or blame a crash/lock.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `For Each` → `Use Word File` (`AutoSave`) on the template, `Replace Text in Document`, no Copy File |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** No faulted job (State=Successful) and no error logs;
> the full job log carries the per-iteration `Replaced 1` → `Replaced 0`
> trace. The agent must broaden from a faulted-jobs query to the successful
> job and read the 1→0 pattern as the signal.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `replace-text-loop-template-overwrite.md`
- Agent identified in-place template editing consuming the placeholder after
  iteration 1 as the cause and recommended a fresh `Copy File` per iteration
  (template read-only) — without treating the green job as healthy or
  fabricating a crash/lock
