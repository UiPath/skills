# Final Resolution

---

**Root Cause:** The `Python Scope` activity's `Path` property is set to
`C:\Program Files\Python311\python.exe` — the Python **executable**. `Path`
must be the **folder** that contains `python.exe` (i.e.
`C:\Program Files\Python311`); the scope resolves the interpreter under that
folder itself. Because the configured value already names `python.exe`, the
scope cannot resolve a valid interpreter and fails at scope open with
`The specified Python path is not valid: C:\Program Files\Python311\python.exe`
before any Python code runs. The file genuinely exists on disk, which is why
the path "looks correct" — but the property expects a directory, not a file.

**What went wrong:** Failing job `bb222222-7777-bbbb-cccc-ddddeeeeffff`
(`PythonHelloWorld`) started at `2026-06-18T11:02:10Z`. `Python Scope` tried
to initialize the interpreter from `Path`, rejected the file path, and
faulted immediately. `Run Python Script: hello.py` never executed.

**Why:** The `Path` property is the install directory, not the interpreter
binary. UiPath documentation specifies a folder such as
`C:\Users\<user>\AppData\Local\Programs\Python\Python311` or
`C:\Program Files\Python311`. Appending `\python.exe` is a common first-time
configuration mistake.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `PythonHelloWorld` (key `bb222222-...`) — Faulted at
  `2026-06-18T11:02:12.180Z`.
- Folder: `PythonAutomations` (key `fb222222-2222-3333-4444-555566667777`).
- Host: `MOCK-HOST`, runtime type `Unattended`.
- Error (verbatim from `or jobs get`):
  `Python Scope: The specified Python path is not valid:
  C:\Program Files\Python311\python.exe`.
- Faulting activity: `PythonScope_1` (`Python Scope`) at `Main.xaml` — the
  fault is at scope open (the stack shows `PythonScope.OnExecuteAsync` →
  `PythonClient.Initialize`), not at a child activity.

### Workflow source (decisive)
- `process/Main.xaml`: `Python Scope`
  `Path="C:\Program Files\Python311\python.exe"`. The value ends in
  `\python.exe` — a **file**, not the install folder. This exactly matches
  the path echoed in the error.
- `Target="x64"`, `Version="Python_311"`, `Library` empty — not the cause;
  the scope never got past resolving `Path`.

### Cross-check — what this is NOT
- Not `Pipe is broken`: no Python host started; the fault is at scope open,
  not at method invocation.
- Not an architecture / engine-init mismatch: the error is specifically
  "path is not valid", not `One or more errors occurred` /
  `Error initializing the Python engine`.
- Not a `WorkingFolder` / relative-path issue: nothing ran.

---

**Recommended Fix (Resolution):**

### Primary fix — set Path to the install folder

In `process/Main.xaml`, change the `Python Scope` `Path` from:

```
C:\Program Files\Python311\python.exe
```

to the containing folder (drop the trailing `\python.exe`):

```
C:\Program Files\Python311
```

Re-run; the scope opens and `Run Python Script: hello.py` executes.

### After fixing Path (Python > 3.9 on Windows)

- Set `Library path` to the matching DLL in that folder
  (`C:\Program Files\Python311\python311.dll`); leave it empty for installs
  ≤ 3.9.
- Set `Version` to the installed version (`Python_311`) or `Auto`.

### Prevention

- `Path` is always the **folder** that contains `python.exe`, never the
  executable and never the `%LocalAppData%\Microsoft\WindowsApps\python` Store
  alias.
- Confirm on the robot host with `where python` (or by opening the folder)
  before setting the property.
