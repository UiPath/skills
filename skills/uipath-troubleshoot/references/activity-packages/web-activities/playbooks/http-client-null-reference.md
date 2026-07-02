---
confidence: medium
signatures:
  - kind: exception
    value: "System.NullReferenceException"
    note: "on UiPath.Web.Activities.HttpClient — a request input (EndPoint, header, cookie, parameter, body) resolved null during request building; no HTTP status or transport phrase in the message"
exclusions:
  - "WebException with an HTTP status or transport phrase → http-request-connection-failure.md"
---

# HTTP Client — Null Reference (NullReferenceException)

## Context

What this looks like:
- A `UiPath.Web.Activities.HttpClient` activity faults with `System.NullReferenceException: Object reference not set to an instance of an object.`
- The exception is raised inside the activity while it builds the request (resolving endpoint, headers, cookies, parameters) or while reading the response — `HttpClient` does not wrap it.

What can cause it:
- **A request input resolves to null** — a workflow variable wired into `EndPoint`, a header value, a cookie value, a parameter, or the body evaluates to `Nothing` at runtime and is dereferenced during request building. (`EndPoint` is a required argument, but a bound variable can still evaluate to null.)
- **Null upstream value** — the null came from a prior activity that returned nothing (e.g., an unset asset, an empty config read, an earlier HTTP call whose output was never set), then was passed into this activity.
- **Response dereferenced after `ContinueOnError`** — a prior `HttpClient` with `ContinueOnError = True` returned an empty response, and a downstream expression reads `.Result` / a header off it.

What to look for:
- **Which input is null** — from the workflow source, list every variable feeding `EndPoint`, `Headers`, `Cookies`, `Parameters`, and `Body`, and trace where each is assigned.
- **The activity immediately before** the faulted one — a common source of the null value.
- **No HTTP status / transport phrase** in the message — distinguishes this from `WebException` ([http-request-connection-failure.md](./http-request-connection-failure.md)); a pure NRE means the request was never sent.

## Investigation

1. **Confirm the signature + activity.** `uip or jobs get <job-key> --output json` → `Info` shows `System.NullReferenceException` and `JobError.ActivityName` = the `HttpClient` activity. The absence of any HTTP status code or transport phrase means the failure is in request building, not the call.
2. **Enumerate the activity's inputs from source.** Capture every variable/expression feeding `EndPoint`, `Headers`, `Cookies`, `Parameters`, `Body`.
3. **Trace each input to its assignment.** Find which one can be `Nothing` on the failing path — an unset variable, a no-result upstream activity, or a config/asset that was empty.
4. **Check for an upstream `ContinueOnError` HTTP call** whose empty response is dereferenced here.

## Resolution

- **Null input variable:** ensure the variable is assigned a non-null value before the activity, or add a guard (validate / default it) on the path that reaches the HTTP Client.
- **Null from an upstream activity:** fix the upstream activity so it returns a value, or handle its empty result explicitly before passing it on.
- **Empty response after `ContinueOnError`:** check the prior call's `StatusCode` / result for success before dereferencing it; do not assume a response exists when `ContinueOnError` is on.
