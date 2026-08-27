# Flow Editing Operations

Strategy selection and shared concepts for modifying `.flow` files. Author non-carve-out structural changes directly in `.flow`; reserve CLI for documented product-managed configuration carve-outs.

## Tool Selection and Required Strategy

Pick the lowest-numbered tool that fits. If none fits, stop and ask the user. Scripting languages (`python`, `node`, `jq`, `sed`, `awk`, shell heredocs) are a last resort and require explicit user approval; see rung 4.

1. **CLI-managed carve-outs only:** use the relevant plugin workflow for connector activity, connector-trigger, or managed HTTP operations when the CLI populates product-managed state (`inputs.detail`, `bindings_v2.json`, connection resources).
2. **Structural `.flow` mutations:** use `Edit` for all OOTB node CRUD, edges, variables, in-place values, output mapping, subflows, scheduled triggers, non-connector resources, and inline-agent nodes/wiring.
3. **Wholesale rewrite:** use `Write` only when ≥70% of nodes change, such as scaffolding from a template. Never use it on a flow containing CLI-owned nodes (connector, connector-trigger, managed HTTP): it clobbers their CLI-owned `bindings[]` / `inputs.detail`, which `flow validate` will not catch. Use `Edit` (rung 2). If using `Write`, run `node configure` **as the last write** to touch `inputs.detail` / `bindings[]`; a later `Write` re-clobbers it. See [CAPABILITY.md — Node ownership](../CAPABILITY.md#node-ownership--who-authors-the-node).
4. **Anything else:** stop and ask the user. Before any scripting language, surface the trade-offs (state bypass, opaque diff, no interruption point) and offer exactly: **Use `Edit` instead** / **Use `Write` (full rewrite)** / **Approve the script for this change** / **Cancel** / **Something else**. Proceed only after explicit approval for this specific change. See the dropdown question rule in [SKILL.md](../../../SKILL.md).

CLI auto-manages cross-cutting state (`definitions[]`, `variables.nodes`, edge references, layout); scripting bypasses that and requires hand-rolling it. `Edit` provides a line-by-line diff and is atomic per call; sequential calls remain interruptible, unlike one script. If a change is too tangled for sequential `Edit` calls, use `Write` for the whole file or stop and ask the user. See [editing-operations-json.md](editing-operations-json.md) and the SKILL.md rule on forbidden tools.

Use Edit / Write for all non-carve-out `.flow` edits. Flow CLI is not an opt-in alternative for OOTB structural edits. Use CLI only for connector activity, connector-trigger, and managed HTTP carve-outs. Inline-agent project lifecycle commands (`uip agent init --inline-in-flow`, `uip agent refresh --inline-in-flow`, `uip agent validate --inline-in-flow`) are allowed for the agent project, but author the `uipath.agent.autonomous` flow node and edges directly in `.flow` JSON.

| Strategy | Guide | When to use |
|---|---|---|
| **Edit / Write** (required outside carve-outs) | [editing-operations-json.md](editing-operations-json.md) | Node/edge CRUD, variables, subflows, output mapping, in-place input updates, scheduled triggers, non-connector resources, inline-agent flow node/wiring. |
| **CLI** (carve-outs only) | [editing-operations-cli.md](editing-operations-cli.md) | Connector activity, connector-trigger, and managed HTTP workflows documented by their plugins. |

## Operation Matrix

**Edit / Write is required outside the carve-out rows.**

| Operation | Default | Notes |
|---|---|---|
| Add a node | **Edit / Write** | Includes HITL QuickForm; wire `completed` after adding. |
| Add a managed HTTP node | **CLI** (carve-out) `node add`, then CLI `node configure` | Run `uip maestro flow node add <file>.flow core.action.http.v2 ...`; do not hand-author `definitions[]`. See [http/impl.md — Step 1](plugins/http/impl.md#add-the-node). |
| Delete a node; add/delete an edge; update non-carve-out inputs; add/edit a workflow variable; add a variable update; map End-node outputs | **Edit** | In-place input edits preserve node ID and `$vars`; variable updates are Edit-only. Every edge needs `targetPort` (Rule #6). |
| Create a subflow | **Edit / Write** | Edit-only, or `Write` for a fresh template. |
| Replace a non-connector trigger; replace a non-connector mock; insert a node; insert a decision branch; remove a node and reconnect | **Edit** | — |
| Configure a connector node or connector trigger | **CLI** (carve-out) | Run `uip maestro flow node configure --detail`; it auto-populates `inputs.detail` + `bindings_v2.json`. Hand-authored `inputs.detail` skips `essentialConfiguration` and fails at runtime — no Edit fallback. |
| Configure a managed HTTP node | **CLI** (carve-out) | Use the documented managed HTTP workflow for `inputs.detail` and connection resources. |
| Add an inline agent node | **Edit / Write** | Scaffold with `uip agent init --inline-in-flow`, then add the `uipath.agent.autonomous` node and edges directly. |

For managed HTTP `inputs.branches` / `timeout` / `retryCount`, set them at `node add --input` time; change them by `uip maestro flow node remove` and re-add with new `--input`. Variable declaration CLI commands `uip maestro flow variable add\|list\|remove` exist for eval inputs; see [variables-and-expressions.md § Variable Management via CLI](../../shared/variables-and-expressions.md#variable-management-via-cli).

For structural changes followed by a carve-out, edit the `.flow` first, then run only the relevant plugin `impl.md` workflow, such as configuring a managed HTTP or connector node. Otherwise use `Edit`, or `Write` for a wholesale rewrite.

## Shared Rules

### Definitions

- Ensure every unique `type:typeVersion` pair in `nodes` has a matching `definitions` entry.
- Run `uip maestro flow registry get <node-type> --output json` and copy the returned node definition object (`Data.Node` or the top-level node object, depending on CLI/plugin version).
- Never hand-write definitions; use one definition per unique type, not per node instance.

### Layout

- Treat `layout.nodes` and `subflows[<id>].layout` as owned by `uip maestro flow format`; do not hand-compute coordinates.
- Placeholder `position` values such as `{ x: 0, y: 0 }` are acceptable while authoring.
- Run `uip maestro flow format <file>.flow` after edits and before publish/debug; see [cli-commands.md](../../shared/cli-commands.md#uip-maestro-flow-format).

### Edges

- Give every edge a `targetPort`; validation rejects edges without it.
- See [file-format.md — Standard ports](../../shared/file-format.md) for port names.
- Use these dynamic ports: decision (`true`/`false), switch (`case-{id}`/`default`), HTTP (`branch-{id}`/`default`), loop (`start`/`continue`/`break` inner, `success`/`error` outer).

### Validation

- Run `uip maestro flow validate <ProjectName>.flow --output json` **once** after all edits complete.
- Do not validate after each individual edit; intermediate states may be invalid.
- Validation checks JSON schema, definitions coverage, edge references, and unique IDs, but does **not** check connector configuration, connection health, expression correctness, or required-field completeness.

### Parallel Same-File Edits

For any turn issuing more than one `Edit` against the same `.flow` (greenfield T2 or brownfield):

- Serialize same-file Edits in execution order. Each later Edit runs against the prior text; an `old_string` overlapping removed or shifted text fails with "string not found."
- Anchor each Edit on its target array's OWN opening key (`"nodes": [`, `"edges": [`, `"definitions": [`, or `layout.nodes`), located in the text just read. Never anchor on "the key that follows X"; top-level key order and presence are not guaranteed (see [file-format.md](../../shared/file-format.md#top-level-structure)).
- Because `"nodes": [` and `"edges": [` recur inside inline `definitions[]` and `subflows.<id>`, use the 2-space-indented top-level occurrence and extend until the match is unique.
- Insert at the array head, immediately after `[`, so `old_string` never spans the closing `]`.

See the full anchor table and example: [greenfield.md — Anchoring parallel `.flow` Edits](greenfield.md#anchoring-parallel-flow-edits--anchor-on-what-you-read-not-on-key-order).

### Expression Prefixes

- Use `=js:` on value expressions: End output `source`, variable updates, HTTP input fields, and node `inputs` values.
- Do **not** use `=js:` on condition expressions: decision `expression`, switch case `expression`, and HTTP branch `conditionExpression`; evaluate these as JS automatically.

See [variables-and-expressions.md](../../shared/variables-and-expressions.md).

## Quick Reference

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