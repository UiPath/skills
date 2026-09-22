# Final Resolution

---

**Root Cause:** Microsoft Word (WINWORD.EXE) was **busy** when the
`Replace Text` activity issued its COM call. The job log shows a Word
instance was already running on the host when the scope started (an
orphaned or concurrent WINWORD.EXE), so the COM message filter rejected the
call with `RPC_E_SERVERCALL_RETRYLATER` (0x8001010A). The intermittency —
"re-running sometimes works" — is the signature of a transient busy state,
not a workflow defect.

**What went wrong:** The `BatchLetterFill` job (started
2026-06-13T15:12:03Z) opened Word, logged
`A Microsoft Word instance was already running on the host when the scope
started`, then faulted at `Replace Text` with
`The message filter indicated that the application is busy. (Exception from
HRESULT: 0x8001010A (RPC_E_SERVERCALL_RETRYLATER))`. Because the failure
depends on whether Word is busy at the moment of the call, it reproduces
only sometimes.

**Why:** Classic Word activities drive Word over COM. When WINWORD.EXE is
busy — already open in the background, locked by another session, or
stalled on a modal dialog — the COM message filter rejects incoming calls
with `RPC_E_SERVERCALL_RETRYLATER` / `RPC_E_CALL_REJECTED`. A leftover
WINWORD.EXE from a prior run, a concurrent job, or an interactive Word
window on the host all produce this. With `Visible = False` a blocking
dialog is invisible but still holds Word busy.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: BatchLetterFill -- Faulted at 2026-06-13T15:12:07.260Z (ran ~3.8s)
- Job type: Unattended, manual, machine MOCK-HOST
- Folder: Doc Batch (key `a2b3c4d5-e6f7-4193-8a9b-0c1d2e3f4051`)
- Warning log: `[Word Application Scope] A Microsoft Word instance was already running on the host when the scope started.`
- Final error: `RPC_E_SERVERCALL_RETRYLATER (0x8001010A)` -> `WordReplaceText "Replace Text"` -> `WordApplicationScope` -> `Main.xaml`

### Word Activities (Root Cause)
- The "Word already running" warning immediately before the busy HRESULT,
  plus the reported intermittency, points at a busy/locked WINWORD.EXE
  (orphaned or concurrent), not at a missing install or a code defect.
- This is the operation-time busy signal (`0x8001010A`), distinct from the
  scope-startup `REGDB_E_CLASSNOTREG` "Word not installed" fault.

---

**Immediate fix:**

Clear the busy/locked Word session and make the workflow resilient. Hand
the user the workflow change and the host checks.

### Host check (Doc Batch / MOCK-HOST, as the robot's Windows user)
1. During/after a failing run, open Task Manager and look for orphaned
   `WINWORD.EXE` instances with no window; end them
   (`Stop-Process -Name WINWORD -Force`).
2. Confirm the document is not open in an interactive Word window and no
   concurrent job/schedule touches it at the same time.

### Workflow fix
1. Add a **Kill Process** activity with `ProcessName = "WINWORD"`
   immediately **before** the `Word Application Scope` to clear any locked
   session, and ensure the scope disposes so Word always closes cleanly.
2. Wrap the operation in a **Retry Scope** so a transient
   `RPC_E_SERVERCALL_RETRYLATER` retries instead of faulting the job on the
   first busy signal.
3. If a hidden dialog is suspected, re-run with the scope `Visible = True`
   to surface it; see word-scope-hangs-background-prompt.md.
- **Source:** `word-activities/playbooks/replace-text-com-busy.md`

---

**Preventive fix:**

1. **Always dispose Word scopes + avoid overlap** -- ensure the scope
   disposes on every path so no orphaned WINWORD.EXE lingers, and avoid
   overlapping schedules / interactive use of the same host.
   - **Who:** RPA developer + scheduler owner.

2. **Make COM operations retry-tolerant** -- wrap Word interactions in a
   Retry Scope to absorb transient busy signals.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | WINWORD.EXE was busy/locked (orphaned or concurrent instance) when Replace Text issued its COM call, so the message filter rejected it | Medium | Confirmed | Yes | `RPC_E_SERVERCALL_RETRYLATER (0x8001010A)` at Replace Text + "Word already running on the host" warning + intermittent ("re-running sometimes works") | Kill Process WINWORD before the scope (+ dispose), confirm not open elsewhere, wrap in Retry Scope |

---

Would you like help adding the Kill Process + Retry Scope to the workflow,
or the exact host commands to clear orphaned WINWORD.EXE on MOCK-HOST?
