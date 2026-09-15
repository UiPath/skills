# Connector Events

*Exact signatures, fields, and defaults: [`onEvent()`](api.md#onevent-function), [`waitForEvent()`](api.md#waitforevent-function).*

The same subscription can start a Flow or pause an already-running path.

Signatures:

- `.trigger(onEvent({ connector, event, where?, filters?, connection?, folder?, version? }))`
- `.step(name, waitForEvent({ connector, event, where?, filters?, connection?, folder?, version? }))`
- both also accept a generated trigger descriptor plus options.

```ts
.step('reply', waitForEvent({
  connector: 'uipath-microsoft-outlook365', event: 'email-received',
  where: { parentFolderId: inboxId },
  filters: [{ field: 'subject', contains: 'Approval' }],
}))
```

## Tenant discovery — `check` names it, `prepare` does it

Event parameters and their ids are connection-specific. Author the
subscription first — an id-valued parameter as a `lookup()` token, never a
pasted id — and one `prepare` discharges everything `check` names:

```ts
.trigger(onEvent({
  connector: 'uipath-microsoft-outlook365', event: 'email-received',
  where: {
    parentFolderId: lookup({ connector: 'uipath-microsoft-outlook365', event: 'email-received' },
      'parentFolderId').by('displayName', 'Inbox'),
  },
  filters: [{ field: 'subject', contains: 'Approval' }],
  connection: 'outlook365', folder: 'shared',
}))
```

```bash
npx flow-sdk registry prepare uipath-microsoft-outlook365 email-received \
  --resolve parentFolderId:displayName=Inbox
```

That one command replaces the old manual sequence end to end: it discovers the
connection and writes both `bindings.json` entries (connection id AND folder
key — the same stage a connector-action prepare runs), fetches the event's
connection-scoped definition, records the object decision for a generic event
(`--object <name>`, the same matching ladder actions use), stores the
where/filter vocabulary in `connectors-local/` so `check` works offline, and
records each `--resolve` in `resolutions.json` for `compile` to substitute.
`check` then validates every `where` key and every `filters[].field` against
the prepared vocabulary — an unknown filter leaf is an ERROR
(`EVENT_FILTER_UNKNOWN_FIELD`), because the platform silently drops it and the
deployed trigger fires on events the filter should exclude.

Two facts prepare surfaces before they can hurt: an event object that requires
a BYOA (bring-your-own-app) connection is refused with the connections that
would work, instead of faulting at runtime with an unrelated webhook error;
and a `webhooks`-mode event prints the URL-registration step — it cannot be
debugged locally, so deploy to test it.

Do not run `uip is triggers objects` / `triggers describe` /
`resources run list` by hand and paste ids into `where`: prepare runs the same
calls deterministically, and a pasted id is meaningless in review and wrong
after a connection move.
Before finishing, inspect the emitted node's `inputs.detail.eventParameters`
and confirm it contains the selected id and the connection/folder bindings refer
to the same connection used for discovery.

`contains` uses case-sensitive substring matching, so preserve scenario casing.
If a known tenant event is absent after refreshing the registry/cache, report a
cache-generation gap instead of inventing a node type, binding, or field. Do
not patch a prebuilt sample/cache entry to make the missing event appear.

## Generic events: name the object

Most connectors expose their record events generically — `record-created`,
`record-updated` (Data Fabric, Salesforce, ServiceNow, Jira, Dynamics, …).
One node type covers every object of the connection, so the subscription must
say which one with `object`. It is not an event parameter: these operations
take none, so `where` stays empty and `check` refuses a subscription that
omits `object` (`EVENT_GENERIC_NO_OBJECT`) or puts the object in `where`.

```ts
import { RecordCreated, RecordUpdated } from './connectors/uipath-uipath-dataservice.ts';

// Start when a ContractRegistry record is created with dueDate before 2026-08-04.
.trigger(onEvent(RecordCreated, {
  object: 'ContractRegistry',
  filters: [{ field: 'dueDate', lessThan: '2026-08-04' }],
  connection: 'dataFabric', folder: 'shared',
}))

// Pause until a FileUploadVerify_20260618 record is updated.
.step('updated', waitForEvent(RecordUpdated, {
  object: 'FileUploadVerify_20260618', connection: 'dataFabric', folder: 'shared',
}))
```

The objects come from the bound connection, never from a guess:

```bash
uip is triggers objects uipath-uipath-dataservice CREATED --connection-id <id> --output json
```

The emitted node carries the object as `inputs.detail.objectName` (and inside
`configuration`), its event as `eventType`, and the platform-declared
`eventMode`. A curated event (Outlook `email-received`, OneDrive `file-created`)
has its object built in — passing `object` there is an error.

## Filter operators

A filter is `{ field, <operator>: value }` with exactly one operator. The
vocabulary is the designer's, and each form compiles to the same
`filterExpression` the canvas would write:

| Operator | Value | Emitted expression |
|---|---|---|
| `contains`, `startsWith`, `endsWith` | text | `contains(subject,'Invoice')` |
| `equals`, `notEquals` | text, number or boolean | `status=='open'`, ``priority==`3` `` |
| `lessThan`, `lessThanOrEqual`, `greaterThan`, `greaterThanOrEqual` | number, or an ISO date string | ``priority>`3` ``, `to_number(dueDate)<to_number('2026-08-04')` |

Ordering a plain string is refused (`EVENT_FILTER_BAD_VALUE`): JMESPath
compares numbers only, so the subscription would match nothing. Write the
value as a number or an ISO-8601 date, or use a text operator.

## Evidence boundary

A local start-trigger run injects a payload; it does not fire a subscription.
For a wait, seed both matching and nonmatching payloads to establish routing.
Only a platform event occurrence proves the connection, scope, and subscription
actually receive the intended event.

## Completion contract

Unless the request explicitly requires a live subscription witness, a
connector-event start is done after the last edit when both of these facts hold:

- `uip maestro flow validate` returns `Valid` for the emitted Flow.
- The emitted `.flow` carries the intended start-trigger type, scope/filter inputs,
  bindings, and downstream edges.

At most one bounded direct-input debug may be used to answer a downstream
behavior question; stop when it answers that question. It is not subscription
proof. Do not poll or sleep on debug instances, create a scratch solution, or
upload seed content solely to manufacture a trigger event.

When the stated acceptance bar does require live delivery, cause one real
platform event and record that witness once. If the environment cannot provide
it, report that boundary instead of substituting repeated debug launches.
