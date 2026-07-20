# Final Resolution

---

**Root Cause:** The `UiPath.Python.Activities` package runs Python in a
separate host process and communicates with it over an IPC pipe. The invoked
function `extract_total` in `parse_invoice.py` starts by executing
`import pandas`. The interpreter that
`Python Scope` resolves on the robot host (`C:\Program Files\Python311`,
`Version=Python_311`, `Target=x64`) does **not** have `pandas` installed, so
when `Invoke Python Method: extract_total` runs, the Python host hits
`ModuleNotFoundError: No module named 'pandas'` and exits before returning a
result. The robot side sees the host process vanish and the pipe close,
surfacing the generic `UiPath.Python.RemoteException wrapping
System.IO.IOException: Pipe is broken`. The real Python error is **not** in
the job log — UiPath only reports that the host died.

The script "runs fine in the developer's IDE / VS Code" because that IDE uses
a different Python interpreter that has `pandas` installed. The packages
available at robot runtime are those installed in the interpreter the scope's
`Path` resolves, not the developer's environment.

**What went wrong:** Failing job `aa111111-7777-bbbb-cccc-ddddeeeeffff`
(`PythonInvoiceParser`) started at `2026-06-18T09:15:02Z`. The `Python Scope`
opened and resolved the interpreter, `Load Python Script` loaded
`parse_invoice.py`, and `Invoke Python Method: extract_total` then crashed the
host on the missing `pandas` import — breaking the pipe.

**Why:** `Pipe is broken` is a symptom, not a cause. It means the
out-of-process Python host died. The most common reason is a third-party
module that exists in the developer's environment but not in the robot's
interpreter; other causes (an unhandled exception, a hard `sys.exit`, flooding
stdout) crash the host the same way. The fix is to surface the real Python
error (run the script from the robot's interpreter) and make the robot
interpreter match the script's dependencies.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `PythonInvoiceParser` (key `aa111111-...`) — Faulted at
  `2026-06-18T09:15:08.640Z`.
- Folder: `PythonAutomations` (key `fa111111-2222-3333-4444-555566667777`).
- Host: `MOCK-HOST`, runtime type `Unattended`. Robot user:
  `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `UiPath.Python.RemoteException wrapping System.IO.IOException: Pipe is
  broken: "Invoke Python Method: extract_total"`.
- Faulting activity: `InvokeMethod_1` (`Invoke Python Method: extract_total`)
  at `Main.xaml`.

### Job logs (sequence)
- Scope resolved the interpreter and started the host process
  (`Path=C:\Program Files\Python311`, `Version=Python_311`, `Target=x64`).
- `Load Python Script: parse_invoice.py` loaded successfully.
- `Invoke Python Method: extract_total` faulted: the Python host process
  exited before returning a result. **No Python traceback is logged** — the
  underlying cause is hidden.

### Workflow source (decisive)
- `process/parse_invoice.py`: `extract_total` begins with
  `import pandas as pd` — a third-party dependency — then calls
  `pd.read_csv(...)`. The import runs at method invocation, which is
  exactly where the job faulted.
- `process/Main.xaml`: `Python Scope` `Path="C:\Program Files\Python311"`,
  `Target="x64"`, `Version="Python_311"`. The scope itself opened fine, so
  this is not a path / engine-init failure — the host died at method
  invocation.
- The user states the script "runs fine in my IDE / VS Code" — confirming a
  different interpreter (one with `pandas`) is used during development.

### Cross-check — what this is NOT
- Not `The specified Python path is not valid`: the scope opened and loaded
  the script; `Path` is the install folder, not `python.exe`.
- Not an engine-init / architecture mismatch: no `One or more errors
  occurred` / `Error initializing the Python engine`; the host started.
- Not a `WorkingFolder` / relative-path issue: the activity faulted, it did
  not complete with wrong output.

---

**Recommended Fix (Resolution):**

### Primary fix — install the missing module into the scope's interpreter

Install `pandas` into the exact interpreter `Python Scope` resolves on the
robot host (not the dev's IDE environment):

```bash
"C:\Program Files\Python311\python.exe" -m pip install pandas
```

On an unattended robot, run this as / for the robot user (or use a virtual
environment and point `Python Scope` `Path` at that venv). Re-run the job; the
pipe no longer breaks.

### Confirm the real error first (diagnosis)

Reproduce out-of-band from the robot's interpreter so the hidden Python
traceback is visible:

```bash
"C:\Program Files\Python311\python.exe" -c "import pandas"
```

This prints the true `ModuleNotFoundError: No module named 'pandas'` that
UiPath swallowed, confirming the cause before installing.

### Prevention

- Keep a checked-in `requirements.txt` and install it into the robot
  interpreter (or venv) as part of provisioning, so the robot environment
  matches the script's dependencies.
- Wrap the invoked Python in `try/except`, log the real exception, and
  re-raise — so a future failure surfaces the Python error instead of a bare
  `Pipe is broken`.
- Validate the script's imports resolve from the robot interpreter before
  wiring it into the workflow.
