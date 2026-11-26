# Disable — Remove Recommended Settings

**Preview gate:** Compliance Standards is a preview feature. Append the disclaimer to user-facing output; on any compliance-packs **403**, stop (org not enrolled). See [preview-gate.md](../preview-gate.md).

Removes all policy deployments configured by the compliance standard.

`<packId>` / `<packName>` below = the standard to remove, resolved via [`../catalog/impl.md` § Pack ID lookup](../catalog/impl.md#pack-id-lookup). With modes off, disable is per standard — removing one leaves any other configured standard untouched. With modes on, every active standard is turned off together (see below). If the user did not name one and `state list` shows more than one active, ask which before touching anything.

## Check current state first

```bash
TENANT_ID=$(uip login status --output json | sed -n 's/.*"TenantId": *"\([^"]*\)".*/\1/p')
uip gov compliance-packs state get tenant $TENANT_ID <packId> --output json
```

Decide from the `state get` result:
- **Confirmed inactive** — a successful response with `Data.active == false`, or a 404: reply "<packName> recommended settings are not currently configured on this tenant." and stop (nothing to remove).
- **State could not be read** — `state get` failed with an auth/connection error (401 / 5xx) so `active` is unknown: do NOT claim "not configured." Proceed to the disable step and report whatever error that call surfaces. (A **403** → preview gate: see [preview-gate.md](../preview-gate.md).)

## Modes on or off?

```bash
uip gov compliance-packs state settings --output json
```

`Data.ModeSelectionEnabled == true` (tenant scope) → [Modes on: Disable all](#modes-on-disable-all). `false`, or a failed / 404 `state settings` → [Modes off: one standard](#modes-off-one-standard).

## Modes on: Disable all

With modes on, standards are turned off together: `state disable` on an active standard answers `disable_all_required`. Say so plainly — the user asked to turn off one standard, and this turns off **every** active one on the tenant.

```bash
uip gov compliance-packs state disable-all $TENANT_ID --dry-run --output json
```

The `--dry-run` preview writes nothing. Show it:

```
Turning off <packName> turns off every active standard on <tenantName>:
  <catalog name of each Data.PackIds[] entry>

Policies leaving your tenant:
  "<PolicyName>"  <ProductDisplayName> · <license type>  →  back to your policy "<RestoredPolicyName>"
  "<PolicyName>"  <ProductDisplayName> · <license type>  →  no policy
  … one line per policy (group Data.UndeployedPolicies[] by PolicyId; list its license types)

The standards' policies stay in Policy Library, so applying a standard later reuses them.

```

Ask with `AskUserQuestion` ([SKILL.md Critical Rule 13](../../../SKILL.md#critical-rules)): question `Turn off all <N> standards on <tenantName>?`, options `Yes, turn off all <N>` / `Cancel`. Without the tool: `Turn off all <N> standards? (y/n)`.

- `RestoredPolicyId` null → `no policy`. A missing `PolicyName` / `RestoredPolicyName` → `a standard's policy` / `your earlier policy`; never print an id.
- `Data.PackIds` empty → nothing is active: say so and stop.
- If the user wants only <packName> off, they can't with modes on; offer to keep everything as it is.

Require `Yes, turn off all <N>` (or `y`). Halt on anything else. Then:

```bash
uip gov compliance-packs state disable-all $TENANT_ID --output json
```

Report from this response (it reads the tenant again, so it can differ from the preview): "Turned off <names> on `<tenantName>`." plus the same policy lines. On 409 another operation is running — wait ~10 seconds and retry, up to 3 times. On `disable_all_not_enabled` (404) modes are off: use the section below.

## Modes off: one standard

### Confirmation
```
This will remove all <packName> recommended settings from <tenantName>.

Policies that will be removed:
  <list Data.policies[].policyType: Data.policies[].externalPolicyId>

```

Ask with `AskUserQuestion` (Critical Rule 13): question `Turn off <packName> on <tenantName>?`, options `Yes, turn off` / `Cancel`. Without the tool: `Are you sure? (y/n)`. Require `Yes, turn off` (or `y`). Halt on anything else.

### Disable

```bash
uip gov compliance-packs state disable tenant $TENANT_ID <packId> --output json
```

### Report

"<packName> recommended settings removed from `<tenantName>`. All associated policy deployments have been deleted."
