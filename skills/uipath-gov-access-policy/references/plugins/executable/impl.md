# Executable Plugin — Implementation

Concrete JSON for the `executableRule` block. Phase 2 reads this file to compose the single `executableRule` block before assembling the top-level `PolicyDefinition` (see [planning-impl.md — Step 2](../../planning-impl.md#step-2--compose-each-block-via-plugins)).

> **Required field: `values`.** Every entry under `executableRule.values[]` must include its own `values` (use `["*"]` for "all of this type") — it cannot be omitted, even when the shared `executableRule.tags` narrow the scope. Missing `values` returns `400 Bad Request` (Critical Rule #5).

## Full `executableRule` shape

```json
"executableRule": {
    "values": [
        {
            "type": "<Agent | AgenticProcess | CaseManagement | Flow>",
            "values": ["*"],
            "operator": "<Or | None>"
        }
    ],
    "tags": {
        "values": ["<TAG_1>"],
        "operator": "<Or | And | None>"
    }
}
```

### Field rules

| Field | Required | Value rules |
|-------|----------|-------------|
| `values` | yes | Array of per-type entries. At least one entry. **Caller types not listed in `values[]` are NoOp on this policy** — this policy does not constrain them. Use this directly to author "any caller type except `<type>`" intent: list ONLY the excluded type with `operator: "None"` and omit the others. See [Example E](#e-all-caller-types-except-a-specific-type-canonical-idiom). |
| `values[].type` | yes | One of: `Agent`, `AgenticProcess`, `CaseManagement`, `Flow`. NOT `RPAWorkflow` or `APIWorkflow`. |
| `values[].values` | yes | `["*"]` or specific UUIDs. Never empty. |
| `values[].operator` | yes | `"Or"` (include) or `"None"` (exclude). On a `["*"]` entry, `"None"` means "match any caller of types other than this entry's `type`". |
| `tags` | optional | Omit entirely when there are no tag constraints. When present, compose via [tags/impl.md](../tags/impl.md). Applies to every entry in `values[]`. |

---

## Worked examples

### A. Single-type, all-of-type, with tag filter

**Intent:** "Production Maestros can use the resource".

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

### B. Single-type, specific UUIDs, no tag filter

**Intent:** "The Maestro with ID def-456 can use the resource".

```json
"executableRule": {
    "values": [
        { "type": "AgenticProcess", "values": ["def-456"], "operator": "Or" }
    ]
}
```

(`tags` omitted.)

### C. Multiple executable types in one rule

**Intent:** "Both Agents and Maestros can use the resource, but only Production ones".

```json
"executableRule": {
    "values": [
        { "type": "Agent",          "values": ["*"], "operator": "Or" },
        { "type": "AgenticProcess", "values": ["*"], "operator": "Or" }
    ],
    "tags": {
        "values": ["Production"],
        "operator": "Or"
    }
}
```

The `tags` block applies to both entries.

### D. Deny-flipped executable

**Intent (original):** "block Development Flows from using the resource". **Flipped to Allow** with the `None` operator on the executable's tags:

```json
"executableRule": {
    "values": [
        { "type": "Flow", "values": ["*"], "operator": "Or" }
    ],
    "tags": {
        "values": ["Development"],
        "operator": "None"
    }
}
```

This allows every Flow **except** Development-tagged ones.

### E. All caller types except a specific type (canonical idiom)

**Intent:** "Any caller can use the resource except `Agent` callers" — i.e. allow `AgenticProcess`, `CaseManagement`, and `Flow` callers but not `Agent` callers.

```json
"executableRule": {
    "values": [
        { "type": "Agent", "values": ["*"], "operator": "None" }
    ]
}
```

Emit ONE entry — the caller type to exclude — with `operator: "None"` and `values: ["*"]`. Caller types not listed (`AgenticProcess`, `CaseManagement`, `Flow`) are NoOp on this filter, so this policy does not constrain them. Combined with `enforcement: "Allow"`, the policy contributes Allow for any non-`Agent` caller.

> **Use this idiom whenever the intent is "any caller type except `<type>`".** Do NOT enumerate every allowed type with `Or` — that produces the same effect but is verbose, error-prone, and obscures the intent. Listing only the excluded type with `None` is the canonical shape.

---

## Update-flow use

When `policy-manage-guide.md — Update` needs to modify the existing `executableRule`:

1. Start from the working file's current `executableRule` object.
2. Change only the part the user asked about (add a type, add a UUID to an entry's `values`, flip an operator, adjust `tags`).
3. Preserve every other field.

Example: the user says "also allow CaseManagement". Existing `executableRule`:

```json
{
    "values": [
        { "type": "AgenticProcess", "values": ["*"], "operator": "Or" }
    ],
    "tags": { "values": ["Production"], "operator": "Or" }
}
```

After update:

```json
{
    "values": [
        { "type": "AgenticProcess",  "values": ["*"], "operator": "Or" },
        { "type": "CaseManagement",  "values": ["*"], "operator": "Or" }
    ],
    "tags": { "values": ["Production"], "operator": "Or" }
}
```

Only `values[]` changed — `tags` is preserved verbatim.

---

## Debug

| Error | Cause | Fix |
|-------|-------|-----|
| `400 Bad Request` / `ExecutableRule.Values is required` | `executableRule.values` missing or empty | Include at least one entry with `type` and `values`. |
| `400 Bad Request` / unknown executable `type` | Tried `RPAWorkflow` or `APIWorkflow` | These are resource-only. Move them to `selectors[]`. |
| `400 Bad Request` / `Values is required` on a per-entry field | An entry's own `values` is missing | Use `["*"]` or specific UUIDs — never an empty array. |
| Policy never matches the intended caller | Caller's tags don't include the tag values in `executableRule.tags`, or caller UUID isn't in `values` | Verify the Resource Catalog tags on the executable, or use `["*"]` + tag filter. |
| Two different executable types need different tag filters | Tried to put `tags` on a single `values[]` entry | Not supported — split the intent into two policies, one per executable type. |
