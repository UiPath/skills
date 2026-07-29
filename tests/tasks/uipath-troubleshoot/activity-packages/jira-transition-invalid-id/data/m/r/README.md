# Transition Issue Fails - Hardcoded / Invalid Transition ID (T2)

This scenario reproduces a `Transition Issue` failure caused by a **hardcoded
transition ID** that is not legal from the ticket's current status. Jira
transition IDs are per-status edges, not global constants, so a literal
`TransitionId="31"` that worked from one status is rejected (`400 Bad Request:
Transition id '31' is not valid ...`) once a ticket starts from a different
status.

## What this scenario uncovers

**Root Cause:** `Transition Issue` uses a hardcoded `TransitionId="31"` with no
`Get Transitions` call. The failing issue (`OPS-1421`) is in status `In Review`,
which has no transition with ID 31.

This maps to:
`references/activity-packages/jira-activities/playbooks/jira-transition-issue-failures.md`
sub-case **T2** (invalid / outdated transition ID; resolve dynamically via Get
Transitions).

The scope authenticates fine (so this is **not** an auth failure), the error is
`is not valid` rather than `is required` (**not** the T1 missing-field case), it
is a routing rejection rather than a rule/permission denial (**not** T3), and
there is no `IssueFieldEditMetadataOperation` conversion error (**not** T4). The
user is framed as **off-host**, so the correct agent behavior is to tie the
rejection to the hardcoded ID and recommend resolving it via `Get Transitions` -
not to attempt host commands.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a `Jira Scope` -> `Transition Issue` using a hardcoded `TransitionId="31"` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `jira-transition-issue-failures.md` (sub-case T2)
- Agent identified the hardcoded/invalid transition ID for the issue's current
  status as the cause (not a missing required field, permission/validator, or
  deserialization bug) and recommended resolving the transition ID dynamically
  via `Get Transitions`, without fabricating host actions
