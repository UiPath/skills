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
  - Handling conflicts and overwrites

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

## Workflow Commands

### Pull

Download remote project files to your local environment:

```bash
uv run uipath pull
```

**Options:**
- `--overwrite` - Automatically replace conflicting local files without confirmation

**Requirements:**
- `UIPATH_PROJECT_ID` must be set in `.env` file or as environment variable

### Push

Upload local project files to remote storage, syncing your local structure with the remote:

```bash
uv run uipath push
```

**Options:**
- `--nolock` - Skip `uv lock` during sync
- `--overwrite` - Bypass confirmation prompts for overwriting remote files
- `--ignore-resources` - Skip resource imports during push

**What It Does:**
1. Updates existing files that have changed
2. Uploads new files
3. Deletes remote files that no longer exist locally

**Requirements:**
- `UIPATH_PROJECT_ID` must be set in `.env` file or as environment variable

## Bidirectional Synchronization

The push and pull commands enable seamless bidirectional sync:

```
Local Project ↔ Remote Storage (Studio Web)
    ↓              ↑
  push          pull
    ↑              ↓
```

## Common Workflows

### Clone a Remote Project Locally

Create `.env` file with:
```env
UIPATH_PROJECT_ID=<project-id>
```

Then pull:
```bash
uv run uipath pull
```

### Sync Local Changes to Remote

```bash
uv run uipath push
```

### Force Overwrite Remote Files

```bash
uv run uipath push --overwrite
```

### Merge Remote Changes (with Overwrite Protection)

```bash
uv run uipath pull
# Review changes, then push your local state
uv run uipath push --overwrite
```

## Next Steps

- **Setting up authentication?** See [Authentication Setup](/uipath-coded-agents:authentication)
- **Building your first agent?** See [Building Agents](/uipath-coded-agents:build)
- **Deploying to the cloud?** See [Deployment](/uipath-coded-agents:deploy)
