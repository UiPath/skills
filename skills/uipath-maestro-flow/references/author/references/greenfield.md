# Greenfield — Create a New Flow

End-to-end journey for creating a Flow project from scratch. Author terminates at `validate` + `tidy`. To publish, run, or debug after this, see [operate/CAPABILITY.md](../../operate/CAPABILITY.md).

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

See [shared/cli-conventions.md](../../shared/cli-conventions.md) for binary resolution, version detection, and the `uip maestro flow` vs `uip flow` command prefix rule. All commands below are written in the `uip maestro flow` form.

## Step 1 — Check login status

Greenfield steps 2–6 work without login (`flow init`, `validate`, `tidy`, registry OOTB nodes, Direct JSON edits). Login is required only when the registry needs tenant-specific connector/resource nodes, or before handing off to Operate.

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
uip solution new "<SolutionName>" --output json
```

Creates `<cwd>/<SolutionName>/<SolutionName>.uipx`. **`cd` into the new solution directory before Step 2b.**

> **Naming convention:** Use the same name for both the solution and the project unless the user specifies otherwise. If the user only provides a project name, use it as the solution name too.

### 2b. Create the Flow project inside the solution folder

```bash
cd <directory>/<SolutionName> && uip maestro flow init <ProjectName>
```

The `cd` is required. Running `uip maestro flow init` from outside the solution directory (or from the parent of `<SolutionName>/`) is wrong — it produces a single-nested layout and breaks every later step.

### 2c. Add the project to the solution

```bash
uip solution project add \
  <directory>/<SolutionName>/<ProjectName> \
  <directory>/<SolutionName>/<SolutionName>.uipx
```

### Expected layout after Steps 2a–2c

```
<cwd>/
└── <SolutionName>/                    ← from `uip solution new`
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

```bash
ls "<directory>/<SolutionName>/<ProjectName>/<ProjectName>.flow"
```

If the file does not exist at that exact path (double-nested), Step 2 is wrong. Delete the partial scaffold and restart from Step 2a — do not try to patch the layout by hand.

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

Edit `<ProjectName>.flow` directly in the project root. The `bindings_v2.json` file is also in the project root for resource bindings.

**Read [editing-operations.md](editing-operations.md).** Direct JSON is the default for all edits. CLI is used for connector, connector-trigger, and inline-agent nodes (see their plugin `impl.md`) or when the user explicitly opts in to CLI.

For each node type, follow the relevant plugin's `impl.md` for node-specific inputs, JSON structure, and configuration. The operations guides cover the mechanics (how to add/delete/wire); the plugins cover the semantics (what inputs and model fields each node type needs).

## Step 5 — Validate loop

Run validation and fix errors iteratively until the flow is clean.

```bash
uip maestro flow validate <ProjectName>.flow --output json
```

**Validation loop:**
1. Run `uip maestro flow validate`
2. If valid → done, move to Step 6 (tidy layout)
3. If errors → read the error messages, fix the `.flow` file
4. Go to 1

Common error categories:
- **Missing targetPort** — every edge needs a `targetPort` string
- **Missing definition** — every `type:typeVersion` in nodes needs a matching `definitions` entry
- **Invalid node/edge references** — `sourceNodeId`/`targetNodeId` must reference existing node `id`s
- **Duplicate IDs** — node and edge `id`s must be unique

## Step 6 — Tidy node layout

After validation passes, **always** run tidy before publishing or debugging — this is the canonical layout step (see "Always run `flow tidy` after edits" in [the Author capability index](../CAPABILITY.md)). Tidy:

- Arranges nodes horizontally (left-to-right) using ELK with `nodeSpacing: 96`, anchored to the leftmost node's original position
- Sets every non-stickyNote node's `size` to `{ "width": 96, "height": 96 }` so Studio Web renders square nodes (skipping this leaves any non-96 dimensions intact and produces misshapen rectangles — the MST-9061 failure mode)
- Recurses into subflows and rewrites `subflows[<id>].layout`
- Backfills missing `position`/`size` entries

```bash
uip maestro flow tidy <ProjectName>.flow --output json
```

## Completion Output

When you finish building the flow, report to the user:

1. **File path** of the `.flow` file created
2. **What was built** — summary of nodes added, edges wired, and logic implemented
3. **Validation status** — whether `flow validate` passes (or remaining errors if unresolvable)
4. **Tidy status** — confirm `flow tidy` was run
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
