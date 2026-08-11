# Final Resolution

---

**Root Cause:** `scripts/aggregate.py` has a module-level loop
(`for _i in range(5_000_000): _LOOKUP[_i] = _i * _i; print("warmup row", ...)`)
that runs at import time. `Load Python Script` executes the module body to bind
its functions, so the loop runs at load and prints ~5M lines to stdout. The
stdout flood saturates the engine's output pipe and the heavy loop does not
complete within the Python Scope's 30s `Timeout`, so the scope faults with
`System.TimeoutException`.

**What went wrong:** The `PyBatchAggregate` job (started 2026-06-11T10:15:02Z)
ran the full ~31 seconds and faulted inside `Load Python Script` with
`System.TimeoutException: The Python script did not complete within the
configured Timeout (30000 ms). The Python standard output stream may be flooded.`
The logs show the engine initializing successfully, then a sustained stream of
`stdout: warmup row ...` trace entries until the timeout. The failure is at load
(building/printing the module-level lookup), not at engine init and not in the
`aggregate` function (which never ran).

**Why:** Python activities talk to the out-of-process interpreter over a pipe.
`Load Python Script` runs the module top-to-bottom, so any module-level work -
and especially `print()` in a large loop - executes at load. Excessive stdout
overruns the engine's output buffer/pipe and stalls communication; a long
module-level computation independently risks exceeding the scope `Timeout`. Both
are present here, and both are L3 ("hang or oversized data") in the playbook.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: PyBatchAggregate -- Faulted at 2026-06-11T10:15:33.540Z (ran ~31 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Batch Analytics (key `aa02b2c3-d4e5-4f60-8a02-000000000002`)
- Final error: `Load Python Script: One or more errors occurred. ---> System.TimeoutException: ... did not complete within the configured Timeout (30000 ms). The Python standard output stream may be flooded.` -> `Main.xaml` -> `PythonScope "Python Scope"` -> `LoadScript "Load Python Script"`

### Python Activities (Root Cause)
- Activity surface: `UiPath.Python.Activities.LoadScript` inside `PythonScope` (`Timeout=30000`).
- Log chain: "Python engine initialized" -> "Loading scripts\\aggregate.py" -> sustained `stdout: warmup row ...` entries -> TimeoutException at ~31s. Engine init succeeded (not L1); no syntax/import error (not L2).
- `scripts/aggregate.py` has a module-level `for _i in range(5_000_000)` loop that builds a lookup and `print()`s every row - executed at import by Load Python Script.

---

**Immediate fix:**

Stop flooding stdout at load and move heavy work out of module scope.

### Fix path A -- remove the load-time stdout (preferred)
Delete the per-row `print("warmup row", ...)` from `scripts/aggregate.py`. Do not
print in a large loop in code that Load Python Script imports; the module body
should bind functions, not emit volume. Keep **Log Python Output to File** off in
production.

### Fix path B -- move the warm-up into a function
Relocate the lookup-building loop out of module scope into a function the
workflow calls via `Invoke Python Method` (or compute it lazily), so loading the
module does not run it. Guard any dev-only run with `if __name__ == "__main__":`.

### Fix path C -- raise Timeout (only if the load is legitimately slow)
If a slow load is genuinely required, raise the `Python Scope` `Timeout` above
the load duration. This alone does not fix a stdout flood - pair it with A/B.
(For an oversized *return value* rather than stdout, write the data to a file and
return the path, or raise the **Script Data Size Limit**.)

### Verification (hand to the user - off-host)
Run the script with the scope's interpreter and watch it flood:
`"C:\Python39\python.exe" scripts\aggregate.py`
It should emit the warm-up flood and run long; after removing the prints / moving
the loop into a function, importing the module should return immediately.

- **Source:** `python-activities/playbooks/load-script-failures.md` (L3)

---

**Preventive fix:**

1. **Studio / script hygiene** -- keep module-level code in scripts invoked by
   Load Python Script to `def`s and imports; never `print()` in a loop or do
   heavy work at module scope.
   - **Why:** Load Python Script runs the module body, so load-time stdout and
     computation execute on the robot and can freeze the engine pipe / exceed
     Timeout.
   - **Who:** RPA developer.

2. **Data boundary** -- return summaries or file paths from Python rather than
   large objects, and raise `Script Data Size Limit` only when genuinely needed.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Module-level loop floods stdout and runs heavy work at import; Load Python Script executes the module body so the load saturates the engine pipe and exceeds Timeout (L3) | High | Confirmed | Yes | Engine "initialized" then sustained `stdout: warmup row ...` to TimeoutException at ~31s; aggregate.py has a 5M-row module-level print loop | Remove load-time stdout, move the warm-up into a function, and/or raise Timeout |

---

Would you like the exact command to reproduce the flood against the scope's
interpreter on MOCK-ROBOT, or help cleaning up the `.local/investigations/`
folder?
