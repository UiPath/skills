# Flow Editing Operations

Strategy selection and shared concepts for modifying `.flow` files. Two implementation strategies are available — choose one per operation and follow the corresponding guide.

## Tool Selection Ladder

> **Pick the lowest-numbered tool that fits the operation and is allowed by default.** Rung 4 (CLI for OOTB add/delete) is opt-in only — skip past it unless the user has explicitly requested CLI. If no rung fits, stop and ask the user via `AskUserQuestion`. Scripting languages (`python`, `node`, `jq`, `sed`, `awk`, shell heredocs) are a last resort and require explicit user approval — see rung 5.
>
> 1. **Connector / connector-trigger / inline-agent node** → `uip maestro flow node configure` (carve-out — auto-populates `inputs.detail` + `bindings_v2.json`).
> 2. **Any other `.flow` mutation** (add/delete OOTB nodes, add/delete edges, add/edit variables, in-place value tweaks, output mapping, subflows) → `Edit`.
> 3. **Wholesale file rewrite** (only when ≥70% of nodes change, e.g., scaffolding from a template) → `Write`.
> 4. **CLI alternative for OOTB add/delete** (`uip maestro flow node {add,delete}` / `edge {add,delete}` / `variable add`) → opt-in only, when the user explicitly requests CLI. Same outcome as rung 2 but with an opaque diff.
> 5. **Anything else** → STOP and ask the user via `AskUserQuestion`. A scripting language is a last resort: surface the trade-offs (state bypass, opaque diff, no interruption point) and present finite options — typically **Use `Edit` instead** / **Use `Write` (full rewrite)** / **Approve the script for this change** / **Cancel** / **Something else**. Only proceed after the user explicitly approves that path for this specific change. See the AskUserQuestion dropdown rule in [SKILL.md](../../../SKILL.md).

### Why not Python / Node / jq / sed?

- The CLI auto-manages cross-cutting state (`definitions[]`, `variables.nodes`, edge references, layout). A scripting mutation bypasses that and forces hand-rolling it — extra surface for mistakes.
- `Edit` shows a line-by-line diff in the transcript; a script is an opaque payload. The user reviews tool calls, not script bodies.
- `Edit` calls are atomic per-call. A coordinated multi-section change is *not* one transaction — it's a sequence of `Edit` calls the user can interrupt between. Treating it as a single Python script removes that interruption point.

If the change feels too tangled for a sequence of `Edit` calls, use `Write` for the whole file or stop and ask the user via `AskUserQuestion` (see rung 5 above) — see the `Edit`/`Write` recipes in [editing-operations-json.md](editing-operations-json.md) and the SKILL.md rule on forbidden tools.

## Default Strategy

> **Default to Edit / Write for all `.flow` edits.** Use CLI only when the user explicitly requests CLI, or for connector, connector-trigger, or inline-agent nodes (see carve-out rows in the matrix below).

| Strategy | Guide | When to use |
|----------|-------|-------------|
| **Edit / Write** (default) | [editing-operations-json.md](editing-operations-json.md) | Default for all `.flow` edits — node/edge CRUD, variables, subflows, output mapping, in-place input updates. |
| **CLI** (opt-in / carve-outs) | [editing-operations-cli.md](editing-operations-cli.md) | Connector, connector-trigger, and inline-agent nodes (carve-outs); or when the user explicitly requests CLI. |

---

## Strategy Selection Matrix

Use this table to determine which strategy to follow for each operation. **Edit / Write is the default**; use CLI only for the carve-out rows or when the user explicitly opts in.

| Operation | Default | Alternative | Notes |
|-----------|---------|-------------|-------|
| Add a node | **Edit / Write** | CLI (opt-in) | CLI still auto-manages definitions/variables when opted in. |
| Add a HITL QuickForm node | **Edit / Write** | CLI (opt-in) via `uip maestro flow hitl add` | Dedicated command also handles definition + `variables.nodes`. Wire `completed` port after. See [hitl/impl.md](plugins/hitl/impl.md). |
| Delete a node | **Edit / Write** | CLI (opt-in) | |
| Add an edge | **Edit / Write** | CLI (opt-in) | Remember `targetPort` (Rule #6). |
| Delete an edge | **Edit / Write** | CLI (opt-in) | |
| Update node inputs | **Edit** | — | In-place edit; preserves node ID and `$vars`. |
| Add/edit workflow variable | **Edit** | — | Edit-only; CLI does not support. |
| Add variable update | **Edit** | — | Edit-only; CLI does not support. |
| Map outputs on End node | **Edit** | — | Edit-only. |
| Create a subflow | **Edit / Write** | — | Edit-only (or `Write` for fresh template). |
| Replace trigger (non-connector) | **Edit** | CLI (opt-in) | |
| Replace mock with real resource (non-connector) | **Edit** | CLI (opt-in) | |
| Insert node between two existing nodes | **Edit** | CLI (opt-in) | |
| Insert a decision branch | **Edit** | CLI (opt-in) | |
| Remove a node and reconnect | **Edit** | CLI (opt-in) | |
| **Configure a connector node** | **CLI** (carve-out) | Edit (fallback) | `uip maestro flow node configure --detail` auto-populates `inputs.detail` + `bindings_v2.json`. |
| **Configure a connector trigger** | **CLI** (carve-out) | Edit (fallback) | Same as above. |
| **Add an inline agent node** | **CLI** (carve-out) | — | Scaffolded via `uip agent init --inline-in-flow`. |

### Mixing strategies

The default strategy is Edit / Write. Mixing is still common: for connector, connector-trigger, or inline-agent nodes, use the CLI as documented in their respective plugin `impl.md`. For everything else, use `Edit` (or `Write` for wholesale rewrites) unless the user explicitly asks for CLI.

---

## Shared Rules

These apply regardless of which strategy you use.

### Definitions

- Every unique `type:typeVersion` pair in `nodes` must have a matching entry in `definitions`
- Definitions come from `uip maestro flow registry get <NODE_TYPE> --output json` — copy the `Data.Node` object
- **Never hand-write definitions** — hand-written definitions cause validation failures
- One definition per unique type, not one per node instance

### Layout

- Layout (`layout.nodes`, `subflows[<id>].layout`) is owned by `uip maestro flow tidy` — do not hand-compute coordinates
- When authoring a node, any placeholder `position` is fine (e.g. `{ x: 0, y: 0 }`); tidy rewrites it on save
- Run `uip maestro flow tidy <file>.flow` after edits and before publish/debug — see [cli-commands.md](../../shared/cli-commands.md#uip-maestro-flow-tidy)

### Edge rules

- `targetPort` is required on every edge — validate rejects edges without it
- See [file-format.md — Standard ports](../../shared/file-format.md) for port names by node type
- Dynamic ports: decision (`true`/`false`), switch (`case-{id}`/`default`), HTTP (`branch-{id}`/`default`), loop (`output`/`success`/`loopBack`)

### Validation

- Run `uip maestro flow validate <ProjectName>.flow --output json` **once** after all edits complete
- Do not validate after each individual edit — intermediate states are expected to be invalid
- Validation checks: JSON schema, definitions coverage, edge references, unique IDs
- Validation does NOT check: connector configuration, connection health, expression correctness, required field completeness

### Expression prefix rules

- Use `=js:` on **value expressions**: end node output `source`, variable updates, HTTP input fields, node `inputs` values
- Do NOT use `=js:` on **condition expressions**: decision `expression`, switch case `expression`, HTTP branch `conditionExpression` — these are always evaluated as JS automatically

See [variables-and-expressions.md](../../shared/variables-and-expressions.md) for the full expression reference.

---

## Quick Reference — Operation to Guide

| I need to... | Go to |
|---|---|
| Add/delete nodes or edges | [Edit/Write guide](editing-operations-json.md) (default) or [CLI guide](editing-operations-cli.md) (opt-in) |
| Change a node's inputs | [Edit/Write guide — Update node inputs](editing-operations-json.md#update-node-inputs) |
| Configure a connector node | [CLI guide — Configure a connector node](editing-operations-cli.md#configure-a-connector-node) (carve-out) or [Edit/Write guide — Connector Node Configuration](editing-operations-json.md#connector-node-configuration-edit--write-fallback) (fallback) |
| Manage variables | [Edit/Write guide — Variable Operations](editing-operations-json.md#variable-operations) |
| Map outputs on End nodes | [Edit/Write guide — Add output mapping](editing-operations-json.md#add-output-mapping-on-an-end-node) |
| Create a subflow | [Edit/Write guide — Create a subflow](editing-operations-json.md#create-a-subflow) |
| Replace a mock placeholder (non-connector) | [Edit/Write guide — Replace a mock](editing-operations-json.md#replace-a-mock-with-a-real-resource-node) (default) or [CLI guide — Replace a mock](editing-operations-cli.md#replace-a-mock-with-a-real-resource-node) (opt-in) |
| Replace a trigger type (non-connector) | [Edit/Write guide — Replace trigger](editing-operations-json.md#replace-manual-trigger-with-scheduled-trigger) (default) or [CLI guide — Replace trigger](editing-operations-cli.md#replace-manual-trigger-with-scheduled-trigger) (opt-in) |
| Replace a trigger type (connector trigger) | [CLI guide — Replace trigger](editing-operations-cli.md#replace-manual-trigger-with-connector-trigger) (carve-out) |
| Understand the `.flow` JSON schema | [file-format.md](../../shared/file-format.md) |
| Look up CLI flags and syntax | [cli-commands.md](../../shared/cli-commands.md) |
| Work with variables and expressions | [variables-and-expressions.md](../../shared/variables-and-expressions.md) |
