# uipath-byo-llm-connector task tests

Task-tier coverage for the `uipath-byo-llm-connector` skill.

Both tasks build the connector **offline** (`builder init --organization`), so they are hermetic. The tenant steps of the lifecycle (import, publish, connections, the probe run through `uip llm-configuration byo-connections`) need a tenant with BYO custom connectors enabled and a person to enter credentials on the connection page; the e2e task runs them against a disconnected CLI and grades the command shape only.

The build is graded on outcome by `chat-bridge-e2e/check_byo_connector.py`: it reads the generated `element.json` / `element-metadata.json` and, with `--hooks`, executes the connector's own registered preRequest and postRequest hooks in a Node vm against an OpenAI chat-completions body and answers from the fictional Acme Inference API (`chat-bridge-e2e/fixtures/acme-inference-api.md`). A connector passes only if it translates both ways — a task cannot pass because `validate` was invoked.

| Task | Tier | Covers |
|------|------|--------|
| `scaffold-smoke` | smoke | shell only: the flavor path `/v1/chat/completions`, the template tag, the key in `x-api-key`, no secret defaults, `validate` passes, no import |
| `chat-bridge-e2e` | e2e | hooks translating OpenAI chat-completions ↔ Acme (messages, system prompt, limits, finish reasons, usage, error pass-through), then import, publish, a connection on the `custom-` key, and a `--no-enabled` probe with `Custom` + `CustomAiGateway` |

Run the grader by hand against a connector directory:

```bash
python3 tests/tasks/uipath-byo-llm-connector/chat-bridge-e2e/check_byo_connector.py <CONNECTOR_DIR> --hooks
```
