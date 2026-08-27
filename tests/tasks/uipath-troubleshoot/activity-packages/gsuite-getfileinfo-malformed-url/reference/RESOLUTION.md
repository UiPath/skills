# Resolution — DriveFileInspector (Shared)

## Fault
The last job in folder **Shared** (`DriveFileInspector`, job `0e3938d5-e2b0-480b-99d5-bcaf0e9123d6`, Unattended on `MOCK-HOST`) ended **Faulted** ~6s after start. It ran a single legacy GSuite **Get File Info** (`UiPath.GSuite.Activities.GetFileInfo`) activity inside a Google Workspace Scope.

## Cause
**Client-side input validation** — the activity threw before any call reached Google Drive (no HTTP status, no Google API round-trip). The File ID input was a **malformed Drive URL with no extractable object id**:

```
System.ArgumentOutOfRangeException: Could not extract an object Id from the Url 'https://drive.google.com/file/d/'. (Parameter 'uri')
   at UiPath.GSuite.Models.CloudObjectIdentifier.FromUrl(Uri uri)
   at UiPath.GSuite.Models.CloudObjectIdentifier.Initialize(String urlOrId)
   at UiPath.GSuite.Models.CloudObjectIdentifier..ctor(String urlOrId)
   at UiPath.GSuite.Models.CloudObjectIdentifier.CreateFromUrlOrId(String urlOrId)
   at UiPath.GSuite.Activities.GetFileInfo.ExecuteAsync(AsyncCodeActivityContext context, CancellationToken cancellationToken)
```

The configured URL is **truncated** — it ends at `/file/d/` with no `<FILE_ID>` segment (a valid link is `https://drive.google.com/file/d/<FILE_ID>/view`). `CloudObjectIdentifier` parses it as a URL, finds no id segment, and throws synchronously. The fault is a workflow-input problem (a bad/truncated URL fed to the File ID property), not a Google/connectivity/auth/resource problem. (The Google Drive and Sheets connections serving folder Shared are Enabled and valid — a connection list confirms this, so the connection is not the problem.)

This is the legacy `GetFileInfo` surface: it surfaces the error **raw** and faults the job (the modern `*Connections` variants can swallow some resolution errors).

## Resolution
Supply a valid Drive file id, or a well-formed Drive URL that contains the `<FILE_ID>` segment, to the Get File Info **File ID** input — or fix the upstream expression/variable that fed it so it is never a truncated/malformed URL before the activity runs. Re-validate and re-run.

Must NOT attribute to: a Google API / HTTP error, an HTTP 404 / file-not-found (the activity never queried Drive), expired/invalid credentials, an invalid connection, an Integration Service outage, rate limiting / 429, a transient 5xx, or a per-request timeout — the exception is raised client-side, before any request to Google, by a malformed URL argument.
