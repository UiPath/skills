---
confidence: high
---

# Trigger Not Firing

## Context

What this looks like:
- An Integration Service event trigger is configured but events don't start jobs or Maestro instances
- External events occur and no corresponding execution is created
- The trigger looks correct in the UI
- The user names a trigger ("my Salesforce trigger"), a process, or neither — only that nothing ran

**Applies to Integration Service event triggers only.** Time, queue, HTTP and API
triggers record no traces. Confirm `ApiTriggerType` is `IntegrationTrigger` at Step 1
and stop if it is not — see the applicability gate in
[investigation_guide.md](../investigation_guide.md#applicability-gate--run-this-first).

For a Maestro process that never started, use
[start-trigger-not-firing.md](../../maestro/playbooks/start-trigger-not-firing.md).
For instances stuck mid-process, use
[wait-for-event-stuck.md](../../maestro/playbooks/wait-for-event-stuck.md).
When a `DAP-RT-105x` code was emitted during trigger evaluation, use
[trigger-execution-failed.md](./trigger-execution-failed.md) instead — that is a coded
runtime fault, not a silent miss.

What can cause it:
- **CA001** — the trigger never polled: connection inactive or expired, trigger disabled, robot account lacks "Triggers" permission in the folder
- **CA002** — it polled and the connector returned nothing: wrong object, wrong parameters (e.g. mail folder), or the event fell outside the poll window
- **CA003** — events arrived and the trigger's filter rejected them
- **CA004** — events matched but dispatch failed: no robot, no license, process unavailable
- **CA005** — the subscription was deleted in the external service, so no event is ever delivered

What to look for:
- Whether any trace exists in the reported window — this splits CA001 from the rest
- `EventsFetched` vs `EventsMatched` on the traces that do exist
- The filter expression in the trace's spans, compared against the payload the connector received

## Investigation

1. **Anchor on the trigger, from whatever the user gave.** Event triggers are
   folder-scoped, so a folder is needed either way.

   | They gave | Do |
   |---|---|
   | the trigger **name** | pass it straight through: `--trigger-name "<name>"` resolves it |
   | the trigger **key** | pass `--trigger-key <guid>` |
   | a process, or neither | list the folder's event triggers and pick with them: `uip or triggers list --type event --folder-path "<folder>" --output json` |

   No separate lookup call is needed for a name — `uip is trigger-traces list` does it,
   and tells you when the name matches nothing or matches two triggers in that folder.
   It also validates the type: a key belonging to a time, queue or HTTP trigger fails
   with `not an Integration Service event trigger` and names the real type.

   A time, queue or HTTP trigger ends this playbook — use
   `uip or triggers history <key> --folder-path "<folder>" --output json` for its failed
   fire attempts instead.

2. **Read the traces for the user's window** — the one command that decides everything
   below. Match `--from` to what the user reported.

   ```bash
   uip is trigger-traces list --trigger-name "<name>" --folder-path "<folder>" --from 24h --output json
   # or --trigger-key <guid>
   ```

3. **Branch on the result** using the table in
   [investigation_guide.md § Step 2](../investigation_guide.md#step-2--read-the-row-before-gathering-anything-else).

4. **Zero traces (CA001) — only now check configuration.** Running these first against
   a trigger that polled fine every five minutes wastes the investigation.

   ```bash
   uip is connections ping <connection-id> --output json
   uip or triggers history <trigger-key> --folder-path "<folder>" --output json
   ```

   `triggers history` logs failed fire attempts (missing license, no machine, disabled
   trigger). It is a failure log, so an empty result does not mean the trigger ran.
   Also verify the robot account holds "Triggers" permission in the folder, not just
   "Connections.View".

5. **Traces exist — open one and read its spans** (CA002/CA003).

   ```bash
   uip traces spans get <trace-id> --output json
   ```

   The `UserFilters` / `Webhook User Filters` span carries
   `DataFilters.input.filter` and `DataFilters.output.matched`. For CA003, quote the
   expression and show which field of the payload failed it.

6. **Matched but no execution (CA004).** The trigger did its part; look downstream.

   ```bash
   uip or jobs list --folder-path "<folder>" --output json
   ```

## Resolution

- **CA001, connection** — re-authenticate: `uip is connections edit <connection-id>`
- **CA001, disabled trigger or permission** — enable the trigger in Orchestrator → folder → Triggers → Event triggers; grant the robot account "Triggers" on the folder
- **CA002** — correct the trigger's object or parameters in Integration Service. If the event predates the window, it will never be picked up; polling triggers only see events after the last poll date
- **CA003** — the filter is working as written and the user's expectation differs. Show the expression and the rejected payload, then change the filter or the event
- **CA004** — provision a robot or license, or fix the process binding in the folder
- **CA005** — recreate the trigger so the subscription is re-registered in the external service

Do not report "the trigger is broken" from zero traces alone — zero traces with a
healthy connection and an enabled trigger points at the subscription (CA005), which is
confirmed in the external service, not in UiPath.
