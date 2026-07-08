---
confidence: medium
---

# Handle Apps Request — Null Reference (NullReferenceException)

## Context

What this looks like:
- A job invoked by a **UiPath App** faults with `System.NullReferenceException: Object reference not set to an instance of an object.`, and the faulted activity is `HandleAppRequest` (display name **Handle Apps Request**).
- `HandleAppRequest` is internal Apps machinery — the user never placed it. It runs the workflow the App invoked and returns the result. The invoked workflow's own exception is **captured and returned to the App, not rethrown**, so a job-faulting NRE at this activity is almost always raised **inside the App-invoked workflow**, surfaced here through the invocation layer.

What can cause it:
- **A null dereference in the App-invoked workflow.** A variable, argument, or object inside the workflow the App ran evaluates to `Nothing` and is dereferenced (the classic in-workflow NRE) — the App invocation is just the entry point.
- **A required input argument the App did not supply.** The App passes input arguments by name; a `null`/missing value the workflow then dereferences faults the same way. Mismatched argument name or type between the App's binding and the workflow's `In` arguments leaves the argument unset.
- **A wrong or missing workflow file binding.** The App points at a workflow whose argument contract differs from what the App sends, so a value the workflow assumes is present is null.

What to look for:
- **No SignalR / hub / transport phrase** in the message — a pure NRE means the failure is in workflow execution, not the channel. A channel/transport fault surfaces on `AppRequestTrigger` instead (see [app-request-trigger-connection-lost.md](./app-request-trigger-connection-lost.md)).
- **The invoked workflow's name and its `In` arguments** vs. what the App binds — the decisive signal.
- **The faulting frame in the stack** — it points inside the invoked workflow's activities, not the WorkflowEvents package internals.

## Investigation

1. **Confirm the signature + activity.** `uip or jobs get <job-key> --output json` → `Info` shows `System.NullReferenceException`; the faulted activity is `HandleAppRequest`.
2. **Identify the invoked workflow.** From traces (`uip or jobs traces <job-key> --output json`) read the workflow file the App invoked and the input arguments delivered to it.
3. **Read the faulting frame.** The stack points inside the invoked workflow — find which variable/argument was dereferenced.
4. **Compare the App's argument bindings to the workflow's `In` arguments** — name and type must match, and every value the workflow dereferences must be supplied non-null.

## Resolution

- **If the null originates in the invoked workflow's logic:** fix it in that workflow — assign the variable before use, or guard the null path (validate / default it) before the dereference. This is an ordinary in-workflow NRE; investigate it as one.
- **If a required input argument arrives null:** correct the App's binding so it supplies the value, and align the argument name/type with the workflow's `In` argument. Add a guard in the workflow for the missing-input case.
- **If the App points at the wrong workflow / a changed contract:** repoint the App at the intended workflow, or update the workflow's argument contract to match what the App sends.
