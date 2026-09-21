<!--skill-flavor:trigger-binding-rule:start-->
2. **Studio Web owns the trigger's deployment registration.** The host derives it from the saved workflow, so treat the host-generated bindings and solution resources as authoritative (rule 16). You own the workflow side: keep the trigger first, and keep its `objectName` / `eventType` / `eventMode` / `filterExpression` accurate. After saving, confirm the activity renders as a **trigger card** — a plain connector card signals wrong event metadata, and what the host derives from it will be equally wrong. Re-stub to correct it.
<!--skill-flavor:trigger-binding-rule:end-->

<!--skill-flavor:trigger-schedule-scope:start-->
4. **Connector events are the only trigger activities that live in the workflow file.** A manual run is the process being invoked; a schedule is an Orchestrator trigger on the deployed process, managed outside the workflow file. See [operating-published-workflows.md](operating-published-workflows.md).
<!--skill-flavor:trigger-schedule-scope:end-->

<!--skill-flavor:trigger-authoring-steps:start-->
1. `uip api-workflow registry resolve "<KEYWORD>" --kind trigger --output json` → trigger type id
2. `uip is connections list <connector-key> --output json` → connection UUID, then `uip is connections ping <CONNECTION_UUID> --output json` — REQUIRED
3. `GenericTrigger` only: `uip is triggers objects <connector-key> <EVENT> --connection-id <CONNECTION_UUID> --output json` → object name
4. `uip is triggers describe <connector-key> <EVENT> <OBJECT> --connection-id <CONNECTION_UUID> --output json` → event parameters
5. `uip api-workflow registry stub <TRIGGER_TYPE_ID> --connection-id <CONNECTION_UUID> [--object-name <OBJECT>] [--inputs '<json>'] --output json`
6. Insert `Data.Activity` as the first entry after `WorkflowStart` in `/solution/<projectName>/Workflow.json` and save.
7. From that project directory, `uip api-workflow validate Workflow.json --output json` until `Data.Status` is `Valid`.
<!--skill-flavor:trigger-authoring-steps:end-->

<!--skill-flavor:trigger-kind-unavailable:start-->
If `resolve` answers `unknown option '--kind'`, the embedded CLI predates trigger support. Report that exact host capability gap and ask how the user wants to proceed — the `uiPathActivityTypeId` and `metadata.configuration` still come from `stub` alone (fact 3).
<!--skill-flavor:trigger-kind-unavailable:end-->

<!--skill-flavor:trigger-binding-command:start-->
Studio Web writes it, derived from the saved workflow. Treat the host-generated bindings and solution resources as authoritative (rule 16).

You own the workflow side. After saving, confirm the activity renders as a **trigger card**: a plain connector card signals wrong event metadata, and what the host derives from it will be equally wrong. Re-stub to correct it.
<!--skill-flavor:trigger-binding-command:end-->

<!--skill-flavor:trigger-local-run:start-->
A subscription fires only from the vendor, so a pre-deploy check supplies the payload itself:

| `eventMode` | How to exercise it |
|---|---|
| `webhooks` | Supply the event payload as the execution input through the consent-gated, schema-inspected `RunProject` host operation, shaped like the event's `outputFields`. The trigger passes it straight through; the rest of the workflow runs on it. |
| `polling` | The same input-supplied path applies. With no input the trigger replays the most recent real matching event, which reaches the live vendor connection and is therefore side-effecting under rule 21 — get the user's consent first. |

Offline `uip api-workflow validate` stays the autonomous pre-flight either way.
<!--skill-flavor:trigger-local-run:end-->

<!--skill-flavor:trigger-clean-gate-antipattern:start-->
- **Treat a clean `uip api-workflow validate` as proof the workflow is well formed, and only that.** Whether the deployed process subscribes to the intended event follows from the saved trigger activity (fact 2), so re-read it before calling the work done.
<!--skill-flavor:trigger-clean-gate-antipattern:end-->
