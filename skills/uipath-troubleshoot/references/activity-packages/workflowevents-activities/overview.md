# App Events (Workflow Events) Activities

Activities from the `UiPath.WorkflowEvents.Activities` package. These are **internal** machinery that connects a **UiPath App** (or a Studio Web app preview) to the robot that runs the App's workflows — they are marked `[Internal]` and a user never drags them onto a canvas. They appear only inside a process that an App invokes.

So the user-visible failure is **"a job invoked by my App faulted"** — the faulted activity name (`HandleAppRequest`, `AppRequestTrigger`, `InitializeHubConnection`) shows up in the job error / trace spans, **not** in the user's project. Treat the activity as the location the fault surfaced, not a control the user can edit.

## Two connection modes

A UiPath App talks to the robot over one of two channels; the same activities run on both:

- **RobotJS** (legacy, default) — a local message channel between the App host and the robot via the executor's `WorkflowCommunication`.
- **SignalR** (modern, Studio Web) — a SignalR hub connection over WebSockets / Server-Sent Events / long-polling. `InitializeHubConnection` sets it up; the trigger and handler ride it.

## Exceptions propagate raw

These activities do **NOT** wrap failures in a package-specific exception type. They surface raw .NET framework exceptions (`NullReferenceException`, `TimeoutException`, `IOException`, `InvalidOperationException`, `AggregateException`) from the SignalR / HTTP / transport / runtime layer. So the **faulted activity class plus the exception class** — not a unique message string — is the primary discriminator. The same exception type on two different activities is a different investigation.

## Key activity types

- **Initialize Apps Hub Connection** (`NetCore.Activities.InitializeHubConnection`) — Studio Web only. At workflow start it resolves the Apps/Orchestrator resource URL and an access token, then kicks off the SignalR hub connection. The hub `StartConnectionAsync` runs on a background thread whose errors are **logged, not thrown** — so a job-faulting `System.AggregateException` comes from the **synchronous** bootstrap (resource-URL / token acquisition, or an invalid session/URL → `WorkflowApplicationException`), wrapped by the async-activity framework. Unwrap the inner exception.
- **Apps Request Trigger** (`AppRequestTrigger`) — waits for the App to send invoke-workflow requests and periodic heartbeats over the channel. A missed heartbeat is handled gracefully (it signals "connection lost", no fault). The activity **faults** when the request-listener leg cannot establish or loses the channel — `TimeoutException` (SignalR connection never established), `IOException` (transport/pipe dropped while awaiting a request), or `InvalidOperationException` (SignalR client in an invalid state). These are channel/transport failures, not the user's workflow logic.
- **Handle Apps Request** (`HandleAppRequest`) — runs the workflow the App invoked and sends the result back over the channel. The invoked workflow's own exception is **captured and returned to the App**, not rethrown — so a job-faulting `System.NullReferenceException` at this activity is almost always a **null dereference inside the App-invoked workflow** (or a required input argument the App did not supply), surfaced through the Apps invocation machinery. Investigate the invoked workflow, not the package internals.

## Package

Namespace / assembly: `UiPath.WorkflowEvents.Activities` (with the Studio-Web-only `NetCore.Activities.InitializeHubConnection`). Ships with the UiPath Apps / Studio Web runtime, not as a toolbox package users add.
