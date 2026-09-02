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

## Tenant discovery

Event parameters and their ids can be connection-specific. Resolve them from
the bound live connection rather than inferring them from a display label or
copying an id from an example, cached descriptor, or earlier session.

```bash
# When a folder path is specified, scope connection discovery to that exact
# folder. Do not choose a same-connector row from an all-folders listing.
uip or folders get <folder-path> --output json
uip is connections list <connector> --folder-key <folder-key> --output json

# Enumerate the event's object types on the exact connection the Flow will bind.
# Use the Integration Service operation (for example EMAIL_RECEIVED), not the
# builder event slug (for example email-received).
uip is triggers objects <connector> <operation> \
  --connection-id <connection-id> --output json

# Describe the selected object to confirm its event-parameter contract.
uip is triggers describe <connector> <operation> <object> \
  --connection-id <connection-id> --output json

# If the contract names a reference object, list its values on that connection.
uip is resources run list <connector> <reference-object> \
  --connection-id <connection-id> --output json
```

Use the selected reference row's live `Id` for an id-valued event parameter.
For Outlook `email-received`, for example, select the `Message` object, confirm
that `parentFolderId` references `MailFolder`, list `MailFolder`, and pass the
Inbox row's `Id` as `where.parentFolderId`; the display name `Inbox` and an id
from another connection are not substitutes.
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
