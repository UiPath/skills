# Restore — Reset to Recommended Settings

**Preview gate:** Compliance Standards is a preview feature. Append the disclaimer to user-facing output; on any compliance-packs **403**, stop (org not enrolled). See [preview-gate.md](../preview-gate.md).

Resets an already-active compliance standard's policies back to the values the standard recommends — undoing any local drift. It resets live policies to the suggested config, recreates any that were deleted, and re-asserts the tenant bindings. Only works while the standard is active; custom (Rego) policies are left untouched.

Use this when the user wants to undo changes made to a configured standard, or after a `coverage` posture check shows drift (`Data.deploymentPolicies[].driftedControls`).

## Check current state first

```bash
TENANT_ID=$(grep '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
uip gov compliance-packs state get tenant $TENANT_ID <packId> --output json
```

Decide from the `state get` result:
- **Not active** — a successful response with `Data.active == false`, or a 404: the standard isn't configured, so there is nothing to restore. Reply "ISO 42001 is not currently configured on this tenant — enable it first with `state enable`." and stop.
- **Active** — `Data.active == true`: proceed.
- **State could not be read** — `state get` failed with an auth/connection error (401 / 5xx) so `active` is unknown: do NOT claim a state. Proceed to the restore step and report whatever error that call surfaces. (A **403** → preview gate: see [preview-gate.md](../preview-gate.md).)

## Confirmation

```
This will reset all ISO 42001 recommended settings on <tenantName> back to the values the standard recommends, overwriting any local changes to those policies.

Are you sure? (y/n)
```

Require `y`. Halt on anything else.

## Restore

```bash
uip gov compliance-packs state restore tenant $TENANT_ID <packId> --output json
```

On failure, read the status the error carries:
- **404** — the packId is not in the loaded catalog. List valid packs with `uip gov compliance-packs catalog list`.
- **409** — either the standard is not active (enable it first with `state enable`) or another operation on this pack is already in progress (wait a few seconds and retry).

## Report

Success returns the full state detail (`Data.active`, `Data.policies[]`). Report:

"ISO 42001 recommended settings on `<tenantName>` reset to the standard's suggested values."
