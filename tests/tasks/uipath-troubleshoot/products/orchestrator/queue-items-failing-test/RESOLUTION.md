# Final Resolution

Root Cause: Invalid SpecificContent enqueued by an upstream dispatcher into the ItemsQueue queue (2 items with `Country='ZZ'`, 2 items with empty `Amount`). The performer correctly surfaced these as BusinessExceptions.

What went wrong: An upstream source enqueued a batch of 4 queue items into ItemsQueue (Shared folder) with objectively invalid input data, and the performer process ERN raised BusinessExceptions for each — exactly as designed.

Why: All 4 failed items were created in a ~60 ms burst on 2026-05-14 at 12:05:33Z, all share the same executor job and robot, and their SpecificContent differs from successful items in exactly two ways that map 1:1 to the two BusinessException reasons. The performer job itself completed Successfully (BusinessException is data-validation behavior, not a code fault), and other items in the same queue processed under the same release with valid Country (US/UK) and populated Amount. This is a bad-data-at-enqueue issue, not a performer regression, not a machine issue, and not an asset/configuration drift.

Evidence:

### Orchestrator (Root Cause)
- Queue: ItemsQueue, Folder: Shared
- 4 failed queue items, all BusinessException:
  - InvoiceId INV-006 (key 3b021051…) — `Country='ZZ'`, Amount=75.00 → "Unsupported country: ZZ" (created 12:05:33.287Z)
  - InvoiceId INV-005 (key 8164a35b…) — `Country='ZZ'`, Amount=50.00 → "Unsupported country: ZZ" (created 12:05:33.273Z)
  - InvoiceId INV-004 (key 746e754b…) — Country=UK, `Amount=''` → "Transaction amount is null" (created 12:05:33.253Z)
  - InvoiceId INV-003 (key 54333a46…) — Country=US, `Amount=''` → "Transaction amount is null" (created 12:05:33.227Z)
- Enqueue burst: ~60 ms (12:05:33.227Z–12:05:33.287Z) — consistent with a single dispatcher batch
- All 4 share executor job `af31127b-1083-4304-930d-ad638022a248`, robotId 6979
- Performer job: process ERN (ReleaseVersionId 53412), EntryPoint `Transaction.xaml`, State = **Successful** (12:06:46.917Z → 12:06:50.357Z)
- Successful items in the same queue, same release: valid Country (US/UK) and populated Amount — performer is not over-rejecting valid data
- Reference field is empty on the failed items; no `CreatorJobKey`/`CreatorUserId` exposed by the documented CLI on this tenant; no dispatcher job observed in the Shared folder in the 6 minutes preceding the enqueue burst — enqueue likely originated outside this folder or via API

Immediate fix:

### Orchestrator (Root Cause)
1. Fix the input data at the source — correct or filter the rows feeding the dispatcher so `Country` is a supported value (e.g., US/UK) and `Amount` is non-empty before enqueue.
   - Why: All 4 failures are explained by 2× `Country='ZZ'` and 2× empty `Amount` in SpecificContent; the performer validates these correctly.
   - Where: Upstream dispatcher process or source system that wrote these 4 rows into ItemsQueue (Shared folder) at 2026-05-14 12:05:33Z.
   - Who: Process owner of the dispatcher / upstream system
   - Source: references/products/orchestrator/playbooks/queue-items-failing.md § Resolution

Gap (disclosed): The documented `uip` CLI does not expose `CreatorJobKey`/`CreatorUserId` on this tenant, and the queue item `Reference` field is empty on the 4 failed items. The specific dispatcher job/principal that enqueued the bad batch could not be attributed from CLI-accessible data alone. Identify the upstream system by other means (Orchestrator UI audit log, dispatcher process logs, or API caller identity).

Preventive fix:

1. Orchestrator — Add input validation in the dispatcher (or an enqueue-time pre-check) so rows with unsupported `Country` or empty `Amount` are rejected (or routed to a quarantine queue) before they reach ItemsQueue.
   - Why: The performer already enforces these rules; pushing the same checks upstream avoids producing BusinessExceptions for known-bad shapes.
   - Where: Dispatcher process / source system feeding ItemsQueue
   - Who: Process owner / RPA developer of the dispatcher
   - Source: references/products/orchestrator/playbooks/queue-items-failing.md § Resolution

2. Orchestrator — Populate the queue item `Reference` field at enqueue time with a dispatcher-identifying value (e.g., dispatcher job key or batch ID).
   - Why: The 4 failed items had empty `Reference`, which prevented dispatcher attribution from CLI data.
   - Where: Dispatcher process — Add Queue Item activity, `Reference` argument
   - Who: RPA developer of the dispatcher
   - Source: [Unverified — surfaced from the observed attribution gap]

Investigation summary:

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Upstream dispatcher enqueued items with invalid SpecificContent | high | confirmed | Yes | SpecificContent verified invalid; 60 ms enqueue burst; performer job state = Successful; valid items processed under same release | Fix input data at source |
| H2 | Performer regression from recent update | medium | inferred-eliminated | No | Performer ran Successful; same release also processes valid items; no documented CLI for release history (residual gap) | n/a |
| H3 | Robot/machine-specific failure | low | inferred-eliminated | No | BusinessException reasons are deterministic data-validation messages, not environment-dependent | n/a |
| H4 | Asset/configuration drift | low | inferred-eliminated | No | SpecificContent values are objectively invalid vs successful items | n/a |

---

Do you want me to help draft the dispatcher-side validation (preventive fix), or clean up `.local/investigations/`?
