---
name: uipath-flow
description: "This skill should be used when the user wants to 'create a new Flow project', 'scaffold a flow with uip flow init', 'add a node to my flow', 'connect nodes in my flow', 'validate a .flow file', 'debug a flow', 'run a flow', 'discover flow node types', or when the user is editing a .flow file, wiring nodes and edges, working with definitions or ports, or asks about the .flow JSON format or uip flow CLI commands."
metadata:
   allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath Flow Authoring Assistant

Comprehensive guide for creating, editing, validating, and debugging UiPath Flow projects using the `uip` CLI and `.flow` file format.

## When to Use This Skill

- User wants to **create a new Flow project** with `uip flow init`
- User is **editing a `.flow` file** — adding nodes, edges, or logic
- User wants to **explore available node types** via the registry
- User wants to **validate** a Flow file locally
- User wants to **debug** a Flow (cloud)
- User asks about the **`.flow` JSON format**, nodes, edges, definitions, or ports
- User asks **how to implement logic** in a Flow (scripts, HTTP calls, branching, etc.)

## Quick Start

These steps are for **creating a new flow from scratch**. For existing projects, skip to the relevant step. For small targeted edits (changing a script body, renaming a node, tweaking a port), skip straight to Step 5.

### Step 0 — Resolve the `uip` binary

The `uip` CLI is installed via npm. If `uip` is not on PATH (common in nvm environments), resolve it first:

```bash
UIP=$(command -v uip 2>/dev/null || npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip
$UIP --version
```

Use `$UIP` in place of `uip` for all subsequent commands if the plain `uip` command isn't found.

### Step 1 — Check login status

`uip flow debug` and process operations require authentication. `uip flow init`, `validate`, and `registry` commands work without login.

```bash
uip login status --format json
```

If not logged in and you need cloud features:
```bash
uip login                                          # interactive OAuth (opens browser)
uip login --authority https://alpha.uipath.com     # non-production environments
```

### Step 2 — Create a new Flow project

```bash
uip flow init <ProjectName>
```

This scaffolds a complete project. See [references/flow-file-format.md](references/flow-file-format.md) for the full project structure.

### Step 3 — Discover available node types

Before editing the `.flow` file, check what nodes are available:

```bash
uip flow registry pull                          # refresh local cache (expires after 30 min)
uip flow registry list --format json            # list all cached node types
uip flow registry search <keyword>              # search by name, tag, or category
uip flow registry search --filter "category=agent"
uip flow registry get <nodeType> --format json  # full schema for one node type
```

> **Auth note**: Without `uip login`, registry shows OOTB nodes only. After login, tenant-specific connector nodes are also available.

### Step 4 — Plan the flow

**Only for new flows or major restructuring** (adding multiple nodes, redesigning connections). Skip this step for small targeted edits.

Before editing the `.flow` file, create a plan and get user approval.

1. **Output the plan directly in chat** with:
   - **Goal** -- one-line summary of what the flow does
   - **Nodes** -- numbered list of each step, its node type, and what it does
   - **Connections** -- how nodes connect (which output port to which input port)
   - **Inputs** -- what the flow needs to start (trigger type, input arguments)
   - **Outputs** -- what the flow produces (return values, side effects)
   - **Missing information** -- anything the user hasn't specified that you need to proceed, marked as `[REQUIRED: description]` (e.g. connector IDs, channel names, credentials)

2. **Ask the user to review the plan before proceeding.** Do NOT move to Step 5 until the user confirms. If the user requests changes, revise the plan and ask again.

### Step 5 — Edit the `.flow` file

Edit `flow_files/<ProjectName>.flow` only. Never edit `content/<ProjectName>.bpmn` — it is auto-generated.

See [references/flow-file-format.md](references/flow-file-format.md) for the full JSON schema, node/edge structure, and definition requirements.

### Step 6 — Validate locally

```bash
uip flow validate flow_files/<ProjectName>.flow --format json
```

Validates JSON structure and cross-references (edges point to existing nodes, every node type has a `definitions` entry). No auth required, runs instantly.

If validation fails, read the errors, fix the `.flow` file, and re-validate. Repeat until validation passes.

### Step 7 — Debug (cloud) — only when explicitly requested

```bash
uip flow debug flow_files/<ProjectName>.flow
```

Requires `uip login`. Uploads to Studio Web, triggers a debug session in Orchestrator, and streams results. Use `flow validate` first — cloud debug is slower and requires connectivity.

**Do NOT run `flow debug` automatically.** Debug executes the flow for real — it will send emails, post Slack messages, call APIs, write to databases, etc. Only run debug when the user explicitly asks to debug or test the flow. After validation succeeds, tell the user the flow is ready and ask if they want to debug it.

## Task Navigation

| I need to... | Read these |
|---|---|
| **Understand the .flow JSON format** | [references/flow-file-format.md](references/flow-file-format.md) |
| **Know all CLI commands** | [references/flow-commands.md](references/flow-commands.md) |
| **Add a Script node** | [references/flow-file-format.md - Script node](references/flow-file-format.md) |
| **Wire nodes with edges** | [references/flow-file-format.md - Edges](references/flow-file-format.md) |
| **Find the right node type** | Run `uip flow registry search <keyword>` |
| **Pack / publish / deploy** | [/uipath:uipath-platform](/uipath:uipath-platform) |

## Key Concepts

### validate vs debug

| Command | What it does | Auth needed |
|---------|-------------|-------------|
| `uip flow validate` | Local JSON schema + cross-reference check | No |
| `uip flow debug` | Converts to BPMN, uploads to Studio Web, runs in Orchestrator, streams results | Yes |

Always `validate` locally before `debug`. Validation is instant; debug is a cloud round-trip.

### .flow file — critical rules

1. **`targetPort` is required on every edge** — `validate` rejects edges without it with `[error] [edges.N.targetPort] expected string, received undefined`
2. **Every node type needs a `definitions` entry** — copy from `uip flow registry get <nodeType>` output
3. **Edit `flow_files/*.flow` only** — `content/*.bpmn` is auto-generated and will be overwritten
4. **Script node returns an object** — `return { key: value }` not a scalar

### CLI output format

All `uip` commands return structured JSON:
```json
{ "Result": "Success", "Code": "FlowValidate", "Data": { ... } }
{ "Result": "Failure", "Message": "...", "Instructions": "Found N error(s): ..." }
```

Always use `--format json` for programmatic use. The `--localstorage-file` warning in some environments is benign.

## References

- **[.flow File Format](references/flow-file-format.md)** — Full JSON schema, node/edge structure, common node types, ports, and examples
- **[CLI Command Reference](references/flow-commands.md)** — All `uip flow` subcommands with parameters
- **[Pack / Publish / Deploy](/uipath:uipath-platform)** — Packaging and Orchestrator deployment (uipath-platform skill)
