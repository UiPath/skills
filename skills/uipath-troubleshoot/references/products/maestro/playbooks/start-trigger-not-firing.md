---
confidence: high
---

# Maestro Process Not Starting from an Event Trigger

## Context

What this looks like:
- A Maestro process that normally starts on its own has produced no new instances
- The user reports a window ("nothing in the last 6 hours") and usually asserts the
  source events did happen — "I sent emails that should match"
- No incident, no faulted instance, nothing to open

**Applies only when the process is started by an Integration Service event trigger.**
A Maestro process can also start manually, from an API call, from a time trigger, or
from a parent process; none of those produce trigger traces. Confirm at Step 1 — see
the applicability gate in
[investigation_guide.md](../../integration-service/investigation_guide.md#applicability-gate--run-this-first).

For instances that started and then stalled, use
[wait-for-event-stuck.md](./wait-for-event-stuck.md). For instances that started and
faulted, use [bpmn-job-stuck.md](./bpmn-job-stuck.md).

**Treat "the events would have matched" as the hypothesis under test, not a given.**
It is the single most common thing the traces disprove, and accepting it sends the
investigation to the connection and the robot when the filter was the cause.

What can cause it:
- **CA001** — the start trigger never polled (connection, disabled trigger, permission)
- **CA002** — it polled and the connector returned nothing: wrong object or parameters (for mail, the watched folder), or the events landed outside the poll window
- **CA003** — events arrived and the trigger's filter rejected them
- **CA004** — events matched but the instance was never created: binding, license, or folder problem
- **CA005** — the process is started by something other than an event trigger, and the premise is wrong

What to look for:
- The process's own start trigger, which is an Orchestrator event trigger in the process's folder
- Whether any trace exists in the user's window
- `EventsFetched` vs `EventsMatched`, then the filter expression in the spans

## Investigation

1. **Confirm an event trigger starts this process (CA005 gate).** Read one recent
   instance, or the process's start element.

   ```bash
   uip maestro bpmn instances list --process-key <process-key> --folder-key <folder-key> --limit 1 --output json
   ```

   `Source: "IntegrationTrigger"` confirms it. `Manual` or anything else ends this
   playbook — say which and route to the Maestro deployment or job playbooks. If the
   process has never produced an instance, read the start element instead and look for
   `ElementExtensionType: "Intsvc.EventTrigger"`:

   ```bash
   uip maestro bpmn instances element-executions <instance-id> --folder-key <folder-key> --output json
   ```

2. **Find the start trigger.** It is an Orchestrator event trigger in the process's
   folder, bound to the process's release.

   ```bash
   uip or triggers list --type event --folder-path "<folder>" --output json
   ```

   Match `ReleaseName` to the process. More than one trigger can start one process —
   list them for the user and confirm which one the missing events should have hit
   rather than assuming the first.

   Read `Key` from the matching row — step 3 takes the key, not the name. Keep the
   `Name` too: it is what the user will recognise when you report back.

   On a CLI predating cli#5902 the command answers `Invalid trigger type: 'event'`,
   and nothing else lists event triggers — ask for the key from Orchestrator → folder
   → **Triggers** → **Event triggers**.

3. **Read the traces for the reported window.** `--source maestro` is what lets this
   authorize without a folder-scoped grant.

   ```bash
   uip is trigger-traces list --trigger-key <trigger-key> --folder-path "<folder>" \
     --source maestro --from 6h --output json
   ```

4. **Branch** using the table in
   [investigation_guide.md § Step 2](../../integration-service/investigation_guide.md#step-2--read-the-row-before-gathering-anything-else).
   For this playbook the two informative outcomes are:

   - **`EventsFetched: 0` across every trace** — the connector never saw the events.
     The trigger is healthy; the problem is upstream. For mail triggers this is almost
     always the watched folder, or mail that arrived before the trigger's last poll.
   - **`EventsFetched > 0`, `EventsMatched: 0`** — the events arrived and the filter
     rejected them. This is the answer to "but I sent matching emails."

5. **Open the trace that should have matched.**

   ```bash
   uip traces spans get <trace-id> --output json
   ```

   The data span holds what the connector received — `response[]` on a polling trigger,
   `Data.payload` on a webhook one — so confirm the user's event is in it. The filter
   span holds the expression and the matches: `result.filter` / `result.matches`
   (polling) or `DataFilters.input.filter` / `DataFilters.output.matched` (webhook). See
   [investigation_guide.md § Step 3](../../integration-service/investigation_guide.md#step-3--spans-carry-the-filter-and-the-payload).

   For a mail trigger the polling shape is the useful one: `result.nonMatches` lists the
   messages that were fetched and rejected, which answers "but I sent it" directly.

6. **Matched but no instance (CA004).** Correlate the trace first; counting
   instances in a window cannot show that a specific event started a specific
   instance.

   ```bash
   uip is correlated-jobs list --trace-id <trace-id> --trigger-key <trigger-key> \\
     --folder-path "<folder>" --output json
   ```

   Compare the row count against the trace's `EventsMatched`, and give a trace
   younger than 60 seconds the benefit of the doubt — dispatch is asynchronous.

   For a Maestro start trigger `JobId` is the **process instance external id**,
   not an Orchestrator job id — resolve it with
   `uip maestro bpmn instances list --process-key <process-key> --folder-key <folder-key>`
   and match on `ExternalId`. See
   [investigation_guide.md § Step 4](../../integration-service/investigation_guide.md#step-4--what-the-trace-actually-started).

## Resolution

- **CA001** — re-authenticate the connection (`uip is connections edit <id>`), enable the trigger in Orchestrator, or grant the robot account "Triggers" on the folder
- **CA002** — correct the watched object or parameters. Events older than the trigger's last poll date are never picked up; say so plainly rather than suggesting a retry
- **CA003** — the filter is doing what it says. Present the expression beside the rejected payload and let the user decide which to change
- **CA004** — fix the release binding, licensing or folder for the process the trigger starts
- **CA005** — the process is not event-started; this playbook does not apply

A deploy via `uip solution deploy run` creates triggers **disabled**. For a process that
has never fired since deployment, check the enabled state before anything else.
