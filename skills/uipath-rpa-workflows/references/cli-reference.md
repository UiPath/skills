# CLI Tool Reference — RPA

@../shared/cli-reference.md

This file covers RPA-specific commands only. Shared commands are in the file above.

---

## RPA-Specific Commands

| Command | Description | Key Parameters |
|---------|-------------|----------------|
| `uip rpa find-activities` | Search for activities by keyword (global, not limited to installed packages) | `--query` (required), `--tags`, `--limit` (default 10) |
| `uip rpa get-default-activity-xaml` | Get default XAML template for an activity | `--activity-class-name` (non-dynamic) or `--activity-type-id` + `--connection-id` (dynamic) |
| `uip rpa list-workflow-examples` | Search example workflows by service tags | `--tags` (comma-separated, required), `--prefix`, `--limit` |
| `uip rpa get-workflow-example` | Retrieve full XAML content of an example | `--key` (blob path from list results) |
| `uip rpa focus-activity` | Focus an activity in Studio designer | `--activity-id` (IdRef; omit to focus all sequentially) |
| `uip rpa close-project` | Close project in Studio | `--project-dir` (optional) |
| `uip rpa get-errors` | Return validation errors (re-validates by default) | `--file-path` (relative to project dir), `--skip-validation` (cached only) |

## RPA Discovery Tools

| Action | How |
|--------|-----|
| **Explore project files** | `Glob` with `**/*.xaml` pattern |
| **Search XAML content** | `Grep` with regex across `.xaml` files |
| **Explore object repository** | `Glob` `**/*` in `{projectRoot}/.objects/` + `Read` metadata |
| **Get JIT type definitions** | `Read` `{projectRoot}/.project/JitCustomTypesSchema.json` |
| **Activity docs** | See [Step 1.2](../SKILL.md#step-12-discover-activity-documentation-primary-source) for the `.local/docs/` discovery flow |

## Connector Capabilities

For RPA-specific connector workflow patterns (activity/resource discovery, connection management, schema inspection), see [connector-capabilities.md](connector-capabilities.md).
