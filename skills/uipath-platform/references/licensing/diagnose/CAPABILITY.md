# Diagnose — Investigate Licensing State Failures

Capability index for diagnosing licensing symptoms via `uip platform`: entitlement gaps, allocation changes that did not take effect, and consumption reports that read wrong.

> **Where you came from / where to go next.** Diagnose is downstream of Operate (a user lost access, an allocation did
> not apply, a report read wrong). Fixes — `tenants licenses set`, `users licenses set`, `groups rules set` — are Operate
> actions requiring explicit user consent after root cause analysis.
>
> **Scope boundary.** This capability diagnoses **licensing state**: which layer holds (or fails to hold) an entitlement,
> and why a licensing command's result differs from what the user expected. It does NOT diagnose runtime faults that
> merely *mention* a license (a job stuck Pending, Studio failing to start, a robot not connecting). For those the
> licensing layer is one hypothesis among many — establish the entitlement facts here, then hand the runtime causal chain
> to `uipath-troubleshoot`.
>
> **Inherits universal rules from [SKILL.md](../../../SKILL.md).** Use `uip platform ... --output json` for all diagnostic reads.

## When to use this capability

- A user or group lost (or never gained) a license bundle they should hold.
- `tenants licenses set` reported success but `get` shows unchanged units.
- A product code is absent from `get` output entirely.
- Seat or unit totals do not reconcile against the purchased pool.
- A consumables report reads zero, or lower/higher than the user expects.
- An allocation cannot be applied because the code will not route to a tenant.
- Determine whether a reported access failure is a licensing cause at all, before escalating.

## Critical rules

1. **Diagnose reads; Operate mutates.** Never run a `set` command while diagnosing — a `set` is an overlay that destroys the evidence of the prior state. Read first, present findings, let the user authorize the fix.
2. **Identify the layer before running anything.** Licensing is four independent layers (see [troubleshooting-guide.md](references/troubleshooting-guide.md#step-1-identify-the-layer)). A symptom answered at the wrong layer produces a confident wrong answer.
3. **Read `get` before reasoning about `set`.** `quantity` is absolute, not a delta, and absent codes keep their current value. Without the starting state you cannot tell an ineffective `set` from a correctly-applied no-op.
4. **Treat an absent row as a window question first.** `tenants licenses get` returns only products whose active interval contains the current time. Absent ≠ never allocated.
5. **`consumed` and consumables totals lag.** Accountant-side aggregation is minutes behind job completion. Never conclude "nothing ran" from a fresh zero.
6. **Do not infer seat-consumption semantics that the workflow guides do not document.** When reconciliation needs a rule that is not written down, say so and fall back to the portal or the REST APIs — do not derive it.
7. **Do not expose private data.** Redact tenant URLs, account GUIDs, user emails, and tokens in summaries.

## Workflow

| Journey | Read |
|---------|------|
| Triage a licensing symptom (sequential ladder) | [references/troubleshooting-guide.md](references/troubleshooting-guide.md) |
| Recognize a known failure pattern (lookup) | [references/failure-modes.md](references/failure-modes.md) |

## Common tasks

| I need to... | Read |
|---|---|
| Work out which licensing layer owns the symptom | [troubleshooting guide → Step 1](references/troubleshooting-guide.md#step-1-identify-the-layer) |
| Investigate why a user lacks a bundle | [troubleshooting guide → Step 3](references/troubleshooting-guide.md#step-3-walk-the-user-bundle-layer) |
| Diagnose an allocation that did not take effect | [failure modes → Allocation reported success but units unchanged](references/failure-modes.md#allocation-reported-success-but-units-unchanged) |
| Explain a product code missing from `get` | [failure modes → Product code absent from get output](references/failure-modes.md#product-code-absent-from-get-output) |
| Diagnose a zero or unexpected consumables figure | [failure modes → Consumables report reads zero or wrong](references/failure-modes.md#consumables-report-reads-zero-or-wrong) |
| Explain why a code will not route to a tenant | [failure modes → Product code will not route](references/failure-modes.md#product-code-will-not-route-to-the-tenant) |
| Reconcile seats against the purchased pool | [failure modes → Unit totals do not reconcile](references/failure-modes.md#unit-totals-do-not-reconcile) |
| Decide whether licensing is the cause at all | [troubleshooting guide → Step 5](references/troubleshooting-guide.md#step-5-decide-whether-licensing-is-the-cause) |

## Anti-patterns

- **Never run `set` to "test" a hypothesis.** `users licenses set` replaces the user's direct bundles and `groups rules set` replaces the whole rule — a diagnostic `set` silently revokes entitlements.
- **Never conclude "no license" from the user-bundle layer alone.** Unattended runtime comes from the tenant allocation, not a user bundle; the two are separate license types.
- **Never read a fresh `consumed: 0` as proof no work ran.** Check the window and the aggregation lag first.
- **Never compare a scoped consumables figure to an account-wide one.** Under `--tenant`, `consumedFromOrgWithoutTenant` is suppressed to zero by design.
- **Never claim a group member holds a bundle without checking `orphan`.** Orphaned rows still consume a lease until the rule is re-applied.
- **Never guess a tenant key or bundle code.** Resolve them first — the resolver requires exactly one match.

## References

### Diagnose-scoped

- [troubleshooting-guide.md](references/troubleshooting-guide.md) — layer-first triage ladder
- [failure-modes.md](references/failure-modes.md) — recurring failure patterns

### Cross-capability

- [licensing.md](../licensing.md) — license hierarchy, product codes, response envelope
- [tenant-allocations.md](../tenant-allocations.md) — tenant layer commands, field reference, error table
- [user-licenses-allocations.md](../user-licenses-allocations.md) — user/group layer commands, code resolution, error table
- [consumables-report.md](../consumables-report.md) — consumption modes, flag reference, error table
- [../../orchestrator/setup-environment.md](../../orchestrator/setup-environment.md) — `uip or licenses`, the Orchestrator license-slot layer
