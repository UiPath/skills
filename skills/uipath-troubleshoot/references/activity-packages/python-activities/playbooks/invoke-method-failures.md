---
confidence: medium
---

# Invoke Python Method (InvokeMethod) Failures

## Context

`UiPath.Python.Activities.InvokeMethod` ("Invoke Python Method") runs **after** `Load Python Script` inside a `Python Scope`. It takes the `PythonObject` from `LoadScript` as its `Instance`, calls the function named in `Name` with the arguments in `InputParameters`, and returns a `PythonObject` in `Result` (typically converted by `Get Python Object`). A failure here means the engine initialized and the script loaded — the fault is in **resolving or calling the function**, in the **arguments**, or in **Python code that runs inside the function**.

If the failure is actually at engine init or script load (`Error initializing Python engine`, `The specified Python path is not valid`, `ModuleNotFoundError` from a top-level import, syntax error), it belongs to [load-script-failures.md](./load-script-failures.md), not here — `Invoke Python Method` never ran.

What this looks like:
- `One or more errors occurred` / `Error invoking the python method` (generic wrapper around a Python-side exception).
- A Python `AttributeError` / "object has no attribute '<name>'" — the function name did not resolve.
- A Python `TypeError` about argument count ("takes N positional arguments but M were given" / "missing required positional argument").
- A **design-time** compile error on the `InputParameters` field (`BC36754` in VB, a type-conversion error like `CS1503`/`CS0029` in C#).
- `System.IO.PipeException` / "Pipe is broken" mid-call.
- `NullReferenceException` when `Instance` is empty.

## Causes

Name the confirmed sub-cause exactly. Do NOT assert a cause unless the investigation arrived at it.

- **M1. Function name does not resolve.** `Name` does not match a function bound at the script's module level. Python raises `AttributeError` / "has no attribute". Sub-causes: a typo; **case mismatch** (`Name` is case-sensitive and must mirror the `def` exactly); the function is nested inside a class or another function (only module-level `def`s are callable by name); or the function is defined only under `if __name__ == "__main__":`, so `LoadScript` never bound it.
- **M2. Argument mismatch at runtime.** The `InputParameters` count, order, or types do not match the function signature → Python `TypeError`. Also covers passing a **complex .NET object** (e.g. `DataTable`, a custom class) that Python cannot consume — only primitives/strings marshal cleanly across the boundary; serialize to a string/JSON or pass a file path instead.
- **M3. `InputParameters` is not an Object array (design-time).** The field expects `IEnumerable<Object>`. Passing a raw typed array or a bare scalar fails to compile in the designer — `BC36754` ("'Integer()' cannot be converted...") in VB, or a `CS1503`/`CS0029` conversion error in C#. This is a configuration error, not a runtime fault.
- **M4. Python-side exception inside the function.** The function resolved and was called, but its body raised — surfaces wrapped in `One or more errors occurred`. Common triggers: a **relative file path** (`open("data.csv")`) resolved against UiPath's working directory (the robot project / `WorkingFolder`), not the script's folder; a `KeyError` / `IndexError` / `ValueError` on the input; or a **lazy `import`** of a package missing from the interpreter at the scope's `Path` (a top-level import would have failed earlier in `LoadScript` — see [load-script-failures.md](./load-script-failures.md) **L2a**).
- **M5. Broken pipe / oversized payload.** `System.IO.PipeException` ("Pipe is broken"). The return value handed back to UiPath is too large (return a file path or a boolean and write the data to a `.csv`/`.xlsx` in the script instead), the payload exceeds the scope's **Script Data Size Limit** (25 MB default), or the engine became unstable — a bitness mismatch can drop the pipe, though that usually fails earlier at engine init (see [load-script-failures.md](./load-script-failures.md) **L1b**).
- **M6. `Instance` is null / not a loaded script.** `Instance` is not bound to a successful `LoadScript` result (the `LoadScript` faulted, was skipped, or its `Result` variable is uninitialized) → `NullReferenceException`. The real fault is upstream at load.

## Investigation

1. **Read the activity + script from the `.xaml`.** Capture `Instance` (which `LoadScript` result it binds), `Name`, the `InputParameters` expression, and the `Result` variable. Open the `.py` and confirm the function is defined at **module level** with the exact name/case.
2. **Confirm it is an invoke fault, not a load fault.** If the job log shows `Error initializing Python engine` / `The specified Python path is not valid` / a `ModuleNotFoundError` from a top-level import / a syntax error, route to [load-script-failures.md](./load-script-failures.md) — `InvokeMethod` never executed.
3. **Decision tree** (stop at the first match):
   - `AttributeError` / "has no attribute '<name>'" → **M1**. Diff `Name` against the `def` (exact case); check the function is not nested or `__main__`-guarded.
   - `TypeError` about argument count / missing argument → **M2** (count/order). A marshalling complaint about a non-primitive argument → **M2** (type).
   - Designer compile error on `InputParameters` (`BC36754` / `CS1503` / `CS0029`) → **M3**.
   - `One or more errors occurred` with a Python traceback naming a line inside the function → **M4**. Read the traceback for the Python exception type (`FileNotFoundError`, `KeyError`, lazy-import `ModuleNotFoundError`).
   - `System.IO.PipeException` / "Pipe is broken" → **M5**. Check the size of the returned object and the `Script Data Size Limit`.
   - `NullReferenceException` on `Instance` → **M6**. Verify `LoadScript` ran and its `Result` is set.
4. **Capture the Python-side traceback (decisive for M4).** Enable **Log Python Output to File** on the `Python Scope` to capture the Python `stderr`/traceback, then reproduce — the wrapped `One or more errors occurred` rarely shows the originating Python line on its own.
5. **Reproduce the call standalone.** With the scope's interpreter, from the scope's `WorkingFolder`: `"<Path>\python.exe" -c "import <module>; print(<module>.<Name>(<args>))"`. If it fails the same way, the fault is the script/arguments (M1/M2/M4), not UiPath wiring.

## Resolution

- **M1 — name does not resolve:** set `Name` to the exact, case-correct module-level function name. Move the target function out of a class / outer function / `if __name__ == "__main__":` block so `LoadScript` binds it at module level.
- **M2 — argument mismatch:** align `InputParameters` count, order, and types with the function signature. Pass only primitives/strings; for structured input, serialize to JSON or write to a file and pass the path. Give Python defaults for optional parameters rather than relying on UiPath to omit them.
- **M3 — `InputParameters` not an Object array:** wrap the arguments as an object array — C#: `new object[] { var1, var2 }`; VB: `New Object() { var1, var2 }`. A single argument still needs the array wrapper.
- **M4 — Python exception in the function:** read the traceback (step 4) and fix the Python cause. For the common relative-path case, use absolute paths in the script **or** pass the path in from UiPath as a parameter (do not rely on `open("data.csv")` resolving against the script folder — it resolves against UiPath's working directory). For a lazy-import `ModuleNotFoundError`, install the module into the interpreter at the scope's `Path` (see [load-script-failures.md](./load-script-failures.md) **L2a**).
- **M5 — broken pipe / oversized payload:** stop returning large objects (DataFrames, big JSON) across the boundary — write them to a `.csv`/`.xlsx` in the script and return the file path or a boolean; raise **Script Data Size Limit (MB)** only if a moderately larger payload is genuinely needed. If the pipe drops instantly on every call, rule out a bitness mismatch via [load-script-failures.md](./load-script-failures.md) **L1b**.
- **M6 — null `Instance`:** ensure `Load Python Script` runs successfully before `Invoke Python Method` and that the `Instance` binds that activity's `Result` variable. If `LoadScript` is failing, resolve that first via [load-script-failures.md](./load-script-failures.md).

**Prevention.** Validate the function name (exact case, module-level) and the argument contract before running in UiPath by calling it with the scope's own interpreter from the scope's `WorkingFolder`. Keep the Python↔UiPath boundary to primitives and file paths, and enable **Log Python Output to File** during development so the originating Python traceback is visible rather than the wrapped `One or more errors occurred`.

If `Invoke Python Method` still fails after M1–M6 are ruled out, capture the `.py` file, the resolved activity properties from the `.xaml`, the Python-side traceback (Log Python Output to File), and a `Verbose` robot log, and open a UiPath support case.
