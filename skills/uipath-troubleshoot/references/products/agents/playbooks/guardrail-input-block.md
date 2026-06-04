---
confidence: high
---

# Guardrail Input Block

## Context

What this looks like:
- Agent job faults; `uip agent run status <job-id> --output json` shows `Faulted`
- `uip traces spans get <trace-id> --output json` — two distinct error formats depending on guardrail type:
  - **Custom guardrail block:** JSON format on `toolCall` or `completion` span — `{"detail":"Use of tool was blocked by guardrail [<NAME>], with reason: <REASON>.\nErrorCode:Agent.BaseError\n","error":"..."}`
  - **Built-in validator block** (PII detection, user prompt attacks, etc.): plain text on `llmPreGuardrails` or `guardrailEvaluation` span — `Guardrail violation Details: Execution was blocked by guardrail [<NAME>], with reason: <REASON> Code: AGENT_RUNTIME.TERMINATION_GUARDRAIL_VIOLATION`
- Blocking point depends on guardrail scope — `Agent` scope fires before any LLM call; `Llm` and `Tool` scope may fire after one or more LLM calls complete
- Guardrail name appears in the error string

> **Distinct error shape:** If the error is `"User is forbidden by governance policy to use: <model>"` (`StatusCode 403`, `ErrorCode 3000`), this is an Automation Ops model-restriction policy, not a custom input guardrail rule. Check the effective policy via CLI: `uip gov aops-policy deployed-policy get <license-type> AITrustLayer <tenant-id> --output json`. Or navigate to Automation Ops → Policies → Model Restrictions in the portal.

What can cause it:
- Custom input guardrail rule matches a keyword or pattern in the invocation payload — overly broad rule blocks legitimate input
- Built-in OOB validator (PII detection, harmful content, prompt injection, user prompt attacks) matches content in the invocation payload — these run automatically when enabled and do not require custom rules
- Guardrail policy was recently tightened and now catches previously accepted inputs
- Test or debug payloads contain terms that accidentally match a production guardrail rule
- Invocation payload contains structured data (JSON, user-submitted text) overlapping with a prohibited pattern
- Guardrail action is set to `Filter` — `Filter` removes the specified fields from the payload; execution continues. Agent may behave unexpectedly if required fields are stripped.

What to look for:
- Guardrail name in the error string (in brackets: `[<NAME>]`) — identifies which guardrail fired. Matched rule details (word pattern, PII entity, threshold) are on the `guardrailEvaluation` span, not in the error string
- Absence of `completion` spans — confirms the block happened before the LLM call (input guardrail, not output)
- Whether the block is consistent (every invocation with that input) vs intermittent (only some) — consistent means the rule is too broad

## Investigation

1. Get the job trace ID:

   ```bash
   uip agent run status <job-id> --output json \
     --output-filter "traceId"
   ```

2. Pull spans and identify the blocking span and layer:

   ```bash
   uip traces spans get <trace-id> --output json \
     --output-filter "spans[?attributes.error != null].{spanType: spanType, error: attributes.error, name: name}"
   ```

   - Identify the blocking span type from the results above. `toolPostGuardrails` → output violation (see [guardrail-output-violation](guardrail-output-violation.md)). `llmPreGuardrails` or `toolGuardrailEvaluation` → input block at LLM or tool scope. Presence of `completion` spans alone does not rule out an input block.
3. Extract the guardrail name from the error:

   ```bash
   uip traces spans get <trace-id> --output json \
     --output-filter "spans[?attributes.error != null].attributes.error"
   ```

   The error string contains a guardrail block indicator followed by the guardrail name or rule ID.

4. Inspect the triggering rule via CLI:

   ```bash
   uip agent guardrails list --output json \
     --output-filter "[?contains(Validator, '<guardrail-name>')].{validator: Validator, scopes: AllowedScopes, stages: GuardrailStages, status: Status}"
   ```

   Then fetch the catalog entry for the validator:

   ```bash
   uip agent guardrails catalog --validator <validator-id> --output json
   ```

   For OOB guardrails: catalog response includes descriptions, security category, when-to-use guidance, and validator parameters.

   For custom guardrails: catalog shows metadata only — actual rule logic (word patterns, number thresholds) lives in the agent definition. Inspect via:

   ```bash
   uip agent config get guardrails --path <PROJECT_DIR> --output json
   ```

   Or open `agent.json` directly from the project directory.

5. Determine whether the block is a **legitimate enforcement** or a **false positive**:
   - Legitimate: the input contains prohibited content (PII, prompt injection attempt, policy violation)
   - False positive: the input is valid but matches an overly broad pattern (e.g., a common business term in the prohibited list)

> **If the job runs without blocking when it should:** If the custom guardrail condition is misconfigured (wrong field name, invalid expression), it silently passes all inputs. Verify the rule condition syntax in AgentBuilder or Flow — confirm it references the correct input field name.

## Resolution

**If the input legitimately violates the guardrail:**
- Fix the caller: ensure the invocation payload does not contain prohibited patterns before sending
- If the agent is user-facing, add system prompt instructions to pre-screen or rephrase inputs before tool calls

**If the guardrail rule is too broad — narrow it:**
- For custom and OOB guardrails: open the agent in AgentBuilder or Flow → Guardrails → select the triggering rule → edit pattern
- For centralized guardrails enforced by a tenant admin: navigate to Automation Ops → Governance → AI Trust Layer → find the policy by name from step 3
- Replace the overly broad expression with a more specific match
- Re-test by re-invoking the agent with the previously blocked input

**If a recent policy change caused regressions — roll back:**
- Identify the rule change date from the last-modified timestamp in AgentBuilder or Flow (custom guardrails) or Automation Ops → Governance → AI Trust Layer (centralized guardrails)
- Restore the prior rule definition or disable the rule while reviewing scope
- Document the rollback and review with the team that owns the guardrail policy
