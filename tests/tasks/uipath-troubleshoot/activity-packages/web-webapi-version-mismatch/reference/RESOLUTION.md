# Final Resolution

---

**Root Cause:** The project's dependency set in `project.json` is incompatible
with the installed Studio. It pins `UiPath.WebAPI.Activities` at `[1.16.2]`
while `UiPath.System.Activities` is at `[21.10.5]` and the developer is on
**UiPath Studio 2021.10** (`studioVersion 21.10.5.0`). The `UiPath.WebAPI.Activities`
build requires a newer Studio line than the one installed; when the workflow
is opened, validated, or the **HTTP Request wizard** is configured, the Web
Activities assembly binds against the older Studio/`System.Activities`
runtime, a member it was compiled against is absent, and Studio throws
`System.MissingMethodException: Method not found: 'Void
UiPath.Web.Activities...'`. This is a **package-vs-Studio (and package-vs-System)
version mismatch**, surfacing at design time / validation. The process has
never executed, so there are no Orchestrator jobs to inspect.

**What went wrong:** Opening / validating `OrderStatusSync`, or clicking
Configure on the HTTP Request wizard, raises `MissingMethodException` naming
`UiPath.Web.Activities`; the HTTP Request activity shows an error. There is no
faulted job and no runtime log because the process never ran — the failure is
entirely at design time. `project.json` shows `UiPath.WebAPI.Activities
[1.16.2]`, `UiPath.System.Activities [21.10.5]`, `studioVersion 21.10.5.0`.

**Why:** `MissingMethodException` / "Method not found" means the
`UiPath.Web.Activities` assembly **loaded** but a member the caller was
compiled against is **absent** — the hallmark of a version mismatch, not a
missing assembly. A `UiPath.WebAPI.Activities` build that targets a newer
Studio than the installed 2021.10 (and sits ahead of the `UiPath.System.Activities`
21.10 line) resolves activity/wizard code that the installed runtime cannot
satisfy, so the method lookup fails at bind time.

---

**Evidence:**

### Design-time (Root Cause)
- Symptom: `System.MissingMethodException: Method not found: 'Void UiPath.Web.Activities...'` on opening / validating the workflow in Studio or configuring the HTTP Request wizard; the HTTP Request activity shows an error. No execution.
- `project.json`: `"UiPath.WebAPI.Activities": "[1.16.2]"`, `"UiPath.System.Activities": "[21.10.5]"`, `"studioVersion": "21.10.5.0"` — the WebAPI package requires a newer Studio than the installed 2021.10 and is out of step with the foundational System.Activities line.
- The error appears at design time / validation, not as a runtime job fault.

### Orchestrator (ruled out)
- No jobs exist for this process (it has never run); `or jobs list ... --state Faulted` returns an empty list. Job evidence is not the source of this diagnosis — `project.json`'s dependency set + the installed Studio version are.

### Runtime assembly-load fault (ruled out)
- This is NOT the runtime `System.IO.FileNotFoundException` / `FileLoadException`
  "Could not load file or assembly 'UiPath.WebAPI.Activities'" fault (works in
  Studio, fails on the robot because the robot's NuGet cache or the
  Orchestrator feed can't supply the pinned version). Here the assembly loads
  — a method is missing — and the failure reproduces in Studio at design time.
  Cleaning `%userprofile%\.nuget\packages` / republishing is the WRONG fix; it
  does not change which versions `project.json` resolves against the installed
  Studio.

---

**Immediate fix:**

Align the WebAPI package to a line compatible with the installed Studio via
**Manage Packages** — do not bump the package ahead of the Studio/System line.

### Fix path A -- align to the installed Studio (recommended)
- Open `Manage Packages` in Studio and set `UiPath.WebAPI.Activities` to a
  version whose minimum-Studio requirement the installed 2021.10 satisfies,
  moving it together with `UiPath.System.Activities` to the same mutually
  compatible line. Reopen / revalidate the workflow and the HTTP Request
  wizard.

### Fix path B -- upgrade Studio to the line the package needs
- If the project must stay on `UiPath.WebAPI.Activities [1.16.2]`, upgrade
  UiPath Studio to the version that package requires, then update
  `UiPath.System.Activities` to match.
- **Source:** `web-activities/playbooks/package-version-mismatch.md`.

> Do not chase Orchestrator/runtime evidence and do not clean the NuGet cache
> or republish — the process never ran and the assembly loads fine. The fix
> is version alignment of the WebAPI package with the installed Studio (and
> the System.Activities line) in Manage Packages.

---

**Preventive fix:**

1. **Bump activity packages as a compatible set, aligned to the target Studio**
   -- when updating `UiPath.WebAPI.Activities`, confirm its minimum-Studio
   requirement is met and move `UiPath.System.Activities` to a matching line.
   - **Why:** a WebAPI package ahead of the installed Studio/System line
     resolves wizard/activity code the runtime cannot satisfy and throws
     `MissingMethodException` at bind time.
   - **Who:** RPA developer / platform team.

2. **Validate dependency bumps in the target Studio before committing** --
   confirm the project opens, validates, and the HTTP Request wizard
   configures cleanly on the Studio line the team runs.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | project.json pins UiPath.WebAPI.Activities [1.16.2] incompatibly with Studio 2021.10 / UiPath.System.Activities [21.10.5], so Web Activities bind an unsatisfiable runtime and throw MissingMethodException at design time | Medium | Confirmed | Yes | Design-time MissingMethodException "Method not found: 'Void UiPath.Web.Activities...'" + project.json version skew vs studioVersion 21.10.5.0 + never ran (no jobs) | Align WebAPI to a Studio-2021.10-compatible line via Manage Packages (or upgrade Studio to match the package) |

---

Would you like the specific `UiPath.WebAPI.Activities` version known to work
on Studio 2021.10, or guidance on moving the whole project to the latest
stable Studio + package line instead?
