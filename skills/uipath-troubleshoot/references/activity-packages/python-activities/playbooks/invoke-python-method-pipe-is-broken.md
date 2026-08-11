---
confidence: medium
---

# Python Scope — Pipe is Broken / Error Invoking Python Method

## Context

What this looks like:
- `Invoke Python Method` or `Run Python Script` (sometimes `Python Scope` itself) faults with:
  - `Python Scope: Pipe is broken` / `Invoke Python Method: Pipe is broken`, or
  - `RemoteException wrapping System.IO.IOException: Pipe is broken`, or
  - `Error invoking Python method`.
- The same script "runs fine in my IDE / Jupyter / command prompt."
- The fault appears at the first activity that actually executes Python code, not at scope open.

What can cause it (the Python-side cause is hidden — UiPath only reports that the host process died):
- **Missing pip module in the scope's interpreter** — the script `import`s a third-party module (e.g. `pandas`, `numpy`, `requests`) that is installed in the developer's IDE interpreter but **not** in the interpreter the `Python Scope` `Path` resolves to. The `ModuleNotFoundError` kills the Python host before it can return; the pipe breaks. Most common cause.
- **Unhandled exception in the script** — any uncaught Python exception (bad data, a `KeyError`, a failed file open) crashes the host the same way.
- **Hard process exit** — the script calls `sys.exit()` / `os._exit()` / `quit()`, or a native extension segfaults, terminating the host.
- **Flooding stdout** — printing very large volumes to the console can overwhelm the pipe buffer and break communication.

What to look for:
- The script's `import` lines vs what is installed in the scope's interpreter (`<scope-path>\python.exe -m pip list`).
- Whether the interpreter the scope points to is the same one the user tested in their IDE.
- Any top-level `sys.exit` / `os._exit` / `quit`, or large `print` loops, in the script.
- Whether the script raises on the robot's input data specifically (works on dev data, fails on production data).

## Investigation

1. Read the error from job evidence. Confirm the signature is `Pipe is broken` / `Error invoking Python method` and the faulted activity is `Invoke Python Method` / `Run Python Script` (not an interpreter-resolution fault at `Python Scope` — that is a different playbook).
2. Read the `.py` file(s) referenced by `Load Python Script` / `Run Python Script` from the project source. List every `import`, especially third-party modules. Note any top-level `sys.exit` / `os._exit` / `quit` and any heavy stdout output.
3. Capture the `Python Scope` `Path` / `Version` / `Target` from the `.xaml` — this identifies the exact interpreter that runs at robot runtime.
4. Establish (ask the user if not in logs) whether the third-party modules are installed in **that** interpreter, and whether the IDE where it "runs fine" uses the same interpreter. These usually differ — that gap is the cause.
5. Have the user reproduce the real Python error out-of-band: run the script directly from the scope's interpreter, `<scope-path>\python.exe <script.py>`. The standalone run prints the true traceback (e.g. `ModuleNotFoundError: No module named 'pandas'`) that UiPath swallowed.

## Resolution

- **If a third-party module is missing from the scope's interpreter:** install it into that exact interpreter — `"<scope-path>\python.exe" -m pip install <module>` — not into the dev's IDE environment. On unattended robots, install under the robot user (or use a virtual environment and point `Path` at it). Re-run; the pipe no longer breaks.
- **If the script raises an unhandled exception:** wrap the body in `try/except`, log the real error, and re-raise or return a clean result so UiPath surfaces the cause instead of a broken pipe. Fix the underlying exception. Pin down whether it is data-dependent (only the robot's input triggers it).
- **If the script hard-exits or floods stdout:** remove `sys.exit()` / `os._exit()` / `quit()` from the invoked code path (let functions `return` instead), and stop printing large volumes to the console — write to a file or return the data via the method result.
- **General prevention:** keep Python logic in functions returning values (no top-level side-effects), standardize the robot interpreter (a checked-in `requirements.txt` installed into the scope's interpreter or venv), and confirm the script runs standalone from the robot interpreter before wiring it into the workflow.

If the failure persists after the imported modules are confirmed installed in the scope's interpreter and the script runs standalone from that interpreter, capture a `Verbose` robot log plus the standalone traceback and open a UiPath support case — residual cases are package/interpreter-version-specific.
