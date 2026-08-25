---
confidence: low
---

# Get Asset Failed — Network or Connectivity Issue

## Context

A `Get Asset`, `Get Orchestrator Asset`, or `Get Credential` activity failed due to network, TLS, or proxy issues between the robot and Orchestrator.

What this looks like:
- `"Orchestrator information is not available"`
- Timeout errors or SSL handshake failures
- Intermittent failures with no consistent error code
- Failures appear after ~2 hours in long-running processes (session expiry)

What can cause it:
- UiPath Robot Windows service not running
- Robot cannot reach the Orchestrator URL (firewall, DNS, proxy)
- Proxy requires authentication (UiPath Robot supports only unauthenticated proxies)
- SSL certificate expired or not trusted by the robot machine
- TLS Extended Master Secret (EMS) incompatibility (manifests as ~1 in 256 intermittent failures)
- Orchestrator auth session expired in long-running processes

What to look for:
- Whether the Robot service is running on the machine
- Network connectivity from the robot machine to the Orchestrator URL
- Proxy and SSL/TLS configuration
- Whether failures are intermittent or consistent
- Whether failures correlate with long-running process duration

## Investigation

1. Confirm the UiPath Robot Windows service is running on the machine.
2. Verify the robot can reach the Orchestrator URL — test from the robot machine.
3. Check for proxy configuration: UiPath Robot supports only unauthenticated proxies.
4. For on-premises Orchestrator: verify the SSL certificate is valid and trusted by the robot machine's certificate store.
5. If failures appear intermittent (~1 in 256 attempts): investigate TLS Extended Master Secret (EMS) compatibility.
6. If failures occur after ~2 hours in long-running processes: the Orchestrator auth session has expired — implement retry logic around the Get Asset call.

## Resolution

- **If Robot service is stopped:** start it and re-run the job.
- **If proxy is blocking:** configure the proxy to allow unauthenticated pass-through, or exclude the Orchestrator URL.
- **If SSL certificate is expired:** renew it on the Orchestrator server and ensure the robot machine trusts it.
- **If session expiry in long-running jobs:** add retry handling (Retry Scope) around the Get Asset activity.
