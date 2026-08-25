# Jira Response Was Not Recognized As JSON - Server URL Truncation (R1)

This scenario reproduces a `Jira Scope` child-activity failure caused by a
`Server URL` that points past the instance root. The classic
`UiPath.Jira.Activities` pack appends its own `/rest/api/...` paths to
`Server URL`; with `/secure/Dashboard.jspa` (a Jira web UI page) appended, the
`Search Issues` REST call hits an HTML page and the pack fails with `Response was
not recognized as JSON`.

## What this scenario uncovers

**Root Cause:** The `Jira Scope` `Server URL` is
`https://acme.atlassian.net/secure/Dashboard.jspa` instead of the bare root
`https://acme.atlassian.net`. The scope authenticates fine; the child REST call
is mis-routed to an HTML page.

This maps to:
`references/activity-packages/jira-activities/playbooks/jira-scope-response-not-json-or-500.md`
sub-case **R1** (URL truncation - path appended past the root instance).

The logs show the session opened successfully (so this is **not** an
authentication failure), and the host is `*.atlassian.net` (Jira Cloud, so **not**
the on-prem Server / Data Center sub-case R2). The user is framed as **off-host**,
so the correct agent behavior is to tie the parse failure to the appended URL
path and recommend the root URL - not to attempt host commands.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a `Jira Scope` (Server URL with `/secure/Dashboard.jspa` appended) wrapping `Search Issues` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `jira-scope-response-not-json-or-500.md` (sub-case R1)
- Agent identified the `Server URL` truncation (a dashboard/page path appended
  past the root instance) as the cause - not an auth failure, not an on-prem
  endpoint issue - and recommended setting `Server URL` to the bare root
  `https://acme.atlassian.net`, without fabricating host actions
