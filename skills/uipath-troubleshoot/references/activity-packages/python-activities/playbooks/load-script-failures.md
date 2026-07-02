---
confidence: medium
signatures:
  - kind: message
    value: "The specified Python path is not valid"
    note: "surfacing at Load Python Script (first scope child) — engine init, scope Path misconfigured (L1a); dedicated diagnostic → python-path-not-valid.md"
  - kind: message
    value: "Error initializing Python engine"
    note: "engine init at the scope layer (L1b-L1e: bitness, Library path, unsupported version, missing .NET Desktop Runtime); see also python-scope-architecture-version-mismatch.md"
  - kind: message
    value: "Error loading the python script"
    note: "script-layer failure executing the module body (L2: syntax error, top-level exception, failed import)"
  - kind: message
    value: "ModuleNotFoundError: No module named"
    note: "top-level import missing from the interpreter at the scope's Path (L2a); lazy import inside a called function → invoke-method-failures.md"
  - kind: message
    value: "One or more errors occurred"
    note: "at Load Python Script — wrapper around a script-layer load failure (L2); at engine init → python-scope-architecture-version-mismatch.md; on Invoke Python Method → invoke-method-failures.md"
---

# Load Python Script (LoadScript) Failures

## Context

`UiPath.Python.Activities.LoadScript` ("Load Python Script") runs inside a `Python Scope`, reads a `.py` file (or inline script text), **executes the module body to bind the functions/objects it defines**, and returns a `PythonObject` for downstream `Invoke Python Method`. A `LoadScript` failure means execution never got past load — either the `Python Scope` could not initialize the engine (a scope-layer fault that surfaces when the first child runs) or the script itself failed to load/import. Invocation-time failures (a called function throwing) are out of scope — that is `Invoke Python Method`.

A strong tell: the script runs fine in an IDE (PyCharm / VS Code) but fails under UiPath. The IDE uses its own venv/conda environment; the `Python Scope` only sees the interpreter at its `Path` plus Windows environment variables, and does **not** auto-activate a venv/conda env.

What this looks like:
- `The specified Python path is not valid` (even when `python.exe` opens manually).
- `Error initializing Python engine 64 bit` / engine fails to start.
- `One or more errors occurred` / `Error loading the python script` (generic wrapper around a Python-side syntax error, top-level exception, or failed import).
- `ModuleNotFoundError: No module named 'xyz'`.
- The scope hangs indefinitely on load, or fails with a data-size error.

## Causes

Name the confirmed sub-cause exactly. Do NOT assert a cause unless the investigation arrived at it.

- **L1. Engine initialization failure (scope layer).** The `Python Scope` cannot stand up the interpreter, so `LoadScript` (the first child) is where it surfaces. Sub-causes:
  - **L1a. `Path` wrong.** `Path` must be the **Python installation or virtual-environment folder** (the one whose `python.exe` and `site-packages` you want) — not the path to `python.exe` itself, and not a "libraries" folder. A trailing slash or a path that resolves only on the developer machine produces `The specified Python path is not valid`.
  - **L1b. Bitness mismatch.** `Target` (`x86`/`x64`) does not match the installed interpreter's bitness. Produces `Error initializing Python engine`. The interpreter bitness — not the OS — is what `Target` must match.
  - **L1c. `Library path` wrong/missing for Python > 3.9 (Windows).** On Windows with Python **> 3.9**, `Library path` must point at the matching `pythonXX.dll` (e.g. `python311.dll`); leaving it empty fails engine init. On Windows with Python **≤ 3.9** it must be **empty**. On Linux it must point at `libpythonXX.so`.
  - **L1d. `Version` unsupported by the package.** The pinned `Version` (or an `Auto`-detected interpreter) is newer than the `UiPath.Python.Activities` package supports (3.10→v1.6.0, 3.11→v1.7.1, 3.12→v1.8.1, 3.13→v1.10.0, 3.14→v2.2.1).
  - **L1e. .NET Desktop Runtime missing.** Windows projects on package **v1.9.0+** require the **.NET Desktop Runtime 6+** (.NET 8 also supported). Without it the engine cannot initialize.
- **L2. Script load / compile / import error (script layer).** The engine initialized, but executing the module body failed. Surfaces as `One or more errors occurred` / `Error loading the python script`. Sub-causes:
  - **L2a. `ModuleNotFoundError`.** The interpreter at `Path` lacks the imported package. The IDE had it (different env); the robot's interpreter does not. Most common when `Path` points at a system Python while the dependencies live in a venv/conda env (or vice-versa).
  - **L2b. Syntax error or top-level exception.** A syntax typo, or loose executable code at module level that raises during load. `LoadScript` runs the module body, so anything outside a `def` executes at load time.
  - **L2c. Unresolved local import.** The script `import`s a sibling `.py` that is not found because `WorkingFolder` does not point at the script's project root, so the relative import path resolves wrong.
- **L3. Hang or oversized data.** The script loads but the workflow stalls or errors on volume. Sub-causes: excessive stdout during load freezing the engine pipe; a long-running load exceeding `Timeout`; or a returned object larger than the **Script Data Size Limit** (default 25 MB).

## Investigation

1. **Read the scope + script from the `.xaml`.** Capture `Path`, `Library path`, `Version`, `Target`, `WorkingFolder`, and the `LoadScript` file path / inline text. Note any top-level (non-`def`) code in the script.
2. **Decision tree** (stop at the first match):
   - `The specified Python path is not valid` / `Error initializing Python engine` → **L1**. Work the sub-causes in order: confirm `Path` is the install/venv **folder** (L1a); compare interpreter bitness to `Target` (L1b); for Python **> 3.9** on Windows confirm `Library path` points at `pythonXX.dll`, for ≤ 3.9 confirm it is empty (L1c); confirm the Python version is `≤` the package max (L1d); confirm .NET Desktop Runtime 6+ is installed (L1e).
   - `ModuleNotFoundError: No module named 'xyz'` → **L2a**. Confirm whether `xyz` is installed in the interpreter at `Path` (not the IDE env).
   - `One or more errors occurred` / `Error loading the python script` with no module error → **L2b/L2c**. Look for top-level code and local imports.
   - Hang, timeout, or a data-size error → **L3**.
3. **Run the script standalone with the scope's interpreter** (decisive for L1 vs L2): `cd <WorkingFolder>` then `"<Path>\python.exe" your_script.py`. If it fails here, the fault is the environment/script (L1c/L1d at the interpreter level, or L2) — not UiPath wiring. If it succeeds here but fails in UiPath, the fault is scope configuration (L1a/L1b/L1e) or `WorkingFolder` (L2c).
4. **For L2a, prove the gap:** `"<Path>\python.exe" -m pip show <module>` against the interpreter at `Path`. Empty output → the module is not in that environment.
5. **Confirm the interpreter facts:** version (`python --version`) and bitness (`python -c "import struct;print(struct.calcsize('P')*8)"`); and `dotnet --list-runtimes` for `Microsoft.WindowsDesktop.App 6`/`8` (L1e).

## Resolution

- **L1a — wrong `Path`:** set `Path` to the Python install/venv **folder** (the one containing `python.exe` and `site-packages`), e.g. `C:\Users\<USER>\AppData\Local\Programs\Python\Python311` or your venv root. Use the **Installed Python Versions** picker to auto-fill `Path`, `Library path`, and `Target` correctly.
- **L1b — bitness mismatch:** set `Target` to match the installed interpreter (install a 64-bit Python for `x64`, or set `Target = x86` for a 32-bit interpreter).
- **L1c — `Library path`:** Python **> 3.9** on Windows → set `Library path` to the matching `pythonXX.dll` (e.g. `<Path>\python311.dll`). Python **≤ 3.9** on Windows → leave it **empty**. Linux → point it at `libpythonXX.so`.
- **L1d — version unsupported:** upgrade `UiPath.Python.Activities` to a version that supports the Python version (see the package map above), or pin `Version` to a supported interpreter.
- **L1e — runtime missing:** install the **.NET Desktop Runtime 6+** on the robot host (.NET 8 supported).
- **L2a — `ModuleNotFoundError`:** point `Path` at the environment whose `site-packages` has the module, **or** install the dependency into the interpreter at `Path` (`"<Path>\python.exe" -m pip install <module>`). Do not rely on the IDE's venv being picked up — it is not.
- **L2b — syntax / top-level error:** fix the syntax, and move executable logic into functions. Keep the module body to `def`s and imports (optionally guard run-on-load logic with `if __name__ == "__main__":`); `Load Python Script` only needs the functions defined, and invokes them via `Invoke Python Method`.
- **L2c — local import not found:** set `WorkingFolder` to the script's project root so relative `import`s resolve.
- **L3 — hang / oversized data:** remove or reduce stdout produced at load (and keep **Log Python Output to File** off in production); raise `Timeout` for a legitimately slow load; for large returns, write the data to a file in the script and pass the file path back instead of the object, or raise **Script Data Size Limit (MB)**.

**Prevention.** Before running in UiPath, run the script with the **same interpreter** the scope points at, from the scope's `WorkingFolder`. Configure the scope via the **Installed Python Versions** picker so `Path`, `Library path`, and `Target` are mutually consistent, and confirm the package version supports the Python version.

If `LoadScript` still fails after L1–L3 are ruled out, capture the `.py` file, the resolved scope properties from the `.xaml`, the interpreter version/bitness, and a `Verbose` robot log (or enable **Log Python Output to File** locally to capture the Python-side traceback), and open a UiPath support case.
