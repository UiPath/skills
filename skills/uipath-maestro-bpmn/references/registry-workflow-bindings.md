# Registry workflow: bindings and triggers

## 4. Bindings — from `bindingInfo`, never invented

A node that targets a cloud resource carries a binding. The `bindingInfo` on the
extension type tells you the binding shape; the concrete value comes from
discovery or the user.

- **Resource bindings** (`bindingInfo.resource` = `process` / `queue` /
  `BusinessRule`): the context field named by `bindingInfo.contextField`
  (e.g. `releaseKey`, `queueName`, `entityKey`) holds the resource key
  (`bindingInfo.propertyAttribute`, usually `Key`). Resolve the real key with
  `registry search` / discovered `Processes` / `Queues`; never guess a GUID.
  A business rule binds `entityKey`, `name`, and `folderPath` to `BusinessRule`
  (`Key`, `name`, `folderPath`) — never a `process` `releaseKey`, even when
  `registry get` returns one. Its key is the rule's catalog entity key, never a
  `Key` from `Processes` or a release key; if the user has not given it, ask.
  A rule defined only in this solution uses its name as the key. The
  `folderPath` binding always carries a `default`, `""` when the rule lives in
  the running job's folder. Its unbound `_label` context holds the rule's name.
- **Connection bindings** (`Intsvc.*`): the context references a connection via
  `=bindings.<bindingId>`, and a `<uipath:binding>` of `resource="Connection"`
  with `propertyAttribute="ConnectionId"` in the process-level
  `<uipath:bindings>` holds the live connection id from `uip is connections list`.
  The context field that carries the reference differs by node kind: activities
  (`Intsvc.ActivityExecution`) use `connection`; connector **triggers and waits**
  (`Intsvc.EventTrigger`, `Intsvc.WaitForEvent`) use `connectionId`. Either way
  `uip maestro bpmn refresh` (and `pack`) materialize that binding into a
  `Connection` resource in `bindings_v2.json` — without it the process passes
  `validate` but faults at runtime with `102010 IntSvcArgumentsError -
  Integration Services invalid value in input` (the connection resolves to null).

Declare all bindings in a single process-level `<uipath:bindings version="v1">`
block. Each `<uipath:binding>` carries `id`, `resource`, `propertyAttribute`, and a
`default` value (the resolved key or id). On a **connection** binding
`resourceKey` is required too — omitting it fails `validate` with
`Integration Service activity connection binding "<id>" is missing
resourceKey`. A `BusinessRule` binding carries the rule key as `resourceKey`.
Other binding kinds (`process`, `queue`) carry no `resourceKey`; do not invent
one.

A folder-scoped connector activity needs TWO bindings that share one
`resourceKey` (the connection id) and differ in `propertyAttribute`: the
connection binding's `default` is the connection id, the folder binding's
`default` is the folder key.

```xml
<uipath:bindings version="v1">
  <uipath:binding id="Binding_JiraConn"   resource="Connection" propertyAttribute="ConnectionId" resourceKey="&lt;connection-id&gt;" default="&lt;connection-id&gt;" />
  <uipath:binding id="Binding_JiraFolder" resource="Connection" propertyAttribute="folderKey"    resourceKey="&lt;connection-id&gt;" default="&lt;folder-key&gt;" />
</uipath:bindings>
```

Only the `ConnectionId` binding becomes a `bindings_v2.json` resource — the
folder binding exists for authoring and validation. `buildConnectionResources`
(`connection-resources.ts`) keeps a binding only when `resource` is
`Connection` **and** `propertyAttribute` is `ConnectionId`, so counting two
bindings in and one resource out is expected, not a dropped binding.

The folder binding is exempt from the missing-binding error because nothing
resolves it through that map: `buildConnectionResources` looks up only the
binding named by the activity's **`connection`** input. Point that input at a
binding whose `propertyAttribute` is anything other than `ConnectionId` and the
lookup misses, producing
`Activity "<name>" references missing Connection binding "<id>"` — an error
naming the activity when the defect is one attribute on the binding. The
`folderKey` input is read separately and never goes through the lookup.

## Integration Service triggers

`Intsvc.TimerTrigger` is portable: its registry entry has
`RequiresDiscovery=false`, no binding, context, or input fields, and needs only
the exact `registry get Intsvc.TimerTrigger` template. It does not require a
live connection or schema enrichment.

`Intsvc.EventTrigger` and connector waits such as `Intsvc.WaitForEvent` enrich
through `registry get` like a [§3](registry-workflow-connector-object.md#3-connector-intsvc-enrichment) activity, but their object and operation come
from the **trigger** catalogue, not from `uip is resources`. Omit `--operation`
and the call fails with `Event enrichment requires --operation`.

```bash
uip is activities list <connectorKey> --triggers --output json   # Name + ObjectName + IsCurated
uip is triggers objects <connectorKey> <OPERATION> --connection-id <id> --output json  # generic rows only
uip is triggers describe <connectorKey> <operation> <objectName> --connection-id <id> --output json
uip maestro bpmn registry get <Intsvc.EventTrigger|Intsvc.WaitForEvent> \
    --connection-id <id> --object-name <ObjectName> --operation <Name> --output json
```

Prefer a row whose `IsCurated` is `Yes`. A generic `CREATED` / `UPDATED` /
`DELETED` row (`IsCurated: No`, `ObjectName: N/A`) is the correct path when no
curated row covers the event, and for a connector that exposes only generic
rows (`uipath-uipath-jdbc`) it is the only path; take its object from
`uip is triggers objects`, which omits connection-specific objects and can
return an empty list without `--connection-id`.

`registry get` returns the node template and its `InputFields`, not the event
schema. That comes from `uip is triggers describe`: build the filter from its
`FilterFields`, never from an activity's `RequestFields`; `EventParameters` are
the trigger's scoping inputs, `OutputFields` the event payload.

The runtime reads only a `target="body"` input; the template's `filter` and
`parameters` fields, and any sibling input without `target`, are dropped. Write one
`body` input as a sibling of `uipath:context`: `queryParams` holds the
`EventParameters`; `filters.expression` AND-joins one equality clause per event
parameter with the `FilterFields` conditions. No filter tree; only the
expression is evaluated.

```xml
<uipath:input name="body" type="json" target="body"><![CDATA[{"filters":{"expression":"(parentFolderId == '<INBOX_ID>') && (contains(subject, 'Invoice'))"},"queryParams":{"parentFolderId":"<INBOX_ID>"}}]]></uipath:input>
```

`uip is triggers` and `registry get` uppercase the operation, so a connector
whose trigger operations are mixed case (`uipath-uipath-testmanager`:
`Created`, `Updated`, `Finished`) returns HTTP 404 / `IS enrichment error` and
has no reachable trigger in CLI 1.204.0.

Curated pairs already confirmed:

| Connector key | Trigger operation | Object |
| --- | --- | --- |
| `uipath-microsoft-outlook365` | `EMAIL_RECEIVED` | `Message` |
| `uipath-atlassian-jira` | `ISSUE_CREATED` | `curated_get_issue` |
| `uipath-salesforce-slack` | `SLACK_EVENT_MESSAGE` | `slack_events_message` |
| `uipath-uipath-dataservice` | `CREATED_V3` | `EntityTriggers_V3` |

A hand-authored connector trigger shell stays **draft** until the CLI supplies
the concrete trigger properties, connection binding, and schemas.

For `Intsvc.EventTrigger` / `Intsvc.WaitForEvent` the connection is referenced
from the node context as **`connectionId`** = `=bindings.<bindingId>` (activities
use `connection`); the timer trigger binds no connection. After authoring the
connection binding, lay the diagram out (`uip maestro bpmn format <file.bpmn>`)
and then run `uip maestro bpmn refresh <project>` so the binding is
materialized into a `Connection` resource in `bindings_v2.json` — a trigger whose
connection is not materialized passes `validate` but faults at runtime with a
null connection (error 102010). Use `refresh`, not the deprecated
`update-metadata`, which does not materialize connection bindings.

## Connectionless vs connector HTTP

- **Connector activity** (`Intsvc.ActivityExecution` / a connector-authenticated
  operation): use when the call goes through a tenant connection, a dynamic
  connector schema, or a connector object operation. Keep the node **draft**
  until enriched. The CLI-owned enrichment blockers — the ones that must be
  resolved before upload or run, and that boundary notes should name explicitly
  — are **connection binding**, **dynamic schemas**, generated **package
  metadata** (`bindings_v2.json`, `entry-points.json`, `operate.json`,
  `package-descriptor.json`). Do not hand-author any of these ([§3](registry-workflow-connector-object.md#3-connector-intsvc-enrichment)).
- **Connectionless / manual HTTP** (`Intsvc.HttpExecution`, or
  `Intsvc.UnifiedHttpRequest` when current tooling exposes the unified shape):
  use when the workflow itself owns the URL, method, payload, and response
  parsing (no connection). Author `mode="manual"`, `method`, `url`, `headers`,
  `parameters`, `body` directly from the registry template.

Status vocabulary for an IS node in a summary: **executable** (activity, inputs,
output variable, and downstream mappings present, runtime-verified if a run was
done), **draft** (BPMN shape/intent present but enrichment missing), **mock**
(returns fixed sample data instead of calling out), **blocked** (a required URL,
auth, schema, or enrichment decision is missing).
