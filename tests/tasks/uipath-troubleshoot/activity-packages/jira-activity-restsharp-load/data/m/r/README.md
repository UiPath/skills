# Jira Activity Could Not Be Loaded - RestSharp Dependency Conflict

This scenario reproduces a `Jira Scope` job that faults at **activity load** with
a `System.IO.FileLoadException` on **RestSharp** (manifest definition does not
match the assembly reference, `HRESULT 0x80131040`). The legacy
`UiPath.Jira.Activities` pack pins `RestSharp 106.x`; a second package in the
project (`UiPath.WebAPI.Activities`) pulls a newer RestSharp, so the assembly
loaded at runtime no longer matches the Jira pack's reference and the activity
cannot bind.

## What this scenario uncovers

**Root Cause:** A transitive RestSharp version conflict. `project.json` depends on
both `UiPath.Jira.Activities` `[1.9.4]` and `UiPath.WebAPI.Activities` `[1.20.2]`;
only one RestSharp loads, and it is not the `106.15.0.0` the Jira pack was built
against.

This maps to:
`references/activity-packages/jira-activities/playbooks/jira-activity-missing-or-not-loaded.md`

The fault is an assembly **load** failure at the scope, before authentication or
any REST call — so the authentication and response/URL families are explicitly
ruled out. The user reports it began after adding a second package, the classic
shared-dependency-collision signature. The user is framed as **off-host**, so the
correct agent behavior is to tie the load error to the RestSharp conflict in
`project.json` and recommend resolving the pin or migrating to the Integration
Service Jira connector - not to attempt host commands.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a `Jira Scope` -> `Create Issue` and a `project.json` depending on both `UiPath.Jira.Activities` and `UiPath.WebAPI.Activities` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `jira-activity-missing-or-not-loaded.md`
- Agent identified a transitive RestSharp version conflict between the Jira pack
  and another package (not a credential, URL, or Jira-side problem) and
  recommended resolving the version conflict or migrating to the Integration
  Service Jira connector, without fabricating host actions
