# Policy Management Guide

Full CRUD lifecycle for AOps governance policies: list, get, create, update, and delete.

## Prerequisites

- User must be logged in — see [aops-policy-commands.md — Authentication](./aops-policy-commands.md#authentication).
- Session directory convention: `./aops-sessions/<YYYYMMDD-HHMMSS>-<short-uuid>/` (see [SKILL.md — Session directory](../SKILL.md#session-directory)).
- For CLI flag details on every subcommand mentioned below, see [aops-policy-commands.md](./aops-policy-commands.md).

**Related guides:** [configure-aops-policy-data-guide.md](./configure-aops-policy-data-guide.md) (policy data authoring) · [aops-policy-deploy-guide.md](./aops-policy-deploy-guide.md) (assignment to subjects).

---

## List policies

For all flags and output shape, see [aops-policy-commands.md — list](./aops-policy-commands.md#uip-gov-aops-policy-list).

Parse `Data` (an array of `PolicyDto`, each with `identifier`, `name`, `productName`, `priority`, `availability`) and display as a table:

```text
  #  Name                    Product        Priority  ID
  1  My Studio Policy        Development    1         <POLICY_ID>
  2  AI Trust Default        AITrustLayer   5         <POLICY_ID>
```

If `Data` is empty, inform the user that no policies were found. Run `uip gov aops-policy product list` to resolve each `productName` identifier to its human-readable `label` for the table.

---

## Get a policy

Always run before `update` or `delete`. For flags, see [aops-policy-commands.md — get](./aops-policy-commands.md#uip-gov-aops-policy-get).

Parse `Data` (`identifier`, `name`, `productName`, `priority`, `availability`, `data`) and display:

```text
Name:         <NAME>
Product:      <PRODUCT_LABEL> (name: <PRODUCT_NAME>)
Priority:     <PRIORITY>
Description:  <DESCRIPTION or "(none)">
ID:           <POLICY_ID>
```

---

## Create a policy

Follow these steps in order.

### Step 1 — Bootstrap and verify product

Before selecting a product, run the bootstrap described in [configure-aops-policy-data-guide.md — Step 1](./configure-aops-policy-data-guide.md#step-1--bootstrap-load-all-products-and-their-templates-create-flow-only). This creates `$SESSION_DIR` and populates `$SESSION_DIR/products/<PRODUCT_NAME>/{form-template.json,form-data.json,form-template-locale-resource.json}` for every product. Each `form-template.json`'s top-level `.product` object `{name, label, ...}` is the catalog entry — no separate `products.json` exists.

After bootstrap completes, choose the product using the matrix below:

| Situation | Action | Store as |
|-----------|--------|----------|
| User named the product explicitly (e.g. *"create a Studio policy"*) | Case A — resolve + verify | `$PRODUCT_NAME` (name, not label) |
| User described a rule but did not name a product | Case B — rank by intent keywords | `$PRODUCT_NAME` after confirmation |

#### Case A — user named the product

1. Match the user's phrase case-insensitively against `.product.label` or `.product.name` across `$SESSION_DIR/products/*/form-template.json` (use the `Glob` tool, then `Read` each `.product`). Call the matched entry the **chosen product**.
2. Extract **intent keywords** from the user's prompt (e.g. "Gemini", "feedback", "region", "default action").
3. Use the **`Grep` tool** (Claude's built-in — NOT `Bash(grep …)`, which prompts for permission every call) to search `$SESSION_DIR/products/<CHOSEN>/form-template-locale-resource.json` for fields whose `label` or `description` matches any intent keyword. Set `glob` to the specific file path, `-i: true`, `output_mode: "content"`.
4. Use the **`Grep` tool** again across `$SESSION_DIR/products/*/form-template-locale-resource.json` to find the same keywords in every other product's locale resource.
5. Decide:
   - Chosen product matches the intent (or the user gave no specific intent) → proceed silently. Store the chosen product's `name` as `$PRODUCT_NAME`.
   - Another product matches and the chosen product does not → ask:
     ```text
     You asked for <CHOSEN_LABEL>, but the settings you described
     (<MATCHED_KEYWORDS>) live under <BETTER_LABEL>.
     Use <BETTER_LABEL> instead? (yes / no / pick another product)
     ```
     Store the user's confirmed product's `name` as `$PRODUCT_NAME`.

#### Case B — user did not name a product

1. If the user's prompt contains intent keywords, use the **`Grep` tool** across `$SESSION_DIR/products/*/form-template-locale-resource.json` with `-i: true` and `output_mode: "count"` to rank every product by how many keywords match. Show the top 3 with a short reason:
   ```text
   Best matches for your request:
      1. AI Trust Layer        (name: AITrustLayer)    — matched: "Gemini", "Claude"
      2. Studio                (name: Development)     — matched: "feedback"
      3. StudioX               (name: Business)        — no direct match
   Which product would you like to create a policy for? (1-3, or ask to see all)
   ```
2. If there are no intent keywords, enumerate products via `Glob` on `$SESSION_DIR/products/*/form-template.json` and `Read` `.product.{name,label}` from each. Display only `label` and `name`:
   ```text
   Available products:
      1. AI Trust Layer        (name: AITrustLayer)
      2. Studio                (name: Development)
      3. StudioX               (name: Business)
      ...
   Which product would you like to create a policy for?
   ```

Store the confirmed product's `name` as `$PRODUCT_NAME`.

### Step 2 — Configure policy data

Follow [configure-aops-policy-data-guide.md](./configure-aops-policy-data-guide.md) starting at **Step 2**. The bootstrap from Step 1 has already written `$SESSION_DIR/products/$PRODUCT_NAME/{form-template.json,form-data.json,form-template-locale-resource.json}` — the agent only needs to read these files, not re-fetch them.

On completion: `$SESSION_DIR/aops-policy-data.json` is set and ready, and the configure-guide has also produced a change-summary block for use in Step 4.

### Step 3 — Collect policy metadata (prompt only for missing fields)

**Skip rule:** if the user's original prompt already supplied a value for a metadata field (name, description, priority, availability), use it silently — only prompt for fields the user did not mention. Either way, always run the priority-landscape fetch below (needed for the Step 4 review's current-#1 citation) before moving to Step 4.

**Always fetch the priority landscape, even when the user supplied a priority.** The review gate in Step 4 must cite the current #1 holder (the group-level tie-breaker winner today) next to the proposed priority — the user can only consent to the impact if they see whose position the new policy is landing behind or ahead of. Store the result as `$PRIORITY_LANDSCAPE` for reuse in Step 4.

When suggesting a priority (only when the user did not supply one), link [SKILL.md — Priority rules](../SKILL.md#priority-rules) when prompting so the user knows what Priority actually does — in particular, that it is **NOT** what picks between user / group / tenant assignments (that's the resolution chain), and only acts as a tie-breaker at the **group level** when a user belongs to multiple groups with competing policies for the same product.

Fetch the current priority landscape:

```bash
uip gov aops-policy list \
  --product-name "$PRODUCT_NAME" \
  --order-by priority \
  --order-direction asc \
  --output json
```

Parse `Data` (array of policy entries, each with `identifier`, `name`, `productName`, `priority`) and display with explicit rank labels. Frame the "wins" language as a group-level concept so the user doesn't mistake Priority for the scope-resolution chain:

```text
Existing policies for <PRODUCT_LABEL>, ordered by priority (ascending):
  priority 1   Strict AI Trust        <POLICY_ID>   ← group-level tie-breaker winner today
  priority 2   Internal Default       <POLICY_ID>
  priority 5   Legacy Overrides       <POLICY_ID>

Priority only matters when a user is assigned multiple of these policies via
different groups. Picking user- or tenant-level assignments is unaffected.
```

If no policies exist yet for this product, say so and note that Priority is unused until at least two policies exist AND a user is assigned both via different groups.

Then suggest defaults and let the user accept (press Enter) or override. Present all three in a single block with a one-line rationale for the priority suggestion:

```text
Proposed policy metadata — press Enter to accept, or reply with overrides:

  Name:         <SUGGESTED_NAME, e.g. "AI Trust Layer — Restrictive">
  Description:  <SUGGESTED_DESCRIPTION>
  Priority:     <MAX_EXISTING + 1>    ← placed last, so creating this policy does not
                                        silently reorder the group-level tie-breaker
                                        for users already assigned existing policies.
                                        Reply with a lower number to outrank specific
                                        policies at the group level.
```

Suggestion rules:
- **Name:** derive from the product label plus the user's intent (e.g. `"Studio — Dev Team Default"`). If intent is unclear, use `"<PRODUCT_LABEL> Policy"`.
- **Description:** one sentence summarizing the notable non-default settings; if there are none, use `"Default <PRODUCT_LABEL> policy."`.
- **Priority:** default to `(max existing priority for this product) + 1` — i.e. place the new policy last. This is the safe default because creating a new policy can never change the effective group-level winner for any existing user. If no existing policies for this product, default to `1`. Only suggest a lower number when the user explicitly says they want the new policy to beat a named existing one at the group level — in that case propose `(target policy's priority) - 1` or lower and call out which specific existing policy the new one will outrank.

Required: `$POLICY_NAME` must be non-empty. If the user clears it, re-prompt.
Optional: omit `--description`, `--priority`, and `--availability` from the create command if the user did not provide them. Do NOT prompt for `--availability` proactively — it is the offline grace period (in days) during which the client (Studio, Assistant, etc.) keeps applying the cached copy of the policy when it cannot reach Automation Ops. Most users leave it at the server default. Only pass `--availability` when the user explicitly supplied a value; it must be an integer > 0 (sending `0` causes the server to normalize to `30`). See [aops-policy-commands.md — create](./aops-policy-commands.md#uip-gov-aops-policy-create) for the full flag description.

### Step 4 — Final review before create (single confirmation gate)

**Expect from configure-guide:** `$SESSION_DIR/aops-policy-data.json` (the saved blueprint, produced by configure-guide Step 8) and a change-summary block (produced by configure-guide Step 9). Configure-guide does NOT prompt — all confirmation consolidates here.

This is the **only** yes/no confirmation in the create flow (Critical Rule #12). Present the complete policy plus a clickable link to the saved policy data file so the user can open it, scan every field, and decide.

> **MANDATORY (Critical Rule #16):** the `Policy data` row is required in every review — not optional, not conditional on whether the user asked for it. It is the user's only chance to review the full composed JSON before the mutation runs, and it is often requested after creation as well. A review without this row is incomplete; do NOT proceed to `create` until it is added and the user has confirmed.

```text
Review policy to be created:

  Name:         <POLICY_NAME>
  Product:      <PRODUCT_LABEL> (name: <PRODUCT_NAME>)
  Description:  <DESCRIPTION or "(none)">
  Priority:     <PRIORITY or "(suggested: MAX_EXISTING+1)">
                Current #1 holder (group-level tie-breaker winner today):
                  "<NAME_AT_PRI_1>" (priority 1, <POLICY_ID_AT_PRI_1>)
                Rank impact: <"placed last — does not reorder existing group-level winners"
                              | "outranks <LIST_OF_POLICIES_WITH_HIGHER_PRIORITY_NUMBERS> at the group level"
                              | "no existing policies — Priority is unused until ≥2 exist and a user is in multiple groups">

  Policy data:  [aops-policy-data.json](<ABSOLUTE_PATH_TO_SESSION_DIR>/aops-policy-data.json)

  Changed settings (vs defaults):
    feedback-enabled             false   (was: true)
    default-action               Warning (was: Error)
  Unchanged fields: 14 kept at defaults.

Open the linked file to see every field.
Create policy "<POLICY_NAME>" for <PRODUCT_LABEL>? (yes / no / keep editing)
```

Populate `<NAME_AT_PRI_1>` and `<POLICY_ID_AT_PRI_1>` from `$PRIORITY_LANDSCAPE` (the `list` result from Step 3). If no existing policies exist for this product, replace the "Current #1 holder" line with `Current #1 holder: (none — this will be the first policy for <PRODUCT_LABEL>)`. If the current #1 holder IS the policy being updated (update flow), say `Current #1 holder: this policy (unchanged)`.

Render the `Policy data` line using markdown link syntax with the **resolved absolute path** to `aops-policy-data.json` (e.g. `[aops-policy-data.json](/Users/alice/work/aops-sessions/20260421-150621-d0d3e5e9/aops-policy-data.json)`). Run `realpath "$SESSION_DIR/aops-policy-data.json"` (or equivalent) to get the absolute path — do NOT emit a relative path, a literal `<SESSION_DIR>` placeholder, or a `~/` path. In IDE environments the link is clickable and opens the file directly.

Do NOT include an `Availability:` row in the review — it is a product-specific enum, almost always left unset, and when unset it adds noise. Only include availability in the review when the user explicitly supplied a value (in which case show it inline, not as its own row, e.g. `Priority: 4, Availability: 30`). `keep editing` is treated the same as `no`: route back to the relevant step (metadata → Step 3, form-data → configure-guide Step 5) and re-enter this gate only after the change is applied. Do NOT run `create` until the user confirms `yes`.

### Step 5 — Create the policy

For flags, see [aops-policy-commands.md — create](./aops-policy-commands.md#uip-gov-aops-policy-create).

```bash
uip gov aops-policy create \
  --name "$POLICY_NAME" \
  --product-name "$PRODUCT_NAME" \
  --input "$SESSION_DIR/aops-policy-data.json" \
  --output json
```

Include `--description`, `--priority`, and/or `--availability` only when the user provided them. Parse the response:

- `Data.identifier` → `$POLICY_ID`
- `Data.productName` → `$PRODUCT_IDENTIFIER` (flat string, not nested)

### Step 6 — Report success and explain the deployment step

```text
Policy created successfully.
  Name:       <POLICY_NAME>
  ID:         <POLICY_ID>
  Product:    <PRODUCT_LABEL>
  Priority:   <PRIORITY or "(none)">
  Composed:   [aops-policy-data.json](./aops-sessions/<SESSION_ID>/aops-policy-data.json)

⚠ This policy is NOT yet effective. Creating a policy only registers it in the
  catalog — nothing will apply it to anyone until you deploy it.

Deployment targets (in order of chain resolution, highest precedence first):
  1. User    — applies to one named user; overrides group and tenant.
  2. Group   — applies to every member of a group; overrides tenant.
  3. Tenant  — applies to every user in the tenant for a given (product, license type);
               the baseline when no user- or group-level assignment wins.

How AOps resolves the effective policy for a given user:
  • It walks User → Group → Tenant and picks the FIRST level that has an
    assignment for that product. Priority is NOT consulted here — scope is.
  • Priority only matters AT the group level: if the user is in multiple
    groups that each have a policy for the same product, the group policy
    with the lowest priority number wins.
  • At the user level and the tenant level there is at most one assignment
    per product (per license type for tenant), so Priority never applies.

Would you like to deploy this policy now?
  - Yes, to a user
  - Yes, to a group
  - Yes, to a tenant (requires license type)
  - Not now (policy stays in the catalog but has no effect)
```

Render the `Composed` line with the actual resolved session path (same substitution rule as Step 4).

If the user picks a deployment target, continue to [aops-policy-deploy-guide.md](./aops-policy-deploy-guide.md) — reuse `$SESSION_DIR`. If they decline, stop and remind them the policy is inactive until deployed.

---

## Update a policy

### Step 1 — Identify the policy and create the session directory

1. If the user did not provide a policy identifier, run `list` (above) and ask them to pick one. Store as `$POLICY_IDENTIFIER`.
2. Create the session directory that will hold all scratch files for this update. The update flow skips the bootstrap, so the caller — not configure-guide Step 1 — owns the session directory:
   ```bash
   SESSION_DIR="./aops-sessions/$(date +%Y%m%d-%H%M%S)-$(uuidgen | cut -c1-8 | tr '[:upper:]' '[:lower:]')"
   mkdir -p "$SESSION_DIR"
   ```
3. Proceed to Step 2.

### Step 2 — Get current values and extract the existing data blueprint

```bash
uip gov aops-policy get "$POLICY_IDENTIFIER" --output json > "$SESSION_DIR/current-policy.json"
```

Display the current values (name, product, priority, description, availability) so the user can see what they are changing.

**Extract the existing policy's data as the update blueprint** — this is the object the user will edit, and any fields not touched must retain their existing values (NOT revert to product defaults):

```bash
jq '.Data.data' "$SESSION_DIR/current-policy.json" > "$SESSION_DIR/existing-policy-data.json"
```

> **Critical:** on update, the blueprint is the existing policy's `data` object — NOT the product's default `form-data.json`. Using the product defaults would silently wipe every non-default setting the user previously configured. Only use form-data defaults as a fallback for brand-new fields added to the product template after the policy was originally created.

### Step 3 — Determine what to change (prompt only for missing information)

**Skip rule:** if the user's original request already specified what to change (e.g. *"update policy X to set priority 3"* or *"add Gemini to the disabled models in policy X"*), apply that intent directly — do not re-ask. Only prompt when the user said `"update policy X"` with no details.

The fields the user may change are: name, description, priority, availability, or policy data (field values). The product cannot be changed on update.

### Step 4 — If updating policy data

Follow [configure-aops-policy-data-guide.md](./configure-aops-policy-data-guide.md) with these update-flow overrides:

- **Skip Step 1 (bootstrap) entirely** — the product is already known, so there is no need to fetch every product's schema. Jump straight to Step 2 and fetch only this product's template into `$SESSION_DIR/products/$PRODUCT_NAME/`.
- **Override the blueprint** for Step 2 and Step 7: use `$SESSION_DIR/existing-policy-data.json` (from Step 2 above) as the working `$POLICY_DATA` — NOT `form-data.json`. This preserves every setting the user previously configured.
- **Use existing policy values as "current"** in prompts. When Mode A/B shows a field's current value, show the existing value, not the product default. Label the schema default separately only if the user asks.
- **Handle schema drift gracefully.** If the existing data is missing a key present in the current `form-data.json` (field added to the template after the policy was created), fill the gap from `form-data.json` and flag it in the final review as "new field: <KEY> = <DEFAULT>".
- **Changed-settings diff is vs. the existing policy**, not vs. product defaults. The final review shows what differs between `$SESSION_DIR/existing-policy-data.json` and `$SESSION_DIR/aops-policy-data.json`.

On completion: `$SESSION_DIR/aops-policy-data.json` is set and ready, and every previously configured value the user did not touch is preserved.

### Step 5 — Final review before update (single confirmation gate)

**Expect from configure-guide (if Step 4 ran):** updated `$SESSION_DIR/aops-policy-data.json` and a change-summary diffed against `existing-policy-data.json`.

This is the **only** yes/no confirmation in the update flow (Critical Rule #12). Show before/after for every changed field.

> **MANDATORY (Critical Rule #16):** the `Policy data` row is required in every update review — not optional. A review without this row is incomplete; do NOT proceed to `update` until it is added and the user has confirmed.

```text
Review policy update:

  Name:         <POLICY_NAME>       (was: <OLD_NAME>)
  Product:      <PRODUCT_LABEL> (unchanged)
  Description:  <DESCRIPTION>       (was: <OLD_DESCRIPTION>)
  Priority:     <PRIORITY>          (was: <OLD_PRIORITY>)  ← reminder: group-level tie-breaker only; lower number wins when a user is in multiple groups with competing policies for this product

  Policy data:  [aops-policy-data.json](<ABSOLUTE_PATH_TO_SESSION_DIR>/aops-policy-data.json)

  Changed settings (vs existing policy data):
    feedback-enabled             false   (was: true)
  Unchanged fields: 15 kept at existing values.

  New fields added by schema drift (if any):
    <KEY>                        <DEFAULT>   (new — filled from product default)

Open the linked file to see every field.
Apply update to policy "<POLICY_NAME>"? (yes / no / keep editing)
```

For each metadata row, show `(unchanged)` instead of `(was: ...)` when the user did not change that field. Only show the schema-drift block when Step 4 filled in at least one new field. `keep editing` is treated the same as `no`: route back to Step 3 or Step 4 and re-enter this gate only after the change is applied. Do NOT run `update` until the user confirms `yes`.

### Step 6 — Run update

> `update` is a **full replacement**, not a patch. Every field you want to keep must be passed again — including `--description`, `--priority`, `--availability`, and `--input`. Omitting any of these flags CLEARS that field on the server. See [aops-policy-commands.md — update](./aops-policy-commands.md#uip-gov-aops-policy-update) for the full flag reference.

```bash
uip gov aops-policy update \
  --identifier "$POLICY_IDENTIFIER" \
  --name "$POLICY_NAME" \
  --product-name "$PRODUCT_NAME" \
  --description "$DESCRIPTION" \
  --priority "$PRIORITY" \
  --input "$SESSION_DIR/aops-policy-data.json" \
  --output json
```

Re-pass every field the user wants to preserve. For any field the user did not change, read the existing value from `$SESSION_DIR/current-policy.json` (saved in Step 2) and pass it through unchanged. Always include `--input "$SESSION_DIR/aops-policy-data.json"` — this is the blueprint produced from `existing-policy-data.json` plus the user's edits, and omitting it wipes the data payload on the server. Only drop `--description`, `--priority`, or `--availability` when the user has explicitly asked to clear that field. `--product-name` must match the policy's existing product.

### Step 7 — Report success

```text
Policy updated successfully.
  Name:    <POLICY_NAME>
  ID:      <POLICY_ID>
  Product: <PRODUCT_LABEL>
```

---

## Delete a policy

> **Destructive.** This cannot be undone.

### Step 1 — Identify the policy

If the user did not provide a policy identifier, run `list` and ask them to pick one. Store as `$POLICY_IDENTIFIER`.

### Step 2 — Get and display the policy

```bash
uip gov aops-policy get "$POLICY_IDENTIFIER" --output json
```

Display:

```text
About to delete:
  Name:     <POLICY_NAME>
  Product:  <PRODUCT_LABEL>
  ID:       <POLICY_ID>
```

### Step 3 — Confirm with the user

Ask verbatim: `Delete policy "<POLICY_NAME>"? This cannot be undone. (yes / no)`

If the user answers anything other than `yes` (or `y`), abort and inform them that deletion was cancelled.

### Step 4 — Delete

```bash
uip gov aops-policy delete "$POLICY_IDENTIFIER" --output json
```

### Step 5 — Confirm

```text
Policy "<POLICY_NAME>" deleted successfully.
```

---

## Debug

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | User token expired or missing | `uip login` and retry — see [aops-policy-commands.md — Authentication](./aops-policy-commands.md#authentication) |
| `Policy not found` / `unknown policyIdentifier` | Stale or wrong GUID | Re-run `list` and copy the `identifier` from the result |
| `Priority conflict` / duplicate priority | Another policy for the same product already holds that priority | Pick a different number; see [SKILL.md — Priority rules](../SKILL.md#priority-rules) |
| `template get returned no template` | Product schema fetch failed (auth, transient network) | Retry; if persistent, verify `uip login status --output json` and the product name |
| `list returned empty` | No policies match the filter | Drop the filter or offer to create a new policy |
| `--name is required` on `update` | `update` is full-replacement; name was omitted | Pass `--name "$POLICY_NAME"` with the existing value to preserve it |
| `--product-name does not match existing product` | Attempt to change product on update | Product cannot be changed on update; delete + recreate instead |
| `--input contents wrapped in {"data":{...}}` | Blueprint was wrapped by hand | Write the raw flat object (Critical Rule #6) — CLI wraps automatically |
| `description` / `priority` / `availability` / `data` silently cleared after update | Flag was omitted on `update` | All update flags are full-replace; re-pass every field to preserve — see [aops-policy-commands.md — update](./aops-policy-commands.md#uip-gov-aops-policy-update) |
| `template upgrade in progress` on `update` | Template is being migrated | Retry once the upgrade completes |

---

## Related commands

- [aops-policy-commands.md](./aops-policy-commands.md) — every flag and output shape used above.
- [configure-aops-policy-data-guide.md](./configure-aops-policy-data-guide.md) — how `$SESSION_DIR/aops-policy-data.json` is produced.
- [aops-policy-deploy-guide.md](./aops-policy-deploy-guide.md) — what to do after a successful `create` or `update`.
