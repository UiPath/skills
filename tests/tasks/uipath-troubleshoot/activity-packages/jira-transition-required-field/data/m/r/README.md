# Transition Issue Fails - Required Field on the Transition Screen (T1)

This scenario reproduces a `Transition Issue` failure caused by a **mandatory
field on the transition screen** not being supplied. The `Done` transition has a
screen that requires `Resolution`; the activity moves the status without it, so
Jira rejects the call with `400 (Bad Request)` and
`{"errors":{"resolution":"Field 'resolution' is required"}}`.

## What this scenario uncovers

**Root Cause:** `Transition Issue` moves `OPS-1530` to `Done` but supplies no
field values, and the `Done` transition screen requires `Resolution`.

This maps to:
`references/activity-packages/jira-activities/playbooks/jira-transition-issue-failures.md`
sub-case **T1** (required field on the transition screen not supplied; use Get
Transitions / Update Issue first).

The scope authenticates fine (so this is **not** an auth failure), the error
names a required field rather than `is not valid` (**not** the T2 invalid-ID
case), it is a field-validation rejection rather than a rule/permission denial
(**not** T3), and there is no `IssueFieldEditMetadataOperation` conversion error
(**not** T4). "Closing by hand works" because the Jira UI prompts for the
resolution. The user is framed as **off-host**, so the correct agent behavior is
to tie the rejection to the missing required field and recommend supplying it -
not to attempt host commands.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a `Jira Scope` -> `Transition Issue` to `Done` with no field values |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `jira-transition-issue-failures.md` (sub-case T1)
- Agent identified a required transition-screen field (`resolution`) not being
  supplied as the cause (not an invalid transition ID, permission/validator, or
  deserialization bug) and recommended supplying the field via `Get Transitions`
  or `Update Issue` before the transition, without fabricating host actions
