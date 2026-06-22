# Final Resolution

Root Cause: The `Salesforce: Get Record` (ConnectorActivity) operation reached Salesforce successfully but the **target record does not exist** — the external service returned **HTTP 404 (NotFound)**, which the Integration Service runtime surfaces as `UiPath.IntegrationService.Activities.Runtime.Exceptions.RuntimeException: ... Status code: NotFound. Error code: DAP-RT-1101.`

What went wrong: Unlike a connection-resolution failure (`DAP-GE-*`), this fault happens **after** the connection resolves and the request is sent. `ExecutionService.SendAsync` issued the connector request; the service responded NotFound, and the runtime threw `RuntimeException` with error code **DAP-RT-1101**. The job's `InputArguments` show `RecordId = "001XX0000 ABCDEF"` — the record the operation tried to fetch.

Why: `DAP-RT-1101` is the connector-operation HTTP-error code. NotFound specifically means the referenced object/record ID is not present in the external service (deleted, never existed, wrong ID, or wrong object type / endpoint). It is an operation-level (input/resource) error, not a connection, credential, or permission error.

Evidence:

### Orchestrator
- Process **AccountEnrichment** (release version 22087), folder **Shared** (`1965a46b-db4e-469e-aaaa-7e0b379cb34d`), job `6b4d2e9a-1c3f-4a8b-9d0e-2f5a7c1b8e4d` ended **Faulted**, host **MOCK-HOST**, `ErrorCode: Robot`.
- Job `Info` + error-level log carry the verbatim signature `RuntimeException: Request failed with error: The requested resource was not found.` / `Status code: NotFound. Error code: DAP-RT-1101.` with `ExecutionService.SendAsync` → `ConnectorActivity.ExecuteAsync`.
- `InputArguments` = `{"RecordId":"001XX0000 ABCDEF"}` — the record ID the operation requested.

Immediate fix:
1. **Correct the record identifier.** Verify the `RecordId` the activity passes points to a record that exists in Salesforce (right ID, right object type). Fix the upstream value or the activity input so it references an existing record.
   - Confirm the object/operation with `uip is resources describe <connector-key> <object>` if which fields/IDs are valid is unclear.

Preventive fix:
1. Guard for the not-found case: check the record exists (or handle a 404) before the Get Record call, so a missing record produces an explicit business error / skip instead of faulting the job.
2. If the IDs come from an upstream system, validate them before the connector call to fail fast with a clear message.

Must NOT attribute to: a disabled / invalid / no-access connection (`DAP-GE-*` codes — connection resolution succeeded here); expired credentials or auth (the request was sent and answered); an IPC / RemoteException; a UiPath platform outage. The external service explicitly answered NotFound for the requested record.
