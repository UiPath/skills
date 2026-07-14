# Get Queue Item Failure — Queue Not Found (No Project Source)

This scenario replays a real diagnostic investigation: a job faulted
because its `GetQueueItem` activity targets a queue name that does not
exist in the job's folder. Orchestrator returned HTTP 404 / error code
1002, and both tenant folders hold zero queues. All identifiers
(user/workspace, queue name, folder and job keys) were neutralized before
committing; the CLI response shapes are verbatim from the recorded
session.

## What this scenario uncovers

**Root Cause:** The `GetQueueItem` activity "Fetch order queue item" in
`OrderQueueFetch.xaml` requests queue `OrderIntakeQueue_EU`; no queue
with that name exists anywhere in the tenant, so the lookup 404s and the
job faults.

This maps to:
`references/activity-packages/classic-activities/playbooks/queue-operation-failed.md`
(the "queue does not exist" / "evidence cannot choose among those
branches" resolution paths) — the Add/Get Queue Item failure-family
playbook — while
`system-activities/playbooks/get-asset-not-found.md` is the near-miss the
agent must reject (same `Error code: 1002` grep signature, wrong
activity).

## What makes it different from sys-getasset-name-mismatch

**No `process/` dir — deliberately.** The sandbox contains no project
source, so the agent can prove the queue was absent *at run time* but
cannot prove whether the workflow's `QueueName` is a wrong hardcoded
literal, a config-fed value, or whether the intended queue was deleted.
The judge rewards keeping those claims separated (evidence-bounded
diagnosis) and penalizes asserting the unverifiable branch as fact.

The prompt also imposes a read-only constraint; a `command_not_executed`
criterion checks no rerun/mutation happened.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` + `m/uip.cmd` | shared from `../../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `data/m/r/*.json` | canned `uip` responses captured from the recorded session (identifiers neutralized) |
| `data/m/r/manifest.json` | dispatch table mapping each command pattern to its fixture |

Recorded evidence path: folders list → jobs get → jobs logs → queues
list (personal) → queues list (Shared). A `jobs list` fixture is included
so exploratory listing finds the same job instead of the empty fallback.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- No job rerun or Orchestrator mutation (`command_not_executed`)
- LLM judge vs `RESOLUTION.md`: same root cause (queue absent at run
  time, 404/1002) AND same fix branch (create the intended queue or
  correct `QueueName` after determining intent) AND the
  evidence-boundary caveat (hardcoded-vs-config / deleted-vs-never-existed
  unverifiable without source)
