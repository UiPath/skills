# Access Policy Management Guide

Full CRUD lifecycle for UiPath access policies: list, get, create, update, delete.

## Prerequisites

- User must be logged in — see [access-policy-commands.md — Authentication](./access-policy-commands.md#authentication).
- For CLI flag details on every subcommand, see [access-policy-commands.md](./access-policy-commands.md).
- All policy JSON authoring flows through [planning-arch.md](./planning-arch.md) + [planning-impl.md](./planning-impl.md) + the plugin `impl.md` files. This guide never authors JSON directly.

---

## List policies

For all flags and output shape, see [access-policy-commands.md — list](./access-policy-commands.md#uip-gov-access-policy-list).

```bash
uip gov access-policy list --output json
```

Parse `Data.results[]` and display as a table:

```text
  #  Name                                     Status    Enforcement  ID
  1  Allow Production Agent in Maestro        Active    Allow        <POLICY_ID>
  2  Allow Agents except Development          Active    Allow        <POLICY_ID>
```

If `Data.results` is empty, inform the user that no policies were found. Offer `create` as the next step.

**Common filters:**

- `--filter "status in ('Active')"` — only active policies
- `--filter "contains(name, 'Production')"` — substring match on name
- `--order-by "CreatedOn desc"` + `--limit 5` — newest first
- `--limit 10 --offset 20` — page 3 at page size 10

---

## Get a policy

Always run before `update` or `delete`. For flags, see [access-policy-commands.md — get](./access-policy-commands.md#uip-gov-access-policy-get).

```bash
uip gov access-policy get <POLICY_ID> --output json
```

Parse `Data` and display:

```text
Name:         <NAME>
Description:  <DESCRIPTION or "(none)">
Type:         <policyType>
Enforcement:  <enforcement>
Status:       <status>
Selectors:    <N entries — resourceType(s): ...>
Executable:   <M entries — type(s): ...>
ID:           <POLICY_ID>
```

For full payload inspection, also show the raw JSON in a code block so the user can see every field.

---

## Create a policy

The policy definition is **always** authored via Phase 1 + Phase 2 + plugins. No free-form JSON authoring.

### Step 1 — Phase 1: author the Policy Spec

Hand off to [planning-arch.md](./planning-arch.md). It builds a **Policy Spec** (narrative paragraph + Spec Components Table covering name, description, status, enforcement, resource selection, actor process, actor identity, tags, operators) — every row pre-filled with the user's values or sensible defaults. The user reviews and edits any row, then approves with `yes`. Phase 1 ends when every Open question is closed and the user has approved.

### Step 2 — Phase 2: compose via plugins

Hand off to [planning-impl.md](./planning-impl.md). It walks each row of the approved Spec Components Table and reads the matching plugin's `impl.md`:

- Resource rows → [plugins/selector/impl.md](./plugins/selector/impl.md)
- Actor Process rows → [plugins/executable/impl.md](./plugins/executable/impl.md)
- Actor Identity rows (only when filled) → [plugins/actor/impl.md](./plugins/actor/impl.md)
- Tag-filter rows → [plugins/tags/impl.md](./plugins/tags/impl.md)

For **create** flows, Phase 2 reuses the slug Phase 1 used for `/tmp/access-policy-<slug>.spec.md` and writes the assembled `PolicyDefinition` to `/tmp/access-policy-<slug>.json` — both files sit side by side in `/tmp` and are surfaced in the review gate. (Update flows use a different file convention — see [Update a policy § Step 2](#step-2--build-the-working-file-from-data) below.)

### Step 3 — Verify metadata is captured in the Spec

Spec rows 1 (`name`), 2 (`description`), 3 (`status`), and 4 (`enforcement`) cover policy metadata. They were filled during Phase 1 — use them silently here (Critical Rule #11).

- **Name** (row 1): required.
- **Description** (row 2): required, one sentence summarizing the Spec narrative.
- **Status** (row 3): defaults to **`Simulated`** (Critical Rule #13 — see [SKILL.md § Enforcement and status](../SKILL.md#enforcement-and-status) for the meaning). Only emit `Active` when the Spec explicitly says so. After creation, if the policy is still Simulated, the post-create numbered next-steps list offers an explicit **Activate** step.
- **Enforcement** (row 4): always `Allow` (Critical Rule #2 — `Deny` is not authorable).

If any required row was unfilled when Phase 2 ran, return to Phase 1's iteration loop. Otherwise proceed to Step 4 without prompting.

### Step 4 — Single review gate

This is the **only** `yes / no` confirmation in the create flow (Critical Rule #7). Lead with a **short human-readable summary** — one plain-English line per block. Hide the technical per-entry breakdown inside a collapsible `<details>` section so the console stays clean:

```markdown
Review the access policy to be created:

  Scope:          Organization "<ORG_NAME>" / Tenant "<TENANT_NAME>"
                  (organizationId: <ORG_UUID>, tenantId: <TENANT_UUID>)
  Name:           <POLICY_NAME>
  Description:    <DESCRIPTION or "(none)">
  Status:         Simulated (preview mode — evaluated but does not affect enforcement)
  Resources:      <RESOURCE_SUMMARY>         e.g. "all Agent resources tagged 'Production'"
  Actor Process:  <ACTOR_PROCESS_SUMMARY>    e.g. "any Maestro"
  Actor Identity: <ACTOR_IDENTITY_SUMMARY>   e.g. "any identity"
  Policy Spec:    [access-policy-<slug>.spec.md](/tmp/access-policy-<slug>.spec.md)   ← human-readable Spec from Phase 1
  Policy data:    [access-policy-<slug>.json](/tmp/access-policy-<slug>.json)        ← JSON payload Phase 2 will submit

<details>
<summary>Show technical details</summary>

  Enforcement:    Allow
  Resource filters (which resource processes this policy protects):
    - <Resource type> — applies to <all|specific IDs|exclude IDs>; tag filter: <Any-of|All-of|Exclude|none>
  Actor Process rule (which processes are allowed to invoke the resources):
    - <Process type> — applies to <all|specific IDs|exclude IDs>
    Shared tag filter: <Any-of|All-of|Exclude|none>
  Actor Identity rule (omit entire block if no identity constraint; tags not supported on Actor Identity):
    - <Identity type> — applies to <all|specific IDs|exclude IDs>

</details>
```

**Scope line — what to fill in.** The Scope line tells the user which organization + tenant the policy will be created in. Use [access-policy-commands.md — Auth context for policy payloads](./access-policy-commands.md#auth-context-for-policy-payloads):

```bash
uip login status --output json
awk -F= '$1 ~ /^UIPATH_(ORGANIZATION|TENANT)_(ID|NAME)$/ {print $1 "=" substr($0, index($0, "=") + 1)}' "$HOME/.uipath/.auth"
```

- `Data.Organization` (preferred) or `UIPATH_ORGANIZATION_NAME` → `<ORG_NAME>`
- `Data.Tenant` (preferred) or `UIPATH_TENANT_NAME` → `<TENANT_NAME>`
- `UIPATH_ORGANIZATION_ID` → `<ORG_UUID>` (matches `organizationId` in the JSON payload)
- `UIPATH_TENANT_ID` → `<TENANT_UUID>` (matches `tenantId` in the JSON payload)

If the org / tenant names are unavailable, show only the UUIDs on the second line and note "(name unavailable)". Do **not** skip the Scope line — the user must always see which environment is about to be mutated. If the user expected a different org / tenant, they should `cancel` and re-login (`uip login --authority …` or tenant selection). Never print `UIPATH_ACCESS_TOKEN` or the full auth file while filling this line.

Then output the full JSON as a ```json code block in the chat (do NOT rely on the file link alone — the user may not be able to open it).

Both file links use the **resolved absolute path** (run `realpath` — Critical Rule #7). The Spec file (`<slug>.spec.md`) and the JSON file (`<slug>.json`) share the same slug so they sit side by side in `/tmp` for easy diff/review.

**User-friendly phrasing rules** (same terminology as [planning-arch.md](./planning-arch.md) — keep them aligned):

- "Resources" / "Resource filters" — not "Selectors".
- "Actor Process rule" — not "Executable rule".
- "Applies to: all / specific IDs / exclude IDs" — not "targeting" and not "operator: Or/None".
- "Tag filter: Any-of / All-of / Exclude" — not "operator: Or / And / None".
- If `Status: Simulated`, append the clarifier `(preview mode — evaluated but does not affect enforcement)` so the user knows the policy is not yet effective.

Ask verbatim:

```
Create access policy "<POLICY_NAME>"? (yes / no / keep editing)
```

`keep editing` is treated the same as `no` — route back:

| If the user wants to change... | Route to |
|---|---|
| Metadata (Spec rows 1 / 2 / 3 — name / description / status; row 4 enforcement is fixed at `Allow`) | Step 3 |
| A block's JSON (enum, targeting, operator, tags) | The relevant plugin's `impl.md`, splice the new block into the file |
| Intent itself (wrong resource, wrong caller, etc.) | [planning-arch.md](./planning-arch.md) — return to Spec iteration, get a fresh `yes`, re-run Phase 2 |

Re-enter this gate only after the change is applied. Do NOT run `create` until the user answers `yes`.

### Step 5 — Create

```bash
uip gov access-policy create --file /tmp/access-policy-<slug>.json --output json
```

Parse the response:

- `Data.upsertedPolicy.id` → record as `$POLICY_ID`
- `Data.statusCode` should be 200
- `Data.errors` should be `null`

If creation fails, show the error to the user and return to Step 4 (keep editing).

### Step 6 — Verify

```bash
uip gov access-policy get "$POLICY_ID" --output json
```

Display the raw JSON from `get` plus the user-friendly summary in the format defined by [SKILL.md — Completion Output](../SKILL.md#completion-output) (Operation & result line, Simulated banner, working file paths, technical details). If `Status == Simulated`, the Simulated banner is mandatory.

### Step 7 — Next steps

Render next steps as a **numbered Markdown list** under a `### What would you like to do next?` heading so the user can reply with the number. Do NOT use `AskUserQuestion`, do NOT render as a table. The option set depends on the policy's current `status`. See [SKILL.md — Completion Output](../SKILL.md#completion-output) for the exact lists for `status: "Simulated"` and `status: "Active"`. **Do NOT offer `evaluate`** (Critical Rule #12).

---

## Update a policy

The existing server-stored definition is **always** the starting state for an update, and every edit flows through the same plugins used at create time. Do **not** rebuild a Phase 1 Spec from scratch — that path is for create only.

### Step 1 — Identify and fetch

If the user did not provide a policy ID, run `list` (above) and ask them to pick one. Store as `$POLICY_ID`.

```bash
uip gov access-policy get "$POLICY_ID" --output json > /tmp/access-policy-"$POLICY_ID"-current.json
```

Display the current values (name, description, selectors summary, executable summary, status) so the user can see what they are changing.

### Step 2 — Build the working file from `Data`

Copy `.Data` as-is into the working file:

```bash
jq '.Data' /tmp/access-policy-"$POLICY_ID"-current.json > /tmp/access-policy-"$POLICY_ID"-working.json
```

Then strip the read-only audit fields:

```bash
jq 'del(.isBuiltIn, .isTemplate, .createdBy, .createdOn, .modifiedBy, .modifiedOn, .deletedBy, .deletedOn)' \
   /tmp/access-policy-"$POLICY_ID"-working.json > /tmp/access-policy-"$POLICY_ID"-working.tmp.json \
  && mv /tmp/access-policy-"$POLICY_ID"-working.tmp.json /tmp/access-policy-"$POLICY_ID"-working.json
```

The working file now has `id`, `organizationId`, `tenantId`, `policyType`, `name`, `description`, `selectors`, `executableRule`, `enforcement`, `status`. These are the fields the update sends — any field you remove is cleared from the server record (Critical Rule #8).

> **Never start from a Phase 1 Spec on update.** The existing policy is the source of truth. A from-scratch Spec silently wipes every field the user does not re-specify, because update is a full replacement.

### Step 3 — Classify what the user wants to change

Parse the user's request and classify each change:

| Change | Handling |
|--------|----------|
| Metadata only (`name` / `description` / `status`) | Edit in place in the working file. Skip plugins. |
| Add / remove / modify a selector (resource) | Re-enter [plugins/selector/impl.md](./plugins/selector/impl.md) with the existing block as starting input, then splice the modified entry back into `selectors[]`. |
| Modify the executable rule | Re-enter [plugins/executable/impl.md](./plugins/executable/impl.md) with the existing `executableRule` as input, apply the change, splice back. |
| Change a tag operator or tag values on any block | Re-enter [plugins/tags/impl.md](./plugins/tags/impl.md); preserve the parent block's other fields. |
| Add / remove / modify the actor identity rule ("only admins…", "block user X", "members of group G") | Re-enter [plugins/actor/impl.md](./plugins/actor/impl.md) with the existing `actorRule` (or absence) as input, apply the change, splice back. To remove identity enforcement, delete the `actorRule` key from the working file. |
| Flip Deny→Allow on an existing policy | Route through [plugins/tags/planning.md — Deny-to-Allow flip](./plugins/tags/planning.md#deny-to-allow-flip), apply `None` operator to the relevant tag block. |

**Skip rule:** if the user's original request already specified what to change (e.g. "set status to Simulated", "add UUID `abc-123` to the executable rule"), apply it directly without re-prompting. Only prompt when the user said `"update policy X"` with no details.

### Step 4 — Apply changes

Edit the working file in place. Update only the fields the user asked about; every other field stays as copied from `Data` in Step 2.

### Step 5 — Single review gate

Show a before/after diff so the user sees exactly what changed:

```text
Review access-policy update:

  Scope:        Organization "<ORG_NAME>" / Tenant "<TENANT_NAME>"
                (organizationId: <ORG_UUID>, tenantId: <TENANT_UUID>)
  Name:         <NEW_NAME>         (was: <OLD_NAME>)
  Description:  <NEW>              (was: <OLD>)
  Status:       <NEW>              (was: <OLD>)
  Selectors:    <change summary>
  Executable:   <change summary>

  Working file: [access-policy-<id>-working.json](/tmp/access-policy-<id>-working.json)
```

The Scope line uses the same safe auth-context workflow as the create gate (see [Step 4 — Single review gate](#step-4--single-review-gate) above for the full source mapping). For an update, display the stored `organizationId` / `tenantId` from the working file and the current login names from `uip login status --output json` when available. If the stored IDs do not match the active login context, stop before `update` and ask the user to switch tenants; otherwise the API will reject the mutation or target the wrong environment.

For each row, show `(unchanged)` if the field was not modified. Output the full updated JSON as a ```json code block in the chat as well.

Ask verbatim:

```
Apply update to access policy "<POLICY_NAME>"? (yes / no / keep editing)
```

`keep editing` routes back to Step 3 or Step 4 for the specific plugin whose block still needs edits. Do NOT run `update` until the user answers `yes`.

### Step 6 — Update

```bash
uip gov access-policy update --file /tmp/access-policy-"$POLICY_ID"-working.json --output json
```

### Step 7 — Verify

```bash
uip gov access-policy get "$POLICY_ID" --output json
```

Display:

```text
POLICY UPDATED

  ID:     <POLICY_ID>
  Name:   <NAME>
  Status: <STATUS>
```

Show the raw JSON so the user can confirm the change took effect.

---

## Delete a policy

> **Destructive.** This cannot be undone. Supports single-policy and multi-policy delete in one call.

### Step 1 — Identify the policy / policies

If the user did not provide policy IDs, run `list` and ask them to pick one or more. Store as `$POLICY_ID` (single) or `$POLICY_IDS` — a space-separated list (multi).

### Step 2 — Get and display each policy

Run `get` once per ID so the user sees what they are about to delete:

```bash
uip gov access-policy get "$POLICY_ID" --output json
```

Display per policy:

```text
About to delete:
  Name:         <NAME>
  ID:           <POLICY_ID>
  Resource:     <RESOURCE_TYPE>
  Executable:   <EXECUTABLE_TYPE>
  Status:       <Active | Simulated>
```

For multi-delete, render each policy as a numbered row and a count header (`About to delete <N> policies:`).

### Step 3 — Confirm

Ask verbatim — single or multi (Critical Rule #9, [SKILL.md — Confirmation-gate wording](../SKILL.md#confirmation-gate-wording)):

```
Delete access policy "<POLICY_NAME>"? This cannot be undone. (yes / no)
```

```
Delete <N> access policies (<POLICY_NAME_1>, <POLICY_NAME_2>, ...)? This cannot be undone. (yes / no)
```

If the user answers anything other than `yes` (or `y`), abort and inform them that deletion was cancelled.

### Step 4 — Delete

Single:

```bash
uip gov access-policy delete "$POLICY_ID" --output json
```

Multi (space-separated UUIDs in one call — see [access-policy-commands.md — delete](./access-policy-commands.md#uip-gov-access-policy-delete)):

```bash
uip gov access-policy delete $POLICY_IDS --output json
```

Parse `Data.policyIds[]` to confirm every requested UUID was deleted. Report any IDs that did not appear in the response.

### Step 5 — Confirm and offer next steps

Print the result line:

```text
Access policy "<POLICY_NAME>" deleted successfully.
```

For multi-delete:

```text
Deleted <N> access policies: <NAME_1>, <NAME_2>, ...
```

Then render the post-delete numbered next-steps menu mandated by [SKILL.md — Completion Output](../SKILL.md#completion-output) (`### What would you like to do next?` → `1. List policies to verify` / `2. Something else`). Do NOT use `AskUserQuestion`.

---

## Debug

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Token expired or missing | `uip login` and retry — see [access-policy-commands.md — Authentication](./access-policy-commands.md#authentication) |
| `Policy not found` | Stale or wrong UUID | Re-run `list` and copy the `id` from the result |
| `400 Bad Request` / `Selectors[0].Values is required` | Missing `values: ["*"]` | Compose the selector via [plugins/selector/impl.md](./plugins/selector/impl.md) — `values` is required even with tags |
| `409 Conflict` / duplicate name | Another policy has the same name | Pick a different name |
| `enforcement: Deny not allowed` | The skill emitted `enforcement: "Deny"` — never authorable (Critical Rule #2) | Switch to `enforcement: "Allow"` and reframe the Deny intent: ask what should be allowed, or use `operator: "None"` on tags / values. See [plugins/tags/planning.md — Deny-to-Allow flip](./plugins/tags/planning.md#deny-to-allow-flip). |
| `ActorRule.Values is required` | Emitted `actorRule` without any entries | Either remove the `actorRule` key entirely (no identity constraint), or add at least one `{ type, values, operator }` entry — see [plugins/actor/impl.md](./plugins/actor/impl.md) |
| Identity filter ignored at runtime | Omitted `actorRule` when the intent required one | Compose the Actor Identity Rule via [plugins/actor/planning.md](./plugins/actor/planning.md) + [plugins/actor/impl.md](./plugins/actor/impl.md) |
| Update silently wiped a field | Started from a fresh Phase 1 Spec instead of `Data` | Re-fetch via `get`, restart update from `Data` (Step 2) |

---

## Related references

- [access-policy-commands.md](./access-policy-commands.md) — every flag and output shape used above.
- [planning-arch.md](./planning-arch.md) — Phase 1 Policy Spec authoring, required for create and for intent-scoped updates.
- [planning-impl.md](./planning-impl.md) — Phase 2 JSON composition.
- [plugins/](./plugins/) — block-level authoring guides for selector, executable, actor, tags.
