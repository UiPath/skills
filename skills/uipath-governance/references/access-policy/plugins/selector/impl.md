# Selector Plugin — Implementation

Concrete JSON for a single entry in `selectors[]`. Phase 2 reads this file to compose every selector before assembling the top-level `PolicyDefinition` (see [planning-impl.md — Step 2](../../planning-impl.md#step-2--compose-each-block-via-plugins)).

> **Required field: `values`.** Every `selectors[]` entry must include `values` (use `["*"]` for "all of this type") — it cannot be omitted, even when `tags` narrow the scope. Missing `values` returns `400 Bad Request` (Critical Rule #5).

## Single selector entry

```json
{
    "resourceType": "<Agent | AgenticProcess | RPAWorkflow | APIWorkflow | CaseManagement | Flow>",
    "values": ["*"],
    "operator": "<Or | None>",
    "tags": {
        "values": ["<TAG_1>", "<TAG_2>"],
        "operator": "<Or | And | None>"
    }
}
```

### Field rules

| Field | Required | Value rules |
|-------|----------|-------------|
| `resourceType` | yes | One of: `Agent`, `AgenticProcess`, `RPAWorkflow`, `APIWorkflow`, `CaseManagement`, `Flow`. |
| `values` | yes | `["*"]` for all-of-type, or `["<UUID>", ...]` for specific IDs. Never empty. |
| `operator` | yes | `"Or"` to include matching IDs; `"None"` to exclude them. |
| `tags` | optional | Omit entirely when the user did not specify tags. When present, compose via [tags/impl.md](../tags/impl.md). |

## Full `selectors[]` array shape

The top-level `PolicyDefinition.selectors` is always an array:

```json
"selectors": [
    { /* entry 1 */ },
    { /* entry 2 */ }
]
```

One array entry per distinct `resourceType` row in the Spec Components Table.

---

## Worked examples

### A. All-of-type with tag filter

**Intent:** "All Production Agents".

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

### B. Specific UUIDs, no tag filter

**Intent:** "Agents with IDs abc-123 and def-456".

```json
{
    "resourceType": "Agent",
    "values": [
        "abc-123",
        "def-456"
    ],
    "operator": "Or"
}
```

(Note: `tags` is omitted — the user did not mention any.)

### C. Specific UUIDs plus tag filter

**Intent:** "Agent abc-123 (must also be Production-tagged)".

```json
{
    "resourceType": "Agent",
    "values": ["abc-123"],
    "operator": "Or",
    "tags": {
        "values": ["Production"],
        "operator": "Or"
    }
}
```

Both filters apply — the policy matches resources that appear in `values` **and** satisfy `tags`.

### D. Multi-entry (two resource types in one policy)

**Intent:** "Production Agents and Production Flows".

```json
"selectors": [
    {
        "resourceType": "Agent",
        "values": ["*"],
        "operator": "Or",
        "tags": { "values": ["Production"], "operator": "Or" }
    },
    {
        "resourceType": "Flow",
        "values": ["*"],
        "operator": "Or",
        "tags": { "values": ["Production"], "operator": "Or" }
    }
]
```

### E. Deny-flipped (exclude Development tags)

**Intent (original):** "block Development Agents". **Flipped to Allow** with the `None` operator on tags (see [tags/planning.md — Deny-to-Allow flip](../tags/planning.md#deny-to-allow-flip)):

```json
{
    "resourceType": "Agent",
    "values": ["*"],
    "operator": "Or",
    "tags": {
        "values": ["Development"],
        "operator": "None"
    }
}
```

This matches every Agent **except** those tagged `Development`.

---

## Update-flow use

When `policy-manage-guide.md — Update` needs to modify an existing selector, pass the existing entry back through this file:

1. Start from the existing entry (already in the working file's `selectors[]`).
2. Change only the field the user asked about (e.g. add an ID to `values`, swap a tag operator).
3. Preserve every other field verbatim.

Example: the user says "add UUID `xyz-789` to the first selector's values". The resulting entry:

```json
{
    "resourceType": "Agent",
    "values": ["abc-123", "xyz-789"],
    "operator": "Or",
    "tags": { "values": ["Production"], "operator": "Or" }
}
```

Everything except `values` is unchanged from the original.

---

## Debug

| Error | Cause | Fix |
|-------|-------|-----|
| `400 Bad Request` / `Selectors[0].Values is required` | `values` missing or empty | Always pass `["*"]` or real UUIDs. Never an empty array. |
| `400 Bad Request` / unknown `resourceType` | Typo or non-existent enum | Use exactly one of the six enum values above. |
| Policy matches nothing at runtime | `values` has specific UUIDs that don't exist, or tag filter doesn't match any resource | Re-run `uip gov access-policy evaluate` with a real resource UUID to confirm matching; check the Resource Catalog tags on the resource. |
| Selectors for multiple types merged into one entry | Attempted to put multiple `resourceType` values in one entry | Split into multiple `selectors[]` entries. Each entry is single-type. |
