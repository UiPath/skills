---
confidence: medium
---

# Custom Connector Trigger Contract

## Context

Use when a custom connector's event operation is absent, a polling trigger never fires, a
webhook cannot be provisioned or delivered, or the provider cannot supply the timestamp and
identity contract the trigger requires.

First use [trigger-not-firing.md](../trigger-not-firing.md) for connection and folder/caller
checks. This playbook covers the custom connector definition and provider event contract.

Required anchors: connector key/published version, connection and trigger IDs, event operation
and resource, event mode, expected provider record/event ID and UTC timestamps, request/trace
ID, exact poll window or webhook delivery evidence, and downstream execution status.

### What can cause it

- The event operation or polling/webhook metadata is absent from the imported/published connector revision.
- The polling URL, timestamp field/format/timezone, stable ID, page contract, event type, or use-last-poll setting is incorrect.
- The provider cannot expose a sufficiently stable timestamp/cursor and unique identity for the polling contract.
- The provider returned the record but mapping, filtering, watermark, or dedupe logic removed it.
- Webhook subscription creation, callback verification, signature validation, delivery, transformation, or deletion is incomplete.
- Integration Service emitted the event but the downstream workflow, folder, caller, or trigger binding did not consume it.

## Investigation

1. **Determine event mode from the published connector:** polling, webhook, or another supported
   mode. Do not infer it from what the provider supports.
2. **Confirm the event operation is declared and published:**

   ```bash
   uip login status --output json
   uip is connectors builder inspect --output json
   uip is connectors builder validate --output json
   uip is connectors event-operations <CONNECTOR_KEY> --output json
   ```

   Before interpreting the tenant-backed list, confirm the login status names the
   affected environment, organization, and tenant. An empty result from the wrong
   session is a scope mismatch, not proof of a connector defect. An empty list in
   the correlated tenant means runtime cannot create the intended trigger.
3. **Polling definition branch:** verify `hasEvents`, standard-resource event metadata,
   poller configuration, resource URL, stable ID field, updated/created timestamp fields,
   timestamp format/timezone, event types, pagination, and use-last-poll behavior.
4. **Provider contract branch:** prove the API can filter or return changes using a monotonic
   enough timestamp/cursor and stable unique ID. A date-only field or non-monotonic value may be
   a capability limitation, not a misconfigured filter.
5. **Polling runtime branch:** trace one expected record through scheduled poll, emitted request
   window/cursor, provider pages, date parsing, filter, dedupe/watermark, and callback. Separate
   no poll trace, empty provider result, returned-but-filtered, and emitted-but-undelivered.
6. **Webhook definition branch:** confirm that adding webhook configuration is not mistaken for
   implementing delivery. A working webhook also needs supported provision/delete resources,
   callback registration, verification/signature handling where required, and event-to-resource
   transformation.
7. **Webhook runtime branch:** verify provider registration/subscription, callback URL and
   authentication/signature, provider delivery log, IS receipt, payload transformation,
   dedupe, and downstream callback.
8. **Long polls:** compare scheduled, started, and completed times. A paginated/long prior poll
   can delay a later interval; do not label it “skipped” without timing evidence.

### Diagnosis

| Evidence | Diagnosis |
|---|---|
| Source declares events but published event-operations is empty | Event metadata/linkage or stale publish |
| Active trigger has no poll trace | Registration/scheduler/trace-ingestion branch |
| Poll runs but expected record is absent | Provider window/cursor/filter/permission/sync branch |
| Record is returned but date/ID/filter/dedupe rejects it | Polling contract/configuration |
| Event is emitted but downstream execution is absent | Callback/handoff branch |
| Webhook config exists but no provision/delete/delivery implementation | Incomplete webhook design |
| Provider lacks stable ID/timestamp/cursor required by polling | Capability limitation/design change |

## Resolution

Quote one confirmed cause verbatim from **What can cause it**, then correct only
that polling/webhook branch. If evidence does not isolate one cause, stop at the
missing discriminator.

Diagnosis is read-only. Obtain explicit approval before editing trigger metadata,
recreating a trigger, importing, publishing, or changing provider webhook settings.

- Recreate the polling bundle with the dedicated trigger authoring command when event metadata
  or configuration is malformed, then validate, import, and publish.
- Correct the proven URL, timestamp field/format/timezone, ID field, pagination, filter, or
  watermark branch. Do not widen windows blindly because duplicates and gaps can result.
- Implement all required webhook lifecycle and verification pieces when webhook delivery is the
  selected design; otherwise use a supported polling contract.
- If the provider cannot meet either event contract, document the limitation and redesign the
  trigger rather than claiming a runtime defect.
- Escalate no-trace or emitted-but-undelivered branches with end-to-end correlation anchors.

### Verification

Create one controlled provider event with a unique ID and known UTC timestamp. Demonstrate that
same ID through provider result/delivery, parsing, filter/dedupe, emitted event/callback, and
downstream execution. Also verify a second poll/delivery does not create an unintended duplicate.

### Escalation Bundle

Include anchors, redacted event and poller metadata, published event-operations output, provider
request/response or delivery record, poll schedule/start/end times, exact window/cursor, date/ID
parsing, filter/dedupe result, callback status, and downstream job/process ID.
