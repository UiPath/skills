# GSuite Get File Info Malformed URL Troubleshooting — Faithful Replay

This scenario replays a real `uipath-troubleshoot` investigation of a Faulted
Orchestrator job whose legacy UiPath.GSuite **Get File Info** activity threw a
**client-side** malformed-URL validation error — before any Google Drive API
call.

## What the original session uncovered

The user asked only *"why did my last job from folder Shared fail?"*. The agent:

1. Listed folders → resolved **Shared** to key `1965a46b-db4e-469e-aaaa-7e0b379cb34d`.
2. Listed Faulted jobs in Shared → newest is **DriveFileInspector**,
   job `0e3938d5-e2b0-480b-99d5-bcaf0e9123d6`.
3. Read the job's `Info` → a `System.ArgumentOutOfRangeException` thrown from
   `CloudObjectIdentifier.FromUrl` / `CreateFromUrlOrId` inside
   `UiPath.GSuite.Activities.GetFileInfo.ExecuteAsync`.

Conclusion: a **client-side input-validation** failure — the File ID input was
a malformed Drive URL (`https://drive.google.com/file/d/`, truncated, no
`<FILE_ID>` segment), so the activity threw *before* any request reached Google
Drive (no HTTP status, no API round-trip). *Not* a Google API, 404, connection,
auth, scope, throttling, outage, or transient fault. (Listing connections
confirms both GSuite connections serving Shared are Enabled and valid — a
defensive fixture reinforces that the connection is fine.)

## Client-side malformed-URL signature

```
System.ArgumentOutOfRangeException: Could not extract an object Id from the Url 'https://drive.google.com/file/d/'. (Parameter 'uri')
 at UiPath.GSuite.Models.CloudObjectIdentifier.FromUrl(Uri uri)
 at UiPath.GSuite.Models.CloudObjectIdentifier.CreateFromUrlOrId(String urlOrId)
 at UiPath.GSuite.Activities.GetFileInfo.ExecuteAsync(...)
```

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven dispatcher) |
| `fixtures/mocks/responses/*.json` | verbatim, scrubbed stdout from the real session's `.local/investigations/raw/` |
| `fixtures/mocks/responses/manifest.json` | first-match-wins dispatch table; both trace forms covered; `docsai ask` is passthrough |

CLI-driven — no `process/` snapshot; the root cause is fully contained in the
`or jobs get` `Info` field.

## Playbook validated

`skills/uipath-troubleshoot/references/activity-packages/gsuite-activities/playbooks/invalid-or-null-input.md`
(legacy `GetFileInfo` malformed-URL signature; also referenced from
`drive-file-not-found.md` and `overview.md`).
