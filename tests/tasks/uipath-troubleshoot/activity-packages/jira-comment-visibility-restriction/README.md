# Add Comment Fails - Comment Visibility Restriction (C4)

This scenario reproduces an `Add Comment` failure caused by a misconfigured
comment `Visibility`. The activity restricts the comment to the project role
`Service Desk Team`, which the bot account is not a member of, so Jira rejects it
with `400 (Bad Request): You are currently not a member of the project role
'Service Desk Team' that you are restricting the comment visibility to`.

## What this scenario uncovers

**Root Cause:** `Add Comment` sets `VisibilityType="Role"` /
`VisibilityValue="Service Desk Team"`. Jira requires the commenting account to
belong to the role/group a restricted comment targets; the bot account does not,
and the user only wants a public comment.

This maps to:
`references/activity-packages/jira-activities/playbooks/jira-add-comment-failures.md`
sub-case **C4** (comment Visibility restriction).

The scope authenticates fine (so this is **not** an auth failure), the status is
`400` about a visibility role rather than `404` (**not** the C2 bad-key case) or a
blanket `403` (**not** the C3 missing-permission case). The user confirms a normal
public comment is fine. The user is framed as **off-host**, so the correct agent
behavior is to tie the rejection to the `Visibility` restriction and recommend
clearing it - not to attempt host commands.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a `Jira Scope` -> `Add Comment` that sets `VisibilityType="Role"` / `VisibilityValue="Service Desk Team"` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `jira-add-comment-failures.md` (sub-case C4)
- Agent identified the misconfigured comment `Visibility` restriction (a project
  role the account is not in) as the cause (not an auth failure, a bad IssueKey,
  or a missing Add Comments permission) and recommended clearing `Visibility` for
  a public comment (or setting a role/group the account belongs to), without
  fabricating host actions
