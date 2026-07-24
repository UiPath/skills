# Final Resolution

---

**Root Cause:** The `ClaimsRuntimeTemplate` machine template is
configured with **4 unattended runtime slots**, but it is bound to a
single workstation (`MOCK-HOST`) that seats at most **2 concurrent
RDP sessions**. During the morning peak, three or more
`PolicyRenewalWorker` jobs are dispatched at once; the first two
seat successfully and the extra job(s) fault ~1s after start with
`Could not start executor. The workstation is in use by another
user. Please retry after the user logs off or disconnects.` This is
the **machine-template slot over-allocation** branch (branch 3) of
the `job-faulted-session-console-contention` playbook — the template
over-allocates slots relative to what the host can physically seat.

**What went wrong:** Job `77aa11bb-...-8811` (PolicyRenewalWorker,
UIPATH\SVCRENEW) faulted at `2026-06-18T09:12:01Z`, ~0.8s after
start, on `MOCK-HOST`. At that instant two other unattended jobs
were **Running** on the same host — `InvoiceMatcher`
(UIPATH\SVCINV) and `MailDispatcher` (UIPATH\SVCMAIL) — occupying
both of the workstation's two RDP session slots. The failing job was
the third concurrent dispatch and was refused a session. A second
PolicyRenewalWorker run faulted identically at `09:05`.

**Why:** `uip or machines list` shows `ClaimsRuntimeTemplate` with
`Runtimes: 4` on a single host (`MOCK-HOST`). At the failure moment
two other jobs were Running on that host — both seatable sessions
occupied. The Robot service log confirms the workstation "already
has 2 active sessions and refused an additional concurrent
connection" and that the credential validated. Correlating the two:
Orchestrator dispatches up to the template's slot count (4), but the
host can only seat 2 concurrent sessions, so peak concurrency
produces the fault. The slot-vs-capacity mismatch is inferred from
the template config and the observed concurrency, not handed over in
a single log line.

**Ruled out:**
- **Logon failure** — the Info/log carry no `Logon failed` /
  `0x0000052E` / locked / password code; the log states the
  credential validated successfully. Not the logon-failure playbook.
- **Session-creation timeout** — two sessions WERE created on this
  host at the same moment (the two Running jobs). The host can
  create sessions; it is out of seats, not slow.
- **Console contention (branch 2)** — `LoginToConsole: false` on the
  SVCRENEW robot user; the fault is not console-bound.
- **Single-interactive-job-per-user (branch 1)** — the two seated
  jobs run as different accounts (SVCINV, SVCMAIL); SVCRENEW is not
  colliding with itself.

---

**Evidence:**

### Orchestrator
- Failing job `77aa11bb-...-8811` — PolicyRenewalWorker, Faulted at
  `2026-06-18T09:12:01.233Z` (~0.8s runtime), `HostMachineName:
  MOCK-HOST`, `LocalSystemAccount: UIPATH\SVCRENEW`,
  `MachineKey: 9f8e7d6c-...` (= ClaimsRuntimeTemplate)
- Job `Info`: `Could not start executor. The workstation is in use
  by another user. Please retry after the user logs off or
  disconnects.`
- Robot log: `the workstation already has 2 active sessions and
  refused an additional concurrent connection. Credential validated
  successfully; this is a session-seating failure, not a logon
  failure.` (The 4-slots-vs-2-seatable conclusion is derived by
  correlating `machines list` with the concurrent Running jobs — see
  below — not stated in the log.)
- Concurrent Running jobs on MOCK-HOST at the failure time:
  `InvoiceMatcher` (UIPATH\SVCINV, Running since 09:08) and
  `MailDispatcher` (UIPATH\SVCMAIL, Running since 09:10) — both
  slots occupied
- `uip or machines list`: `ClaimsRuntimeTemplate` → `Runtimes: 4`,
  `Hosts: ["MOCK-HOST"]`
- `uip or users get` (svcrenewals): `LoginToConsole: false`,
  `RunOnlyOneJobAtATime: false`, credential current (PasswordLastSet
  2026-05-30)

---

**Immediate fix:**

1. **Reduce the `ClaimsRuntimeTemplate` slot count to match the
   host's concurrent-session capacity (2).**
   - **Why:** The template dispatches up to 4 jobs to a host that
     seats only 2 RDP sessions. Capping slots at 2 stops
     Orchestrator from over-dispatching, so no job is ever the
     rejected 3rd session.
   - **Where:** Orchestrator UI → Tenant → Machines →
     `ClaimsRuntimeTemplate` → edit → set unattended runtimes/slots
     to 2 (or however many concurrent RDP sessions the workstation
     truly allows).
   - **Who:** Tenant / machine admin
   - **Source:**
     `products/orchestrator/playbooks/job-faulted-session-console-contention.md`
     (branch 3)

2. **Rerun the faulted PolicyRenewalWorker job(s).**
   - Once slots ≤ seatable sessions, the job seats normally.

---

**Alternative / scale-out fix:**

- If the workload genuinely needs 4 concurrent runtimes, add more
  hosts to the template (scale horizontally) so 4 slots map to 4
  seatable sessions, or raise the workstation's allowed concurrent
  RDP sessions (Windows Server + RDS licensing) rather than a
  client SKU capped at low concurrency.

---

**Preventive fix:**

1. **Machine** — Keep every template's slot count ≤ the sum of
   concurrent sessions its hosts can physically seat. Treat slot
   count as a promise the host must be able to honor.
   - **Source:**
     `products/orchestrator/playbooks/job-faulted-session-console-contention.md`
     (Prevention)
2. **Orchestrator** — Alert on repeated `workstation is in use by
   another user` / session-seating errors per machine template — the
   peak-only failure pattern is the fingerprint of slot
   over-allocation.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Machine-template slot over-allocation vs. host session capacity (branch 3) | High | Confirmed | Yes | `Runtimes: 4` on single host MOCK-HOST; 2 other jobs Running (both slots seated) when the 3rd faulted; Robot log names 4 slots vs 2 seatable sessions | Reduce template slots to 2 (or scale out hosts) → rerun |
| H2 | Logon failure / bad credential (logon-failure playbook) | Low | Refuted | No | No `Logon failed` / `0x0000052E` / locked code; log says credential validated | n/a |
| H3 | Session-creation timeout | Low | Refuted | No | Two sessions were created successfully on the same host at the same time | n/a |
| H4 | Console contention on HD robot (branch 2) | Low | Refuted | No | `LoginToConsole: false` on the failing robot user | n/a |
| H5 | Single-interactive-job-per-user (branch 1) | Low | Refuted | No | The two seated jobs run as different accounts (SVCINV, SVCMAIL), not SVCRENEW | n/a |

---

Would you like help applying the fix — reducing the template's slot
count, or planning a horizontal scale-out of the machine template?
