# IPC Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity's namespace and class match the reported failure (`UiPath.IPC.Activities.BroadcastMessage`, `UiPath.IPC.Activities.SendMessage`). The activity is the discriminator, **not** the exception FQN: `System.TimeoutException` and `System.UnauthorizedAccessException` are generic framework types — routing to this package depends on the faulted-activity label (`[Broadcast Message]`) and a `UiPath.IPC.Activities.*` stack frame, not on the `System.*` prefix.
- **Exception class** — `System.TimeoutException` and `System.UnauthorizedAccessException` are distinct root causes with distinct fixes; do not apply one's cause to the other. `TimeoutException` = no receiver found on the channel in time (a **timing / channel-name** problem); `UnauthorizedAccessException` = the named-pipe endpoint denied the connection (a **session / user / elevation boundary** problem).
- **Channel** — the `Channel` string in evidence matches the channel the user is asking about, and is compared **case-sensitively** against the receiver's channel. A sender and receiver on different channel names are effectively unrelated even when both look healthy.
- **Sender / receiver pairing** — IPC always involves two sides. Confirm which process holds the `Broadcast Message` / `Send Message` (the faulted side) and which holds the `Message Receiver Trigger`. A fault on the sender with no corresponding running receiver is the core signal for the timeout case.
- **Robot / machine / session identity** — the sender and receiver run on the **same robot, same Windows user, same session, same machine**. Evidence showing the two processes on different hosts, different robot accounts, different user sessions, or different elevation levels is the core signal for the unauthorized-access case — not transferable "healthy" data from a co-located pair.
- **Package version** — the `UiPath.IPC.Activities` version in each project's `project.json`. A protocol/version mismatch between sender and receiver is a distinct cause from timeout/access-denied.
- **Timestamp** — the failure occurred during the time window the user reported, and the receiver process was (or was not) alive at the broadcast instant. Load-bearing for the timeout case — a receiver that started a second too late reproduces only with the same timing.

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## What to Capture

1. **Workflow source** — read the `Broadcast Message` / `Send Message` node from the `.xaml` to capture the literal `Channel` expression, the `Timeout` value, and the `Message` payload type. Property-panel summaries truncate; the XAML is authoritative.
2. **Receiver existence + channel** — whether a `Message Receiver Trigger` process exists, its exact `Channel` string, and whether it was **running in parallel** and past its listener-initialization at the broadcast instant.
3. **Launch ordering** — how and when the receiver process is started relative to the broadcast (e.g. a `Run Parallel Process` / background job launched **before** the sender broadcasts, vs launched after / not at all).
4. **Session / user / elevation** — the Windows session, user account, and elevation level of **both** the sender and receiver processes. Attended user session vs unattended Session 0, two different robot accounts, or one elevated + one not are the access-denied signals.
5. **Timeout value** — the literal `Timeout` (ms). `0` drops silently with no exception; a low value can expire before a legitimately-launched receiver finishes initializing.
6. **Package version** — `UiPath.IPC.Activities` version in both the sender and receiver `project.json`, compared against each other.

## Testing Prerequisites

When testing hypotheses for `Broadcast Message` / `Send Message` issues, gather and verify these before drawing conclusions:

1. **Activity identity** — confirm the faulted activity is `UiPath.IPC.Activities.BroadcastMessage` / `SendMessage` and the exception class (`TimeoutException` vs `UnauthorizedAccessException`) from the job error / logs.
2. **Receiver state** — whether a Message Receiver Trigger on the **exact same channel** was alive and listening in parallel at the broadcast instant. The user (or someone with desktop/robot access) must confirm; it cannot be inferred from the sender's log alone.
3. **Channel match** — the sender's `Channel` string character-for-character (case-sensitive) against the receiver's. A silent mismatch presents identically to "no receiver".
4. **Session/user/elevation parity** — for an access-denied fault, whether both processes run under the same session, user, and elevation. This is a host-level fact, not visible in job logs.
5. **Timeout adequacy** — the configured `Timeout` versus how long the receiver takes to come up; `0` means silent-drop, low values race the receiver's startup.
