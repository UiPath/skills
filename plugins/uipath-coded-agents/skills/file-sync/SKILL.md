---
description: Sync project files between local and remote storage using push and pull
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# File Synchronization for UiPath Projects

Synchronize your UiPath project files between local development environments and remote storage with push and pull operations.

## Documentation

- **[File Sync Guide](references/file-sync.md)** - Complete file synchronization workflow
  - `uipath push` - Upload local files to remote storage
  - `uipath pull` - Download remote files to local environment
  - Bidirectional synchronization
  - Conflict resolution and overwrites
  - Common workflows and troubleshooting

## Quick Start

1. **[Authenticate](/uipath-coded-agents:authentication)** with UiPath

2. Create `.env` file with your project ID:

   ```env
   UIPATH_PROJECT_ID=<your-project-id>
   ```

3. Pull remote files to local:

   ```bash
   uv run uipath pull
   ```

4. Make local changes to your project files

5. Push local files to remote:

   ```bash
   uv run uipath push
   ```

## Command Reference

| Command | Purpose | Key Options |
|---------|---------|-------------|
| `uv run uipath pull` | Download remote files to local | `--overwrite` |
| `uv run uipath push` | Upload local files to remote | `--overwrite`, `--nolock`, `--ignore-resources` |

> **Note:** Push mirrors local to remote — it updates, uploads new files, and **deletes** remote files not present locally. See the [File Sync Guide](references/file-sync.md) for details on conflict resolution and common workflows.

## Next Steps

- **Setting up authentication?** See [Authentication Setup](/uipath-coded-agents:authentication)
- **Building your first agent?** See [Building Agents](/uipath-coded-agents:build)
- **Deploying to the cloud?** See [Deployment](/uipath-coded-agents:deploy)
