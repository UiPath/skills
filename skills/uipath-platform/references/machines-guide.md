# Machines Guide

Manage Orchestrator machines via `uip or machines` — list, create, edit, delete, and assign to folders.

## Concepts

Machines define where robots execute and how many license slots are allocated. Machines are **tenant-scoped** but must be **assigned to folders** before jobs can run.

**Types:** `Template` (pooled hosts, default) | `Standard` (single specific host)

**Scopes:** `Default` | `Shared` | `PersonalWorkspace` | `Cloud` | `Serverless`

**Slot types:** `Unattended` | `Headless` | `Non-production` | `Testing`

---

## Commands

### 1. List Machines

```bash
uip or machines list --output json
```

| Option | Required | Description |
|---|---|---|
| `--type <TYPE>` | No | `Standard`, `Template` |
| `--scope <SCOPE>` | No | `Default`, `Shared`, `PersonalWorkspace`, `Cloud`, `Serverless` |

---

### 2. Get Machine Details

```bash
uip or machines get <MACHINE_KEY> --output json
```

---

### 3. Create a Machine

```bash
uip or machines create --name "<MACHINE_NAME>" --output json
```

| Option | Required | Description |
|---|---|---|
| `--name` | Yes | Unique within tenant |
| `--type` | No | `Standard` or `Template` (default: `Template`) |
| `--description` | No | Optional |
| `--unattended-slots <N>` | No | Unattended runtime slots |
| `--headless-slots <N>` | No | Headless runtime slots |
| `--non-production-slots <N>` | No | Non-production slots |
| `--testing-slots <N>` | No | Testing slots |

**Example — Template machine with 5 unattended slots:**

```bash
uip or machines create \
  --name "ProductionPool" \
  --type Template \
  --unattended-slots 5 \
  --output json
```

---

### 4. Edit a Machine

```bash
uip or machines edit <MACHINE_KEY> --output json
```

Only provided options are updated. Same slot options as `create` plus `--name` and `--description`.

---

### 5. Delete Machines

```bash
uip or machines delete <MACHINE_KEYS...> --output json
```

> Machine must be unassigned from all folders first.

---

### 6. Assign / Unassign Machine to Folder

```bash
uip or machines assign <MACHINE_KEYS...> --folder-path "<FOLDER_PATH>" --output json
uip or machines unassign <MACHINE_KEYS...> --folder-path "<FOLDER_PATH>" --output json
```

Both accept `--folder-path` or `--folder-key`. Multiple keys use bulk API.

---

### 7. Check Folder Runtime Capacity

```bash
uip or folders runtimes "<FOLDER_PATH>" --output json
```

Shows slot capacity per runtime type. Use to verify assigned machines provide enough slots before starting jobs.

---

## Anti-Patterns

- **Do not delete before unassigning.** Delete fails if machine is still assigned to any folder.
- **Do not assign machines with zero slots.** An assigned machine with no slots provides no runtime capacity.
- **Do not confuse machine `key` (GUID) with `name`.** All commands require the key.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Job stays `Pending` | No machines/slots in folder | `uip or folders runtimes` to check; assign machine or increase slots |
| Delete fails "in use" | Still assigned to folder(s) | Unassign first |
| Create fails "name exists" | Name must be unique per tenant | Choose different name or find existing with `machines list` |
| Assign returns empty results | Invalid `--folder-key` GUID format | CLI does not validate GUID format — ensure it's a valid UUID from `folders list` |
