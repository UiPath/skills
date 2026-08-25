---
confidence: high
---

# O365 — Throttling / rate limit (429)

## Context

What this looks like — the job faults after Microsoft Graph rate-limits the tenant/app/mailbox (HTTP 429). The message is one of:

- `Too many requests.` — the canonical throttle signal. Surfaced after the underlying Microsoft Graph SDK's built-in retries (which honor the server's `Retry-After`) are exhausted.
- `The app or user has been throttled.`
- `(HTTP Status Code: TooManyRequests) Batching request failed with an unknown reason.` — a 429 on one sub-request inside a batched operation whose error body couldn't be parsed. The status renders as the name `TooManyRequests`, not the number `429`, so don't pattern-match on the digits in this batching message.
- A raw Microsoft Graph throttling message surfaced verbatim from a batched sub-response (when its error body *can* be parsed).

> **Version note:** the friendly `Too many requests.` mapping for the SDK's "retries exhausted" condition (`tooManyRetries`) was added in package **3.10**. On **3.9.11** and earlier, that condition is **not** remapped — it surfaces as a raw Graph/HTTP throttle message via the generic-error fall-through instead. On older packages, match the raw throttle wording (and the 429 status) as well. Legacy (non-Connections) activities likewise surface this class as a raw `Microsoft.Graph.ServiceException` with Graph's own throttle wording rather than the friendly sentence.

What activities can produce this:
- **Any** Mail, Files/OneDrive, or Excel Online activity, but it is **far more likely** under high call volume — **For Each File/Folder** (`ForEachFileFolderConnections`), **For Each Email** (`ForEachEmailConnections`), **Bulk Add List Items** (`BulkAddListItemsConnections`), retrieve-all reads (e.g. **Get Email List** (`GetEmailListConnections`) with `MaxResults = 0`), or any loop/bulk path that issues many Graph calls in a short window.

What can cause it:
- **Microsoft Graph rate limit exceeded.** Per-app, per-mailbox, or per-tenant limits were hit. Graph returns 429 with a `Retry-After`; the Microsoft Graph SDK's built-in retries (not this activity package) respect it but eventually give up, and the throttle message is what you see.
- **High call volume amplifies it.** Large `For Each` loops, bulk operations, retrieve-all, and request batching pack many calls together and reach the limit quickly.

What to look for:
- The failure follows a burst of operations (a big loop, a bulk action, many sequential calls), and the same workflow may succeed when re-run later or with less data.

> **Different cause, do not apply this playbook:**
> - 404/409 resource errors (`The resource could not be found.`, `The specified item name already exists.`) — these are deterministic, tied to a specific resource and fixed by correcting the locator or conflict behaviour, not by slowing down. Use the not-found / name-conflict playbooks.
> - `The server is unable to process the current request.` (503) or request timeouts — service/transport transients, not rate limiting. Use **transient-service-error**.
> - `The app or user has exceeded the allowed quota.` — a storage/quota limit, not a rate limit. Don't route it here; it isn't fixed by backing off.

## Investigation

1. Confirm the message is one of the throttle patterns above, and check whether it followed a high-volume step (large `For Each`, bulk, retrieve-all, or batched call).

## Resolution

There is no resource argument to fix — 429 is a transient, volume-driven limit. Reduce the call rate so the workflow stays under Microsoft Graph's threshold:

- **Throttle the volume:** add a short delay between iterations, lower parallelism/concurrency, process fewer items per run, and narrow filters / lower `MaxResults` / `Top` so fewer calls are made.
- **Honor `Retry-After` with backoff:** wrap the throttled operation in a Retry scope that waits and re-tries (exponential backoff). Re-run failed work after the suggested wait rather than immediately.
- **Spread the load:** stagger scheduled jobs so multiple processes don't hit the same tenant/app simultaneously.

If volume is already modest and `Retry-After`-respecting backoff still 429s, the limit is being consumed elsewhere — escalate (another process/app sharing the tenant or app registration, or a tenant-wide throttling event).
