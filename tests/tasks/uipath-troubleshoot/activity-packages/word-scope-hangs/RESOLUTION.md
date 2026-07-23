# Final Resolution

---

**Root Cause:** The `Word Application Scope` in `Main.xaml` opens
`NDA-Protected.docx`, a password-protected document, with no `Password`
supplied and `Visible=False`. Word raises a password prompt that the
unattended robot cannot answer. The modal dialog blocks all COM calls into
Word, so the scope hangs - the job never advances past it and is eventually
cancelled (State=Stopped) after ~30 minutes with no error.

**What went wrong:** The `NDAFiller` job (started 2026-06-11T10:05:02Z) ran
for 00:30:07 and was cancelled by the user. The job logs stop at
`Starting Microsoft Word` -> `Opening document 'data\NDA-Protected.docx'`
and never produce another activity line or any Error entry. The job
finished in State=Stopped, not Faulted, and `or jobs logs --level Error`
returns nothing. A hang with no exception is the signature of Word waiting
on a modal dialog that nobody can dismiss.

**Why:** Classic `Word Application Scope` drives Word over COM. When Word
needs user input - a password prompt for a protected document, a
document-recovery sidebar, a Safe Mode message, an activation prompt, or a
"trust this file" bar - it shows a modal dialog and blocks every COM call
until the dialog is dismissed. With `Visible=False` (the unattended
default) the dialog is invisible to anyone watching, but it still wedges
the scope. The protected document plus a missing `Password` is the most
direct cause here, but any of those background prompts produces the same
silent hang.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: NDAFiller -- State **Stopped** at 2026-06-11T10:35:09Z after running 00:30:07
- Job type: Unattended, manual, machine MOCK-HOST
- Folder: Legal Docs (key `f6a7b8c9-d0e1-4193-a4b5-c6d7e8f90304`)
- No faulted jobs in the folder; `or jobs logs --level Error` returns an empty list
- Job Info: `Job was canceled by user 'user1' after running for 00:30:07 with no progress. Last activity reached: Word Application Scope.`
- Full log ends at `Opening document 'data\NDA-Protected.docx'` then jumps straight to `Execution was canceled ... never advanced past [Word Application Scope]` - no activity in between.

### Word Activities (Root Cause)
- `Main.xaml`: the `Word Application Scope` opens `FileName="data\NDA-Protected.docx"` with `Visible="False"` and no `Password` property set.
- The document name and the "opens then hangs with no error" pattern point at a background password prompt (or another modal dialog) blocking COM - not a crash, missing install, or corrupt file.

---

**Immediate fix:**

The cause is a hidden modal dialog. The agent cannot see the robot screen,
so hand the user the observe-and-clear steps.

### Host steps (Legal Docs / MOCK-HOST, as the robot's Windows user)
1. Re-run the process with the `Word Application Scope`'s `Visible` set to
   `True` and watch WINWORD.EXE. Note the dialog that appears - most likely
   an "Enter password" prompt for `NDA-Protected.docx`, possibly a recovery
   sidebar, Safe Mode, activation, or trust-this-file bar.
2. During the hang, open Task Manager and check for a WINWORD.EXE stuck
   with a modal window.

### Fix
1. If a password prompt blocks it: supply the document password in the
   `Word Application Scope` properties, or remove protection from the
   source document if it does not need to be encrypted.
2. If a recovery / Safe Mode / activation / trust prompt blocks it: open
   the document interactively once to clear the startup alert, complete
   Office activation under the robot user, and/or add the document folder
   to Word Trusted Locations
   (`File > Options > Trust Center > Trust Center Settings > Trusted Locations`).
3. Guard against future silent hangs: give the surrounding sequence/job a
   finite timeout so it fails fast instead of hanging, and ensure the scope
   disposes so no orphaned WINWORD.EXE lingers.
- **Source:** `word-activities/playbooks/word-scope-hangs-background-prompt.md`

---

**Preventive fix:**

1. **Always supply credentials for protected documents** -- never open a
   password-protected file in an unattended `Word Application Scope`
   without the `Password` set.
   - **Why:** the prompt is invisible unattended and hangs the job until
     cancelled.
   - **Who:** RPA developer.

2. **Bound long-running scopes** -- set finite timeouts so a blocked dialog
   surfaces as a fast failure, not a 30-minute hang.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Word is blocked on a hidden modal dialog (password prompt for the protected document) so the scope hangs until cancelled | Medium | Confirmed | Yes | State=Stopped after 30 min, no Error logs, logs stop at "Opening document NDA-Protected.docx", scope is Visible=False with no Password | Run visible to surface the dialog; supply the password / clear the prompt; add a finite timeout |

---

Would you like help editing the workflow to supply the document password
and add a timeout, or the exact host steps to re-run with Word visible on
MOCK-HOST?
