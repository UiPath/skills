# Diagnose — Investigate Governance Policy Failures

Capability index for diagnosing AOps product-policy and Access tool-use-policy failures via `uip gov`.

> **Where you came from / where to go next.** Diagnose is downstream of Operate (a deployed policy failed
> to take effect, blocked something unexpected, or returned empty). Source fixes — policy edits, redeployment,
> rule changes — are Operate actions requiring explicit user consent after root cause analysis.
>
> **Inherits universal rules from [SKILL.md](../../SKILL.md).** Use `uip gov ... --output json` for all diagnostic reads.

## When to use this capability

- Investigate why a deployed AOps policy isn't taking effect.
- Debug deployment precedence (user > group > tenant override chain).
- Diagnose wrong policy applied (license-type / product mismatch).
- Triage access-policy blocking a legitimate tool invocation.
- Investigate access-policy not blocking when it should (rule too narrow).
- Diagnose `deployed-policy get` returning empty (no deployment, wrong subject).
- Investigate policy create/update rejection (invalid product identifier, malformed JSON).
- Audit which policies are deployed to which subjects.

## Critical rules

1. **Diagnose reads; Operate mutates.** Do not create/delete/redeploy policies while diagnosing — present findings and let the user decide the fix.
2. **Use the CLI as the diagnostic interface.** Run `uip gov ... --output json` for all reads.
3. **Use `deployed-policy get` for effective policy.** Returns the single policy that applies after the user → group → tenant chain is walked. Use `deployed-policy list` to see every applicable policy in priority order.
4. **Use `access-policy evaluate` for rule testing.** The PDP resolves `Allow` / `Deny` / `NoOp` for a concrete request context — faster and more authoritative than manual rule inspection.
5. **Classify the branch first.** AOps (product-layer) and Access (tool-use) are separate systems. Determine which branch the symptom belongs to before investigating.
6. **Do not expose private data.** Redact tenant URLs, policy payloads, and user identifiers in summaries.

## Workflow

| Journey | Read |
|---------|------|
| Triage a governance failure (sequential ladder) | [references/troubleshooting-guide.md](references/troubleshooting-guide.md) |
| Recognize a known failure pattern (lookup) | [references/failure-modes.md](references/failure-modes.md) |

## Common tasks

| I need to... | Read |
|---|---|
| Investigate why a deployed AOps policy isn't enforced | [troubleshooting guide → Step 2](references/troubleshooting-guide.md#step-2-check-whats-deployed) |
| Debug deployment precedence (user > group > tenant) | [troubleshooting guide → Step 3](references/troubleshooting-guide.md#step-3-check-precedence) |
| Diagnose wrong policy applied | [failure modes → Wrong policy applied](references/failure-modes.md#wrong-policy-applied-license-type-mismatch) |
| Investigate blocked tool invocation | [failure modes → Access policy blocking legitimate invocation](references/failure-modes.md#access-policy-blocking-legitimate-tool-invocation) |
| Investigate access policy not blocking | [failure modes → Access policy not blocking](references/failure-modes.md#access-policy-not-blocking) |
| Diagnose empty deployed-policy result | [failure modes → Deployed policy returns empty](references/failure-modes.md#deployed-policy-returns-empty) |
| Troubleshoot policy create/update rejection | [failure modes → Policy create/update rejected](references/failure-modes.md#policy-createupdate-rejected) |
| Evaluate access-policy rules against test inputs | [troubleshooting guide → Step 4](references/troubleshooting-guide.md#step-4-for-access-evaluate-with-test-inputs) |

## Anti-patterns

- **Never redeploy or edit policies while diagnosing.** Present findings first; let the user authorize mutations.
- **Never assume which branch the failure belongs to.** Classify AOps vs Access before investigating.
- **Never skip `deployed-policy get` and jump to policy definition.** The effective policy (after chain resolution) may differ from the policy definition.
- **Never run `access-policy evaluate` with dummy UUIDs and draw conclusions.** Untagged/unknown UUIDs correctly return `NoOp` — that does not mean the policy is broken.
- **Never guess subject IDs.** Resolve via `deployment user/group/tenant list` before deeper queries.

## References

### Diagnose-scoped

- [troubleshooting-guide.md](references/troubleshooting-guide.md) — diagnostic priority ladder
- [failure-modes.md](references/failure-modes.md) — recurring failure patterns

### Cross-capability

- [aops-policy-deployed-guide.md](../aops-policy/aops-policy-deployed-guide.md) — query effective deployed policy
- [aops-policy-deploy-guide.md](../aops-policy/aops-policy-deploy-guide.md) — deployment precedence and subject matrix
- [access-policy-commands.md](../access-policy/access-policy-commands.md) — CLI reference including `evaluate`
- [disambiguation-guide.md](../disambiguation-guide.md) — classify AOps vs Access intent
