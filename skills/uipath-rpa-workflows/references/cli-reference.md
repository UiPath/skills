# CLI Tool Reference — RPA

@../shared/cli-reference.md

This file covers RPA-specific commands only. Shared commands are in the file above.

---

## RPA-Specific Commands

### find-activities

Search for activities by keyword. Global search — not limited to installed packages.

```bash
uip rpa find-activities --query "<KEYWORD>" --output json --use-studio
uip rpa find-activities --query "<KEYWORD>" --tags "<TAGS>" --limit 20 --output json --use-studio
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--query` | Yes | Search keyword |
| `--tags` | No | Filter by tags |
| `--limit` | No | Max results (default 10) |

---

### get-default-activity-xaml

Get the default XAML template for an activity. Two modes depending on whether the activity is dynamic (connector-backed) or not.

```bash
# Non-dynamic activity:
uip rpa get-default-activity-xaml --activity-class-name "<FULLY_QUALIFIED_CLASS>" --output json --use-studio

# Dynamic activity (connector-backed):
uip rpa get-default-activity-xaml --activity-type-id "<TYPE_ID>" --connection-id "<CONN_ID>" --output json --use-studio
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--activity-class-name` | One mode | Fully qualified class name (non-dynamic) |
| `--activity-type-id` | One mode | Activity type ID (dynamic) |
| `--connection-id` | No | Connection ID for dynamic activities |

---

### list-workflow-examples

Search example workflows by service tags.

```bash
uip rpa list-workflow-examples --tags "service1,service2" --output json --use-studio
uip rpa list-workflow-examples --tags "service1" --prefix "<PREFIX>" --limit 20 --output json --use-studio
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--tags` | Yes | Comma-separated service tags |
| `--prefix` | No | Filter by name prefix |
| `--limit` | No | Max results (default 10) |

---

### get-workflow-example

Retrieve the full XAML content of an example workflow.

```bash
uip rpa get-workflow-example --key "<BLOB_PATH>" --output json --use-studio
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--key` | Yes | Blob path from `list-workflow-examples` results |

---

### focus-activity

Focus an activity in the Studio designer view.

```bash
uip rpa focus-activity --activity-id "<IDREF>" --output json --use-studio
uip rpa focus-activity --output json --use-studio
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--activity-id` | No | Activity IdRef. Omit to focus all activities sequentially. |

---

### close-project

Close the current project in Studio.

```bash
uip rpa close-project --output json --use-studio
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--project-dir` | No | Project directory (defaults to current working directory) |

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
