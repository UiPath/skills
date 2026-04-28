# Tags Plugin — Planning

> **User-facing terminology vs JSON field.** User-facing label: **tag filter**. JSON field: `tags` sub-object — shown only in code / CLI contexts.

The `tags` sub-object is the shared **Resource Catalog Tag** filter used inside selector entries and inside `executableRule`. It is the primary mechanism for scoping an access policy to a subset of resources / executables without listing individual UUIDs.

## When to Use

Add a `tags` sub-object to a `selectors[]` entry or to `executableRule` whenever the user mentions a tag-style attribute on the Resource or Actor Process side. Omit the entire `tags` key when no tag constraint applies. **Resource Catalog Tags** are labels assigned to resources in the UiPath Resource Catalog; the `tags` sub-object matches on those labels at evaluation time.

> `actorRule` does **not** support `tags` today — never emit `actorRule.tags`.

## Block shape (conceptual)

```text
tags = { values: ["<tag1>", "<tag2>", ...], operator: <Or | And | None> }
```

- `values` — list of tag names. Must be non-empty when the `tags` key is present. Omit the whole key when there are no tag constraints.
- `operator` — how `values` is applied. One of `Or` (Any-of), `And` (All-of), `None` (Exclude).

## Operator semantics

| Operator | Meaning | Example phrasing |
|----------|---------|------------------|
| `Or` | Match resources with **any** of the listed tags | "Production or Staging agents" |
| `And` | Match resources with **all** of the listed tags | "agents tagged both Production and Critical" |
| `None` | **Exclude** resources with any of the listed tags | "agents not tagged Development" |

Worked mental model:

- `{ values: ["Production", "Staging"], operator: "Or" }` → matches resources tagged Production **or** Staging.
- `{ values: ["Production", "Critical"], operator: "And" }` → matches resources tagged Production **and** Critical.
- `{ values: ["Development"], operator: "None" }` → matches resources **not** tagged Development.

## Common Resource Catalog tag names

The Resource Catalog tag set is tenant-specific, but these names recur across UiPath environments:

- **Environment:** `Production`, `Development`, `Staging`, `Test`
- **Criticality / data class:** `Critical`, `PII`, `Confidential`
- **Team / org:** `Finance`, `Marketing`, `HR`, `Platform`
- **Product / domain:** user-specific product names

> Tags the user mentions must actually exist in the Resource Catalog of the **policy's own tenant** (the active tenant from the safe auth-context workflow). A policy that references `DoesNotExist` silently matches nothing. **Confirm tag names during Phase 1** before approving the Spec by running `uip admin rcs tag list --output json` (no `--tenant` — the default targets the policy's tenant; see [resource-lookup-guide.md § 4](../../resource-lookup-guide.md#4-resource-catalog-tags)). If the tag is missing, surface it as an Open question and ask the user to either pick a returned tag or add the missing one to the Resource Catalog before the JSON is composed.

## Deny-to-Allow flip

> **Internal mechanic — not user-facing copy.** Do NOT surface "Deny-to-Allow flip", "None operator", or "enforcement: Deny is not authorable" jargon to the user. The Spec narrative describes the policy in plain English of **what's allowed** — the flip happens silently inside the agent.

Access policies of type `ToolUsePolicy` only support `enforcement: "Allow"` (Critical Rule #2) — `enforcement: "Deny"` is **not authorable**. Intent phrased as Deny must be reframed as an equivalent Allow rule. Two equivalent shapes; pick whichever produces the clearer Spec narrative:

- **Reframe scope.** Translate to "Allow only `<positive-set>`" and target it with `operator: "Or"`. Example: "Deny Development agents" → "Allow only Production / Staging agents" with `tags: { values: ["Production", "Staging"], operator: "Or" }`.
- **`None`-operator flip.** Keep "everything except X" framing and emit `operator: "None"` on the relevant `tags` or `values`. The rest of this section walks through the `None`-operator pattern.

### When to flip via tags

| User phrasing | Flipped intent | `tags` |
|---------------|----------------|--------|
| "Deny Development agents" | Allow agents **except** Development-tagged | `{ values: ["Development"], operator: "None" }` |
| "Block Staging resources" | Allow resources **except** Staging | `{ values: ["Staging"], operator: "None" }` |
| "Prevent PII-tagged data being used by flows" | Allow flows to use everything **except** PII-tagged | `{ values: ["PII"], operator: "None" }` on the selector |

### Decision procedure for Deny intent

1. Identify the negative predicate (the set the user wants to exclude).
2. Check whether the predicate is expressible as a tag (or set of tags) on the resource or executable.
3. If yes, emit the affirmative complement on the correct block:
   - Deny by **resource attribute** → `None` on the selector's `tags`.
   - Deny by **caller attribute** → `None` on the `executableRule`'s `tags`.
4. If the predicate is over UUIDs rather than tags, use `operator: "None"` on `values` instead (see [selector/planning.md](../selector/planning.md) and [executable/planning.md](../executable/planning.md)).
5. If no clean flip exists (e.g. "deny for user X" — that is an actor predicate and the access policy cannot express it as a tag filter), stop and consult [actor/planning.md](../actor/planning.md).

### Three worked flips

**A. Single tag.** "Deny Development agents" → selector `tags: { values: ["Development"], operator: "None" }`.

**B. Multiple tags.** "Block Development or Staging flows" → selector (`resourceType: Flow`) `tags: { values: ["Development", "Staging"], operator: "None" }`. The `None` operator on multiple values excludes resources tagged with **any** of them.

**C. Mixed tag + UUID exclusion.** "Block specific process `xyz-789` and everything tagged Development" — two parts. Flip the UUID exclusion onto `values` with `operator: "None"`, and flip the tag exclusion onto `tags` with `operator: "None"`. These go on the same selector entry. Note that this does not combine cleanly when the user also wants an include; split into two selectors or escalate to the user.

## Decision tree: picking the operator

```text
Is the user denying / excluding something?
├── yes → operator: None   (and go read the Deny-to-Allow flip section above)
└── no  → Is the user listing alternatives ("Production or Staging")?
           ├── yes → operator: Or
           └── no  → Is the user requiring all tags at once ("both X and Y")?
                      ├── yes → operator: And
                      └── no  → default to Or with a single tag, or omit tags entirely
```

## Where the block lives

The same `tags` shape appears in two blocks of the access policy:

| Block | Effect |
|-------|--------|
| `selectors[].tags` | Narrows the set of **resources** a selector matches (Selection Rule). |
| `executableRule.tags` | Narrows the set of **Actor Processes** (callers) — applies across all entries in `executableRule.values[]`. |

> **`actorRule` does NOT support tags today.** Identity-side tag filters are unsupported — emitting `actorRule.tags` returns `400 Bad Request`. Enumerate the matching users / groups directly under `actorRule.values[].values` instead. See [actor/planning.md](../actor/planning.md) and Critical Rule #5.

There is no per-entry `tags` inside `executableRule.values[]`. If different entry types need different tag filters, split into two policies.

## Anti-patterns

- Do NOT emit `enforcement: "Deny"` ever. The API does not support it (Critical Rule #2). Reframe the user's intent as Allow + scope filter, or use `operator: "None"` on `tags` / `values` to express "everything except X".
- Do NOT invent tag names. If the user hasn't confirmed a tag exists in the Resource Catalog, run `uip admin rcs tag list --output json` against the policy's tenant (the default — no `--tenant`) and ask the user to pick from the returned list.
- Do NOT pass an empty `values: []` array. Either include at least one tag, or omit the entire `tags` key.
- Do NOT use `operator: "And"` with a single tag — it's equivalent to `Or` with one tag; use `Or` for clarity.
- Do NOT confuse Resource Catalog Tags with executable `type` or with free-text descriptions. Only named labels assigned in the Resource Catalog qualify.

## Next: compose the JSON

When Phase 2 needs the concrete JSON for a `tags` block, read [tags/impl.md](./impl.md).
