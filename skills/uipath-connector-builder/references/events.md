# Events Reference

Events detect vendor-side changes (CREATED / UPDATED / DELETED). Two mechanisms:
**polling** (periodic API calls) and **webhooks** (vendor pushes notifications). An event
source is always an existing activity — wire it AFTER the activity exists.

## How events are configured NOW

`uip is connectors builder trigger create` is the single entry point. It folds together what
used to be two separate steps (the old `config preset --kind event` and `event polling add`,
both REMOVED). One call seeds the event config bundle, writes the per-resource poller config,
sets the SR `metadata.events`, and flips `hasEvents`. The activity must already exist —
`trigger create` HARD-FAILS if its SR is missing. Runnable workflow: SKILL.md → "Add a polling (or webhook) trigger".

Key flags (`trigger create`):
- `--resource-name <name>` — existing activity/standard-resource to wire (required).
- `--event-kind polling | webhook | all` — which config bundle to seed (default `polling`).
- `--updated-date-field <field>` — vendor last-modified field (e.g. `LastModifiedDate`).
- `--created-date-field <field>` — defaults to `--updated-date-field`.
- `--id-field <field>` — primary key (defaults to `Id`).
- `--date-format <mask>` / `--created-date-format <mask>` — timestamp mask (created defaults to updated).
- `--event-types <csv>` — defaults to `CREATED,UPDATED,DELETED`.
- `--polling-url <url>` — explicit; auto-generated from the GET path when omitted.
- `--date-timezone <tz>` — default `GMT`.
- `--polling-resource-label <label>` — label in `elementMetadata.pollingResources`.
- `--override <key>=<value>` — per-entry defaultValue override for the event preset (repeatable).

## What gets written

1. `element-metadata.json → hasEvents: true` (without it, events never fire).
2. `element.json → configuration[]` — the event config keys (the preset bundle).
3. `standard-resources/<name>.json → metadata.events` — per-resource event metadata.
4. `element.json/configuration/event.poller.configuration` — the polling JSON blob below.

## Polling config keys (the bundle)

`event.notification.enabled` (master switch), `event.vendor.type` (`polling` / `webhook`),
`event.poller.refresh_interval` (minutes, default 15), `event.poller.configuration`
(JSON blob below), `event.notification.callback.url`, `event.raw.enabled`.

## event.poller.configuration JSON

First resource is typically keyed `"events"`; others use the resource name.
```json
{
  "events": {
    "url": "/accounts?where=LastModifiedDate>'${date:yyyy-MM-dd'T'HH:mm:ss.SSS'Z'}'",
    "idField": "Id",
    "datesConfiguration": {
      "updatedDateField": "LastModifiedDate",
      "updatedDateFormat": "yyyy-MM-dd'T'HH:mm:ss.SSSZ",
      "updatedDateTimezone": "GMT",
      "createdDateField": "CreatedDate",
      "createdDateFormat": "yyyy-MM-dd'T'HH:mm:ss.SSSZ"
    },
    "createdCheckTolerance": 10
  }
}
```
Per-resource fields: `url` (required — IS slug path with `${date:FORMAT}` placeholder for
last poll time), `idField` (required — unique key), `datesConfiguration` (required),
`createdCheckTolerance` (sec, default 10), `filterByUpdatedDate`, `filterByCurrentDate`,
`pageSize`, `pollDelay`, `batchSize`, `postHooks`, `postHookPipelines`, `useLastPollDate`,
`useHydrationBeforePostHooks`, `objectName`, `parameters`.

`datesConfiguration`: `updatedDateField`, `updatedDateFormat` (Java SimpleDateFormat),
`updatedDateTimezone` (default GMT), `createdDateField`, `createdDateFormat`
(defaults to updated), `createdDateTimezone`.

The `${date:FORMAT}` placeholder (and `${gmtDate:FORMAT}`, the GMT-forced variant) is
replaced at runtime with the last poll time; the format MUST match what the vendor accepts
(e.g. Salesforce `yyyy-MM-dd'T'HH:mm:ss.SSSZ`, most REST `yyyy-MM-dd'T'HH:mm:ss'Z'`, ISO
`yyyy-MM-dd'T'HH:mm:ssXXX`, or epoch millis).

To tweak one key after `trigger create`, `state query` the entry then `state patch` the
complete object back (patch REPLACES — see [debugging.md](debugging.md)).

## Webhook config keys (`--event-kind webhook` or `all`)

`event.notification.callback.headers`, `event.notification.signature.key` (HMAC),
`event.notification.basic.username`, `event.notification.basic.password`,
`event.notification.instance.finder`. Webhooks usually need `onProvisionWebhook` /
`onDeleteWebhook` system resources + a post hook (see
[system-resources.md](system-resources.md), [hooks.md](hooks.md)).

## SR-level event metadata (`metadata.events`)

`trigger create` writes this — DON'T hand-author it. The shape periodic requires (a flat
`{type:"polling", …}` is silently IGNORED — `event-operations` comes back empty and the trigger
never fires):

```json
"events": {
  "eventMode": ["polling"],
  "polling": {
    "configuration": {
      "datesConfiguration": { "updatedDateField": "...", "updatedDateFormat": "...",
        "updatedDateTimezone": "GMT", "createdDateField": "...", "createdDateFormat": "..." },
      "idField": "id",
      "url": "/tickets?where=modifiedTime>'${gmtDate:...}'",
      "useLastPollDate": true
    },
    "eventTypes": [
      { "operation": "CREATED", "displayName": "Record Created", "description": "..." },
      { "operation": "UPDATED", "displayName": "Record Updated", "description": "..." }
    ]
  }
}
```

Each `eventTypes[]` entry: `operation` (CREATED / UPDATED / DELETED / a curated op like
TICKET_CLOSED), `displayName`, `description`, optional `objectName`. Top-level `eventMode` is the
array `["polling"]` (or `["webhooks"]` / `["fps"]`). Confirm a published trigger surfaced with
`uip is connectors event-operations <custom-key>` — a non-empty list means it's wired.

## See also
- [configuration.md](configuration.md), [debugging.md](debugging.md), [standard-resources.md](standard-resources.md)
