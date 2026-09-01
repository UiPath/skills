# Final Resolution

---

**Root Cause:** Orchestrator cannot **retrieve** the robot credential
because the credential **store backend is unreachable** — the
Orchestrator SQL database that backs the "Orchestrator Database"
credential store is down / not reachable (connection timeout). The
credential is never obtained, so no Windows logon is attempted, and
every robot bound to that store fails to start. This is the
Orchestrator-Database-store branch of the
`credential-store-unavailable` playbook — **not** a wrong or expired
password.

**What went wrong:** Job `aabbccdd-...-aabbcc` (SecurePortalBot,
SecureOps) faulted ~0.7s after start at `2026-06-27T05:00:02Z` with
`ErrorCode: Orchestrator` and `Info` = "Unable to retrieve
credentials from Orchestrator Database credential store. Please
check your connection settings and ensure the Orchestrator Database
service is running." A second, unrelated process (`VendorSyncBot`,
different machine) faulted 40s later with the **same** store error —
store-wide impact.

**Why:** The Robot log is explicit: "Credential store 'Orchestrator
Database' read failed: unable to open a connection to the
Orchestrator SQL database (timeout). No credential was retrieved;
Windows logon was not attempted." Two different processes on
different machines failing identically confirms the shared store
backend, not any one credential, is the problem.

**Ruled out:**
- **Wrong / expired password** — no `Logon failed` / `0x0000052E` /
  locked / expired code; the failure is at credential *retrieval*,
  before any logon.
- **One user's config** — two unrelated processes on different
  machines fail with the same store error simultaneously; the
  common factor is the credential store.

---

**Evidence:**

### Orchestrator
- Failing job `aabbccdd-...-aabbcc` — SecurePortalBot, Faulted
  `2026-06-27T05:00:02.760Z`, `ErrorCode: Orchestrator`
- Job `Info`: `Unable to retrieve credentials from Orchestrator
  Database credential store. Please check your connection settings
  and ensure the Orchestrator Database service is running.`
- Second affected job: `VendorSyncBot` (different process, machine
  MOCK-HOST-2), same store error at `05:00:41`
- Robot log: `Credential store 'Orchestrator Database' read failed:
  unable to open a connection to the Orchestrator SQL database
  (timeout). No credential was retrieved; Windows logon was not
  attempted.`

---

**Immediate fix:**

1. **Restore Orchestrator Database credential-store connectivity.**
   - **Why:** The store read fails because the Orchestrator SQL
     database is unreachable. Until Orchestrator can reach its DB,
     no credential can be retrieved and every bound robot fails to
     start.
   - **Where:** Verify the Orchestrator SQL database service is
     running and reachable from Orchestrator (service up, connection
     string correct, network/firewall path open). This is an
     Orchestrator-infrastructure dependency (see `overview.md` §
     Dependencies).
   - **Who:** Orchestrator / platform / DBA team
   - **Source:**
     `products/orchestrator/playbooks/credential-store-unavailable.md`
     (Orchestrator Database store branch)

2. **Verify with the credential store's Test, then rerun** the
   failed jobs once retrieval succeeds.

---

**If the store is an EXTERNAL vault instead** (CyberArk / Azure Key
Vault / HashiCorp): check the store definition's endpoint /
credentials / network reachability and that the vault service is up;
use Orchestrator's **Test** on the store. (Not the case here — the
error names the Orchestrator Database store.)

---

**Preventive fix:**

1. **Monitoring** — Alert on credential-store retrieval failures and
   on Orchestrator SQL database health; a store outage is store-wide
   and blocks every bound robot at once.
   - **Source:**
     `products/orchestrator/playbooks/credential-store-unavailable.md`
     (Prevention)
2. **Change safety** — After any DB or credential-store migration,
   run the store's Test and a canary job before re-enabling
   triggers.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Orchestrator Database credential store unreachable (store backend down) | High | Confirmed | Yes | Info + log name the Orchestrator Database store read failing on a SQL connection timeout; no logon attempted; two unrelated processes fail store-wide | Restore Orchestrator SQL DB / store connectivity, Test the store, rerun |
| H2 | Wrong / expired robot password | Low | Refuted | No | No logon code; failure is at credential retrieval, before any logon | n/a |
| H3 | One user's misconfiguration | Low | Refuted | No | Two unrelated processes on different machines fail identically — shared store, not one user | n/a |

---

Would you like help confirming the Orchestrator database / credential
store status, or setting up a store-health alert?
