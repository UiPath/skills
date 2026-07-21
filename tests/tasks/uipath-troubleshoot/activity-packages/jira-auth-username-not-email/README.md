# Jira Scope Authentication Failure - Username Is an accountId, Not the Email (A2)

This scenario reproduces a `Jira Scope` authentication failure caused by the
`Username` being set to an alphanumeric Jira Cloud **accountId** instead of the
account **email**. Jira Cloud authenticates API-token calls against the account
email; an `accountId` there is rejected at scope open with `Authentication
information is invalid. Please check your credentials and try again.`

## What this scenario uncovers

**Root Cause:** The `Jira Scope` `Username` is `557058:9d8c7b6a-1f2e-4a3b-bc01-aabbccddeeff`
(a Jira `accountId`) rather than the account email. Every other auth property is
valid, so Atlassian rejects only the username identity.

This maps to:
`references/activity-packages/jira-activities/playbooks/jira-scope-authentication-failures.md`
sub-case **A2** (username must be the account email).

The project isolates A2 by ruling out the sibling sub-cases: the `Api Token` is a
`SecureString` in-argument (not a plain `String`, so **not A1**), there is no
`Client Id` / `Client Secret` (**not A3**), and `Authentication Type = Api Token`
rather than basic password auth (**not A4**). The user is framed as **off-host**,
so the correct agent behavior is to tie the auth failure to the username format
and recommend the email - handing the user the Atlassian-side confirmation, not
attempting host commands.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a `Jira Scope` (Api Token auth, SecureString token, accountId username) wrapping `Search Issues` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `jira-scope-authentication-failures.md` (sub-case A2)
- Agent identified the `Username` being a Jira `accountId` instead of the account
  email as the cause (not a bad token, leftover OAuth params, or an MFA blocker)
  and recommended setting `Username` to the account email, without fabricating
  host actions
