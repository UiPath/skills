# Resolution — WorkspaceSheetSync (Shared)

## Fault
The last job in folder **Shared** (`WorkspaceSheetSync`, job `4e00b4ca-b35b-4457-bb12-74f270d20cb0`, Unattended on `MOCK-HOST`) ended **Faulted** ~7s after start. It ran a single GSuite **Download File** (`UiPath.GSuite.Activities.DownloadFileConnections`) activity.

## Cause
**Integration Service connection layer** failure — the activity could not resolve or authorize the connection it references. The job dispatched and started normally, then faulted during OAuth token acquisition (`ConnectionClient.GetAccessToken`), **before** any Google Drive API call:

```
UiPath.GSuite.Exceptions.GSuiteException: Connection [00000000-1111-2222-3333-444444444444] is invalid or you do not have access to it
 ---> UiPath.GSuite.Exceptions.GSuiteInternalException: Connection [00000000-1111-2222-3333-444444444444] is invalid or you do not have access to it
 ---> UiPath.ConnectionClient.Contracts.ConnectionHttpException: Connection [00000000-1111-2222-3333-444444444444] is invalid or you do not have access to it
   at UiPath.ConnectionClient.ConnectionClient.GetAccessToken(String connectionId, Boolean forceRefresh, CancellationToken ct)
   at UiPath.GSuite.Activities.BaseLeafConnectionServiceActivityWithoutBindings.ExecuteAsync(...)
```

The configured `ConnectionId` (`00000000-1111-2222-3333-444444444444`) does not resolve to a connection the running identity can use. A connection list for folder Shared confirms it: both GSuite connections that exist there (Google Drive, Google Sheets) are **Enabled**, and neither is the bogus id the activity references — so the referenced connection is not resolvable for this runner. This is NOT a Drive/file problem, NOT bad activity input, and NOT a transient Google error — it is connection resolution/authorization.

Sub-causes the runtime error alone cannot distinguish (require the project's connection resource file / `bindings_v2.json` + workflow to confirm): connection deleted or disabled; connection owned in a different workspace; robot account lacks folder permission to use it; project points at a connection in the wrong folder.

## Resolution
Point the activity at a valid, accessible GSuite connection in the runner's folder — re-select or create the Google connection in the project (Studio connection picker), or correct the `ConnectionId` / folder binding — and ensure the robot's identity has permission to the connection's folder. Re-publish and re-run.

Must NOT attribute to: a Drive HTTP 404 / file-not-found, a null/empty activity input, rate limiting / 429, a transient 5xx, a timeout, or a Google API data error — the exception is a connection-resolution/authorization failure raised before any Google request.
