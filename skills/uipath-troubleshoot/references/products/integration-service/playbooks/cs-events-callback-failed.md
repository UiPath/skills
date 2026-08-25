---
confidence: medium
---

# Connection Service — Event Callback Processing Failed (CNS1005, CNS2000, CNS1015–CNS1019, CNS1024, CNS1029, CNS2011)

> **Fault bucket: 🛠 B1 — service-side (machine-to-machine path; the customer never makes these calls).** These codes fire while Connection Service processes an **inbound event callback** from the connector platform (the webhook that says "an event happened on the third-party side"). The caller is the platform itself, not a user — so a bad payload, an orphaned instance, or a mismatched connection ID is a platform/data-drift issue. The **customer-visible symptom is a trigger that doesn't fire** (or fires late); triage the customer report via [trigger-not-firing.md](./trigger-not-firing.md) and use this page to interpret what the service-side codes mean.

## Context

What this looks like (owner-team view — App Insights traces, not customer errors):
- `Connection Service error reported: [StatusCode: NotFound, ErrorCode: "CNS1005", ErrorReason: "Connection for element instance [N] was not found"]` — the single **highest-volume** CNS signal in production
- `CNS2000` — *"Fail to handle notification"* — a 500 catch-all around event handling

| Code | Name | Exact meaning | HTTP |
|------|------|---------------|:---:|
| `CNS1005` | ConnectionForElementInstanceNotFound | An event arrived for a provider-side element instance that maps to **no connection** — the connection was deleted but the provider-side subscription still delivers events (orphaned instance) | 404 |
| `CNS2000` | EventsCallbackFailed | Unhandled exception while processing the event callback | 500 |
| `CNS1015` | EventsCallbackInstanceIdMissing | Callback payload missing the instance ID | 400 |
| `CNS1016` | EventsCallbackHasMoreThanOneEvent | Callback carried more than one event (unsupported shape) | 400 |
| `CNS1017` | ObjectTypeMissing | Callback payload missing object name/type | 400 |
| `CNS1018` | EventsInfoMissing | Callback payload missing the events section | 400 |
| `CNS1019` | EventTypeMissing | Callback payload missing the event type | 400 |
| `CNS1024` | EventsCallbackRequestInvalid | Callback body null/unparsable JSON | 400 |
| `CNS1029` | EventsCallbackInvalidConnectionId | Connection ID in the callback route doesn't match the instance's actual connection | 400 |
| `CNS2011` | EventTypeUtilFailed | No matching event operation/mode/type registered for the connector event key — event-catalog mapping gap | 400 |

Related codes on the *outbound* side of the same pipeline: `CNS1011`/`CNS1012`/`CNS1013` (connection-event create/delete validation — duplicate registration, missing IDs) are low-volume request-validation errors on event-configuration APIs; fix the request. Event *dispatch* to downstream products failing is `CNS2012` — see [cs-dependency-unavailable.md](./cs-dependency-unavailable.md).

What can cause it:
- **`CNS1005` steady-state noise:** connections deleted while the provider-side event subscription lives on for a while — expected background volume, mostly benign; each hit is a dropped event for a connection that no longer exists
- Malformed or truncated payloads from the connector platform / provider (the `CNS101x` family)
- Connector catalog/event-registration drift (`CNS2011`, and `CNS2045` — see [cs-connector-unavailable.md](./cs-connector-unavailable.md))
- Genuine processing bugs or downstream failures inside event handling (`CNS2000`)

What to look for:
- **Volume shape, not single hits.** A flat baseline of `CNS1005` is normal; a step-change spike (or a cluster on one tenant/connector) is an incident or a mass-deletion side effect
- Whether a specific connector dominates the failures (points at that connector's payload shape or event registration)
- For a customer-reported missing trigger event: whether their connection was recently deleted/recreated (the old instance still emitting → events land on the orphan, new connection gets nothing until re-subscription)

## Investigation

1. **Start from the customer symptom** ("trigger didn't fire") with [trigger-not-firing.md](./trigger-not-firing.md) — verify the trigger, connection state, and event subscription first.
2. **Owner team — locate the callback failures:** in the region's Connection Service App Insights, `union traces, exceptions | where message has "CNS1005" or customDimensions.ErrorCode in ("CNS1005","CNS2000","CNS1029") | summarize count() by tostring(customDimensions.ErrorCode), bin(timestamp, 1h)` and segment by tenant/connector to find clusters.
3. **`CNS1005` for a specific complaint:** match the element-instance number in the message against the customer's connection history — if the events target a deleted connection's instance, the fix is re-establishing the subscription on the *new* connection (usually recreating the trigger), not chasing the 404s.
4. **`CNS101x` payload-shape codes:** capture a sample payload (owner team) and identify the sending connector — this is a defect report against the connector/platform event pipeline, not something to work around per-customer.
5. **`CNS2000`:** read the wrapped inner exception in the trace — it is a catch-all; classify the real cause (DB? downstream? mapping?) and route accordingly.

## Resolution

- **Customer-facing:** if events stopped after a connection was recreated, recreate/re-save the trigger so the event subscription binds to the new connection instance. Verify a test event flows end-to-end.
- **`CNS1005` background noise:** no action per-hit. Sustained high volume from one tenant is worth a cleanup (delete stale provider-side subscriptions) — an owner-team/ops action.
- **Payload-shape and mapping codes (`CNS101x`, `CNS2011`):** escalate to the Integration Service owner team with connector key, sample `traceId`s, and the earliest occurrence — these are connector/platform defects.
- **`CNS2000` clusters:** treat as a service incident — escalate with the inner-exception signature and time window.
- **Never** advise customers to retry or re-authenticate for these codes — the failing call is machine-to-machine; nothing on the customer side retries it.
