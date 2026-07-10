# Agent Input Schema Validation Failure

Faithful-replay scenario for the `uipath-troubleshoot` skill. It covers an
Agents invocation where the payload omits a required input field.

## What this exercises

The trace contains an `agentRun` span with:

`Input validation failed Details: Data failed json schema validation ... customerEmail Field required`

The local `IntakeAgent/agent.json` declares `customerEmail` as a required
string input. The fixture includes denied `uip agent debug` rules for command
shape coverage; the agent should present the corrected debug command instead of
running a live debug session during diagnosis.

The agent should diagnose a bad caller payload, show a corrected `uip agent
debug --inputs` command, and only suggest editing `agent.json` plus
refresh/validate/upload when the schema itself needs changing.

It must not use deprecated agent run, input-management, or standalone publish
commands.
