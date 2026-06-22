# Final Resolution

Root Cause: The `Google Drive: Get File or Folder` (ConnectorActivity) operation reached Google Drive successfully but the **target file does not exist** — the provider returned **HTTP 404 (File not found)**, which the Integration Service runtime surfaces as `UiPath.IntegrationService.Activities.Runtime.Exceptions.RuntimeException: ... Status code: NotFound. Error code: DAP-RT-1101.`

> This scenario's error text was captured from a **real Google Drive connector execution** (a `Get File or Folder` call against a live connection with a non-existent file ID) — the signature, `ProviderMessage` block, and stack frames are verbatim, not synthesized.

What went wrong: Unlike a connection-resolution failure (`DAP-GE-*`), this fault happens **after** the connection resolves and the request is sent. `ExecutionService.GetListResponseAsync` → `ExecuteOperationAsync` issued the connector request; Google responded 404, and the runtime threw `RuntimeException` with error code **DAP-RT-1101**. The embedded `ProviderMessage` block names the exact provider error: `providerErrorCode - 404`, `reason=notFound`, `location=fileId`, `message - File not found: 1AbCdEfGhIjKlMnOpQrStUvWxYz000NOTFOUND.` The job's `InputArguments` show `FileId = "1AbCdEfGhIjKlMnOpQrStUvWxYz000NOTFOUND"` — the file the operation tried to fetch.

Why: `DAP-RT-1101` is the connector-operation HTTP-error code. NotFound (`reason=notFound`, `location=fileId`) means the referenced file ID is not present in Google Drive (deleted, never existed, wrong ID, or no access for this connection's identity). It is an operation-level (input/resource) error, not a connection, credential, or permission-resolution error. The `ProviderMessage` / `ProviderErrorCode` fields are the most actionable evidence — they carry the downstream provider's own error.

Evidence:

### Orchestrator
- Process **DriveSync** (release version 22087), folder **Shared** (`1965a46b-db4e-469e-aaaa-7e0b379cb34d`), job `6b4d2e9a-1c3f-4a8b-9d0e-2f5a7c1b8e4d` ended **Faulted**, host **MOCK-HOST**, `ErrorCode: Robot`.
- Job `Info` + error-level log carry the verbatim signature: `RuntimeException: Request failed with error:` / `ProviderErrorCode : 404` / `reason=notFound, location=fileId` / `Status code: NotFound. Error code: DAP-RT-1101.` with `ExecutionService.GetListResponseAsync` → `ExecuteOperationAsync` → `ConnectorActivity.ExecuteAsync`.
- `InputArguments` = `{"FileId":"1AbCdEfGhIjKlMnOpQrStUvWxYz000NOTFOUND"}` — the file ID the operation requested.

Immediate fix:
1. **Correct the file identifier.** Verify the `FileId` the activity passes points to a file that exists in Google Drive (right ID, right Drive, right account). Fix the upstream value or the activity input so it references an existing file. The `ProviderMessage` (`location=fileId`, `reason=notFound`) confirms the file ID is the failing parameter.

Preventive fix:
1. Guard for the not-found case: check the file exists (or handle a 404 / `reason=notFound`) before the Get File or Folder call, so a missing file produces an explicit business error / skip instead of faulting the job.
2. If the IDs come from an upstream system, validate them before the connector call to fail fast with a clear message.

Must NOT attribute to: a disabled / invalid / no-access connection (`DAP-GE-*` codes — connection resolution succeeded here); expired credentials or auth (the request was sent and answered); an IPC / RemoteException; or a UiPath platform outage. The external provider explicitly answered 404 / `notFound` for the requested file.
