# Final Resolution

---

**Root Cause:** `CsvHelper.dll` is bundled in **both** `UiPath.System.Activities`
(which provides `Append To CSV`) and `UiPath.Excel.Activities`. The project pins
**mismatched versions** — `UiPath.System.Activities [23.4.0]` and
`UiPath.Excel.Activities [2.24.4]` — which bundle incompatible `CsvHelper`
builds. `Append To CSV` is compiled against one `CsvHelper` API but the runtime
resolves the other assembly, so the constructor it calls does not exist and the
activity throws `System.MissingMethodException: Method not found: 'Void
CsvHelper.CsvWriter..ctor(System.IO.TextWriter, CsvHelper.Configuration.CsvConfiguration)'`.

**What went wrong:** The `CsvExporter` job (started 2026-06-13T08:02:14Z) read
the Excel range successfully, then faulted ~2 seconds later at the `Append To
CSV` step with the `CsvHelper` `Method not found` error. The "recently upgraded
one of the activity packages" detail corroborates a version split between the two
packages that share `CsvHelper`.

**Why:** `CsvHelper` is a transitive dependency shared by `UiPath.System.Activities`
and `UiPath.Excel.Activities`. NuGet/Studio resolves a single `CsvHelper.dll` for
the project; when the two UiPath packages are on release lines that expect
different `CsvHelper` versions, the resolved assembly satisfies only one of them.
The CSV activity (from System.Activities) then calls a `CsvHelper` member/ctor
signature that is absent in the bound version — a classic `MissingMethodException`.
This is a dependency/binding conflict, not a file, data, or host problem.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: CsvExporter -- Faulted at 2026-06-13T08:02:16.540Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Reporting (key `ca010001-d4e5-4f60-8a01-000000000001`)
- Final error: `Append To CSV: Method not found: 'Void CsvHelper.CsvWriter..ctor(System.IO.TextWriter, CsvHelper.Configuration.CsvConfiguration)'` -> `Main.xaml` -> `AppendToCsvFile "Append To CSV"` (the Read Range step succeeded first)

### CSV Activities (Root Cause)
- Activity surface: `UiPath.Core.Activities.AppendToCsvFile` (Append To CSV), from `UiPath.System.Activities`.
- The error names a `CsvHelper.CsvWriter` constructor — the signature of a `CsvHelper` assembly-binding conflict, not a file/data error.
- `project.json` pins `UiPath.System.Activities [23.4.0]` and `UiPath.Excel.Activities [2.24.4]` — both bundle `CsvHelper`, and these versions are not aligned.

---

**Immediate fix:**

Align the two packages that share `CsvHelper`.

### Fix path A -- upgrade both packages (preferred)
In Studio's **Manage Packages**, upgrade **both** `UiPath.System.Activities` and
`UiPath.Excel.Activities` to their latest stable versions from the same release
line, so their bundled `CsvHelper` requirements match. Rebuild and republish.

### Fix path B -- align to a compatible pair
If you cannot move to latest, set both packages to a known-compatible
combination (same release line) rather than leaving one upgraded and the other
behind. Leaving them split re-introduces the conflict.

### Verification
After aligning, the project resolves a single consistent `CsvHelper`, the
`Append To CSV` constructor binds, and the `Method not found` no longer occurs on
re-run.

- **Source:** `csv-activities/playbooks/csv-helper-method-not-found.md`

---

**Preventive fix:**

1. **Dependency hygiene** -- upgrade `UiPath.System.Activities` and
   `UiPath.Excel.Activities` together; they share `CsvHelper`, so bumping one in
   isolation creates a binding conflict.
   - **Why:** "Upgraded one package, CSV broke" is the recurring shape of this
     failure.
   - **Who:** RPA developer.

2. **Build gate** -- catch the `MissingMethodException` in a dev/test run before
   publishing when activity-package versions change.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | CsvHelper version conflict: UiPath.System.Activities and UiPath.Excel.Activities pin mismatched versions that bundle incompatible CsvHelper, so Append To CSV binds the wrong assembly | High | Confirmed | Yes | `Method not found: 'CsvHelper.CsvWriter..ctor(...)'` at Append To CSV; project.json System [23.4.0] vs Excel [2.24.4]; Read Range succeeded first | Upgrade/align both UiPath.System.Activities and UiPath.Excel.Activities to current stable |

---

Would you like the exact compatible version pair for your Studio release, or help
cleaning up the `.local/investigations/` folder?
