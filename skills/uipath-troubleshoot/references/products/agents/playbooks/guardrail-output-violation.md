---
confidence: high
---

# Guardrail Output Violation

## Context

What this looks like:
- Agent job faults after one or more LLM calls; `uip agent run status <job-id> --output json` shows `Faulted`
- `uip traces spans get <trace-id> --output json` contains an `agentRun` span whose `ATTRIBUTES.error` contains:
  ```
  AGENT_RUNTIME.TERMINATION_GUARDRAIL_VIOLATION
  ```
- At least one `completion` span precedes the faulting `agentRun` span — the LLM ran and returned output
- The guardrail was configured with action **Block** — this error code does not fire for Log-only or HITL guardrail actions
- Agent execution also terminates if a guardrail with `escalate` action fires and the assigned Action Center reviewer rejects the task — produces the same `AGENT_RUNTIME.TERMINATION_GUARDRAIL_VIOLATION` error; check the `escalationTool` span in the trace

> **Distinct error shape:** If the trace shows `PROVIDER_ERROR: "Error during <provider> API call."`, the guardrail provider was unreachable — that is NOT a `TERMINATION_GUARDRAIL_VIOLATION`. The violation code means the provider successfully evaluated the output and returned a block verdict.

> **Trace UI note:** Read the `agentRun` span error field directly via CLI — the guardrail evaluation span may appear loading in the trace UI even after output is rendered (evaluation runs asynchronously).

What can cause it:
- LLM-generated response matched a prohibited pattern in an output guardrail rule
- System prompt does not constrain output format or content, allowing responses that trigger guardrail rules
- A guardrail rule was recently added or tightened and now conflicts with valid LLM output formats (e.g., structured JSON fields containing terms the rule prohibits)
- LLM responded to an adversarial user prompt and generated prohibited content
- Guardrail action was recently changed from HITL (creates human review task) to Block (faults the job) — behavior change is immediate and silent

What to look for:
- Presence of `completion` spans before the `agentRun` fault and a `toolPostGuardrails` span with error — confirms this is an output violation. For input blocks at LLM or tool scope, `completion` spans may also exist; use the blocking span type to distinguish.
- The LLM output text in the preceding `completion` span — identifies exactly which content triggered the rule
- The guardrail name in the error — identifies which rule fired and its scope (`Output`)

## Investigation

1. Get the job trace ID:

   ```bash
   uip agent run status <job-id> --output json \
     --output-filter "traceId"
   ```

2. Confirm `completion` spans precede the fault:

   ```bash
   uip traces spans get <trace-id> --output json \
     --output-filter "spans[?spanType == 'completion' || spanType == 'agentRun'].{spanType: spanType, startTime: startTime, error: attributes.error}"
   ```

   Verify at least one `completion` span has an earlier `startTime` than the faulting `agentRun` span. If a `toolPostGuardrails` span carries the error, this is an output violation. If `llmPreGuardrails` or `toolGuardrailEvaluation` carries the error instead, this is an input block at LLM or tool scope — see [guardrail-input-block](guardrail-input-block.md).

3. Extract the guardrail name and violation details from the `agentRun` error:

   ```bash
   uip traces spans get <trace-id> --output json \
     --output-filter "spans[?spanType == 'agentRun'].attributes.error"
   ```

   The error contains the guardrail name and `AGENT_RUNTIME.TERMINATION_GUARDRAIL_VIOLATION`.

4. Retrieve the LLM output from the preceding `completion` span to identify what triggered the rule:

   ```bash
   uip traces spans get <trace-id> --output json \
     --output-filter "spans[?spanType == 'completion'].attributes"
   ```

   Inspect the response content field — identify the phrase, pattern, or data structure that matched the output guardrail rule.

5. Inspect the triggering rule via CLI:

   ```bash
   uip agent guardrails list --output json \
     --output-filter "[?contains(Validator, '<guardrail-name>')].{validator: Validator, scopes: AllowedScopes, stages: GuardrailStages, status: Status}"
   ```

   Then fetch the catalog entry for the validator:

   ```bash
   uip agent guardrails catalog --validator <validator-id> --output json
   ```

   The catalog response includes scope (`Output`), security category, and rule description. To confirm the action type (`Block` vs `HITL`) and last-modified date, open the portal: Automation Ops → Guardrails → find rule by name from step 3. If the action was recently changed from `HITL` to `Block`, that is the root cause — the rule previously created a human review task; it now faults the job.

## Resolution

**If the LLM output is too unconstrained — tighten the system prompt:**
- Edit `agent.json` → `messages[0].content`: add explicit output constraints (e.g., "Respond only in JSON format. Do not include explanatory prose.", "Never include names or email addresses in responses")
- Validate and republish:

  ```bash
  uip agent refresh --output json
  uip agent validate --output json
  uip solution publish --output json
  ```

**If the guardrail rule is too sensitive — adjust it:**
- Edit the triggering output rule in the portal (same path as step 5 above) → select rule → edit pattern
- Make the pattern more specific or exclude structured data fields from matching
- Re-test by re-invoking the agent with the same input that previously caused the violation

**If a guardrail action was changed from HITL to Block:**
- Revert the action to HITL in the portal (Automation Ops → Guardrails) if the HITL review workflow is still required
- Or keep Block and fix the underlying output pattern (system prompt or rule narrowing above)

**If a recent rule change caused regressions — roll back:**
- Identify the rule change date from the last-modified timestamp in the portal (Automation Ops → Guardrails)
- Restore the prior rule definition or disable the rule temporarily
- Document the rollback and review the rule scope with the guardrail policy team
