# Actor Plugin — Implementation

Concrete JSON for the `actorRule` block — the policy's **Actor Identity Rule**. Phase 2 reads this file to compose the `actorRule` block before assembling the top-level `PolicyDefinition` (see [planning-impl.md — Step 2](../../planning-impl.md#step-2--compose-each-block-via-plugins)). Omit the block entirely when the user expressed no identity intent.

> **Required field: `values`.** Every entry under `actorRule.values[]` must include its own `values` (use `["*"]` for "all of this type"). Missing `values` returns `400 Bad Request` (Critical Rule #5). `actorRule.tags` is **never supported** — do not add a `tags` block here.

> **Supported types: `User` and `Group` only** (Critical Rule #16). Robots resolve to `User` after lookup; `ExternalApplication` is not supported. See [planning.md](./planning.md) for the resolution flow.

## Full `actorRule` shape

```json
"actorRule": {
    "values": [
        { "type": "User",  "values": ["<USER_UUID>", "..."],  "operator": "<Or | None>" },
        { "type": "Group", "values": ["<GROUP_UUID>", "..."], "operator": "<Or | None>" }
    ]
}
```

### Structural constraints (Critical Rule #16)

- `values[]` carries **at most two entries** — one `User` and one `Group`. Either, both, or none of those entries may be present, but never duplicates of the same type.
- **Multiple users / groups go inside a single entry's `values[]` array** — never split across multiple entries of the same `type`.
- **Operators must match across the two entries.** When both `User` and `Group` are present, both `operator` fields must be the same value (both `"Or"` or both `"None"`). Mixed operators are rejected by the API. Mixed-operator user intent must be split into two policies (see [planning.md — Mixed-operator intent → two policies](./planning.md#mixed-operator-intent--two-policies)).

### Field rules

| Field | Required | Value rules |
|-------|----------|-------------|
| `values` | yes | Array of at most two per-type entries (one `User`, one `Group`). At least one entry when the block is emitted. |
| `values[].type` | yes | One of: `User`, `Group`. **Never** `ExternalApplication` or `Robot` (Critical Rule #16). Each type appears at most once across the array. |
| `values[].values` | yes | `["*"]` or specific UUIDs. Multiple identities of the same type are listed here, not split into multiple entries. Never empty. |
| `values[].operator` | yes | `"Or"` (include) or `"None"` (exclude). When both `User` and `Group` entries are present, this value MUST match across both entries. |
| `tags` | **NOT SUPPORTED** | `actorRule` does not accept a `tags` block today. Never emit one. If the user wants tag-style narrowing, enumerate the matching users / groups under `values[].values` instead. |

> **Whole-block emission is optional.** If the user did not mention any identity, omit the `actorRule` key from the top-level `PolicyDefinition` entirely — do NOT emit `{"values": [{"type": "User", "values": ["*"], "operator": "Or"}]}` as a default.

> **No `actorRule.tags`.** Unlike `selectors[]` and `executableRule`, the Actor Identity rule does not support tag filters today. Emitting `actorRule.tags` returns `400 Bad Request` from the API.

---

## Worked examples

### A. Single-type, specific users

**Intent:** "Only users alice-uuid and bob-uuid can trigger this".

```json
"actorRule": {
    "values": [
        { "type": "User", "values": ["alice-uuid", "bob-uuid"], "operator": "Or" }
    ]
}
```

### B. Single-type, all of one type

**Intent:** "Any user can trigger this" (no narrowing).

```json
"actorRule": {
    "values": [
        { "type": "User", "values": ["*"], "operator": "Or" }
    ]
}
```

> **No identity tag filter.** If the user said "any user tagged Admin", **`actorRule.tags` is not supported** — refuse and offer to (a) enumerate the admin user UUIDs under `values[].values`, (b) use a `Group` UUID for the Admins group, or (c) drop the tag filter so the rule applies to any user. Never emit `actorRule.tags`.

### C. Multi-type (one User entry + one Group entry — operators match)

**Intent:** "Members of the Ops group and admin users alice-uuid, bob-uuid can trigger this".

Both entries are include-style, so both use `operator: "Or"` (the operator must match across `User` and `Group` per Critical Rule #16):

```json
"actorRule": {
    "values": [
        { "type": "User",  "values": ["alice-uuid", "bob-uuid"], "operator": "Or" },
        { "type": "Group", "values": ["ops-group-uuid"],         "operator": "Or" }
    ]
}
```

**Mixed-operator intent → two policies.** If the user said "allow alice-uuid and bob-uuid **but exclude** the Ops group", the operators don't match and the API rejects it. Author two separate policies:

```json
// Policy A — allow specific users
"actorRule": {
    "values": [
        { "type": "User", "values": ["alice-uuid", "bob-uuid"], "operator": "Or" }
    ]
}

// Policy B — exclude the Ops group
"actorRule": {
    "values": [
        { "type": "Group", "values": ["ops-group-uuid"], "operator": "None" }
    ]
}
```

**Same-type merging.** Multiple users (or multiple groups) belong in **one** entry's `values[]` array. Do NOT emit two `User` entries — merge their UUIDs:

```json
// CORRECT — single User entry with multiple UUIDs
"actorRule": {
    "values": [
        { "type": "User", "values": ["alice-uuid", "bob-uuid", "carol-uuid"], "operator": "Or" }
    ]
}

// WRONG — duplicate User entries (rejected by the API)
"actorRule": {
    "values": [
        { "type": "User", "values": ["alice-uuid"], "operator": "Or" },
        { "type": "User", "values": ["bob-uuid"],   "operator": "Or" }
    ]
}
```

### D. Deny-flipped actor

**Intent (original):** "block user alice-uuid". **Flipped to Allow** with the `None` operator:

```json
"actorRule": {
    "values": [
        { "type": "User", "values": ["alice-uuid"], "operator": "None" }
    ]
}
```

This allows every User **except** `alice-uuid`. (See [../tags/planning.md — Deny-to-Allow flip](../tags/planning.md#deny-to-allow-flip) for the decision procedure.)

### E. Robot-only trigger (resolves to `User`)

**Intent:** "Only the unattended robot `build-bot` can trigger this".

Resolution flow (see [planning.md — Robot intent](./planning.md#robot-intent-resolves-to-user)):
1. `GET /orchestrator_/odata/Robots` → match `build-bot` → read `Username`.
2. `uip or users list` filtered on that `UserName` → get the User UUID `bot-user-uuid`.
3. Emit:

```json
"actorRule": {
    "values": [
        { "type": "User", "values": ["bot-user-uuid"], "operator": "Or" }
    ]
}
```

> Never emit `{ "type": "Robot", ... }`. The server rejects it as an unknown type, and the policy authoring contract does not support it (Critical Rule #16).

---

## Update-flow use

When `policy-manage-guide.md — Update` needs to modify an existing `actorRule`:

1. Start from the working file's current `actorRule` object (or absence — "add identity constraint" means inserting the block fresh).
2. Change only the part the user asked about (add a type, add a UUID, flip an operator, adjust `tags`).
3. Preserve every other field.

Example: existing rule allows specific admin users; user says "also allow members of the Ops group".

Before:

```json
"actorRule": {
    "values": [
        { "type": "User", "values": ["alice-uuid", "bob-uuid"], "operator": "Or" }
    ]
}
```

After:

```json
"actorRule": {
    "values": [
        { "type": "User",  "values": ["alice-uuid", "bob-uuid"], "operator": "Or" },
        { "type": "Group", "values": ["ops-group-uuid"],         "operator": "Or" }
    ]
}
```

> **No `actorRule.tags`.** If you find a legacy `actorRule.tags` block on a policy fetched via `get`, drop it from the working file before submitting the update — emitting it returns `400 Bad Request` (see Debug table below).

Removing the block entirely: drop the `actorRule` key from the working file (do not set it to `null` or `{}`).

---

## Debug

| Error / signal | Cause | Fix |
|----------------|-------|-----|
| `400 Bad Request` / `ActorRule.Values is required` | `actorRule.values` empty or missing while block is present | Remove the `actorRule` key entirely, or include at least one entry. |
| `400 Bad Request` / unknown actor `type` | Typo, or emitted `Robot` / `ExternalApplication`, or a resource type like `Agent` / `APIWorkflow` | Use exactly one of `User`, `Group`. Robot intent must be resolved to a `User` UUID first (Critical Rule #16). |
| `400 Bad Request` / duplicate `type` in `actorRule.values` | Emitted two `User` entries (or two `Group` entries) | Merge them into a single entry whose `values[]` lists every UUID. `actorRule.values[]` carries at most one entry per type (Critical Rule #16). |
| `400 Bad Request` / mismatched operators in `actorRule.values` | The `User` entry uses `operator: "Or"` and the `Group` entry uses `operator: "None"` (or vice versa) | Operators must match across both entries (Critical Rule #16). For mixed-include/exclude intent, split into two policies (see Worked Example C). |
| `400 Bad Request` on `type: Group` | Server build does not accept `Group` | Fall back to enumerating member user UUIDs under a single `type: User` entry. Report the limitation. |
| `400 Bad Request` / `Values is required` on a per-entry field | An entry's own `values` is empty | Use `["*"]` or specific UUIDs — never `[]`. |
| Policy never matches the intended actor | Actor UUID not in `values` | Log in as that user (`uip login`) and run `uip gov access-policy evaluate --resource-type <TYPE> --output json` — the calling user is taken from the bearer. (Under an S2S token, pass `--actor-identity-id <UUID>` instead.) |
| `400 Bad Request` referencing `tags` on `actorRule` | Emitted an `actorRule.tags` block (or kept one inherited from a fetched policy) | Remove the `tags` key from `actorRule` — Actor Identity does not support tag filters today (Spec rules / Critical Rule #5). Enumerate matching users / groups under `values[].values` instead. |
| Evaluation returns Deny even though selectors + executable match | `actorRule` is present and the caller's identity falls outside `values` | Check whether the block should be present at all; omit it if the user never asked for identity enforcement. |
