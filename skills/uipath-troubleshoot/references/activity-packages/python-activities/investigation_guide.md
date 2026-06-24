# Python Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity's namespace and class match the reported failure (`UiPath.Python.Activities.PythonScope`, `UiPath.Python.Activities.LoadScript`, `InvokeMethod`, `GetObject`). A `Load Python Script` fault is distinct from an invocation fault: a load failure means the scope/script never bound; an `Invoke Python Method` fault means the script loaded and the failure is in the called function.
- **Interpreter identity** — the Python install at the scope's `Path` on the robot host matches the interpreter the user tested. The same script behaves differently per interpreter: a venv/conda env in an IDE has different `site-packages` than a system Python or the env at `Path`. Evidence from the developer's IDE env is not transferable to the robot.
- **Bitness + version** — the installed interpreter's bitness matches `Target` (`x86`/`x64`), and its version is `≤` the max the `UiPath.Python.Activities` package supports. Bitness/version mismatch with the package or `Library path` is a known engine-init cause.
- **Robot / machine identity** — the robot account and the machine where Python is installed match the one the user reports. Python install location, `PATH`, the `pythonXX.dll`, and the .NET Desktop Runtime are per-machine; evidence from a different host is not transferable.
- **Package version** — the `UiPath.Python.Activities` version in `project.json` matches what is installed on the execution host, and supports the Python version in use.
- **Timestamp** — the failure occurred during the window the user reported (load-bearing for hang/timeout investigations).

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## What to Capture

1. **Workflow source** — read the `PythonScope` node from the `.xaml` for the literal `Path`, `Library path`, `Version`, `Target`, `WorkingFolder`, `Timeout`, and `Script Data Size Limit` expressions, and the `LoadScript` file path / inline script. Property-panel summaries truncate; the XAML is authoritative.
2. **The script itself** — the `.py` file (or inline text). Identify any **top-level (module-body) code** that runs at load: loose statements, `import` lines, and prints. `Load Python Script` executes the module body, so a top-level error crashes the load.
3. **Interpreter facts on the robot host** — Python version and bitness (`python --version`, `python -c "import struct;print(struct.calcsize('P')*8)"`), the install/venv folder, and whether the imported modules exist in *that* interpreter's `site-packages` (`python -m pip show <module>`).
4. **`Library path` correctness** — for Python > 3.9 on Windows, whether `Library path` points at the matching `pythonXX.dll`; for ≤ 3.9 on Windows, whether it is (correctly) empty; on Linux, the `libpythonXX.so` path.
5. **.NET Desktop Runtime** — whether .NET Desktop Runtime 6+ is installed on the host (`dotnet --list-runtimes` → look for `Microsoft.WindowsDesktop.App 6/8`). Required for Windows projects on package v1.9.0+.
6. **Package version** — `UiPath.Python.Activities` in `project.json` vs the version restored on the execution host, and whether it supports the target Python version.

## Testing Prerequisites

Before drawing conclusions, gather and verify:

1. **Script runs standalone** — the exact `python.exe` from the scope's `Path` runs the script from a Windows Command Prompt with the scope's `WorkingFolder` as the current directory (`cd <WorkingFolder> && "<Path>\python.exe" script.py`). If it fails there, the fault is the environment/script, not UiPath.
2. **Interpreter ↔ scope alignment** — confirmed bitness match (`Target` vs interpreter), version `≤` package max, and `Library path` set per the > 3.9 rule.
3. **Module availability** — every imported third-party module is installed in the interpreter at `Path`, not only in the IDE's venv/conda env.
4. **Load vs invoke isolation** — confirm whether the failure is at load (`LoadScript`) or at invocation (`InvokeMethod`); they have different root causes and fixes.
