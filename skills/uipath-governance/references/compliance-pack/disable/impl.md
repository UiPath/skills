# Disable — Remove Recommended Settings

Removes all policy deployments configured by the compliance standard.

## Check current state first

```bash
TENANT_ID=$(grep '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
uip gov compliance-packs state get tenant $TENANT_ID <packId> --output json
```

Inspect BOTH fields — never decide on `active` alone:

- `Data.active` — whether the standard is toggled on.
- `Data.policies[]` — policy artifacts still attached to the pack state.

A clean skip requires a POSITIVE clean read. If `state get` does not return readable state — auth error, network failure, anything other than a clean 404 or a parseable result — do NOT assume clean: proceed to Disable and run it once.

Decide on a readable result:

1. `active: true` → proceed to Disable. Normal removal path.
2. (`active: false` AND `policies` empty) OR a clean 404 → already clean. Do NOT call `state disable`. Report: "ISO 42001 recommended settings are not configured on this tenant and no residual policies remain — nothing to remove." Stop.
3. `active: false` AND `policies` non-empty (residual) → toggled off but leftover artifacts remain; the "remove settings" intent is NOT yet satisfied. Proceed to Disable to purge them, then report how many were removed.

Never infer "nothing to do" from `active: false` alone — confirm `policies` is empty first, and only from a response you could actually read.

## Confirmation

```
This will remove all ISO 42001 recommended settings from <tenantName>.

Policies that will be removed:
  <list Data.policies[].policyType: Data.policies[].externalPolicyId>

Are you sure? (y/n)
```

Require `y`. Halt on anything else.

## Disable

```bash
uip gov compliance-packs state disable tenant $TENANT_ID iso-42001-2023 --output json
```

Pass the pack id unquoted (`iso-42001-2023`) or brace-form (`${PACK_ID}`) — not `"$PACK_ID"`. After it returns, re-read state and confirm `active: false` and `policies` empty.

## Report

"ISO 42001 recommended settings removed from `<tenantName>`. All associated policy deployments have been deleted."
