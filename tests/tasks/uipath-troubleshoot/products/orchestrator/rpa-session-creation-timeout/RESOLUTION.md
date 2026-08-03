# Final Resolution

---

**Root Cause:** Every `NightlyReconciler` run enters Running, the Robot begins
creating the Windows session for `UIPATH\SVC_RECON` on `RECON-BOT-01`, and the
create-session step **does not complete within the 120s session-creation
timeout**, so the job faults with `Could not start executor. Creating user
session timed out.` Nothing refused the credential (no logon-failure code) — the
session creation simply took too long. This is a **host-side latency / resource
condition** (slow interactive logon, host CPU/RAM/session saturation, or
network/DC/profile-share latency pushing session creation past the window), not a
credential, no-host, or Robot-version problem. This is the
`Could Not Start Executor — Creating User Session Timed Out` playbook.

**What went wrong:** Job `c0ffee01-1111-4222-8333-444455556666` (NightlyReconciler,
schedule trigger) went Pending → Running at `2026-07-13T02:00:05Z`, then Faulted at
`02:02:05Z` (~120s later) with `Could not start executor. Creating user session
timed out.` The two prior scheduled runs (`c0ffee02-...` at 01:00Z, `c0ffee03-...`
at 00:00Z) faulted identically — a recurring, ~timeout-length fault consistent with
a persistent host-latency margin, not a one-off. The robot-service log states the
create-session call timed out and that **LSA returned no logon rejection** (no
bad-password, locked, or expired status).

**Why (discriminators):**
- **Not a logon failure (`job-faulted-logon-failure` ruled out):** the error is a pure
  timeout — `Creating user session timed out` — with **no** `0x0000052E` / `0x00000775`
  / `0x00000532` / `131092` code, no `Logon failed for user`, no `account is locked`,
  no `RDP connection failed`. The robot log explicitly says LSA returned no rejection.
- **Not a no-host / stuck-Pending case:** `jobs history` shows the job reached
  **Running** (the Robot accepted it and began session creation) before faulting — it
  was not stuck in Pending, and a host was connected.
- **Not a Robot-version defect:** there is no documented Robot version that fixes this
  error; the KB attributes it to host resources / configuration / infrastructure
  latency, and it occurs across current versions. The host's Robot build (`23.4.7`,
  from `machines list`) is a data point, **not the cause** — do not recommend a version
  upgrade.

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
  rejection.`
- `or machines list` (and `--all-fields`): `RECON-BOT-01` `robotVersions[].version =
  23.4.7`, one connected Unattended runtime — checked to identify the host; the version
  is not the cause.
- `or jobs history c0ffee01-...`: Pending (02:00:04.900Z) → Running (02:00:05.100Z) →
  Faulted (02:02:05.400Z).

---

**Immediate fix:**

### Robot host (Root Cause)
1. **Raise the session-creation timeout — set `UIPATH_SESSION_TIMEOUT` on `RECON-BOT-01`.**
   - **Why:** the documented workaround for this error — give session creation more time
     (a higher value in seconds, e.g. `300`–`500`) so a legitimately slow session
     completes instead of being cut off at 120s.
   - **Where:** set the `UIPATH_SESSION_TIMEOUT` system environment variable on the Robot
     host, then restart the Robot service.
   - **Who:** platform / infrastructure admin.
   - **Source:** `products/orchestrator/playbooks/job-faulted-session-timeout.md`.
2. **Reduce host-side session-creation latency.**
   - **Why:** the timeout is a symptom of slow session creation — trim the
     roaming/mandatory profile, lighten/asynchronize GPO and logon-script processing,
     exclude Robot working directories from synchronous AV scanning, and relieve
     CPU/RAM/session pressure (fewer concurrent slots / more capacity). Check DC and
     profile-share latency.
   - **Who:** platform / infrastructure admin.
3. **Interim: re-run the job** — a retry may succeed when the host is momentarily less
   loaded, but it does not fix the underlying latency; the `UIPATH_SESSION_TIMEOUT`
   raise + host remediation is the durable fix.

**Not the fix:** upgrading the Robot version. There is no version-specific fix for this
error; a version change will not resolve a host-latency/resource cause.

---

**Preventive fix:**

1. **Baseline host session-creation latency** and keep `UIPATH_SESSION_TIMEOUT` above the
   worst observed session-creation time on that template. **Who:** platform team.
2. **Alert on repeated `Could not start executor. Creating user session timed out.`** per
   host — it flags a host that is drifting past the timeout margin. **Where:**
   Orchestrator → Alerts → severity Error + keyword filter.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Session creation exceeded the 120s timeout window (host latency / resources / infra), playbook's session-timeout class | High | Confirmed | Yes | Job Info `Creating user session timed out`; ~120s duration; robot log: create-session timed out, LSA returned no rejection; three identical recurring faults | Raise `UIPATH_SESSION_TIMEOUT` + reduce host logon/resource latency; re-run as interim |
| H2 | Logon failure — bad password / locked / RDP (playbook job-faulted-logon-failure) | Low | Refuted | No | No `0x000005..`/`131092` code, no `Logon failed`/`account is locked`/`RDP connection failed`; robot log states LSA returned NO rejection; duration ~120s (timeout), not sub-second | n/a |
| H3 | No host / stuck Pending | Low | Refuted | No | `jobs history` shows Pending→Running→Faulted; a runtime is connected on RECON-BOT-01 | n/a |
| H4 | Known Robot-version defect (upgrade fixes it) | Low | Refuted | No | No documented version fixes this error; KB attributes it to host resources/config/infra latency; it occurs across current versions — the host's `23.4.7` build is not the cause | n/a |

---

Would you like help setting `UIPATH_SESSION_TIMEOUT` on `RECON-BOT-01`, or working
through the host logon-latency / resource checks on that machine?
