---
confidence: medium
signatures:
  - kind: message
    value: "Internal server error occurred. Please try again later."
  - kind: message
    value: "The service is currently unavailable. Please try again later."
  - kind: message
    value: "Network error occurred before reaching the server."
  - kind: message
    value: "Request deadline exceeded."
  - kind: message
    value: "The current state conflicts with what the request expects."
  - kind: message
    value: "limit was exceeded."
    note: "covers 'The daily limit was exceeded.' / 'The user rate limit was exceeded.' / 'The rate limit was exceeded.' — Google 429 rate/quota reasons, NOT the storage quota ('storage quota was exceeded' → upload-storage-quota-exceeded.md)"
  - kind: message
    value: "A task was canceled."
    note: "GSuite per-request RequestTimeout (HttpClient cancellation) — not a System.TimeoutException, which is auth-phase → connection-and-auth-failures.md"
  - kind: message
    value: "An error occurred in the activity."
    note: "GSuite generic fallback for unmapped Google API errors — read the inner status/reason from the trace before concluding"
  - kind: error-code
    value: "dailyLimitExceeded"
  - kind: error-code
    value: "userRateLimitExceeded"
  - kind: error-code
    value: "rateLimitExceeded"
exclusions:
  - "Authentication attempt took longer than <N> seconds (auth-phase TimeoutException) → connection-and-auth-failures.md"
  - "The storage quota was exceeded. / Upload failed after <N> bytes → upload-storage-quota-exceeded.md"
  - "Clean 401/403/404 with a definite message → connection-and-auth-failures.md, drive-file-not-found.md"
---

# GSuite — Transient service errors, rate limits, and per-request timeouts

## Context

This playbook covers failures where the request reached (or tried to reach) Google and failed for a reason that is environmental and often temporary: a Google-side 5xx, a rate/quota-per-interval limit, a network fault, or a per-request timeout. The activity inputs and the target resource are usually fine — the same workflow often succeeds on retry. Distinguish **intermittent** (transient, retry) from **consistent** (network path or a timeout set too low).

What this looks like — any of the following messages:

- `Internal server error occurred. Please try again later.` — wrapped `GSuiteException`, Google **HTTP 500**. Transient.
- `The service is currently unavailable. Please try again later.` — wrapped `GSuiteException`, Google **HTTP 503**. Transient (Google maintenance / overload).
- `Network error occurred before reaching the server. Typically a network outage or misconfiguration.` — wrapped `GSuiteException`, **HTTP 502**.
- `Request deadline exceeded.` — wrapped `GSuiteException`, **HTTP 504**.
- `The current state conflicts with what the request expects.` — wrapped `GSuiteException`, **HTTP 409**.
- `The daily limit was exceeded.` / `The user rate limit was exceeded.` / `The rate limit was exceeded.` — wrapped `GSuiteException`, Google **HTTP 429** with reason `dailyLimitExceeded` / `userRateLimitExceeded` / `rateLimitExceeded`. The connection is making more requests than Google's per-day or per-interval quota allows.
- `An error occurred in the activity.` — the **generic fallback**: a Google API error whose status code and reason matched none of the known mappings (for example, a 429 without a recognized reason, or an uncommon status). The real status is in the inner exception / activity trace — read it before concluding; do not assume a specific cause from this text alone.
- A raw `System.Net.Http.HttpRequestException` — a network-layer failure (DNS resolution, connection reset, TLS handshake, firewall/proxy drop). Legacy activities surface this raw; modern activities may wrap it.
- `A task was canceled.` (a `System.Net.Http.TaskCanceledException` / `OperationCanceledException`) — the Google API request exceeded the activity's **per-request** `RequestTimeout` (the `HttpClient` timeout). **This is not a `System.TimeoutException`** — a `TimeoutException` in GSuite only ever comes from the *authentication* phase (see the connection-and-auth playbook). A per-request timeout cancels the task instead.

**Trigger activities** (`Gmail.Triggers.NewEmailReceived`, `Gmail.Triggers.EmailSent`, etc.) wrap their work in a retry-with-backoff: they automatically retry socket-level `HttpRequestException` and 5xx `GoogleApiException` (exponential backoff capped at 30s) before surfacing. So a transient error that faults a trigger generally means the condition persisted across the entire retry window, not a single blip.

What can cause it:
- **Transient Google fault** (5xx): Google service degradation, regional outage, or maintenance. Self-resolves.
- **Rate / quota limit** (429): the connection (or the whole project) exceeded Google's per-minute or per-day API quota — often a burst of requests in a loop, or many robots sharing one connection.
- **Network path failure** (`HttpRequestException`): DNS, proxy, firewall, or connectivity loss between the robot and Google.
- **Per-request timeout** (`A task was canceled.`): the call genuinely took longer than `RequestTimeout` (large payload, slow network), or `RequestTimeout` is set too low for the operation.

> **Different cause — do not apply this playbook:**
> - **`Authentication attempt took longer than <N> seconds ...`** is an *auth-phase* `TimeoutException`, a connection problem — use [connection-and-auth-failures.md](./connection-and-auth-failures.md).
> - **`The storage quota was exceeded.`** / **`Upload failed after <N> bytes ...`** is a *storage* quota (403), not an API rate limit — use [upload-storage-quota-exceeded.md](./upload-storage-quota-exceeded.md).
> - A clean 401/403/404 with a definite message → connection-and-auth or drive-file-not-found, not this playbook.

## Investigation

1. **Read the embedded status code / inner exception, not just the sentence.** A wrapped `GSuiteException` carries the original status; for `An error occurred in the activity.` the activity trace holds the real Google status and reason. Classify: 5xx (transient), 429 (rate limit), network (`HttpRequestException`), or timeout (`A task was canceled.`).
2. **Determine intermittent vs. consistent.** Check whether the same activity/connection succeeded on adjacent runs or fails every time. Intermittent points to a transient 5xx or a momentary network blip; consistent points to a network-path problem, an exhausted quota, or a `RequestTimeout` that is too low.
3. **For 429:** check the request volume around the failure — a loop firing many calls, or many jobs sharing one connection — and whether it's a daily vs per-minute limit (the message distinguishes them).
4. **For `A task was canceled.`:** capture the configured `RequestTimeout` and the expected size/latency of the operation.
5. **For network errors / persistent 5xx:** check the Google Workspace Status Dashboard for an active incident, and verify the robot's outbound connectivity (proxy, firewall, DNS) to Google endpoints.

## Resolution

- **If transient (intermittent 5xx / momentary network):** This is expected and recoverable. Wrap the activity in a Retry Scope (or rely on the trigger's built-in retry) and rerun. No configuration change needed if it succeeds on retry.
- **If rate-limited (429):** Reduce request rate — add delays or batching in loops, spread load across connections, or request a higher Google API quota. A `dailyLimitExceeded` resets at the start of the next day (Pacific time); per-user/per-minute limits clear within the minute.
- **If a persistent network failure (`HttpRequestException`):** Fix the network path — confirm the robot can reach Google API endpoints through the configured proxy/firewall, and that DNS resolves. Not a workflow defect.
- **If a per-request timeout (`A task was canceled.`):** Raise the activity's `RequestTimeout` if the operation is legitimately slow (large read/write), or reduce the payload size. Confirm network latency to Google is normal.
- **If `An error occurred in the activity.` and the inner status doesn't fit any of the above:** report the captured inner status/reason from the trace and re-triage — the generic message means the specific cause was not one of the mapped patterns.

If a 5xx or network error persists well beyond a normal retry window and the Google Status Dashboard shows no incident, escalate with the captured traces (endpoint, status, timing) rather than continuing to retry.
