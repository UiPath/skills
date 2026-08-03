# Resolution — SheetRangeWriter (Shared)

## Fault
The last job in folder **Shared** (`SheetRangeWriter`, job `d5e0e6b0-55b8-4256-8494-c601cb986dab`, Unattended on `MOCK-HOST`) ended **Faulted** ~4.5s after start. It ran a single GSuite **Write Range** (`UiPath.GSuite.Activities.WriteRangeConnections`) activity.

## Cause
The Write Range activity sent a **malformed A1 range** to the Google Sheets API, which rejected it with HTTP 400:

```
UiPath.GSuite.Exceptions.GSuiteException: The request is not as expected by Google API.
 ---> Google.GoogleApiException: The service sheets has thrown an exception. HttpStatusCode is BadRequest. Unable to parse range: Sheet1!A0
```

The configured range `Sheet1!A0` is invalid because **Google Sheets rows are 1-indexed** — row 0 does not exist, so the API cannot parse the range. The spreadsheet itself resolved fine and the connection authenticated; the failure is server-side range parsing of a present-but-malformed range. (The friendly top-level message `The request is not as expected by Google API.` wraps the verbatim `HttpStatusCode is BadRequest. Unable to parse range: Sheet1!A0`.) The Google Drive and Sheets connections serving folder Shared are Enabled and valid — a connection list confirms this, so the connection is not the problem.

## Resolution
Use a valid 1-based A1 range (e.g. `Sheet1!A1` or `Sheet1!A1:B2`). If the range is built dynamically, fix the off-by-one (a 0-based row/column index used directly in A1 notation) so the row component is ≥ 1. Re-validate and re-run.

Must NOT attribute to: an HTTP 404 / resource-not-found, an invalid/inaccessible connection or auth failure, a null/empty input (the range is present, just malformed), rate limiting / 429, a transient 5xx, or a timeout — the error is a Sheets API 400 caused by an unparseable A1 range.
