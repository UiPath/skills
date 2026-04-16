---
name: uipath-governance
description: "[PREVIEW] UiPath governance hub — compliance drift checks against .uipolicy packs (AITL V1). More features planned. For applying packs→uipath-compliance-applier."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath Governance

Umbrella skill for UiPath tenant governance operations. Routes to feature-specific workflows based on user intent.

## When to Use This Skill

- "Check compliance against this policy pack"
- "Audit my tenant against ISO 27001"
- "Is my tenant compliant with the policy pack?"
- "Run a drift check"
- "Compare my tenant state to the compliance pack"

DO NOT use for:
- Applying or deploying policies — use `uipath-compliance-applier`
- Authoring compliance packs
- Ad-hoc single-policy creation or modification

## Feature Routing

| Feature | Trigger phrases | Entry point |
|---|---|---|
| Compliance Check | "check compliance", "drift", "audit against pack", "is my tenant compliant" | [references/compliance-check/workflow-guide.md](references/compliance-check/workflow-guide.md) |

Read the entry point file for the matched feature and follow its workflow.

## Critical Rules

1. **Read-only.** Never mutate tenant state. No `create`, `assign`, `update`, or `delete` CLI calls. Only `list`, `get`, and `status`.
2. **`--output json` on every `uip` call.** Parse `Data` / `Message`.
3. **Auth check first.** Run `uip login status --output json` before any operation. Halt if not logged in.
4. **AITL-only in V1.** Skip non-AITL policies with `reason: "out-of-version-scope"`. Never attempt to fetch or diff non-AITL product state.
5. **Always write the JSON report.** Even if everything is compliant. The report is the audit artifact.
6. **Never commit the report.** It contains tenant identifiers and policy values.
7. **Clause-level reporting.** Always map property diffs back to clauses. Never present raw `formData` diffs without clause context.
8. **Feature logic lives in references.** SKILL.md routes to features — it does not contain workflow steps.

## Anti-patterns

- **Never modify a policy to fix drift.** Report and offer handoff to the compliance-applier. The governance skill is an observer.
- **Never prompt for scope narrowing.** Check all applicable clauses by default. Narrow only on explicit user signal.
- **Never silently skip a non-AITL policy.** Always include it in the report's `skippedPolicies` array.
- **Never compare against defaults.** Compare against the pack's expected values, not the product's factory defaults.
- **Never run checks in parallel.** Sequential per-policy, per-property.
