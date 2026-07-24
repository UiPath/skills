# Final Resolution

---

**Root Cause:** A **known Robot defect** — the executor bootstrap
fails to create its credential-provider working directory under
`C:\Windows\TEMP\UiPath\CredProvider`, so the job faults at start
with `Could not start executor. Could not find a part of the path
'C:\Windows\TEMP\UiPath\CredProvider'.` This is documented issue
**ROBO-4022**, fixed in Robot **23.10.9**. The host runs Robot
**23.10.4**, which predates the fix. This is the
`known-issue-robot-defect` playbook: the fault is a fixed bug in the
Robot build, not a configuration problem to repair by hand.

**What went wrong:** Job `bbccddee-...-bbccdd` (LedgerPostingBot,
BackOffice) faulted ~0.6s after start on `MOCK-HOST`. The Robot log
notes the failure "matches a known Robot defect on builds prior to
23.10.9," and `uip or machines list` shows the host template
(`BackOfficeRuntime`) running Robot `23.10.4`.

**Why:** The running version (`23.10.4`) is older than the fix
version (`23.10.9`). The defect is in how the older executor handles
its CredProvider TEMP directory; upgrading the Robot resolves it.

**Ruled out (common wrong turns):**
- **Hand-create the missing folder / change TEMP permissions** —
  the directory is created by the executor at runtime; manually
  making it (or editing ACLs) does not fix the underlying build
  defect and is not the supported resolution.
- **Credential-store / logon problem** — there is no `Logon failed`
  code and no credential-retrieval error; the failure is executor
  bootstrap, matched to a known issue.

---

**Evidence:**

### Orchestrator
- Failing job `bbccddee-...-bbccdd` — LedgerPostingBot, Faulted
  `2026-06-28T06:00:02Z`, `HostMachineName: MOCK-HOST`
- Job `Info`: `Could not start executor. Could not find a part of
  the path 'C:\Windows\TEMP\UiPath\CredProvider'.`
- Robot log: `Executor bootstrap failed creating the
  credential-provider working directory ... This matches a known
  Robot defect on builds prior to 23.10.9.`
- `uip or machines list`: `BackOfficeRuntime` → `RobotVersion:
  23.10.4` (predates the 23.10.9 fix)
- Known issue: ROBO-4022, fixed in 23.10.9 (customer-portal
  known-issues feed)

---

**Immediate fix:**

1. **Upgrade the Robot on the affected host(s) to ≥ 23.10.9.**
   - **Why:** The CredProvider-path failure is a known Robot defect
     (ROBO-4022) corrected in 23.10.9. The host runs 23.10.4.
     Upgrading past the fix version resolves it; no manual folder or
     permission changes are needed or supported.
   - **Where:** Update the Robot build on the `BackOfficeRuntime`
     hosts from `23.10.4` to `23.10.9` (or later).
   - **Who:** Platform / machine admin
   - **Source:**
     `products/orchestrator/playbooks/known-issue-robot-defect.md`

2. **Rerun** the LedgerPostingBot job after the upgrade.

---

**Preventive fix:**

1. **Fleet hygiene** — Keep robots on a current, patched version;
   most executor-start faults like this are fixed in later releases.
2. **Triage habit** — Match a `Could not start executor` signature
   against the customer-portal known-issues feed + the host Robot
   version before deep-diagnosing — a known-and-fixed defect is a
   version bump, not an investigation.
   - **Source:**
     `products/orchestrator/playbooks/known-issue-robot-defect.md`
     (Prevention)

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Known Robot defect (ROBO-4022, CredProvider path) on a build < 23.10.9 | High | Confirmed | Yes | Info = CredProvider TEMP path; log flags a known defect < 23.10.9; machines list shows Robot 23.10.4 | Upgrade Robot to ≥ 23.10.9; rerun |
| H2 | Missing folder / TEMP permissions to fix by hand | Low | Refuted | No | Directory is created by the executor at runtime; manual creation/ACL changes don't fix the build defect | n/a |
| H3 | Credential-store / logon failure | Low | Refuted | No | No logon code, no credential-retrieval error; failure is executor bootstrap matched to a known issue | n/a |

---

Would you like help planning the Robot upgrade to 23.10.9 across the
BackOffice hosts?
