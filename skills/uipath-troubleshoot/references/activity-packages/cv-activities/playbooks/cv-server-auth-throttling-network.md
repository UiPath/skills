---
confidence: medium
signatures:
  - kind: exception
    value: "System.ArgumentException"
    note: "built by CVSessionData.Compute / ToErrorMessageWithCode() with [Error code: N] text — surfaces lazily on a child's first refresh, not at scope entry"
  - kind: message
    value: "Computer Vision cannot be enabled: the current user is not authenticated."
  - kind: message
    value: "The specified Computer Vision server"
    note: "covers the 403 variant with the server name and the 502/503/504/408 could-not-be-reached variant"
  - kind: message
    value: "Computer Vision rate limit exceeded."
  - kind: message
    value: "The requested data exceeds the maximum payload accepted by the server."
  - kind: message
    value: "hit the maximum number of words it is able to identify"
    note: "covers the cloud (MaxOCRCloud) and local-server (MaxOCR) word-limit variants — thrown even on HTTP 200"
  - kind: message
    value: "Error while sending request."
  - kind: message
    value: "Response from server is not valid."
    note: "generic fall-through masking transport errors — the real cause is in the trace, not the surfaced message"
  - kind: message
    value: "Server URL is empty and UseLocalServer option is false"
exclusions:
  - "Local-server install/prerequisite errors (LocalServer package missing, VC++ redistributable, AVX2) → cv-scope-setup-failures.md"
  - "Element not found with no error code (the analysis call succeeded) → cv-element-not-found.md"
  - "CvElementExistsWithDescriptor returned false — it only swallows not-found; server errors still fault"
---

# CV — Server errors: auth (401), unreachable (403/5xx), throttling (429), payload/word limits, network

## Context

All five CV activities share one transport stack and one throw site. When the CV analysis response is `null`, carries an `Error`, carries a `LocalServerError`, or has `OCRWordLimitPassed = true`, `CVSessionData.Compute` throws `System.ArgumentException` whose message is built by `cvData.ToErrorMessageWithCode()` — the `[Error code: <code>] <text>` strings below. There is **no handshake at scope entry**: CV Screen Scope (`CVScope`) only resolves the target window and publishes session data. Server reachability, auth, and throttling surface lazily on the **first child activity's first refresh** — so `scope succeeded but first CV Click fails with a server error` is normal and does NOT mean the scope is misconfigured.

What this looks like — match on message text (the leading `[Error code: N]` is informational; do not pattern-match the digits alone):

- `[Error code: 401] Computer Vision cannot be enabled: the current user is not authenticated.` — auth. (`ResponseInvalidApiKey`; full text continues with login / API-key paste instructions.)
- `[Error code: 403] The specified Computer Vision server '<server>' could not be reached.` — forbidden / blocked path. (`ResponseForbiddenError`; continues with firewall/VPN guidance. `<server>` = the configured `Server` URL.)
- `The specified Computer Vision server could not be reached.` — unreachable (`ResponseInvalidServer`, mapped from 502/503/504/408). No server name in this variant.
- `The Computer Vision server encountered an error.` — server-side fault (`ResponseServerError`, 500).
- `The requested data exceeds the maximum payload accepted by the server.` — payload too large (`ResponseEntityTooLarge`, 413).
- `[Error code: 429] Computer Vision rate limit exceeded.` — throttling, optionally followed by `Please try again in <seconds> seconds.` (`CVResponseThrottling` + `PleaseRetryAfterSeconds`). Full text mentions free-tier upgrade.
- `Error while sending request.` — network/transport. Followed by the raw `HttpRequestException` text (DNS, TLS `The SSL connection could not be established`, proxy, connection refused). (`ErrorWhileSending`.)
- `Response from server is not valid.` — generic fall-through (`ResponseNotValid`). **This is the masking case** — see the trap note below.
- `The ComputerVision server has hit the maximum number of words it is able to identify (<count>). Please indicate a screen with less words.` — OCR word limit, cloud (`MaxOCRCloud`). Local-server variant: `UiPath.ComputerVision.LocalServer has hit the maximum number of words it is able to identify (<count>). Please indicate a screen with less words.` (`MaxOCR`). Thrown even on HTTP 200.
- `Server URL is empty and UseLocalServer option is false` — no server configured at runtime (`ComputerVisionServerNotSet`).

What activities can produce this error:
- **CV Screen Scope** (`CVScope`) — on its own session-refresh path (debug/healing sample lookup).
- **CV Click** (`CvClickWithDescriptor`), **CV Type Into** (`CvTypeIntoWithDescriptor`), **CV Get Text** (`CvGetTextWithDescriptor`) — on the find/refresh that triggers a server analysis call.
- **CV Element Exists** (`CvElementExistsWithDescriptor`) — **faults** (throws this `ArgumentException`) on server errors. It only swallows `ElementNotFoundException` (→ `Result = false`); a server/auth/throttle error is NOT converted to `false` and still throws.

What can cause it (ordered most→least common):
- **Wrong/expired/revoked `ApiKey`, or robot not authenticated to the licensed Automation Cloud tenant** → 401. On a cloud URL the client first sends the `ApiKey` as `X-UIPATH-License`; a 401 marks the key unauthorized and silently falls back to an `X-UIPATH-Token` from the access provider (refreshing once). The 401 message surfaces only after **both** the key and the token fallback fail. On a non-cloud `Server` URL there is no token fallback.
- **Firewall / VPN / proxy / DNS / TLS blocking the server** → 403 (`ResponseForbiddenError`), 502/503/504 (`ResponseInvalidServer`), or `Error while sending request.` / `Response from server is not valid.` (transport).
- **Free-tier / shared-key rate limit** → 429. Retried internally (see Version/retry note) before surfacing.
- **Screenshot too large** → 413 — very high-resolution or multi-monitor scope regions.
- **On-prem / local CV server down or overloaded** → 500 (`ResponseServerError`) or 503.
- **Text-dense screen** → OCR word limit (scope set on the whole desktop instead of one window, full-screen spreadsheets/terminals).
- **`Server` URL unset at runtime** → `Server URL is empty and UseLocalServer option is false` (Project Settings server URL cleared, or `Server` arg evaluates to empty string, with `UseLocalServer = false`).

> **Retry/timing note:** HTTP 429 and 520 (Cloudflare "unknown error") are retried internally every 2s within a window of `2 × TimeoutMS` (default `TimeoutMS = 30000`) before the throttled response surfaces. The job therefore **appears slow, then fails** — a single transient 429 is absorbed transparently if the server recovers in-window. `LocalServerError` responses bypass this retry loop and surface immediately.

> **Pattern-matching trap — `Response from server is not valid.`:** transport exceptions (`HttpRequestException`, DNS, TLS, proxy) are caught in the client and converted to a response with `ErrorMessage` set. When no status code is attached, the message becomes `Error while sending request.` + raw text. When the body is unparseable or empty with no status, it falls through to the **generic** `Response from server is not valid.`, which **masks the real network error**. The underlying cause is visible only in the trace/runtime-dump logs, not the surfaced message. Do not conclude "server returned garbage" from this string alone — check the trace.

> **Different cause, do not apply this playbook:**
> - `Element not found` / descriptor match failed within timeout (no `[Error code]`, no server text) — the call reached the server and returned, but the descriptor did not match. Use [cv-element-not-found.md](./cv-element-not-found.md).
> - CV Screen Scope fails to resolve the **target window** or local-server prerequisites (`Please make sure you have UiPath.ComputerVision.LocalServer package installed...`, `...requires Microsoft Visual C++ Redistributable...`, `...requires a processor that accepts AVX2...`, or `Server or OCR engine is required.` at design time) — use [cv-scope-setup-failures.md](./cv-scope-setup-failures.md).
> - `Invalid Descriptor` (`InvalidDescriptorException`) — missing `Target`, broken image references, parse failure. Use [cv-invalid-descriptor.md](./cv-invalid-descriptor.md).
> - CV Element Exists returns `false` (no exception) when you expected an error, or `ContinueOnError = true` swallowed a fault — use [cv-silent-failures-and-false-results.md](./cv-silent-failures-and-false-results.md).
> - `System.OperationCanceledException` / `TaskCanceledException` — job stop / parent cancellation, not a server error.

## Investigation

1. **Capture the exact surfaced message** and the `[Error code: N]` if present. This is the primary routing key — map it to a branch below.
2. **Read the scope's transport properties** from the faulted activity's enclosing `CVScope`: `Server`, `ApiKey`, `UseLocalServer`, `CvMethod`, `TimeoutMS`. (For runtime-bound values, confirm what they evaluated to — `Server`/`ApiKey` may be expressions.)
3. **Check the trace / runtime-dump logs** when the message is generic (`Response from server is not valid.`) or transport (`Error while sending request.`) — the masked HTTP status, DNS/TLS detail, or swallowed client exception is recorded there, not in the surfaced message. The runtime JSON dump is written by the dump service just before the throw.
4. **Establish whether the failure is deterministic or volume/timing-driven.** 429 follows a burst (loops, many robots on one key) and may succeed on re-run later; 401/403/`Server URL is empty` are deterministic and fail every run regardless of load.
5. **Confirm cloud vs on-prem `Server`.** Cloud (`cloud.uipath.com` family) has the ApiKey→token fallback; an on-prem URL sends `ApiKey` as `X-UIPATH-License` with no fallback, so a stale key fails harder there.

## Resolution

Match the surfaced message to a branch. Each branch names the evidence that confirms it and the evidence that rules it OUT — do not apply a fix the evidence doesn't support.

### Branch A — Auth (401): `Computer Vision cannot be enabled: the current user is not authenticated.`
Evidence: `[Error code: 401]`; fails on every run; `ApiKey` is set on the scope or in Project Settings. On a cloud URL this means **both** the `ApiKey` header and the access-token fallback were rejected.
Ruled out when: the message is 403/5xx (reachability, not auth) or a transport string — those are not auth failures; do not rotate the key for them.
Fix (user/config-side): verify the `ApiKey` is current — copy a fresh key from Automation Cloud > Admin > Licenses > Robots & Services into Project Settings > Computer Vision > API Key, OR ensure the robot is signed in to the licensed cloud tenant so the token fallback can authenticate. Confirm the tenant license includes CV entitlement. **Silent auth degradation:** if the workflow "used to work," a rotated/revoked key now silently falls back to the interactive token and only fails when that path also lacks entitlement — treat a sudden 401 after a key rotation as the rotated key.

### Branch B — Server unreachable / forbidden (403, 502/503/504, 500)
Evidence: `[Error code: 403] The specified Computer Vision server '<server>' could not be reached.` (forbidden / intermediary block), or `The specified Computer Vision server could not be reached.` (502/503/504/408), or `The Computer Vision server encountered an error.` (500). Deterministic for 403; intermittent for 5xx if the server is overloaded.
Ruled out when: the message is 401 (auth) or 429 (throttle).
Fix (user/infra-side): verify the `Server` URL is correct and reachable from the robot host. Check firewall / VPN / proxy / TLS-inspection rules allow the CV endpoint. For on-prem CV server, confirm the server process is up and not overloaded (500/503). This is an infrastructure fix, not a workflow edit.

### Branch C — Throttling (429)
Evidence: `[Error code: 429] Computer Vision rate limit exceeded.`, optionally `Please try again in <seconds> seconds.`; the job ran slow (internal 2s retries over the `2 × TimeoutMS` window) before failing; follows a burst of CV calls or many robots sharing one `ApiKey`; same workflow may pass on re-run with less load.
Ruled out when: the failure is deterministic and load-independent — that is auth/reachability, not throttling. Do NOT "fix" a 401/403 by adding backoff.
Fix (user-side): reduce CV call rate — fewer CV activities per loop iteration, lower concurrency/parallel robots on the shared key, add backoff/Retry around the CV step honoring the `Please try again in <seconds>` hint, stagger scheduled jobs. If on a free/community tier, upgrade the license. Raising `TimeoutMS` only widens the internal retry window (mitigation), it does not raise the rate limit.

### Branch D — Payload too large (413): `The requested data exceeds the maximum payload accepted by the server.`
Evidence: `ResponseEntityTooLarge`; scope `Target` is a very large region — full multi-monitor desktop or high-DPI capture.
Fix (user-side): narrow the scope `Target` to a single window/region instead of the whole desktop, reducing the screenshot the client base64-encodes and POSTs.

### Branch E — OCR word limit: `...has hit the maximum number of words it is able to identify (<count>)...`
Evidence: `MaxOCRCloud` (cloud) or `MaxOCR` (`UiPath.ComputerVision.LocalServer ...`, local); thrown even on HTTP 200 because the response sets `OCRWordLimitPassed`. Scope covers a text-dense screen.
Fix (user-side): indicate a smaller, less text-dense region — scope a single pane/window rather than a full spreadsheet, terminal, or desktop. The `<count>` in the message is the server's cap.

### Branch F — Network / transport: `Error while sending request.` or generic `Response from server is not valid.`
Evidence: `Error while sending request.` carries the raw `HttpRequestException` (DNS resolution failure, `The SSL connection could not be established`, proxy auth, connection refused). The generic `Response from server is not valid.` **masks** the same class — confirm via trace/dump (Investigation step 3) before concluding it is a malformed-response problem.
Ruled out when: the trace shows a clean HTTP status code (then it is one of Branches A–E, not transport).
Fix (user/infra-side): resolve robot-host networking — DNS for the CV endpoint, trusted root cert for TLS-inspection proxies, self-signed cert trust for on-prem, proxy credentials configured for the robot service.

### Branch G — Server URL missing: `Server URL is empty and UseLocalServer option is false`
Evidence: `ComputerVisionServerNotSet` at runtime; `UseLocalServer = false` and `Server` (arg or Project Settings server URL) evaluated to empty.
Fix (user/config-side): set Project Settings > Computer Vision > Server URL, set the scope `Server` argument, or enable `UseLocalServer` if local mode is intended. If `Server` is bound to an expression, verify it doesn't evaluate to an empty string at runtime.

> **Local-server `LocalServerError` note:** when `UseLocalServer = true`, the same `[Error code: N]` throw path can carry a `LocalServerError`. Engine/install failures (`Please make sure you have UiPath.ComputerVision.LocalServer package installed...`, VC++ redistributable, AVX2, `Response from local server is not valid.`) are scope-setup problems — route to [cv-scope-setup-failures.md](./cv-scope-setup-failures.md). Only the `MaxOCR` local word-limit message (Branch E) belongs here.

If the surfaced message and the trace both rule out every branch above — the `ApiKey` is confirmed current and entitled, the `Server` is reachable from the robot host with no proxy/TLS/DNS interference, the load is modest with backoff in place, and the scope region and word count are within limits — the cause is outside the CV activity stack. Escalate (tenant-wide CV outage, license/entitlement change, or an upstream proxy/network event) rather than continue under this playbook. Do NOT recommend rotating keys, adding backoff, or shrinking the region when the evidence does not point to that branch.
