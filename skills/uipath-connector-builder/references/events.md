# Events Reference

Events detect vendor-side changes (created/updated/deleted). Two mechanisms:
**polling** (periodic API calls) and **webhooks** (vendor pushes notifications).

## Where it's configured
1. `element.json → configuration[]` — event config keys
2. `element-metadata.json → hasEvents: true` (required, else events never fire)
3. `standard-resources/*.json` — `metadata.events` per resource
4. `event.poller.configuration` — JSON blob defining polling per resource
5. `event-hook/` — optional JS post-processing

`config preset create --kind event --event-type polling` seeds these keys in one call;
add or edit individual keys with `config create`.

## Polling config keys
`event.notification.enabled` (master switch), `event.vendor.type` (`polling`/`webhook`),
`event.poller.refresh_interval` (minutes, default 15), `event.poller.configuration`
(JSON blob), `event.notification.callback.url`, `event.raw.enabled`.

## Poller configuration JSON
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
`pageSize`, `pollDelay`, `batchSize`, `postHooks`, `postHookPipelines`,
`useLastPollDate`, `useHydrationBeforePostHooks`, `objectName`, `parameters`.

`datesConfiguration`: `updatedDateField`, `updatedDateFormat` (Java SimpleDateFormat),
`updatedDateTimezone` (default GMT), `createdDateField`, `createdDateFormat`
(defaults to updated), `createdDateTimezone`.

The `${date:FORMAT}` placeholder (and `${gmtDate:FORMAT}`, the GMT-forced variant) is
replaced at runtime with the last poll time; the format MUST match what the vendor accepts
(e.g. Salesforce `yyyy-MM-dd'T'HH:mm:ss.SSSZ`, most REST `yyyy-MM-dd'T'HH:mm:ss'Z'`, ISO
`yyyy-MM-dd'T'HH:mm:ssXXX`, or epoch millis).

## Webhook config keys (additional)
`event.notification.callback.headers`, `event.notification.signature.key` (HMAC),
`event.notification.basic.username`, `event.notification.basic.password`,
`event.notification.instance.finder`. Webhooks usually need `onProvisionWebhook` /
`onDeleteWebhook` system resources + an event hook (see [system-resources.md](system-resources.md)).

## Event types (SR level)
`operation` (CREATED/UPDATED/DELETED), `eventMode` (polling/webhooks/fps), `displayName`,
`description`, `objectName`, `isHidden`, `lifecycleStage`.

## See also
- [configuration.md](configuration.md), [debugging.md](debugging.md)
