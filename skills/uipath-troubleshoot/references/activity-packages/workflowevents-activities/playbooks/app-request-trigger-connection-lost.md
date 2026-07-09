---
confidence: medium
---

# Apps Request Trigger — Connection / Transport Lost (Timeout / IOException / InvalidOperation)

## Context

What this looks like — a job invoked by a **UiPath App** faults at `AppRequestTrigger` (display name **Apps Request Trigger**) with one of:

- `System.TimeoutException` — message `SignalR connection did not establish within 60 seconds. Current state: <state>` (SignalR mode). The hub connection never reached `Connected` while the trigger waited.
- `System.IO.IOException` — the underlying transport (SignalR socket, or the RobotJS pipe) dropped while the trigger was awaiting a request from the App.
- `System.InvalidOperationException` — the SignalR client was driven in an invalid state (e.g. invoked on a connection that is not connected / was disposed).

`AppRequestTrigger` is internal Apps machinery the user never placed. It waits for the App to send invoke-workflow requests and heartbeats. A **missed heartbeat is handled gracefully** (it signals "connection lost" without faulting); the job faults only when the request-listener leg cannot establish or loses the channel and rethrows the error through the trigger's bookmark. All three signatures are the same root domain: **the App↔robot channel failed**, not the user's workflow logic.

What can cause it:
- **The App never connected within the timeout** — the App instance closed, crashed, or was never opened against this run; or the SignalR hub was unreachable, so the connection stayed un-established for 60s (`TimeoutException`).
- **Network / transport drop** — the WebSocket/long-polling transport (or the local RobotJS pipe) was interrupted mid-wait by a network fluctuation, proxy/idle timeout, or the App host going away (`IOException`).
- **Invalid channel state** — the hub connection was lost/disposed and an operation was attempted on it, or a reconnect left the client in a non-connected state (`InvalidOperationException`).

What to look for:
- **Which exception type** — it selects the branch (establish-timeout vs transport-drop vs invalid-state).
- **Whether the App instance was alive** for the run — a closed/crashed App or one never opened is the most common cause of the establish-timeout.
- **Connection mode** — SignalR (Studio Web / modern Apps) vs RobotJS (legacy). The `SignalR connection did not establish` message is SignalR mode; a RobotJS pipe drop surfaces as `IOException`.
- **Network conditions on the robot host** — proxy, idle-socket, or firewall behavior that severs long-lived connections.

## Investigation

1. **Confirm the signature + activity.** `uip or jobs get <job-key> --output json` → `Info` shows `System.TimeoutException` / `System.IO.IOException` / `System.InvalidOperationException`; the faulted activity is `AppRequestTrigger`.
2. **Read the message and branch:** the `SignalR connection did not establish within 60 seconds` text → establish-timeout; a transport/IO phrase → connection drop; an invalid-operation message → invalid hub state.
3. **Check the App side** — was the App instance open and connected for this run, or did it close / fail to open? An App that is not connected can never complete the handshake.
4. **Check the robot host's connectivity** to the SignalR hub (network fluctuation, proxy, idle-connection timeout) for the transport-drop and timeout branches.

## Resolution

- **Establish-timeout (`TimeoutException`):** ensure the UiPath App is actually open and connected to this run before/while the workflow waits; confirm the robot host can reach the SignalR hub (network/proxy/firewall). The trigger waits 60s — a connection that never forms means the App side never attached, not that the timeout is too short.
- **Transport drop (`IOException`):** treat as an environmental connection loss — verify network stability between the robot host and the hub, and proxy/idle-socket timeouts that sever long-lived connections; re-run once connectivity is stable. Recurring drops on the same network path point at the proxy/firewall.
- **Invalid channel state (`InvalidOperationException`):** the channel was lost/disposed before the operation — resolve the underlying disconnect (as for the transport-drop branch); if it reproduces deterministically on a specific App/runtime version, capture the trace and report it as an Apps runtime issue.
- These are platform/transport failures — do not look for a fix inside the user's workflow logic.
