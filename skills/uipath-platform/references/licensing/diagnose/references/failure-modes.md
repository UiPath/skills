# Failure Modes — Licensing

Named failure patterns with symptom → cause → investigation → fix. Match the user's symptom to a pattern, then follow the investigation steps.

These are keyed by **symptom** — what the user reports. For patterns keyed by **CLI error message** (you already have the error text in hand), use the `Error Conditions` table in the owning workflow guide instead: [tenant-allocations.md](../../tenant-allocations.md#error-conditions), [user-licenses-allocations.md](../../user-licenses-allocations.md#error-conditions), [consumables-report.md](../../consumables-report.md#error-conditions).

All investigation commands are read-only. Never run a `set` while diagnosing.

---

## Allocation Reported Success But Units Unchanged

**Symptom:** User ran `tenants licenses set`, it returned success, but `get` shows the old numbers — or numbers they did not expect.

**Causes:**
1. `quantity` treated as a delta — it is absolute, so `5` set the tenant to 5 rather than adding 5
2. Codes omitted from the input file kept their previous quantity — `set` is an overlay, not a replace
3. Applied to a different tenant than the one being inspected
4. The value did apply, but a bundle window means `get` no longer returns that row
5. Only some codes in the input routed; the rest were rejected per-code

**Investigation:**
1. Read current state: `uip platform tenants licenses get "<TENANT_KEY>" --output json`
2. Ask for the exact input file used, and diff its codes against the `get` output — separate "code absent from input" (expected to be unchanged) from "code present in input but unchanged" (the real failure)
3. Confirm the tenant key in the `set` command matches the one being inspected
4. If a code is missing entirely rather than unchanged, switch to [Product code absent from get output](#product-code-absent-from-get-output)

**Fix:** Cause 1 → re-issue with the intended absolute total. Cause 2 → include the code explicitly, with `quantity: 0` to zero it out. Cause 3 → re-issue against the correct tenant key. Cause 4 → see the window pattern below. Cause 5 → see the routing pattern below. Present the corrected `set` command; do not run it.

---

## Product Code Absent From `get` Output

**Symptom:** A product the user knows is purchased and allocated does not appear in `tenants licenses get` at all.

**Causes:**
1. Bundle window — `get` returns only products whose active interval contains the current time. An expired bundle is hidden even with `allocated > 0` historically
2. The code was never provisioned on this tenant's service licenses
3. The SKU is not on the account at all

**Investigation:**
1. `uip platform tenants licenses get "<TENANT_KEY>" --output json` — note that every returned row carries `startDate` / `endDate`, so the returned rows tell you what "currently active" means for this account
2. Check whether the same code appears for a different tenant — present elsewhere means provisioned on the account, absent on this tenant
3. Attempting to allocate it will surface a routing error naming the cause — see the next pattern rather than guessing

**Fix:** Cause 1 → renewal or window question; the CLI cannot extend a window. Causes 2 and 3 → the SKU must be provisioned through the portal first; `set` cannot introduce a new code. In all three, state that this is a provisioning action outside the CLI.

---

## Product Code Will Not Route To The Tenant

**Symptom:** `tenants licenses set` fails for a specific code, complaining it cannot be routed, or that routing is ambiguous.

**Causes:**
1. The code is not already present on the tenant's service licenses — `set` adjusts existing codes, it cannot introduce new ones
2. The same code exists on more than one of the tenant's service licenses, so the target is ambiguous

**Investigation:**
1. `uip platform tenants licenses get "<TENANT_KEY>" --output json` — a code absent here cannot be routed by `set`
2. Distinguish the two: "cannot route" means absent; "ambiguous routing" means duplicated across service types, and the error names the service types involved

**Fix:** Cause 1 → provision the SKU on the tenant through the portal, then re-run `set`. Cause 2 → the duplicate allocation must be resolved in the portal or via support; the CLI cannot disambiguate. Neither is fixable from the CLI — say so plainly rather than retrying.

---

## User Lacks A Bundle They Should Hold

**Symptom:** One person cannot use a product others can, or reports losing access they previously had.

**Causes:**
1. Never assigned — no direct grant and no group rule covers them
2. A later `users licenses set` replaced their direct bundles; anything absent from that input was revoked
3. A `groups rules set` replaced the group rule, dropping the bundle for every member
4. A group rule `quota` is filled, so this member gets no lease
5. Their group row is `orphan: true` — the lease is consumed but not effective for them
6. Account seats are exhausted, so no new lease could be granted

**Investigation:**
1. `uip platform users licenses get "<USER_EMAIL>" --output json` — read `source` on each row (`direct` vs `group`) and `leasedAt` for when it was granted
2. If the expected code is absent, read the rule rather than the user: `uip platform groups rules details "<GROUP_NAME>" --output json` — check entitled bundles, `quota`, and the member's `orphan` flag. The rule header is on **stderr**
3. Check seat availability: `uip platform users licenses available --output json`
4. Compare `leasedAt` on their surviving bundles — a cluster of identical timestamps points to a bulk `set` that replaced their prior grants

**Fix:** Cause 1 → assign directly or add to the group. Cause 2 → re-issue `users licenses set` with the **full** intended bundle list, not just the missing one. Cause 3 → re-issue `groups rules set` with the full rule. Cause 4 → raise the quota or grant directly. Cause 5 → re-apply the rule or fully remove the departed user to release the lease. Cause 6 → free seats or purchase more. Present the command; do not run it.

---

## Consumables Report Reads Zero Or Wrong

**Symptom:** A consumption report shows zero, or a figure the user says is too low or too high.

**Causes:**
1. Aggregation lag — `consumed` and consumable totals are minutes behind job completion
2. Window mismatch — with no `--start-date`/`--end-date`, every consumable uses **its own** bundle window, so rows in one summary can span different date ranges
3. Scope suppression — under `--tenant`, `consumedFromOrgWithoutTenant` is deliberately zero; only tenant-pool and org-pool figures are populated
4. Non-recursive folders — in `folders` mode, `consumedBySelf` excludes child folders, so a parent looks emptier than the subtree
5. Comparing point-in-time totals as if they were running totals — `consumedAmount` and `consumedBySelf` are totals over the requested range
6. Wrong unit — the code is not an active consumable in this organization, or is a runtime code rather than a consumable
7. Reading a scoped figure against an account-wide expectation

**Investigation:**
1. Re-run with the window stated explicitly so every row shares one range:
   ```bash
   uip platform licenses consumables get --mode summary \
     --start-date "<YYYY-MM-DD>" --end-date "<YYYY-MM-DD>" --output json
   ```
2. Compare scoped against unscoped — run once with `--tenant` and once without, and attribute the difference to suppression rather than to missing consumption
3. For a per-day view, all four flags are required: `--mode daily --tenant <T> --unit <CODE> --start-date <D> --end-date <D>`
4. Confirm the unit is a consumable at all — runtime codes (`UNATT`, `RU`, `TEU`) are allocated, not consumed; `PLTU` appears on both axes and is a common source of confusion
5. For `folders` mode, sum the children yourself before comparing to a tenant total

**Fix:** Cause 1 → re-query after the lag; do not report zero as fact. Causes 2, 3, 5, 7 → the number is correct, the comparison is not; explain the semantics. Cause 4 → reconstruct the tree and roll up. Cause 6 → pick a code from the list the CLI returns.

---

## Unit Totals Do Not Reconcile

**Symptom:** Allocated plus available does not match what the user believes was purchased.

**Causes:**
1. Units reserved by other tenants are being overlooked — the identity is `totalUnitsInAccount = allocated + availableForAllocation + allocatedAcrossOtherTenants`
2. Comparing across bundle windows — only currently-active products are returned
3. Comparing a consumption figure against an allocation figure; `consumed` is a subset of `allocated`, not an addend
4. Conflating separate license types — tenant runtime units and per-seat user bundles are different pools and never sum together
5. Leases consumed by `orphan: true` group rows, which are held without being effective

**Investigation:**
1. `uip platform tenants licenses get "<TENANT_KEY>" --output json` — verify the four-field identity holds per code. If it does, the arithmetic is right and the user's expectation is what needs correcting
2. Enumerate every tenant to account for `allocatedAcrossOtherTenants` rather than inferring it
3. For seats, use `uip platform users licenses available --output json`, and count group leases via `groups rules details` including orphaned rows

**Fix:** Causes 1–4 → walk the user through the identity with their own numbers; no change is needed. Cause 5 → re-apply the rule or remove departed users to release leases. If the identity genuinely does not hold, the CLI cannot explain it — escalate to the portal or the License Resource Manager REST API and say so.

---

## Reported As Licensing, Caused Elsewhere

**Symptom:** A runtime failure the user attributes to licensing — job stays Pending, Studio starts unlicensed, robot will not connect.

**Cause:** The licensing layer they checked is not the one that runtime path draws on, or licensing is not involved at all.

**Investigation:**
1. Map the runtime path to its layer: unattended job → tenant allocation (`UNATT`, `RU`, `PLTU`); Studio/attended → user bundle (`RPADEVPRONU`, `ATTUNU`); folder-scoped robot slot → `uip or licenses`, a different surface
2. Confirm presence or absence at that layer only, capturing the output as evidence
3. Note that a current snapshot cannot prove entitlement state during an incident older than 24 hours

**Fix:** Entitlement absent → licensing is the cause; present the layer, evidence, and recommended `set`. Entitlement present → licensing is excluded; hand the causal chain to `uipath-troubleshoot` along with the evidence gathered so it is not re-fetched. Do not keep digging in licensing once the entitlement is confirmed present.
