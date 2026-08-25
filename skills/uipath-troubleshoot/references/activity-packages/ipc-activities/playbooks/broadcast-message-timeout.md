---
confidence: medium
---

# Broadcast Message — System.TimeoutException (No Channel / Receiver Found)

## Context

What this looks like:
- Activity `Broadcast Message` / `Send Message` (`UiPath.IPC.Activities.BroadcastMessage` / `SendMessage`) faults with `System.TimeoutException`
- Message: `Timeout of <N> ms has passed and no channel was found to send the message to.`
- May be intermittent — succeeds when the receiver is up in time, faults when it is not

What can cause it:
- The activity searches for an active **Message Receiver Trigger** listening on the configured `Channel`, up to `Timeout` (ms). The timeout expired before a live receiver was found. Root causes:
  - **Receiver not running in parallel** — the receiver process was not launched, was launched *after* the broadcast, was still initializing its listener loop, or had already exited when the sender broadcast.
  - **Channel-string mismatch** — the receiver is up, but its `Channel` does not match the sender's **exactly** (the comparison is case-sensitive). To the sender this is indistinguishable from "no receiver".
  - **`Timeout` too low** — the receiver comes up legitimately but slower than the configured window, so the search expires first.

What to look for:
- Whether a Message Receiver Trigger process on the **same channel** was alive and past initialization at the broadcast instant.
- The sender's `Channel` string vs the receiver's, character-for-character (case-sensitive).
- The launch ordering — is the receiver started **before** the broadcast?

## Investigation

1. Confirm the faulted activity is `Broadcast Message` / `Send Message` and the exception is `System.TimeoutException` with the `no channel was found` message; capture `<N>` (the configured `Timeout`).
2. Read the sender `.xaml` for the literal `Channel` string and `Timeout` value.
3. Ask the user (or someone with robot access) whether the receiver process (Message Receiver Trigger) was running in parallel on the **exact same channel** at the broadcast time, and how/when it is launched relative to the sender.

## Resolution

- **Launch the receiver in parallel first** — start the Message Receiver Trigger process **before** the sender broadcasts, e.g. via a `Run Parallel Process` activity or a background job, and confirm its listener is initialized. IPC requires the receiver to be actively listening at the moment of the broadcast.
- **Match the channel string exactly** — verify both sides use the identical, case-sensitive `Channel` value (prefer a shared config asset / constant over hand-typed literals to avoid `OrderBus` vs `orderbus` drift).
- **Raise the `Timeout`** — set `Timeout` to at least **5000–10000 ms** so the receiver has time to initialize its listener loop before the search expires. Do not set it too low. (`Timeout = 0` drops the message immediately with **no** exception — a different, silent failure mode.)
- **Wrap in Try Catch** — if a receiver may legitimately be absent, wrap `Broadcast Message` in a Try Catch to handle the `TimeoutException` gracefully rather than faulting the job.

> Related: a receiver that IS up on the same channel but the pipe endpoint denies the connection (different session / user / elevation) throws `System.UnauthorizedAccessException`, not a timeout → [broadcast-message-unauthorized-access.md](./broadcast-message-unauthorized-access.md).
