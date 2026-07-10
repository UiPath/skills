# Agent LLM Insufficient Information

Faithful-replay scenario for the `uipath-troubleshoot` skill. It covers an
Agents runtime failure where a completion span returns a JSON error whose
`detail` says the recipient is missing.

## What this exercises

The trace contains a failing `completion` span with:

`{"detail":"Insufficient information to send the email: recipient is missing"}`

The local agent prompt says only "Send the requested email update" and the
input schema has a single `task` field. The agent should identify that the
system prompt and/or programmatic input schema does not force the caller to
provide a recipient.

The expected fix is to edit `agent.json` directly: update
`messages[0].content`, rebuild `contentTokens`, add an input field such as
`recipient` when programmatic calls need it, then run refresh/validate and
solution upload. Local reproduction should be presented as a `uip agent debug`
command and run only after explicit user approval, because debug uploads and
executes the agent.
