# Build plan — ConnectorSpliceCase

Phase 1 and Phase 2 are already done: the solution, the case, the stage, the
conditions, and the connector task's Phase 2 shape are all on disk. Only the
Phase 3 connector splice (T04) is outstanding.

## T04: Add connector-activity task "Post Slack message" to "Notify"
- type-id: 37a305b2-89b1-315d-b73f-1778839a6c47
- connection-id: e03f734e-0f80-4e8a-a7c1-0ece309b0ca4
- connector-key: uipath-salesforce-slack
- object-name: send_message_to_channel_v2
- input-values: {"bodyParameters":{"channel":"#general","messageToSend":"Case started"},"queryParameters":{"send_as":"bot"}}
- isRequired: true
- runOnlyOnce: false
- activation-mode: parallel
- entry-rule: current-stage-entered
- rationale: "Single connector activity; independent work that starts with the stage."
- order: after T03
- lane: 0
- verify: task carries the spliced caseShape context, inputs, and outputs with binding placeholders substituted and root bindings appended
