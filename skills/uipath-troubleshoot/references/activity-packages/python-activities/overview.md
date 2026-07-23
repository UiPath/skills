# Python Activities

Activities from the `UiPath.Python.Activities` package for invoking Python from a UiPath workflow on Windows or cross-platform. The package does **not** run Python in-process. `Python Scope` spawns a separate Python host process (a child `python.exe` / interpreter) and marshals objects to and from it over an IPC pipe. Child activities — `Load Python Script`, `Run Python Script`, `Invoke Python Method`, `Get Python Object` — call into that out-of-process host across the pipe.

## How Python Scope Executes

`Python Scope` resolves an interpreter from its properties, launches it as a child process, and exposes the live host to child activities:

1. Resolve the interpreter from `Path` (the install **folder**), `Version`, `Target` (bitness), and — for Python > 3.9 on Windows / any Linux — `Library path` (the `pythonXY.dll` / `libpythonX.Y.so`).
2. Spawn the Python host process and open the IPC pipe to it.
3. `Load Python Script` / `Run Python Script` send code into the host; `Invoke Python Method` calls a function; `Get Python Object` marshals a `PythonObject` back to a .NET type.
4. Close the host and the pipe at end of scope.

Two properties of this model drive most failures:

- **The interpreter is external and resolved from the scope, not from the developer's machine state.** `Path` must point at the install folder (never at `python.exe` itself, never at the `WindowsApps\python` Store alias). `Target` (x86 / x64) and `Version` must match the actual interpreter on the **robot** host, not the developer's. A mismatch fails before any script runs.
- **The Python side is a black box reached over a pipe.** Any unhandled Python-side failure — `ModuleNotFoundError`, a syntax error, a non-zero `sys.exit`, an OOM kill, flooding stdout — kills the host process and breaks the pipe. UiPath surfaces this as a generic `Pipe is broken`, not the underlying Python traceback. The packages installed in the **scope's** interpreter (not the dev's IDE) are what's available at runtime.

## Key Activities

- **Python Scope** (`UiPath.Python.Activities.PythonScope`) — resolve and launch the interpreter; host all child Python activities. Properties: `Path` (install folder), `Library path` (the `.dll`/`.so`, > 3.9 / Linux only), `Version` (`Auto` or e.g. `Python_311`), `Target` (`x86` / `x64`), `WorkingFolder`, `Timeout`.
- **Load Python Script** (`UiPath.Python.Activities.LoadScript`) — load code from a file or string into a `PythonObject`. Properties: `File` / `Code`, `Result`.
- **Run Python Script** (`UiPath.Python.Activities.RunScript`) — load and execute a script in one step.
- **Invoke Python Method** (`UiPath.Python.Activities.InvokeMethod`) — call a function in a loaded `PythonObject`. Properties: `Instance`, `Name`, `InputParameters`, `Result`.
- **Get Python Object** (`UiPath.Python.Activities.GetObject`) — marshal a `PythonObject` to a .NET type. Properties: `PythonObject`, `TypeArgument`, `Result`.

## Common Failure Patterns

- **`Pipe is broken` / `Error invoking Python method`** — the child Python host process died or stopped responding (commonly raised at `Invoke Python Method` / `Run Python Script`, often wrapped as `RemoteException wrapping System.IO.IOException: Pipe is broken`). The Python-side cause is hidden: a missing pip module in the scope's interpreter, an unhandled exception, a hard `sys.exit`, or flooding stdout. The script "runs fine in my IDE" because the IDE uses a different interpreter with the module installed.
- **`The specified Python path is not valid: <path>`** — `Python Scope` could not resolve the interpreter from `Path`. Usual traps: `Path` points at `python.exe` (the executable) instead of the **folder** containing it, or at the `%LocalAppData%\Microsoft\WindowsApps\python` Microsoft Store alias (not a real install).
- **`One or more errors occurred` / `Error initializing the Python engine`** — interpreter could not be loaded. Bitness mismatch (`Target` x86 vs a 64-bit install, or vice-versa), a `Version`/`Library path` that doesn't match the install, or a missing .NET Desktop Runtime the engine depends on.
- **Python Scope hangs / freezes with no error** — on pkg v1.9.0+ with target framework `Windows`, the Python host runs on the .NET Desktop Runtime (6.0 x64; 5.0 for older packs); if it is missing the host never starts and the scope hangs (Studio freezes at design time, or a runtime job stalls) instead of faulting. Diagnose via OS Event Viewer; fix by installing the runtime or switching to Windows-Legacy. See `python-scope-hang-dotnet-runtime.md`.
- **Script runs but reads/writes the wrong files** — relative paths inside the script resolve against `WorkingFolder`, which defaults to the robot's per-package directory, not the project folder. Same CWD-divergence class as relative workflow paths.

## Package

NuGet: `UiPath.Python.Activities`

Version-specific behavior is documented in the relevant playbooks. The pack pins which Python versions and runtimes a given release supports (and the required .NET Desktop Runtime) — match the package version to the interpreter and runtime on the **robot** host before concluding a code defect. See the [package documentation](https://docs.uipath.com/activities/other/latest/developer/about-the-python-activities-pack) for the supported-version matrix.
