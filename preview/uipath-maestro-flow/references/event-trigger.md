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
# Enumerate the event's objects on the exact connection the Flow will bind.
uip is triggers objects <connector> <event> \
  --connection-id <connection-id> --output json

# Describe the selected object to confirm its event-parameter contract.
uip is triggers describe <connector> <event> <object> \
  --connection-id <connection-id> --output json
```

Use the selected object's live `Id` for an id-valued event parameter. For
Outlook `email-received`, for example, choose the Inbox `MailFolder` returned by
`triggers objects` and pass that row's `Id` as `where.parentFolderId`; the
display name `Inbox` and an id from another connection are not substitutes.
Before finishing, inspect the emitted node's `inputs.detail.eventParameters`
and confirm it contains the selected id and the connection/folder bindings refer
to the same connection used for discovery.

`contains` uses case-sensitive substring matching, so preserve scenario casing.
If a known tenant event is absent after refreshing the registry/cache, report a
cache-generation gap instead of inventing a node type, binding, or field. Do
not patch a prebuilt sample/cache entry to make the missing event appear.

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
