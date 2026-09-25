# Trigger Authoring

Start an API workflow from a connector event (Slack button click, new Outlook calendar entry, new Salesforce record). A trigger is an event subscription, not a callable activity: `call: "UiPath.IntSvcEvent"`, first activity after `WorkflowStart`.

## Critical facts

1. **The trigger is the FIRST activity after `WorkflowStart`, and there is at most one.** Studio Web inserts it at that slot and offers "Add trigger" only while none exists.
<!--skill-flavor:trigger-binding-rule:start-->
2. **`bindings_v2.json` must carry an `EventTrigger` entry; `uip api-workflow bindings sync` writes it.** Run it after every trigger add or edit. That entry registers the Orchestrator event trigger on deploy. Without it the workflow validates, packs, publishes and deploys clean — and never fires. No gate catches this.
<!--skill-flavor:trigger-binding-rule:end-->
3. **Never hand-author a trigger.** `registry resolve --kind trigger`, then `registry stub` (rule 16). `uiPathActivityTypeId` and `metadata.configuration` are not guessable.
<!--skill-flavor:trigger-schedule-scope:start-->
4. **Only connector events live in the workflow file.** A schedule is an Orchestrator trigger on the deployed process (`uip or triggers`); a manual run is just invoking it. See [operating-published-workflows.md](operating-published-workflows.md).
<!--skill-flavor:trigger-schedule-scope:end-->

## Authoring flow

<!--skill-flavor:trigger-authoring-steps:start-->
1. `uip api-workflow registry resolve "<KEYWORD>" --kind trigger --output json` → trigger type id
2. `uip is connections list <connector-key> --output json` → connection UUID, then `uip is connections ping <CONNECTION_UUID> --output json` — REQUIRED
3. `GenericTrigger` only: `uip is triggers objects <connector-key> <EVENT> --connection-id <CONNECTION_UUID> --output json` → object name
4. `uip is triggers describe <connector-key> <EVENT> <OBJECT> --connection-id <CONNECTION_UUID> --output json` → event parameters
5. `uip api-workflow registry stub <TRIGGER_TYPE_ID> --connection-id <CONNECTION_UUID> [--object-name <OBJECT>] [--inputs '<json>'] --output json`
6. Insert `Data.Activity` as the first entry after `WorkflowStart`.
7. `uip api-workflow bindings sync --workflow <WORKFLOW_PATH> --output json`
8. `uip api-workflow validate <WORKFLOW_PATH> --output json`
<!--skill-flavor:trigger-authoring-steps:end-->

Connection rules (folder-scoped listing, `ping` mandatory) are the same as for any connector activity: [connector-activity-discovery.md](connector-activity-discovery.md#step-2--verify-a-vendor-connection-intsvc-kind-only).

### Resolve

Triggers live in a separate TypeCache catalog. `--kind` takes `activity`, `trigger`, or `all` (default). The keyword also matches `EventOperation`, so `resolve "button_clicked" --kind trigger` works.

<!--skill-flavor:trigger-kind-unavailable:start-->
If `resolve` answers `unknown option '--kind'`, the installed CLI predates trigger support — upgrade it. Hand-authoring is not the fallback (fact 3).
<!--skill-flavor:trigger-kind-unavailable:end-->

Trigger matches carry `ActivityType` (`CuratedTrigger` pins its object; `GenericTrigger` needs `--object-name`), `EventOperation` (`CREATED`, `BUTTON_CLICKED`, …) and `EventMode` (`polling` / `webhooks`).

### Event parameters and filter

`uip is triggers describe` reports three groups; only the first is an input:

| Group | Meaning |
|---|---|
| `eventParameters` | Scope the subscription (which channel, which folder). Supply via `--inputs`. The stub routes each by IS location: `path`/`query` → `with.pathParameters` / `with.queryParameters`; the rest → `with.eventParameters` and the mandatory filter. |
| `filterFields` | Payload fields a user filter can test. Not inputs. |
| `outputFields` | The event payload downstream activities read. |

`stub` returns `Data.EventParameters` and `Data.FilterFields`. A required parameter not supplied comes back as a warning — heed it; an unscoped subscription fires on everything.

## The trigger activity

Skeleton: [../assets/templates/trigger-workflow-template.json](../assets/templates/trigger-workflow-template.json). Differences from a connector activity, all load-bearing:

- `call: "UiPath.IntSvcEvent"`; no `method`/`endpoint`; `with.eventType` holds the event operation, `with.eventMode` is `polling` or `webhooks`.
- `instanceParameters.activityType` is `CuratedTrigger` / `GenericTrigger` with `eventOperation` + `eventMode`; `httpMethod` and `path` are `null`. A `GenericTrigger` omits `instanceParameters.objectName`.
- Parameter values are bare literals, never `${'...'}`-wrapped (rule 16).
- Slot key keeps display-name word boundaries (`Button_Clicked_1`); the export bucket derives from the object (`button_1`). Read the payload as `$context.outputs.<ExportBucketKey>.content`, using the stub's `Data.ExportBucketKey` verbatim.

## The EventTrigger binding

<!--skill-flavor:trigger-binding-command:start-->
`uip api-workflow bindings sync` writes it and regenerates it on every sync, so an edit to object, event, filter or connection reaches it:

```json
{
  "resource": "EventTrigger",
  "key": "<CONNECTION_UUID>",
  "activityId": "Button_Clicked_1",
  "activityDisplayName": "Button Clicked",
  "value": { "ConnectionId": { "defaultValue": "<CONNECTION_UUID>", "isExpression": false } },
  "metadata": {
    "UseConnectionService": "true",
    "Connector": "uipath-salesforce-slack",
    "ActivityName": "Button Clicked",
    "BindingsVersion": "2.2",
    "ObjectName": "button",
    "Operation": "BUTTON_CLICKED",
    "FilterExpression": "(channel_id == '<CHANNEL_ID>')",
    "SolutionsSupport": "true"
  }
}
```

Path/query event parameters get a companion `Property` entry (`key` = event operation, `ParentResourceKey: "EventTrigger.<CONNECTION_UUID>"`), also regenerated. In Solutions mode follow with `uip solution resources refresh --solution-folder <SOLUTION_DIR>` (rule 16).
<!--skill-flavor:trigger-binding-command:end-->

## Filter expression

`filterExpression` is JMESPath: mandatory half (from event parameters, written by `stub`) `&&` user half (a condition on `filterFields`, written by you). Quoting follows the field type: strings single-quoted, booleans and numbers backtick JSON literals — `(channel_id == 'C123') && (isAllDay == \`true\`)`. Double quotes are not JMESPath string literals. Bad quoting passes `validate` and fails at subscription time or matches nothing. Editing `with.filterExpression` is a trigger edit (fact 2).

## Exercising a trigger before deploy

<!--skill-flavor:trigger-local-run:start-->
| `uip api-workflow run` | Result |
|---|---|
| `--input-arguments '<json>'` | The trigger passes the input through as the event payload; no connector call. Shape it like `outputFields`. |
| No input, `eventMode: polling` | Reads the latest matching event from the live connection (needs auth, healthy connection). No match → `"<EVENT>: Trigger activity could not find any matches"`. Side-effecting under rule 21. |
| No input, `eventMode: webhooks` | Fails by design; the event only arrives from the vendor. Use `--input-arguments`. |
<!--skill-flavor:trigger-local-run:end-->

## Anti-patterns

- **Do NOT place the trigger anywhere but first, or add a second one.**
- **Do NOT hand-edit `metadata.configuration`** to change event or object — re-stub; `eventOperation`, `eventMode`, `objectName` must agree across `with` and the blob.
<!--skill-flavor:trigger-clean-gate-antipattern:start-->
- **Do NOT treat a clean `validate` / `pack` / `publish` / `deploy` as proof the trigger fires.** Only the `EventTrigger` binding does that (fact 2).
<!--skill-flavor:trigger-clean-gate-antipattern:end-->
