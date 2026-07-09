---
confidence: medium
---

# UI Activity Timeout — Element or State Never Reached

## Context

A classic UI Automation activity ran for its full timeout without the element or state it was
waiting for ever being reached, and threw `ActivityTimeoutException`. This is the typical signature
of `Wait UI Element Appear` (the element never appeared) and `Wait Image Vanish` (the image was
still present when the timeout expired), but any classic UI activity can time out waiting for its
target.

What this looks like:
- `ActivityTimeoutException`, or an error message such as "Activity timeout exceeded"
- The activity's duration is very close to its configured timeout (default is typically 30 seconds)
- For `Wait UI Element Appear`: the awaited element never showed up
- For `Wait Image Vanish`: the on-screen image never disappeared

What can cause it:
- The awaited element/state genuinely never occurs (the preceding action didn't take effect, the
  page/dialog never opened, the long-running operation never finished)
- The expected change happens later than the configured timeout (the timeout is too short for the
  real workload)
- For `Wait Image Vanish`: the image never vanishes because the underlying operation is stuck, or the
  matched image is slightly different from what's on screen so the match logic behaves unexpectedly
- The robot session is locked or in a disconnected RDP session, so the UI does not render/update
- An upstream step that should have triggered the change failed silently

What to look for:
- Is the faulted activity actually a UI automation type? `ActivityTimeoutException` can also come from
  non-UI waits — confirm the activity before applying this playbook
- Is the duration within 1–2 seconds of the configured timeout (genuine timeout) vs. failing early
  (different problem)?
- Is it consistent or intermittent? Intermittent points to timing/load; consistent points to a
  state that never occurs
- Was the robot session interactive and unlocked during the run?

## Investigation

1. Confirm the faulted activity is a classic UI activity and note its timeout value.
2. Compare the activity duration against the timeout to confirm it waited the full window.
3. Determine what the activity was waiting for (which element to appear, which image to vanish) and
   verify from logs/screenshots whether that change ever happened.
4. Check the upstream step that should have caused the change — confirm it actually executed and took
   effect.
5. Confirm the robot session was interactive and unlocked (locked/disconnected sessions stop the UI
   from updating).
6. If intermittent, correlate failures with system load or slower-than-usual application responses.

## Resolution

- **If the awaited change never happens because an upstream step didn't take effect:** fix the
  upstream step; the wait is correctly reporting that the expected state never arrived.
- **If the workload is genuinely slower than the timeout:** raise the timeout to a realistic value
  for the real workload — but only after confirming the change does eventually occur.
- **If the session was locked/disconnected:** run the process in an interactive, unlocked session.
- **If `Wait Image Vanish` never matches what's on screen:** verify the captured image still matches
  the current UI (scaling, resolution, theme); see [image-target-not-found.md](./image-target-not-found.md).
- Do not raise the timeout blindly — establish that the element/state can occur at all first.
