# Final Resolution

---

**Root Cause:** The `Python Scope` `Target` property is set to `x86`
(32-bit), but the Python interpreter the scope resolves on the robot host
(`C:\Program Files\Python311`, Python 3.11) is 64-bit. UiPath launches the
Python host at the `Target` bitness and cannot load a 64-bit interpreter's
native library into a 32-bit process, so engine initialization fails with
`One or more errors occurred. (Error initializing the Python engine)` whose
inner exception is `System.BadImageFormatException: An attempt was made to
load a program with an incorrect format. (0x8007000B)` — the canonical
32-bit/64-bit load-mismatch signature. The fault is at scope open, before any
script runs.

**What went wrong:** Failing job `cc333333-7777-bbbb-cccc-ddddeeeeffff`
(`PythonDataCruncher`) started at `2026-06-18T13:40:05Z`. `Python Scope` tried
to start the Python host at `Target=x86`, the 64-bit interpreter could not
load into the 32-bit host, and the scope faulted with the aggregate /
`BadImageFormatException` error. `Run Python Script: crunch.py` never ran.

**Why:** `Target` (x86 / x64) must match the architecture of the installed
Python interpreter. `crunch.py` uses only the standard library, so this is not
a missing-module / pipe failure; and the error is engine-init, not "path is
not valid", so `Path` is fine. The only configuration inconsistent with a
64-bit install is `Target=x86`.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `PythonDataCruncher` (key `cc333333-...`) — Faulted at
  `2026-06-18T13:40:07.900Z`.
- Folder: `PythonAutomations` (key `fc333333-2222-3333-4444-555566667777`).
- Host: `MOCK-HOST`, runtime type `Unattended`.
- Error (verbatim from `or jobs get`):
  `Python Scope: One or more errors occurred. (Error initializing the Python
  engine) ---> System.BadImageFormatException: An attempt was made to load a
  program with an incorrect format. (0x8007000B)`.
- Faulting activity: `PythonScope_1` (`Python Scope`) at `Main.xaml` — the
  stack shows `PythonScope.OnExecuteAsync` → `PythonProcessClient.Start`
  (engine init), not a child activity.

### Workflow source (decisive)
- `process/Main.xaml`: `Python Scope` `Target="x86"`,
  `Path="C:\Program Files\Python311"`, `Version="Python_311"`, `Library`
  empty.
- The user states the installed Python 3.11 is 64-bit. `Target=x86` against a
  64-bit interpreter is the mismatch.
- `process/crunch.py` imports only `statistics` (standard library) — no
  third-party dependency, ruling out a missing-module / pipe cause.

### Decisive signal
- `BadImageFormatException (0x8007000B)` is the standard "wrong architecture"
  load error. Combined with `Target=x86` in source and a 64-bit install, it
  pins the cause to a bitness mismatch — not a path, version-pin, or
  dependency problem.

### Cross-check — what this is NOT
- Not `Pipe is broken`: the host never initialized; the script never ran.
- Not `The specified Python path is not valid`: `Path` is the install folder
  and the error is engine-init, not path resolution.
- Not a missing module: `crunch.py` is standard-library only.

---

**Recommended Fix (Resolution):**

### Primary fix — match Target to the interpreter bitness

In `process/Main.xaml`, change the `Python Scope` `Target` from `x86` to
`x64` to match the 64-bit Python 3.11 install. Re-run; the engine initializes
and `Run Python Script: crunch.py` executes.

### If a 32-bit Python is genuinely required

If `x86` is needed for a native dependency, install a 32-bit Python 3.11,
point `Python Scope` `Path` at that install folder, and keep `Target=x86`.
Both sides must agree.

### Confirm the interpreter bitness (diagnosis)

On the robot host:

```bash
"C:\Program Files\Python311\python.exe" -c "import struct; print(struct.calcsize('P') * 8)"
```

`64` confirms a 64-bit interpreter (so `Target` must be `x64`); `32` would
mean `x86`.

### Also verify (same playbook)

- `Version` matches the installed Python (`Python_311` or `Auto`), and the
  `UiPath.Python.Activities` pack version supports that Python release.
- For Python > 3.9 on Windows, `Library path` points at the matching
  `python311.dll`.
- The required .NET Desktop Runtime for the pack version is installed on the
  robot host.
