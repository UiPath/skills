# Final Resolution

---

**Root Cause:** The project pins `UiPath.Word.Activities` at `[2.0.0]`, but
the developer is running **UiPath Studio 2021.10**, which cannot construct
that newer package's activity designer. When the `Replace Text` activity is
dropped onto the canvas (or the workflow that contains it is opened), the
designer-construction reflection call throws
`System.Reflection.TargetInvocationException` and Studio becomes unstable.
This is a **design-time** Studio↔package version mismatch — the workflow has
never executed, so there are no Orchestrator jobs to inspect.

**What went wrong:** Opening `ClauseInserter` / dropping `Replace Text`
crashes Studio at design time with `TargetInvocationException`. There is no
faulted job and no runtime log because the process never ran — the failure
is entirely in the Studio designer. `project.json` shows
`UiPath.Word.Activities [2.0.0]` against `studioVersion 21.10.5.0`.

**Why:** A package version newer than the installed Studio can ship an
activity whose designer types Studio 2021.10 cannot load/instantiate. Studio
constructs the designer via reflection when the activity is placed or the
workflow opened; if the type can't be created, the reflection call surfaces
as `TargetInvocationException` (often wrapping an inner type/version load
error). Because this happens in the designer, it is independent of the
robot/runtime — it is purely a Studio-vs-package incompatibility.

---

**Evidence:**

### Design-time (Root Cause)
- Symptom: `TargetInvocationException` on dropping `Replace Text` / opening the workflow in Studio; Studio goes unstable. No execution.
- `project.json`: `"UiPath.Word.Activities": "[2.0.0]"`, `"studioVersion": "21.10.5.0"` — a package major newer than the installed Studio supports.
- The crash is at design time in the designer, not a runtime job fault.

### Orchestrator (ruled out)
- No jobs exist for this process (it has never run); `or jobs list ... --state Faulted` returns an empty list. Job evidence is not the source of this diagnosis — the project source + the Studio version are.
- This is NOT the runtime `Cannot create unknown type WordApplicationScope` fault (a robot missing the package at execution). Here the package is present in the project; Studio simply can't construct its designer.

---

**Immediate fix:**

Align the Studio and `UiPath.Word.Activities` versions. Either path works.

### Fix path A -- downgrade the package to match Studio (quickest)
- Open `Manage Packages` in Studio, select `UiPath.Word.Activities`, and
  **downgrade to a version compatible with Studio 2021.10** (a known-stable
  release for that Studio line), then reopen the workflow.

### Fix path B -- upgrade Studio to support the newer package
- If `UiPath.Word.Activities 2.0.0` is required (e.g. for features other
  activities depend on), **upgrade UiPath Studio** to a version that
  supports it, so the whole dependency set is compatible.
- **Source:** `word-activities/playbooks/replace-text-version-mismatch.md`

> Do not chase Orchestrator/runtime evidence - the workflow never ran. The
> fix is the Studio↔package version alignment in Manage Packages.

---

**Preventive fix:**

1. **Keep Studio and activity packages on compatible versions** -- pin
   package versions that match the team's installed Studio line; bump them
   together.
   - **Why:** a package newer than Studio crashes the designer at
     design time.
   - **Who:** RPA developer / platform team.

2. **Validate dependency bumps in the target Studio** -- before committing a
   package upgrade, confirm it opens cleanly in the Studio version the team
   runs.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | UiPath.Word.Activities [2.0.0] is newer than Studio 2021.10 can construct, so the designer throws TargetInvocationException at design time | Medium | Confirmed | Yes | Design-time TargetInvocationException on drop/open + project.json pins Word.Activities [2.0.0] vs studioVersion 21.10.5.0 + never ran (no jobs) | Align via Manage Packages: downgrade the package to a 2021.10-compatible version, or upgrade Studio |

---

Would you like the specific `UiPath.Word.Activities` version range known to
work with Studio 2021.10, or guidance on upgrading Studio instead?
