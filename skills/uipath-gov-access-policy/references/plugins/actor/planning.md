# Actor Identity Plugin — Planning

> **User-facing terminology vs JSON field.** The user-facing name for this block is **Actor Identity rule**. The underlying JSON field is `actorRule` — that name is only shown in code / CLI contexts. When summarizing the policy to the user, always say "Actor Identity rule", never "Actor rule".

The `actorRule` block is the policy's **Actor Identity Rule** — it identifies **who** (which user or group) is allowed (or blocked) from triggering the Actor Process that invokes the Resource. The access policy has at most one `actorRule` block, which can hold at most two entries — one `User` and one `Group` (Critical Rule #16).

> **Supported types: `User` and `Group` only** (Critical Rule #16). `ExternalApplication` is **not supported** today; reject any intent that names a service principal / registered app and route the user to use a User or Group instead, or to omit Actor Identity entirely. **Robot intent maps to `User`** — look up the robot via [resource-lookup-guide.md § Robots](../../resource-lookup-guide.md#robots-resolve-to-type-user) (REST → `Username` → `uip or users list`), resolve to its linked User UUID, and emit a `User`-typed entry. Never emit `type: "Robot"` or `type: "ExternalApplication"`.

> **Terminology recap.** The access policy has three rule parts:
> - **Selection Rule** → `selectors[]` — which Resource/Tool the policy applies to.
> - **Actor Process Rule** → `executableRule` — which executable workflow is calling the Resource.
> - **Actor Identity Rule** → `actorRule` — which user or group is triggering the Actor Process.
>
> All three must pass for the evaluation result to be Allow. See [../../../SKILL.md](../../../SKILL.md) for the full evaluation flow.

## When to Use

Emit `actorRule` **only when the user expressed actor-identity intent**. If the user did not mention a user, group, or robot identity, omit the block entirely — absence of `actorRule` means "any actor passes the identity check".

## When intent is actor-shaped

Flag these phrases during Phase 1 and route them to this plugin:

- "only admins can…", "only user X can…"
- "restrict user X from…", "block user Y from…"
- "members of group G can…", "users in group Z can…"
- "on behalf of actor X…"
- "when robot R triggers…" (resolves to `User` — see [Robot intent](#robot-intent-resolves-to-user))

If the user names an external application / service principal / S2S app / registered app, **stop and tell them** that `ExternalApplication` is not supported today (Critical Rule #16). Offer the workarounds:
- Use a `User` (the user account the app authenticates as), or
- Use a `Group` containing the app's identity, or
- Omit the Actor Identity rule entirely so the policy applies regardless of identity.

## Block shape (conceptual)

```text
actorRule = {
    values: [
        { type: "User",  values: [<user_uuid>, <user_uuid>, ...],   operator: <Or | None> },
        { type: "Group", values: [<group_uuid>, <group_uuid>, ...], operator: <Or | None> }
    ]
}
```

Strict structural constraints (Critical Rule #16):

- `actorRule.values[]` carries **at most two entries** — at most one `User` entry and at most one `Group` entry. Never duplicate entries of the same type.
- **Multiple users / groups go inside a single entry's `values[]` array**, not as multiple entries. If the user names three admin users plus the Ops group, that is one `User` entry (with three UUIDs) plus one `Group` entry (with one UUID) — two entries total.
- **Operators must match across `User` and `Group`.** When both entries are present, their `operator` must be the same value (both `Or`, or both `None`). Mixing `Or` on one and `None` on the other is invalid — the API rejects it. If the user expresses mixed intent (e.g. "allow these users but exclude this group"), split into **two policies**: one with the `User` entry (operator `Or`) and one with the `Group` entry (operator `None`).
- **No `tags` block.** Unlike `selectors[]` and `executableRule`, `actorRule` does **not** support `tags` today. If the user asks for an identity tag filter, refuse and offer to enumerate the matching users / groups directly under `values[]`, or to drop the tag filter entirely.

## Intent → actor identity type

Map the user's phrasing to the enum.

| User phrase | `type` |
|-------------|--------|
| "user X", "specific person", "admin Alice" | `User` |
| "group G", "members of group", "role X" | `Group` |
| "robot R", "unattended robot", "attended robot" | `User` (resolve via [Robot intent](#robot-intent-resolves-to-user)) |
| "external application", "service account", "S2S app", "registered app" | **Not supported** — reject and offer workarounds (see [When intent is actor-shaped](#when-intent-is-actor-shaped)). |

## Targeting modes

Same two modes as selectors and executables:

| Mode | `values` | `operator` |
|------|----------|------------|
| **All of this type** | `["*"]` | `Or` |
| **Specific IDs** | `["<UUID>", ...]` | `Or` |
| **Exclude specific IDs** | `["<UUID>", ...]` | `None` |

`values: ["*"]` is required on every entry (Critical Rule #5). Missing it returns `400`.

### Resolving Actor Identity names to UUIDs

If the user named a specific identity ("only Alice", "members of group Ops"), resolve the name to a UUID via [resource-lookup-guide.md](../../resource-lookup-guide.md):

- **User** → `uip or users list --output json` (filter by `UserName` / `Name`). `uip or users current --output json` for "only me".
- **Group** → no public Orchestrator endpoint. Ask the user to paste the UUID from the Admin portal and record it as an **Open question** on the Phase 1 Spec until supplied.

Present matched users as a numbered picker (see [resource-lookup-guide.md § 3](../../resource-lookup-guide.md#3-users-actor-identity-uuids)). Never silently pick the first row.

### Robot intent resolves to `User`

A robot in UiPath identity is **a kind of user** (Critical Rule #16). When the user says "robot R can trigger…":

1. Look up the robot via the REST fallback `GET /orchestrator_/odata/Robots` — see [resource-lookup-guide.md § Robots](../../resource-lookup-guide.md#robots-resolve-to-type-user) for the secure token-sourcing pattern.
2. Read the `Username` field on the matched robot record.
3. Resolve that username to a User UUID with `uip or users list --output json` filtered on `UserName`.
4. Emit `{ "type": "User", "values": ["<USER_UUID>"], "operator": "Or" }` — never `type: "Robot"`.

If the robot has no linked user (rare), surface as an Open question and stop — do not invent a UUID.

## Multi-type actor rules

`actorRule.values[]` holds **at most two entries** — one `User` and one `Group`. Same-type identities are merged into a single entry's `values[]` array, never duplicated as separate entries.

### Single-`User`-entry merging (users + robots in one entry)

If the user says "users alice-uuid, bob-uuid, and the build-bot robot can trigger…", these are **all `User`** in the JSON (Critical Rule #16 — robots resolve to `User`). Resolve the robot to its linked User UUID, then merge all three into one `User` entry — never emit two `User` entries:

```text
actorRule:
  values:
    1. type: User, values: ["alice-uuid", "bob-uuid", "<bot-user-uuid>"], operator: Or
```

### Two-type case (operators must match)

If the user says "admins **and** members of group Ops can trigger…", emit one `User` entry plus one `Group` entry — both with the **same** operator:

```text
# CORRECT — both entries use operator: Or
actorRule:
  values:
    1. type: User,  values: ["<ADMIN_UUID>", ...], operator: Or
    2. type: Group, values: ["<OPS_GROUP_UUID>"],  operator: Or
```

The pattern below is **rejected by the API** (mismatched operators across the two entries):

```text
# REJECTED — User uses Or, Group uses None — API returns 400 Bad Request
actorRule:
  values:
    1. type: User,  values: ["<ADMIN_UUID>"],     operator: Or       # ← include
    2. type: Group, values: ["<OPS_GROUP_UUID>"], operator: None     # ← exclude (mismatch)
```

To express that mixed intent, split into two policies — see [Mixed-operator intent → two policies](#mixed-operator-intent--two-policies) below.

### Mixed-operator intent → two policies

If the user wants to **allow** specific users but **exclude** a group (or vice versa), the operators don't match — that cannot be expressed in a single `actorRule`. Split into two policies and tell the user:

- Policy A: `actorRule.values: [{ type: "User", values: [...], operator: "Or" }]`
- Policy B: `actorRule.values: [{ type: "Group", values: [...], operator: "None" }]`

There is no `actorRule.tags` block — tags are not supported on Actor Identity today. To narrow within a type, list the specific UUIDs.

## Deny-flipped actor intent

"**Deny** user Alice from triggering this resource" must be expressed as Allow with `operator: None` (Critical Rule #2 — `enforcement: "Deny"` is not authorable):

```text
actorRule:
  values:
    1. type: User, values: ["<ALICE_UUID>"], operator: None    # allow all Users except Alice
```

"Only admins" is already positive — emit `operator: Or` with the admin user UUIDs (or a `Group` UUID for the Admins group). Identity tag filters are not supported on `actorRule`; if the user wants tag-style narrowing, enumerate the matching users / groups directly. See [../tags/planning.md — Deny-to-Allow flip](../tags/planning.md#deny-to-allow-flip) for the general flip pattern (which still applies to Resource and Actor Process tag filters).

## When NOT to emit `actorRule`

- The user said nothing about identity. Omit the block — do not default to `["*"]` on `User`, because that would still evaluate the block. Absence is semantically "no identity constraint".
- The user's intent is actually a **tag on the executable** ("only admin-launched Agents" — emit `executableRule.tags` instead; see [../executable/planning.md](../executable/planning.md)).
- The user asked for an **identity tag filter** ("any user tagged Admin"). Tags are not supported on `actorRule` today — refuse and offer to enumerate the matching users / groups, or drop the tag filter.
- The user is asking for per-user access on a **non-ToolUsePolicy** policy type. This skill only mutates `ToolUsePolicy`; stop and tell them.

## Relationship with Actor Process (executable) and Selection (selectors)

Identity gates the **trigger**. The executable rule gates the **caller workflow**. The selector gates the **target resource**. These compose as AND — every rule present must pass for the evaluation to return Allow. See [planning-arch.md § The three rule blocks](../../planning-arch.md#the-three-rule-blocks-boundary-table) for the boundary table.

## Anti-patterns

- Do NOT emit `actorRule` when the user did not mention identity. An empty-but-present `actorRule` can still filter out actors that don't satisfy `["*"]` semantics.
- Do NOT put resource or executable types (`RPAWorkflow`, `APIWorkflow`, `Agent`, `AgenticProcess`, `CaseManagement`, `Flow`) in `actorRule.values[].type` — this block is for **identity** types only. See [planning-arch.md § The three rule blocks](../../planning-arch.md#the-three-rule-blocks-boundary-table) for the boundary.
- Do NOT emit `type: "Robot"` or `type: "ExternalApplication"`. Robot intent resolves to `User`; ExternalApplication is not supported.
- Do NOT use `operator: And` on `values` — only `Or` / `None`.
- Do NOT emit duplicate entries of the same type (Critical Rule #16). Two `User` entries or two `Group` entries → merge into one entry with all UUIDs in its `values[]` array.
- Do NOT mix operators across `User` and `Group` entries (Critical Rule #16). When both entries are present, their `operator` must be the same value. Mixed intent ("allow these users, exclude that group") splits into two policies.
- Do NOT emit more than two entries in `actorRule.values[]`. The maximum is one `User` entry plus one `Group` entry.
- Do NOT invent identity types beyond `User | Group`.
- Do NOT emit `actorRule.tags`. The Actor Identity rule does not support tag filters today.

## Next: compose the JSON

When Phase 2 needs the concrete JSON for the `actorRule` block, read [actor/impl.md](./impl.md).
