---
confidence: medium
---

# LLM Call Failed — Insufficient Information in Prompt

## Context

What this looks like:
- A deployed agent job or `uip agent debug` run faults mid-run
- `uip traces spans get <trace-id> --output json` contains a span with `SPANTYPE: completion` or `agentRun` whose `ATTRIBUTES.error` is a JSON string starting with `{"detail":"Insufficient information..."}` or `{"detail":"Insufficient information to <action>..."}`
- The error detail names a missing piece of context: recipient, topic, date range, scope, etc.

What can cause it:
- Agent system prompt is too open-ended — the LLM cannot infer required parameters from the user's message alone
- User invocation omits a required input field that the agent's instructions assume will be present
- Agent is invoked programmatically with a sparse or template payload that lacks inline context
- The agent's task description tells the LLM to perform an action but provides no data to act on

What to look for:
- The `detail` field in the error JSON names the missing information — use this to identify whether it is a prompt design issue or a caller input issue
- Whether the failure is consistent (every invocation) vs. intermittent (some inputs work) — consistent means the system prompt is the root cause; intermittent means the input payload varies

## Investigation

1. Get the spans for the failing run. If you already have a trace ID, use it directly. If you only have an Orchestrator job key, resolve it through traces:

   ```bash
   uip traces spans get <trace-id> --output json

   # or
   uip traces spans get --job-key <job-key> --folder-path "<folder-path>" --output json
   ```

2. Pull spans and find the failing `completion` or `agentRun` span:

   ```bash
   uip traces spans get <trace-id> --output json \
     --output-filter "spans[?attributes.error != null].{name: name, spanType: spanType, error: attributes.error}"
   ```

3. Parse the `error` field — it is a JSON string. Extract the `detail` value:

   ```bash
   uip traces spans get <trace-id> --output json \
     --output-filter "spans[?attributes.error != null].attributes.error" \
     | jq -r '.[] | fromjson | .detail'
   ```

   The detail names the missing information (e.g., `"The request does not specify which releases or their scope"`).

4. Determine whether the missing context should come from the **system prompt** or the **caller's input**:
   - If the missing info is structural (always required for the agent's purpose) → system prompt issue
   - If the missing info varies per invocation (e.g., a recipient, a date) → input schema issue

## Resolution

**If the system prompt is too vague — improve it:**
- Edit `agent.json` → `messages[0].content` and rebuild its `contentTokens`: add explicit instructions covering the missing context named in the `detail` field; add constraints or clarification prompts (e.g., "If the user does not specify X, ask for clarification before proceeding")
- Refresh and validate the agent:

  ```bash
  uip agent refresh "<AGENT_PROJECT_DIR>" --output json
  uip agent validate "<AGENT_PROJECT_DIR>" --output json
  ```

- After successful validation, report the result and ask whether the user wants to upload the corrected solution to Studio Web or publish/deploy it to Orchestrator. Do not perform any delivery action without explicit approval.

**If a required input is missing from the caller's payload:**
- Inspect the declared input schema: open `agent.json` locally, check `inputSchema`
- If the parameter exists but the caller omitted it — fix the caller or add a default in the schema
- If the parameter does not exist in the schema — add it directly to `agent.json` → `inputSchema.properties`; add the field name to `inputSchema.required` only when every invocation must provide it. Then refresh and validate so `entry-points.json` is regenerated:

  ```bash
  uip agent refresh "<AGENT_PROJECT_DIR>" --output json
  uip agent validate "<AGENT_PROJECT_DIR>" --output json
  ```

  After successful validation, report the result and ask whether the user wants to upload or publish/deploy the corrected solution. Do not perform any delivery action without explicit approval.

**If the agent is invoked with a sparse programmatic payload:**
- Ensure all required `inputSchema` fields are populated before calling the deployed agent/API, or before local reproduction with `uip agent debug <AGENT_PROJECT_DIR> --inputs '<json>' --output json`
- Run `uip agent debug` only after explicit user approval because it uploads the enclosing solution and executes the agent; otherwise provide the command for the user to run
- Pass missing context as inline input arguments rather than relying on the LLM to infer them
- A payload-only correction does not require publishing or deploying the agent project
