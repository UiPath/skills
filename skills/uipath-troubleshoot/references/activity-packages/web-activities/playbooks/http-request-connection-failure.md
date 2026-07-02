---
confidence: medium
signatures:
  - kind: exception
    value: "System.Net.WebException"
    note: "on UiPath.Web.Activities.HttpClient — status / DNS / connection / TLS failure; message 'The operation has timed out.' → http-request-timeout.md"
  - kind: message
    value: "The remote server returned an error"
  - kind: message
    value: "No such host is known"
    note: "DNS failure on modern .NET (targetFramework Windows, .NET 6+)"
  - kind: message
    value: "The remote name could not be resolved"
    note: "DNS failure on legacy .NET Framework"
  - kind: message
    value: "Unable to connect to the remote server"
  - kind: message
    value: "Could not establish trust relationship for the SSL/TLS secure channel"
exclusions:
  - "WebException 'The operation has timed out.' → http-request-timeout.md"
---

# HTTP Client — Request Failed (WebException)

## Context

What this looks like:
- A `UiPath.Web.Activities.HttpClient` activity faults with `System.Net.WebException`.
- The job `Info` / `JobError.Type` names `System.Net.WebException`; the message is framework-originated (not a UiPath string), e.g.:
  - `The remote server returned an error: (404) Not Found.` / `(401) Unauthorized.` / `(500) Internal Server Error.`
  - DNS failure — `No such host is known. (<host>:<port>)` on modern .NET (`targetFramework: Windows`, .NET 6+; confirmed by repro on .NET 8) or `The remote name could not be resolved: '<host>'` on legacy .NET Framework
  - `Unable to connect to the remote server`
  - `The underlying connection was closed: Could not establish trust relationship for the SSL/TLS secure channel.`
- The exception is the raw RestSharp/transport exception unwrapped from the request task — `HttpClient` does not wrap it.
- **A timeout also surfaces as `System.Net.WebException` on modern .NET, with message `The operation has timed out.`** If that is the message, this is a timeout, not a connection failure — go to [http-request-timeout.md](./http-request-timeout.md).

What can cause it (branch from the message):
- **Non-success HTTP status (4xx/5xx)** — the server was reached and answered with an error status. `401/403` = auth/permission; `404` = wrong path/resource; `429` = rate limited; `5xx` = server-side fault.
- **DNS resolution failure** (`remote name could not be resolved`) — wrong/typo'd host, or DNS not reachable from the robot machine.
- **Connection refused / unreachable** (`Unable to connect`) — host up but port closed, service down, or firewall/proxy blocking egress.
- **SSL/TLS failure** (`Could not establish trust relationship` / `secure channel`) — untrusted/expired server cert, or a TLS-version/proxy-interception mismatch.

What to look for:
- **The status code or transport phrase in the message** — selects the branch directly.
- **`EndPoint` value** in the workflow source — confirm scheme/host/path are intended; a bare host gets `http://` prepended by the activity.
- **`ContinueOnError`** — if `True`, the activity would NOT fault here; a faulted job means it is `False` (or the failure is elsewhere).
- **Whether the same endpoint works from the robot machine** — isolates robot-network/proxy from a server-side problem.

## Investigation

1. **Capture the exact message + faulted activity.** `uip or jobs get <job-key> --output json` → `Info` (full message) and `JobError.ActivityName` / `WorkflowFilePath`. Confirm the activity is `HttpClient`.
2. **Read the request configuration from source.** Open the workflow; capture `EndPoint`, `Method`, auth properties, and `EnableSSLVerification`.
3. **Branch on the message:**
   - Has an HTTP status code → server answered; go to step 4.
   - "could not be resolved" / "Unable to connect" → transport/network; go to step 5.
   - "SSL/TLS" / "trust relationship" → certificate/TLS; go to step 6.
4. **Status-code branch.** Map the code: `401/403` → auth/permission on the target API; `404` → endpoint path/resource wrong or removed; `429` → throttling; `5xx` → target service fault (often transient — check whether earlier runs succeeded).
5. **Transport branch.** Verify the host resolves and the port is reachable from the **robot machine** (not the author's machine). Check proxy/firewall egress rules.
6. **TLS branch.** Check the server certificate validity/chain and the TLS version the endpoint requires; confirm the robot's trust store and that any intercepting proxy is trusted.

## Resolution

- **Non-success status:** fix per code — supply/refresh credentials or scope (`401/403`); correct the `EndPoint` path or resource id (`404`); add backoff / reduce call rate (`429`); for `5xx`, treat as a target-service fault — retry, or escalate to the API owner if persistent.
- **DNS failure:** correct the host in `EndPoint`; ensure the robot machine can resolve it (DNS server / hosts entry / VPN).
- **Connection refused / unreachable:** confirm the service is listening on the expected port and that the robot's network/proxy/firewall allows egress to it.
- **SSL/TLS failure:** install/trust a valid server certificate (or fix the expired one); align the TLS version; trust the intercepting proxy's CA on the robot machine. Disabling `EnableSSLVerification` masks the problem and is not a fix for production endpoints.
