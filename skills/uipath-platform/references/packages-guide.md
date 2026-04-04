# Packages, Feeds, and Attachments Guide

Manage packages, feeds, and job attachments via `uip or packages`, `uip or feeds`, and `uip or attachments`.

## Concepts

**Packages** are versioned `.nupkg` artifacts. They are **tenant-scoped** — no folder context needed. To execute: upload package → create process (folder-scoped) → start job.

**Feeds** are NuGet repositories in Orchestrator. The default tenant feed is used when `--feed-id` is omitted.

**Attachments** are files produced by job executions. Find IDs via `uip or jobs get`, download with `uip or attachments download`.

---

## Package Commands

### 1. List Packages

```bash
uip or packages list --output json
```

| Option | Required | Description |
|---|---|---|
| `-s, --search "<NAME>"` | No | Filter by name (contains match) |
| `--feed-id "<FEED_ID>"` | No | Scope to specific feed (default: tenant feed) |
| `-l, --limit <N>` | No | Default: `50` |
| `--offset <N>` | No | Default: `0` |

Returns package key (format: `PackageId:Version`), title, version, metadata.

---

### 2. Get Package Details

```bash
uip or packages get <PACKAGE_KEY> --output json
```

`<PACKAGE_KEY>` format: `PackageId:Version` (e.g., `InvoiceProcessor:2.3.1`).

---

### 3. List Package Versions

```bash
uip or packages versions <PACKAGE_ID> --output json
```

`<PACKAGE_ID>` is the name without version (e.g., `InvoiceProcessor`). Use before `processes update-version` to verify available versions.

---

### 4. List Entry Points

```bash
uip or packages entry-points <PACKAGE_KEY> --output json
```

Returns entry point paths, display names, and input/output argument schemas. Use the path when creating a process with `--entry-point`.

---

### 5. Upload a Package

```bash
uip or packages upload <FILE_PATH> --output json
```

| Option | Required | Description |
|---|---|---|
| `--feed-id "<FEED_ID>"` | No | Target feed (default: tenant feed) |

After upload, the package is available tenant-wide but not executable — create a process to bind it to a folder.

---

## Feed Commands

### List Feeds

```bash
uip or feeds list --output json
```

Returns feed ID, name, type, URL. Use feed ID with `--feed-id` on package commands.

---

## Attachment Commands

### Download Attachment

```bash
uip or attachments download <ATTACHMENT_ID> --output json
```

Tenant-scoped. Get attachment IDs from `uip or jobs get <JOB_KEY> --output json`.

---

## Anti-Patterns

- **Do not skip `entry-points`** for multi-entry-point packages — wrong entry point means wrong workflow executes.
- **Do not confuse `<PACKAGE_ID>` and `<PACKAGE_KEY>`.** ID = name only (`MyProcess`). Key = name:version (`MyProcess:1.0.0`).
- **An uploaded package is not executable.** You must `processes create` to bind it to a folder first.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `upload` fails "package already exists" | Same ID+version in feed | Increment version, rebuild, re-upload |
| `entry-points` returns empty | Wrong key format | Verify format is `PackageId:Version` from `packages list` |
| `versions` returns empty | Package ID not found | Run `packages list` to find exact ID |
