<!--skill-flavor:trigger-binding-rule:start-->
2. **Studio Web owns the trigger's deployment registration.** It derives the `EventTrigger` binding from the saved workflow; treat host-generated bindings and solution resources as authoritative (rule 16). Keep the trigger first and its `objectName` / `eventType` / `eventMode` / `filterExpression` accurate. After saving, confirm the activity renders as a **trigger card** — a plain connector card means wrong event metadata, and the derived registration is equally wrong. Re-stub to correct it.
<!--skill-flavor:trigger-binding-rule:end-->

<!--skill-flavor:trigger-schedule-scope:start-->
4. **Only connector events live in the workflow file.** A schedule is an Orchestrator trigger on the deployed process, managed outside the workflow. See [operating-published-workflows.md](operating-published-workflows.md).
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
If `resolve` answers `unknown option '--kind'`, the embedded CLI predates trigger support. Report that host capability gap and ask how the user wants to proceed — hand-authoring is not the fallback (fact 3).
<!--skill-flavor:trigger-kind-unavailable:end-->

<!--skill-flavor:trigger-binding-command:start-->
Studio Web writes it from the saved workflow, including the `Property` companion for path/query event parameters. Treat host-generated bindings and solution resources as authoritative (rule 16). After saving, confirm the activity renders as a **trigger card**; re-stub if it renders as a plain connector card.
<!--skill-flavor:trigger-binding-command:end-->

<!--skill-flavor:trigger-local-run:start-->
Run through the consent-gated, schema-inspected `RunProject` host operation:

| Input | Result |
|---|---|
| Execution input shaped like `outputFields` | The trigger passes it through as the event payload; no connector call. The safe way to exercise the body. |
| No input | The runtime fetches a recent matching event through the live connection: always for `polling`; for `webhooks` only when the connector has a debug-polling configuration, otherwise it fails with publish guidance. Reaches the vendor — side-effecting under rule 21. |

Studio Web's **Test trigger** panel checks filter matches against recent events without running the workflow. Offline `uip api-workflow validate` stays the autonomous pre-flight.
<!--skill-flavor:trigger-local-run:end-->

<!--skill-flavor:trigger-clean-gate-antipattern:start-->
- **Treat a clean `uip api-workflow validate` as proof the file is well formed, and only that.** The subscription follows from the saved trigger activity (fact 2), so re-read it before calling the work done.
<!--skill-flavor:trigger-clean-gate-antipattern:end-->
