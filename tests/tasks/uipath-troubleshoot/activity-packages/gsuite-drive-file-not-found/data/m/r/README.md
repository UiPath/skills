# GSuite Drive File-Not-Found Troubleshooting — Faithful Replay

This scenario replays a real `uipath-troubleshoot` investigation of a Faulted
Orchestrator job whose UiPath.GSuite **Download File** activity hit a Google
Drive **404**.

## What the original session uncovered

The user asked only *"why did my last job from folder Shared fail?"*. The agent:

1. Listed folders → resolved **Shared** to key `1965a46b-db4e-469e-aaaa-7e0b379cb34d`.
2. Listed Faulted jobs in Shared → newest is **DriveDocSync**,
   job `f41ed418-163b-487b-8077-e51f8af4a1af`.
3. Read the job's `Info` → a `UiPath.GSuite.Exceptions.GSuiteException`
   wrapping `Google.GoogleApiException` with **HttpStatusCode NotFound** and
   `File not found: 1AbCnonexistentFILEid000000000000000.` thrown from
   `DownloadFileConnections`.

Conclusion: a Google Drive **404 / resource-resolution** failure on the
configured file id — *not* a connection, auth, scope, throttling, or transient
fault. (Listing connections confirms both GSuite connections serving Shared are
Enabled and valid — a defensive fixture reinforces that the connection is fine.)

## 404 signature

```
Google.GoogleApiException: The service drive has thrown an exception.
HttpStatusCode is NotFound. File not found: 1AbCnonexistentFILEid000000000000000.
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

`skills/uipath-troubleshoot/references/activity-packages/gsuite-activities/playbooks/drive-file-not-found.md`
