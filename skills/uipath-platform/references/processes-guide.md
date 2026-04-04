# Processes Guide

Manage Orchestrator processes via `uip or processes` — create, inspect, update, and roll back.

## Concepts

A **process** binds a package to a folder. Packages are tenant-scoped; processes are folder-scoped. You start jobs from processes, not packages.

```
Package (.nupkg) → Process (folder-scoped) → Job (execution)
```

- **Process key** — GUID. Use with `get`, `update-version`, `rollback`, `jobs start`.
- **Package key** — `PackageId:Version`. From `packages list`.

> **Folder context:** `list` and `create` require `--folder-path` or `--folder-key`. Per-process commands (`get`, `update-version`, `rollback`) use the globally unique process key.

---

## Commands

### 1. List Processes

```bash
uip or processes list --folder-path "<FOLDER_PATH>" --output json
```

| Option | Required | Description |
|---|---|---|
| `--folder-path` / `--folder-key` | Yes (one of) | Folder scope |
| `-s, --search "<NAME>"` | No | Contains match |
| `--limit <N>` | No | Default: `50` |
| `--offset <N>` | No | Default: `0` |

---

### 2. Get Process Details

```bash
uip or processes get <PROCESS_KEY> --output json
```

Returns package version, entry point, input/output argument schemas, process type, job priority, and retention config. Use before starting a job to inspect required inputs.

---

### 3. Create a Process

```bash
uip or processes create \
  --name "<PROCESS_NAME>" \
  --package-id "<PACKAGE_ID>" \
  --package-version "<VERSION>" \
  --folder-path "<FOLDER_PATH>" \
  --output json
```

| Option | Required | Description |
|---|---|---|
| `--name` | Yes | Display name |
| `--package-id` | Yes | Package name without version |
| `--folder-path` / `--folder-key` | Yes (one of) | Target folder |
| `--package-version` | Yes | Version to bind. Use `packages versions` to find available. |
| `--entry-point "<PATH>"` | No | For multi-entry-point packages (e.g., `Workflows/ProcessInvoice.xaml`) |
| `--description` | No | Description |
| `--job-priority` | No | `Low`, `Normal` (default), `High` |
| `--retention-period <DAYS>` | No | 1-180, default: `30` |
| `--retention-action` | No | `Delete` (default), `Archive`, `None` |
| `--retention-bucket` | No | Required when `--retention-action Archive` |

> Run `uip or packages entry-points "<PACKAGE_KEY>" --output json` first for multi-entry-point packages.

---

### 4. Update Process Version

```bash
uip or processes update-version <PROCESS_KEY> --output json
```

Updates to latest version. Pass `--package-version` to pin a specific version (single key only). Multiple keys use bulk API — `--package-version` not supported.

Running jobs are unaffected — only future starts use the new version.

---

### 5. Rollback Process Version

```bash
uip or processes rollback <PROCESS_KEY> --output json
```

Reverts to previous version. Use immediately after a bad update.

---

## Anti-Patterns

- **Do not pass `--package-version` with multiple process keys.** Bulk API does not support version pinning.
- **Do not confuse `--package-id` (name) with process key (GUID).**
- **Do not skip `entry-points` for multi-entry-point packages.** Omitting `--entry-point` uses the default, which may be wrong.
- **Do not assume a process exists after uploading.** You must call `processes create` explicitly.
- **Do not roll back multiple times.** Rollback targets the single previous version. Use `update-version --package-version` for deeper rollbacks.
- **No `processes delete` CLI command.** Use Orchestrator UI.
- **Retention policies are write-only.** `processes get`/`list` do not show retention settings — verify via UI.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `create` fails "package not found" | Wrong `--package-id` | Verify with `packages list --search` |
| `create` fails "folder not found" | Wrong `--folder-path` | Use exact `fullPath` from `folders list` |
| `update-version` fails "version not found" | Version not in feed | Check `packages versions` |
| `rollback` fails "no previous version" | Only one version in history | Use `update-version --package-version` instead |
