---
confidence: medium
---

# Directory Not Found Exception

## Context

`System.IO.DirectoryNotFoundException` in the user's workflow code. A file or directory operation targeted a path whose directory portion does not exist. In `Assign` activities this comes from `System.IO` calls in expressions (`Directory.GetFiles`, `File.ReadAllText`, `new StreamReader`, `Directory.EnumerateFiles`) against a path whose parent directory is missing.

> A missing *file* when the directory exists throws `FileNotFoundException`; a missing *directory segment* in the path throws `DirectoryNotFoundException`. The message "Could not find a part of the path" points at the directory segment.

**Scope:** only applies when the exception originates from the user's workflow logic — a path the user's expression or argument passed to an I/O call. If the stack trace shows the fault deep inside an activity package namespace with no user code in the call chain, redirect to that package's troubleshooting.

What this looks like:
- Workflow faults with `System.IO.DirectoryNotFoundException`
- Error message: "Could not find a part of the path 'C:\…'." — the path is in the message
- Frequently environment-specific: works in Studio on the dev machine, fails on the unattended robot host

What can cause it:
- Hardcoded path that exists on the developer machine but not on the robot machine
- Path built from a config/asset value that is wrong or empty for the current environment
- Relative path resolved against an unexpected working directory at runtime
- Mapped network drive (e.g., `Z:\`) not mounted in the unattended robot session — use UNC
- A directory expected to be created upstream (Create Folder) that didn't run

What to look for:
- The full path in the exception message
- Where the path came from (literal, config, asset, environment variable, prior output)
- Whether the path is machine- or environment-specific (dev vs robot, attended vs unattended)

## Investigation

1. **Get the stack trace** — for local execution, list `%localappdata%\UiPath\logs\` and open the log for today's date (if not found, ask for the error date); for Orchestrator, get job traces. Confirm the top stack frames are in the user's workflow, not a package namespace
2. Locate the faulted activity in source code (typically an `Assign` calling `System.IO`) and read the path expression
3. Extract the failing path from the message and trace its source (literal, config key, asset, argument binding)
4. Determine why the directory is absent on the executing machine: is the path environment-specific? Is it a mapped drive unavailable to the robot session? Was an upstream Create Folder skipped?
5. If intermittent or environment-dependent: compare the path value between the machine where it works and the one where it fails

The root cause is WHY the directory was absent on the executing host (hardcoded dev path, wrong config for the environment, unmapped drive, missing upstream creation), not merely which I/O call threw.

## Resolution

- **If hardcoded dev path:** source the path from a per-environment config/asset; do not hardcode machine-specific paths
- **If mapped drive on unattended:** use a UNC path (`\\server\share\…`) — mapped drive letters are per-interactive-session and absent in unattended robots
- **If directory should exist first:** create it with `Directory.CreateDirectory(path)` or a Create Folder activity before writing
- **If path may be missing:** validate `Directory.Exists(path)` before the operation and handle the missing case explicitly (fail with a clear `BusinessException` naming the path)
