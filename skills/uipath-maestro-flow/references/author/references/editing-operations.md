# Flow Editing Operations

Strategy selection and shared concepts for modifying `.flow` files. Direct `.flow` authoring is required for non-carve-out structural edits; CLI is reserved for the documented product-managed configuration carve-outs.

## Tool Selection Ladder

> **Pick the lowest-numbered tool that fits the operation.** If no rung fits, stop and ask the user via `AskUserQuestion`. Scripting languages (`python`, `node`, `jq`, `sed`, `awk`, shell heredocs) are a last resort and require explicit user approval — see rung 4.
>
> 1. **CLI-managed carve-outs only** → use the relevant plugin workflow for connector activity, connector-trigger, or managed HTTP operations when the CLI populates product-managed state (`inputs.detail`, `bindings_v2.json`, connection resources).
> 2. **Any structural `.flow` mutation** (add/delete OOTB nodes, add/delete edges, add/edit variables, in-place value tweaks, output mapping, subflows, scheduled triggers, non-connector resources, inline-agent node/wiring) → `Edit`.
> 3. **Wholesale file rewrite** (only when ≥70% of nodes change, e.g., scaffolding from a template) → `Write`.
> 4. **Anything else** → STOP and ask the user via `AskUserQuestion`. A scripting language is a last resort: surface the trade-offs (state bypass, opaque diff, no interruption point) and present finite options — typically **Use `Edit` instead** / **Use `Write` (full rewrite)** / **Approve the script for this change** / **Cancel** / **Something else**. Only proceed after the user explicitly approves that path for this specific change. See the AskUserQuestion dropdown rule in [SKILL.md](../../../SKILL.md).

### Why not Python / Node / jq / sed?

- The CLI auto-manages cross-cutting state (`definitions[]`, `variables.nodes`, edge references, layout). A scripting mutation bypasses that and forces hand-rolling it — extra surface for mistakes.
- `Edit` shows a line-by-line diff in the transcript; a script is an opaque payload. The user reviews tool calls, not script bodies.
- `Edit` calls are atomic per-call. A coordinated multi-section change is *not* one transaction — it's a sequence of `Edit` calls the user can interrupt between. Treating it as a single Python script removes that interruption point.

If the change feels too tangled for a sequence of `Edit` calls, use `Write` for the whole file or stop and ask the user via `AskUserQuestion` (see rung 4 above) — see the `Edit`/`Write` recipes in [editing-operations-json.md](editing-operations-json.md) and the SKILL.md rule on forbidden tools.

## Required Strategy

> **Use Edit / Write for all non-carve-out `.flow` edits.** Flow CLI is not an opt-in alternative for OOTB structural edits. Use CLI only for connector activity, connector-trigger, and managed HTTP carve-outs. Inline-agent project lifecycle commands (`uip agent init --inline-in-flow`, `uip agent refresh --inline-in-flow`, `uip agent validate --inline-in-flow`) are allowed for the agent project, but the `uipath.agent.autonomous` flow node and edges are authored directly in `.flow` JSON.

| Strategy | Guide | When to use |
|----------|-------|-------------|
| **Edit / Write** (required outside carve-outs) | [editing-operations-json.md](editing-operations-json.md) | Node/edge CRUD, variables, subflows, output mapping, in-place input updates, scheduled triggers, non-connector resources, inline-agent flow node/wiring. |
| **CLI** (carve-outs only) | [editing-operations-cli.md](editing-operations-cli.md) | Connector activity, connector-trigger, and managed HTTP workflows documented by their plugins. |

---

## Strategy Selection Matrix

Use this table to determine which strategy to follow for each operation. **Edit / Write is required outside the carve-out rows.**

| Operation | Default | Alternative | Notes |
|-----------|---------|-------------|-------|
| Add a node | **Edit / Write** | — | Flow CLI is not an option for non-carve-out node CRUD. |
| Add a managed HTTP node | **Edit / Write** for the node, then CLI `node configure` | — | Add the `core.action.http.v2` node directly; use the CLI carve-out only for `inputs.detail` configuration. |
| Add a HITL QuickForm node | **Edit / Write** | — | Wire `completed` port after adding. See [hitl/impl.md](plugins/hitl/impl.md). |
| Delete a node | **Edit / Write** | — | |
| Add an edge | **Edit / Write** | — | Remember `targetPort` (Rule #6). |
| Delete an edge | **Edit / Write** | — | |
| Update node inputs | **Edit** | — | In-place edit; preserves node ID and `$vars`. |
| Add/edit workflow variable | **Edit** | — | Edit-only; CLI does not support. |
| Add variable update | **Edit** | — | Edit-only; CLI does not support. |
| Map outputs on End node | **Edit** | — | Edit-only. |
| Create a subflow | **Edit / Write** | — | Edit-only (or `Write` for fresh template). |
| Replace trigger (non-connector) | **Edit** | — | |
| Replace mock with real resource (non-connector) | **Edit** | — | |
| Insert node between two existing nodes | **Edit** | — | |
| Insert a decision branch | **Edit** | — | |
| Remove a node and reconnect | **Edit** | — | |
| **Configure a connector node** | **CLI** (carve-out) | Edit (fallback) | `uip maestro flow node configure --detail` auto-populates `inputs.detail` + `bindings_v2.json`. |
| **Configure a connector trigger** | **CLI** (carve-out) | Edit (fallback) | Same as above. |
| **Configure a managed HTTP node** | **CLI** (carve-out) | Edit (fallback) | Same as above for managed HTTP `inputs.detail` and connection resources. |
| Add an inline agent node | **Edit / Write** | — | Scaffold the inline agent project with `uip agent init --inline-in-flow`, then add the `uipath.agent.autonomous` node and edges directly. |

### Mixing strategies

Mixing is still common: use direct `.flow` edits for structural changes, then use the CLI only for the carve-out operation documented in the relevant plugin `impl.md` (for example, configuring a managed HTTP or connector node after the node exists). For everything else, use `Edit` (or `Write` for wholesale rewrites).

---

## Shared Rules

These apply regardless of which strategy you use.

### Definitions

- Every unique `type:typeVersion` pair in `nodes` must have a matching entry in `definitions`
- Definitions come from `uip maestro flow registry get <node-type> --output json` — copy the returned node definition object (`Data.Node` or the top-level node object, depending on CLI/plugin version)
- **Never hand-write definitions** — hand-written definitions cause validation failures
- One definition per unique type, not one per node instance

### Layout

- Layout (`layout.nodes`, `subflows[<id>].layout`) is owned by `uip maestro flow format` — do not hand-compute coordinates
- When authoring a node, any placeholder `position` is fine (e.g. `{ x: 0, y: 0 }`); format rewrites it on save
- Run `uip maestro flow format <file>.flow` after edits and before publish/debug — see [cli-commands.md](../../shared/cli-commands.md#uip-maestro-flow-format)

### Edge rules

- `targetPort` is required on every edge — validate rejects edges without it
- See [file-format.md — Standard ports](../../shared/file-format.md) for port names by node type
- Dynamic ports: decision (`true`/`false`), switch (`case-{id}`/`default`), HTTP (`branch-{id}`/`default`), loop (`output`/`success`/`loopBack`)

### Validation

- Run `uip maestro flow validate <ProjectName>.flow --output json` **once** after all edits complete
- Do not validate after each individual edit — intermediate states are expected to be invalid
- Validation checks: JSON schema, definitions coverage, edge references, unique IDs
- Validation does NOT check: connector configuration, connection health, expression correctness, required field completeness

### Parallel same-file Edits

Applies to any turn that issues more than one `Edit` against the same `.flow` (greenfield T2 and brownfield alike):

- **Same-file Edits serialize in execution order** — they do not race, but each later Edit runs against the text the earlier ones already changed. An `old_string` that overlaps text a prior Edit removed or shifted fails with "string not found."
- **Anchor each Edit on its target array's OWN opening key** (`"nodes": [`, `"edges": [`, `"definitions": [`, or `layout.nodes`), located in the text you just `Read` — never on "the key that follows X." Top-level key order and presence are not guaranteed (see [file-format.md](../../shared/file-format.md#top-level-structure)).
- **`"nodes": [` and `"edges": [` are NOT unique** — they recur inside inline `definitions[]` and inside any `subflows.<id>` block. Anchor on the 2-space-indented (top-level) occurrence and extend until the match is unique.
- Insert at the array's head (right after `[`) so the `old_string` never spans the array's closing `]`.

Full per-array anchor table and worked example: [greenfield.md — Anchoring parallel `.flow` Edits](greenfield.md#anchoring-parallel-flow-edits--anchor-on-what-you-read-not-on-key-order).

### Expression prefix rules

- Use `=js:` on **value expressions**: end node output `source`, variable updates, HTTP input fields, node `inputs` values
- Do NOT use `=js:` on **condition expressions**: decision `expression`, switch case `expression`, HTTP branch `conditionExpression` — these are always evaluated as JS automatically

See [variables-and-expressions.md](../../shared/variables-and-expressions.md) for the full expression reference.

---

## Quick Reference — Operation to Guide

| I need to... | Go to |
|---|---|
| Add/delete nodes or edges | [Edit/Write guide](editing-operations-json.md) |
| Change a node's inputs | [Edit/Write guide — Update node inputs](editing-operations-json.md#update-node-inputs) |
| Configure a connector node | [CLI guide — Configure a connector node](editing-operations-cli.md#configure-a-connector-node) (carve-out) or [Edit/Write guide — Connector Node Configuration](editing-operations-json.md#connector-node-configuration-edit--write-fallback) (fallback) |
| Manage variables | [Edit/Write guide — Variable Operations](editing-operations-json.md#variable-operations) |
| Map outputs on End nodes | [Edit/Write guide — Add output mapping](editing-operations-json.md#add-output-mapping-on-an-end-node) |
| Create a subflow | [Edit/Write guide — Create a subflow](editing-operations-json.md#create-a-subflow) |
| Replace a mock placeholder (non-connector) | [Edit/Write guide — Replace a mock](editing-operations-json.md#replace-a-mock-with-a-real-resource-node) |
| Replace a trigger type (non-connector) | [Edit/Write guide — Replace trigger](editing-operations-json.md#replace-manual-trigger-with-scheduled-trigger) |
| Replace a trigger type (connector trigger) | [CLI guide — Replace trigger](editing-operations-cli.md#replace-manual-trigger-with-connector-trigger) (carve-out) |
| Understand the `.flow` JSON schema | [file-format.md](../../shared/file-format.md) |
| Look up CLI flags and syntax | [cli-commands.md](../../shared/cli-commands.md) |
| Work with variables and expressions | [variables-and-expressions.md](../../shared/variables-and-expressions.md) |
