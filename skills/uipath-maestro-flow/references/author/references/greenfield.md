# Greenfield — Create a New Flow

End-to-end journey for creating a Flow project from scratch. Author terminates at `validate` + `format`. To publish, run, or debug after this, see [operate/CAPABILITY.md](../../operate/CAPABILITY.md).

> **Brownfield edits use a different journey.** If the `.flow` file already exists, see [brownfield.md](brownfield.md) instead.

## Should you plan first?

For complex flows, produce a plan before building. Reference [planning-arch.md](planning-arch.md) and [planning-impl.md](planning-impl.md) for the node type catalog, port reference, wiring rules, and topology patterns.

**Plan when:**
- The flow has 5+ nodes with branching or parallel paths
- The flow uses connectors or resources that need discovery
- The user's requirements are ambiguous and you need to confirm the approach

**Don't plan when:**
- Adding/editing a single node in an existing flow (use [brownfield.md](brownfield.md))
- The flow is a straightforward linear pipeline (trigger → action → action → end)
- The user has already described the exact topology they want

### Examples

**Plan:** "Build a flow that receives a Jira ticket, classifies it with an AI agent, routes urgent tickets to Slack and non-urgent to a queue, and logs everything to a Google Sheet."
→ Multiple services, branching logic, connector discovery needed. Plan first.

**Don't plan:** "Create a flow that calls an API and sends the result to Slack."
→ Linear pipeline, user knows what they want. Build directly, ask questions inline if needed. **"Build directly" skips the plan doc, not the registry search** — you still `registry search` each named service and pick a node type via the Step 3 ladder.

**Judgment call:** "Build me a flow that processes invoices."
→ Ambiguous requirements. Ask clarifying questions; plan if answers reveal complexity.

## Three-turn execution map

Steps 0–6 are **logical phases**, not separate turns. A typical greenfield build collapses to **three assistant turns** (universal SKILL.md rule #10). Each step heading below carries a `[T1]` / `[T2]` / `[T3]` tag — emit every tool call inside the same Turn as one assistant message.

| Turn | Steps | What you emit in ONE assistant message |
|---|---|---|
| **T1 — Setup + discovery** | 0, 1, 2, 3 | One chained `Bash` (scaffold + register + pull + `node add` for each CLI-owned node) **+** parallel `Bash` (one `registry get` per OOTB type you'll inline) **+** parallel `Read` (plugin `impl.md`s) **+** optional `uip login status` |
| **T2 — Read + author** | 4 | One `Read` of the `.flow` **+** a batch of `Edit` calls (or one `Write` if ≥70% of nodes change). Claude Code serializes Edits on the same file, so they don't race |
| **T3 — Finalize** | 5, 6 | One chained `Bash` (`node configure && validate && format`). On validate failure: one Edit turn, then re-chain `validate && format` |

### Batching anti-patterns

- **One CLI per turn.** Never issue `solution init`, then `cd`, then `flow init` as three separate Bash calls — chain with `&&`. Same for `node configure && validate && format`.
- **Sequential `registry get`s.** Emit every `registry get` as a parallel `Bash` in one message alongside the T1 scaffold chain.
- **Validating after every Edit.** Validate once at the end of T3 (or after a recovery Edit). Intermediate states are expected to be invalid.
- **Re-reading the `.flow` every turn.** `Read` once at the start of T2; subsequent `Edit`s in the same conversation don't need re-reading unless an external command (e.g., `node configure`, `format`) rewrites the file between Edits.
- **`Edit` in the same turn as a `Bash` that mutates the same file.** Parallel tool calls race — separate them across turns.
- **Two parallel `Edit`s anchored to the same byte range.** Same-file Edits serialize in execution order; if Edit N's `old_string` overlaps text that Edit N-1's substitution removed or shifted, Edit N fails with "string not found." Use the [per-array anchor pattern](#anchoring-parallel-flow-edits--anchor-on-what-you-read-not-on-key-order) — anchor each Edit on its target array's own opening key, never on key order or a shared boundary.

## Step 0 — Resolve the `uip` binary and detect command prefix **[T1]**

See [shared/cli-conventions.md](../../shared/cli-conventions.md) for binary resolution, version detection, and the `uip maestro flow` vs `uip flow` command prefix rule. All commands below are written in the `uip maestro flow` form. <!-- uip-check-skip -->

This probe is read-only — emit as a parallel `Bash` alongside the Step 2 scaffold chain. It does not need its own turn.

## Step 1 — Check login status **[T1 — only if needed]**

Greenfield steps 2–6 work without login (`flow init`, `validate`, `format`, registry OOTB nodes, `Edit` / `Write` edits). Login is required only when the registry needs tenant-specific connector/resource nodes, or before handing off to Operate.

```bash
uip login status --output json
```

If not logged in and you need tenant nodes:

```bash
uip login                                          # interactive OAuth (opens browser)
uip login --authority https://alpha.uipath.com     # non-production environments
```

When you do need it, emit `uip login status --output json` as a parallel `Bash` inside T1.

## Step 2 — Create a solution, THEN a Flow project inside it **[T1]**

> **A Flow project cannot exist outside a solution** (universal rule in [SKILL.md](../../../SKILL.md)). Scaffold or select a solution (Step 2a) BEFORE running `uip maestro flow init` (Step 2b). Skipping the solution step produces a single-nested `<Project>/<Project>.flow` layout that fails Studio Web upload and packaging. The correct layout is **always** `<Solution>/<Project>/<Project>.flow` (double-nested — see the tree after Step 2c).

Check the current directory for existing `.uipx` files. If existing solutions are found, use `AskUserQuestion` to present a dropdown with one option per discovered `.uipx`, a **"Create a new solution"** option, and **"Something else"** as the last option (for a custom path). If no existing solutions are found, create a new one automatically. See the AskUserQuestion dropdown rule in [SKILL.md](../../../SKILL.md).

- If the user specifies an existing `.uipx` file path or solution name, use that (skip to Step 2b)
- Otherwise, create a new solution (Step 2a)

### Canonical T1 chain — issue this as ONE `Bash` call

This is the consolidated command that does Steps 2a + 2b + Step 3 + (optionally) one `node add` per CLI-owned node, in one chained Bash. `node add` signature is `<file> <node-type>` (file first):

```bash
uip solution init "<SolutionName>" --output json \
  && cd "<SolutionName>" \
  && uip maestro flow init "<ProjectName>" --output json \
  && cd "<ProjectName>" \
  && uip maestro flow registry pull \
  && uip maestro flow node add "<ProjectName>.flow" core.action.http.v2 --label "<NodeLabel>" --output json
```

Tail-append one `node add` per CLI-owned node (`uipath.connector.*`, `uipath.connector.trigger.*`, `core.action.http.v2`). Each `node add` returns the new node `id` in `Data` — capture it from the chained output for T2/T3. Drop the trailing `node add` segment when the flow is OOTB-only.

In the SAME assistant message (parallel to this chain): emit one `Bash` per OOTB `registry get <NODE_TYPE>` you'll need in T2 (always `core.control.end` — see Step 4), and parallel `Read` calls for any plugin `impl.md`s you'll consult.

> **Older `solution-tool` (< 1.0.0)** used `solution new` (see [.claude/rules/cli-renames.md](../../../../../.claude/rules/cli-renames.md)). If `solution init` returns `unknown command`, substitute `solution new`.

The sub-steps below describe what each command in the chain does and how to verify the result.

### 2a. Create a new solution

```bash
uip solution init "<SolutionName>" --output json
```

Creates `<cwd>/<SolutionName>/<SolutionName>.uipx`. **`cd` into the new solution directory before Step 2b.**

> **Naming convention:** Use the same name for both the solution and the project unless the user specifies otherwise. If the user only provides a project name, use it as the solution name too.

### 2b. Create the Flow project inside the solution folder

```bash
cd <directory>/<SolutionName> && uip maestro flow init <ProjectName> --output json
```

The `cd` is required. Running `uip maestro flow init` from outside the solution directory (or from the parent of `<SolutionName>/`) is wrong — it produces a single-nested layout and breaks every later step.

> **Bash session state persists across tool calls.** This `cd` is **not scoped to one Bash invocation** — your cwd remains inside `<SolutionName>/` for every subsequent `Bash` call until you `cd` somewhere else. Plan the rest of Step 2 (and Steps 3–6) accordingly: either keep using paths relative to the solution dir, or anchor with `$(pwd)` / the absolute `Data.Path` returned by `flow init`. Do NOT prefix later commands with the original `<directory>/<SolutionName>/...` — that would resolve as `<SolutionName>/<directory>/<SolutionName>/...` and look like a layout bug when it isn't.

`--output json` is required so Step 2c can inspect `Data.SolutionRegistration.Status` to confirm the project was auto-registered with the parent solution.

### 2c. Verify the project is registered in the solution

When `uip maestro flow init` is run from inside a solution directory (Step 2b), it **auto-registers** the project with the nearest parent `.uipx`. The success envelope reports this in `Data.SolutionRegistration`:

```json
{
  "Result": "Success",
  "Code": "FlowInit",
  "Data": {
    "Status": "Created successfully",
    "Path": ".../<SolutionName>/<ProjectName>",
    "SolutionRegistration": {
      "Status": "Registered",                     // or "AlreadyRegistered"
      "Solution": ".../<SolutionName>.uipx",
      "Project": "<ProjectName>/project.uiproj",
      "ProjectId": "<uuid>"
    }
  }
}
```

If `Data.SolutionRegistration.Status` is `Registered` or `AlreadyRegistered`, **you are done** with this step — proceed to the layout check.

**Fallback** — only if `Status` is `Skipped` or `Failed` (e.g., `init` was run outside the solution directory and produced a single-nested layout, or the `.uipx` write failed): wire the project manually.

```bash
uip solution project add \
  <directory>/<SolutionName>/<ProjectName> \
  <directory>/<SolutionName>/<SolutionName>.uipx
```

If the registration was skipped because of single-nesting, **delete the partial scaffold and restart from Step 2a** — do not try to patch the layout by hand. See [diagnose/references/failure-modes.md — Single-nested layout](../../diagnose/references/failure-modes.md#single-nested-layout).

### Expected layout after Steps 2a–2c

```
<cwd>/
└── <SolutionName>/                    ← from `uip solution init`
    ├── <SolutionName>.uipx
    └── <ProjectName>/                 ← from `uip maestro flow init` (run from inside <SolutionName>/)
        ├── <ProjectName>.flow         ← the file you edit
        ├── project.uiproj
        ├── bindings_v2.json
        ├── entry-points.json
        ├── operate.json
        └── package-descriptor.json
```

**Self-check — run this before Step 3:**

After Step 2b your cwd is inside `<SolutionName>/` (the `cd` persists). Verify the flow file using a `$(pwd)`-anchored absolute path so the check is robust to that cwd drift:

```bash
ls "$(pwd)/<ProjectName>/<ProjectName>.flow"
```

Equivalent: use the absolute project dir reported by `flow init` in `Data.Path` and append `/<ProjectName>.flow`. Either form gives an absolute path that doesn't depend on the current cwd.

> **Don't write `<SolutionName>/<ProjectName>/<ProjectName>.flow` here.** From inside `<SolutionName>/` that resolves to `<SolutionName>/<SolutionName>/<ProjectName>/<ProjectName>.flow` (triple-nested) and the `ls` will fail even though the layout is correct. That false negative wastes turns chasing a non-bug.

If the file does not exist at the absolute double-nested path, Step 2 is wrong. Delete the partial scaffold and restart from Step 2a — do not try to patch the layout by hand.

See [shared/file-format.md](../../shared/file-format.md) for the full project structure.

## Step 3 — Refresh the registry **[T1 — chained tail of Step 2]**

This is already the last segment of the [canonical T1 chain](#canonical-t1-chain--issue-this-as-one-bash-call) above. Standalone:

```bash
uip maestro flow registry pull                          # refresh local cache (expires after 30 min)
```

**Parallel `registry get`** — in the same T1 assistant message, emit one separate `Bash` per OOTB node type whose definition you'll inline in T2. **Always fetch `core.control.end`** — `flow init` does not scaffold one (see Step 4):

```bash
uip maestro flow registry get core.control.end --output json
```

> **Auth note**: Without `uip login`, registry shows OOTB nodes only. After login, tenant-specific connector and resource nodes are also available. **In-solution sibling projects** are always available via `--local` without login — see below.

### Select the node type for each external service (runs even when full planning is skipped)

Calling a named external service (Slack, open-meteo, Stripe, any REST API)? **Search first — never guess the node type from the brand name:**

```bash
uip maestro flow registry search "<service>" --output json --output-filter "[*].{NodeType:NodeType,DisplayName:DisplayName,Description:Description,AvailableOnTenant:AvailableOnTenant}"
```

Then pick the first match down this ladder:

1. **Curated connector activity** (`uipath.connector.<key>.<op>` in the results) → use it.
2. **Connector exists but no activity for what you need** → `core.action.http.v2` (connector mode).
3. **No connector at all** → `core.action.http.v2` (manual mode).
4. **No API** (desktop app) → [rpa](references/plugins/rpa/planning.md).

Manual HTTP is the **bottom of the ladder** — only the search returning no connector authorizes it. Picking it without searching is the brand-name shortcut forbidden by [SKILL.md rule #3](../../../SKILL.md#critical-rules-universal).

**In-solution discovery (no login required):**

```bash
uip maestro flow registry list --local --output json     # discover sibling projects in the same .uipx solution
uip maestro flow registry get "<node-type>" --local --output json  # get full manifest for a local node
```

Run from inside the flow project directory. Returns the same manifest format as the tenant registry. Use `--local` to wire in-solution resources (RPA, agents, flows, API workflows) without publishing them first.

## Step 4 — Build the flow **[T2]**

> **`flow init` scaffolds ONLY the manual trigger (`start` / `core.trigger.manual`) with zero edges.** Every other user-owned node — **including the End node** — is yours to add via `Edit` / `Write`. Any HTTP / connector / connector-trigger node you `node add`-ed in T1 is already in `nodes[]` and `definitions[]` but has empty `inputs.detail` (filled in T3) and is not wired yet.

### T2 batch — issue these in ONE assistant message

1. **One `Read`** of `<ProjectName>.flow` — required before any Edit/Write; T1's chained Bash mutated the file and Claude Code's file-state tracker does not auto-refresh on external mutations.
2. **A batch of parallel `Edit` calls** — one per top-level array you're modifying. Same-file Edits serialize in execution order, so each `old_string` must anchor to text NO OTHER parallel Edit modifies. Use the **per-array anchor pattern** below.
   - Edit `nodes[]` — add the End node (and any other user-owned nodes).
   - Edit `definitions[]` — paste the End definition verbatim from T1's `registry get core.control.end` output.
   - Edit `edges[]` — wire `trigger → <httpNode> → end`. End-node `outputs` mapping goes here too if you declared an `out` variable in `variables.globals`.
   - Edit `layout.nodes` — placeholder `{ position: { x: 0, y: 0 }, size: { width: 96, height: 96 }, collapsed: false }` per new node; `format` rewrites positions in T3.

   `Write` of the whole file is allowed but token-costly on flows >~10 nodes — only fall back to `Write` when ≥70% of nodes change AND the file is small (see [editing-operations.md — Tool Selection Ladder](editing-operations.md#tool-selection-ladder)).

#### Anchoring parallel `.flow` Edits — anchor on what you Read, not on key order

> **Do not assume a top-level key order.** The CLI does not guarantee which keys are present or in what sequence — fixtures show `runtime` before `nodes` on one flow and absent on another, and `bindings` / `variables` / `solutionId` / `projectId` / `metadata` appear in varying positions. Any anchor of the form "closing `]` + the NEXT top-level key" is coupled to that ordering and will silently break across CLI versions or between flows. **Anchor on the target array's OWN key instead — you just `Read` the file at the top of T2, so anchor to text that read actually contains.**

Anchor each Edit using its target array's own opening key, located in the text you just Read — not adjacency to a neighbor key. The catch: `"nodes": [` and `"edges": [` are NOT unique in the file. They recur **inside `definitions[]`** — an inline node definition (HTTP v2, agents, subprocess) embeds its own nested `nodes`/`edges` arrays. (Even a fresh flow with one `node add`-ed HTTP node shows `"nodes": [` four times.) The reliable discriminator is **indentation: the top-level array sits at 2-space indent; every nested one is deeper** (4, 10, 14 spaces). `"definitions": [` and the top-level `"layout": {` happen to appear once each, so they need no disambiguation.

| Edit target | Anchor on (from the text you Read) | How to insert |
|---|---|---|
| Append to `nodes[]` | The **2-space-indented** `\n  "nodes": [` (the top-level array — deeper-indented `"nodes": ["` inside definitions do not match the two-leading-space prefix) plus the `start` node's opening `{ "id": "start"`. | Insert the new node object as the first element, immediately after the `[`: `\n    { new node JSON },`. Head-insertion keeps `old_string` clear of the array's closing `]`. |
| Append to `edges[]` | The **2-space-indented** `\n  "edges": [`. Empty after `flow init` (`\n  "edges": []`); the 2-space prefix distinguishes it from nested `edges` arrays. | When empty, replace `\n  "edges": []` with `\n  "edges": [\n    { new edge JSON }\n  ]`. When non-empty, anchor through the first edge and insert the new edge as the first element. |
| Append to `definitions[]` | `"definitions": [` plus the first definition's opening bytes. Top-level `definitions[]` is the only one in the file, so this is reliably unique. | Insert the new definition right after the opening `[`, as the first element. Never anchor on whatever key follows `definitions` — that key varies (`runtime`, `bindings`, `variables`, `layout`, depending on CLI version and what the flow contains). |
| Add an entry to `layout.nodes` | `"layout": {\n    "nodes": {\n      "start":` — `start` is the always-present trigger and the first key under `layout.nodes` in `init`-scaffolded flows. The top-level `"layout": {` is the only one. | `"layout":` + `"start":` jointly disambiguate. Insert `"<newId>": { ... },\n      ` before `"start":`. CLI-owned nodes added via `node add` already have a `layout.nodes` entry — only add entries for nodes you author by hand (e.g. End). |

**Why head-insertion.** Inserting the new element right after the array's opening `[` means the `old_string` never includes the array's closing `]` — so it cannot collide with a closing `]` from a nested object (`form.sections[].fields[]`), and it never references a sibling top-level key whose position is not guaranteed. JSON array element order is not semantically significant for `nodes` / `edges` / `definitions`, so head vs. tail insertion is equivalent; `flow format` normalizes layout regardless.

**Disjointness rule.** Two parallel Edits MUST anchor on DIFFERENT top-level arrays — nodes-Edit on the top-level `nodes[]`, edges-Edit on the top-level `edges[]`, definitions-Edit on `definitions[]`, layout-Edit on `layout.nodes`. Because each anchors on its own array (not a shared boundary), the parallel Edits never overlap — provided each anchor is unique first (see below).

**Pre-flight uniqueness check.** Before submitting an Edit, confirm your `old_string` appears **exactly once** in the file you Read. `"definitions": [` and the top-level `"layout": {` are reliably unique. `"nodes": [` and `"edges": [` are NOT — they recur inside inline definitions, so anchor on the **2-space-indented** occurrence and extend through the first element's opening (e.g. `"id": "start"`) until the match count is one. Never anchor on a bare bracket shape, and never assume the first textual occurrence is the top-level one.

**Safer fallback when in doubt:** serialize the Edits across two turns. Two turns ≈ +5–10s; a failed Edit recovery loop is usually +20–30s (recovery requires re-reading a file slice, re-deriving an anchor, and re-submitting).

See [shared/file-format.md — Top-level structure](../../shared/file-format.md#top-level-structure) for which top-level keys exist and the note that their order is not guaranteed.

> **Intra-turn ordering.** If a parallel `Edit` fails with "file not read," split `Read` into its own turn (cost: +1 turn).

### Node ownership recap

> **Before each node, classify it as user-owned or CLI-owned (see [CAPABILITY.md — Node ownership](../CAPABILITY.md#node-ownership--who-authors-the-node)). Connector activities, connector triggers, and `core.action.http.v2` are CLI-only — use `uip maestro flow node add` + `uip maestro flow node configure`, never Edit. Hand-writing these will fail `flow validate`.**

Edit `<ProjectName>.flow` directly in the project root. The `bindings_v2.json` file is also in the project root for resource bindings.

> **Tool selection by ownership.** Use `Edit` for in-place changes to user-owned nodes; `Write` only when ≥70% of nodes change. For CLI-owned nodes (above), use `uip maestro flow node add` + `node configure` — see the relevant plugin's `impl.md` for the full configuration workflow. Inline-agent project scaffolding uses `uip agent init --inline-in-flow`, but inline-agent flow node/wiring edits are direct `.flow` JSON (the agent node itself is user-owned).

Read [editing-operations.md](editing-operations.md) for strategy selection and per-operation recipes.

> **Self-check before each mutation:** name the tool you're about to use. If the answer isn't `Edit`, `Write`, or `uip maestro flow ...` — STOP and ask the user via `AskUserQuestion` (per the dropdown rule in [SKILL.md](../../../SKILL.md)). `python`, `node`, `jq`, `sed`, `awk`, and shell heredocs are a last resort and require explicit user approval after you've surfaced the trade-offs. See [editing-operations.md — Tool Selection Ladder](editing-operations.md#tool-selection-ladder).

For each node type, follow the relevant plugin's `impl.md` for node-specific inputs, JSON structure, and configuration. The operations guides cover the mechanics (how to add/remove/wire); the plugins cover the semantics (what inputs and model fields each node type needs).

## Step 5 — Validate **[T3 — chain with Step 6, plus any T1 `node configure`]**

### Canonical T3 chain — issue this as ONE `Bash` call

```bash
uip maestro flow node configure "<ProjectName>.flow" "<httpNodeId>" \
  --detail '{"authentication":"manual","method":"GET","url":"https://api.example.com/...","query":{"...":"..."}}' \
  --output json \
  && uip maestro flow validate "<ProjectName>.flow" --output json \
  && uip maestro flow format "<ProjectName>.flow" --output json
```

Tail-append one `node configure` per CLI-owned node added in T1, using the node IDs captured from T1's chained output. Drop the entire `node configure` segment if no CLI-owned nodes exist.

**On validate failure:** one `Edit` turn to fix, then re-chain `validate && format` in one Bash. Do not validate after every individual Edit during T2 — intermediate states are expected to be invalid.

### Common error categories

- **Missing targetPort** — every edge needs a `targetPort` string
- **Missing definition** — every `type:typeVersion` in nodes needs a matching `definitions` entry
- **Invalid node/edge references** — `sourceNodeId`/`targetNodeId` must reference existing node `id`s
- **Duplicate IDs** — node and edge `id`s must be unique

## Step 6 — Format node layout **[T3 — chained tail of Step 5]**

This is the last segment of the [canonical T3 chain](#canonical-t3-chain--issue-this-as-one-bash-call) above. After validation passes, format must run before publishing or debugging (see "Always run `flow format` after edits" in [the Author capability index](../CAPABILITY.md)). Format:

- Arranges nodes horizontally (left-to-right) using ELK with `nodeSpacing: 96`, anchored to the leftmost node's original position
- Sets every non-stickyNote node's `size` to `{ "width": 96, "height": 96 }` so Studio Web renders square nodes (skipping this leaves any non-96 dimensions intact and produces misshapen rectangles — the MST-9061 failure mode)
- Recurses into subflows and rewrites `subflows[<id>].layout`
- Backfills missing `position`/`size` entries

Standalone (only if not chained from Step 5):

```bash
uip maestro flow format <ProjectName>.flow --output json
```

## Completion Output

When you finish building the flow, report to the user:

1. **File path** of the `.flow` file created
2. **What was built** — summary of nodes added, edges wired, and logic implemented
3. **Validation status** — whether `flow validate` passes (or remaining errors if unresolvable)
4. **Format status** — confirm `flow format` was run
5. **Mock placeholders** — list any `core.logic.mock` nodes that need to be replaced, and which skill to use
6. **Missing connections** — any connector nodes that need connections the user must create
7. **What's next** — use `AskUserQuestion` to present the dropdown below (see the AskUserQuestion dropdown rule in [SKILL.md](../../../SKILL.md))

### What's next dropdown

Authoring terminates here. Each option below hands off to Operate — read [operate/CAPABILITY.md](../../operate/CAPABILITY.md) for the command sequence.

| Option | What it does |
| --- | --- |
| **Publish to Studio Web** (default) | Push the solution to Studio Web so the user can visualize, edit, and publish from the browser. |
| **Debug the solution** | Execute the flow end-to-end against real systems. Confirm consent first — debug has real side effects (see the consent-before-debug rule in [SKILL.md](../../../SKILL.md)). |
| **Deploy to Orchestrator** | Pack and publish directly to Orchestrator (bypasses Studio Web). Only when explicitly chosen — see [/uipath:uipath-platform](/uipath:uipath-platform). |
| **Something else** | Last option. Accept free-form string input and act on it (e.g., "just leave it", "pack but don't publish", "upload to a different tenant"). |

Do not run any of these actions without explicit user selection. Once the user picks an option, read [operate/CAPABILITY.md](../../operate/CAPABILITY.md) and follow that capability's flow — do not run operate commands from inside this doc.
