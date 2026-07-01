# Final Resolution

---

**Root Cause:** The Active Directory password for the `UIPATH\USER1`
service account was rotated on `2026-05-11T07:14:00Z`, but the
credential stored in Orchestrator for this user's unattended Robot
was **not** updated to match. Every job triggered against
`InvoiceIngestor` since the rotation has tried to log on with the
old password and been rejected by Windows with
`0x0000052E` ("user name or password is incorrect"). This is the
"password mismatch / stale Orchestrator credential" branch of the
`Could Not Start Executor — Logon Failed for User` playbook
(branch 3).

**What went wrong:** Job `aabb1122-3344-5566-7788-99aabbccdd00`
(InvoiceIngestor, triggered manually) faulted ~0.7s after start with
`Could not start executor. Logon failed for user UIPATH\USER1.
The user name or password is incorrect. (0x0000052E). Last error:
131092. RDP connection failed.` Identical failures had occurred
every ~10 minutes since `2026-05-12T10:55Z` (three faults in
`or jobs list --state Faulted`). On the same Robot machine
(`MOCK-HOST`), a different unattended user (`UIPATH\USER2`,
process `OrderExporter`) succeeded at `11:20Z` — so the machine,
network, and RDP path are healthy. The fault is scoped to the
`UIPATH\USER1` credential.

**Why:** AD `PasswordLastSet` for `UIPATH\USER1` is
`2026-05-11T07:14:00Z` (yesterday, per the initial report and the
`_meta.ad_password_last_set_observed` annotation on
`or users get`). The Orchestrator-stored credential record shows
`PasswordLastSet: 2026-05-04T09:00:00Z` — seven days older than AD.
Orchestrator is still presenting the pre-rotation password on every
logon attempt. LSA accepts the user (the account exists and is
**not** locked: sub-status `0xC000006A` "wrong password", not
`0xC0000234` "account locked") and rejects only the password,
which is the defining fingerprint of branch 3 (vs. branch 2 where
LSA returns `0x00000775` / account locked, or branch 5 where LSA
returns an interactive-auth-required prompt for MFA).

**Branch 1 ruled out:** `RequiresUserInteraction: false` on the
job; even if it were true, `LoginToConsole: true` on both robots
in the folder.

**Branch 6 ruled out:** A sibling unattended user succeeded on the
same machine at `11:20Z` — RDP slot was available.

**Lockout-loop risk (branch 4):** The Orchestrator credential is
still wrong AND triggers continue to fire every ~10 minutes. Each
failed attempt increments `badPwdCount` on the AD account. If the
domain lockout threshold is, e.g., 10 bad attempts, the account
will lock within ~100 minutes of leaving this unchanged — at
which point the failure flips from branch 3 to branch 4 (chained
3 → 2). The fix below addresses this proactively by disabling
triggers before rotating the stored credential.

---

**Evidence:**

### Orchestrator (Propagation)
- Failing job: `InvoiceIngestor` (key `aabb1122-...`) — Faulted at
  `2026-05-12T11:30:01.118Z` (ran for ~0.71s)
- Failing job type: `Unattended`, `RequiresUserInteraction: false`,
  triggered manually by user `user1` on machine `MOCK-HOST`,
  `LocalSystemAccount: UIPATH\USER1`
- Folder: `UnattendedDemo` (key
  `f1e2d3c4-b5a6-7890-1234-56789abcdef0`)
- Same-user pattern: three Faulted runs with identical Info
  (`aabb1122-...` at 11:30Z, `aabb1100-...` at 11:15Z,
  `aabb1099-...` at 11:05Z, plus `aabb1088-...` at 10:55Z) — every
  attempt since 10:55Z for this user has failed with the same
  signature
- Same-machine cross-check: `OrderExporter` (key `bbcc2233-...`,
  user `UIPATH\USER2`) succeeded on `MOCK-HOST` at `11:20Z` —
  rules out machine/RDP cause
- Failing job's `Info` field carries:
  `Could not start executor. Logon failed for user UIPATH\USER1.
  The user name or password is incorrect. (0x0000052E). Last
  error: 131092. RDP connection failed.`

### Orchestrator (Root Cause)
- Robot Service log at `2026-05-12T11:30:00.988Z`:
  `[Robot] Windows logon attempt for UIPATH\USER1 on MOCK-HOST
  rejected by LSA. NTSTATUS=0xC000006D (STATUS_LOGON_FAILURE).
  Sub-status=0xC000006A (wrong password). Account is NOT locked.`
- `or users get c1d2e3f4-...`:
  `unattendedRobot.PasswordLastSet: 2026-05-04T09:00:00Z` (the
  password Orchestrator is currently sending)
- User report (or `Get-ADUser user1 -Properties PasswordLastSet`
  on a domain controller): AD password was rotated
  `2026-05-11T07:14:00Z` — 7 days *after* the credential
  Orchestrator still holds
- Robot user record shows `LoginToConsole: true` —
  session-creation permission is NOT the problem (rules out
  branch 1)

---

**Immediate fix (apply in this order — do NOT unlock or
re-trigger before step 2):**

### Orchestrator (Root Cause)
1. **Pause triggers for `InvoiceIngestor` (and any other process
   that uses `UIPATH\USER1`).**
   - **Why:** Every failed start increments `badPwdCount` on the
     AD account. Leaving triggers active while you rotate the
     stored credential risks tripping the lockout threshold
     (branch 4).
   - **Where:** Orchestrator UI → Tenant → `UnattendedDemo` →
     Triggers → disable / pause every trigger bound to processes
     running as `UIPATH\USER1`. Also pause manual operators.
   - **Who:** Folder admin / scheduler admin
   - **Source:**
     `products/orchestrator/playbooks/job-faulted-logon-failure.md`
     (branch 4 prevention)

2. **Update the password stored in Orchestrator for the
   `UIPATH\USER1` robot account.**
   - **Why:** The Windows logon failure is caused by Orchestrator
     sending the pre-rotation password. Replacing it with the
     current AD password lets the next logon succeed.
   - **Where:** Orchestrator UI → Tenant → Users →
     `user1` (key `c1d2e3f4-a5b6-c7d8-e9f0-1a2b3c4d5e6f`) →
     Robot password. If the credential is in a Credential Store
     instead, edit the asset that holds it.
   - **Who:** Tenant admin / robot owner
   - **Source:**
     `products/orchestrator/playbooks/job-faulted-logon-failure.md`
     (branch 3)

3. **Verify the new credential manually before re-arming
   triggers.**
   - **Why:** A second mistake (e.g., typo, wrong AD account)
     would just re-arm the lockout risk. Logging on once
     manually with the new password proves it is correct
     against AD.
   - **Where:** RDP to `MOCK-HOST` once as `UIPATH\USER1` using
     the new password (or `runas /user:UIPATH\USER1 cmd` from
     any domain-joined host).
   - **Who:** Tenant admin
   - **Source:**
     `products/orchestrator/playbooks/job-faulted-logon-failure.md`
     (branch 3 verification)

4. **(Only if AD lockout already tripped between rotation and
   fix.)** Have a domain admin unlock the account.
   - **Why:** If `badPwdCount` reached threshold before step 1
     pauses the triggers, the account will be locked even after
     the Orchestrator credential is corrected. Unlock so the
     next attempt is not pre-empted.
   - **Where:** AD Users & Computers → user → Account → "Unlock
     account", or `Unlock-ADAccount -Identity user1` on a
     domain controller.
   - **Who:** Domain admin
   - **Source:**
     `products/orchestrator/playbooks/job-faulted-logon-failure.md`
     (branch 2 / 4)

5. **Re-enable triggers.**
   - **Where:** Orchestrator UI → Triggers → re-enable everything
     paused in step 1.
   - **Who:** Folder admin / scheduler admin

---

**Preventive fix:**

1. **Process** — Rotate the AD password for robot service
   accounts and the Orchestrator-stored credential in lockstep
   (one runbook, not two).
   - **Why:** Decoupling them is the root cause of every branch-3
     and branch-4 incident. Treat the two writes as a single
     transactional change.
   - **Where:** Internal runbook / change-management ticket
     template; rotation script that updates AD then immediately
     calls the Orchestrator API or UI to update the user record.
   - **Who:** Platform team / identity team
   - **Source:**
     `products/orchestrator/playbooks/job-faulted-logon-failure.md`
     (Prevention)

2. **Orchestrator** — Subscribe to alerts for repeated
   `Could not start executor / Logon failed for user` errors
   on each unattended user.
   - **Why:** The three-faults-in-25-minutes pattern is the
     pre-lockout fingerprint. Alerting on the first two surfaces
     the issue while it is still branch 3 (recoverable in one
     change), not branch 4 (recoverable only after pausing,
     fixing, and unlocking).
   - **Where:** Orchestrator UI → Alerts → severity "Error" +
     keyword filter on `Logon failed` or `0x0000052E`.
   - **Who:** Admin or platform team

3. **AD / Identity** — Where compliance allows, move robot
   service accounts to non-expiring passwords or a Group
   Managed Service Account (gMSA) pattern. If that is forbidden,
   ensure these accounts are tagged so identity team's rotation
   process automatically queues the Orchestrator-side update.
   - **Why:** Removes the human-in-the-loop step that caused
     this incident.
   - **Where:** AD policy + identity team's rotation tooling.
   - **Who:** Identity team

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Stale Orchestrator credential after AD password rotation (playbook branch 3) | High | Confirmed | Yes | Job Info: `Logon failed ... (0x0000052E)`; Robot log: sub-status `0xC000006A` (wrong password), account NOT locked; AD `PasswordLastSet=2026-05-11`, Orchestrator `PasswordLastSet=2026-05-04` (stale by 7 days); same-machine sibling user `USER2` succeeds, same-user pattern persists across every recent attempt | Pause triggers → update Orchestrator credential → verify by manual logon → re-enable |
| H2 | Account locked in AD (playbook branch 2) | Low | Refuted | No | Robot log explicitly states `Account is NOT locked`; LSA sub-status is `0xC000006A` (wrong password), not `0xC0000234` (locked); Windows error is `0x0000052E`, not `0x00000775` | n/a |
| H3 | Session-configuration mismatch (playbook branch 1) | Low | Refuted | No | `RequiresUserInteraction: false` on the job; even if it were true, `LoginToConsole: true` on the robot user — Robot is permitted to create its own console session | n/a |
| H4 | RDP slot conflict (playbook branch 6) | Low | Refuted | No | `OrderExporter` ran on `MOCK-HOST` as `UIPATH\USER2` at `11:20Z` and Succeeded — no slot contention | n/a |
| H5 | Lockout-loop chained 3 → 2 (playbook branch 4) | Medium | Risk (not yet realised) | Watch | Account currently NOT locked, but each failed attempt increments `badPwdCount`; triggers fire every ~10 minutes; without step 1 (pause triggers) the next ~7 attempts will likely trip lockout | Apply branch 4 fix sequence proactively — pause triggers first |

---

Would you like help applying the fix — disabling triggers,
updating the stored credential, or verifying the new password
against AD? I can also clean up the `.investigation/` folder if
you no longer need it.
