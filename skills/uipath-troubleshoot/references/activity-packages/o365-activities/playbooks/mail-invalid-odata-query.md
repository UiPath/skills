---
confidence: high
---

# O365 Mail — Invalid OData filter query

## Context

What this looks like — a Mail read activity faults while applying its filter/query:

- `Invalid Query. Please use OData format for filter queries. Press F1 for examples.` — the package's fixed message, raised as `Office365Exception` when Microsoft Graph rejects the request with a `RequestBroker--ParseUri` error code (malformed `$filter`). Thrown from the shared Mail proxy, so it surfaces with this exact text from **both** legacy and Connections activities.
- A raw Graph invalid-filter message surfaced verbatim — other malformed-query Graph codes that don't hit the fixed mapping; on legacy activities inside a raw `Microsoft.Graph.ServiceException` with `Code: BadRequest`, e.g. `Invalid filter clause: ')' or operator expected at position <n> in '<composed filter>'.` (the message echoes the full composed `$filter`, including the date-range clause the activity prepends).

The failure is deterministic: the same query fails every run, independent of mailbox content.

What activities can produce this error:
- **Get Mail** (legacy `GetMail`) — `Query` property (OData `$filter` string).
- **Get Newest Email** (`GetNewestEmail`) — `QueryFilter` advanced filter.
- **Get Email List** (`GetEmailListConnections`), **For Each Email** (`ForEachEmailConnections`) — advanced/raw filter expressions.
- Mail triggers with filter expressions (`NewEmailReceived`, `WaitForEmailReceived`) on their filter path.

What can cause it:
- **Malformed OData syntax** — unbalanced quotes/parentheses, missing operators (`eq`, `ge`, `and`), or natural-language text where OData is expected.
- **Wrong property names** — properties not on the Graph `message` entity (e.g., `sender` vs `from/emailAddress/address`), or wrong casing of a property path.
- **Unsupported operations** — `$filter` on properties Graph doesn't index for filtering, combining `$search`-only constructs into `$filter`, or unsupported functions.
- **Bad literal formats** — datetimes not in ISO 8601 (`2024-01-01T00:00:00Z`), unquoted strings, or quoted numerics.

What to look for:
- The exact filter/query string from the activity's properties in the workflow source.
- Whether the query ever worked — a previously-working query that now fails usually means the string is built dynamically and an input made it malformed.

> **Different cause, do not apply this playbook:**
> - `There was an error on the email server. Please try modifying your Query or Top values to continue.` — a Graph `UnknownError` (server-side), not a deterministic parse failure. Use [transient-service-error.md](./transient-service-error.md).
> - Zero results with no error — the query is valid but matches nothing. Use [get-newest-email-no-match.md](./get-newest-email-no-match.md) for the trigger/no-match case.

## Resolution

The error is unambiguous; the configured query string is rejected by Microsoft Graph. Fix the query:

1. **Read the exact query string** from the failing activity (`Query` / `QueryFilter` / filter expression) in the workflow source. If it's built from variables, log/inspect the final composed value — the defect is often in an interpolated input.
2. **Validate the syntax against OData for Graph messages:** property paths like `subject`, `from/emailAddress/address`, `receivedDateTime`; operators `eq/ne/gt/ge/lt/le`, `and/or/not`, `startswith()`, `contains()`; ISO 8601 datetimes; single-quoted string literals.
3. **Test the corrected filter** in Graph Explorer against `/me/messages?$filter=...` until it returns 200, then copy it back into the activity.
4. **If the query is dynamic:** guard the inputs (escape single quotes, format dates as ISO 8601) before composing the filter.
