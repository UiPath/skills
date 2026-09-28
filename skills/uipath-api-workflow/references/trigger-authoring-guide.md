# Trigger Authoring

Start an API workflow from a connector event (a Slack button clicked, a new Outlook calendar entry, a new Salesforce record). The trigger is an event subscription, not a callable activity: `call: "UiPath.IntSvcEvent"`, first after `WorkflowStart`.

## Rules

1. **One trigger, first after `WorkflowStart`.** Never place it elsewhere or add a second one.
<!--skill-flavor:trigger-binding-rule:start-->
2. **Run `uip api-workflow bindings sync` after every trigger add or edit.** It writes the `EventTrigger` entry in `bindings_v2.json` that registers the subscription on deploy. Without it the workflow validates, packs, publishes and deploys clean, and never fires. No gate catches this.
<!--skill-flavor:trigger-binding-rule:end-->
3. **Never hand-author a trigger.** `registry resolve --kind trigger`, then `registry stub` (rule 16). Use the stub output verbatim. To change the event or object, re-stub; do not edit `metadata.configuration`.
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

Triggers live in a separate TypeCache catalog; `--kind` takes `activity`, `trigger`, or `all` (default). The keyword also matches `EventOperation`, so `resolve "button_clicked" --kind trigger` works. Each trigger match carries `ActivityType` (`CuratedTrigger` pins its object; `GenericTrigger` needs `--object-name`), `EventOperation` (`CREATED`, `BUTTON_CLICKED`, …) and `EventMode` (`polling` or `webhooks`).

<!--skill-flavor:trigger-kind-unavailable:start-->
If `resolve` answers `unknown option '--kind'`, the installed CLI predates trigger support — upgrade it. Hand-authoring is not the fallback (rule 3).
<!--skill-flavor:trigger-kind-unavailable:end-->

## Event parameters

`uip is triggers describe` returns three groups. Only the first is an input.

- `eventParameters` scope the subscription (which channel, which folder). Pass them with `--inputs`.
- `filterFields` are payload fields a user filter can test.
- `outputFields` are the event payload downstream activities read.

`stub` echoes `Data.EventParameters` and `Data.FilterFields`. A required parameter you did not supply comes back as a warning. Heed it: an unscoped subscription fires on everything.

## Reading the payload

Downstream activities read `$context.outputs.<ExportBucketKey>.content`, using the stub's `Data.ExportBucketKey` verbatim. Skeleton: [../assets/templates/trigger-workflow-template.json](../assets/templates/trigger-workflow-template.json).

## The EventTrigger binding

<!--skill-flavor:trigger-binding-command:start-->
`uip api-workflow bindings sync` derives it from the trigger's `with` clause and regenerates it on every sync. After syncing, check `bindings_v2.json` for one `resource: "EventTrigger"` entry whose `key` is the connection UUID and whose `metadata.ObjectName` / `Operation` / `FilterExpression` match `with.objectName` / `eventType` / `filterExpression`. Event parameters the connector registers with (typically path and query fields) also get a `Property` entry under it. In Solutions mode follow with `uip solution resources refresh --solution-folder <SOLUTION_DIR>` (rule 16).
<!--skill-flavor:trigger-binding-command:end-->

## Filter expression

`with.filterExpression` is JMESPath in two halves joined by ` && `: the mandatory half, which `stub` writes from the event parameters, and an optional user half you write against `filterFields`.

- Quote by field type: strings in single quotes, booleans and numbers as backtick literals — `(channel_id == 'C123') && (isAllDay == \`true\`)`. Double quotes are identifiers in JMESPath, not strings.
- An array field (its name contains `[*]`) is matched with a projection, not `==`: `ParentFolders[?ID=='INBOX']`. `stub` writes a plain comparison for such a field; replace it.
- Bad quoting passes `validate` and fails at subscription time or matches nothing.
- Editing `filterExpression` is a trigger edit (rule 2).

## Exercising a trigger before deploy

<!--skill-flavor:trigger-local-run:start-->
| `uip api-workflow run` | Result |
|---|---|
| `--input-arguments '<json>'` | The trigger passes the input through as the event payload; no connector call. Shape it like `outputFields`. |
| No input, `eventMode: polling` | Reads the latest matching event from the live connection (needs auth, healthy connection). No match → `"<EVENT>: Trigger activity could not find any matches"`. Side-effecting under rule 21. |
| No input, `eventMode: webhooks` | Fails by design; the event only arrives from the vendor. Use `--input-arguments`. |
<!--skill-flavor:trigger-local-run:end-->

<!--skill-flavor:trigger-clean-gate-antipattern:start-->
A clean `validate` / `pack` / `publish` / `deploy` is not proof the trigger fires. Only the `EventTrigger` binding does that (rule 2).
<!--skill-flavor:trigger-clean-gate-antipattern:end-->
