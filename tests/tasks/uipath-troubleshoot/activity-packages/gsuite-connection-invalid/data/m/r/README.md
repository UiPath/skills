# GSuite Connection-Invalid Troubleshooting — Faithful Replay

This scenario replays a real `uipath-troubleshoot` investigation of a Faulted
Orchestrator job whose UiPath.GSuite **Download File** activity referenced an
Integration Service connection that could not be resolved or authorized.

## What the original session uncovered

The user asked only *"why did my last job from folder Shared fail?"*. The agent:

1. Listed folders → resolved **Shared** to key `1965a46b-db4e-469e-aaaa-7e0b379cb34d`.
2. Listed Faulted jobs in Shared → newest is **WorkspaceSheetSync**,
   job `4e00b4ca-b35b-4457-bb12-74f270d20cb0`.
3. Read the job's `Info` → a `UiPath.GSuite.Exceptions.GSuiteException`
   wrapping `ConnectionHttpException`, thrown from `GetAccessToken` at OAuth
   token acquisition — **before** any Google Drive call.

Conclusion: an Integration Service **connection-resolution / authorization**
failure — the referenced connection `00000000-1111-2222-3333-444444444444` is
invalid or not accessible to the running identity — *not* a Drive 404, bad
input, throttling, transient, or timeout fault. Listing connections corroborates
this: both real GSuite connections serving Shared are Enabled, and the bogus id
the activity references is not among them.

## Connection-invalid signature

```
UiPath.GSuite.Exceptions.GSuiteException: Connection [00000000-1111-2222-3333-444444444444] is invalid or you do not have access to it
 ---> UiPath.ConnectionClient.Contracts.ConnectionHttpException: Connection [00000000-1111-2222-3333-444444444444] is invalid or you do not have access to it
   at UiPath.ConnectionClient.ConnectionClient.GetAccessToken(...)
```

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven dispatcher) |
| `fixtures/mocks/responses/*.json` | verbatim, scrubbed stdout from the real session's `.local/investigations/raw/` |
| `fixtures/mocks/responses/manifest.json` | first-match-wins dispatch table; `docsai ask` is passthrough |

CLI-driven — no `process/` snapshot; the root cause is fully contained in the
`or jobs get` `Info` field.

## Playbook validated

`skills/uipath-troubleshoot/references/activity-packages/gsuite-activities/playbooks/connection-and-auth-failures.md`
