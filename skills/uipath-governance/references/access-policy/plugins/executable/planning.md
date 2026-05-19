# Actor Process Plugin — Planning

> **User-facing terminology vs JSON field.** The user-facing name for this block is **Actor Process rule**. The underlying JSON field is `executableRule` — that name is only shown in code / CLI contexts. When summarizing the policy to the user, always say "Actor Process rule", never "Executable rule".

The `executableRule` block identifies the **caller** — the Actor Process that uses the resource. The access policy has exactly one `executableRule` block, but that block can contain multiple per-type entries.

## When to Use

Always. Every access policy this skill authors has exactly one `executableRule`.

## Block shape (conceptual)

```text
executableRule = {
    values: [
        { type: <Agent | AgenticProcess | CaseManagement | Flow>, values: [...], operator: <Or | None> },
        ...                                                       # one entry per executable type
    ],
    tags: { values: [...], operator: <Or | And | None> }          # optional, applies to all entries
}
```

- `executableRule.values[]` — one entry per executable **type** the user mentioned.
- `executableRule.tags` — optional. When present, narrows the set for every entry in `values[]`.

## Intent → executable type

Map the user's phrasing to the enum. These are the only valid executable `type` values.

| User phrase | User-facing label | JSON `type` |
|-------------|-------------------|-------------|
| "agent", "AI agent" | Agent | `Agent` |
| "maestro", "maestro process", "agentic process" | **Maestro** | `AgenticProcess` |
| "case management", "case" | Case Management | `CaseManagement` |
| "flow" | Flow | `Flow` |

> Always say **Maestro** in user-facing text (Spec narrative, summaries, review gate); emit `AgenticProcess` only inside JSON code blocks (Critical Rule #14).

> **Not valid here:** `RPAWorkflow` and `APIWorkflow` are resource-only types. They live in `selectors[]` (see [selector/planning.md](../selector/planning.md)); they cannot appear in `executableRule.values[].type`.

## Targeting modes

Same two modes as selectors, plus a third pattern that operates on the entry's `type` rather than its `values`:

| Mode | Entry shape | When to use |
|------|-------------|-------------|
| **All of this type** | `{ type: <T>, values: ["*"], operator: "Or" }` | "Any `<T>` caller". |
| **Specific IDs** | `{ type: <T>, values: ["<UUID>", ...], operator: "Or" }` | "These specific `<T>` callers". |
| **Exclude specific IDs** | `{ type: <T>, values: ["<UUID>", ...], operator: "None" }` | "Any `<T>` caller except these UUIDs". |
| **Exclude a whole type** | `{ type: <T>, values: ["*"], operator: "None" }` — and **omit every other type** from `values[]` | "Any caller type except `<T>`". Caller types not listed in `values[]` are NoOp on this filter (the policy does not constrain them). See [Excluding a caller type](#excluding-a-caller-type). |

`values: ["*"]` is required on every entry (Critical Rule #5). Missing it returns `400`.

### Resolving Actor Process names to UUIDs

If the user named a specific caller ("the Maestro Production process"), resolve the name to a UUID via [resource-lookup-guide.md](../../resource-lookup-guide.md) using the **two-step flow**:

1. **Discover the folder first** — `uip or processes list` requires `--folder-path`. If the user did not say which folder, run `uip or folders list --output json` and ask the user to pick before searching.
2. **Translate the Actor Process type** — Orchestrator's `--process-type` is **not** the same string as the access-policy `type`. For Actor Process values, map: `Agent`→`Agent`, `AgenticProcess`→`ProcessOrchestration`, `Flow`→`Flow`, `CaseManagement`→`CaseManagement`. See the full table in [resource-lookup-guide.md § Access-policy type → Orchestrator `--process-type`](../../resource-lookup-guide.md#access-policy-type--orchestrator---process-type).
3. **Search** — `uip or processes list --folder-path "<PATH>" --process-type "<ORCHESTRATOR_TYPE>" --name "<SUBSTR>" --output json`. Present the matching rows as a numbered picker. Use the returned `Key` field as the UUID.

Never ask the user to leave the chat to find a UUID — run the lookup first. Only surface an open question when the lookup returns no match after broadening the search.

## Multi-type executable rules

If the user says "allow Agents **and** Maestros to use…", emit two entries (one per JSON `type`):

```text
executableRule:
  values:
    1. type: Agent,           values: ["*"], operator: Or
    2. type: AgenticProcess,  values: ["*"], operator: Or
  tags: { values: ["Production"], operator: Or }    # applied to both entries
```

The shared `executableRule.tags` applies uniformly across every entry — there is **no per-entry `tags`** inside `executableRule.values[]`. If different executable types need different tag rules, the policy is probably really two policies; flag this during Phase 1 and ask the user.

## Excluding a caller type

When the user says "any caller **except** `<type>`" — e.g. "block Agent callers, allow everything else" — emit ONE entry of the **excluded** type with `operator: "None"` and `values: ["*"]`, and OMIT every other type from `values[]`. Do NOT enumerate the allowed types.

```text
# Intent: "any caller except Agent"
executableRule:
  values:
    1. type: Agent, values: ["*"], operator: None
```

**Why this works.** Caller types not listed in `executableRule.values[]` are NoOp on this filter — the policy does not constrain them. The single `None`-on-`Agent` entry says "this policy applies when the caller's type is NOT `Agent`". Combined with `enforcement: "Allow"`, the policy contributes Allow for every non-`Agent` caller.

**Why NOT enumerate.** Listing `AgenticProcess`, `CaseManagement`, `Flow` with `Or` produces the same runtime effect but:
- It is verbose and obscures the user's "all except X" intent.
- It rots when new caller types are added to the platform.
- It tempts authors to "just add another type with `Or`" instead of reasoning about exclusion.

The canonical shape is the single-entry `None`-on-excluded-type form. See [executable/impl.md — Example E](./impl.md#e-all-caller-types-except-a-specific-type-canonical-idiom).

> **"Exclude UUIDs" vs "exclude a type" vs "exclude a tag"** are three different operators that all happen to use `None`:
> - **Exclude UUIDs** — `{ type: <T>, values: ["<UUID1>", ...], operator: "None" }` matches any `<T>` caller whose UUID is NOT in the list.
> - **Exclude a type** — `{ type: <T>, values: ["*"], operator: "None" }` matches any caller whose type is NOT `<T>` (this section).
> - **Exclude a tag** — `tags: { values: ["<TAG>"], operator: "None" }` (top-level on `executableRule`) matches callers that do NOT carry the tag. See [tags/planning.md — Deny-to-Allow flip](../tags/planning.md#deny-to-allow-flip).

## Top-level `tags` vs per-entry `values`

- `executableRule.tags` — applies once, to all entries in `values[]`. The only place tag filters live in this block.
- Per-entry `values` — targets individual executables by UUID.

## Deny-flipped intent

"Deny flows from using Production Agents" flips to: Allow all flows to use Agents **except** Production-tagged ones. The flip lives on the **selector**'s tags (`operator: None` on `Production`), not on the executable. See [tags/planning.md — Deny-to-Allow flip](../tags/planning.md#deny-to-allow-flip) for the decision procedure.

## Anti-patterns

- Do NOT put `RPAWorkflow` or `APIWorkflow` in `executableRule.values[].type` — those are resource-only.
- Do NOT omit `values` — it is required per entry.
- Do NOT confuse the Actor Process rule (`executableRule`, the calling workflow) with the Actor Identity rule (`actorRule`, the user/group triggering it). See [planning-arch.md § The three rule blocks](../../planning-arch.md#the-three-rule-blocks-boundary-table) for the boundary.
- Do NOT merge distinct `type` values into one entry — one entry per type.
- Do NOT use `operator: And` on `values` — only `Or` / `None`.

## Next: compose the JSON

When Phase 2 needs the concrete JSON for the `executableRule` block, read [executable/impl.md](./impl.md).
