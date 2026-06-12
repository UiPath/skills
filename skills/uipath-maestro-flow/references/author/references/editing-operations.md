# Flow Editing Operations

Strategy selection and shared concepts for modifying `.flow` files. Direct `.flow` authoring is required for non-carve-out structural edits; CLI is reserved for the documented product-managed configuration carve-outs.

## Tool Selection Ladder

> **Pick the lowest-numbered tool that fits the operation.** If no rung fits, stop and ask the user. Scripting languages (`python`, `node`, `jq`, `sed`, `awk`, shell heredocs) are a last resort and require explicit user approval — see rung 4.
>
> 1. **CLI-managed carve-outs only** → use the relevant plugin workflow for connector activity, connector-trigger, or managed HTTP operations when the CLI populates product-managed state (`inputs.detail`, `bindings_v2.json`, connection resources).
> 2. **Any structural `.flow` mutation** (add/delete OOTB nodes, add/delete edges, add/edit variables, in-place value tweaks, output mapping, subflows, scheduled triggers, non-connector resources, inline-agent node/wiring) → `Edit`.
> 3. **Wholesale file rewrite** (only when ≥70% of nodes change, e.g., scaffolding from a template) → `Write`.
> 4. **Anything else** → STOP and ask the user. A scripting language is a last resort: surface the trade-offs (state bypass, opaque diff, no interruption point) and present finite options — typically **Use `Edit` instead** / **Use `Write` (full rewrite)** / **Approve the script for this change** / **Cancel** / **Something else**. Only proceed after the user explicitly approves that path for this specific change. See the dropdown question rule in [SKILL.md](../../../SKILL.md).

### Why not Python / Node / jq / sed?

- The CLI auto-manages cross-cutting state (`definitions[]`, `variables.nodes`, edge references, layout). A scripting mutation bypasses that and forces hand-rolling it — extra surface for mistakes.
- `Edit` shows a line-by-line diff in the transcript; a script is an opaque payload. The user reviews tool calls, not script bodies.
- `Edit` calls are atomic per-call. A coordinated multi-section change is *not* one transaction — it's a sequence of `Edit` calls the user can interrupt between. Treating it as a single Python script removes that interruption point.

If the change feels too tangled for a sequence of `Edit` calls, use `Write` for the whole file or stop and ask the user (see rung 4 above) — see the `Edit`/`Write` recipes in [editing-operations-json.md](editing-operations-json.md) and the SKILL.md rule on forbidden tools.

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
| Add a managed HTTP node | **CLI** (carve-out) `node add`, then CLI `node configure` | — | Use `uip maestro flow node add <file> core.action.http.v2 ...` to add the node. Do not hand-author `definitions[]` for this node type. See [http/impl.md — Step 1](plugins/http/impl.md#add-the-node). |
| Add a HITL QuickForm node | **Edit / Write** | — | Wire `completed` port after adding. See [hitl/impl.md](plugins/hitl/impl.md). |
| Delete a node | **Edit / Write** | — | |
| Add an edge | **Edit / Write** | — | Remember `targetPort` (Rule #6). |
| Delete an edge | **Edit / Write** | — | |
| Update node inputs | **Edit** | — | In-place edit; preserves node ID and `$vars`. **Exception:** managed HTTP `inputs.branches` / `timeout` / `retryCount` must be set at `node add --input` time — to change them, `uip maestro flow node remove` and re-add with new `--input`. |
| Add/edit workflow variable | **Edit** | — | Edit-only; CLI does not support. |
| Add variable update | **Edit** | — | Edit-only; CLI does not support. |
| Map outputs on End node | **Edit** | — | Edit-only. |
| Create a subflow | **Edit / Write** | — | Edit-only (or `Write` for fresh template). |
| Replace trigger (non-connector) | **Edit** | — | |
| Replace mock with real resource (non-connector) | **Edit** | — | |
| Insert node between two existing nodes | **Edit** | — | |
| Insert a decision branch | **Edit** | — | |
| Remove a node and reconnect | **Edit** | — | |
| **Configure a connector node** | **CLI** (carve-out) | — | `uip maestro flow node configure --detail` auto-populates `inputs.detail` + `bindings_v2.json`. Hand-authored `inputs.detail` skips `essentialConfiguration` and fails at runtime — no Edit fallback. |
| **Configure a connector trigger** | **CLI** (carve-out) | — | Same as above. |
| **Configure a managed HTTP node** | **CLI** (carve-out) | — | Same as above for managed HTTP `inputs.detail` and connection resources. |
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

- Run `uip maestro flow validate <ProjectName>.flow --output json` **once** after all edits complete — not after each individual edit ([CAPABILITY.md rule #8](../CAPABILITY.md#critical-rules))
- Validation checks: JSON schema, definitions coverage, edge references, unique IDs
- Validation does NOT check: connector configuration, connection health, expression correctness, required field completeness

### Parallel same-file Edits

Applies to any turn that issues more than one `Edit` against the same `.flow` (greenfield T2 and brownfield alike). **Same-file Edits serialize in execution order** — they do not race, but each later Edit runs against the text the earlier ones already changed. An `old_string` that overlaps text a prior Edit removed or shifted fails with "string not found."

#### Anchoring parallel `.flow` Edits — anchor on what you Read, not on key order

> **Do not assume a top-level key order.** The CLI does not guarantee which keys are present or in what sequence — fixtures show `runtime` before `nodes` on one flow and absent on another, and `bindings` / `variables` / `solutionId` / `projectId` / `metadata` appear in varying positions. Any anchor of the form "closing `]` + the NEXT top-level key" is coupled to that ordering and will silently break across CLI versions or between flows. **Anchor on the target array's OWN key instead — anchor to text the file you just `Read` actually contains.**

Anchor each Edit using its target array's own opening key, located in the text you just Read — not adjacency to a neighbor key. The catch: `"nodes": [` and `"edges": [` are NOT unique in the file. They recur **inside inline `definitions[]`** (an HTTP v2 / agent / subprocess definition embeds its own nested `nodes`/`edges`) **and inside any `subflows.<id>` block** (each subflow holds its own `nodes`/`edges`) — so even a small flow can carry several copies. The reliable, version-independent discriminator is **indentation: the top-level array sits at 2-space indent; every nested one is deeper.** `"definitions": [` and the top-level `"layout": {` appear once each, so they need no disambiguation.

| Edit target | Anchor on (from the text you Read) | How to insert |
|---|---|---|
| Append to `nodes[]` | The **2-space-indented** `\n  "nodes": [` (the top-level array — deeper-indented `"nodes": ["` inside definitions do not match the two-leading-space prefix) plus the `start` node's opening `{ "id": "start"`. | Insert the new node object as the first element, immediately after the `[`: `\n    { new node JSON },`. Head-insertion keeps `old_string` clear of the array's closing `]`. |
| Append to `edges[]` | The **2-space-indented** `\n  "edges": [`. Empty after `flow init` (`\n  "edges": []`); the 2-space prefix distinguishes it from nested `edges` arrays. | When empty, replace `\n  "edges": []` with `\n  "edges": [\n    { new edge JSON }\n  ]`. When non-empty, anchor through the first edge and insert the new edge as the first element. |
| Append to `definitions[]` | `"definitions": [` plus the first definition's opening bytes. Top-level `definitions[]` is the only one in the file, so this is reliably unique. | Insert the new definition right after the opening `[`, as the first element. Never anchor on whatever key follows `definitions` — that key varies (`runtime`, `bindings`, `variables`, `layout`, depending on CLI version and what the flow contains). |
| Add an entry to `layout.nodes` | `"layout": {\n    "nodes": {\n      "start":` — `start` is the always-present trigger and the first key under `layout.nodes` in `init`-scaffolded flows. The top-level `"layout": {` is the only one. | `"layout":` + `"start":` jointly disambiguate. Insert `"<newId>": { ... },\n      ` before `"start":`. CLI-owned nodes added via `node add` already have a `layout.nodes` entry — only add entries for nodes you author by hand (e.g. End). |

**Why head-insertion.** Inserting the new element right after the array's opening `[` means the `old_string` never includes the array's closing `]` — so it cannot collide with a closing `]` from a nested object (`form.sections[].fields[]`), and it never references a sibling top-level key whose position is not guaranteed. JSON array element order is not semantically significant for `nodes` / `edges` / `definitions`, so head vs. tail insertion is equivalent; `flow format` normalizes layout regardless.

**Disjointness rule.** Two parallel Edits MUST anchor on DIFFERENT top-level arrays — nodes-Edit on the top-level `nodes[]`, edges-Edit on the top-level `edges[]`, definitions-Edit on `definitions[]`, layout-Edit on `layout.nodes`. Because each anchors on its own array (not a shared boundary), the parallel Edits never overlap — provided each anchor is unique first (see below).

**Pre-flight uniqueness check.** Before submitting an Edit, confirm your `old_string` appears **exactly once** in the file you Read. `"definitions": [` and the top-level `"layout": {` are reliably unique. `"nodes": [` and `"edges": [` are NOT — they recur inside inline definitions and subflows, so anchor on the **2-space-indented** occurrence and extend through the first element's opening (e.g. `"id": "start"`) until the match count is one. Never anchor on a bare bracket shape, and never assume the first textual occurrence is the top-level one.

**Safer fallback when in doubt:** serialize the Edits across two turns. One extra turn is cheaper than a failed-Edit recovery loop (which forces a re-Read, a re-derived anchor, and a re-submit).

See [shared/file-format.md — Top-level structure](../../shared/file-format.md#top-level-structure) for which top-level keys exist and the note that their order is not guaranteed.

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
