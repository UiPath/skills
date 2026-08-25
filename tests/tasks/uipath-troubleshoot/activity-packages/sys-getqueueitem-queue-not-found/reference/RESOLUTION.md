# Final Resolution

---

**Root Cause:** The `GetQueueItem` activity ("Fetch order queue item") in
`OrderQueueFetch.xaml` requests a queue named **`OrderIntakeQueue_EU`**,
and no queue with that name exists in the folder where the job runs.
Orchestrator answered the queue lookup with HTTP 404 / error code 1002
("OrderIntakeQueue_EU does not exist"), the workflow's TryCatch rethrew
it, and the job ended Faulted.

**What went wrong:** The job for process **OrderQueueFetch** (job key
`b7e3d2a4-5f61-48c9-a0d2-4e9b1c7f8a23`) started 2026-07-01T14:31:26.380Z
in the user's personal workspace and faulted ~1.4 seconds later when the
queue lookup failed:
`UiPath.Core.Activities.OrchestratorHttpException: Status code: 404 (Not
Found). Orchestrator response: OrderIntakeQueue_EU does not exist. Error
code: 1002`.

**Why:** The activity resolved its `QueueName` input to the concrete
string `OrderIntakeQueue_EU` (so the name was configured, not null — an
empty name fails client-side with a "may not be null or empty" validation
error, not a 404). The job's folder — the personal workspace — contains
**zero queues**, and the only other folder (Shared) also contains zero,
so the lookup can only return 404.

**Evidence boundary (what current evidence cannot prove):** The project
source is not available, so it cannot be determined whether the
`QueueName` value is hardcoded in the workflow or fed from a variable /
config, nor whether `OrderIntakeQueue_EU` is a wrong name or the intended
queue was deleted / never created. The queue lists reflect today's state,
not the run date — they cannot distinguish "never existed" from "deleted
since". Either way, the runtime 404 proves the queue did not exist **at
run time**.

---

**Evidence:**

### System Activities / workflow (Root Cause)
- Job record `Info`: `UiPath.Core.Activities.OrchestratorHttpException:
  Status code: 404 (Not Found). Orchestrator response:
  OrderIntakeQueue_EU does not exist. Error code: 1002`, at
  `GetQueueItem "Fetch order queue item"` in `OrderQueueFetch.xaml`
- Matching Error log entry at `2026-07-01T14:31:27.143Z`

### Orchestrator (Surface)
- Job state `Faulted`, ran `14:31:26.380Z → 14:31:27.777Z` on 2026-07-01
- Queue list in the personal workspace: **0 queues**
- Queue list in Shared: **0 queues**

### Sibling causes eliminated
- Not `get-asset-not-found`: the faulting activity is `GetQueueItem` on a
  queue, not Get Asset / Get Credential
- Queue name not empty/null: the error shows the resolved name; an empty
  name fails client-side validation, not with a 404
- Not permissions: a permission failure returns a permission/403 error,
  not error code 1002 "does not exist"
- Not network/timeout: the robot received a well-formed Orchestrator
  application response

---

**Immediate fix** (investigation only — no change executed; source:
`classic-activities/playbooks/queue-operation-failed.md § Resolution`,
branches "If the queue name is wrong in source/configuration" / "If the
intended queue is missing or was deleted", presented conditionally per
the "If evidence cannot choose among those three branches" guidance):

1. Determine which queue this process is *supposed* to read, then
   **either** create/recreate that queue in the personal workspace
   (Orchestrator → workspace → Queues → Add queue, named exactly as the
   workflow references it), **or** correct the `QueueName` property of
   the `GetQueueItem` activity "Fetch order queue item" in
   `OrderQueueFetch.xaml` to an existing queue and republish.
   - **Who:** RPA developer / process owner
   - **Prerequisite:** project source (to see whether `QueueName` is
     hardcoded or config-fed) or queue deletion history

---

**Investigation Summary:**

| # | Hypothesis | Status | Key Evidence |
|---|------------|--------|--------------|
| H1 | Queue named by `GetQueueItem` doesn't exist in the job's folder | **Confirmed** | 404 / error code 1002 at run time; 0 queues in the personal workspace and in Shared |
| H2 | Asset lookup failure (get-asset-not-found) | Rejected | Faulting activity is `GetQueueItem` on a queue, not Get Asset |
| H3 | Queue name empty/null | Rejected | Error shows the resolved name; empty name fails client-side, not 404 |
| H4 | Permission denied | Rejected | 404 + code 1002 "does not exist", not a permission error |
| H5 | Network/HTTP/timeout | Rejected | Well-formed Orchestrator application response received |
