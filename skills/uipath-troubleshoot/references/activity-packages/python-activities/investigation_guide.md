# Python Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity's namespace and class match the reported failure (e.g., `UiPath.Python.Activities.InvokeMethod` / "Invoke Python Method", `UiPath.Python.Activities.PythonScope` / "Python Scope", `UiPath.Python.Activities.RunScript` / "Run Python Script"). A `Pipe is broken` fault at `Invoke Python Method` and an interpreter-resolution fault at `Python Scope` are different code paths — treat them as different.
- **Python script** — the `.py` file (or inline code) in evidence matches the script the user is asking about. `Load Python Script` / `Run Python Script` reference a specific `File`; a different script is unrelated data.
- **Interpreter identity** — the Python install the scope's `Path` / `Version` / `Target` resolves to matches the interpreter the user reports. The packages available at runtime are those installed in **that** interpreter, not the developer's IDE environment and not a different Python on the same host.
- **Robot / machine identity** — the robot account and the machine where Python is installed match the one the user reports. Python interop is per-machine and per-interpreter; evidence from the developer's machine (where "it runs fine") is not transferable to the robot host.
- **Run surface** — whether the run was foreground Studio / attended or unattended / Session 0 / background. Load-bearing for `WorkingFolder` / relative-path causes (the robot's CWD differs from Studio's) and for interpreter access (the robot user may not see a per-user Python install).
- **Package + runtime version** — the `UiPath.Python.Activities` version from `project.json`, the interpreter version, and the installed .NET Desktop Runtime. The pack supports a specific Python-version / runtime matrix; a skew here produces engine-init failures unrelated to the user's code.
- **Timestamp** — the failure occurred during the time window the user reported.

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## Testing Prerequisites

When testing hypotheses for `Python Scope` failures, gather and verify these before drawing conclusions:

1. **Activity identity** — confirm the faulted activity (`Python Scope`, `Load Python Script`, `Run Python Script`, `Invoke Python Method`, `Get Python Object`) and the exact error string. `Pipe is broken`, `The specified Python path is not valid`, and `One or more errors occurred` / `Error initializing the Python engine` map to different playbooks.
2. **Scope configuration** — from the `.xaml`, capture the `Python Scope` `Path`, `Library path`, `Version`, `Target`, and `WorkingFolder`. Check `Path` for the two classic traps: ending in `\python.exe`, or pointing at `...\WindowsApps\python`.
3. **Script source** — read the `.py` file(s) referenced by `Load Python Script` / `Run Python Script`. Note every `import` (third-party modules are the prime `Pipe is broken` suspect), any top-level `sys.exit` / `os._exit`, heavy stdout/print volume, and any relative file path the script opens.
4. **Interpreter packages** — whether the third-party modules the script imports are installed in the interpreter the scope's `Path` resolves to (not the dev's IDE). Not visible in the job log — the user (or someone with access to the robot host) confirms via `<scope-path>\python.exe -m pip list`.
5. **Interpreter bitness / version** — the actual install's bitness (x86 / x64) and version vs the scope's `Target` / `Version`. Run-surface dependent: a per-user install under the developer's profile may not exist for the robot user.
6. **Run surface** — foreground Studio Run/Debug vs attended vs unattended / Session 0. Confirms or eliminates the `WorkingFolder` CWD-divergence cause and per-user-interpreter visibility.
7. **Package + .NET runtime version** — `UiPath.Python.Activities` version from `project.json` and the installed .NET Desktop Runtime, checked against the pack's supported matrix.

### Out-of-band confirmation

The deciding proof for several Python causes lives on the robot host, not in the job log: whether the imported module is installed in the scope's interpreter (`pip list`), the interpreter's true bitness, and whether the script runs standalone from that exact interpreter (`<scope-path>\python.exe <script>`). Record these as out-of-band confirmation steps — they do not block a hypothesis when no alternative cause is better supported, but they are how the user closes the case.
