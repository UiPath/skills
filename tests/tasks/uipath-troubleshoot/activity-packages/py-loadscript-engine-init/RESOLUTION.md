# Final Resolution

---

**Root Cause:** The `Python Scope` in `Main.xaml` cannot initialize its
Python engine on the robot host, so `Load Python Script` faults at startup
with `Error initializing Python engine 64 bit` before the script is loaded
or any method is invoked. The project targets Python 3.11 (`Path =
C:\Python311`, `Version = Auto`, `Target = x64`), but the scope's
**`Library path` is empty**. On Windows, for Python **> 3.9** the
`Library path` must point at the matching `pythonXX.dll`
(`python311.dll`); left empty, the engine cannot initialize.

**What went wrong:** The `PyDataTransform` job (started
2026-06-10T14:03:11Z) faulted ~2.4 seconds after launch when the
`Python Scope` tried to stand up the interpreter. The runtime error was
`Load Python Script: One or more errors occurred. ---> System.Exception:
Error initializing Python engine 64 bit`, with the stack pointing at
`PythonScope "Python Scope"` → `LoadScript "Load Python Script"`. The
failure is at engine initialization (the script body never executes),
which is the signature of a scope-configuration / host-interpreter problem
rather than a Python syntax or `ModuleNotFoundError` issue.

**Why:** The `UiPath.Python.Activities` `Python Scope` initializes an
out-of-process Python engine bound through Python.NET. To load the
interpreter it needs the Python shared library. On Windows with Python
**> 3.9** the `Library path` property must be set to the matching
`pythonXX.dll` (for Python **≤ 3.9** it is left empty); this project runs
Python 3.11 with an empty `Library path`, so the engine never initializes.
A bitness mismatch between the installed interpreter and `Target` (`x64`)
produces the same engine-initialization error and must be ruled out on the
host.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: PyDataTransform -- Faulted at 2026-06-10T14:03:13.640Z (ran ~2.4 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Data Pipelines (key `b2c3d4e5-f6a7-4182-93a4-b5c6d7e8f902`)
- Final error: `Load Python Script: One or more errors occurred. ---> System.Exception: Error initializing Python engine 64 bit` -> `Main.xaml` -> `PythonScope "Python Scope"` -> `LoadScript "Load Python Script"` -> `Sequence "Main Sequence"`

### Python Activities (Root Cause)
- Activity surface: `UiPath.Python.Activities.PythonScope` containing `LoadScript` ("Load Python Script").
- Scope config in `Main.xaml`: `Path="C:\Python311"`, `Target="x64"`, `Version="Auto"`, and **no `LibraryPath`** (empty).
- Package: `UiPath.Python.Activities [1.10.0]` (supports up to Python 3.13, so 3.11 is supported -- the version is not the problem).
- The error is at engine init (before the script loads), which discriminates this from `ModuleNotFoundError` (L2a) or a syntax/top-level error (L2b).

---

**Immediate fix:**

The cause is an engine-initialization failure. The primary fix is a scope
configuration change the user can make without host access; confirm the
host interpreter as a corroborating check.

### Fix path A -- set the `Library path` for Python > 3.9 (primary)
- In the `Python Scope`, set **`Library path`** to the robot's matching
  `pythonXX.dll` -- for Python 3.11 at `C:\Python311`, that is
  `C:\Python311\python311.dll`. On Windows, `Library path` is **required**
  for Python > 3.9 and must be left empty only for Python <= 3.9.
- Easiest reliable route: on a machine with the interpreter, use the
  **Installed Python Versions** picker in the scope, which auto-fills
  `Path`, `Library path`, and `Target` consistently.

### Fix path B -- verify interpreter bitness vs `Target` (corroborating)
- `Error initializing Python engine 64 bit` is also produced by a
  bitness mismatch. Confirm a **64-bit** Python 3.11 is installed at
  `C:\Python311` on MOCK-ROBOT so it matches `Target = x64`. If the robot
  has 32-bit Python, either install 64-bit Python or set `Target = x86`.

### Host check (Data Pipelines / MOCK-ROBOT, as the robot's Windows user)
1. Confirm the interpreter exists and its bitness:
   `"C:\Python311\python.exe" --version` and
   `"C:\Python311\python.exe" -c "import struct;print(struct.calcsize('P')*8)"`
   (expect `3.11` and `64`).
2. Confirm the shared library path: `dir C:\Python311\python311.dll`.

- **Source:** `python-activities/playbooks/load-script-failures.md`

---

**Preventive fix:**

1. **Studio** -- configure the `Python Scope` via the **Installed Python
   Versions** picker so `Path`, `Library path`, and `Target` are mutually
   consistent, rather than hand-setting `Path`/`Target` and leaving
   `Library path` empty.
   - **Why:** the empty-`Library path`-on-Python-3.10+ trap is silent at
     design time and only surfaces as an engine-init fault at runtime.
   - **Who:** RPA developer.

2. **Robot host provisioning** -- standardize the unattended robot image to
   include the expected Python version at the expected path and bitness for
   any process that uses Python activities.
   - **Who:** Platform / robot host team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Python Scope engine fails to initialize because `Library path` is empty while the project targets Python 3.11 (> 3.9) on Windows | High | Confirmed | Yes | `Error initializing Python engine 64 bit` at `PythonScope`/`LoadScript` startup + scope config `Path=C:\Python311`, `Target=x64`, no `LibraryPath` | Set `Library path` to `C:\Python311\python311.dll` (Python > 3.9 requires it on Windows) |
| H2 | Interpreter bitness on the robot does not match `Target = x64` | Medium | Plausible -- needs host confirmation | Possible co-cause | Same engine-init error string; bitness not observable from Orchestrator | Confirm 64-bit Python 3.11 on the host, or set `Target = x86` |
| H3 | `ModuleNotFoundError` / Python syntax or top-level error | Low | Rejected | No | Failure is at engine init, before the script body loads | n/a |

---

Would you like the exact host commands to confirm the Python interpreter
version, bitness, and `python311.dll` location on MOCK-ROBOT, or help
cleaning up the `.local/investigations/` folder?
