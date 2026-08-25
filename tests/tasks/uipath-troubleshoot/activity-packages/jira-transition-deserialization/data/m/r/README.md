# Transition Workflow Fails - Metadata Deserialization Bug in an Old Pack (T4)

This scenario reproduces a Jira transition workflow that faults with a
`Newtonsoft.Json.JsonSerializationException: Error converting value "add" to type
'Atlassian.Jira.IssueFieldEditMetadataOperation'` while `Get Transitions` parses
the transition field metadata. The project pins an **old**
`UiPath.Jira.Activities` version (`1.5.0`) with a known metadata-deserialization
bug on complex fields (here a custom field with an `operations` array).

## What this scenario uncovers

**Root Cause:** A version-bound deserialization bug. The workflow is configured
correctly (dynamic `Get Transitions`, valid auth/URL), but `UiPath.Jira.Activities
[1.5.0]` cannot map the complex field metadata to its
`Atlassian.Jira.IssueFieldEditMetadataOperation` type.

This maps to:
`references/activity-packages/jira-activities/playbooks/jira-transition-issue-failures.md`
sub-case **T4** (deserialization / package-version type mismatch; upgrade the
pack or migrate to the Integration Service connector).

The scope authenticates fine (so this is **not** an auth failure), the error is a
JSON type-conversion exception rather than `Field '<name>' is required` (**not**
T1) or `Transition '<id>' is not valid` (**not** T2), and it is not a
rule/permission denial (**not** T3). The workflow even uses the correct dynamic
`Get Transitions` pattern, isolating the cause to the package version. The user
is framed as **off-host**, so the correct agent behavior is to tie the
deserialization error to the old pack version and recommend upgrading (or
migrating to Integration Service) - not to attempt host commands.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project pinning `UiPath.Jira.Activities [1.5.0]`, with a `Jira Scope` -> `Get Transitions` -> `Transition Issue` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `jira-transition-issue-failures.md` (sub-case T4)
- Agent identified the old-package metadata-deserialization bug
  (`IssueFieldEditMetadataOperation`) as the cause (not a missing field, invalid
  ID, or permission/validator) and recommended upgrading `UiPath.Jira.Activities`
  to a current release or migrating to the Integration Service Jira connector,
  without fabricating host actions
