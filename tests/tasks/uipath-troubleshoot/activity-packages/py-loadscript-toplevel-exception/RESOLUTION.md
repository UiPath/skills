# Final Resolution

---

**Root Cause:** `scripts/order_import.py` has a module-level (top-level)
statement `DEFAULT_DISCOUNT = 100 / 0` that raises `ZeroDivisionError` at import
time. `Load Python Script` executes the module body to bind the functions it
defines, so that top-level line runs at load and faults the activity with
`Error loading the python script` / `One or more errors occurred` before
`import_orders` is ever invoked.

**What went wrong:** The `PyOrderImport` job (started 2026-06-11T08:41:05Z)
faulted ~2 seconds after launch inside `Load Python Script`. The logs show the
Python engine initializing and reporting "Python engine initialized", then
`[Load Python Script] ... Error loading the python script: ZeroDivisionError:
division by zero` with the traceback frame `File "order_import.py", line 21, in
<module>` -> `DEFAULT_DISCOUNT = 100 / 0`. The engine started fine and there is
no missing-module error, so the failure is in executing the module body, not in
engine initialization or an import.

**Why:** Load Python Script (`UiPath.Python.Activities.LoadScript`) does not just
parse the file - it runs the module top-to-bottom to bind the functions that
`Invoke Python Method` will later call. Any statement that is not inside a `def`
/ `class` (module-scope "top-level" code) executes at load. A configuration
line, a self-test, or any top-level call that raises will abort the load and
surface as the generic `Error loading the python script` wrapper; the inner
Python exception (`ZeroDivisionError` here) is the real cause. "Runs fine in my
editor" does not clear it - the module-level crash happens whenever the module
is loaded.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: PyOrderImport -- Faulted at 2026-06-11T08:41:07.480Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Order Processing (key `aa01b2c3-d4e5-4f60-8a01-000000000001`)
- Final error: `Load Python Script: One or more errors occurred. ---> Python.Runtime.PythonException: Error loading the python script: ZeroDivisionError: division by zero` -> `Main.xaml` -> `PythonScope "Python Scope"` -> `LoadScript "Load Python Script"`

### Python Activities (Root Cause)
- Activity surface: `UiPath.Python.Activities.LoadScript` (Load Python Script) inside `PythonScope`.
- Log chain: "Initializing Python engine" -> "Python engine initialized" -> "Loading scripts\\order_import.py" -> "Error loading the python script: ZeroDivisionError". The engine init succeeded, so this is **L2b** (script load), not **L1** (engine init).
- Traceback frame `File "order_import.py", line 21, in <module>` -> `DEFAULT_DISCOUNT = 100 / 0` - module-scope code, not a function called from the workflow.
- The scope is validly configured (Path `C:\Python39`, Version `Python_39`, Target `x64`, empty Library path is correct for Python <= 3.9), reinforcing that the fault is the script, not the scope.

---

**Immediate fix:**

Stop the module-level code from running (and raising) when the module loads.

### Fix path A -- guard the top-level code (preferred)
In `scripts/order_import.py`, remove or repair the `DEFAULT_DISCOUNT = 100 / 0`
line and keep the module body to `def`s and imports. If a value must be computed
at run, do it inside a function. If the file is also run directly during dev,
guard the run-on-load logic:

```python
if __name__ == "__main__":
    print(import_orders("orders.csv"))
```

Load Python Script only needs the functions defined; it invokes them via Invoke
Python Method.

### Fix path B -- move setup into a function
Relocate any genuine setup into a function the workflow calls explicitly via
`Invoke Python Method`, so loading the module only binds functions and never
executes work.

### Verification (hand to the user - off-host)
Run the script standalone with the **same interpreter the scope targets** to see
the real traceback the wrapper hides:
`"C:\Python39\python.exe" scripts\order_import.py`
It should reproduce the `ZeroDivisionError` at line 21; after the fix it should
import cleanly.

- **Source:** `python-activities/playbooks/load-script-failures.md` (L2b)

---

**Preventive fix:**

1. **Studio / script hygiene** -- keep `.py` files invoked by Load Python Script
   to `def`s and imports at module scope; put runnable code behind
   `if __name__ == "__main__":` or inside functions.
   - **Why:** Load Python Script runs the module body, so top-level code executes
     on the robot even when it was only meant for local testing.
   - **Who:** RPA developer.

2. **Pre-deploy check** -- run each script through its target interpreter before
   wiring it into the workflow; a script that raises at import in a plain
   terminal will raise in the scope.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Module-level code in order_import.py raises at import; Load Python Script runs the module body so the load faults (L2b) | High | Confirmed | Yes | Engine "initialized" then "Error loading the python script: ZeroDivisionError" at `order_import.py` line 21 `in <module>`; valid scope config; no ModuleNotFoundError | Move top-level code into a function or behind `if __name__ == "__main__":`; remove the divide-by-zero |

---

Would you like the exact command to run the script against the scope's
interpreter on MOCK-ROBOT, or help cleaning up the `.local/investigations/`
folder?
