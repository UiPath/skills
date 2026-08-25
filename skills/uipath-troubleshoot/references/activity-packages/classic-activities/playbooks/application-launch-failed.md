---
confidence: medium
---

# Application Could Not Launch

## Context

`Open Application` (or `Open Browser` launching the browser executable) could not start the target
application, so the scope had no window to attach to.

What this looks like:
- The activity fails at or shortly after launch, before any inner activity runs
- A validation error "Both FileName and Arguments arguments are null. You should pass at least one of
  them" (neither `FileName` nor `Arguments` was provided)
- The application starts but never produces the expected window, so the scope's selector then fails
  to attach

What can cause it:
- The executable / file path in `FileName` does not exist on the robot machine, or is a path that is
  valid on the developer machine but not on the robot
- Neither `FileName` nor `Arguments` is set
- The arguments are malformed or the working directory is wrong, so the process exits immediately
- The application requires elevation/permissions the robot account does not have
- The app launches a splash/loader and the real window appears later than the scope expects, or under
  a different selector than configured
- The application is already running in a mode that prevents a second instance from starting

What to look for:
- The exact `FileName`, `Arguments`, and selector configured on the activity
- Whether that executable path exists on the robot machine (not just the dev machine)
- Whether a process actually started (and immediately exited) vs. never started
- Whether the scope selector matches the window the app actually shows

## Investigation

1. Read the `FileName`, `Arguments`, and the scope selector from the failing activity.
2. Confirm the executable/file path exists and is launchable on the robot machine and account.
3. Confirm at least one of `FileName` / `Arguments` is set (the validation error fires when both are
   empty).
4. Launch the application manually with the same path/arguments on the robot machine to see whether
   it starts and what window it produces.
5. Compare the window the app actually shows against the scope selector — confirm they match.
6. Check whether the app needs elevation or is blocked by policy/AV on the robot machine.

## Resolution

- **If the path is missing/incorrect on the robot:** correct `FileName` to a path valid on the robot
  machine, or ensure the application is installed there.
- **If both FileName and Arguments are empty:** set at least one so the activity has something to
  launch.
- **If arguments/working directory are wrong:** fix them so the process starts and stays running.
- **If the window appears later or under a different selector:** point the scope selector at the
  window the app actually produces, and wait for that window rather than racing the cold start.
- **If elevation/permissions are missing:** grant the robot account what the app requires, or launch
  it through a supported elevated mechanism.
