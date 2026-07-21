# Final Resolution

---

**Root Cause:** The runtime robot has an **older `UiPath.System.Activities`** than
the version the workflow was built against (`project.json` pins `25.10.5`). The
`Write CSV` activity in `Main.xaml` sets the `Encoding` property, which exists in
the build-time activity but **not** in the robot's older `WriteCsvFile`. When the
runtime deserializes the XAML it cannot set that member, so the workflow fails to
initialize with `Cannot set unknown member 'UiPath.Core.Activities.WriteCsvFile.Encoding'`.

**What went wrong:** The `ReportExport` job (started 2026-06-15T08:20:11Z)
faulted ~1.6 seconds in, at **workflow initialization** (before any activity
executed), with `System.Xaml.XamlObjectWriterException: Cannot set unknown member
'UiPath.Core.Activities.WriteCsvFile.Encoding'`. It runs in Studio on the
developer machine (which has the newer package) and only fails on the robot —
the signature of an activity-package version mismatch, not a logic defect.

**Why:** A published workflow's XAML records the properties of the activity
versions it was built with. At runtime the robot deserializes that XAML against
**its** installed activity packages. If the robot's `UiPath.System.Activities`
(or `UiPath.Excel.Activities`) is older and lacks a property the XAML sets, the
deserializer raises "Cannot set unknown member". Build-time and runtime activity
versions must match.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: ReportExport -- Faulted at 2026-06-15T08:20:12.760Z (ran ~1.6 seconds, at init)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Exports (key `ea010001-d4e5-4f60-8a01-000000000001`)
- Final error: `Cannot set unknown member 'UiPath.Core.Activities.WriteCsvFile.Encoding'` (`System.Xaml.XamlObjectWriterException`) -> `Main.xaml` -> `WriteCsvFile "Write CSV"` (at workflow initialization, before execution)

### CSV Activities (Root Cause)
- Activity surface: `UiPath.Core.Activities.WriteCsvFile` (Write CSV); the XAML sets `Encoding="UTF-8"`.
- `project.json` pins `UiPath.System.Activities [25.10.5]`. The robot's installed version is older and its `WriteCsvFile` has no `Encoding` member → "unknown member" on deserialization.
- The failure is at init (not a CsvHelper `Method not found`, a delimiter, an access, or an encoding-value error) and is environment-specific (Studio works, robot fails).

---

**Immediate fix:**

Make the runtime's activity-package versions match the build.

### Fix path A -- align the robot to project.json (preferred)
Install the **same `UiPath.System.Activities` version (25.10.5)** — and any other
activity packages `project.json` pins — on the robot / execution server, then
re-run. Activity-package versions must match between build and runtime.

### Fix path B -- rebuild against the runtime's versions
If the robot must stay on its current (older) version, set the project's
dependencies to that version in **Manage Packages**, re-validate, and republish,
so the XAML only sets members the runtime activity defines.

### Verification (hand to the user - off-host)
Compare `project.json`'s `UiPath.System.Activities` version (`25.10.5`) against
the version installed on MOCK-ROBOT (Assistant/Robot package list, or the
runtime's `packages` folder). A mismatch confirms the cause; after aligning,
the workflow initializes and the error is gone.

- **Source:** `csv-activities/playbooks/write-csv-cannot-set-unknown-member.md`

---

**Preventive fix:**

1. **Release hygiene** -- pin and deploy matching activity-package versions to
   robots/execution servers; bump dev and runtime together.
   - **Why:** "Works in Studio, fails on the robot with 'cannot set unknown
     member'" is the classic version-skew failure.
   - **Who:** RPA developer / platform team.

2. **Governance** -- standardize activity-package versions across the robot fleet
   so published packages deserialize consistently.
   - **Who:** Platform team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The robot's UiPath.System.Activities is older than project.json (25.10.5), so the Write CSV Encoding property is unknown to the runtime activity at deserialization | High | Confirmed | Yes | `Cannot set unknown member 'WriteCsvFile.Encoding'` at init; project.json pins 25.10.5; works in Studio, fails on robot | Install matching package versions on the robot (or rebuild against the runtime's versions) |

---

Would you like the exact step to compare the robot's package versions against
project.json, or help cleaning up the `.local/investigations/` folder?
