# Resolution — SheetExportRunner (Shared)

## Fault
The last job in folder **Shared** (`SheetExportRunner`, job `c123367e-8e5e-4ec0-9903-fd75d5ef9ad7`, Unattended on `MOCK-HOST`) ended **Faulted** ~7s after start. It ran a single GSuite **Write Range** (`UiPath.GSuite.Activities.WriteRangeConnections`) activity.

## Cause
**Client-side input validation** — the activity threw before any call reached Google Sheets (no HTTP status, no Google API round-trip). The `range` input fed to Write Range was null/empty:

```
UiPath.GSuite.Exceptions.GSuiteException: Value cannot be null. (Parameter 'range')
 ---> UiPath.GSuite.Exceptions.GSuiteInternalException:  is not a valid Spreadsheet range. (Parameter 'range')
 ---> System.ArgumentNullException:  is not a valid Spreadsheet range. (Parameter 'range')
   at UiPath.GSuite.Sheets.Extensions.SheetsServiceExtensions.GetRangeMetadataInformationAsync(SheetsService service, String spreadsheetId, String range, RangeType rangeType, CancellationToken ct)
   at UiPath.GSuite.Sheets.Services.SheetsServiceProxy.WriteRangeAsync(...)
   at UiPath.GSuite.Activities.WriteRangeConnections.SafeExecuteAsync(...)
```

All three exception layers reference the same `range` parameter. The fault is a workflow-input problem (the `Range` property was an empty/null value), not a Google/connectivity/auth/resource problem. (The Google Drive and Sheets connections serving folder Shared are Enabled and valid — a connection list confirms this, so the connection is not the problem.)

## Resolution
Set a valid A1-notation `Range` on the Write Range activity (e.g. `Sheet1!A1`), or fix the upstream expression/variable that fed `range` so it is never null/empty before the activity runs. Re-validate and re-run.

Must NOT attribute to: a Google API / HTTP error, an HTTP 404 / resource-not-found, expired/invalid credentials, an invalid connection, an Integration Service outage, rate limiting / 429, a transient 5xx, or a per-request timeout — the exception is raised client-side, before any request to Google, by an empty `range` argument.
