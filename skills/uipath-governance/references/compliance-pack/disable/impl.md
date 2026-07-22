# Disable — Remove Recommended Settings

**Preview gate:** Compliance Standards is a preview feature. Append the disclaimer to user-facing output; on any compliance-packs **403**, stop (org not enrolled). See [preview-gate.md](../preview-gate.md).

Removes all policy deployments configured by the compliance standard.

## Check current state first

```bash
TENANT_ID=$(grep '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
uip gov compliance-packs state get tenant $TENANT_ID <packId> --output json
```

Decide from the `state get` result — inspect BOTH `Data.active` and `Data.policies`, never `active` alone:
- **Clean — nothing to remove** — a successful response with `Data.active == false` AND `Data.policies` empty, or a 404: reply "ISO 42001 recommended settings are not currently configured on this tenant." and stop.
- **Residual policies** — `Data.active == false` but `Data.policies` is non-empty: the standard is toggled off yet leftover policy artifacts remain, so "remove settings" is NOT yet satisfied. Proceed to the disable step to purge them, then report how many were removed.
- **Active** — `Data.active == true`: proceed to the disable step (normal removal path).
- **State could not be read** — `state get` failed with an auth/connection error (401 / 5xx) so `active` is unknown: do NOT claim "not configured." Proceed to the disable step and report whatever error that call surfaces. (A **403** → preview gate: see [preview-gate.md](../preview-gate.md).)

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
uip gov compliance-packs state disable tenant $TENANT_ID <packId> --output json
```

## Report

"ISO 42001 recommended settings removed from `<tenantName>`. All associated policy deployments have been deleted."
