# Final Resolution

---

**Root Cause:** The tenant's **Robot Unit pool is exhausted** — 25
of 25 units are in use and 0 are available. Serverless jobs
(`RuntimeType: Serverless`) must reserve a Robot Unit from the
tenant pool to start; with the pool empty, every serverless start is
refused at the licensing layer before any Robot session is created.
The failing `LedgerSyncService` job faults immediately with
`Automation cannot be started. Your tenant's assigned Robot Units
have been exceeded. Allocate more Robot Units to your tenant to
continue.` This is the **tenant Robot Units exhausted** branch
(branch 3) of the `serverless-cannot-start-licensing` playbook.

**What went wrong:** Job `99cc33dd-...-0011` (LedgerSyncService,
user `alice`) faulted at `2026-06-20T02:00:03Z`, ~0.8s after start,
with `ErrorCode: License` and `RuntimeType: Serverless`. A second
serverless job — `ExpenseImporter` (user `bob`) — faulted three
minutes later with the **same** tenant-Robot-Units message. Two
different processes owned by two different users failing identically
is the tenant-wide fingerprint: the shared pool is the constraint,
not any one user.

**Why:** `uip or licenses info` shows tenant `RobotUnits`:
`Allocated 25, Used 25, Available 0`. The serverless log is
explicit: "Robot Unit reservation denied for tenant: requested 1
unit, tenant pool has 0 of 25 available (25 in use). Reservation is
tenant-scoped; per-user quota is not the limiting factor." The
reporting user's Personal Automation monthly quota has plenty
remaining (166 of 200) and per-user Robot Unit allocation is unused
— so this is neither a personal-quota nor a per-user-RU problem.

**Ruled out:**
- **Personal Automation monthly quota (branch 1)** — the user's
  monthly quota is 166/200 remaining; not exhausted. Waiting for a
  monthly reset would not help.
- **Per-user Robot Units (branch 2)** — `alice` has 5 units
  allocated, 0 used; her per-user allocation is not the blocker.
- **Time-limit cancellation (branch 4)** — the jobs faulted ~0.8s
  after start; they never ran, so no execution-time ceiling was
  hit.
- **Could not obtain user token / designer cap** — not the error
  text; not intermittent; scoped to the tenant pool.

---

**Evidence:**

### Orchestrator
- Failing job `99cc33dd-...-0011` — LedgerSyncService,
  `RuntimeType: Serverless`, Faulted at `2026-06-20T02:00:03.900Z`
  (~0.8s), `ErrorCode: License`, folder LedgerOps
- Job `Info`: `Automation cannot be started. Your tenant's assigned
  Robot Units have been exceeded. Allocate more Robot Units to your
  tenant to continue.`
- Second serverless fault: `ExpenseImporter` (user `bob`), same
  message, `02:03Z` — tenant-wide, not one user
- Serverless log: `Robot Unit reservation denied for tenant:
  requested 1 unit, tenant pool has 0 of 25 available (25 in use)`
- `uip or licenses info`: tenant `RobotUnits` = Allocated 25 / Used
  25 / **Available 0**; user `alice` Personal Automation
  166/200 remaining; per-user RU 0/5 used

---

**Immediate fix:**

1. **Allocate more Robot Units to the tenant (or free units in
   use).**
   - **Why:** Serverless starts reserve a unit from the tenant pool.
     With 0 available, every serverless job is refused. Adding
     capacity (or releasing units held by long-running / stuck jobs)
     lets reservations succeed.
   - **Where:** Automation Cloud → Admin → Licenses → allocate Robot
     Units to the `AcmeProd` tenant. To free units immediately,
     stop non-essential serverless runs currently holding the 25
     units.
   - **Who:** Organization / tenant admin
   - **Source:**
     `products/orchestrator/playbooks/serverless-cannot-start-licensing.md`
     (branch 3)

2. **Rerun the faulted serverless jobs** once the tenant pool shows
   available units.

---

**Preventive fix:**

1. **Orchestrator / Licensing** — Monitor tenant Robot Unit
   utilization and alert before the pool is exhausted (e.g. at 80%).
   Tenant-pool exhaustion is a tenant-wide outage — every serverless
   job stops, not just one user's.
   - **Source:**
     `products/orchestrator/playbooks/serverless-cannot-start-licensing.md`
     (Prevention)
2. **Capacity planning** — Size the tenant Robot Unit pool for peak
   concurrency (the overnight batch window here), or stagger nightly
   schedules so concurrent reservations stay under the pool size.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Tenant Robot Unit pool exhausted (branch 3) | High | Confirmed | Yes | Info names the tenant; `licenses info` tenant RU 0 of 25 available; two users' serverless jobs fail identically; log states tenant-scoped reservation denied | Allocate more Robot Units to the tenant (or free units) → rerun |
| H2 | Personal Automation monthly quota exhausted (branch 1) | Low | Refuted | No | User quota 166/200 remaining; message names tenant, not user | n/a |
| H3 | Per-user Robot Units exceeded (branch 2) | Low | Refuted | No | User RU 0/5 used; not the limiting factor | n/a |
| H4 | Time-limit cancellation (branch 4) | Low | Refuted | No | Jobs faulted ~0.8s after start; never executed | n/a |

---

Would you like help applying the fix — allocating Robot Units to the
tenant, identifying which runs are holding the 25 in-use units, or
setting up a utilization alert?
