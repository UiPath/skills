---
confidence: high
---

# Guardrail Violation

## Context

What this looks like:
- Agent job faults; `uip agent run status <job-id> --output json` shows `Faulted`
- `agentRun` span has `AGENT_RUNTIME.TERMINATION_GUARDRAIL_VIOLATION` in `attributes.error`
- Container span (`agentPreGuardrails`, `llmPreGuardrails`, `toolPreGuardrails`, `agentPostGuardrails`, `llmPostGuardrails`, `toolPostGuardrails`) carries the blocking error
- Child `guardrailEvaluation` or `toolGuardrailEvaluation` span identifies the rule: `guardrailName`, `action`, `validationResult`, `reason`

Classification table — container span type identifies scope and stage:

| Container span | Stage | Data validated |
|---|---|---|
| `agentPreGuardrails` | pre (input-side) | agent invocation payload |
| `llmPreGuardrails` | pre (input-side) | LLM prompt / messages |
| `toolPreGuardrails` | pre (input-side) | tool call arguments |
| `agentPostGuardrails` | post (output-side) | agent response |
| `llmPostGuardrails` | post (output-side) | LLM response |
| `toolPostGuardrails` | post (output-side) | tool call result |

What can cause it:
- Block action matched content in invocation payload, LLM prompt/response, or tool call arguments/result
- Escalate action fired and Action Center reviewer rejected the task
- Recent rule tightening or action change from Log/Escalate to Block — behavior change is immediate and silent
- Overly broad pattern matches legitimate content (common business terms, structured JSON fields)
- OOB validators (PII detection, harmful content, prompt injection, user prompt attacks) at agent or LLM scope — these run automatically when enabled and require no custom rules

> **Filter and Log do not fault the job.** Filter removes `excludedFields` from the payload; `updatedInput`/`updatedOutput` appear on the evaluation span; execution continues. Agent may behave unexpectedly if required fields are stripped. Log records the match; `severityLevel` appears on the evaluation span; execution continues. Neither produces `TERMINATION_GUARDRAIL_VIOLATION`.

> **Distinct error shape — governance policy:** If the error is `"User is forbidden by governance policy to use: <model>"` (`StatusCode 403`, `ErrorCode 3000`), this is an Automation Ops model-restriction policy, not a guardrail rule. Check via: `uip gov aops-policy deployed-policy get <license-type> AITrustLayer <tenant-id> --output json`

> **Trace UI async note:** Guardrail evaluation spans may show loading in the trace UI after output is rendered — evaluation runs asynchronously. Use CLI to read span attributes directly.

## Investigation

1. Get trace ID:

   ```bash
   uip agent run status <job-id> --output json \
     --output-filter "traceId"
   ```

2. Find erroring spans, identify container span, classify pre/post using the table above. If the only erroring span is `agentRun` and no container guardrail span appears in the results, the termination error propagated from a child evaluation — proceed to step 3 to find the `guardrailEvaluation` or `toolGuardrailEvaluation` span directly:

   ```bash
   uip traces spans get <trace-id> --output json \
     --output-filter "spans[?attributes.error != null].{spanType: spanType, error: attributes.error, name: name}"
   ```

3. Read the `guardrailEvaluation` or `toolGuardrailEvaluation` child span for `guardrailName`, `action`, `validationResult`, `payload`, and `reason`:

   ```bash
   uip traces spans get <trace-id> --output json \
     --output-filter "spans[?spanType == 'guardrailEvaluation' || spanType == 'toolGuardrailEvaluation'].{spanType: spanType, guardrailName: attributes.guardrailName, action: attributes.action, validationResult: attributes.validationResult, payload: attributes.payload, reason: attributes.reason}"
   ```

4. Inspect the triggering rule:

   ```bash
   uip agent guardrails list --output json \
     --output-filter "[?contains(Validator, '<GUARDRAIL_NAME>')].{validator: Validator, scopes: AllowedScopes, stages: GuardrailStages, status: Status}"
   ```

   Then fetch the catalog entry:

   ```bash
   uip agent guardrails catalog --validator <validator-id> --output json
   ```

   For custom guardrails (rule logic in agent definition):

   ```bash
   uip agent config get guardrails --path <PROJECT_DIR> --output json
   ```

   To confirm action type and last-modified date: open agent in AgentBuilder or Flow → Guardrails → find rule by name from step 3 (optional — confirms action type and last-modified date; CLI output above is sufficient to identify the rule).

5. Escalate action only — check reviewer outcome:

   ```bash
   uip traces spans get <trace-id> --output json \
     --output-filter "spans[?spanType == 'guardrailEscalation' || spanType == 'toolGuardrailEscalation'].{spanType: spanType, reviewOutcome: attributes.reviewOutcome, reviewStatus: attributes.reviewStatus, reviewedBy: attributes.reviewedBy}"
   ```

   `reviewOutcome: "Rejected"` means reviewer rejected → faults the job. Absent or pending span means the Action Center task is still open.

## Resolution

**Block + legitimate violation:** Fix caller payload (pre/input-side container span) so it does not contain prohibited content before sending. For post/output-side violations, tighten the system prompt in `agent.json → messages[0].content` to constrain LLM output (e.g., "Respond only in JSON. Do not include names or email addresses.").

**Rule too broad:** Narrow the pattern in AgentBuilder or Flow → Guardrails. For centralized guardrails enforced by a tenant admin: Automation Ops → Governance → AI Trust Layer → find policy by name from step 3. Replace the overly broad expression with a more specific match. Re-test with the previously blocked input.

**Action changed from Log/Escalate to Block:** Revert the action in AgentBuilder or Flow → Guardrails if the prior review workflow is still required. Or keep Block and fix the underlying data (system prompt or rule narrowing above).

**Escalate reviewer rejected:** Determine if the rejection was correct or reviewer error. If reviewer error, re-invoke agent to create a new Action Center task. If the rule intent is the issue, adjust the rule or fix data handling before re-invoking.

**Filter causing unexpected behavior (not a fault):** Inspect `updatedInput`/`updatedOutput` on the evaluation span from step 3 to see which fields were removed. Verify the agent handles absent fields gracefully. Add fallback logic if required fields can be stripped.

**Recent rule regression:** Check last-modified date in AgentBuilder or Flow → Guardrails. Restore the prior rule definition or disable the rule temporarily. Document the rollback and review rule scope with the guardrail policy team.

Validate and republish after any rule or agent change:

```bash
uip agent refresh --output json
uip agent validate --output json
uip solution publish --output json
```
