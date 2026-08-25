# Final Resolution

---

**Root Cause:** A **known Robot defect** — on affected builds the
Robot stores its Credential Provider logs under
`C:\Windows\TEMP\UiPath\CredProvider`, a TEMP location that can be
cleaned up; when the executor then finds the path missing at start-up
the job faults with `Could not start executor. Could not find a part
of the path 'C:\Windows\TEMP\UiPath\CredProvider'.` This is documented
in UiPath KB 799589: affected on builds up to `23.4.9` / `23.10.8` /
`24.10.4`, fixed in `23.4.11` / `23.10.10` / `24.10.7` (the fix
relocates these logs to `%programdata%`). The host runs Robot
**23.10.4**, which predates the fix. This is the
`known-issue-robot-defect` playbook: the fault is a fixed bug in the
Robot build, not a configuration problem to repair by hand.

**What went wrong:** Job `bbccddee-...-bbccdd` (LedgerPostingBot,
BackOffice) faulted ~0.6s after start on `MOCK-HOST`, the executor
unable to find the credential-provider log directory
`C:\Windows\TEMP\UiPath\CredProvider`. Correlating that signature
with the customer-portal known-issues feed matches UiPath KB 799589,
and `uip or machines list` shows the host template
(`BackOfficeRuntime`) running Robot `23.10.4` — below the 23.10-line
fix.

**Why:** The running version (`23.10.4`) is older than the 23.10-line
fix (`23.10.10`). On the affected build the CredProvider log directory
under TEMP is prone to cleanup, leaving the executor unable to find it
at start-up; upgrading the Robot to the fix version resolves it.

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
- Robot log: `Executor start failed: the credential-provider log
  directory C:\Windows\TEMP\UiPath\CredProvider is missing.`
- `uip or machines list`: `BackOfficeRuntime` → `RobotVersion:
  23.10.4` (predates the 23.10.10 fix)
- Known issue: signature correlates to UiPath KB 799589, fixed in
  23.4.11 / 23.10.10 / 24.10.7 (customer-portal known-issues feed)

---

**Immediate fix:**

1. **Upgrade the Robot on the affected host(s) to ≥ 23.10.10.**
   - **Why:** The CredProvider-path failure is a known Robot defect
     (UiPath KB 799589) corrected in 23.4.11 / 23.10.10 / 24.10.7. The
     host runs 23.10.4. Upgrading to the fix version on its release
     line resolves it; no manual folder or permission changes are
     needed or supported.
   - **Where:** Update the Robot build on the `BackOfficeRuntime`
     hosts from `23.10.4` to `23.10.10` (or later).
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
| H1 | Known Robot defect (KB 799589, CredProvider path) on a build ≤ 23.10.8 | High | Confirmed | Yes | Info = CredProvider TEMP path missing; signature correlates to KB 799589 (fix ≥ 23.10.10); machines list shows Robot 23.10.4 | Upgrade Robot to ≥ 23.10.10; rerun |
| H2 | Missing folder / TEMP permissions to fix by hand | Low | Refuted | No | Directory is created by the executor at runtime; manual creation/ACL changes don't fix the build defect | n/a |
| H3 | Credential-store / logon failure | Low | Refuted | No | No logon code, no credential-retrieval error; failure is executor bootstrap matched to a known issue | n/a |

---

Would you like help planning the Robot upgrade to 23.10.10 across the
BackOffice hosts?
