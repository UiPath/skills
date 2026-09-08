<!--skill-flavor:ct-configure-command:start-->
uip maestro flow node configure /solution/<FlowProject>/new.flow <triggerId> --output json --detail '{
<!--skill-flavor:ct-configure-command:end-->

<!--skill-flavor:ct-event-node-add:start-->
uip maestro flow node add /solution/<FlowProject>/new.flow uipath.connector.event.<key>.<event> \
<!--skill-flavor:ct-event-node-add:end-->

<!--skill-flavor:ct-bindings:start-->
Trigger nodes require more binding resources than activity nodes: `Connection` + `EventTrigger` + `Property` resources. **`node configure` and the host handle all of these automatically:**

- **Connection bindings** — created in the `.flow` file by `node configure` (Step 6)
- **EventTrigger + Property bindings** — `node configure` writes `bindings_v2.json` in the project directory (`/solution/<FlowProject>/bindings_v2.json`); the host debug reads the saved project directly
<!--skill-flavor:ct-bindings:end-->

<!--skill-flavor:ct-cli-commands:start-->
uip maestro flow node remove /solution/<FlowProject>/new.flow start --output json       # remove manual trigger
uip maestro flow node add /solution/<FlowProject>/new.flow <trigger-node-type> --label "<LABEL>" --position 200,144 --output json
uip maestro flow node configure /solution/<FlowProject>/new.flow <nodeId> --detail '<TRIGGER_DETAIL_JSON>' --output json
<!--skill-flavor:ct-cli-commands:end-->

<!--skill-flavor:ct-testing:start-->
`uip flow debug` works with trigger-based flows (two-token verb — `uip maestro flow debug` is not intercepted and fails in the browser bundle). Debug does **not** wait for a live event — it **pulls the most recent matching event** from the connector's lookback window and executes immediately.
<!--skill-flavor:ct-testing:end-->

<!--skill-flavor:ct-testing-2:start-->
```bash
uip flow debug
# → runs the saved open project (no positional needed; a project NAME selects another project in the solution)
# → fetches the most recent matching event from the past ~1 hour and executes immediately
# → plain-text output: status line, Trace ID, Run logs, Execution trace
```

If it prints `TimedOut after 300s` with `(no run logs emitted)`, ask the user to run Debug from the designer.

<!--skill-flavor:ct-testing-2:end-->

<!--skill-flavor:ct-testing-3:start-->
| Trigger mode | Debug support | Behavior |
|---|---|---|
| `polling` | Supported | Pulls recent events via debug API, executes immediately |
| `webhooks` | **Not supported** | Webhook triggers cannot be tested in debug — publish and fire a real event |

> **If the trigger uses `webhooks` event mode**, tell the user that debug is not available for webhook triggers. Publish the open solution (`uip solution publish --location "<FolderPathOrKey>"`; destination from `uip solution publish --help` PublishLocations) and test with a real webhook event.
<!--skill-flavor:ct-testing-3:end-->

<!--skill-flavor:ct-testing-4:start-->
3. **Check event mode** — if `webhooks`, debug is not supported; inform the user and publish instead
<!--skill-flavor:ct-testing-4:end-->

<!--skill-flavor:ct-debug-tip-bindings:start-->
5. **Bindings are auto-managed** — `node configure` creates flow-level bindings and writes `bindings_v2.json` in the project directory; the host debug reads the saved project directly
<!--skill-flavor:ct-debug-tip-bindings:end-->
