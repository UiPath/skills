# Final Resolution

---

**Root Cause:** `scripts/ledger_sync.py` does `import ledger_utils`, a **local
sibling module** that exists at `scripts/ledger_utils.py`. The `Python Scope` has
**no `WorkingFolder` set**, so the interpreter's working directory / import path
is the robot's per-package directory, not `scripts/`. The sibling module is not
on the import path, so `Load Python Script` faults at load with
`ModuleNotFoundError: No module named 'ledger_utils'`.

**What went wrong:** The `PyLedgerSync` job (started 2026-06-11T13:22:48Z)
faulted ~2 seconds after launch inside `Load Python Script` with
`Error loading the python script: ModuleNotFoundError: No module named
'ledger_utils'` at `File "ledger_sync.py", line 7, in <module>` ->
`import ledger_utils`. The engine initialized fine, and the named module is the
user's own file present in the project - not a third-party dependency.

**Why:** `Load Python Script` runs the module body, which executes its top-level
`import` statements. Python resolves a bare `import ledger_utils` against
`sys.path`, which includes the interpreter's working directory. The Python Scope
sets that working directory from its `WorkingFolder` property; when it is unset,
it defaults to the robot's per-package directory, not the folder that holds the
script and its siblings. So a local sibling import that works on the developer's
machine (run from the script's folder) fails on the robot. This is L2c - an
unresolved **local** import, distinct from L2a (a missing **third-party**
package), and the fix is path configuration, not `pip`.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: PyLedgerSync -- Faulted at 2026-06-11T13:22:50.470Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Finance Sync (key `aa03b2c3-d4e5-4f60-8a03-000000000003`)
- Final error: `Load Python Script: One or more errors occurred. ---> Python.Runtime.PythonException: Error loading the python script: ModuleNotFoundError: No module named 'ledger_utils'` -> `Main.xaml` -> `PythonScope "Python Scope"` -> `LoadScript "Load Python Script"`

### Python Activities (Root Cause)
- Activity surface: `UiPath.Python.Activities.LoadScript` inside `PythonScope`.
- Log chain: "Python engine initialized. WorkingFolder resolved to the package directory (no WorkingFolder set)." -> "Loading scripts\\ledger_sync.py" -> "ModuleNotFoundError: No module named 'ledger_utils'". Engine init succeeded (not L1).
- `scripts/ledger_sync.py` line 7 is `import ledger_utils`; `scripts/ledger_utils.py` exists in the same folder. The module is local, so this is a path/WorkingFolder problem, not a missing pip package (not L2a).
- The `Python Scope` in `Main.xaml` has no `WorkingFolder` attribute set.

---

**Immediate fix:**

Put the script's folder on the interpreter's import path via `WorkingFolder`.

### Fix path A -- set WorkingFolder to the script's folder (preferred)
On the `Python Scope` in `Main.xaml`, set `WorkingFolder` to `scripts` (the
folder containing `ledger_sync.py` and `ledger_utils.py`). With the working
directory at the script's root, `import ledger_utils` resolves and the load
succeeds. Do **not** `pip install ledger_utils` - it is a local file, not a
package.

### Fix path B -- restructure imports (alternative)
If the helpers should live in a package, turn the folder into a package and use a
package-relative import, ensuring the package root is on `sys.path`. For a single
sibling file, Fix path A is simpler.

### Verification (hand to the user - off-host)
Reproduce the resolution dependence with the scope's interpreter:
- From the project root: `"C:\Python39\python.exe" scripts\ledger_sync.py` -> reproduces `ModuleNotFoundError`.
- From the script folder: `cd scripts && "C:\Python39\python.exe" ledger_sync.py` -> imports cleanly.
This confirms the fix is the working directory (WorkingFolder), not a missing package.

- **Source:** `python-activities/playbooks/load-script-failures.md` (L2c)

---

**Preventive fix:**

1. **Studio** -- when a Python script imports sibling modules, set the
   `Python Scope` `WorkingFolder` to the script's folder so local imports resolve
   on the robot the same way they do on dev.
   - **Why:** The interpreter's working directory defaults to the robot's package
     directory, not the script folder, so local imports silently break after
     deployment.
   - **Who:** RPA developer.

2. **Script structure** -- keep a script and its helper modules in one folder and
   point `WorkingFolder` at it (or package them properly).
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | A local sibling import (ledger_utils) fails at load because the Python Scope has no WorkingFolder, so scripts/ is not on the import path (L2c) | High | Confirmed | Yes | `ModuleNotFoundError: No module named 'ledger_utils'` at ledger_sync.py line 7; ledger_utils.py present in scripts/; scope has no WorkingFolder; engine initialized | Set WorkingFolder to the script's folder (scripts/); do not pip install |

---

Would you like the exact host commands to confirm the working-directory
dependence on MOCK-ROBOT, or help cleaning up the `.local/investigations/`
folder?
