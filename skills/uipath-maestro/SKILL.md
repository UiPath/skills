---
name: uipath-maestro
description: "This skill should be used when the user wants to 'manage Maestro process instances', 'list Maestro processes', 'pause or resume a Maestro instance', 'cancel or retry a Maestro instance', 'navigate a Maestro instance to a specific step', 'manage Maestro incidents', 'check Maestro instance status', 'set Maestro instance input or deadline', 'create notes on a Maestro instance', or when the user asks about UiPath Maestro CLI commands, Maestro runtime management, or orchestrating long-running business processes with Maestro."
metadata:
   allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath Maestro Runtime Management Assistant

Comprehensive guide for managing UiPath Maestro process instances, processes, and incidents using the `uip maestro` CLI commands.

## When to Use This Skill

- User wants to **list or inspect Maestro process instances**
- User wants to **pause, resume, cancel, or retry** a Maestro instance
- User wants to **navigate a Maestro instance** to a specific step (`goto`)
- User wants to **set input data or a deadline** on a Maestro instance
- User wants to **create or list notes** on a Maestro instance
- User wants to **update the priority** of a Maestro instance
- User wants to **list or view Maestro processes** (deployed process definitions)
- User wants to **list Maestro incidents** (runtime errors)
- User asks about **Maestro CLI commands** or Maestro runtime concepts

> **Note:** Maestro processes are authored in UiPath Studio Web (BPMN designer), not via the CLI. The `uip maestro` commands are for **runtime management only** — there is no `init`, `validate`, or `pack` equivalent for Maestro.

## Quick Start

### Step 0 — Resolve the `uip` binary

The `uip` CLI is installed via npm. If `uip` is not on PATH (common in nvm environments), resolve it first:

```bash
if UIP=$(command -v uip 2>/dev/null); then
  # uip is on PATH, use it directly
  :
else
  # uip not on PATH, resolve via npm
  UIP=$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip
fi
$UIP --version
```

Use `$UIP` in place of `uip` for all subsequent commands if the plain `uip` command isn't found.

### Step 1 — Check login status

All `uip maestro` commands require authentication.

```bash
uip login status --format json
```

If not logged in:
```bash
uip login                                          # interactive OAuth (opens browser)
uip login --authority https://alpha.uipath.com     # non-production environments
```

### Step 2 — Install the Maestro tool plugin

The `maestro` command group is provided by the `@uipath/maestro-tool` plugin. Install it if not already present:

```bash
uip tools install @uipath/maestro-tool
```

Verify installation:
```bash
uip maestro --help
```

### Step 3 — List process instances

```bash
uip maestro instances list --format json
uip maestro instances list --folder-key <key> --format json
uip maestro instances list --process-key <key> --format json
```

### Step 4 — Inspect a specific instance

```bash
uip maestro instances get <instance-id> --format json
```

### Step 5 — Take action on an instance

```bash
uip maestro instances pause <instance-id> --format json
uip maestro instances resume <instance-id> --format json
uip maestro instances cancel <instance-id> --comment "Reason" --format json
uip maestro instances retry <instance-id> --format json
```

## Task Navigation

| I need to... | Read these |
|---|---|
| **List/filter process instances** | [references/maestro-commands.md - instances list](references/maestro-commands.md) |
| **Inspect instance details** | [references/maestro-commands.md - instances get](references/maestro-commands.md) |
| **Pause/resume/cancel/retry an instance** | [references/maestro-commands.md - Instance Lifecycle](references/maestro-commands.md) |
| **Navigate an instance to a step** | [references/maestro-commands.md - instances goto](references/maestro-commands.md) |
| **Set input data or deadline** | [references/maestro-commands.md - instances input/deadline](references/maestro-commands.md) |
| **Create or list notes** | [references/maestro-commands.md - instances notes](references/maestro-commands.md) |
| **Update instance priority** | [references/maestro-commands.md - instances update-priority](references/maestro-commands.md) |
| **List tasks for an instance** | [references/maestro-commands.md - instances list-tasks](references/maestro-commands.md) |
| **List deployed processes** | [references/maestro-commands.md - processes](references/maestro-commands.md) |
| **List incidents** | [references/maestro-commands.md - incidents](references/maestro-commands.md) |
| **Know all Maestro CLI commands** | [references/maestro-commands.md](references/maestro-commands.md) |
| **Authenticate / manage tenants** | [/uipath:uipath-platform](/uipath:uipath-platform) |
| **Pack / publish / deploy** | [/uipath:uipath-platform](/uipath:uipath-platform) |

## Key Concepts

### Maestro vs Flow

| Aspect | Flow | Maestro |
|--------|------|---------|
| **Authoring** | CLI (`uip flow init`, `.flow` files) | Studio Web (BPMN designer) |
| **CLI scope** | Full lifecycle (init, validate, pack, debug) | Runtime management only |
| **CLI prefix** | `uip flow` | `uip maestro` |
| **Folder parameter** | `--folder-id` | `--folder-key` |
| **Install** | Built into `@uipath/cli` | Requires `uip tools install @uipath/maestro-tool` |

> **Important:** Maestro uses `--folder-key` (not `--folder-id`). This is a different parameter than what the Flow CLI uses. Get folder keys from `uip or folders list --format json`.

### Instance Lifecycle

Maestro process instances transition through these states:

```
Running  -->  Paused   (via pause)
Paused   -->  Running  (via resume)
Running  -->  Cancelled (via cancel)
Faulted  -->  Running  (via retry)
Running  -->  Completed (automatic, on process completion)
```

### CLI output format

All `uip maestro` commands return structured JSON:
```json
{ "Result": "Success", "Code": "...", "Data": { ... } }
{ "Result": "Failure", "Message": "...", "Instructions": "..." }
```

Always use `--format json` for programmatic use.

### The `goto` command — quoting the steps array

The `goto` command takes a JSON array as a positional argument. Be careful with shell quoting:

```bash
# Bash — use single quotes around the JSON array
uip maestro instances goto <instance-id> '["Step1","Step2"]' --format json

# If your step names contain special characters, escape carefully
uip maestro instances goto <instance-id> '["Approval Step","Review Step"]' --format json
```

## References

- **[Maestro CLI Command Reference](references/maestro-commands.md)** — All `uip maestro` subcommands with parameters and examples
- **[UiPath Platform / Authentication](/uipath:uipath-platform)** — Login, tenants, Orchestrator folders (uipath-platform skill)
- **[Flow Authoring](/uipath:uipath-flow)** — Flow project creation and editing (uipath-flow skill)
