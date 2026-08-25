---
confidence: high
---

# Response Content Too Large (8 MB JSON limit)

> **Fault bucket: 👤 A — Customer-resolvable.** A payload-sizing problem on the customer's side: the connector operation asked the provider for more data than Integration Service will carry in a single JSON response. Not an IS defect and not a provider outage — the fix is narrowing the query or moving file bytes out of the JSON payload. Lead with: "This is a response-size issue on your side — the connector returned more than the 8 MB JSON limit. Narrow the query or pass files outside JSON." See [dap-error-codes-reference.md](../dap-error-codes-reference.md#fault-ownership--the-two-bucket-decision).

## Context

What this looks like:
- Verbatim message **`Response content too large`** in the job log / activity error
- Thrown by `UiPath.IntegrationService.Activities.Runtime.Exceptions.RuntimeException` on a `ConnectorActivity` (a list/search/get operation, or a download that returns file bytes)
- The connection is healthy and the provider call **succeeded** — the failure is IS refusing to marshal the oversized response, not a provider error. No `ProviderErrorCode` / provider status is present.
- Can also fire on a **`ConnectorTriggerActivity`** — the 8 MB ceiling applies to trigger event payloads too.

What can cause it:
- Integration Service enforces an **8 MB limit for data in JSON format**. A list/search/get returned more rows/fields than fit — usually an unbounded query (no **Max records**, no filter) against a large object.
- The 8 MB JSON limit **includes Base64-encoded files carried inside the JSON body** — downloading a file as an inline Base64 field blows the budget fast. Files handled **outside** JSON have a separate **1 GB** limit.
- A trigger's event payload exceeded 8 MB.

What to look for:
- The `Response content too large` string — this is the decisive signature; do not confuse with `DAP-RT-1101` (a *provider* error with a status code) — here the provider returned data successfully and IS rejected the size.
- Which operation: a **list/search** (row-count problem → filter/Max records) vs a **download/get file** (Base64-in-JSON problem → pass outside JSON).
- Whether a **Max records** input and query filter are set on the activity (absence points straight at an unbounded pull).

> Shares the `RuntimeException` class with [connector-runtime-exception.md](./connector-runtime-exception.md), but that page covers binding/input/provider `DAP-RT-` codes with a provider status. **This page is only for the `Response content too large` message** (no provider status, size-limit breach). NOT for a provider `BadRequest`/`NotFound` (`DAP-RT-1101`) → [connector-runtime-exception.md](./connector-runtime-exception.md) / [request-failed.md](./request-failed.md).

## Investigation

1. **Confirm the signature** — the log carries `Response content too large`, no `ProviderErrorCode` / provider HTTP status. If a provider status IS present, this is a provider error, not a size breach → [request-failed.md](./request-failed.md).
2. **Identify the failing operation and connector** — read the connection resource file if source is available (see "Connection Resource File" in [overview.md](../overview.md)) to get `connectorKey`; note whether the activity is a list/search/get vs a file download, and whether it feeds a trigger.
3. `uip is resources describe <connector-key> <object-name>` — check whether the operation exposes **Max records** / paging / filter inputs, and whether the object can return file/binary fields.
4. **Inspect the activity inputs in the workflow source** — is **Max records** set? Is there a query filter? Is a file being requested as an inline (Base64) field rather than a file output?

## Resolution

- **List/search returning too many rows:** set the activity's **Max records** to a bounded value and add a query filter (date range, status, key) so the response stays under 8 MB. Page through large result sets in batches instead of pulling everything at once.
- **Download/get returning file bytes inline:** stop carrying the file inside the JSON body. Use the connector's file-handling path (a file/attachment output handled outside JSON) so the 1 GB out-of-JSON limit applies instead of the 8 MB JSON limit.
- **Trigger payload over 8 MB:** narrow the trigger's object/fields or filter the event so its payload fits; move any large file content out of the event body.
- If the operation genuinely must return more than 8 MB of structured JSON and offers no paging/filter, that is a connector-capability limit — split the work into smaller queries; do not treat it as a workflow bug.
