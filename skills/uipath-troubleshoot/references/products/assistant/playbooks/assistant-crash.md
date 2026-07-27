---
confidence: low
---

# Assistant Crashes or Closes Unexpectedly

## Context

The Assistant window closes, goes white/blank, or freezes then dies — with or without an error. Low confidence: crashes have many causes and `combined.log` alone rarely captures the fatal frame.

What this looks like:
- `combined.log` ends abruptly with no clean shutdown line, or shows a main-process exception just before it stops.
- The **renderer** side (where most crashes originate) is not in `combined.log` — you need the **DevTools console** for an unhandled rejection / `Uncaught` error with a stack trace and function name.
- `Robot.log` usually keeps running (separate process) unless the crash is Robot-service-side.

What can cause it:
1. **Renderer exception** — an unhandled error/rejection in the Angular UI (blank window or immediate close). Evidence lives in DevTools console, not `combined.log`.
2. **Main-process exception** — an uncaught exception in the Electron main process → `combined.log` shows it as the last line.
3. **Robot-service crash** — the native service died; `Robot.log` ends with a fatal trace and the Assistant loses its backend.
4. **Environment** — GPU/driver (white screen), out-of-memory, or antivirus killing the process — no in-app trace; corroborate with Windows Event Viewer.

What to look for:
- **Is it reproducible on a specific action?** If so, treat it as that action's failure first (sign-in / connect / start) — the crash may be a symptom, not the root.
- Which process died — Assistant (Electron) vs Robot service — decides `combined.log`/DevTools vs `Robot.log`.

## Investigation

1. Anchor: does the crash follow a specific action? If yes, run that action's playbook first; a crash on sign-in/connect/start is usually the underlying failure surfacing.
2. Read the **tail** of `combined.log` — a main-process exception on the last line → cause 2; a clean-then-gone tail with a blank UI → cause 1, **ask for the DevTools console** (the renderer stack is the whole answer).
3. If `Robot.log` ends with a fatal trace at the crash time (timezone-convert) → cause 3; route the exception class via `summary.md`.
4. If no app-side trace anywhere → cause 4; ask for **Windows Event Viewer** (Application log) entries for `UiPath.Assistant` / `.NET Runtime` at the crash time, and GPU/AV details.

## Resolution

- **Cause 1 (renderer):** capture the DevTools stack (component/service name + error); apply a workaround for the specific error and report the crash to UiPath support with the stack.
- **Cause 2 (main process):** capture the `combined.log` exception (handler + stack) and report it to UiPath support.
- **Cause 3 (Robot service):** route the `Robot.log` fatal exception via `summary.md`; if it maps to sign-in/connect/start, fix that root cause.
- **Cause 4 (environment):** disable GPU acceleration for the white-screen/driver case, raise available memory, or add an AV exclusion for the Assistant/Robot executables per the Event Viewer evidence.
