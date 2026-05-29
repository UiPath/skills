# Policy Deploy Guide

Assign policies to a user, group, or tenant by writing a JSON assignment file and passing it to `deployment <subject> configure --input`.

> **Non-interactive.** The agent drives the full flow. Build the JSON file from the user's stated intent (or prompt them to choose per product), call `configure --input`, then verify with `deployment <subject> get`. Do NOT launch `configure` without `--input` — that path is removed.

## Prerequisites

- User must be logged in — see [aops-policy-commands.md — Authentication](./aops-policy-commands.md#authentication).
- You have the target subject identifier (user / group / tenant GUID). If not, use the matching `list` subcommand — see [aops-policy-commands.md — deployment](./aops-policy-commands.md#uip-gov-aops-policy-deployment-usergrouptenant).
- You have a session directory for scratch files. Reuse `$SESSION_DIR` from the configure-policy-data session if one exists, or create a new one:
  ```bash
  SESSION_DIR="./aops-sessions/$(date +%Y%m%d-%H%M%S)-$(uuidgen | cut -c1-8 | tr '[:upper:]' '[:lower:]')"
  mkdir -p "$SESSION_DIR"
  ```
- For every deployment subcommand's flags, see [aops-policy-commands.md — deployment](./aops-policy-commands.md#uip-gov-aops-policy-deployment-usergrouptenant).

---

## Input file shape

| Subject | JSON shape |
|---------|------------|
| user   | `[{ "productIdentifier": "<PRODUCT_NAME>", "policyIdentifier": "<POLICY_GUID>\|null" }, ...]` |
| group  | `[{ "productIdentifier": "<PRODUCT_NAME>", "policyIdentifier": "<POLICY_GUID>\|null" }, ...]` |
| tenant | `[{ "productIdentifier": "<PRODUCT_NAME>", "licenseTypeIdentifier": "<LICENSE_TYPE_GUID>", "policyIdentifier": "<POLICY_GUID>\|null" }, ...]` |

Semantics:

- `productIdentifier` — product `name` (not label). See [aops-policy-commands.md — product list](./aops-policy-commands.md#uip-gov-aops-policy-product-list).
- `licenseTypeIdentifier` (tenant only) — license type **`identifier` (GUID)** from `license-type list`, not the `name` and not the label. See [aops-policy-commands.md — license-type list](./aops-policy-commands.md#uip-gov-aops-policy-license-type-list).
- `policyIdentifier`:
  - a policy GUID → assign that policy to this product (and license type, for tenants)
  - `null` → **No Policy** explicitly (overrides any inherited policy)
  - **Omit the entry entirely** → inherit (user/group inherits from tenant; tenant inherits from global)

---

## Deployment precedence

When the same product has assignments at multiple scopes, the narrowest wins:

> **User > Group > Tenant**

- A **user** assignment (including explicit `null` = No Policy) overrides any group or tenant assignment for that product.
- A **group** assignment overrides the tenant assignment for that product (for members of that group).
- A **tenant** assignment is the org-wide default for a `(product, license type)` pair.
- A product with no assignment at any scope → inherits the global default (no policy enforced).

**Decision hint:** pick the narrowest scope that matches the user's ask.

> **Precedence is NOT Priority.** The User > Group > Tenant chain above is pure scope resolution — AOps walks it and picks the first level that has an assignment for the product. The policy's `--priority` value is a separate concept and plays no role here. Priority only breaks ties **within the group level**, when a single user belongs to multiple groups that each have their own policy for the same product. See [SKILL.md — Priority rules](./aops-policy-overview-guide.md#priority-rules).

| User's ask | Correct scope |
|-----------|---------------|
| "Apply only to Alice" / "exception for jdoe" | user |
| "Apply to the Developers team" / "everyone in group X" | group |
| "Everyone in the tenant" / "org-wide default" | tenant |
| "Everyone except Alice" | tenant + user-level `null` override for Alice |

> **Do not deploy at a broader scope than requested.** If the user says "only for Alice", do not touch tenant or group — a tenant change affects every other user who currently inherits from it.

## License-type → product compatibility

Tenant deployments are keyed by `(product, license type)`. Not every license carries every product — deploying a policy to a `(product, license type)` pair whose license does not include that product is a no-op. Common license → product mappings:

| License type | Products included |
|--------------|-------------------|
| RPA Developer | Studio, StudioX, Assistant, Robot |
| Automation Developer | Studio, StudioX, Assistant, Robot |
| Citizen Developer | StudioX, Assistant, Robot |
| Attended Robot | Assistant, Robot |
| Unattended Robot | Robot |
| Tester | Studio, Robot |

> Always check the live list via `uip gov aops-policy license-type list --output json` — org-specific license types may exist. See [aops-policy-commands.md — license-type list](./aops-policy-commands.md#uip-gov-aops-policy-license-type-list).

If the user asks to deploy (for example) an Assistant policy to the `Unattended Robot` license, push back — Unattended Robot has no Assistant slot, so the assignment will have no effect.

---

## Subject decision matrix

| User intent | Subject | Section |
|-------------|---------|---------|
| "Apply to Alice" / a named individual | user | [3.1](#31-deploy-to-a-user) |
| "Apply to the Developers group" / named team | group | [3.2](#32-deploy-to-a-group) |
| "Apply to everyone in the tenant" | tenant | [3.3](#33-deploy-to-a-tenant) |
| "Apply to a license type org-wide" (requires license type) | tenant | [3.3](#33-deploy-to-a-tenant) |

---

## 3.1 Deploy to a user

### Step 1 — Identify the user

Run `uip gov aops-policy deployment user list --output json` (see [commands reference](./aops-policy-commands.md#deployment-usergrouptenant-list)).

Parse `Data.result[]` (output shape in [aops-policy-commands.md — deployment list](./aops-policy-commands.md#deployment-usergrouptenant-list)). Display as a numbered list:

```text
Governance users:
  1. alice@example.com    (source: cloud)    <USER_ID>
  2. bob@example.com      (source: cloud)    <USER_ID>
```

- If only one user exists, use it automatically and inform the user.
- If one entry's `name` or `email` matches the current login (from `uip login status`), suggest it as the default.
- The list contains only users the governance service has already seen — it is not a full IdP roster. If the target user is missing, fall back to the IdP:

  1. Run `uip admin users list --search "<NAME_OR_EMAIL>" --output json` (see [/uipath:uipath-admin — user-management.md](../../../uipath-admin/references/user-management.md)).
  2. From the matched record, take `id` as `$USER_ID`, `displayName` (or `userName`) as `$USER_DISPLAY_NAME`, and `email` as `$USER_EMAIL`. Set `$USER_SOURCE` from the IdP origin (`cloud`, `local`, `aad`).
  3. `configure` auto-registers the user via the `AddUser` endpoint on first call — no separate registration step is needed.
  4. If the IdP search also returns nothing, ask the caller to supply the GUID, display name, and email directly.

Store the chosen user's `identifier` as `$USER_ID`, its `name` as `$USER_DISPLAY_NAME`, its `email` as `$USER_EMAIL`, and its `source` as `$USER_SOURCE`. `$USER_DISPLAY_NAME`, `$USER_EMAIL`, and `$USER_SOURCE` are all passed to `configure` in the next step.

### Step 2 — Pick policies per product (pre-fill defaults; prompt only on ambiguity)

**Skip rule:** if the user's original request already named the product(s) and policy(s) to assign, use those directly — do not re-ask.

1. Run `uip gov aops-policy product list --output json` to enumerate products (show `label` and `name`, no internal flags).
2. For each product the user wants to assign, run `uip gov aops-policy list --product-name "<PRODUCT_NAME>" --output json` to list candidate policies. Auto-match to the user's stated intent; prompt only if the intent is ambiguous or missing.
3. Fetch the current assignments to build the diff: `uip gov aops-policy deployment user get "$USER_ID" --output json`. **Do NOT prompt for confirmation here** — confirmation happens at Step 4 only.

### Step 3 — Write the assignment file

```bash
cat > "$SESSION_DIR/user-policies.json" <<'EOF'
[
  { "productIdentifier": "AITrustLayer", "policyIdentifier": "<POLICY_GUID>" },
  { "productIdentifier": "Development",  "policyIdentifier": null }
]
EOF
```

> Only include products whose assignment should change. Omitted products keep their current assignment (inherit from tenant). Use `null` to explicitly clear an assignment (No Policy).

### Step 4 — Final review before configure (single confirmation gate)

This is the **only** yes/no confirmation in the user-deploy flow (Critical Rule #12). Present the full assignment file plus a diff vs the current state:

```text
Deploying policies to <USER_DISPLAY_NAME>:
  AI Trust Layer  →   aitl-test-policy   (<POLICY_ID>)
  Studio          →   (No Policy)
Omitted products inherit from the tenant.

Apply these changes to <USER_DISPLAY_NAME>? (yes / no)
```

Do NOT proceed without an explicit `yes`.

### Step 5 — Save the assignments

> **FULL-REPLACE semantics.** `configure` is not a merge. Any product not listed in `$SESSION_DIR/user-policies.json` is removed from the user's override list, and the user falls back to group/tenant inheritance for that product. To preserve existing overrides, seed the input file from `deployment user get "$USER_ID"` before adding or editing entries.

```bash
uip gov aops-policy deployment user configure "$USER_ID" \
  --user "$USER_DISPLAY_NAME" \
  --email "$USER_EMAIL" \
  --source "$USER_SOURCE" \
  --input "$SESSION_DIR/user-policies.json" \
  --output json
```

The flag is `--user`, **not** `--user-name`. `--source` defaults to `local`; pass the identity-provider source from the `list` entry (e.g. `cloud`, `aad`) so the stored override stays consistent with the upstream identity record. `--email` is used only when governance auto-registers a brand-new user on this call (`AddUser` path); for already-registered users it is ignored. When omitted, it defaults to `--user`. Pass it explicitly whenever the IdP supplied a distinct email so the audit record carries the right address.

### Step 6 — Verify

```bash
uip gov aops-policy deployment user get "$USER_ID" --output json
```

`Data` is an array of `{ productIdentifier, policyIdentifier }`. Show the saved per-product assignments and confirm they match the plan.

---

## 3.2 Deploy to a group

### Step 1 — Identify the group

Run `uip gov aops-policy deployment group list --output json`. Parse `Data.result[]` (output shape in [aops-policy-commands.md — deployment list](./aops-policy-commands.md#deployment-usergrouptenant-list)). Display as a numbered list and let the user pick. Store the chosen group's `identifier` as `$GROUP_ID`, its `name` as `$GROUP_DISPLAY_NAME`, and its `source` as `$GROUP_SOURCE`.

If the group is not yet known to the governance service, fall back to the IdP:

1. Run `uip admin groups list --output json` and filter client-side: `--output-filter "Data[?contains(displayName, '<NAME>')]"`. `uip admin groups list` has **no** `--search` flag (see [/uipath:uipath-admin — group-management.md](../../../uipath-admin/references/group-management.md)).
2. From the matched record, take `id` as `$GROUP_ID` and `displayName` as `$GROUP_DISPLAY_NAME`. Set `$GROUP_SOURCE` from the IdP origin.
3. `configure` auto-registers the group via the `AddGroup` endpoint on first call — no separate registration step is needed.
4. If the IdP lookup also returns nothing, ask the caller to supply the GUID and display name directly.

### Step 2 — Pick policies per product (pre-fill defaults; prompt only on ambiguity)

Same as [3.1 Step 2](#step-2--pick-policies-per-product-pre-fill-defaults-prompt-only-on-ambiguity): enumerate products, list candidate policies per product, auto-match to intent, fetch current assignments via `deployment group get "$GROUP_ID"` for the diff.

### Step 3 — Write the assignment file

```bash
cat > "$SESSION_DIR/group-policies.json" <<'EOF'
[
  { "productIdentifier": "AITrustLayer", "policyIdentifier": "<POLICY_GUID>" },
  { "productIdentifier": "Development",  "policyIdentifier": null }
]
EOF
```

Same semantics as the user variant — include only products whose assignment should change.

### Step 4 — Final review before configure (single confirmation gate)

```text
Deploying policies to <GROUP_DISPLAY_NAME>:
  AI Trust Layer  →   aitl-test-policy   (<POLICY_ID>)
  Studio          →   (No Policy)
Omitted products inherit from the tenant.

Apply these changes to <GROUP_DISPLAY_NAME>? (yes / no)
```

Do NOT proceed without an explicit `yes`.

### Step 5 — Save the assignments

> **FULL-REPLACE semantics.** Any product not listed in `$SESSION_DIR/group-policies.json` is removed from the group's override list; its members then fall back to tenant inheritance (unless a per-user override exists). To preserve existing overrides, seed the input from `deployment group get "$GROUP_ID"` first.

```bash
uip gov aops-policy deployment group configure "$GROUP_ID" \
  --group "$GROUP_DISPLAY_NAME" \
  --source "$GROUP_SOURCE" \
  --input "$SESSION_DIR/group-policies.json" \
  --output json
```

The flag is `--group`, **not** `--group-name`. `--source` defaults to `local`; pass the upstream IdP source (e.g. `cloud`, `aad`) from the `list` entry.

### Step 6 — Verify

```bash
uip gov aops-policy deployment group get "$GROUP_ID" --output json
```

`Data` is an array of `{ productIdentifier, policyIdentifier }`. Show the saved per-product assignments and confirm they match the plan.

---

## 3.3 Deploy to a tenant

### Step 1 — Identify the license type

Tenant deployments are keyed by `(product, license type)`. List license types via `uip gov aops-policy license-type list --output json` — see [aops-policy-commands.md — license-type list](./aops-policy-commands.md#uip-gov-aops-policy-license-type-list) for the full output shape and sample rendering.

> **Use the license type's `identifier` (GUID) — not its `name`, not its label — as `licenseTypeIdentifier` in tenant assignment entries.** The `name` is only accepted by `deployed-policy get` / `deployed-policy list` as the positional `<license-type>` argument.

### Step 2 — Identify the tenant

```bash
uip gov aops-policy deployment tenant list --output json
```

Optional flags: `--product-name <PRODUCT_NAME>`, `--limit <N>`, `--offset <N>`.

> `tenant list` triggers an upstream OMS sync before returning, so freshly created or recently re-enabled tenants show up here without a separate registration step. The first call after a tenant change may take longer.

Parse `Data.result[]` (output shape in [aops-policy-commands.md — deployment list](./aops-policy-commands.md#deployment-usergrouptenant-list)). Each tenant entry carries `tenantPolicies[]` — the current assignments, each keyed by `(productIdentifier, licenseTypeIdentifier, policyIdentifier)`. Let the user pick, then store the chosen tenant's `identifier` as `$TENANT_ID` and `name` as `$TENANT_NAME`.

### Step 3 — Pick policies per `(product, license type)`

1. For each `(product, license type)` pair the user wants to assign, run `uip gov aops-policy list --product-name "<PRODUCT_NAME>" --output json` and pick a policy (or match the user's intent).
2. Fetch current assignments: `uip gov aops-policy deployment tenant get "$TENANT_ID" --output json`.

### Step 4 — Write the assignment file

```bash
cat > "$SESSION_DIR/tenant-policies.json" <<'EOF'
[
  { "productIdentifier": "AITrustLayer", "licenseTypeIdentifier": "<NOLICENSE_GUID>",    "policyIdentifier": "<POLICY_GUID>" },
  { "productIdentifier": "Development",  "licenseTypeIdentifier": "<DEVELOPMENT_GUID>",  "policyIdentifier": null }
]
EOF
```

> `licenseTypeIdentifier` is the GUID from `license-type list` (`Data[].identifier`), NOT the license-type `name`. Resolve each license type's GUID from Step 1 before writing the file.

### Step 5 — Final review before configure (single confirmation gate)

```text
Deploying policies to <TENANT_NAME>:
  AI Trust Layer  / NoLicense    →   aitl-default  (<POLICY_ID>)
  Studio          / Development  →   (No Policy)
Omitted (product, license type) pairs keep their current assignment.

Apply these changes to <TENANT_NAME>? (yes / no)
```

Do NOT proceed without an explicit `yes`.

### Step 6 — Save the assignments

> **FULL-REPLACE semantics.** Any `(product, license type)` pair not listed in `$SESSION_DIR/tenant-policies.json` is removed from the tenant and reverts to "no pin". To preserve existing assignments, seed the input file from `deployment tenant get "$TENANT_ID"` before editing.

```bash
uip gov aops-policy deployment tenant configure "$TENANT_ID" \
  --tenant-name "$TENANT_NAME" \
  --input "$SESSION_DIR/tenant-policies.json" \
  --output json
```

### Step 7 — Verify

```bash
uip gov aops-policy deployment tenant get "$TENANT_ID" --output json
```

`Data` is `{ identifier, name, tenantPolicies: [ { productIdentifier, licenseTypeIdentifier, policyIdentifier } ] }`.

---

## Remove assignments

> **Destructive.** Always show the current assignments (`deployment <subject> get`) and get explicit `yes` confirmation before running `delete` or `remove`.

### Remove all policy assignments for a user or group

Use `delete` to strip every assignment in one call. The subject itself remains in the governance system; only the policy mappings are removed.

```bash
uip gov aops-policy deployment user  delete "$USER_ID"  --output json
uip gov aops-policy deployment group delete "$GROUP_ID" --output json
```

Confirmation prompt (verbatim): `Delete all policy assignments for <SUBJECT_NAME>? This cannot be undone. (yes / no)`

### Remove a tenant's assignment for one product (optionally one license type)

Use `remove` for scoped removal. Prefer `remove` over re-running `configure` with `policyIdentifier: null` when the goal is to drop the mapping entirely (setting `null` keeps an explicit "No Policy" override, which still wins over inherited assignments at a higher scope).

```bash
uip gov aops-policy deployment tenant remove "$TENANT_ID" \
  --product-name "$PRODUCT_NAME" \
  --output json
```

Add `--license-type <LICENSE_TYPE_NAME>` to remove only one license-type entry for that product. Omit it to remove every license-type entry for the product.

Confirmation prompt (verbatim): `Remove <PRODUCT_LABEL> assignment from <TENANT_NAME>? This cannot be undone. (yes / no)`

---

## Debug

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | User token expired or missing | `uip login` and retry — see [aops-policy-commands.md — Authentication](./aops-policy-commands.md#authentication) |
| `unknown productIdentifier` | Used the product label instead of its `name` | Re-run `uip gov aops-policy product list --output json` and pass the `name` field |
| `unknown licenseTypeIdentifier` | Used the license `name` or label instead of its `identifier` (GUID) | Re-run `uip gov aops-policy license-type list --output json` and copy the `identifier` field (GUID) |
| `unknown policyIdentifier` (GUID) | Stale or wrong policy GUID | Re-run `uip gov aops-policy list --product-name "<PRODUCT_NAME>" --output json` and copy the `identifier` |
| `missing licenseTypeIdentifier in tenant entries` | Tenant entry omitted `licenseTypeIdentifier` | Add it to every tenant-subject entry (required key) |
| `configure rejects the JSON` | Any of the above + malformed array | Validate with `jq type` and `jq '.[0] | keys'` before resubmitting |
| `unknown flag --user-name` / `--group-name` | Flag renamed | Use `--user` (user configure) or `--group` (group configure). Only `tenant configure` uses `--tenant-name`. |
| Existing assignments disappear after `configure` | Treated `configure` as merge | `configure` is FULL-REPLACE — seed the input file from `deployment <subject> get` before adding/modifying entries |
| `deployment user list` / `group list` returns no results | Subject not yet seen by the governance service (governance only lists subjects with prior overrides) | Resolve from the IdP via the Step 1 fallback (`uip admin users list --search` for users, `uip admin groups list` for groups). `configure` auto-registers the subject on first call via `AddUser` / `AddGroup` — no separate onboarding step needed. |
| User cannot provide a tenant identifier | Tenant GUID unknown | Retrieve from Orchestrator or UiPath Cloud portal |
| `null` assignment still inherited at a higher scope | User assumed `null` removed the mapping | `null` means explicit "No Policy" (overrides inheritance); use `tenant remove` (or omit the entry) to restore inheritance |

---

## Related commands

- [aops-policy-commands.md](./aops-policy-commands.md) — every deployment flag and output shape used above.
- [aops-policy-manage-guide.md](./aops-policy-manage-guide.md) — create the policy before deploying it.
- [aops-policy-deployed-guide.md](./aops-policy-deployed-guide.md) — verify assignment took effect, or query effective rules after chain resolution.
