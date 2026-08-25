# Replace Text Failure - Silent No-Substitution (Run-Split Placeholder)

This scenario reproduces a **silent** `Replace Text` failure: the job
completes **Successfully** but the `[Name]` placeholder is left unchanged in
the output, because the token is split across Word's internal XML runs in
the template and the exact-string search matches nothing.

## What this scenario uncovers

**Root Cause:** The `[Name]` placeholder in the template was edited in place,
so Word fragmented it across multiple `<w:t>` runs. `Replace Text` searches
for the contiguous `[Name]`, matches zero occurrences, and replaces nothing
— the job reports success (matching nothing is not an error). The trace log
`Replaced 0 occurrence(s) of '[Name]'` is the diagnostic tell.

This maps to:
`references/activity-packages/word-activities/playbooks/replace-text-silent-no-substitution.md`

The correct agent behavior is to recognize a **Successful job with wrong
output** as a silent failure (not dismiss it because the job is green), tie
it to run-splitting via the "0 occurrences" log, and recommend retyping the
placeholder cleanly in one run or doing the substitution in code.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `Replace Text` searching for `[Name]` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** There are **no faulted jobs** and **no error logs** —
> the job is `Successful`. The agent must broaden from a faulted-jobs query
> to the successful job and read the `Replaced 0 occurrence(s) of '[Name]'`
> trace line as the signal. This tests whether the agent treats a green job
> with wrong output as a real failure.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `replace-text-silent-no-substitution.md`
- Agent identified the run-split placeholder (exact-string search matching
  nothing on a Successful job) as the cause and recommended retyping the
  placeholder cleanly in one run and/or an in-code string/regex replace —
  without treating the green job as healthy or fabricating a crash/lock
