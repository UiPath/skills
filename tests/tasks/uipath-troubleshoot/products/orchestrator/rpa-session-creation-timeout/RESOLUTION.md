# Final Resolution

---

**Root Cause:** The unattended Robot installed on `RECON-BOT-01` is version
**23.4.7**, which carries a known session-creation-timeout defect fixed in the
Robot **23.10** release. On the affected versions the Robot's create-Windows-session
step can hang and time out even on a healthy host. Every `NightlyReconciler` run
enters Running, the Robot begins creating the Windows session for `UIPATH\SVC_RECON`,
the create-session call does not complete within the 120s session-creation timeout,
and the job faults with `Could not start executor. Creating user session timed out.`
This is the **known Robot defect (< 23.10)** branch (cause 1) of the
`Could Not Start Executor — Creating User Session Timed Out` playbook.

**What went wrong:** Job `c0ffee01-1111-4222-8333-444455556666` (NightlyReconciler,
schedule trigger) went Pending → Running at `2026-07-13T02:00:05Z`, then Faulted at
`02:02:05Z` (~120s later) with `Could not start executor. Creating user session
timed out.` The two prior scheduled runs (`c0ffee02-...` at 01:00Z, `c0ffee03-...`
at 00:00Z) faulted identically. The robot-service log states the create-session call
timed out and that **LSA returned no logon rejection** (no bad-password, locked, or
expired status). `machines list` shows `RECON-BOT-01` has one connected Robot at
`robotVersions[].version = 23.4.7` — earlier than 23.10.

**Why (discriminators):**
- **Not a logon failure (`job-faulted-logon-failure` ruled out):** the error is a pure
  timeout — `Creating user session timed out` — with **no** `0x0000052E` / `0x00000775`
  / `0x00000532` / `131092` code, no `Logon failed for user`, no `account is locked`,
  no `RDP connection failed`. The robot log explicitly says LSA returned no rejection.
- **Not a no-host / stuck-Pending case:** `jobs history` shows the job reached
  **Running** (the Robot accepted it and began session creation) before faulting — it
  was not stuck in Pending, and a host was connected (`robotVersions` populated).
- **Not host resource exhaustion / slow logon (causes 2 & 3):** the executing Robot is
  < 23.10, which is the specific documented defect; there is no evidence of host
  saturation. Version is the discriminating signal (a version ≥ 23.10 would push toward
  causes 2/3).

---

**Evidence:**

### Orchestrator (Symptom)
- Failing job: `NightlyReconciler` (key `c0ffee01-...`) — Pending→Running at
  `2026-07-13T02:00:05.100Z`, Faulted at `02:02:05.400Z` (~120s).
- Type `Unattended`, `RequiresUserInteraction: false`, schedule-triggered, host
  `RECON-BOT-01`, `LocalSystemAccount: UIPATH\SVC_RECON`.
- Folder: `UnattendedOps` (key `a1b2c3d4-e5f6-4789-abcd-000000000001`).
- Same-signature pattern: three Faulted runs (`c0ffee01-...` 02:00Z, `c0ffee02-...`
  01:00Z, `c0ffee03-...` 00:00Z), all `Could not start executor. Creating user session
  timed out.`
- Job `Info`: `Could not start executor. Creating user session timed out.`

### Orchestrator (Root Cause)
- Robot-service log at `2026-07-13T02:02:05.210Z`: `[Robot] Creating a Windows session
  for UIPATH\SVC_RECON on RECON-BOT-01 did not complete within the 120s
  session-creation timeout. The create-session call timed out; LSA returned NO logon
  rejection ... Robot version 23.4.7.`
- `or machines list` (and `--all-fields`): `RECON-BOT-01`
  `robotVersions[].version = 23.4.7`, one connected Unattended runtime — earlier than
  the 23.10 fix.
- `or jobs history c0ffee01-...`: Pending (02:00:04.900Z) → Running (02:00:05.100Z) →
  Faulted (02:02:05.400Z).

---

**Immediate fix:**

### Orchestrator / Robot (Root Cause)
1. **Upgrade the Robot on `RECON-BOT-01` to version 23.10 or later** (the release that
   fixes the session-creation-timeout defect).
   - **Why:** version 23.4.7 carries the defect; the fix ships in 23.10.
   - **Where:** update the UiPath Robot on the host (installer / deployment tooling);
     confirm the new version reports in `machines list` `robotVersions`.
   - **Who:** platform / infrastructure admin.
   - **Source:** `products/orchestrator/playbooks/job-faulted-session-timeout.md`
     (cause 1). Confirm the exact fixed version against the Customer Portal / KB
     (`uip docsai ask ... --source technical_solution_articles`) before committing the
     target build.
2. **Interim mitigation: re-run the job.**
   - **Why:** the timeout is intermittent on the affected versions, so a retry usually
     succeeds while the upgrade is scheduled.
   - **Where:** Orchestrator UI → Jobs → re-run `NightlyReconciler`, or wait for the
     next scheduled trigger.
   - **Who:** folder / operations admin.

---

**Preventive fix:**

1. **Keep unattended Robots on a supported/patched version** and standardize the Robot
   version across the machine template, so a single stale host cannot reintroduce the
   defect. **Who:** platform team.
2. **Alert on repeated `Could not start executor. Creating user session timed out.`**
   per host — it is the fingerprint of an unpatched Robot. **Where:** Orchestrator →
   Alerts → severity Error + keyword filter.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Known Robot session-creation-timeout defect on version < 23.10 (playbook cause 1) | High | Confirmed | Yes | `machines list` `robotVersions.version=23.4.7` on RECON-BOT-01; job Info `Creating user session timed out`; robot log: create-session timed out at 120s, LSA returned no rejection; three identical faults | Upgrade Robot to ≥ 23.10; re-run as interim |
| H2 | Logon failure — bad password / locked / RDP (playbook job-faulted-logon-failure) | Low | Refuted | No | No `0x000005..`/`131092` code, no `Logon failed`/`account is locked`/`RDP connection failed`; robot log states LSA returned NO rejection; duration ~120s (timeout), not sub-second | n/a |
| H3 | No host / stuck Pending | Low | Refuted | No | `jobs history` shows Pending→Running→Faulted; a runtime is connected on RECON-BOT-01 (`robotVersions` populated) | n/a |
| H4 | Host resource exhaustion / slow interactive logon (causes 2 & 3) | Low | Refuted | No | Executing Robot is 23.4.7 (< 23.10), the specific documented defect; no host-saturation evidence; a version ≥ 23.10 would be needed to move toward these | n/a |

---

Would you like help scheduling the Robot upgrade on `RECON-BOT-01`, or re-running
`NightlyReconciler` as an interim measure? I can also clean up the
`.local/investigations/` folder if you no longer need it.
