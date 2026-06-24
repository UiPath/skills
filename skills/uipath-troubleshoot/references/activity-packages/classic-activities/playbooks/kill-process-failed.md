---
confidence: low
---

# Kill Process Failed

## Context

`Kill Process` failed while trying to terminate one or more processes on the robot machine.

What this looks like:
- "Encountered errors while trying to kill a process" — one or more matched processes could not be
  terminated
- The activity targeted a process name or process object that no longer exists, or that the robot
  account is not allowed to terminate

What can cause it:
- No process matching the given name was running (already exited, or the name/case is wrong)
- The robot account lacks the privilege to terminate the process (a process owned by another user, a
  service, or a protected/system process)
- Several processes matched the name and at least one of them failed to terminate, so the errors are
  reported together
- The process is in a state where it cannot be killed immediately (hung, being debugged)

What to look for:
- The process name or process object the activity targeted
- Whether such a process was actually running at that moment, and under which user
- Whether multiple instances matched
- Whether `ContinueOnError` is set (which would suppress these failures)

## Investigation

1. Identify the target process name/object on the failing `Kill Process`.
2. Determine whether a matching process was running when the activity executed, and under which user
   account.
3. Check whether multiple instances matched and whether only some failed to terminate.
4. Confirm whether the robot account has rights to terminate that process (own user vs another user /
   service / protected process).

## Resolution

- **If no matching process was running:** guard the kill (only kill when present), or accept that
  there was nothing to terminate; check the name/case is correct.
- **If access is denied:** run with an account that has privilege to terminate the process, or target
  only processes the robot account owns.
- **If some of several instances failed:** handle each instance, or narrow the target so it matches
  only the intended process.
- **If the goal is best-effort cleanup:** consider whether `ContinueOnError` is appropriate so a
  non-critical kill does not fault the workflow — but only when the termination is genuinely optional.
