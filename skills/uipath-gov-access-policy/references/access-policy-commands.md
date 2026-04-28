# uip gov access-policy — CLI Command Reference

Single source of truth for every `uip gov access-policy` subcommand, its flags, and its output shape. All commands return `{ "Result": "Success"|"Failure", "Code": "...", "Data": { ... } }`. Use `--output json` for programmatic use — every command in this skill must pass it.

> For task workflows (list / get / create / update / delete), see [policy-manage-guide.md](./policy-manage-guide.md). This file only documents the command surface.

The CLI wraps two endpoints:
- **PAP (Policy Administration Point)** — `list` / `get` / `create` / `update` / `delete` operate on policy records.
- **PDP (Policy Decision Point)** — `evaluate` asks the service to resolve the effective decision (`Allow` / `Deny` / `NoOp`) for a concrete request context. `evaluate` requires tenant-scoped login.

---

## Common flags (shared across `uip` list commands)

These flags work the same way on `uip gov access-policy list` and on every `uip or ... list` lookup command (used by [resource-lookup-guide.md](./resource-lookup-guide.md)). Per-subcommand sections only document what is **specific** to that subcommand and link back here for the shared flags.

| Flag | Purpose |
|------|---------|
| `--output json` | **Always pass this in scripted flows.** Emits structured JSON for parsing. |
| `--limit <N>` | Page size — max records to return (default varies per command). |
| `--offset <N>` | Records to skip before the returned page, 0-based (default `0`). |
| `--order-by <ORDER>` | OData sort expression — `<Field> <asc|desc>` (e.g. `Name asc`, `CreatedOn desc`). |
| `--login-validity <MINUTES>` | Override interactive-login token lifetime for this call. Rarely needed. |

---

## Authentication

Every subcommand requires an active login. Check first:

```bash
uip login status --output json
```

If not logged in:

```bash
uip login                                          # interactive OAuth
uip login --authority https://alpha.uipath.com     # non-production environments
```

For `evaluate`, login must target a specific tenant (not just an organization).

### Reading `organizationId` and `tenantId`

The org and tenant UUIDs required in every `PolicyDefinition` live in `~/.uipath/.auth`:

```bash
grep -E "UIPATH_ORGANIZATION_ID|UIPATH_TENANT_ID" ~/.uipath/.auth
```

Expected output:

```
UIPATH_ORGANIZATION_ID=<ORG_UUID>
UIPATH_TENANT_ID=<TENANT_UUID>
```

Copy these into `organizationId` and `tenantId` when composing a policy (see [planning-impl.md — Step 1](./planning-impl.md#step-1--gather-identity)). Never hardcode.

---

## uip gov access-policy list

Search for access policies with optional filters and pagination.

```bash
uip gov access-policy list --output json
```

**Subcommand-specific flags** (shared `--limit` / `--offset` / `--order-by` / `--login-validity` documented in [Common flags](#common-flags-shared-across-uip-list-commands) above):

| Flag | Required | Description |
|------|----------|-------------|
| `--filter <EXPRESSION>` | no | OData-style filter (e.g. `status in ('Active')`, `contains(name, 'Production')`) |

**Output:** `Data.totalCount` and `Data.results[]`. Each entry includes `id`, `name`, `status`, plus the full `PolicyDefinition` fields (`selectors`, `executableRule`, `enforcement`, `organizationId`, `tenantId`) and audit metadata. Use the `id` with `get` / `update` / `delete` / `evaluate`.

**Example:**

```bash
uip gov access-policy list --filter "status in ('Active')" --order-by "Name asc" --output json
```

---

## uip gov access-policy get

Fetch the full `PolicyDefinition` for a single policy by UUID. Always run before `update` or `delete`.

```bash
uip gov access-policy get <POLICY_ID> --output json
```

**Arguments:** `<POLICY_ID>` (UUID) — required. Obtain from `list` (the `id` field of each result).

**Output:** `Data` is the full `PolicyDefinition`. Use it verbatim as the starting state for an update (see [policy-manage-guide.md — Update Step 2](./policy-manage-guide.md#step-2--build-the-working-file-from-data)).

---

## uip gov access-policy create

Create a new access policy from a JSON file conforming to `PolicyDefinition`.

```bash
uip gov access-policy create --file <PATH> --output json
```

**Flags:**

| Flag | Required | Description |
|------|----------|-------------|
| `--file <PATH>` | yes | Path to a JSON file containing the full `PolicyDefinition` |
| `--login-validity <MINUTES>` | no | Override interactive-login token lifetime |

**File contents:** a raw `PolicyDefinition` object sent **as-is** (no `{ "data": {...} }` envelope wrapping). Do **not** include a server-assigned `id`. Minimum required fields: `policyType`, `organizationId`, `tenantId`, `name`, `selectors`, `executableRule`, `enforcement`, `status`. See [planning-impl.md](./planning-impl.md) for how to compose this object from plugin building blocks.

**Output:** `Data.statusCode`, `Data.errors` (usually `null` on success), and `Data.upsertedPolicy` with the stored document. Capture `Data.upsertedPolicy.id` as the new policy UUID for follow-up `evaluate`, `update`, or `delete`.

---

## uip gov access-policy update

Update an existing access policy from a JSON file. Sent as HTTP PATCH — the server applies the supplied `PolicyDefinition` fields to the existing record. **Treat it as a full replacement**: every field you omit from the file is cleared on the server (Critical Rule #8 in [SKILL.md](../SKILL.md#critical-rules)).

```bash
uip gov access-policy update --file <PATH> --output json
```

**Flags:**

| Flag | Required | Description |
|------|----------|-------------|
| `--file <PATH>` | yes | Path to a JSON file containing the updated `PolicyDefinition`. Must include the policy's `id` to identify the target record. |
| `--login-validity <MINUTES>` | no | Override interactive-login token lifetime |

**File contents:** the full `PolicyDefinition` — seed it by running `access-policy get <id>`, editing the returned JSON, and passing it back. The file **must** include `id`, `organizationId`, `tenantId`, and every rule block you want to keep. Strip audit fields (`isBuiltIn`, `isTemplate`, `createdBy`, `createdOn`, `modifiedBy`, `modifiedOn`, `deletedBy`, `deletedOn`).

**Output:** `Data.statusCode`, `Data.errors`, and `Data.upsertedPolicy` with the stored document.

> See [policy-manage-guide.md — Update](./policy-manage-guide.md#update-a-policy) for the full `get → edit → review → update` flow.

---

## uip gov access-policy delete

Delete one or more access policies by UUID. **Permanent — cannot be undone.**

```bash
uip gov access-policy delete <POLICY_ID> --output json
uip gov access-policy delete <POLICY_ID_1> <POLICY_ID_2> --output json    # multiple IDs in a single request
```

**Arguments:** one or more `<POLICY_ID>` (UUID), space-separated — required.

**Output:** `Data.policyIds[]` listing the deleted UUIDs.

Always `get` the policy first and show a summary to the user. Require an explicit `yes` before running delete — see [SKILL.md — Confirmation-gate wording](../SKILL.md#confirmation-gate-wording).

---

## uip gov access-policy evaluate

Ask the Policy Decision Point (PDP) to resolve the effective decision (`Allow` / `Deny` / `NoOp`) for a request context. Returns the aggregated enforcement, which policies contributed, and evaluation details.

> **Requires tenant-scoped login** — login must target a specific tenant, not just an organization (Critical Rule #12).
>
> **User-initiated only.** Do not run `evaluate` automatically after create (Critical Rule #12). Dummy UUIDs with no Resource Catalog tags correctly return `NoOp` and confuse the user into thinking the policy is broken.

```bash
uip gov access-policy evaluate \
  --resource-type <RESOURCE_TYPE> \
  --resource-id <RESOURCE_UUID> \
  --actor-process-type <ACTOR_PROCESS_TYPE> \
  --actor-process-id <ACTOR_PROCESS_UUID> \
  --output json
```

> **Flag naming.** The CLI flags mirror the skill's user-facing rule names — `--resource-*` (Selection Rule) and `--actor-process-*` (Actor Process Rule, `executableRule` in JSON). The JSON field names (`actorRule`, `executableRule`) stay unchanged on the wire.
>
> **Actor identity is inferred, not passed.** Under a user token (`uip login`), the calling user is taken from the bearer — omit `--actor-identity-id`. Under an S2S token, pass `--actor-identity-id <ID>` to evaluate on behalf of a specific actor; the CLI documents the flag as required only in this mode. There is no companion `--actor-identity-type` — the type is always derived server-side from the actor record. To preview enforcement for a different user under user-token mode, log in as that user first.
>
> **Robot / ExternalApplication actors don't match `actorRule` (Critical Rule #16).** Access policies of type `ToolUsePolicy` accept only `User` and `Group` in `actorRule.values[].type`. When the inferred or S2S-supplied actor resolves server-side to a `Robot` or `ExternalApplication`, the request will only match policies that have no `actorRule` block at all — every policy with an `actorRule` returns `NoOp` for that actor regardless of UUID. If the user expected a match for a Robot, see [plugins/actor/impl.md — Robot intent](./plugins/actor/impl.md) for the User-fallback pattern.

**Flags:**

| Flag | Required | Description |
|------|----------|-------------|
| `--resource-type <TYPE>` | conditional | The protected asset being accessed. One of `Agent`, `AgenticProcess`, `RPAWorkflow`, `APIWorkflow`, `CaseManagement`, `Flow`. |
| `--resource-id <ID>` | conditional | Identifier of the specific resource instance (e.g. an Agent UUID). **No `*` — real UUIDs only.** |
| `--actor-process-type <TYPE>` | conditional | The workflow/agent being executed on behalf of the actor, if any. One of `Agent`, `AgenticProcess`, `CaseManagement`, `Flow`. |
| `--actor-process-id <ID>` | conditional | Identifier of the actor process (e.g. a Flow UUID). **No `*`.** |
| `--actor-identity-id <ID>` | S2S only | Identifier of the actor to evaluate on behalf of. The CLI documents this flag as required only when calling with an S2S token. Under a user token, omit it — the actor is inferred from the bearer (see the **Actor identity is inferred** callout above). |
| `--folder-key <KEY>` | no | Folder key (UUID) scoping the request to a specific folder. |
| `--trace-parent-id <ID>` | no | W3C traceparent header value to correlate this evaluation with upstream traces. |
| `--login-validity <MINUTES>` | no | Override interactive-login token lifetime |

**Output:** `Data.enforcement` plus `Data.evaluationDetails` and `Data.effectivePolicies[]` (the policies that contributed to the decision).

**Interpreting the result:**

| Enforcement | Meaning |
|-------------|---------|
| `Allow` | A matching policy allows the request. The policy is working. |
| `NoOp` | No policies matched the request; allowed by default. With real UUIDs this means the policy does not cover that context. With unknown/untagged UUIDs it is expected — the policy can still be correct. |
| `Deny` | A policy is blocking. Inspect `Data.effectivePolicies` to find which one. |

**Example:**

```bash
uip gov access-policy evaluate \
  --resource-type Agent \
  --output json
```

The calling user (from `uip login`) is the actor; their identity is taken from the bearer.

---

## Shared error table

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Token expired or missing | Run `uip login`, then retry |
| `403 Forbidden` | User is not in the org | Check login org context; re-login with the correct tenant |
| `400 Bad Request` / `Selectors[0].Values is required` | Missing `values: ["*"]` on a selector or executable-rule entry | Add `"values": ["*"]` — required even when `tags` narrow the scope |
| `400 Bad Request` / unknown `resourceType` or `type` | Enum typo | Use a valid enum value — see [plugins/selector/impl.md](./plugins/selector/impl.md) / [plugins/executable/impl.md](./plugins/executable/impl.md) |
| `409 Conflict` | Policy name already exists | Choose a different name |
| `Policy not found` | Stale ID | Re-run `list` and copy the current `id` |
| `enforcement: "Deny" not allowed` | The skill emitted `enforcement: "Deny"` — never authorable (Critical Rule #2) | Switch to `enforcement: "Allow"` and reframe Deny intent: ask what should be **allowed** and target that set, or use the `None` operator on tags / values. See [plugins/tags/planning.md — Deny-to-Allow flip](./plugins/tags/planning.md#deny-to-allow-flip). |
| `ActorRule.Values is required` | Emitted `actorRule` with no entries | Either omit the `actorRule` key, or add entries — see [plugins/actor/impl.md](./plugins/actor/impl.md) |
| `400 Bad Request` on `actorRule.values[].type: Group` | Server build does not accept `Group` | Enumerate member user UUIDs under `type: User` — see [plugins/actor/impl.md — Debug](./plugins/actor/impl.md#debug) |
| `evaluate` rejects with tenant-context error | Login is org-scoped, not tenant-scoped | Re-login targeting the specific tenant (Critical Rule #12) |
| `unknown flag --resource-identifier` / `--actor-type` / `--actor-identifier` / `--executable-type` / `--executable-identifier` / `--actor-identity-type` | Flags were renamed and `--actor-identity-type` was removed | Use the current set: `--resource-id`, `--actor-process-type`, `--actor-process-id`. For actor identity: omit under a user token (inferred from the bearer); pass `--actor-identity-id <ID>` only under an S2S token. |
