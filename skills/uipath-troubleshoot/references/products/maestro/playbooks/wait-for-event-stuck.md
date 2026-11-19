---
confidence: high
---

# Maestro Instances Stuck on a Wait-For-Event

## Context

What this looks like:
- Process instances sit in `Running` and make no progress
- The user is producing the event they believe should resume them — "I am updating the
  cases and nothing moves"
- No incident, no fault; the instances are simply waiting
- The user rarely says "trigger" or "Wait-For-Event". **"Still running" and "stuck" are
  the tells**

**Applies only when the instances are waiting on an Integration Service Wait-For-Event
element.** An instance in `Running` can equally be waiting on a timer, an Action Center
task, a child job, or a long-running activity. Confirm at Step 2 and route out if the
element is not a WFE — see the applicability gate in
[investigation_guide.md](../../integration-service/investigation_guide.md#applicability-gate--run-this-first)
and [bpmn-job-stuck.md](./bpmn-job-stuck.md) for the non-WFE causes.

**A Wait-For-Event trigger is created per instance and correlates to one specific
record.** Ten stuck instances are ten different triggers with ten different filters.
Never generalise from one, and never assume an update to *a* record of the right type
will resume an instance waiting on *another*.

What can cause it:
- **CA001** — the instance is not waiting on a WFE at all (timer, task, child job)
- **CA002** — the WFE trigger received no event: the update produced no notification the connector saw, or the connection is down
- **CA003** — an event arrived and the correlation filter rejected it, because it names a different record than the one the user updated
- **CA004** — the event matched and the instance still did not resume, which is a Maestro-side resume failure rather than a trigger problem

What to look for:
- Which element each instance is parked on, and whether it carries `intSvcTriggerId`
- Whether that instance's trigger has any traces at all in the window
- The record id inside the correlation filter, compared against what the user updated

## Investigation

1. **List the stuck instances** for the process and window. The user usually has no
   instance id.

   ```bash
   uip maestro bpmn instances list --process-key <process-key> --folder-key <folder-key> \
     --status Running --from-date <iso-8601> --output json
   ```

2. **Confirm each is parked on a Wait-For-Event (CA001 gate).** A Maestro instance id
   doubles as its trace id, so its spans are reachable directly.

   ```bash
   uip traces spans get <instance-id> --output json
   ```

   Span `Attributes` arrive as a JSON string. The waiting element is the one whose
   attributes carry `intSvcTriggerId`, with `elementType: "ReceiveTask"` and
   `elementExtensionType: "Intsvc.WaitForEvent"`. **No span carries `intSvcTriggerId`**
   → the instance is waiting on something else; stop here and route to
   [bpmn-job-stuck.md](./bpmn-job-stuck.md).

3. **Read that element's trigger traces — once per instance.** Each instance has its
   own trigger, so this runs per instance, not once for the process. Investigate a
   handful first and only widen if their causes differ.

   ```bash
   uip is trigger-traces list --instance-id <instance-id> --from 24h --output json
   ```

   The command resolves `intSvcTriggerId` from the spans itself and queries with
   `source=maestro`; no folder is needed. If the process has more than one WFE element,
   it lists them and asks for `--element <element-id>`.

4. **Branch.**

   - **Zero traces (CA002)** — the trigger received nothing. The user's update produced
     no event the connector saw. Check the connection, and confirm the update really
     raised the event type the element subscribes to (an update that changes no watched
     field often raises nothing).
   - **Traces with `EventsMatched: 0` (CA003)** — events arrived and the correlation
     filter rejected them. Go to Step 5. **This is the usual answer.**
   - **Traces with `EventsMatched > 0` (CA004)** — the trigger matched and the instance
     should have resumed. The fault is Maestro-side; see
     [bpmn-job-stuck.md](./bpmn-job-stuck.md).

5. **Read the correlation filter and name the record (CA003).**

   ```bash
   uip traces spans get <trace-id> --output json
   ```

   The `Webhook User Filters` span carries `DataFilters.input.filter`, e.g.

   ```
   (Id == 'F9BAC415-3BE3-F111-91F2-7C1E521F9806' && Name == 'TriggersReliability_Updated')
   ```

   That id is the only record this instance will resume for. Compare it against what
   the user updated. The `Webhook Data` span holds the payload that did arrive, so both
   sides of the mismatch can be shown together.

## Resolution

- **CA001** — not a trigger problem; the instance waits on a timer, task or child job
- **CA002** — restore the connection, or have the user make a change that actually raises the subscribed event. Report which event type the element subscribes to
- **CA003** — the instance is waiting on a specific record and a different one was updated. Give the user the id from the filter. If the correlation key itself is wrong, that is a process-design fix in the WFE element, not a runtime one
- **CA004** — escalate as a Maestro resume failure, quoting the trace id that matched and the instance that did not advance

Present per instance, not in aggregate. Ten instances stuck for two different reasons
reported as one cause sends the user to fix the wrong thing. When several share a
cause, group them and say how many.
