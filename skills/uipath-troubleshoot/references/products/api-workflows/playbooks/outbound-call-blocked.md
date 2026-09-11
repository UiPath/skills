---
confidence: medium
---

# Outbound Call to an External System Blocked — Wrong IP Range Allowlisted

## Context

What this looks like:
- A Connector or HTTP activity calling a **customer-controlled or firewalled** endpoint times out, is refused, or is rejected by the target's edge — while calls to public endpoints from the same workflow succeed
- The connection itself is healthy: `uip is connections ping <connection-uuid> --output json` returns `Code: "ConnectionPing"`
- The target system's own logs show the request either never arriving, or arriving from an IP its firewall does not recognize
- It is reproducible and endpoint-specific, not intermittent

**Discriminator.** This is not an auth failure. An auth-shaped 401/403 from the Integration Service proxy → [connection-auth-failure.md](./connection-auth-failure.md). This playbook is for a request the target never accepted at the network layer, with a clean connection behind it.

**Why this is an API-Workflow-specific trap.** An API workflow has **two outbound paths**, and which one a call takes depends on the activity and its authentication mode:

| Path | Which calls take it | Allowlist the target must have |
|---|---|---|
| **Serverless robots** | `HTTP` activity using **manual authentication** | [Serverless static IPs](https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/static-ip-configuration) |
| **Integration Service** | `HTTP` activity using **connector-based authentication**, plus **every Connector activity** regardless of auth mode | [Integration Service IPs](https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/configuring-firewall#integration-service) |

So two activities in the same workflow, hitting the same host, can egress from two different IP ranges. A firewall allowlisted for one path blocks the other — which is why "it works from the connector but not from the HTTP activity" (or the reverse) is the classic presentation. Allowlisting is required **only** for external communication; UiPath-internal traffic needs none.

What to look for:
- The failing activity's **kind and authentication mode** — this alone determines which path it egressed from, and therefore which IP range had to be allowlisted
- Whether a *different* activity in the same workflow reaches the same host successfully. If so, compare their auth modes before anything else; that contrast is the diagnosis
- Whether the target is behind a customer firewall, a private network, or an IP-restricted SaaS tenant. A fully public endpoint does not produce this fault
- Timing: this appears the first time a workflow calls a restricted system, or after the target's network team changed the allowlist — not gradually

## Investigation

1. Read the failing activity's result payload for the network-layer symptom (timeout, connection refused, or a target-side rejection page rather than an API error body): `uip or jobs get <job-key> --output json`, `uip or jobs logs <job-key> --output json`.
2. Establish the connection is healthy, to separate this from the auth family: `uip is connections ping <connection-uuid> --output json`. A clean ping plus a failing call to a restricted host is the signature.
3. Determine the egress path from the workflow JSON — this is the decisive step. Read the failing activity's `call` and `bodyParameters.authentication`:
   - `call: "UiPath.Http"` with `authentication: "manual"` → **serverless robots** path
   - `call: "UiPath.Http"` with `authentication: "connector"` → **Integration Service** path
   - `call: "UiPath.IntSvc"` (any Connector activity) → **Integration Service** path
4. Compare against any activity in the same workflow that **does** reach the host. A working call on the other path confirms the allowlist covers one range and not the other.
5. Ask the user to check the target's firewall/allowlist against the IP set for the path identified in step 3, and to check the target's inbound logs for a rejected source IP. This is evidence only the user can supply — the CLI cannot see the target's firewall.
6. Local runs prove nothing here. `uip api-workflow run --no-auth` egresses from the developer's own machine, so a workflow that works locally and fails in cloud is consistent with this fault and does not rule it out.

## Resolution

- **If the wrong range is allowlisted:** the target's network owner adds the IP set for the path the activity actually uses (step 3). Recommendation-only — this is a change on the customer's side, outside UiPath. Give them the specific range and the reason, not just a link.
- **If a workflow deliberately mixes paths against one restricted host:** allowlist both ranges, or make the calls consistent — move the manual-auth HTTP activity onto the connector's connection (`authentication: "connector"`) so everything egresses via Integration Service and only one range needs allowlisting.
- **If the target cannot allowlist cloud ranges at all:** the integration needs a different topology. Escalate — this is an architecture decision, not a workflow fix.
- **Cross-reference:** for the connection's own auth internals, see the **Integration Service** product.
