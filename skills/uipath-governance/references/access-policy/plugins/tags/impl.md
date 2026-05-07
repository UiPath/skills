# Tags Plugin — Implementation

Concrete JSON for the shared `tags` sub-object. Phase 2 reads this file whenever a selector entry or `executableRule` needs a tag filter (see [planning-impl.md — Step 2](../../planning-impl.md#step-2--compose-each-block-via-plugins)).

> **Required when `tags` is present: `values` and `operator`.** When the `tags` key exists, both `tags.values` (non-empty array) and `tags.operator` (`Or` / `And` / `None`) are required. Omit the entire `tags` key when there is no tag constraint — never emit `"tags": {}` or `"tags": { "values": [] }`.

## Shape

```json
"tags": {
    "values": ["<TAG_1>", "<TAG_2>"],
    "operator": "<Or | And | None>"
}
```

### Field rules

| Field | Required | Value rules |
|-------|----------|-------------|
| `values` | yes (when `tags` is present) | Non-empty array of Resource Catalog tag name strings. Never `[]`. |
| `operator` | yes (when `tags` is present) | One of `"Or"`, `"And"`, `"None"`. Case-sensitive. |

Omit the entire `tags` key when the user did not specify tags. Do NOT emit `"tags": {}` or `"tags": { "values": [] }`.

## Operator cheat-sheet

| Operator | Rule semantics |
|----------|----------------|
| `"Or"` | Match if the resource has **any** of `values`. |
| `"And"` | Match if the resource has **all** of `values`. |
| `"None"` | Match if the resource has **none** of `values` (i.e., exclude). |

See [tags/planning.md](./planning.md) for when to pick each.

---

## Worked examples

### A. Single-tag `Or` (most common)

**Intent:** "only Production resources".

```json
"tags": {
    "values": ["Production"],
    "operator": "Or"
}
```

### B. Multi-tag `And`

**Intent:** "resources tagged both Production and Critical".

```json
"tags": {
    "values": ["Production", "Critical"],
    "operator": "And"
}
```

Only resources carrying both tags match.

### C. Deny-flip with `None`

**Intent (original):** "deny Development resources". **Flipped to Allow** (see [planning.md — Deny-to-Allow flip](./planning.md#deny-to-allow-flip)):

```json
"tags": {
    "values": ["Development"],
    "operator": "None"
}
```

This matches every resource **except** those tagged `Development`.

### D. Multi-tag `None` (exclude any of several)

**Intent (original):** "block Development or Staging flows". On the selector (`resourceType: Flow`):

```json
"tags": {
    "values": ["Development", "Staging"],
    "operator": "None"
}
```

Matches every Flow that does **not** carry either tag.

---

## Where this block embeds

Paste the composed `tags` object into the parent block returned by [selector/impl.md](../selector/impl.md) or [executable/impl.md](../executable/impl.md). Example embedded in a selector entry:

```json
{
    "resourceType": "Agent",
    "values": ["*"],
    "operator": "Or",
    "tags": {
        "values": ["Production"],
        "operator": "Or"
    }
}
```

And embedded at the top of `executableRule` (applies to every entry in `executableRule.values[]`):

```json
"executableRule": {
    "values": [
        { "type": "AgenticProcess", "values": ["*"], "operator": "Or" }
    ],
    "tags": {
        "values": ["Production"],
        "operator": "Or"
    }
}
```

---

## Update-flow use

When `policy-manage-guide.md — Update` needs to change tags on an existing block:

1. Start from the existing `tags` object in the working file (copied from `.Data` in the update prelude).
2. Mutate only the fields the user asked about — add/remove entries in `values`, or flip `operator`.
3. If the user wants to remove tag filtering entirely, delete the `tags` key (do not leave behind an empty object).

Example: the user says "also exclude Staging". Existing:

```json
{ "values": ["Development"], "operator": "None" }
```

After update:

```json
{ "values": ["Development", "Staging"], "operator": "None" }
```

---

## Debug

| Error / symptom | Cause | Fix |
|-----------------|-------|-----|
| `400 Bad Request` / `Tags.Values is required` | `tags.values` is missing or empty | Either populate with at least one tag, or remove the `tags` key entirely. |
| `400 Bad Request` / unknown operator | Typo (e.g. `"or"`, `"NOT"`, `"Not"`) | Use exactly `"Or"`, `"And"`, or `"None"` — case-sensitive. |
| Policy never matches anything at runtime | Tag name doesn't exist in the Resource Catalog of the policy's tenant, or target resource isn't labeled with it | Verify the tag with `uip admin rcs tag list --output json` (no `--tenant` — the default targets the policy's own tenant). See [resource-lookup-guide.md § 4](../../resource-lookup-guide.md#4-resource-catalog-tags). If the tag is missing, add it to the Resource Catalog of the policy's tenant or pick a tag from the returned list. |
| `None` operator matches more than expected | `None` excludes only the named tags — everything else matches | If the user meant "only these and nothing else", they want `Or`, not `None`. Re-check intent with them. |
| API rejected `enforcement: "Deny"` | The skill emitted `enforcement: "Deny"` — never authorable (Critical Rule #2) | Switch to `enforcement: "Allow"` and re-author. See [planning.md — Deny-to-Allow flip](./planning.md#deny-to-allow-flip). |
