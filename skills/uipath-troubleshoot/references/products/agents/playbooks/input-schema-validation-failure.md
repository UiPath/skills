---
confidence: high
---

# Input Schema Validation Failure

## Context

What this looks like:
- Agent job faults at startup; `uip agent run status <jobId> --output json` shows `Faulted`
- `uip traces spans get <traceId> --output json` contains an `agentRun` span whose `ATTRIBUTES.error` matches one of two variants:

  **Variant A — agent configuration schema:**
  ```
  Agent configuration invalid Details: ... agent.json failed schema validation: 1 validation error for AgentDefinition <field-path>
  ```

  **Variant B — input payload schema:**
  ```
  Input validation failed Details: Data failed json schema validation: 1 validation error for DynamicType_0 BatchJson <field-name>
    <type-error> [type=<type_code>, input_value=...]
  ```

What can cause it:
- **Variant A:** `agent.json` contains a field with the wrong type — e.g., a string value where an object is expected (`folderPathPrefix`, `escalation.channels`). Usually introduced after a manual edit or a failed schema migration.
- **Variant B:** The input payload passed to `uip agent run start` (or the caller API) omits a required field or passes a wrong type — e.g., a dict where a string is expected, or a missing required key.

What to look for:
- The error names the exact field path (`resources.0.context.settings.folderPathPrefix`) and the type mismatch — use this to locate the offending value immediately
- Variant A faults before any LLM call (the agent never starts); Variant B faults at invocation time

## Investigation

1. Get the job trace ID:

   ```bash
   uip agent run status <jobId> --output json \
     --output-filter "traceId"
   ```

2. Pull the failing `agentRun` span error:

   ```bash
   uip traces spans get <traceId> --output json \
     --output-filter "spans[?spanType == 'agentRun'].attributes.error"
   ```

3. Determine the variant from the error prefix:
   - `Agent configuration invalid` → **Variant A** — `agent.json` is misconfigured
   - `Input validation failed` → **Variant B** — caller passed a bad payload

4. **Variant A only** — validate the agent project locally:

   ```bash
   uip agent validate --output json
   ```

   The validator names the same field path as the span error. Confirm the offending field and its current value in `agent.json`.

5. **Variant B only** — the error names the exact offending field and type mismatch inline (e.g., `Field required [type=missing, ...]` or `Input should be a valid string [type=string_type, ...]`). Use the field name from the error directly — no need to diff the full schema.

## Resolution

**Variant A — fix `agent.json`:**
- Open `agent.json` and locate the field named in the error (e.g., `resources[0].context.settings.folderPathPrefix`)
- Correct the value to match the expected type (the error states `Input should be an object` / `Input should be a valid string` etc.)
- Re-validate before republishing:

  ```bash
  uip agent validate --output json
  uip agent publish --output json
  ```

**Variant B — fix the input payload:**
- If a required field is missing: add it to the invocation call or the `uip agent run start` arguments
- If a field has the wrong type: correct the type to match the schema (e.g., pass a plain string instead of a dict)
- If the schema itself needs updating to match new caller expectations — add or modify the input parameter:

  ```bash
  uip agent input add --name "<paramName>" --type string --output json
  uip agent publish --output json
  ```

- Re-invoke with the corrected payload:

  ```bash
  uip agent run start --agent-name "<name>" --folder-id <id> \
    --input '{"<paramName>": "<value>"}' --output json
  ```
