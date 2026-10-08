---
confidence: medium
---

# Outbound Call to an External System Blocked — Wrong IP Range Allowlisted

## Context

What this looks like:
- A Connector or HTTP activity calling a customer-controlled or firewalled endpoint times out, is refused, or is turned away by the target — while calls to public endpoints from the same workflow work fine
- The connection is healthy: `uip is connections ping <CONNECTION_UUID> --output json` returns `Code: "ConnectionPing"`
- The target's own logs show the request never arriving, or arriving from an IP address its firewall doesn't recognise
- It happens every time, to that one endpoint. It is not intermittent, and it starts either the first time the workflow calls that system or right after the target's network team changed something

**This is not an authentication failure.** A 401 or 403 from the Integration Service proxy belongs in [connection-auth-failure.md](./connection-auth-failure.md). This playbook is for a request the target never accepted at all, with a healthy connection behind it.

An API workflow reaches the outside world by **two different routes**, and which one a call takes depends on the activity and how it authenticates:

| Route | Calls that take it | What the target has to allow |
|---|---|---|
| **Serverless robots** | An `HTTP` activity using **manual** authentication | [Serverless static IPs](https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/static-ip-configuration) |
| **Integration Service** | An `HTTP` activity using **connector-based** authentication, and every Connector activity whatever its auth | [Integration Service IPs](https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/configuring-firewall#integration-service) |

So two activities in the same workflow, calling the same host, can arrive from two different IP ranges. A firewall that allows one route blocks the other — which is why "it works from the connector but not from the HTTP activity", or the other way round, is how this usually gets reported. Only external calls need allowlisting; traffic inside UiPath needs none.

## Investigation

1. Read the failing activity's result for the network-level symptom — a timeout, a refused connection, or a rejection page from the target rather than a proper API error: `uip or jobs get <JOB_KEY> --output json`, then `uip or jobs logs <JOB_KEY> --level Error --output json`.
2. Confirm the connection is healthy, which is what separates this from an auth problem: `uip is connections ping <CONNECTION_UUID> --output json`. A healthy ping plus a failing call to a restricted host is the signature.
3. Work out which route the call took, from the workflow file. This is the step that decides the answer. Read the failing activity's `call` and `bodyParameters.authentication`:
   - `call: "UiPath.Http"` with `authentication: "manual"` → serverless robots
   - `call: "UiPath.Http"` with `authentication: "connector"` → Integration Service
   - `call: "UiPath.IntSvc"` (any Connector activity) → Integration Service
4. Compare it against any activity in the same workflow that *does* reach that host. If one works and one doesn't, and they take different routes, that is your answer.
5. Ask the user to check the target's firewall against the IP range for the route you identified in step 3, and to look in the target's inbound logs for a rejected source IP. Only they can get this — the CLI cannot see the customer's firewall.
6. A local run tells you nothing here. `uip api-workflow run --no-auth` goes out from the developer's own machine, so "works locally, fails in the cloud" fits this problem and does not rule it out.

## Resolution

- **Wrong range allowed:** the target's network owner needs to add the IP range for the route the activity actually uses (step 3). You can only recommend this — the change is on the customer's side, outside UiPath. Give them the specific range and the reason, not just a link.
- **The workflow mixes both routes against one restricted host:** either allow both ranges, or make the calls consistent — switch the manual-auth HTTP activity onto the connector's connection (`authentication: "connector"`) so everything leaves through Integration Service and only one range needs allowing.
- **The target cannot allow cloud IP ranges at all:** the integration needs a different design. Escalate — that is an architecture decision, not a workflow fix.
- **Related:** for how the connection itself authenticates, see the **Integration Service** product.
