# Disable — Remove Recommended Settings

**Preview gate:** Compliance Standards is a preview feature. Append the disclaimer to user-facing output; on any compliance-packs **403**, stop (org not enrolled). See [preview-gate.md](../preview-gate.md).

Turns a compliance standard off. Its policies leave the tenant's slots and stay in Automation Ops, with any hand edits; nothing is deleted. The tenant's own policy goes back into each slot it held before.

`<packId>` / `<packName>` below = the standard to remove, resolved via [`../catalog/impl.md` § Pack ID lookup](../catalog/impl.md#pack-id-lookup). If the user did not name one and `state list` shows more than one active, ask which before touching anything.

## Check current state first

```bash
TENANT_ID=$(grep '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
uip gov compliance-packs state get tenant $TENANT_ID <packId> --output json
uip gov compliance-packs state list tenant $TENANT_ID --output json
uip gov compliance-packs settings get --output json
```

Decide from the `state get` result:
- **Confirmed inactive** — a successful response with `Data.Active == false`, or a 404: reply "<packName> recommended settings are not currently configured on this tenant." and stop (nothing to remove).
- **State could not be read** — `state get` failed with an auth/connection error (401 / 5xx) so `Active` is unknown: do NOT claim "not configured." Proceed to the disable step and report whatever error that call surfaces. (A **403** → preview gate: see [preview-gate.md](../preview-gate.md).)

**Who else goes off.** With modes on (`settings get` → `Data.ModeSelectionEnabled == true`) several standards can be active, and disabling one can turn off others:
- `<packName>` in **Enforce** (`Data.Mode` `"enforce"` or `null`) → **every** active standard on the tenant is turned off, so none is left pointing at a policy that was just removed. Name each other `Active` standard from `state list`.
- `<packName>` in **Observe** (`Data.Mode == "audit"`) → only `<packName>` goes off.

With modes off, or `settings` unknown (older CLI), only one standard can be active — nothing else is affected.

## Confirmation

```
This will turn off <packName> on <tenantName>.

Also turned off:  <other standard>, <other standard>      (Enforce with others active; omit otherwise)
To keep <other standard>, turn it on again afterwards.

Its policies come off your tenant and stay in Automation Ops, with any changes you made — nothing is deleted.
Where your own policy was in place before, it goes back.

Are you sure? (y/n)
```

Never list policy ids. Ask, then END YOUR REPLY. Proceed only on an explicit `y` in the user's next message; halt on anything else.

## Disable

```bash
uip gov compliance-packs state disable tenant $TENANT_ID <packId> --output json
```

## Report

Re-run `state list` and report what is now off:

"<packName> turned off on `<tenantName>`." When others went with it: "Also turned off: <other standard>, …" Then: "Their policies are still in Automation Ops, unassigned; your own policies are back in place."
