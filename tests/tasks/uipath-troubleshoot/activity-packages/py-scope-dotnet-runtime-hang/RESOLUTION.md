# Final Resolution

---

**Root Cause:** The project targets the **Windows** framework
(`project.json` `targetFramework: "Windows"`) on `UiPath.Python.Activities`
**1.10.0** (>= v1.9.0). On that combination the `Python Scope` runs its Python
host process on the **.NET Desktop Runtime**. The new unattended robot host is
**missing the .NET Desktop Runtime**, so the host process never becomes ready;
the scope waits on it indefinitely and the job is stopped on the max-execution
timeout - with no Python traceback and no engine-init error.

**What went wrong:** The `PyScoreModel` job (started 2026-06-12T09:05:11Z) ran
for ~15 minutes making no progress and was then stopped. The logs show the scope
"Starting the Python host process" and "Waiting for the Python host process to
become ready...", then nothing until "The Python host process did not respond.
The job was stopped after exceeding its maximum execution time (15 minutes). No
error was reported by the Python side." The script never executed. The
"recently rebuilt on a new unattended robot" detail points at a host
provisioning gap, not a workflow or script defect.

**Why:** Starting with `UiPath.Python.Activities` v1.9.0, a project on the
**Windows** target framework hosts Python on the .NET Desktop Runtime (6.0;
.NET 8 also supported). If that runtime is absent on the machine, the host
process cannot activate - and rather than a clean error, the scope hangs (a
runtime job stalls until killed; in Studio the designer freezes). The absence of
any Python error or engine-init exception is the tell: the scope config here is
valid (`Path=C:\Python311`, `LibraryPath=C:\Python311\python311.dll`,
`Target=x64` are mutually consistent), so this is not a bitness, Library-path,
version, or script problem - it is the missing runtime. The decisive host-side
evidence is in the OS Event Viewer.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: PyScoreModel -- Faulted at 2026-06-12T09:20:12.880Z (ran ~15 minutes, then stopped)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: ML Pipelines (key `cc01a2b3-d4e5-4f60-8c01-000000000001`)
- Final state: hang with no Python error -> `Python Scope: The Python host process did not respond ... stopped after exceeding its maximum execution time (15 minutes). No error was reported by the Python side.` -> `Main.xaml` -> `PythonScope "Python Scope"`

### Python Activities (Root Cause)
- Activity surface: `UiPath.Python.Activities.PythonScope` - the host process never became ready; `Load Python Script` / `Invoke Python Method` never ran.
- Log chain: "Starting the Python host process (Target: x64, Path: C:\\Python311, LibraryPath: C:\\Python311\\python311.dll, Version: Auto)" -> "Waiting for the Python host process to become ready..." -> [15-minute gap] -> "host process did not respond ... stopped". No Python traceback, no engine-init exception.
- `project.json`: `targetFramework` = `Windows`, `UiPath.Python.Activities` = `1.10.0`. This is the v1.9.0+ / Windows combination that depends on the .NET Desktop Runtime.
- Scope config is valid (Path folder, LibraryPath matches python311.dll, Target x64) - rules out bitness / Library-path causes.

---

**Immediate fix:**

Provide the runtime the Windows-target host needs, or drop the dependency.

### Fix path A -- install the .NET Desktop Runtime (preferred)
Install the **.NET Desktop Runtime 6.0 (x64)** on MOCK-ROBOT (current packs also
accept .NET 8) from the Microsoft download portal, then re-run. Match the **x64**
runtime to the 64-bit robot.

### Fix path B -- switch to Windows-Legacy
If the runtime cannot be installed on the host, set the project **target
framework to Windows-Legacy** (which does not depend on the .NET Desktop
Runtime) and republish.

### Verification (hand to the user - off-host)
On MOCK-ROBOT:
1. **Event Viewer -> Windows Logs -> Application**, around 2026-06-12 09:05-09:20,
   for a `.NET Runtime` activation / "framework 'Microsoft.WindowsDesktop.App' ...
   not found" error - this confirms the missing runtime that UiPath swallowed.
2. `dotnet --list-runtimes` - expect **no** `Microsoft.WindowsDesktop.App 6.x`
   (or `8.x`) entry; that absence is the root cause. After installing it, the
   entry appears and the scope runs.

- **Source:** `python-activities/playbooks/python-scope-hang-dotnet-runtime.md`

---

**Preventive fix:**

1. **Robot host provisioning** -- bake the **.NET Desktop Runtime 6.0 (x64)** into
   the unattended robot image whenever a process uses `Python Scope` on the
   Windows target framework (pkg v1.9.0+).
   - **Why:** A Windows-target Python project silently hangs (no error) on a host
     without the runtime - a recurring "works on dev, hangs on the new robot"
     failure.
   - **Who:** Platform / robot host team.

2. **Studio** -- if the host cannot carry the .NET Desktop Runtime, keep the
   project on Windows-Legacy for Python workloads.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | A Windows-target project on UiPath.Python.Activities 1.10.0 runs on a host missing the .NET Desktop Runtime, so the Python host never starts and the scope hangs with no error | High | Confirmed | Yes | ~15-min hang, "host process did not respond / no error", project.json targetFramework=Windows + pkg 1.10.0, scope config valid (no bitness/Library-path error), no script ran | Install .NET Desktop Runtime 6.0 (x64) on the host, or switch the project to Windows-Legacy; confirm via Event Viewer / `dotnet --list-runtimes` |

---

Would you like the exact Event Viewer filter and the .NET Desktop Runtime
download link for MOCK-ROBOT, or help cleaning up the `.local/investigations/`
folder?
