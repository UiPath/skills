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
→ Linear pipeline, user knows what they want. Build directly, ask questions inline if needed.

**Judgment call:** "Build me a flow that processes invoices."
→ Ambiguous requirements. Ask clarifying questions; plan if answers reveal complexity.

## Step 0 — Resolve the `uip` binary and detect command prefix

See [shared/cli-conventions.md](../../shared/cli-conventions.md) for binary resolution, version detection, and the `uip maestro flow` vs `uip flow` command prefix rule. All commands below are written in the `uip maestro flow` form. <!-- uip-check-skip -->

## Step 1 — Check login status

Greenfield steps 2–6 work without login (`flow init`, `validate`, `format`, registry OOTB nodes, `Edit` / `Write` edits). Login is required only when the registry needs tenant-specific connector/resource nodes, or before handing off to Operate.

```bash
uip login status --output json
```

If not logged in and you need tenant nodes:

```bash
uip login                                          # interactive OAuth (opens browser)
uip login --authority https://alpha.uipath.com     # non-production environments
```

## Step 2 — Create a solution, THEN a Flow project inside it

> **A Flow project cannot exist outside a solution** (universal rule in [SKILL.md](../../../SKILL.md)). Scaffold or select a solution (Step 2a) BEFORE running `uip maestro flow init` (Step 2b). Skipping the solution step produces a single-nested `<Project>/<Project>.flow` layout that fails Studio Web upload and packaging. The correct layout is **always** `<Solution>/<Project>/<Project>.flow` (double-nested — see the tree after Step 2c).

Check the current directory for existing `.uipx` files. If existing solutions are found, use `AskUserQuestion` to present a dropdown with one option per discovered `.uipx`, a **"Create a new solution"** option, and **"Something else"** as the last option (for a custom path). If no existing solutions are found, create a new one automatically. See the AskUserQuestion dropdown rule in [SKILL.md](../../../SKILL.md).

- If the user specifies an existing `.uipx` file path or solution name, use that (skip to Step 2b)
- Otherwise, create a new solution (Step 2a)

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

## Step 3 — Refresh the registry

```bash
uip maestro flow registry pull                          # refresh local cache (expires after 30 min)
```

> **Auth note**: Without `uip login`, registry shows OOTB nodes only. After login, tenant-specific connector and resource nodes are also available. **In-solution sibling projects** are always available via `--local` without login — see below.

**In-solution discovery (no login required):**

```bash
uip maestro flow registry list --local --output json     # discover sibling projects in the same .uipx solution
uip maestro flow registry get "<nodeType>" --local --output json  # get full manifest for a local node
```

Run from inside the flow project directory. Returns the same manifest format as the tenant registry. Use `--local` to wire in-solution resources (RPA, agents, flows, API workflows) without publishing them first.

## Step 4 — Build the flow

> **Before each node, classify it as user-owned or CLI-owned (see [CAPABILITY.md — Node ownership](../CAPABILITY.md#node-ownership--who-authors-the-node)). Connector activities, connector triggers, and `core.action.http.v2` are CLI-only — use `uip maestro flow node add` + `uip maestro flow node configure`, never Edit. Hand-writing these will fail `flow validate`.**

Edit `<ProjectName>.flow` directly in the project root. The `bindings_v2.json` file is also in the project root for resource bindings.

> **Tool selection by ownership.** Use `Edit` for in-place changes to user-owned nodes; `Write` only when ≥70% of nodes change. For CLI-owned nodes (above), use `uip maestro flow node add` + `node configure` — see the relevant plugin's `impl.md` for the Quick Reference sequence. Inline-agent project scaffolding uses `uip agent init --inline-in-flow`, but inline-agent flow node/wiring edits are direct `.flow` JSON (the agent node itself is user-owned).

Read [editing-operations.md](editing-operations.md) for strategy selection and per-operation recipes.

> **Self-check before each mutation:** name the tool you're about to use. If the answer isn't `Edit`, `Write`, or `uip maestro flow ...` — STOP and ask the user via `AskUserQuestion` (per the dropdown rule in [SKILL.md](../../../SKILL.md)). `python`, `node`, `jq`, `sed`, `awk`, and shell heredocs are a last resort and require explicit user approval after you've surfaced the trade-offs. See [editing-operations.md — Tool Selection Ladder](editing-operations.md#tool-selection-ladder).

For each node type, follow the relevant plugin's `impl.md` for node-specific inputs, JSON structure, and configuration. The operations guides cover the mechanics (how to add/remove/wire); the plugins cover the semantics (what inputs and model fields each node type needs).

## Step 5 — Validate loop

Run validation and fix errors iteratively until the flow is clean.

```bash
uip maestro flow validate <ProjectName>.flow --output json
```

**Validation loop:**
1. Run `uip maestro flow validate`
2. If valid → done, move to Step 6 (format layout)
3. If errors → read the error messages, fix the `.flow` file
4. Go to 1

Common error categories:
- **Missing targetPort** — every edge needs a `targetPort` string
- **Missing definition** — every `type:typeVersion` in nodes needs a matching `definitions` entry
- **Invalid node/edge references** — `sourceNodeId`/`targetNodeId` must reference existing node `id`s
- **Duplicate IDs** — node and edge `id`s must be unique

## Step 6 — Format node layout

After validation passes, **always** run format before publishing or debugging — this is the canonical layout step (see "Always run `flow format` after edits" in [the Author capability index](../CAPABILITY.md)). Format:

- Arranges nodes horizontally (left-to-right) using ELK with `nodeSpacing: 96`, anchored to the leftmost node's original position
- Sets every non-stickyNote node's `size` to `{ "width": 96, "height": 96 }` so Studio Web renders square nodes (skipping this leaves any non-96 dimensions intact and produces misshapen rectangles — the MST-9061 failure mode)
- Recurses into subflows and rewrites `subflows[<id>].layout`
- Backfills missing `position`/`size` entries

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
