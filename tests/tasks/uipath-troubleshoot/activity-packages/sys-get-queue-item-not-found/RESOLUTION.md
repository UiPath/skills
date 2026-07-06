# Final Resolution

---

**Root Cause:** The `Get Queue Item` activity in `Main.xaml` references
the queue `OrdersToProcess`, which does not exist in the `Finance` folder
where the job runs. When the activity called Orchestrator, it returned
HTTP 404 (Not Found) with `OrdersToProcess does not exist. Error code:
1002`, raising a `UiPath.Core.Activities.OrchestratorHttpException` and
faulting the job. Despite the generic "HTTP Error / Check HTTP
connectivity" text in the job header, this is NOT a connectivity problem —
the request reached Orchestrator, and the response body names the missing
queue.

**What went wrong:** The `OrderProcessor` job (started
2026-06-24T12:45:10.300Z) faulted ~1.4 seconds after launch when
`Get Queue Item` tried to fetch a transaction from queue
`OrdersToProcess`.

**Why:** A 404 with error code 1002 is Orchestrator's "resource does not
exist" response — here, the named queue. Because the request succeeded at
the transport layer and returned a structured 404 naming the queue, the
cause is a missing/misnamed queue or a folder mismatch (the queue is
defined in a different folder than the one the job runs in), not
network/HTTP connectivity.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: OrderProcessor — Faulted at 2026-06-24T12:45:11.700Z (ran ~1.4 seconds)
- Folder: Finance (key `4b1c7e90-2a3d-4f5e-9c8b-1a2b3c4d5e6f`)
- Machine: MOCK-HOST
- ErrorCode: `System.Utilities.Sys.HttpError`
- Final error: `Status code: 404 (Not Found). Orchestrator response: OrdersToProcess does not exist. Error code: 1002` → `Main.xaml` → `GetQueueItem "Get Queue Item"` → `Sequence "Main Sequence"` → `OrderProcessor "OrderProcessor"`

### System Activities (Root Cause)
- Activity: `GetQueueItem` (DisplayName: "Get Queue Item")
- QueueName: `OrdersToProcess`
- Exception: `UiPath.Core.Activities.OrchestratorHttpException: Status code: 404 (Not Found). Orchestrator response: OrdersToProcess does not exist. Error code: 1002`
- The "HTTP Error / Check HTTP connectivity" header is the activity's generic banner; the response body is the actual evidence — the queue is missing in this folder.

---

**Immediate fix:**

### System Activities (Root Cause)
1. Create the queue `OrdersToProcess` in the `Finance` folder (or run the job in the folder where the queue is defined), and confirm the `QueueName` matches exactly.
   - **Why:** The 404 / error code 1002 is a missing-resource response for the named queue. Queues are folder-scoped, so a queue defined in another folder is invisible to a job running in `Finance`.
   - **Where:** Orchestrator UI → `Finance` folder → Queues → create `OrdersToProcess` (exact name/case). Alternatively, point the process at the folder that already owns the queue. In `Main.xaml`, verify `<ui:GetQueueItem ... QueueName="OrdersToProcess" ...>` matches the queue's real name.
   - **Who:** RPA developer / Orchestrator admin
   - **Source:** `system-activities/playbooks/queue-transaction-activity-failed.md` (404 / "does not exist. Error code: 1002" branch)

---

**Preventive fix:**

1. **Deployment** — Make queue provisioning part of the environment setup for the process (queue exists in the target folder before the process is scheduled), or bind `QueueName` to a folder-level asset/constant to prevent name drift.
   - **Why:** A missing queue in the target folder fails every run; catching it at deploy time avoids a runtime fault.
   - **Who:** RPA developer / platform team

2. **Orchestrator** — Add a faulted-job alert for the `Finance` folder so a missing-queue failure surfaces immediately.
   - **Why:** The 404 would be caught on the first run instead of recurring silently.
   - **Who:** Admin / platform team

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Queue `OrdersToProcess` does not exist in the Finance folder | High | Confirmed | Yes | HTTP 404 / code 1002, `OrchestratorHttpException`, body names the queue | Create the queue in Finance (or run in the queue's folder); match QueueName |
| H2 | HTTP / network connectivity problem | Low | Rejected | No | Request reached Orchestrator and returned a structured 404 naming the queue | — |

---

Would you like help creating the `OrdersToProcess` queue in the Finance
folder or repointing the process, and verifying the `QueueName` in
`Main.xaml`? I can also clean up the `.local/investigations/` folder if
you no longer need it.
