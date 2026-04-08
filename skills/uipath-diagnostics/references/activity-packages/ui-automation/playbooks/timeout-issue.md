---
confidence: low
---

# Timeout Issue

## Context

A UI automation activity exceeded its timeout waiting for an element or application state. The default timeout is typically 30 seconds.

TimeoutException is ambiguous — it could be a UI timeout (Check App State, element wait) or a non-UI timeout (HTTP request, queue transaction). Confirm the faulted activity is a UI automation type before following this playbook.

What this looks like:
- Activity waited the full timeout duration and threw TimeoutException
- The target element either never appeared or took too long to become interactable

What can cause it:
- Target element genuinely doesn't exist (page didn't load, navigation failed, wrong page)
- Application is slower than usual (server-side delay)
- Element exists but appears after the timeout window (timing gap)
- Robot session is locked or in a disconnected RDP session
- Picture-in-Picture (PiP) mode has different element visibility rules

What to look for:
- Is the faulted activity a UI automation type? If not, this playbook doesn't apply
- Is the activity duration close to the configured timeout? (within 1-2 seconds = genuine timeout)
- Is the issue intermittent (works sometimes, fails sometimes)?
- Is the robot session locked or disconnected?

## Resolution

- If application is genuinely slower: increase the timeout value in the activity properties
- If wrong page is displayed: fix the upstream navigation logic
- If timing gap: add a Check App State or Element Exists activity before the failing activity
- Do NOT just increase timeout blindly — find out why the element is delayed
