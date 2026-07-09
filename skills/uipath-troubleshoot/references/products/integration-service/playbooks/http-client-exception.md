---
confidence: high
---

# HTTP Client Exception (DAP-RT-1103)

> **Fault bucket: 🛠 B2 — Service/provider-side (not customer-fixable in the workflow → escalate).** A network-level failure between the robot and UiPath's Integration Service endpoint. On self-hosted robots the customer owns the egress path (firewall/proxy/DNS) — that part is theirs to fix; it is never a workflow change. On UiPath-hosted cloud robots there is no customer-side network to fix — escalate. Lead with: "This is a connectivity issue between the robot and UiPath's cloud, not a workflow bug — check network egress or escalate." See [dap-error-codes-reference.md](../dap-error-codes-reference.md#fault-ownership--the-two-bucket-decision).

## Context

**What the target host is:** the connector request goes from the activity runtime (robot) to **UiPath's Integration Service endpoint** in Automation Cloud — the connection's `ApiBaseUri`, shaped like `https://cloud.uipath.com/<org>/<tenant>/elements_`. IS then calls the vendor API on the robot's behalf. `DAP-RT-1103` means the runtime could not reach the **UiPath endpoint**; a vendor-side failure returns an HTTP status through IS and surfaces as `DAP-RT-1101` instead.

What this looks like:
- Error code `DAP-RT-1103` (HttpClientException)
- Network-level failure — no HTTP status returned (exception before/without a response)
- `ProviderErrorCode` absent (the request never got a response)
- Maps to the `retry-exception` SRE alert when retries are exhausted

What can cause it:
- DNS cannot resolve the UiPath cloud host from the robot machine
- Firewall/proxy blocks outbound traffic to UiPath cloud domains — see [Configuring the firewall](https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/configuring-firewall) for the domains and outbound IP ranges to allowlist
- TLS handshake failure — usually an SSL-inspecting corporate proxy re-signing the certificate, or a stripped trust store on the robot machine
- Request timeout to the IS endpoint, or a transient blip — absorbed by IS's automatic retry (max 2 attempts, jittered backoff; see [Retry semantics](../dap-error-codes-reference.md#retry-semantics)) unless sustained

What to look for:
- Absence of `ProviderErrorCode` — distinguishes this from `DAP-RT-1101` (a status was returned)
- Whether `retry-exception` fired — retries exhausted means sustained connectivity failure, not a blip
- **Where the job ran** — UiPath-hosted cloud robot (UiPath-managed network → escalate) vs self-hosted robot (customer machine/VM; customer owns DNS/firewall/proxy egress)
- `RequestId` to correlate timing across the call

## Investigation

1. **Confirm it is network-level, not provider-level** — verify `ProviderErrorCode` is absent. If a status is present, use [request-failed.md](./request-failed.md) instead.
2. **Read the connection resource file** — identify the connector and connection (see "Connection Resource File" in [overview.md](../overview.md)).
3. `uip is connections ping <connection-id>` — if ping also fails at the network layer, the problem is connectivity, not the operation.
4. **Determine the runtime environment** — the machine the job executed on (from the job's host identity): self-hosted robot / unattended machine vs UiPath-hosted cloud robot. Self-hosted egress rules differ from a developer's machine — debug may succeed where deployed fails.
5. On self-hosted robots: check the UiPath cloud host resolves and is reachable from that machine (DNS, firewall egress, proxy).

## Resolution

- **Self-hosted robot — DNS / firewall / proxy:** allowlist the UiPath cloud domains and outbound IP ranges from the robot's network, and configure proxy settings on the robot machine if required. Follow [Configuring the firewall](https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/configuring-firewall).
- **Self-hosted robot — TLS:** if a corporate proxy performs SSL inspection, install/trust the proxy's CA on the robot machine or exclude UiPath cloud domains from inspection.
- **UiPath-hosted cloud robot:** no customer-side network to fix — escalate to UiPath support with the `DAP` code, `RequestId`, and timestamp.
- **Sustained `retry-exception`:** retries are already exhausted; application-level retry will not help. Route to whoever owns network egress (customer network team for self-hosted; UiPath for cloud robots).
