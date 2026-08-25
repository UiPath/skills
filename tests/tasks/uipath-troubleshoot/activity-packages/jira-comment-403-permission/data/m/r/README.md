# Add Comment Fails - 403 Forbidden / Missing Add Comments Permission (C3)

This scenario reproduces an `Add Comment` failure caused by the bot account
lacking the **Add Comments** permission in the project. The Jira Scope
authenticates and the issue is located, but Jira rejects the comment with `403
(Forbidden): You do not have permission to comment on this issue` - the account
is authenticated but not authorized for this action.

## What this scenario uncovers

**Root Cause:** `rpa-bot@company.com` authenticated successfully (valid API
token) but is not in a group / project role mapped to **Add Comments** in the
target project's permission scheme, so the comment is rejected with `403`.

This maps to:
`references/activity-packages/jira-activities/playbooks/jira-add-comment-failures.md`
sub-case **C3** (403 Forbidden / missing project permission).

The key discriminator is `403` (authenticated, not authorized) vs `401` /
`Authentication information is invalid` (an auth failure). The `IssueKey`
(`OPS-1502`) is well-formed and reading works, so this is **not** the C2
bad-key/`404` case; no `Visibility` is set, so it is **not** C4. The user is
framed as **off-host** and is not a Jira admin, so the correct agent behavior is
to identify the missing project permission and hand the user a precise admin
request - not to attempt host commands or workflow edits.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a `Jira Scope` -> `Add Comment` on a well-formed `IssueKey` (no Visibility set) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `jira-add-comment-failures.md` (sub-case C3)
- Agent identified the missing **Add Comments** project permission for the
  authenticated bot account as the cause (not an invalid credential, a bad
  IssueKey, or a visibility issue) and recommended having a Jira administrator
  grant the permission (verifiable by commenting manually as the service
  account), without fabricating host actions
