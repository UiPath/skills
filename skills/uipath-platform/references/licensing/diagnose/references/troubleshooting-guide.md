# Licensing Diagnostic Ladder

Layer-first triage for licensing symptoms. Work through in order — stop when you have enough to diagnose. Every command is read-only.

## Step 1: Identify the Layer

Licensing is four independent layers. An entitlement can be present at one and absent at the next, so the first job is deciding which layer the symptom belongs to — not which command to run.

```
Account (organization)          totalUnitsInAccount — the purchased pool
  └── Tenant allocation         units reserved per tenant   → uip platform tenants licenses
  └── User bundle               per-seat entitlement        → uip platform users licenses / groups rules
        └── Group rule lease     inherited, optional quota
  └── Orchestrator slot         user/robot license slot     → uip or licenses  (separate surface)
```

Tenant allocations and user bundles are **separate license types**, not a hierarchy: an unattended job draws on the tenant's runtime allocation (`UNATT`, `RU`, `PLTU`); a developer opening Studio draws on a user bundle (`RPADEVPRONU`). A user with every bundle cannot make an unattended job run, and a fully allocated tenant cannot get a developer into Studio.

| Symptom | Layer | Next step |
|---------|-------|-----------|
| "User can't use <product>", bundle missing for one person | User bundle | Step 3 |
| "Group members don't have their license" | User bundle → group rule | Step 3 |
| "No seats left", "can't assign any more" | Account pool → user bundle | Step 2, then Step 3 |
| "Set the allocation but nothing changed" | Tenant allocation | Step 4, then [failure-modes → Allocation reported success](failure-modes.md#allocation-reported-success-but-units-unchanged) |
| "Code missing from the output" | Tenant allocation → bundle window | [failure-modes → Product code absent](failure-modes.md#product-code-absent-from-get-output) |
| "Can't allocate that product to the tenant" | Tenant allocation → routing | [failure-modes → Code will not route](failure-modes.md#product-code-will-not-route-to-the-tenant) |
| "Report shows zero", "numbers look wrong" | Consumption reporting | [failure-modes → Consumables reads zero or wrong](failure-modes.md#consumables-report-reads-zero-or-wrong) |
| "Totals don't add up to what we bought" | Account pool | [failure-modes → Totals do not reconcile](failure-modes.md#unit-totals-do-not-reconcile) |
| "License slot not assigned in the folder" | Orchestrator slot | [setup-environment.md](../../../orchestrator/setup-environment.md) — `uip or licenses`, not `uip platform` |
| Job Pending/faulted, Studio won't start, robot won't connect | **Not established yet** | Step 5 — establish entitlement facts, then hand off |

## Step 2: Establish the Account Pool Baseline

Every unit question resolves against the purchased pool. Read it once, from any tenant:

```bash
uip platform tenants licenses get "<TENANT_KEY>" --output json
```

Each row carries the account-level totals alongside the tenant's own:

| Field | Use in diagnosis |
|-------|------------------|
| `totalUnitsInAccount` | The purchased pool. Equals `allocated + availableForAllocation + allocatedAcrossOtherTenants` — if it does not, stop and see [failure-modes → Totals do not reconcile](failure-modes.md#unit-totals-do-not-reconcile) |
| `availableForAllocation` | Units still free anywhere in the account. `0` means the pool is exhausted — no tenant can gain units without another losing them |
| `allocatedAcrossOtherTenants` | Units held by other tenants — the source of units if this tenant needs more |
| `allocated` | Reserved for this tenant |
| `consumed` | Subset of `allocated` actually in use. Lags real-time by minutes |

For seat-based (user bundle) questions, the equivalent baseline is:

```bash
uip platform users licenses available --output json
```

## Step 3: Walk the User-Bundle Layer

Resolve the person, then read what they actually hold. The resolver is a **starts-with** match and requires exactly one hit — pass a full email when a name is ambiguous.

```bash
uip platform users licenses get "<USER_EMAIL_OR_NAME_PREFIX>" --output json
```

Read `source` on every returned row:

- `"direct"` — granted by `users licenses set` on this user.
- `"group"` — leased through a group rule. The user's own record is not where the grant lives; the rule is.

Branch on what you find:

| Finding | Meaning | Next |
|---------|---------|------|
| Expected code present | The entitlement exists at this layer. The symptom is elsewhere | Step 5 |
| No rows at all | User holds no bundles — never assigned, or a `set` replaced them | Check whether a group should be granting it (below) |
| Code absent, others present | A prior `users licenses set` replaced the direct bundles — it replaces, not merges | Confirm intent with the user before re-adding |
| Code present via `group` but product still unusable | Entitlement is fine at this layer | Step 5 |

When a group is supposed to be the source, read the rule — not the user:

```bash
uip platform groups rules get --output json
uip platform groups rules details "<GROUP_NAME>" --output json
```

On `details`, check in this order:

1. **Is the code in the rule's entitled bundles at all?** If not, the rule was replaced — `groups rules set` replaces the whole rule, dropping any bundle absent from the input.
2. **Is there a `quota`, and is it filled?** A quota caps how many members can hold the bundle; members beyond it do not get a lease.
3. **Is the user's row `orphan: true`?** Orphaned rows still consume a lease until the rule is re-applied or the user is fully removed — so a lease can be consumed by someone who no longer benefits from it.
4. **Is `useExternalLicense` set?** It is informational, set outside these commands — do not treat it as a grant you can change here.

> The rule header (entitled bundles, quotas) is written to **stderr**; the JSON on stdout is the member list. When piping to `jq` you will lose the header — read both streams.

## Step 4: Walk the Tenant-Allocation Layer

```bash
uip platform tenants licenses get "<TENANT_KEY>" --output json
```

Compare against what the user believes they set:

| Observation | Interpretation |
|-------------|----------------|
| `allocated` differs from the value in their input file | The `set` did not apply, or applied to a different tenant. See [failure-modes → Allocation reported success](failure-modes.md#allocation-reported-success-but-units-unchanged) |
| `allocated` matches, user expected it to be higher | `quantity` is absolute, not additive — their value replaced the old one rather than adding to it |
| Code they set is absent from output | Bundle window, or the code never routed. See [failure-modes → Product code absent](failure-modes.md#product-code-absent-from-get-output) |
| A code they did **not** include still has its old value | Correct behavior — `set` is an overlay. Codes absent from the input keep their current quantity |
| `consumed` > 0 but `allocated` reduced below it | Over-committed: jobs are using more than the new reservation. Flag this explicitly to the user |
| `availableForAllocation: 0` | Pool exhausted — the requested increase was impossible, not merely rejected |

## Step 5: Decide Whether Licensing Is the Cause

For a runtime symptom (job Pending or faulted, Studio unlicensed, robot not connecting), licensing is **one hypothesis**. This capability's job is to settle that hypothesis with facts, then stop.

Establish and record:

1. The relevant layer for that runtime path — unattended job → tenant allocation; Studio/attended → user bundle; folder-scoped robot slot → `uip or licenses`.
2. Whether the entitlement is present at that layer, with the command output as evidence.
3. Whether `availableForAllocation` or a quota was exhausted at the time — noting that a current snapshot cannot prove state during an incident older than 24 hours.

Then:

- **Entitlement genuinely absent** → licensing is the cause. Present the layer, the evidence, and the exact `set` command as a recommendation. Do not run it.
- **Entitlement present** → licensing is excluded. Say so, hand the runtime causal chain to `uipath-troubleshoot`, and pass along the evidence you gathered so it is not re-fetched.
- **Cannot tell from the CLI** → the operation may not be covered. Fall back to the License Resource Manager / License Accountant REST APIs ([licensing.md → REST API Fallback](../../licensing.md#rest-api-fallback)) or the portal. Say which, and why the CLI was insufficient.
