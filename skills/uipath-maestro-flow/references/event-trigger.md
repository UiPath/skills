# Connector Events

*Exact signatures, fields, and defaults: `onEvent()`, `waitForEvent()`.*

A subscription starts a Flow or pauses a running path:

- `.trigger(onEvent({ connector, event, where?, filters?, connection, folder, version? }))`
- `.step(name, waitForEvent({ connector, event, where?, filters?, connection, folder, version? }))`
- Both accept a generated trigger descriptor plus options.

`connection` and `folder` are required `bindings.json` labels. Without them, the node compiles to `connectionId: null`; `uip maestro flow validate` refuses it and `check` reports `BINDING_MISSING` first.

## At a glance

Use an Integration Service event subscription to start or pause a Flow. Every id-valued `where` parameter must be a `lookup()` token. Run `registry prepare <key> --action <event>` to resolve it, write bindings, and store the vocabulary validated by `check`. Wrong-case filter fields are errors because the platform silently drops them. Generic `record-created`/`record-updated` events require `object: '<Entity>'`, never `object` in `where`.

Follow the completion contract before debugging: an injected start payload tests downstream wiring, not subscription delivery.

## Tenant discovery — `check` names it, `prepare` does it

Author the subscription with `lookup()` for every id-valued parameter, then run one `prepare`:

```bash
uip maestro registry prepare uipath-microsoft-outlook365 --action email-received \
  --resolve parentFolderId:displayName=Inbox
```

Run that command to discover the connection; write both `bindings.json` entries (connection id and folder key, as connector-action prepare does); fetch the connection-scoped event definition; record a generic event's object decision (`--object <name>`, using the same matching ladder as actions); store `where`/filter vocabulary in `.flow-sdk/connectors-local/` for offline `check`; and record each `--resolve` in `resolutions.json` for `compile`.

`check` validates every `where` key and `filters[].field`. An unknown leaf is an ERROR, `EVENT_FILTER_UNKNOWN_FIELD`, because the platform would silently drop it. Prepare refuses an event object requiring a BYOA (bring-your-own-app) connection and reports usable connections. For a `webhooks`-mode event, it prints the URL-registration step; it cannot be tested locally, so deploy to test it.

Do not run `uip is triggers objects` / `triggers describe` / `resources run list` manually or paste ids into `where`: prepare performs the same calls deterministically, and pasted ids become invalid after a connection move. Before finishing, inspect `inputs.detail.eventParameters` and confirm it contains the selected id and that connection/folder bindings use the discovery connection.

`contains` is case-sensitive substring matching; preserve scenario casing. If a known tenant event is absent after refreshing the registry/cache, report a cache-generation gap. Do not invent a node type, binding, or field, or patch a prebuilt sample/cache entry to make the event appear.

## Generic events: name the object

Generic `record-created` and `record-updated` events (Data Fabric, Salesforce, ServiceNow, Jira, Dynamics, …) require the object for the bound connection and take no event parameters, so `where` stays empty. `check` rejects a missing object with `EVENT_GENERIC_NO_OBJECT` and rejects an object placed in `where`.

<!--skill-flavor:generic-event-import:start-->
import { RecordCreated, RecordUpdated } from './connectors/uipath-uipath-dataservice.ts';
<!--skill-flavor:generic-event-import:end-->

Use the generated descriptor with `object`, optional `filters`, and required `connection` and `folder`; discover objects from the bound connection, never by guessing:

```bash
uip is triggers objects uipath-uipath-dataservice CREATED --connection-id <id> --output json
```

The emitted node carries the object in `inputs.detail.objectName` and `configuration`, its event in `eventType`, and the platform-declared `eventMode`. Curated events such as Outlook `email-received` and OneDrive `file-created` have built-in objects; passing `object` is an error.

## Started by an HTTP call

For a caller such as another webhook or script, run the HTTP Webhook connector subscription: `onEvent({ connector: 'uipath-http-webhook', event: 'http-webhook', connection, folder })`. Integration Service configures caller authentication on the connection; with header authentication, a missing or wrong header returns 401 and starts no run.

The event is webhook-mode. Read its URL with:

```bash
uip is webhooks config uipath-http-webhook --connection-id <CONNECTION_ID> --element-instance-id <ELEMENT_INSTANCE_ID> --output json
```

Both ids come from `uip is connections list --all-folders --output json` (`Id`, `ElementInstanceId`). The URL returns 404 until the flow is deployed with its trigger active.

Read the request from `out('start', …)`:

- JSON-body top-level fields directly;
- parsed `body` and `headers` (header names lower-case);
- `request_body` and `request_headers` as JSON text, also usable by `filters`;
- `eventType`.

Query-string parameters are not delivered. Headers include the authentication header: never log or return `headers` whole. The caller receives only acceptance (200 with a `webhookEventId`), not flow output; use another trigger if it needs the run result.

## Filter operators

A filter is `{ field, <operator>: value }` with exactly one operator. The designer vocabulary compiles to the canvas's `filterExpression`:

| Operator | Value | Emitted expression |
|---|---|---|
| `contains`, `startsWith`, `endsWith` | text | `contains(subject,'Invoice')` |
| `equals`, `notEquals` | text, number or boolean | `status=='open'`, ``priority==`3` `` |
| `lessThan`, `lessThanOrEqual`, `greaterThan`, `greaterThanOrEqual` | number, or an ISO date string | ``priority>`3` ``, `to_number(dueDate)<to_number('2026-08-04')` |
| `is`, `isNot` | always `true` | ``hasAttachments==`true` ``, ``isRead!=`true` `` |

`is`/`isNot` are the canvas's “Is”/“Is not” tests and always compare with `true`; `isNot: true` also matches a missing field. For “is false,” use `equals: false`. Any other `is`/`isNot` value is refused with `EVENT_FILTER_BAD_VALUE`.

Ordering a plain string is refused with `EVENT_FILTER_BAD_VALUE`: JMESPath compares numbers only. Use a number, an ISO-8601 date, or a text operator. A backslash at the end of a filter or `where` value, or before another `\\` or a `'`, is refused with `EVENT_FILTER_BACKSLASH`, because JMESPath engines interpret `\\` differently (the specification as one backslash, reference libraries as two). A backslash before another character, such as `C:\tmp` or `Finance\Q3`, is retained and reads consistently.

## Evidence boundary

A local start-trigger run injects a payload; it does not fire a subscription. For a wait, seed matching and nonmatching payloads to establish routing. Only a real platform event proves connection, scope, and subscription delivery.

## Completion contract

Unless explicitly required to witness a live subscription, finish after the last edit when both hold:

- `uip maestro flow validate` returns `Valid` for the emitted Flow.
- The emitted `.flow` has the intended start-trigger type, scope/filter inputs, bindings, and downstream edges.

Use at most one bounded direct-input debug for a downstream behavior question and stop when answered; it is not subscription proof. Do not poll or sleep on debug instances, create a scratch solution, or upload seed content solely to manufacture a trigger event.

If live delivery is required, cause one real platform event and record that witness once. If the environment cannot provide it, report that boundary instead of repeating debug launches.