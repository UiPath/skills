# Policy Deployment Query Guide

Query the **single effective deployed policy** for a `(licenseType, product, tenant)` tuple, or the **full list of applicable policies** ordered by priority, for the calling user (or a named user via S2S).

> **Terminology — read before using.**
> - `deployed-policy get` returns the **single effective policy** — the one policy that actually applies after the user → group → tenant inheritance chain has been walked and any 'No Policy' pins have been honored. The default mode resolves for the caller's own identity; the S2S `--user-id` mode resolves for a named user; the S2S `--tenant-only` mode skips user/group overrides and returns only the tenant assignment.
> - `deployed-policy list` returns **every applicable policy** for the caller, in priority order. Use this to see why a particular policy wins — not just the winner.
> - "Which policy actually applies?" → `get`. "Which policies are in play, and in what order?" → `list`.

## Prerequisites

1. User must be logged in — see [aops-policy-commands.md — Authentication](./aops-policy-commands.md#authentication).
2. For `--user-id` or `--tenant-only` modes of `get`: an S2S token is required — see [aops-policy-commands.md — S2S token](./aops-policy-commands.md#s2s-token).
3. All commands require three positional arguments: `<LICENSE_TYPE> <PRODUCT_NAME> <TENANT_ID>`. For flag/positional details, see [aops-policy-commands.md — deployed-policy get](./aops-policy-commands.md#uip-gov-aops-policy-deployed-policy-get) / [deployed-policy list](./aops-policy-commands.md#uip-gov-aops-policy-deployed-policy-list).

---

## Step 1 — Collect required inputs

If the user has not provided the positional values, ask **one at a time** in this order — resolve each before moving to the next:

1. `License type?` — if unknown, run `uip gov aops-policy license-type list --output json` and let the user pick by `name` (e.g. `Attended`, `Unattended`), not by `identifier` (GUID) or label. `deployed-policy get/list` take the `name` as the `<licenseType>` positional argument. Store as `$LICENSE_TYPE`.
2. `Product name (identifier)?` — run `uip gov aops-policy product list --output json` if unknown.
3. `Tenant identifier (GUID)?` — if unknown, run `uip gov aops-policy deployment tenant list --output json` and let the user pick from tenants that already have policy assignments. Store as `$TENANT_ID`.
4. **For specific-user lookup only:** `User identifier (GUID)?` — run `uip gov aops-policy deployment user list --output json` if unknown (each entry carries `identifier`, `name`, `source`). Store as `$USER_ID`. Then ensure the S2S bearer token is available — set `UIP_S2S_TOKEN` in the caller's environment so the CLI picks it up automatically (see [aops-policy-commands.md — S2S token](./aops-policy-commands.md#s2s-token)).

Proceed to the matching query below.

---

## Get the effective deployed policy (default — caller's own identity)

Returns the single effective policy for the caller for the given `(licenseType, product, tenant)` — the policy that remains after the user → group → tenant inheritance chain has been walked. Uses the caller's `uip login` token. To look up another user's effective policy, add `--s2s-token --user-id`; to skip user/group overrides and see only the tenant-level assignment, add `--s2s-token --tenant-only`.

```bash
uip gov aops-policy deployed-policy get \
  "$LICENSE_TYPE" "$PRODUCT_NAME" "$TENANT_ID" \
  --output json
```

Parse `Data` — it carries `policyIdentifier`, `name`, and `data` — and display:

```text
Effective policy:
  Policy name:     <NAME>
  Policy ID:       <POLICY_IDENTIFIER>
  Product:         <PRODUCT_NAME>
  License type:    <LICENSE_TYPE>
  Tenant:          <TENANT_ID>
  Data payload:    <DATA — pretty-print or attach as a link to a saved file>
```

If `Data` is `{ "Message": "No policy applies." }`, `null`, `{}`, or absent, inform the user that no policy applies for this `(licenseType, product, tenant)`. This happens when no rule matches and no default exists — the service returns HTTP 204.

---

## Get the effective deployed policy for a specific user (S2S)

Requires an S2S bearer token. Returns the effective policy for the named user after the full user → group → tenant chain is walked.

```bash
export UIP_S2S_TOKEN="<TOKEN>"          # CLI reads this automatically

uip gov aops-policy deployed-policy get \
  "$LICENSE_TYPE" "$PRODUCT_NAME" "$TENANT_ID" \
  --user-id "$USER_ID" \
  --output json
```

The flag is `--user-id`, **not** `--user-identifier`.

---

## Get the tenant-level policy only (S2S)

Explicitly bypasses any user/group chain consideration. Requires an S2S bearer token.

```bash
export UIP_S2S_TOKEN="<TOKEN>"          # CLI reads this automatically

uip gov aops-policy deployed-policy get \
  "$LICENSE_TYPE" "$PRODUCT_NAME" "$TENANT_ID" \
  --tenant-only \
  --output json
```

---

## List every applicable policy for the calling user

Returns every policy that applies to the caller for the given `(licenseType, product, tenant)`, in priority order. Unlike `get`, which returns only the single effective (top-priority) policy, `list` surfaces every applicable entry so you can see why a particular policy wins. **User token only — does NOT accept `--s2s-token`.** Returns an empty array when nothing applies.

```bash
uip gov aops-policy deployed-policy list \
  "$LICENSE_TYPE" "$PRODUCT_NAME" "$TENANT_ID" \
  --output json
```

Parse `Data` (an array of applicable policies in priority order). Each entry has `policyIdentifier`, `name`, `priority`, and `source` — one of `User`, `Group`, or `Tenant`. Render as a table:

```text
Applicable policies (highest-precedence first):
  Source    Priority   Name                           Policy ID
  User      20         Restricted StudioX Policy      <POLICY_ID>
  Tenant    10         Baseline StudioX Policy        <POLICY_ID>
```

Use this when the user asks:

- "Why is this policy winning for me?"
- "What is my effective policy, and where does each entry come from?"
- "Which of my policy settings came from tenant vs group vs user?"

To inspect applicable policies for another user, log in as that user, or call `deployed-policy get --s2s-token --user-id <id>` (note: `get` returns only the single effective policy, not the full list).

---

## Debug

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | User token expired (or S2S token missing/expired for S2S modes) | `uip login` for user-token modes; re-export `UIP_S2S_TOKEN` for S2S modes — see [aops-policy-commands.md — Authentication](./aops-policy-commands.md#authentication) |
| `Data` is `{ "Message": "No policy applies." }` / `null` / `{}` on `get` | Service returned HTTP 204 — no rule matched and no default exists | Inform the user; confirm the tenant has a deployment via [aops-policy-deploy-guide.md](./aops-policy-deploy-guide.md) |
| `Data` is `[]` on `list` | No policies apply in this context | Inform the user; verify that the user, product, and license type are all valid in the calling tenant |
| `--user-id` rejected / `unknown flag --user-identifier` | Called without an S2S token, or used the old flag name | The flag is `--user-id`, not `--user-identifier`. Either drop `--user-id` (query the caller's own policy) or `export UIP_S2S_TOKEN="<TOKEN>"` before the call (fallback: pass `--s2s-token "$UIP_S2S_TOKEN"`) |
| `--tenant-only` rejected | Passed without `--s2s-token` | Same as above — `--tenant-only` is an S2S-only mode |
| `--s2s-token` rejected on `list` | `deployed-policy list` does not accept S2S tokens | Remove `--s2s-token`; re-run under `uip login` |
| User cannot provide a tenant identifier | Tenant GUID unknown | Retrieve from Orchestrator or UiPath Cloud portal |

---

## Related commands

- [aops-policy-commands.md](./aops-policy-commands.md) — full `deployed-policy` command reference and authentication modes.
- [aops-policy-deploy-guide.md](./aops-policy-deploy-guide.md) — assign a policy before querying it.
