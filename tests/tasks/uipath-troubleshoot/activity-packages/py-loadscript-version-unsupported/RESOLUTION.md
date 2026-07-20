# Final Resolution

---

**Root Cause:** The project pins `UiPath.Python.Activities` **1.8.1**, whose
supported-Python matrix tops out at **3.12**. The robot now has **Python 3.13**
(the `Python Scope` `Version=Auto` detected 3.13). The package cannot initialize
a Python engine for an unsupported interpreter version, so `Load Python Script`
faults at engine init with `Error initializing the Python engine. The detected
Python version 3.13 is not supported by UiPath.Python.Activities 1.8.1` - before
the script ever loads.

**What went wrong:** The `PyForecast` job (started 2026-06-11T15:48:19Z) faulted
~2 seconds after launch. The logs show `[Python Scope] Initializing Python engine
(Target: x64, Path: C:\Python313, Version: Auto -> detected 3.13)` immediately
followed by the engine-init error naming Python 3.13 vs the package version. The
"we recently upgraded Python on the new robot" detail corroborates a
version-support gap, not a code defect.

**Why:** Each `UiPath.Python.Activities` release supports a bounded set of Python
versions (per the playbook map: 3.10 -> 1.6.0, 3.11 -> 1.7.1, 3.12 -> 1.8.1,
3.13 -> 1.10.0, 3.14 -> 2.2.1). When the interpreter on the robot is newer than
the pinned package supports, the engine host cannot be created and the scope
fails at initialization. Here `Path`/`Target`/`Library path` are all consistent
with the 3.13 install, so the only mismatch is the package's support ceiling -
this is L1d, not L1a/L1b/L1c, and not a script-load (L2) problem.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: PyForecast -- Faulted at 2026-06-11T15:48:21.360Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Forecasting (key `aa04b2c3-d4e5-4f60-8a04-000000000004`)
- Final error: `Load Python Script: One or more errors occurred. ---> System.Exception: Error initializing the Python engine. The detected Python version 3.13 is not supported by UiPath.Python.Activities 1.8.1` -> `Main.xaml` -> `PythonScope "Python Scope"` -> `LoadScript "Load Python Script"`

### Python Activities (Root Cause)
- Activity surface: `UiPath.Python.Activities.PythonScope` (engine init), surfacing at the first child `LoadScript`.
- `project.json` pins `UiPath.Python.Activities` `[1.8.1]` (max Python 3.12).
- Log: engine init detected Python 3.13; error explicitly names "Python version 3.13 ... not supported by UiPath.Python.Activities 1.8.1".
- `Main.xaml` `Python Scope`: `Path=C:\Python313`, `LibraryPath=C:\Python313\python313.dll` (correct for > 3.9), `Target=x64`. Library path and bitness are correct, so the cause is version support (L1d), not L1c/L1b.

---

**Immediate fix:**

Align the package with the installed Python (or vice versa).

### Fix path A -- upgrade the package (preferred)
Upgrade `UiPath.Python.Activities` to a version whose supported matrix includes
Python 3.13 - **1.10.0** or later - in `project.json` / Manage Packages, then
republish. This lets the engine initialize against the 3.13 interpreter.

### Fix path B -- pin to a supported Python version
If the package cannot be upgraded, install a Python version the current package
supports (<= 3.12 for 1.8.1) on the robot, and set the `Python Scope` `Path`,
`Version`, and `Library path` to that interpreter instead of relying on
`Auto` detecting 3.13.

### Verification (hand to the user - off-host)
On MOCK-ROBOT, confirm the interpreter version:
`C:\Python313\python.exe --version`
Expect `Python 3.13.x`. Cross-check the pinned package in `project.json`
(`UiPath.Python.Activities 1.8.1`) against the supported-version map; 3.13
requires 1.10.0+.

- **Source:** `python-activities/playbooks/load-script-failures.md` (L1d)

---

**Preventive fix:**

1. **Dependency management** -- when upgrading Python on robot hosts, bump
   `UiPath.Python.Activities` to a version that supports the new interpreter (and
   re-test), or standardize the robot's Python on a version the pinned package
   supports.
   - **Why:** "Upgraded Python, automation broke" is a recurring version-support
     gap; the package release lags new Python versions.
   - **Who:** Platform / robot host team + RPA developer.

2. **Studio** -- pin `Version` explicitly to the supported interpreter rather
   than `Auto`, so a host Python upgrade does not silently push the scope onto an
   unsupported version.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The robot's Python (3.13) is newer than the pinned UiPath.Python.Activities 1.8.1 supports, so the engine cannot initialize (L1d) | High | Confirmed | Yes | Engine-init error naming "Python version 3.13 not supported by UiPath.Python.Activities 1.8.1"; project.json pins 1.8.1; Library path/bitness correct; "recently upgraded Python" | Upgrade the package to 1.10.0+ (supports 3.13), or pin Version/Path to a supported Python (<= 3.12) |

---

Would you like the exact host command to confirm the Python version on
MOCK-ROBOT, or help cleaning up the `.local/investigations/` folder?
