# Final Resolution

---

**Root Cause:** The `Attach Document` activity
(`UiPath.Testing.Activities.AttachDocument`) in `Main.xaml` has
`FilePath="C:\TestData\evidence\run-report.pdf"`. That file does not exist at
runtime. `Attach Document` validates the input file with a `File.Exists` check
**before** it makes any Orchestrator / test-case call, so the missing file
faults the activity synchronously with
`System.IO.FileNotFoundException: C:\TestData\evidence\run-report.pdf` — the
exception **message is the path itself**.

This maps to:
`references/activity-packages/testing-activities/playbooks/attach-document-file-not-found.md`

**What went wrong:** The `EvidenceArchival` job (started
2026-06-25T07:39:46.717Z) faulted ~3.5 seconds after launch the moment its
single `Attach Document` activity ran. There is no upstream activity — the
attach is the first and only step — so the missing artifact surfaces
immediately.

**Why:** `Attach Document` checks that the input file exists before it streams
it to the test case. The path `C:\TestData\evidence\run-report.pdf` is not
present on the robot host at runtime, so the `File.Exists` guard throws. The
`.NET` stack is
`UiPath.Shared.Testing.Orchestrator.Services.AttachDocumentService.AttachDocument`
-> `UiPath.Testing.Activities.AttachDocument.ExecuteAsync` — no test-case /
Orchestrator-call frames, confirming the fault precedes any server interaction.

---

**This is NOT:**

- **NOT an Orchestrator connectivity / robot-reach problem.** The job ran on
  the robot (`State` went Pending -> Running -> Faulted), produced job logs,
  and faulted with a local file-system exception — not a connection or
  enqueue error.
- **NOT a missing Test-Job / test-case context.** `Attach Document` only
  attaches to a test case when run inside a Test Job, but the
  `FileNotFoundException` is raised by the activity's `File.Exists` check
  **before** that test-case interaction and **is** the real fault. It must not
  be dismissed as "expected outside a test job" — the activity never reached
  the attach call; it failed on the missing input file.
- **NOT a permissions / access-denied problem.** The exception is
  `System.IO.FileNotFoundException`, not an access-denied / `E_ACCESSDENIED`.
  The path is absent, not protected.
- **NOT a different activity or package.** The fault originates in
  `UiPath.Testing.Activities.AttachDocument`, named explicitly in both the job
  `Info` stack and the error log, and corresponds to the single
  `uta:AttachDocument` node in `Main.xaml`.
- **NOT a folder-path / Orchestrator-folder issue.** The folder `Shared`
  (key `defb8e05-e36b-4c36-bf11-0b4d08ce6cd1`) resolved and the job ran there;
  the missing file is a local filesystem path, unrelated to the Orchestrator
  folder.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `EvidenceArchival` -- Faulted at 2026-06-25T07:39:50.263Z (ran ~3.5 seconds)
- Job type: Unattended, source Manual, on machine MOCK-HOST
- Folder: Shared (key `defb8e05-e36b-4c36-bf11-0b4d08ce6cd1`)
- Job key: `e192429e-1248-4872-863a-24ad8f6e88fe`
- History: Pending (07:39:15) -> Running (07:39:46) -> Faulted (07:39:50)
- Final error (`jobs get` `Info` and `jobs logs --level Error`):
  `Attach Document: C:\TestData\evidence\run-report.pdf` ->
  `Main.xaml` -> `AttachDocument "Attach Document"` ->
  `Sequence "Archive Evidence"` -> `Main "Main"`, with
  `System.IO.FileNotFoundException: C:\TestData\evidence\run-report.pdf` and a
  stack rooted at
  `UiPath.Shared.Testing.Orchestrator.Services.AttachDocumentService.AttachDocument`
  -> `UiPath.Testing.Activities.AttachDocument.ExecuteAsync`.

### Testing Activities (Root Cause)
- `Main.xaml`: a `Sequence "Archive Evidence"` whose only child is
  `<uta:AttachDocument ... FilePath="C:\TestData\evidence\run-report.pdf" />`.
  The `FilePath` literal matches the exception message character-for-character.
- The exception **message is the path**, and the stack has **no test-case
  frames** — the signature of the pre-attach `File.Exists` check failing on a
  missing input file.

---

**Immediate fix:**

Correct / validate the `Attach Document` `FilePath` so the file exists at that
path when the robot runs.

1. **Confirm the path the activity targets.**
   - **What:** In `Main.xaml`, `Attach Document` has
     `FilePath="C:\TestData\evidence\run-report.pdf"`. That is the exact path
     in the `FileNotFoundException`.
   - **Why:** The activity faults because nothing exists at that path on the
     robot host at runtime.

2. **Make the file exist at that path (or fix the path).**
   - **What:** Either ensure `C:\TestData\evidence\run-report.pdf` is present
     on the robot host under the robot's identity, OR correct `FilePath` to
     the real location of the report. If the report is produced by an upstream
     step, ensure that step ran and wrote to this exact path. If the path is
     relative or machine-specific, anchor it to a known base so it resolves
     identically on the robot.
   - **Why:** `Attach Document`'s `File.Exists` check must pass before it can
     attach.

3. **Guard the attach for best-effort artifacts.**
   - **What:** If the evidence file is optional, wrap `Attach Document` in a
     `File.Exists(...)` `If` (or a `Try Catch`) so a missing artifact does not
     fault the job.
   - **Why:** Prevents a missing optional file from failing the whole run.

Re-run `EvidenceArchival` after the file is in place (or the path corrected)
and confirm the attach succeeds. That confirms the fix and closes the case.

---

**Preventive fix:**

1. **Use fully-qualified, robot-valid paths for attachment inputs.** Avoid
   developer-machine paths that do not exist on the unattended robot host;
   anchor any relative path to a known base.
   - **Why:** A path that exists on the dev machine but not the robot is the
     most common reason `Attach Document` faults with `FileNotFoundException`.
   - **Who:** RPA developer.

2. **Guard optional attachments with `File.Exists`.** When an attachment is
   best-effort, check the file exists before attaching.
   - **Why:** Keeps a missing optional artifact from failing the test/job.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The `Attach Document` `FilePath` (`C:\TestData\evidence\run-report.pdf`) points at a file that does not exist at runtime; the activity's pre-attach `File.Exists` check throws `System.IO.FileNotFoundException` | High | Confirmed | Yes | `FileNotFoundException` message = the path; stack `AttachDocumentService.AttachDocument` with no test-case frames; `FilePath` in `Main.xaml` matches the path verbatim | Correct/validate `FilePath` so the file exists at runtime; guard with `File.Exists` for optional artifacts |
| H2 | Missing Test-Job / test-case context (attach not valid outside a Test Job) | Low | Eliminated | No | The fault is a `File.Exists` failure raised before any test-case call; no test-case frames in the stack | n/a |

---

Would you like me to draft the `Main.xaml` `FilePath` correction (or a
`File.Exists` guard) as a concrete edit, or clean up the
`.local/investigations/` folder?
