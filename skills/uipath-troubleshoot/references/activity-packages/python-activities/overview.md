# Python Activities

Activities from the `UiPath.Python.Activities` package for running Python code from a UiPath workflow on Windows (and Linux robots). All Python activities run inside a **`Python Scope`** container that initializes an out-of-process Python engine bound through Python.NET, then exposes that engine to its child activities. The package depends on a real Python interpreter installed on the robot host and — for Windows projects on package **v1.9.0+** — the **.NET Desktop Runtime 6 or higher**.

## How Python Scope Executes

`Python Scope` does the heavy lifting; the child activities operate against the engine it stands up. Behaviour chain:

1. **Initialize the Python engine** — load the interpreter resolved from `Path` / `Library path`, at the bitness in `Target` and the version in `Version`. Requires a matching, loadable `pythonXX.dll` (Windows) / `libpythonXX.so` (Linux) and, on Windows package v1.9.0+, the .NET Desktop Runtime 6+.
2. **Load the script** (`Load Python Script`) — read the `.py` file (or inline script text) and **execute its module body** to bind the functions/objects it defines, returning a `PythonObject`.
3. **Invoke** (`Invoke Python Method`) — call a named function on that loaded object with arguments.
4. **Marshal results back** (`Get Python Object`) — convert a returned Python object to a .NET type.

Failures originate at distinct layers — engine initialization (step 1), script load/compile/import (step 2), method invocation (step 3), or data marshalling/size (step 4). Knowing which layer produced the error narrows the investigation. `Load Python Script` failures are the most common and span steps 1–2: the scope must initialize *and* the script must load cleanly before any method runs.

## Key Activities

- **Python Scope** (`PythonScope`, display name "Python Scope") — initialize the Python engine and run child activities against it. Key properties below.
- **Load Python Script** (`LoadScript`, display name "Load Python Script") — load a `.py` file or inline script and return a `PythonObject` for downstream invocation. Executes the module body at load time.
- **Invoke Python Method** (`InvokeMethod`, display name "Invoke Python Method") — call a function on a loaded `PythonObject` with input arguments.
- **Get Python Object** (`GetObject`, display name "Get Python Object") — convert a `PythonObject` to a typed .NET value.
- **Run Python Script** (`RunScript`) — load and run a script in one step (where present in the package version).

## Python Scope Properties

| Property | Accepts | Notes |
|----------|---------|-------|
| **Installed Python Versions** | design-time picker | Lists Python installs detected on the machine. Selecting one auto-fills `Path`, `Library path`, and `Target`, and sets `Version` to `Auto`. |
| **Path** | folder path (string/var) | The **Python installation or virtual-environment folder** whose `python.exe` and `site-packages` you want (e.g. `C:\Users\<USER>\AppData\Local\Programs\Python\Python311` or a venv root). NOT the path to `python.exe` itself, and NOT a "libraries" folder. |
| **Library path** | file path (string/var) | Windows + Python **> 3.9**: path to `pythonXX.dll` (e.g. `...\python311.dll`). Windows + Python **≤ 3.9**: **leave empty**. Linux: path to `libpythonXX.so`. Wrong/missing on 3.10+ is a top cause of engine-init failure. |
| **Version** | dropdown | Default `Auto`. `Auto` detects only Python v3.5+. Or pin an explicit version. The package version caps the max Python it supports (see below). |
| **Target** | `x86` / `x64` | Must match the **bitness of the installed interpreter**, not the OS. |
| **WorkingFolder** | string/var | Working directory for the scripts. Set to the script's project root so local `import` of sibling `.py` files resolves. |
| **Timeout** | seconds | Terminates a script that runs longer than this. |
| **Script Data Size Limit (MB)** | Int32 | Default 25. Larger returned data raises an error — save to a file and pass the file path instead. |
| **Log Python Output to File** | bool | Writes stdout/stderr to logs. Default False. Local debugging only — **leave disabled in production**. |

## Common Failure Patterns

- **Engine initialization failure** — the scope cannot stand up the interpreter. Surfaces as `The specified Python path is not valid` or `Error initializing Python engine 64 bit`. Causes: `Path` not pointing at the install/venv folder, `Target` bitness not matching the interpreter, `Library path` wrong/missing for Python > 3.9 on Windows, a `Version` the package cannot support, or the .NET Desktop Runtime 6+ missing (package v1.9.0+).
- **Script load error** — `One or more errors occurred` / `Error loading the python script`. `Load Python Script` executes the module body to bind functions; any top-level syntax error, exception, or failed import crashes the load.
- **`ModuleNotFoundError: No module named 'xyz'`** — the interpreter at `Path` lacks the package. The script runs in an IDE (which uses its own venv/conda env) but not under UiPath, because the scope only sees the interpreter at `Path` and Windows environment variables — it does **not** auto-activate a venv/conda env unless `Path` points at it.
- **Hang / pipe freeze / oversized data** — the script loads but the workflow stalls (excessive stdout during load, or a long-running load that needs `Timeout`), or returned data exceeds the Script Data Size Limit.

## Package

NuGet: `UiPath.Python.Activities`

Max supported Python version is gated by the package version: **3.10** (v1.6.0), **3.11** (v1.7.1), **3.12** (v1.8.1), **3.13** (v1.10.0), **3.14** (v2.2.1). v2.1.0 removed the Python.Runtime DLLs for Python 2.7 / 3.4 / 3.5 (those versions are no longer supported). Windows projects require .NET Desktop Runtime 6+ since v1.9.0 (.NET 8 also supported).
