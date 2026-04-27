# uip gov aops-policy — CLI Command Reference

Single source of truth for every `uip gov aops-policy` subcommand, its flags, and its output shape. All commands output `{ "Result": "Success"|"Failure", "Code": "...", "Data": { ... } }`. Use `--output json` for programmatic use — every command in this skill must pass it.

> For task workflows (create / update / delete / deploy / query), see the matching `*-guide.md`. This file only documents the command surface.

---

## uip gov aops-policy list

List policies (optionally filtered by product).

```bash
uip gov aops-policy list --output json
```

**Flags:**

| Flag | Required | Description |
|------|----------|-------------|
| `--product-name <PRODUCT_NAME>` | no | Filter by product name (identifier, not label) |
| `--product-label <PRODUCT_LABEL>` | no | Filter by product label |
| `--search <TERM>` | no | Search by name |
| `--limit <N>` | no | Page size (default: 20) |
| `--offset <N>` | no | Page index, 0-based (default: 0) |
| `--order-by <FIELD>` | no | Sort field (e.g. `priority`, `name`) |
| `--order-direction <asc\|desc>` | no | Sort direction |

**Output:** `Data` is an array of `PolicyDto`. Each entry has `identifier`, `name`, `productName`, `priority`, and `availability`. `productName` is a flat string (the product identifier) — not a nested `product.{name,label}` object. An empty array means no policies matched.

---

## uip gov aops-policy get

Fetch a single policy by GUID. Always run before `update` or `delete`.

```bash
uip gov aops-policy get <POLICY_IDENTIFIER> --output json
```

**Output:** `Data` is a `PolicyDto` with `identifier`, `name`, `productName`, `priority`, `availability`, and `data`. `Data.data` is the full form-data blueprint — save it to reuse as the update input (see [aops-policy-manage-guide.md — Update](./aops-policy-manage-guide.md#update-a-policy)).

---

## uip gov aops-policy create

Create a new policy.

```bash
uip gov aops-policy create \
  --name "<POLICY_NAME>" \
  --product-name "<PRODUCT_NAME>" \
  --input "<SESSION_DIR>/aops-policy-data.json" \
  --output json
```

**Flags:**

| Flag | Required | Description |
|------|----------|-------------|
| `--name <POLICY_NAME>` | yes | Policy display name. Must be non-empty. |
| `--product-name <PRODUCT_NAME>` | yes | Product identifier (name, not label). |
| `--input <PATH>` | no | Path to the policy-data JSON. This is the filled form-data blueprint — a flat key/value object, with no `{ "data": {...} }` wrapper; the CLI wraps it under `{ data: ... }` before submission. Omit only when the policy has no data payload. |
| `--description <TEXT>` | no | Free-form description. Omit entirely if unset — do not pass an empty string. |
| `--priority <N>` | no | Integer rank used **only as a group-level tie-breaker** when a user is in multiple groups with competing policies for the same product — then the lowest priority number wins. Priority does NOT determine user / group / tenant precedence (that's the scope-resolution chain) and has no effect at the user or tenant level. See [SKILL.md — Priority rules](../SKILL.md#priority-rules). |
| `--availability <DAYS>` | no | Offline grace period — the number of days the client (e.g. Studio, Assistant) will keep applying the cached copy of this policy when it cannot reach Automation Ops. Integer > 0. Sending `0` is normalized by the server to `30`. When multiple products contribute to a merged policy response, the smallest `availability` across contributors is used. Only pass when the user explicitly supplies a value — otherwise rely on the server default. |

**Output:** `Data.identifier` (new policy GUID), `Data.name`, `Data.productName` (confirmed product identifier — flat string, not a nested object).

---

## uip gov aops-policy update

Update an existing policy. **Full replacement, not a patch** — every field you want to keep must be passed again, including `--name`, `--product-name`, `--description`, `--priority`, `--availability`, AND `--input`. Omitting any of these flags CLEARS that field on the server. `--product-name` must match the policy's existing product (changing product on update is not supported).

```bash
uip gov aops-policy update \
  --identifier "<POLICY_IDENTIFIER>" \
  --name "<POLICY_NAME>" \
  --product-name "<PRODUCT_NAME>" \
  --description "<DESCRIPTION>" \
  --priority <N> \
  --input "<SESSION_DIR>/aops-policy-data.json" \
  --output json
```

**Flags:**

| Flag | Required | Description |
|------|----------|-------------|
| `--identifier <GUID>` | yes | Target policy GUID (from `list` or `get`). |
| `--name <POLICY_NAME>` | yes | Policy name. Required on every update — pass the existing value to preserve it, or a new value to change it. |
| `--product-name <PRODUCT_NAME>` | yes | Must match the policy's existing product (changing product on update is not supported). |
| `--description <TEXT>` | conditional | **Full-replace**: omitting this flag CLEARS the description on the server. To preserve the existing value, re-pass it from `policy get`. |
| `--priority <N>` | conditional | **Full-replace**: omitting this flag CLEARS priority on the server. To preserve the existing value, re-pass it from `policy get`. |
| `--availability <DAYS>` | conditional | Offline grace period in days (see [create](#uip-gov-aops-policy-create) for semantics). **Full-replace**: omitting this flag CLEARS availability on the server. To preserve the existing value, re-pass it from `policy get`. |
| `--input <PATH>` | conditional | **Full-replace**: omitting this flag CLEARS the data payload. To preserve existing data, save `Data.data` from `policy get` to a file and re-pass it. Points at the raw form-data object (no `{ "data": {...} }` wrapper). |

> **Template upgrade in progress.** `update` fails with a `template upgrade in progress` error if the underlying Form.io template is being migrated; retry once the upgrade completes.

**Output:** `Data` carries the updated policy's `identifier`, `name`, and `productName`.

---

## uip gov aops-policy delete

Delete a policy. **Destructive — cannot be undone.** Always run `get` first and confirm with the user.

```bash
uip gov aops-policy delete <POLICY_IDENTIFIER> --output json
```

> **Fails if the policy is still assigned.** Deletion is blocked if the policy is referenced by any tenant, user, or group assignment. Clear the references first — run `deployment tenant|user|group remove` (or `configure` with a filtered list) on every subject — then retry delete.

**Output:** `Result: "Success"` on deletion. `Data.Status` is `"Deleted"` and `Data.identifier` echoes the deleted GUID.

---

## uip gov aops-policy product list

List products that support governance policies. Products are read-only — registered by the governance service, not created via the CLI.

```bash
uip gov aops-policy product list --output json
```

**Output:** `Data` is an array of product entries. Each entry has `identifier` (GUID), `name`, and `label`. Pass `name` (not `label`) to `--product-name`, `template get`, and every `deployment ... configure` entry; `label` is the human-readable display string.

## uip gov aops-policy product get

Fetch a single product record to confirm a product name exists before using it.

```bash
uip gov aops-policy product get <PRODUCT_NAME_OR_GUID> --output json
```

The positional argument accepts either the product `name` (e.g. `StudioX`) or its GUID.

**Output:** `Data` has `identifier`, `name`, `label`.

> In the create flow, prefer the bootstrap from `template list` over `product list`. The bootstrap materializes every product's full schema plus catalog metadata in one call — see [configure-aops-policy-data-guide.md — Step 1](./configure-aops-policy-data-guide.md#step-1--bootstrap-load-all-products-and-their-templates-create-flow-only).

---

## uip gov aops-policy license-type list

List license types available to the organization. Required for tenant deployment, where assignments are keyed by `(product, licenseType)`.

```bash
uip gov aops-policy license-type list --output json
```

**Output:** `Data` is an array. Each entry has `identifier` (GUID) and `name` (e.g. `Attended`, `Unattended`).

Sample rendering:

```text
Available license types:
  1. Attended        (identifier: a1b2c3d4-0000-0000-0000-0000000000A1)
  2. Unattended      (identifier: a1b2c3d4-0000-0000-0000-0000000000A2)
```

> **Two different identifiers — do not confuse them:**
> - For `deployment tenant configure` entries, the JSON `licenseTypeIdentifier` field takes the license type's **`identifier` (GUID)** from `license-type list`.
> - For `deployed-policy get` / `deployed-policy list`, the positional `<licenseType>` argument takes the license type's **`name`** (e.g. `Attended`).

---

## uip gov aops-policy template list

Fetch every product's form template, default form data, and locale resource in one call. This is the create-flow bootstrap.

```bash
uip gov aops-policy template list --output-dir "<SESSION_DIR>/products" --output json
```

**Flags:**

| Flag | Required | Description |
|------|----------|-------------|
| `--output-dir <DIR>` | yes | Directory where per-product subfolders are written. |

**Output:** writes three files per product into `<output-dir>/<ProductName>/`:

| File | Purpose |
|------|---------|
| `form-template.json` | Raw form.io DTO returned by the governance API. Top-level `.product` object `{name, label}` is the catalog entry. |
| `form-data.json` | Fillable blueprint — a flat key/value object generated from the template. Display-only components (`hidden`, `button`, `submit`, `htmlelement`, `content`) are omitted. Fields without an explicit default get a type-appropriate default: `false` for checkbox, `[]` for editgrid, `{}` for selectboxes, and `null` for text/select. |
| `form-template-locale-resource.json` | Locale-resolved reference. Every product-scoped locale key is replaced with its English string; a sibling `<prop>-key` preserves the original key for traceability. `defaultData.data` is replaced with a flat, annotated per-field map `{ value, type, label, description?, tooltip? }`. Select and selectboxes option labels appear under `template.components[...].values[].label`. Cross-product keys (e.g. `AutomationOps.submit`) are left unresolved. |

Per-product failures are collected and do not abort; the command exits non-zero only if every product fails. Do NOT create a separate `products.json` — enumerate `<output-dir>/*/form-template.json` and read each file's top-level `product` object.

> **Template versions.** Templates are versioned per product release (e.g. `22.4`, `23.10`, `24.10.1`). The CLI returns the template matching the current product release in the target org. Governance knobs present only in a newer template will be silently ignored by older Studio/Assistant/Robot installs. If the user mentions a specific product version, confirm the returned template's version matches before configuring rules that depend on newer knobs. Run `uip gov aops-policy template list --help` to discover any version-selection flag available on your CLI build.

---

## uip gov aops-policy template get

Fetch a single product's template (update flow — product already known). The positional argument takes the product `name` or `identifier` (GUID).

```bash
uip gov aops-policy template get <PRODUCT_NAME> \
  --output-form-data "<DIR>/form-data.json" \
  --output-template-locale-resource "<DIR>/form-template-locale-resource.json" \
  --output json \
  | jq '.Data.template' > "<DIR>/form-template.json"
```

**Flags:**

| Flag | Required | Description |
|------|----------|-------------|
| `--output-form-data <PATH>` | no | Write the fillable form-data blueprint JSON (the object you edit and submit back on create/update). |
| `--output-template-locale-resource <PATH>` | no | Write the locale-resolved template reference JSON (open this to understand every field, its options, descriptions, tooltips, and validation rules). |

**Output:**
- When both output flags are passed, `Data` has `formDataFile` and `templateLocaleResourceFile` — the absolute paths of the written files.
- When neither output flag is passed, the template and form-data are returned inline as `Data.template` and `Data.formData` (useful for piping or scripting). If `Data.template` is missing in this mode, stop and surface the error.

---

## uip gov aops-policy deployment {user|group|tenant}

Deployment subcommands assign policies to a subject. For the full workflow, see [aops-policy-deploy-guide.md](./aops-policy-deploy-guide.md).

### Input file shape

The `--input` payload is an array of per-product assignments. Semantics are the same for all three subjects; the tenant variant adds `licenseTypeIdentifier`.

| Subject | JSON shape |
|---------|------------|
| `user`  | `[{ "productIdentifier": "<PRODUCT_NAME>", "policyIdentifier": "<POLICY_GUID>\|null" }, ...]` |
| `group` | `[{ "productIdentifier": "<PRODUCT_NAME>", "policyIdentifier": "<POLICY_GUID>\|null" }, ...]` |
| `tenant` | `[{ "productIdentifier": "<PRODUCT_NAME>", "licenseTypeIdentifier": "<LICENSE_TYPE_GUID>", "policyIdentifier": "<POLICY_GUID>\|null" }, ...]` |

- `productIdentifier` — product `name` (not label). See [product list](#uip-gov-aops-policy-product-list).
- `licenseTypeIdentifier` (tenant only) — license type **`identifier` (GUID)** from `license-type list`, not the `name` and not the label. See [license-type list](#uip-gov-aops-policy-license-type-list).
- `policyIdentifier`:
  - a GUID → assign that policy for this product (and license type, for tenants)
  - `null` → **No Policy** (explicitly overrides any inherited policy)
  - **Omit the entry entirely** → inherit (user/group inherits from tenant; tenant inherits from global)

### deployment {user|group|tenant} list

List subjects with existing policy assignments.

```bash
uip gov aops-policy deployment user   list --output json
uip gov aops-policy deployment group  list --output json
uip gov aops-policy deployment tenant list --output json
```

Optional: `--limit <N>` (default 20), `--offset <N>` (zero-based page index, default 0). Tenant variant also accepts `--product-name <PRODUCT_NAME>` to scope results to tenants with an assignment for that product.

**Output:** `Data` is an array.
- User entries: `identifier`, `name`, and `source` (the identity-provider source — e.g. `cloud`, `local`, `aad`). This is **not** a full IdP roster; it includes only users the governance service has already seen.
- Group entries: `identifier`, `name`, `source`. Typically only groups that have at least one policy override are returned.
- Tenant entries: `identifier`, `name`, and `tenantPolicies[]`. Each policy entry carries `productIdentifier`, `licenseTypeIdentifier` (GUID), and `policyIdentifier`.

### deployment {user|group|tenant} get

Fetch current assignments for a subject. Returns only **explicit** overrides at the queried level — no chain resolution. Returns an empty array when the subject has no overrides. For the effective runtime policy after chain resolution, use `deployed-policy get`.

```bash
uip gov aops-policy deployment user   get <USER_ID>   --output json
uip gov aops-policy deployment group  get <GROUP_ID>  --output json
uip gov aops-policy deployment tenant get <TENANT_ID> --output json
```

**Output:**
- User/group `get`: `Data` is an array of `{ productIdentifier, policyIdentifier }`.
- Tenant `get`: `Data` is `{ identifier, name, tenantPolicies: [ { productIdentifier, licenseTypeIdentifier, policyIdentifier } ] }`.

### deployment {user|group|tenant} configure

Apply assignments non-interactively via `--input`. **FULL-REPLACE, not merge** — entries not in the input file are removed from the subject. To preserve existing assignments while adding new ones, seed the input from `deployment <subject> get`.

```bash
uip gov aops-policy deployment user configure "<USER_ID>" \
  --user "<USER_DISPLAY_NAME>" \
  --source "<IDP_SOURCE>" \
  --input "<SESSION_DIR>/user-policies.json" \
  --output json

uip gov aops-policy deployment group configure "<GROUP_ID>" \
  --group "<GROUP_DISPLAY_NAME>" \
  --source "<IDP_SOURCE>" \
  --input "<SESSION_DIR>/group-policies.json" \
  --output json

uip gov aops-policy deployment tenant configure "<TENANT_ID>" \
  --tenant-name "<TENANT_NAME>" \
  --input "<SESSION_DIR>/tenant-policies.json" \
  --output json
```

**Subject-specific configure flags:**

| Subject | Display-name flag | Extra flags | Notes |
|---------|-------------------|-------------|-------|
| user    | `--user <NAME>`   | `--source <SRC>` (default `local`; e.g. `cloud`, `aad`) | Display name stored alongside the override (surfaced in audit logs / UI). |
| group   | `--group <NAME>`  | `--source <SRC>` (default `local`)                      | Display name stored alongside the override. |
| tenant  | `--tenant-name <NAME>` | —                                                  | Must match the tenant's name in the governance service (from `tenant get`/`tenant list`). |

> **Do NOT use `--user-name` or `--group-name`** — those flags do not exist. The user variant takes `--user`; the group variant takes `--group`. Only the tenant variant uses `--tenant-name`.

> Do NOT launch `configure` without `--input` — that path is not supported.

### deployment {user|group} delete

Remove **all** policy assignments for a user or group. **Destructive.** Always confirm first.

```bash
uip gov aops-policy deployment user  delete "<USER_ID>"  --output json
uip gov aops-policy deployment group delete "<GROUP_ID>" --output json
```

- `user delete` — equivalent to `user configure` with an empty array; the user falls back to group/tenant inheritance for all products.
- `group delete` — removes the group and all of its policy overrides from governance state. The group itself remains in the upstream identity provider.

**Output:** `Data.Status` = `"Deleted"`, `Data.identifier` echoes the subject GUID.

### deployment tenant remove

Remove a tenant's assignment for a single product (optionally one license type). **Destructive.** Internally this is a client-side read-modify-write — the CLI runs `get` → filters out the matching entry → calls `configure` — so it is not atomic. Fails fast with `No matching policy assignment to remove` when nothing matches.

```bash
uip gov aops-policy deployment tenant remove "<TENANT_ID>" \
  --product-name "<PRODUCT_NAME>" \
  --output json
```

Add `--license-type <LICENSE_TYPE_NAME>` to remove only one license-type entry for the product. Omit it to remove every license-type entry for the product.

> **Concurrency warning.** Because this is a client-side `get → filter → save`, any concurrent change to the same tenant's assignments between the read and the save will be overwritten. Do not run `tenant remove` concurrently against the same tenant.

**Output:** `Data.removed` lists the entries that were dropped; `Data.tenantPolicies` is the post-removal assignment snapshot (useful for audit).

---

## uip gov aops-policy deployed-policy get

Return the single effective deployed policy for a `(licenseType, product, tenant)` tuple — the one policy that actually applies after the user → group → tenant inheritance chain has been walked and any 'No Policy' pins have been honored. Uses the caller's `uip login` token by default.

```bash
uip gov aops-policy deployed-policy get \
  "<LICENSE_TYPE>" "<PRODUCT_NAME>" "<TENANT_ID>" \
  --output json
```

**Positional arguments (all required):**

| Position | Argument | Description |
|----------|----------|-------------|
| 1 | `<LICENSE_TYPE>` | License type `name` (e.g. `Attended`, `Unattended`) — matches a `name` from `license-type list`. |
| 2 | `<PRODUCT_NAME>` | Product `name` — identifier, not label (e.g. `StudioX`, `Development`) — matches a `name` from `product list`. |
| 3 | `<TENANT_ID>` | Tenant GUID — from `deployment tenant list`. |

**Resolution modes (mutually exclusive):**

1. **Default (user-token)** — no flags. Resolves using the caller's own `uip login` identity.
2. **S2S + `--user-id <GUID>`** — resolves for a specific user (service-to-service call).
3. **S2S + `--tenant-only`** — resolves tenant-level policy only, skipping user/group overrides.

Modes 2 and 3 require an S2S token (read from the `UIP_S2S_TOKEN` environment variable, or passed via `--s2s-token`).

**Optional flags:**

| Flag | Description |
|------|-------------|
| `--s2s-token <TOKEN>` | S2S bearer token. Overrides the user token from `uip login`. Required for `--user-id` or `--tenant-only`. Prefer setting `UIP_S2S_TOKEN` in the environment — the CLI reads it automatically so the token never lands in shell history. See [Authentication](#authentication). |
| `--user-id <GUID>` | Look up the effective policy for a specific user (runs the full user→group→tenant walk). Requires `--s2s-token`. |
| `--tenant-only` | Bypass the user/group chain — return the tenant-level assignment only. Requires `--s2s-token`. |

**Output:** `Data` is the resolved policy — `policyIdentifier`, `name`, and `data` (the resolved policy's data payload). When no rule matches and no default exists, the service returns `204` and `Data` is `{ "Message": "No policy applies." }` — surface that message to the user. Use `deployed-policy list` to see every applicable policy, not just the one that won.

---

## uip gov aops-policy deployed-policy list

List every policy that applies to a `(licenseType, product, tenant)` for the calling user, in priority order. Unlike `get`, which returns only the single effective (top-priority) policy, `list` shows every applicable entry — useful for understanding why a particular policy wins. **User token only — does NOT accept `--s2s-token`.** Returns an empty array when nothing applies.

```bash
uip gov aops-policy deployed-policy list \
  "<LICENSE_TYPE>" "<PRODUCT_NAME>" "<TENANT_ID>" \
  --output json
```

**Output:** `Data` is an array of applicable policies in priority order. Each entry has `policyIdentifier`, `name`, `priority`, and `source` (one of `User`, `Group`, `Tenant` — the level that contributed this entry). To inspect applicable policies for another user, log in as that user, or call `deployed-policy get --s2s-token --user-id <id>` for their single effective policy.

---

## Authentication

All `uip gov aops-policy` commands require an authenticated session. Two modes are supported.

### User token (uip login)

Interactive OAuth — default for all commands.

```bash
uip login                                          # production (opens browser)
uip login --authority https://alpha.uipath.com     # non-production environments
uip login status --output json                     # verify logged-in state
```

The token is stored by the CLI and used automatically for every subsequent command. Covers all subcommands except the S2S-only `deployed-policy get --user-id` and `deployed-policy get --tenant-only` modes.

### S2S token

Required for the two server-to-server modes of `deployed-policy get`:
- `--user-id <GUID>` — look up another user's deployed policy.
- `--tenant-only` — explicitly bypass chain resolution.

**Acquisition (one-time):**

1. In the target tenant's Admin → **External Applications**, register a new confidential application with the `AOps.Write` (or equivalent governance) scope.
2. Exchange the application's client-credentials for a bearer token via the tenant's OAuth token endpoint (see your tenant admin docs).
3. Export the token in the caller's shell before running the command. Prefer the `UIP_S2S_TOKEN` environment variable — the CLI picks it up automatically, so it never appears on the command line or in shell history:
   ```bash
   export UIP_S2S_TOKEN="<TOKEN>"
   ```
4. Run S2S-mode calls without any token flag — the CLI reads `UIP_S2S_TOKEN` directly. Fall back to `--s2s-token "$UIP_S2S_TOKEN"` only if you need to override the env-var value for a single call.

**When NOT to use:**
- `deployed-policy list` rejects `--s2s-token` — use the user token (from `uip login`) instead.
- All other commands accept the user token; prefer `uip login` unless S2S is explicitly required.

---

## Global options

All `uip` commands support:

- `--output json|yaml|table` — programmatic vs display output. **Always pass `--output json` when the output is parsed.**
- `--help` — list the subcommand's flags. Run any command with `--help` to discover additional options beyond those listed here.

---

## Debug

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | User token expired or missing | Run `uip login` (or re-export `UIP_S2S_TOKEN` for S2S modes) and retry |
| `command not found: uip` | UiPath CLI not installed | `npm install -g @uipath/uipcli` |
| `unknown productIdentifier` | Used the product label instead of the `name` | Re-fetch via [product list](#uip-gov-aops-policy-product-list) and pass the `name` field |
| `unknown licenseTypeIdentifier` | Used the license type `name` or label instead of its `identifier` (GUID) in a tenant assignment | Re-fetch via [license-type list](#uip-gov-aops-policy-license-type-list) and copy the `identifier` field |
| `unknown policyIdentifier` (GUID) | Stale or wrong GUID | Re-run `list` and copy the `identifier` from the result |
| `missing licenseTypeIdentifier in tenant entries` | Tenant assignment entry omitted `licenseTypeIdentifier` | Add it to every tenant-subject entry (required key) |
| `deployed-policy list rejects --s2s-token` | `list` mode does not accept S2S tokens | Remove `--s2s-token`; re-run under `uip login` |
| `--user-id passed without --s2s-token` | S2S-only mode called with user token | Either drop `--user-id` (query caller's own policy) or set `UIP_S2S_TOKEN` in the environment (or pass `--s2s-token "$UIP_S2S_TOKEN"`) |
| `template get returned no template` | Product fetch failed (auth, transient network) | Retry; if persistent, verify `uip login status` and the product name |
| `template upgrade in progress` on `update` | Underlying Form.io template is migrating | Retry the `update` once the upgrade completes |
| `Policy created but not effective` | Policy has no deployment | Deploy via [aops-policy-deploy-guide.md](./aops-policy-deploy-guide.md) — a created policy only sits in the catalog until assigned |
| `Cannot delete policy — still assigned` | Policy referenced by tenant/user/group assignments | Run `deployment <subject> remove` (or `configure` with a filtered list) on every subject that references the policy, then retry `delete` |
| `unknown flag --user-name` / `--group-name` / `--policy-identifier` / `--user-identifier` / `--data-file` | Flag was renamed | Use the current flag: `--user` (user configure), `--group` (group configure), `--identifier` (policy update), `--user-id` (deployed-policy get), `--input` (create/update, deployment configure) |
