---
confidence: medium
---

# HTTP Request — Blocked by Corporate Proxy (StatusCode 0 / 407)

## Context

What this looks like:
- An `HttpClient` / `NetHttpRequest` call to an **external/public** endpoint returns a **`StatusCode` of `0`** (or `NULL`/empty response), or fails with **`(407) Proxy Authentication Required`**, or a connection timeout/abort — **only from the robot machine / a virtual or server environment**, while the same call works from a developer laptop.
- StatusCode `0` means **no HTTP response reached the activity** — the request never made it to the server. It is a transport/connectivity signal, not a server answer.
- Internal/intranet endpoints succeed; only egress to the internet fails. The differentiator is the **network path**, not the request itself.

What causes it:
- The environment sits behind a **corporate proxy** required for outbound internet, and the request is not traversing it. The Web activities do **not** expose a built-in proxy configuration, and do not reliably pick up the interactive user's system proxy when running under a **service/unattended** account (Session 0) — so egress is dropped by the firewall/proxy.
- **`407`** specifically = the proxy is in the path but the request carries **no proxy credentials**.

What to look for:
- **`StatusCode == 0`, `407`, or a timeout/abort with no HTTP status** — the transport signal.
- **Endpoint is external** (public internet) vs internal — external-only failure points at egress/proxy.
- **Run context** — unattended/service account vs interactive; failure on a server/VM but not the author's machine.
- **Whether a proxy is required for internet egress** in this environment (ask / check environment policy).
- This is distinct from a **DNS / connection-refused / TLS `WebException`** (host resolves but call fails for a server/cert reason) — for those see [http-request-connection-failure.md](./http-request-connection-failure.md). Here the host is reachable *in principle* but the proxy hop is missing.

## Investigation

1. **Capture the symptom.** From logs/traces or the workflow output: is it `StatusCode 0`, `407`, or a timeout with no status? `uip or jobs logs <job-key> --level Error --output json` / `uip or jobs traces <job-key> --output json`.
2. **Confirm the endpoint is external** and that the failure is environment-specific (robot/server, not the developer machine).
3. **Establish whether a proxy governs internet egress** in that environment and whether the robot's run account routes through it.
4. **Rule out a plain transport failure** — if the message is a `WebException` naming DNS / "Unable to connect" / SSL, that is [http-request-connection-failure.md](./http-request-connection-failure.md), not a proxy gap.

## Resolution

- **Route the request through the proxy.** Because the activity has no proxy property, either:
  - Configure the **robot's run account / machine** to use the corporate proxy for outbound HTTP (system proxy for the service account, or `HTTP_PROXY`/`HTTPS_PROXY` where honored), OR
  - Set the proxy **programmatically** before the call — build `New System.Net.WebProxy(proxyAddress)`, set `NetworkCredential` for the `407` case, then `System.Net.WebRequest.DefaultWebProxy = proxy` (Assign activities, ahead of the HTTP request).
- **Supply proxy credentials** when the symptom is `407`.
- **Whitelist the target host** for egress on the corporate proxy/firewall, or add it to the proxy **bypass list** (`proxy.BypassProxyOnLocal`, `proxy.BypassList`) when it should skip the proxy.
- Verify from the **robot machine under the run account** (not the author's machine) that egress to the endpoint now returns a real status code.
