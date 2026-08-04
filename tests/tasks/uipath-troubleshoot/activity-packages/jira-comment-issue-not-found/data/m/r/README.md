# Add Comment Fails - Issue Not Found / IssueKey Missing Project Prefix (C2)

This scenario reproduces an `Add Comment` failure caused by a malformed
`IssueKey`. The activity passes `1450` (a bare number) instead of the full Jira
key `OPS-1450`, so Jira returns `404 (Not Found) - Issue Not Found` and the
comment is never posted.

## What this scenario uncovers

**Root Cause:** `Add Comment` has `IssueKey="1450"` - missing the `PROJECT-`
prefix. Jira keys are `PROJECT-NNN`; a bare number does not resolve to an issue.

This maps to:
`references/activity-packages/jira-activities/playbooks/jira-add-comment-failures.md`
sub-case **C2** (Issue Not Found / bad IssueKey format).

The scope authenticates fine (so this is **not** an auth failure), the status is
`404` rather than `403` (**not** the C3 permission case), and no `Visibility` is
configured (**not** C4). The user confirms the issue exists (browser URL
`.../browse/OPS-1450`), isolating the cause to the prefix-less key. The user is
framed as **off-host**, so the correct agent behavior is to tie the 404 to the
malformed `IssueKey` and recommend passing the full key - not to attempt host
commands.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a `Jira Scope` -> `Add Comment` using `IssueKey="1450"` (no project prefix) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `jira-add-comment-failures.md` (sub-case C2)
- Agent identified the malformed `IssueKey` (missing the `PROJECT-` prefix) as
  the cause (not an auth failure, a 403 permission problem, or a visibility
  issue) and recommended passing the full issue key including the prefix, without
  fabricating host actions
