# Final Resolution

---

**Root Cause:** The `Invoke Python Method` activity in `Main.xaml` calls
`clean_records`, but that function is defined **only inside the
`if __name__ == "__main__":` block** of `scripts/transform.py`. When
`Load Python Script` imports the module, `__name__` is the module name
(not `"__main__"`), so the guarded block never runs and `clean_records` is
never bound at module level. `Invoke Python Method` then cannot resolve the
name and faults with `AttributeError: module 'transform' has no attribute
'clean_records'`.

**What went wrong:** The `PyRecordCleaner` job (started
2026-06-11T08:21:40Z) initialized the Python engine and loaded the script
successfully, then faulted ~2.7 seconds in when `Invoke Python Method`
tried to call `clean_records`. The runtime error was
`Invoke Python Method: One or more errors occurred. --->
Python.Runtime.PythonException: AttributeError : module 'transform' has no
attribute 'clean_records'`, with the stack pointing at `PythonScope` →
`InvokeMethod`. Because `Load Python Script` succeeded first, this is an
invocation-resolution fault, not an engine-init or script-load failure.

**Why:** `Load Python Script` executes the module body to bind the
functions/objects defined **at module level**, and returns that as the
`PythonObject` the `Invoke Python Method` `Instance` consumes. Code under
`if __name__ == "__main__":` is intentionally skipped on import, so any
`def` nested inside that guard (or inside a class / another function) is
never bound and is not callable by name. The script runs fine when executed
directly (`python transform.py`) because direct execution sets
`__name__ == "__main__"` and runs the block — which is why it "works
standalone but fails in UiPath".

---

**Evidence:**

### Orchestrator (Propagation)
- Job: PyRecordCleaner -- Faulted at 2026-06-11T08:21:42.880Z (ran ~2.7 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Data Pipelines (key `b2c3d4e5-f6a7-4182-93a4-b5c6d7e8f902`)
- Log order: `Execution started` -> `[Python Scope] Python engine initialized` -> `[Load Python Script] Loaded script: scripts\transform.py` -> `[Invoke Python Method] ... AttributeError ... has no attribute 'clean_records'`
- The engine initialized and the script loaded BEFORE the fault -- so this is not a load-script-failures (engine-init / load) issue.

### Python Activities (Root Cause)
- Activity surface: `UiPath.Python.Activities.InvokeMethod` ("Invoke Python Method"), `Name = "clean_records"`, `Instance` bound to the `Load Python Script` result.
- `scripts/transform.py` defines `clean_records` only inside `if __name__ == "__main__":` -- it is not a module-level function, so `LoadScript` never binds it.
- The error is `AttributeError ... has no attribute 'clean_records'` at the invoke step, which is the signature of a name that does not resolve at module level (invoke-method-failures M1).

---

**Immediate fix:**

This is a script-structure fix in the project source -- no host access
needed.

### Fix path A -- move the function to module level (primary)
- Edit `scripts/transform.py` so `def clean_records(...)` is defined at
  **module level** (dedent it out of the `if __name__ == "__main__":`
  guard). Keep only the direct-run call (e.g. `print(clean_records())`)
  under the `__main__` guard, if anything.
- After the change, `Load Python Script` binds `clean_records` and
  `Invoke Python Method` can resolve it. Re-run.

### Verification
- Confirm the function is callable from the scope's interpreter the way
  UiPath calls it (by import, not by running the file):
  `"C:\Python311\python.exe" -c "import transform; print(transform.clean_records)"`
  -- this must succeed (it currently raises `AttributeError`), whereas
  `python transform.py` succeeds either way and is NOT a valid check.

- **Source:** `python-activities/playbooks/invoke-method-failures.md`

> Note: `Name` is also case-sensitive and must mirror the `def` exactly;
> here the name matches but is not bound at module level. Either way the
> fix is to make a correctly-named module-level function.

---

**Preventive fix:**

1. **Studio / script authoring** -- keep functions that UiPath invokes at
   module level; reserve `if __name__ == "__main__":` for direct-run
   harness code only, never for `def`s the workflow calls.
   - **Why:** `Load Python Script` binds module-level defs and skips the
     `__main__` block on import, so a function under that guard works when
     run standalone but is invisible to `Invoke Python Method`.
   - **Who:** RPA developer.

2. **Pre-flight check** -- validate by import, not by running the file:
   `python -c "import <module>; print(<module>.<func>)"`.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `Invoke Python Method` cannot resolve `clean_records` because it is defined only under `if __name__ == "__main__":` and never bound at module level by `Load Python Script` | High | Confirmed | Yes | `AttributeError ... has no attribute 'clean_records'` at the invoke step, after the script loaded successfully + `transform.py` defines the function under the `__main__` guard | Move `def clean_records` to module level; re-run |
| H2 | Engine-init / script-load failure | Low | Rejected | No | Engine initialized and `Load Python Script` succeeded in the logs before the fault | n/a (see load-script-failures) |
| H3 | Wrong/missing argument (TypeError) | Low | Rejected | No | The error is `AttributeError` (name resolution), not a `TypeError` about arguments | n/a |

---

Would you like me to apply the `transform.py` change (move `clean_records`
to module level), or help clean up the `.local/investigations/` folder?
