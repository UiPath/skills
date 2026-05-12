# Phase 2 — Implementation Resolution

Compose the concrete `PolicyDefinition` JSON from an **approved Phase 1 Spec** (narrative paragraph + Spec Components Table — see [planning-arch.md](./planning-arch.md)). This phase walks each row of the Spec table and reads the matching plugin's `impl.md` to produce the exact JSON — it never writes JSON from memory and it never re-interprets the user's chat history.

> **Prerequisite:** the user must have explicitly approved a Spec via [planning-arch.md](./planning-arch.md). If no Spec exists, or the Spec still has `(missing)` rows or open questions, return to Phase 1.

---

## Step 1 — Gather identity

Every `PolicyDefinition` requires `organizationId` and `tenantId` at the top level. Read them from `~/.uipath/.auth` — see [access-policy-commands.md — Reading `organizationId` and `tenantId`](./access-policy-commands.md#reading-organizationid-and-tenantid) for the exact command. Use the two UUIDs verbatim in the assembled JSON; never hardcode (Critical Rule #3).

If the file is missing or the IDs are not present, the user is not logged in — stop and route them to [access-policy-commands.md — Authentication](./access-policy-commands.md#authentication).

---

## Step 2 — Compose each block via plugins

Walk the Spec Components Table row-by-row. For every Resource / Actor Process / Actor Identity row, read the matching plugin's `impl.md` and follow its JSON shape exactly. The plugin `impl.md` is the only authoritative source for block-level JSON — do NOT reconstruct from memory.

> **Spec must arrive without UUID placeholders.** Phase 1 is responsible for resolving every name to a real UUID via [resource-lookup-guide.md](./resource-lookup-guide.md) (Critical Rule #15) before the user approves the Spec. If a `<…_UUID>` placeholder reaches Phase 2, the Spec is incomplete — stop, return to Phase 1, run the missing lookup, re-approve. Never paste a placeholder into the policy file.

| Spec rows | Plugin impl file | Produces |
|-----------|------------------|----------|
| Resource rows (Spec rows 5/6, plus 7 if a tag filter) | [plugins/selector/impl.md](./plugins/selector/impl.md) | One entry of `selectors[]` per Resource type |
| Actor Process rows (Spec rows 8/9, plus 10 if a tag filter) | [plugins/executable/impl.md](./plugins/executable/impl.md) | The `executableRule` object |
| Actor Identity rows (Spec rows 11/12) — only when present in the Spec (omitted entirely when the user gave no identity intent). **No tags** — `actorRule` does not support tag filters today | [plugins/actor/impl.md](./plugins/actor/impl.md) | The `actorRule` object |
| Any tag-filter row (rows 7 / 10 only) | [plugins/tags/impl.md](./plugins/tags/impl.md) | `{ values: [...], operator: ... }` |

Work in this order so the assembled object is complete before the review gate:

1. For every Resource row in the Spec, follow [plugins/selector/impl.md](./plugins/selector/impl.md). If the row has a tag filter (Spec row 7), compose it via [plugins/tags/impl.md](./plugins/tags/impl.md) and nest it inside the selector.
2. Follow [plugins/executable/impl.md](./plugins/executable/impl.md) to build the single `executableRule` from the Actor Process rows. If row 10 has a tag filter, compose it via [plugins/tags/impl.md](./plugins/tags/impl.md) and nest it at the top level of `executableRule` (not per-entry).
3. **Only if the Spec has Actor Identity rows present** (rows 11/12 are not `(none = any identity)`), follow [plugins/actor/impl.md](./plugins/actor/impl.md) to build the `actorRule` object. **Never emit `actorRule.tags`** — tags are not supported on Actor Identity today (see [plugins/actor/impl.md — Field rules](./plugins/actor/impl.md)). If the Spec has no Actor Identity rows, **omit the `actorRule` key entirely** from the top-level document — do not emit an empty or default block.

---

## Step 3 — Assemble the top-level `PolicyDefinition`

Wrap the composed blocks with the fixed top-level fields:

```json
{
  "policyType": "ToolUsePolicy",
  "organizationId": "<ORG_UUID>",
  "tenantId": "<TENANT_UUID>",
  "name": "<POLICY_NAME>",
  "description": "<DESCRIPTION>",
  "selectors": [
    /* one or more selector blocks from Step 2 */
  ],
  "executableRule": {
    /* Actor Process Rule — executable rule block from Step 2 */
  },
  "actorRule": {
    /* Actor Identity Rule — OMIT this key entirely if the Spec has no Actor Identity rows */
  },
  "enforcement": "Allow",   /* always "Allow" — never "Deny" (Critical Rule #2) */
  "status": "Simulated"
}
```

### Fixed-value rules

| Field | Source | Notes |
|-------|--------|-------|
| `policyType` | always `"ToolUsePolicy"` | The only type this skill mutates (Critical Rule #2). |
| `name` | Spec row 1 | Required. |
| `description` | Spec row 2 | Required. Should match the Spec narrative paragraph. |
| `enforcement` | Spec row 4 (always `Allow`) | **Always `"Allow"`** — `"Deny"` is not authorable (Critical Rule #2). Deny intent is expressed by writing an Allow policy that targets the complement of what should be blocked (re-framed scope, or `operator: "None"` on tags / values). Never emit `"enforcement": "Deny"`. |
| `status` | Spec row 3 (default `Simulated`) | Default `Simulated` for new policies (Critical Rule #13). Emit `Active` only when the Spec explicitly says so. |
| `organizationId`, `tenantId` | from Step 1 | Never hardcoded. |

### Fields to OMIT

Do NOT include these in the file — they are server-managed:

- `id` (create only; required on update — see [policy-manage-guide.md — Update](./policy-manage-guide.md#update-a-policy))
- `isBuiltIn`, `isTemplate`
- `createdBy`, `createdOn`, `modifiedBy`, `modifiedOn`
- `deletedBy`, `deletedOn`

---

## Step 4 — Write the working file

Reuse the **same slug** Phase 1 used for `/tmp/access-policy-<slug>.spec.md` (see [planning-arch.md — Spec file convention](./planning-arch.md#spec-file-convention)) so the Spec and JSON sit side by side under the same name:

```bash
SLUG=$(echo "<POLICY_NAME>" | tr '[:upper:] ' '[:lower:]-' | tr -cd '[:alnum:]-')
POLICY_FILE="/tmp/access-policy-${SLUG}.json"
SPEC_FILE="/tmp/access-policy-${SLUG}.spec.md"   # already written by Phase 1 — must exist
```

Write the assembled top-level object to `$POLICY_FILE`. The file contents must be the raw `PolicyDefinition` object — do NOT wrap it in `{ "data": {...} }`.

If `$SPEC_FILE` does not exist when Phase 2 runs, the Spec was never approved — return to Phase 1.

For **update** flows, the file path convention is `/tmp/access-policy-<id>-working.json` and the file starts as a copy of `Data` from `get` — see [policy-manage-guide.md — Update](./policy-manage-guide.md#update-a-policy) Step 2. Updates do NOT generate a `.spec.md` (Critical Rule #8 — the existing server `Data` is the source of truth).

---

## Step 5 — Handoff

Return both the composed `$POLICY_FILE` (JSON) and the `$SPEC_FILE` (markdown, written by Phase 1) paths to [policy-manage-guide.md](./policy-manage-guide.md), which:

1. Runs the **single review gate** — shows the full JSON in chat plus clickable links to **both** `$SPEC_FILE` and `$POLICY_FILE` (resolved absolute paths) so the user can compare the human-readable Spec against the machine payload before approval.
2. Requires explicit `yes`.
3. Runs `uip gov access-policy create --file "$POLICY_FILE" --output json` (or `update`).
4. Verifies the result with `get`.

Phase 2 does NOT run the CLI itself and does NOT prompt for confirmation — all confirmation consolidates in the manage-guide.

---

## Iteration

If the review gate in the manage-guide is answered with `keep editing`, route back based on the scope of the change:

| Change scope | Route to |
|--------------|----------|
| Top-level metadata only (Spec rows 1/2/3 — name, description, status; row 4 enforcement is fixed at `Allow` per Critical Rule #2) | [policy-manage-guide.md — Step 3](./policy-manage-guide.md#create-a-policy) |
| A block's JSON shape (enum, targeting, operator) | The relevant plugin's `impl.md` — compose that block again and splice back into the file |
| Intent itself (which resource? which actor process? Deny-flip?) | [planning-arch.md](./planning-arch.md) — return to Spec iteration, get a fresh `yes`, then re-run Phase 2 |

Re-enter the review gate only after the change is applied.
