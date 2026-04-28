# Selector Plugin — Planning

> **User-facing terminology vs JSON field.** The user-facing name for this block is **Selection Rule** (the Resource being protected). The underlying JSON field is `selectors[]` — that name is only shown in code / CLI contexts.

The `selectors[]` block identifies the **Resource** the access policy is about — what is being used by the Actor Process. One entry per distinct resource type the user mentioned.

## When to Use

Always. Every access policy this skill authors has at least one selector entry.

- One selector entry → one resource type.
- User mentioned multiple resource types ("Agents and Flows") → emit multiple entries, one per type. Do NOT merge types into a single entry.

## Block shape (conceptual)

```text
selectors[i] = {
    resourceType: <Agent | AgenticProcess | RPAWorkflow | APIWorkflow | CaseManagement | Flow>,
    values: [...],                                                # required — UUIDs or ["*"]
    operator: <Or | None>,
    tags: { values: [...], operator: <Or | And | None> }          # optional — per-entry
}
```

## Intent → resource type

Map the user's phrasing to the enum. These are the only valid `resourceType` values.

| User phrase | User-facing label | JSON `resourceType` |
|-------------|-------------------|---------------------|
| "agent", "AI agent" | Agent | `Agent` |
| "maestro", "maestro process", "agentic process" | **Maestro** | `AgenticProcess` |
| "RPA workflow", "RPA", "robot process" | **RPA** | `RPAWorkflow` |
| "API workflow", "API" | API Workflow | `APIWorkflow` |
| "case management", "case", "case work item" | Case Management | `CaseManagement` |
| "flow" | Flow | `Flow` |

> Always say **Maestro** and **RPA** in user-facing text; emit `AgenticProcess` and `RPAWorkflow` only inside JSON (Critical Rule #14).

If a phrase is ambiguous (e.g. "process" could be Maestro/`AgenticProcess` or RPA/`RPAWorkflow`), ask the user before picking.

## Targeting modes

Each selector entry picks one of two targeting modes. This is always expressed via the `values` field.

| Mode | `values` | `operator` | When to use |
|------|----------|------------|-------------|
| **All of this type** | `["*"]` | `Or` | User said "all agents", "any flow", or didn't name specific resources. Tag filter then narrows the set. |
| **Specific IDs** | `["<UUID1>", "<UUID2>", ...]` | `Or` | User named specific resources by UUID. |
| **Exclude specific IDs** | `["<UUID>", ...]` | `None` | Rare — user said "all agents except X". Usually easier to re-express via tag `None`. |

`values: ["*"]` is **required** even when you are using `tags` to narrow the scope. It is NOT optional. Missing `values` returns `400 Bad Request` (Critical Rule #5).

If the user mentions specific resources by **name** (e.g. "the Invoice Agent"), you need UUIDs. Resolve via [resource-lookup-guide.md](../../resource-lookup-guide.md) using the **two-step flow**:

1. **Discover the folder first** — `uip or processes list` requires `--folder-path` (or `--folder-key`). If the user did not say which folder, run `uip or folders list --output json`, show the folders, and ask the user to pick.
2. **Translate the resource type** — the Orchestrator `--process-type` value is **not** the same string as the access-policy `resourceType`. Use the mapping table in [resource-lookup-guide.md § Access-policy type → Orchestrator `--process-type`](../../resource-lookup-guide.md#access-policy-type--orchestrator---process-type) — notably `AgenticProcess`→`ProcessOrchestration`, `RPAWorkflow`→`Process`, `APIWorkflow`→`Api`.
3. **Search** — `uip or processes list --folder-path "<PATH>" --process-type "<ORCHESTRATOR_TYPE>" --name "<SUBSTR>" --output json`. Present the matching rows as a numbered picker. Use the returned `Key` field as the UUID.

Only surface an Open question in the Phase 1 Spec when the lookup still returns no match after broadening the search.

## Tag filter

Any tag phrase the user used ("Production Agent", "tagged Staging", "not Development") becomes a `tags` sub-object nested inside the selector entry. Tag composition is handled by the [tags plugin](../tags/planning.md).

The `tags` filter applies at the **per-entry level** (inside `selectors[N].tags`) — each `selectors[]` entry has its own independent tag filter. There is no top-level `selectors.tags` shared across entries. Two resource types with different tag filters → two `selectors[]` entries.

Omit `tags` entirely if the user did not mention any tags. Do NOT add empty `tags: { values: [], operator: "Or" }` objects.

## Multi-type selectors

If the policy targets multiple resource types, emit one `selectors[]` entry per type:

In the Spec Components Table (see [planning-arch.md — Spec output format](../../planning-arch.md#spec-output-format)), render multi-type targeting as one Resource row group per type, with user-friendly phrasing:

```text
  Resource filters (which resource processes this policy protects):
    1. Resource type: Agent
       Applies to:   all Agent resources
       Tag filter:   Any-of ["Production"]
    2. Resource type: Flow
       Applies to:   all Flow resources
       Tag filter:   Any-of ["Production"]
```

Each entry's `tags` is independent — a Production Agent selector does NOT imply a Production Flow selector.

## Anti-patterns

- Do NOT omit `values` — it is required even when `tags` narrow the scope.
- Do NOT put callers or identities here — this block is for Resources only. See [planning-arch.md § The three rule blocks](../../planning-arch.md#the-three-rule-blocks-boundary-table) for the boundary.
- Do NOT merge distinct resource types into one entry — one entry per `resourceType`.
- Do NOT use `operator: And` on `values` — only `Or` (include) and `None` (exclude) are supported at the values level.
- Do NOT put resource UUIDs in `tags.values`. Tag names and resource IDs live in different arrays — UUIDs go in the selector's own `values`, tag names go in `tags.values`.

## Next: compose the JSON

When Phase 2 needs the concrete JSON for a selector entry, read [selector/impl.md](./impl.md).
