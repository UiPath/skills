# Replace Text Failure - 256-Character Input Limit

This scenario reproduces a classic `Replace Text` (`WordReplaceText`)
failure where the `Replace` value exceeds the classic activity's hard
256-character limit, faulting with `System.ArgumentException: Value cannot
be longer than 256 characters`.

## What this scenario uncovers

**Root Cause:** Classic `Replace Text` caps `Search`/`Replace` inputs at
256 characters. The replacement clause is longer, so the activity throws
`ArgumentException` on the `Replace` parameter. Shorter clauses pass; the
project pins an older `UiPath.Word.Activities` version where the cap
applies. The document opens fine — the fault is purely the input length.

This maps to:
`references/activity-packages/word-activities/playbooks/replace-text-length-limit.md`

The correct agent behavior is to tie the `ArgumentException` to the 256-char
classic cap and recommend either upgrading `UiPath.Word.Activities` or doing
the substitution via `String.Replace` / regex in code — not editing the
template or blaming Word.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; classic `Replace Text` with a long `Replace` value, pinning `UiPath.Word.Activities [1.7.0]` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** The logs show the document opening successfully
> (`Document ... opened`) before the `ArgumentException`, locating the fault
> at the substitution input rather than at file access or COM.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `replace-text-length-limit.md`
- Agent identified the 256-character classic input limit as the cause and
  recommended upgrading the package or substituting via string/regex in code
  — without editing the template or fabricating actions
