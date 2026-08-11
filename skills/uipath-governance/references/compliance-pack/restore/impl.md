# Restore — Reset to Recommended Settings

**Preview gate:** Compliance Standards is a preview feature. Append the disclaimer to user-facing output; on any compliance-packs **403**, stop (org not enrolled). See [preview-gate.md](../preview-gate.md).

Resets an already-active compliance standard's policies back to the values the standard recommends — undoing any local drift. It resets live policies to the suggested config, recreates any that were deleted, and re-asserts the tenant bindings. Only works while the standard is active; custom (Rego) policies are left untouched.

Use this when the user wants to undo changes made to a configured standard, or after a `coverage` posture check shows drift (`Data.Summary.DriftedControlCount > 0`, detail in `Data.DeploymentPolicies[].DriftedControls[]` — the ⟳ rows in the posture table).

`<packName>` below = the standard's display name (e.g. "ISO 42001") — from the user's request or `Data.Packs[].PackName` in `catalog list`.

## Check current state first

```bash
TENANT_ID=$(grep '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
uip gov compliance-packs state get tenant $TENANT_ID <packId> --output json
```

Decide from the `state get` result:
- **Not active** — a successful response with `Data.Active == false` (a never-applied known pack returns 200 with `Active: false`, `PackStateId: null`): the standard isn't configured, so there is nothing to restore. Reply "<packName> is not currently configured on this tenant — enable it first with `state enable`." and stop.
- **404** — the packId itself is not usable (unknown, or a catalog entry with no bundle). Do NOT suggest `state enable` — it would 404 too. Re-check the id with `catalog list` and stop.
- **Active** — `Data.Active == true`: proceed.
- **State could not be read** — `state get` failed with an auth/connection error (401 / 5xx) so `Active` is unknown: do NOT claim a state. Proceed to Confirmation, then the restore step, and report whatever error the restore call surfaces. (A **403** → preview gate: see [preview-gate.md](../preview-gate.md).)

## Confirmation

```
This will reset all <packName> recommended settings on <tenantName> back to the values the standard recommends, overwriting any local changes to those policies.
This includes any values you configured for the standard's manual settings — those go back to the bundle defaults and will need to be configured again. Policies that were deleted are recreated.

Are you sure? (y/n)
```

Ask, then STOP — end your reply. Never run `state restore` in the same response as this question. Proceed only on an explicit `y` in the user's next message; halt on anything else. The user's original request ("reset my settings") is intent, not consent. Sole exception: the user explicitly waived confirmation in advance (e.g., "don't ask for confirmation") — treat the waiver as `y`.

## Restore

```bash
uip gov compliance-packs state restore tenant $TENANT_ID <packId> --output json
```

On failure, read the status the error carries:
- **404** — the packId is not in the loaded catalog. List valid packs with `uip gov compliance-packs catalog list`.
- **409** — either the standard is not active (enable it first with `state enable`) or another operation on this pack is already in progress (wait a few seconds and retry).

## Report

Success returns the full state detail (`Data.Active`, `Data.Policies[]`). Report:

"<packName> recommended settings on `<tenantName>` reset to the standard's suggested values."

## Arriving from a coverage drift check

When `coverage` routed here (its next-action case 3a — `Summary.DriftedControlCount > 0` or an `unverifiable` product), the ⟳ settings and Cannot-Be-Checked products it listed ARE what this call fixes. Two changes to the flow above:

- **Skip the `state get` pre-check.** Coverage already proves the pack is active — drift and `unverifiable` both exist only on an active pack. Go straight to Confirmation, and name the ⟳ settings (and any product whose policy will be recreated) so the user sees exactly what is about to change.
- **Verify after.** Re-run `coverage` and confirm the ⟳ settings flipped back to ✓ and no product is Cannot-Be-Checked anymore. If any is still ⟳, it did not reset — report that plainly rather than claiming success. ⚙ manual items reappearing IS expected (restore resets their values to bundle defaults); do not report those as a failure.

What restore does and does not fix, per the server's own semantics (it resets every live pack policy to the bundle's suggested formData — a FULL replacement — and recreates deleted ones):
- ⟳ drifted settings — fixed.
- Cannot-Be-Checked products (policy deleted out-of-band) — fixed: the policy is recreated with the bundle's values.
- ⚙ manual settings — NOT fixed, and worse: any value an admin had already configured for them is wiped back to the bundle default. After a restore, expect the ⚙ list to be back in full; say so, and point at the manual-settings flow to (re)configure them AFTER the restore, never before.
