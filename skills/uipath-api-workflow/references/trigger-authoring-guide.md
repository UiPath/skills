# Trigger Authoring

Start an API workflow from a connector event — a Slack button click, a new Outlook calendar entry, a new Salesforce record — rather than from an HTTP call or a schedule.

A trigger is an **event subscription**, not a callable activity. It compiles to `call: "UiPath.IntSvcEvent"` and is the workflow's first activity.

## Critical facts

1. **The trigger is the FIRST activity in the root sequence**, immediately after `WorkflowStart`. A workflow has at most one trigger.
<!--skill-flavor:trigger-binding-rule:start-->
2. **`bindings_v2.json` must carry an `EventTrigger` entry, and `uip api-workflow bindings sync` is the command that writes it.** Run it after every trigger add or edit. That entry is what registers the Orchestrator event trigger on deploy. Without it the workflow validates, packs, publishes and deploys clean — and then never fires. Every gate reports success, so nothing else will catch this. It is the most expensive mistake on this page.
<!--skill-flavor:trigger-binding-rule:end-->
3. **Never hand-author a trigger.** Rule 16 applies unchanged: `registry resolve --kind trigger`, then `registry stub`. The `uiPathActivityTypeId` and `metadata.configuration` are not guessable.
<!--skill-flavor:trigger-schedule-scope:start-->
4. **Only connector events are trigger activities here.** A manual run is just invoking the process; a schedule is an Orchestrator trigger on the deployed process (`uip or triggers`). Neither appears in the workflow file. See [operating-published-workflows.md](operating-published-workflows.md).
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

Steps 2 and 4 follow the same rules as any Integration Service activity: a listing is folder-scoped, and `ping` is not optional. See [connector-activity-discovery.md](connector-activity-discovery.md#step-2--verify-a-vendor-connection-intsvc-kind-only).

### Step 1 — resolve the trigger

Triggers live in a **separate TypeCache catalog** from activities: an activity-only search never returns one, and the reverse holds too. `--kind` takes `activity`, `trigger`, or `all` (default).

```bash
uip api-workflow registry resolve "button clicked" --kind trigger --output json
```

<!--skill-flavor:trigger-kind-unavailable:start-->
If `resolve` answers `unknown option '--kind'`, the installed CLI predates trigger support — upgrade it before authoring a trigger. An older `registry stub` cannot emit `UiPath.IntSvcEvent` either, and hand-authoring is not the fallback (fact 3).
<!--skill-flavor:trigger-kind-unavailable:end-->

Every match carries `Kind`. Trigger matches add:

| Field | Meaning |
|---|---|
| `ActivityType` | `CuratedTrigger` (object fixed by the definition) or `GenericTrigger` (you pick the object) |
| `EventOperation` | The connector event — `CREATED`, `BUTTON_CLICKED`, `UPDATED`, … |
| `EventMode` | `polling` or `webhooks` — see [Exercising a trigger before deploy](#exercising-a-trigger-before-deploy) |

The keyword also matches `EventOperation`, so `resolve "button_clicked" --kind trigger` works when you know the event name but not the display name.

### Step 3 — the object, for `GenericTrigger` only

A `CuratedTrigger` pins its object. A `GenericTrigger` applies one event to an object you choose, exactly like a Generic activity — and its TypeCache definition carries no `objectName`, so `stub` fails until `--object-name` supplies one (exact message in [cli-reference.md](cli-reference.md#uip-api-workflow-registry-stub)). Pass the chosen `name` from:

```bash
uip is triggers objects <connector-key> CREATED --connection-id <CONNECTION_UUID> --output json
```

### Steps 4–5 — event parameters and the filter

`uip is triggers describe` reports three groups. Only the first is an input:

| Group | What it is |
|---|---|
| `eventParameters` | Values that **scope the subscription** (which Slack channel, which folder). Supply via `--inputs`; they land in `with.eventParameters`. |
| `filterFields` | Payload fields a **user filter** can test. Not inputs — see [Filter expressions](#filter-expressions). |
| `outputFields` | The event payload downstream activities read. |

```bash
uip api-workflow registry stub <TRIGGER_TYPE_ID> --connection-id <CONNECTION_UUID> \
  --inputs '{"channel_id":"<CHANNEL_ID>"}' --output json
```

`stub` returns `Data.EventParameters` and `Data.FilterFields` alongside the usual `Data.Activity`. Required event parameters you did not supply come back as a warning — heed it, because an unscoped subscription fires on everything.

## The trigger activity shape

```jsonc
{
  "Button_Clicked_1": {
    "call": "UiPath.IntSvcEvent",
    "with": {
      "connector": "uipath-salesforce-slack",
      "connectionId": "<REPLACE_WITH_VENDOR_CONNECTION_UUID>",
      "connectionResourceId": "<REPLACE_WITH_VENDOR_CONNECTION_UUID>",
      "eventParameters": { "channel_id": "<CHANNEL_ID>" },
      "objectName": "button",
      "eventType": "BUTTON_CLICKED",
      "eventMode": "webhooks",
      "filterExpression": "(channel_id == '<CHANNEL_ID>')"
    },
    "export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"button_1\": $output } }" },
    "metadata": {
      "activityType": "Connector",
      "fullName": "Connector",
      "displayName": "Button Clicked",
      "uiPathActivityTypeId": "<REPLACE_WITH_TRIGGER_TYPE_ID>",
      "configuration": "{\"essentialConfiguration\":{...}}"
    }
  }
}
```

Differences from a regular connector activity, all load-bearing:

- `call` is `UiPath.IntSvcEvent`, not `UiPath.IntSvc`.
- No `method`, no `endpoint` — an event has no verb or path. Inside `metadata.configuration`, `httpMethod` and `path` are `null`.
- `instanceParameters.activityType` is `CuratedTrigger` / `GenericTrigger` and carries `eventOperation` + `eventMode`. A `GenericTrigger` omits `instanceParameters.objectName`, keeping the object on the configuration's top level only.
- `eventParameters` values are connector fields: **bare literals**, never `${'...'}`-wrapped — same as `bodyParameters` (rule 16, the inversion of rule 5).
- The slot key keeps the display name's word boundaries — `Button_Clicked_1`, not `ButtonClicked_1` — while the export bucket derives from the object name (`button_1`), so **slot key and export bucket differ**. Read the payload as `$context.outputs.<ExportBucketKey>.content`, using the stub's `Data.ExportBucketKey` verbatim.

Copy-paste skeleton: [../assets/templates/trigger-workflow-template.json](../assets/templates/trigger-workflow-template.json).

## The EventTrigger binding

<!--skill-flavor:trigger-binding-command:start-->
`uip api-workflow bindings sync` writes it, regenerating it on every sync so an edit to the object, event, filter or connection reaches it:

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

In Solutions mode, follow it with `uip solution resources refresh --solution-folder <SOLUTION_DIR>` as for any connector activity (rule 16).
<!--skill-flavor:trigger-binding-command:end-->

> Not generated yet: the companion `Property` binding StudioWeb emits for triggers whose event fields sit in `path` / `query` locations (`design.exposeAsSubBinding`). Most triggers have none. If deployment does not rebind an event parameter per environment, open the workflow once in StudioWeb and let the designer write that entry.

## Filter expressions

`filterExpression` is JMESPath with **two halves joined by `&&`**:

| Half | Source | Who writes it |
|---|---|---|
| Mandatory | The event parameters you supplied | `registry stub`, automatically |
| User | A condition on payload fields (`filterFields`) | You, by hand |

Quote literals the JMESPath way, not the JavaScript way: strings in single quotes (`(channel_id == 'C123')`), booleans and numbers as backtick-wrapped JSON literals (``(isAllDay == `true`)``, ``(count == `3`)``). Double quotes are not JMESPath string literals.

An all-day-only user filter on an Outlook calendar event, combined with its mandatory half:

```
(calendar_id == '<CALENDAR_ID>') && ((isAllDay==`true`))
```

Add the user half by editing `with.filterExpression`; the trigger's registration is regenerated from it (fact 2). Bad quoting does not fail validation — it fails at subscription time, or silently matches nothing.

## Exercising a trigger before deploy

<!--skill-flavor:trigger-local-run:start-->
`uip api-workflow run` behaves differently depending on what you give it:

| Situation | What happens |
|---|---|
| `--input-arguments '<json>'` with data | The trigger **passes the input straight through** as the event payload. No connector call. This is how to exercise the rest of the workflow offline. |
| No input, `eventMode: polling` | Calls Integration Service and **replays the most recent real event** matching the filter. Needs auth and a healthy connection. No match → `"<EVENT>: Trigger activity could not find any matches"`. |
| No input, `eventMode: webhooks` | Cannot be debugged. The run fails by design — a webhook event only arrives from the vendor. |

For a webhooks trigger, always test with `--input-arguments`, shaping the payload like the event's `outputFields`.

> The polling path fires against the **live vendor connection** and consumes a real event. Treat it as a side-effecting run under rule 21 — get the user's consent before looping on it.
<!--skill-flavor:trigger-local-run:end-->

## Anti-patterns

- **Do NOT put the trigger anywhere but first, and do NOT add a second one.** It is the workflow's entry point; an event subscription in the middle of a sequence is meaningless.
- **Do NOT hand-edit `metadata.configuration`** to change the event or object. Re-stub instead — `eventOperation`, `eventMode` and `objectName` appear in several places that must agree.
<!--skill-flavor:trigger-clean-gate-antipattern:start-->
- **Do NOT treat a clean `validate` / `pack` / `publish` / `deploy` as proof the trigger works.** It only proves the workflow is well formed; see fact 2 for the artifact that makes it fire.
<!--skill-flavor:trigger-clean-gate-antipattern:end-->
