# Python Activities Presentation Rules

- **Activities** — use the display name (e.g., "Python Scope", "Invoke Python Method", "Run Python Script", "Load Python Script"), not the fully qualified class name (e.g., `UiPath.Python.Activities.InvokeMethod`)
- **Scripts** — refer to the Python file by its name (e.g., "script `parse_invoice.py`") or the inline `Code` location; not by the `PythonObject` variable holding the loaded handle
- **Interpreter** — name the interpreter by its resolved install folder and version (e.g., "the Python 3.11 install at `C:\Program Files\Python311`"), and distinguish it explicitly from the developer's IDE interpreter when the script "runs fine in my IDE"
- **`Path` property** — when the fix is a folder-vs-file correction, show both the wrong value (`...\Python311\python.exe`) and the corrected value (`...\Python311`) so the user can see the exact edit
- **Error strings** — quote the exact message (`The specified Python path is not valid: <path>`, `Pipe is broken`, `One or more errors occurred`) and, when present, the wrapping type (`RemoteException wrapping System.IO.IOException`) so the user can correlate it with the Output panel / job log
- **Bitness** — refer to the interpreter and the scope `Target` as "32-bit (x86)" / "64-bit (x64)", and state which side is which (e.g., "`Target` is x86 but the install is 64-bit")
- **Run surface** — name the surface in the user's terms (e.g., "Studio Run/Debug (foreground)", "unattended robot (Session 0)"), not internal runtime flags like `isAttended`
