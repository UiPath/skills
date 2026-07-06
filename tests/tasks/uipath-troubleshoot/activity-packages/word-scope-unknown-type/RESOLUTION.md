# Final Resolution

---

**Root Cause:** `Main.xaml` references `Word Application Scope` from the
`UiPath.Word.Activities` package (pinned `[1.17.2]` in `project.json`). The
unattended robot (MOCK-ROBOT-02) does not have that package version
restored, so the `WordApplicationScope` type cannot be created and the
process faults at **load time** with
`Cannot create unknown type '{clr-namespace:UiPath.Word.Activities;assembly=UiPath.Word.Activities}WordApplicationScope'`
before any activity runs. This is a package restore / version-availability
gap on the robot, not a workflow-logic defect.

**What went wrong:** The `InvoiceLetters` job (started
2026-06-09T14:03:01Z) faulted ~0.8 seconds after launch - too fast to have
opened a document or hit COM. The error is a `XamlObjectWriterException`
("Cannot create unknown type ... WordApplicationScope"), which fires while
the runtime deserializes the workflow and cannot resolve the activity type
from a loaded assembly. The process runs in Studio (which has the package)
and fails only on the new robot - the signature of a missing/mismatched
package on the execution host.

**Why:** The XAML names `WordApplicationScope` in
`UiPath.Word.Activities`, and `project.json` declares that dependency. At
runtime the robot must restore the same `UiPath.Word.Activities` version
and load its assembly to instantiate the activity. If the published
package did not bundle the dependency, or the robot's feed does not carry
that version, the type is unknown and the workflow fails to load. No COM
call, no document access, no Word install is involved - the failure is
upstream of execution.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: InvoiceLetters -- Faulted at 2026-06-09T14:03:02.060Z (ran for ~0.8 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT-02
- Folder: Doc Automation (key `b2c3d4e5-f6a7-4182-93a4-b5c6d7e8f902`)
- Final error: `System.Xaml.XamlObjectWriterException: Cannot create unknown type '{clr-namespace:UiPath.Word.Activities;assembly=UiPath.Word.Activities}WordApplicationScope'` -> `Main.xaml` -> `Main "Main"`
- The fault is at workflow load (no `Execution started` -> activity logs; the type fails to construct), distinguishing it from the COM `REGDB_E_CLASSNOTREG` startup fault.

### Project source (Root Cause)
- `Main.xaml` references `ui:WordApplicationScope` and declares
  `UiPath.Word.Activities` in `TextExpression.ReferencesForImplementation`.
- `project.json` pins `"UiPath.Word.Activities": "[1.17.2]"`.
- The error names exactly that assembly/type, so the robot did not have
  `UiPath.Word.Activities` 1.17.2 restored when it tried to load the
  workflow.

---

**Immediate fix:**

The cause is unambiguous from the error, but the remediation is on the
package feed / robot side, which the agent cannot perform. Hand the user
the steps.

### Steps (package feed / publish)
1. Confirm `UiPath.Word.Activities` `1.17.2` (the `project.json` version)
   exists on the feed the robot restores from (tenant/host Orchestrator
   feed or the configured NuGet source).
2. If it is missing, push that exact version to the feed, OR update the
   project to a version that IS on the feed and re-pin `project.json`.
3. Re-publish the `InvoiceLetters` process so the dependency is bundled,
   then re-deploy the release to the "Doc Automation" folder.
4. Confirm MOCK-ROBOT-02 can reach the feed (no proxy/credential gap on
   the robot's restore path).
- **Source:** `word-activities/playbooks/word-scope-cannot-create-unknown-type.md`

> Do NOT change the workflow logic or the `WordApplicationScope` activity -
> the XAML is correct. The fix is making the referenced package version
> resolvable on the robot.

---

**Preventive fix:**

1. **Version pinning + feed parity** -- pin `UiPath.Word.Activities` in
   `project.json` and ensure the robot's feed always carries the pinned
   versions used across the portfolio.
   - **Why:** "Works in Studio, fails on the robot" recurs whenever the
     robot's available package versions diverge from the developer's.
   - **Who:** RPA developer + platform team.

2. **Publish verification** -- after publishing, verify the released
   package bundled its dependencies (or that the robot feed resolves them)
   before scheduling on a new robot.
   - **Who:** Release owner.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The robot lacks the UiPath.Word.Activities version the project pins, so WordApplicationScope cannot be created and the workflow faults at load | High | Confirmed | Yes | `XamlObjectWriterException: Cannot create unknown type ... WordApplicationScope` at ~0.8s load + project.json pins `[1.17.2]` + works in Studio, fails on new robot | Make the pinned UiPath.Word.Activities version available on the robot feed, pin it, and republish |

---

Would you like the exact `uip` / Orchestrator steps to check the feed for
`UiPath.Word.Activities` 1.17.2 and republish, or help cleaning up the
`.local/investigations/` folder?
