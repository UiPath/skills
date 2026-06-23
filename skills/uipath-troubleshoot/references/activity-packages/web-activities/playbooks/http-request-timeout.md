---
confidence: medium
---

# HTTP Client — Request Timed Out (TimeoutException)

## Context

What this looks like:
- A `UiPath.Web.Activities.HttpClient` activity faults with `System.TimeoutException` and the default message `The operation has timed out.`
- `HttpClient` throws this explicitly when the underlying RestSharp request returns status `TimedOut` — the request exceeded `TimeoutMS` (default `6000` ms).
- For the modern `NetHttpRequest` activity a timeout instead surfaces as `System.AggregateException` → inner `TaskCanceledException` — see [net-http-request-aggregate-failure.md](./net-http-request-aggregate-failure.md).

What can cause it:
- **Endpoint slower than `TimeoutMS`** — the server responds, but later than the configured budget (large payload, slow query, cold start).
- **`TimeoutMS` set too low** — a tight timeout for an endpoint that is legitimately slow.
- **Endpoint hung / not responding** — server overloaded or down; the request never completes.
- **Network latency / proxy stall** between the robot machine and the endpoint.

What to look for:
- **`TimeoutMS` value** in the workflow source vs the endpoint's realistic response time.
- **Whether the endpoint responds at all** when called manually from the robot machine, and how long it takes.
- **Recent-runs pattern** — if earlier runs succeeded and only recent ones time out, the endpoint slowed or degraded (not a config change).

## Investigation

1. **Confirm the signature + activity.** `uip or jobs get <job-key> --output json` → `Info` shows `System.TimeoutException: The operation has timed out.` and `JobError.ActivityName` = the `HttpClient` activity.
2. **Read `TimeoutMS` and `EndPoint` from source.** Note whether `TimeoutMS` is left at the `6000` ms default.
3. **Measure the endpoint** from the robot machine (or an equivalent network position): does it respond, and in how long relative to `TimeoutMS`?
4. **Check recent runs** for the same process (`uip or jobs list ... --output json`) — a shift from success to timeout points at endpoint degradation rather than a workflow change.

## Resolution

- **Endpoint legitimately slower than the budget:** raise `TimeoutMS` to cover the endpoint's real response time (with headroom).
- **Endpoint hung / down:** treat as a target-service availability problem — retry, or escalate to the API owner; raising the timeout alone will not help a non-responding server.
- **Network/proxy stall:** fix egress latency / proxy configuration on the robot machine.
- **Genuinely long operation:** if the endpoint is expected to take a long time, combine a higher `TimeoutMS` with a retry/backoff around the activity rather than an unbounded wait.
