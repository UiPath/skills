# Diagnose — Investigate Licensing State Failures

Diagnose licensing symptoms via `uip platform`: entitlement gaps, ineffective allocations, and incorrect consumption reports.

> **Direction.** Diagnose follows Operate (lost access, ineffective allocation, incorrect report). Fixes—`tenants licenses set`, `users licenses set`, `groups rules set`—are Operate actions requiring explicit user consent after root-cause analysis.
>
> **Scope.** Diagnose licensing state: which layer holds (or fails to hold) an entitlement and why a licensing command differs from expectations. Do not diagnose runtime faults that merely mention a license (a job stuck Pending, Studio failing to start, or a robot not connecting); establish entitlement facts here, then hand the runtime causal chain to `uipath-troubleshoot`.
>
> **Inherits universal rules from [SKILL.md](../../../SKILL.md).** Use `uip platform ... --output json` for all diagnostic reads.

## When to use this capability

- A user or group lost or never gained an expected license bundle.
- `tenants licenses set` reported success but `get` shows unchanged units.
- A product code is absent from `get` output.
- Seat or unit totals do not reconcile with the purchased pool.
- A consumables report reads zero or an unexpected value.
- An allocation cannot apply because its code will not route to a tenant.
- Determine whether licensing is the cause before escalating an access failure.

## Critical rules

1. **Diagnose reads; Operate mutates.** Never run a `set` command while diagnosing: a `set` is an overlay that destroys prior-state evidence. Read first, present findings, and let the user authorize the fix. Re-running the user's `set` to reproduce the symptom is still a mutation. A seemingly disconnected CLI is not permission to try it: an unauthenticated command is not guaranteed to fail, and resolved credentials mutate production. Explain a `set` by reading `get` and citing documented semantics or `set --help`; never execute it.
2. **Identify the layer before running anything.** Licensing has four independent layers; see [troubleshooting-guide.md](references/troubleshooting-guide.md#step-1-identify-the-layer). Answering at the wrong layer produces a confident wrong answer.
3. **Read `get` before reasoning about `set`.** `quantity` is absolute, not a delta, and absent codes retain their current value. Without the starting state, an ineffective `set` cannot be distinguished from a correctly applied no-op.
4. **Treat an absent row as a window question first.** `tenants licenses get` returns only products whose active interval contains the current time; absent ≠ never allocated.
5. **`consumed` and consumables totals lag.** Accountant-side aggregation is minutes behind job completion; never conclude “nothing ran” from a fresh zero.
6. **Do not infer seat-consumption semantics that workflow guides do not document.** If reconciliation needs an unwritten rule, say so and fall back to the portal or REST APIs; do not derive it.
7. **Do not expose private data.** Redact tenant URLs, account GUIDs, user emails, and tokens in summaries.

## Workflow

| Journey | Read |
|---|---|
| Triage a licensing symptom (sequential ladder) | [references/troubleshooting-guide.md](references/troubleshooting-guide.md) |
| Recognize a known failure pattern (lookup) | [references/failure-modes.md](references/failure-modes.md) |

## Common tasks

| I need to... | Read |
|---|---|
| Identify the licensing layer | [troubleshooting guide → Step 1](references/troubleshooting-guide.md#step-1-identify-the-layer) |
| Investigate why a user lacks a bundle | [troubleshooting guide → Step 3](references/troubleshooting-guide.md#step-3-walk-the-user-bundle-layer) |
| Diagnose an ineffective allocation | [failure modes → Allocation reported success but units unchanged](references/failure-modes.md#allocation-reported-success-but-units-unchanged) |
| Explain a missing product code | [failure modes → Product code absent from get output](references/failure-modes.md#product-code-absent-from-get-output) |
| Diagnose an unexpected consumables figure | [failure modes → Consumables report reads zero or wrong](references/failure-modes.md#consumables-report-reads-zero-or-wrong) |
| Explain why a code will not route to a tenant | [failure modes → Product code will not route](references/failure-modes.md#product-code-will-not-route-to-the-tenant) |
| Reconcile seats with the purchased pool | [failure modes → Unit totals do not reconcile](references/failure-modes.md#unit-totals-do-not-reconcile) |
| Decide whether licensing is the cause | [troubleshooting guide → Step 5](references/troubleshooting-guide.md#step-5-decide-whether-licensing-is-the-cause) |

## Anti-patterns

- **Never re-run the user's failed `set` to reproduce the symptom.** Quote it in the write-up, do not execute it, and do not treat an offline or unauthenticated environment as safe.
- **Never run `set` to test a hypothesis.** `users licenses set` replaces direct bundles and `groups rules set` replaces the whole rule; diagnostic use can silently revoke entitlements.
- **Never conclude “no license” from the user-bundle layer alone.** Unattended runtime comes from tenant allocation, not a user bundle; they are separate license types.
- **Never treat a fresh `consumed: 0` as proof no work ran.** Check the window and aggregation lag.
- **Never compare a scoped consumables figure to an account-wide one.** Under `--tenant`, `consumedFromOrgWithoutTenant` is suppressed to zero by design.
- **Never claim a group member holds a bundle without checking `orphan`.** Orphaned rows still consume a lease until the rule is re-applied.
- **Never guess a tenant key or bundle code.** Resolve them first; the resolver requires exactly one match.

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