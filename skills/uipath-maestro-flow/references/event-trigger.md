# Connector Events

*Exact signatures, fields, and defaults: `onEvent()`, `waitForEvent()`.*

The same subscription can start a Flow or pause an existing path.

Signatures:

- `.trigger(onEvent({ connector, event, where?, filters?, connection, folder, version? }))`
- `.step(name, waitForEvent({ connector, event, where?, filters?, connection, folder, version? }))`
- Both also accept a generated trigger descriptor plus options.

```ts
.step('reply', waitForEvent({
  connector: 'uipath-microsoft-outlook365', event: 'email-received',
  where: { parentFolderId: inboxId },
  filters: [{ field: 'subject', contains: 'Approval' }],
  connection: 'outlook', folder: 'shared',
}))
```

`connection` and `folder` are required `bindings.json` labels. Without them, compilation emits `connectionId: null`, which `uip maestro flow validate` refuses; `check` therefore reports `BINDING_MISSING` first.

## At a glance

Start on or pause for an Integration Service event with `.trigger(onEvent(subscription))` or `.step(name, waitForEvent(subscription))`.

```ts
const mail = { connector: 'uipath-microsoft-outlook365',
  event: 'email-received', where: { parentFolderId: inboxId },
  connection: 'outlook', folder: 'shared' };   // bindings.json labels, both required
export default flow('mail').trigger(onEvent(mail))
  .step('reply', script({ code: 'return $vars.start.output.subject;' })).build();
```

Use `lookup()` for every id-valued parameter; run `registry prepare <key> --action <event>` to resolve ids, write bindings, and store `where`/`filters` vocabulary. `check` reports a wrong-case filter field as an error — the platform drops it silently. Generic `record-created`/`record-updated` events require `object: '<Entity>'`, never `object` in `where`.

An injected start payload tests downstream wiring, not subscription delivery; use the completion contract before debugging.

## Tenant discovery — `check` names it, `prepare` does it

Event parameters and their ids are connection-specific. Author the
subscription first — an id-valued parameter as a `lookup()` token, never a
pasted id — and one `prepare` discharges everything `check` names:

```ts
.trigger(onEvent({
  connector: 'uipath-microsoft-outlook365', event: 'email-received',
  where: { parentFolderId: lookup({ connector: 'uipath-microsoft-outlook365', event: 'email-received' }, 'parentFolderId').by('displayName', 'Inbox') },
  filters: [{ field: 'subject', contains: 'Approval' }], connection: 'outlook', folder: 'shared',
}))
```

```bash
uip maestro registry prepare uipath-microsoft-outlook365 --action email-received \
  --resolve parentFolderId:displayName=Inbox
```

That one command does all of this itself — do not do these steps by hand: it discovers the connection and writes both `bindings.json` entries (connection id AND folder key, as connector-action prepare does), fetches the connection-scoped event definition, records a generic event's object decision (`--object <name>`, using the same matching ladder as actions), stores `where`/filter vocabulary in `.flow-sdk/connectors-local/` so `check` works offline, and records each `--resolve` in `resolutions.json` for `compile` to substitute.

`check` validates every `where` key and `filters[].field` against that vocabulary. An unknown filter leaf is an ERROR (`EVENT_FILTER_UNKNOWN_FIELD`) because the platform silently drops it and may trigger on excluded events.

Prepare refuses an event object that requires a BYOA (bring-your-own-app) connection and shows which connections work, rather than allowing an unrelated runtime webhook fault. For a `webhooks`-mode event, prepare prints the URL-registration step; it cannot be debugged locally, so deploy to test it.

Do not run `uip is triggers objects` / `triggers describe` / `resources run list` by hand or paste ids into `where`: prepare runs those calls deterministically, and pasted ids are meaningless in review and wrong after a connection move.

Before finishing, inspect the emitted node's `inputs.detail.eventParameters`; confirm it contains the selected id and that connection/folder bindings use the same discovered connection. `contains` is case-sensitive substring matching, so preserve scenario casing.

If a known tenant event is absent after refreshing the registry/cache, report a cache-generation gap; do not invent a node type, binding, or field, or patch a prebuilt sample/cache entry to make it appear.

## Generic events: name the object

Most connectors expose generic `record-created` and `record-updated` events (Data Fabric, Salesforce, ServiceNow, Jira, Dynamics, …). Specify the bound connection's object with `object`; these operations take no event parameters, so `where` stays empty. `check` refuses a missing object (`EVENT_GENERIC_NO_OBJECT`) or an object in `where`.

```ts
<!--skill-flavor:generic-event-import:start-->
import { RecordCreated, RecordUpdated } from './connectors/uipath-uipath-dataservice.ts';
<!--skill-flavor:generic-event-import:end-->

.trigger(onEvent(RecordCreated, {
  object: 'ContractRegistry', filters: [{ field: 'dueDate', lessThan: '2026-08-04' }],
  connection: 'dataFabric', folder: 'shared',
}))
.step('updated', waitForEvent(RecordUpdated, {
  object: 'FileUploadVerify_20260618', connection: 'dataFabric', folder: 'shared',
}))
```

Get objects from the bound connection, never by guessing. Run:

```bash
uip is triggers objects uipath-uipath-dataservice CREATED --connection-id <id> --output json
```

The emitted node carries the object in `inputs.detail.objectName` and `configuration`, the event as `eventType`, and the platform-declared `eventMode`. Curated events (Outlook `email-received`, OneDrive `file-created`) have a built-in object; passing `object` is an error.

## Started by an HTTP call

A caller that starts the flow over HTTP, such as another system's webhook or a script, reaches it through the HTTP Webhook connector: `onEvent({ connector: 'uipath-http-webhook', event: 'http-webhook', connection, folder })`. The caller's authentication is set on the connection when it is created in Integration Service. With header authentication, Integration Service answers 401 to a request whose header is missing or wrong, and no run starts.

This is a webhook-mode event. Read the caller URL by running:

```bash
uip is webhooks config uipath-http-webhook --connection-id <CONNECTION_ID> --element-instance-id <ELEMENT_INSTANCE_ID> --output json
```

Both ids come from `uip is connections list --all-folders --output json` (`Id`, `ElementInstanceId`). The URL returns 404 until the flow is deployed with its trigger active.

Read the request from trigger output with `out('start', …)`:

- JSON-body top-level fields directly;
- parsed `body` and `headers` (header names lower-case);
- `request_body` and `request_headers` as JSON text, also accepted by `filters`;
- `eventType`.

Query-string parameters are not delivered. The headers include the authentication header itself, so never log or return `headers` whole. The caller gets only the acceptance (200 with a `webhookEventId`), never the flow's output, so a caller that needs the run's result is not served by this trigger.

## Filter operators

A filter is `{ field, <operator>: value }` with exactly one operator. The designer vocabulary compiles to the canvas `filterExpression`:

| Operator | Value | Emitted expression |
|---|---|---|
| `contains`, `startsWith`, `endsWith` | text | `contains(subject,'Invoice')` |
| `equals`, `notEquals` | text, number or boolean | `status=='open'`, ``priority==`3` `` |
| `lessThan`, `lessThanOrEqual`, `greaterThan`, `greaterThanOrEqual` | number, or an ISO date string | ``priority>`3` ``, `to_number(dueDate)<to_number('2026-08-04')` |
| `is`, `isNot` | always `true` | ``hasAttachments==`true` ``, ``isRead!=`true` `` |

`is`/`isNot` are the canvas "Is"/"Is not" boolean tests and always compare with `true`; `isNot: true` also matches a missing field. For "is false", use `equals: false`. Any other value is refused (`EVENT_FILTER_BAD_VALUE`).

Ordering a plain string is refused (`EVENT_FILTER_BAD_VALUE`): JMESPath compares numbers only. Use a number, an ISO-8601 date, or a text operator.

A backslash at the end of a filter or `where` value, or before another `\` or `'`, is refused (`EVENT_FILTER_BACKSLASH`) because JMESPath engines disagree (`\\` is one backslash in the specification and two in reference libraries). A backslash before any other character (`C:\tmp`, `Finance\Q3`) is preserved and reads identically.

## Evidence boundary

A local start-trigger run injects a payload; it does not fire a subscription. For a wait, seed both matching and nonmatching payloads to establish routing. Only a platform event occurrence proves the connection, scope, and subscription receive the intended event.

## Completion contract

Unless the request explicitly requires a live subscription witness, a connector-event start is complete after the last edit when both hold:

- `uip maestro flow validate` returns `Valid` for the emitted Flow.
- The emitted `.flow` has the intended start-trigger type, scope/filter inputs, bindings, and downstream edges.

Use at most one bounded direct-input debug for a downstream behavior question, and stop when answered; it is not subscription proof. Do not poll or sleep on debug instances, create a scratch solution, or upload seed content solely to manufacture a trigger event.

If acceptance requires live delivery, cause one real platform event and record that witness once. If the environment cannot provide it, report that boundary instead of repeating debug launches.
