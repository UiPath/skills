# Resolution — DriveDocSync (Shared)

## Fault
The last job in folder **Shared** (`DriveDocSync`, job `f41ed418-163b-487b-8077-e51f8af4a1af`, Unattended on `MOCK-HOST`) ended **Faulted**. It ran a single **Download File** (`UiPath.GSuite.Activities.DownloadFileConnections`) activity.

## Cause
The Google Drive file the activity targets — ID `1AbCnonexistentFILEid000000000000000` — does not resolve under the connection's Google account, so the Drive API returned **404 Not Found**:

```
UiPath.GSuite.Exceptions.GSuiteException: The resource was not found.
 ---> Google.GoogleApiException: The service drive has thrown an exception.
      HttpStatusCode is NotFound. File not found: 1AbCnonexistentFILEid000000000000000.
   at UiPath.GSuite.Drive.Extensions.DriveExtensions.GetFileAsync(...)
   at UiPath.GSuite.Drive.Services.DriveServiceProxy.DownloadOrExportLocallyAsync(...)
   at UiPath.GSuite.Activities.DownloadFileConnections.SafeExecuteAsync(...)
```

This is a **resource-resolution (404)** failure, not a connection/auth or transient failure: the connection authenticated and reached Google; Google reported the specific file ID does not exist or is not visible to this account. The fault is fully attributable to the configured Download File target. (The Google Drive and Sheets connections serving folder Shared are Enabled and valid — a connection list confirms this, so the connection is not the problem.)

## Resolution
Pick the case that matches the file's real state in Drive (signed in as the connection's account):

- **File deleted / in Trash / not findable** → restore from Trash or recreate it, then update the Download File activity to the new file's ID.
- **File exists but the configured ID is wrong/stale** → re-select the correct file through the connection browser in `Main.xaml` so a fresh ID is captured.
- **File exists but owned by / not shared with this account** → share it with the connection's Google account (≥ viewer), or switch the connection to an account that already has access.

Must NOT attribute to: Integration Service outage, expired/invalid credentials, insufficient OAuth scope, rate limiting / 429, a transient 5xx, or a per-request timeout — the evidence is an unambiguous Drive **404 for a specific file ID**.
