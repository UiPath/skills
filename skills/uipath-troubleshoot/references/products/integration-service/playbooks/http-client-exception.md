---
confidence: high
---

# HTTP Client Exception (DAP-RT-1103)

> **Fault bucket: 🛠 B2 — Service/provider-side (not customer-fixable in the workflow → escalate).** A network-level failure reaching the provider host. If it is the customer's own network egress (firewall/proxy/DNS on a self-hosted robot), that part is theirs to fix; the connectivity to the provider is not a workflow change. Lead with: "This is a connectivity/provider-reachability issue, not a workflow bug — check network egress or escalate." See [dap-error-codes-reference.md](../dap-error-codes-reference.md#fault-ownership--the-two-bucket-decision).

## Context

What this looks like:
- Error code `DAP-RT-1103` (HttpClientException)
- Network-level failure — IS could not reach the target host at all (no HTTP status returned)
- `ProviderErrorCode` is typically absent (the request never got a response)
- Maps to the `retry-exception` SRE alert when retries are exhausted

What can cause it:
- DNS resolution failure for the provider host
- Connectivity/firewall blocking outbound traffic to the provider
- Provider host unreachable or TLS handshake failure
- Transient network blip (would normally be absorbed by retry)

What to look for:
- Absence of `ProviderErrorCode` — distinguishes this from `DAP-RT-1101` (provider returned a status)
- Whether `retry-exception` fired — IS retries network failures; exhaustion means a sustained connectivity problem, not a blip
- `RequestId` to correlate timing across the call

## Investigation

1. **Confirm it is network-level, not provider-level** — verify `ProviderErrorCode` is absent. If a status is present, use [request-failed.md](./request-failed.md) instead.
2. **Read the connection resource file** — identify the connector and target host (see "Connection Resource File" in [overview.md](../overview.md)).
3. `uip is connections ping <connection-id>` — if ping also fails at the network layer, the problem is connectivity, not the operation.
4. Check whether the provider host is reachable from the runtime environment (DNS, firewall egress, proxy). For self-hosted/unattended robots, egress rules differ from a developer's machine — debug may succeed where deployed fails.

## Resolution

- **DNS / host unreachable:** verify the provider hostname resolves and is correct in the connector configuration.
- **Firewall / proxy:** allow outbound access to the provider host from the robot's environment; configure proxy settings if the environment requires one.
- **TLS failure:** ensure the runtime trusts the provider's certificate chain.
- **Sustained `retry-exception`:** treat as an environment/connectivity problem — escalate to whoever owns network egress, not as a workflow bug. Retries are already exhausted; application retry will not help.
