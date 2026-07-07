# System Activities

Core workflow activities from the `UiPath.System.Activities` package. Two families: **Orchestrator-resource** activities that read/write platform data (assets, credentials, queue items, storage buckets), and **local runtime** activities that act on the robot machine's filesystem and network (compression, modern StudioX file/folder operations, file download).

## Key Activity Types

Orchestrator-resource:
- **Get Asset / Get Orchestrator Asset** — retrieve a text, integer, boolean, or JSON asset value from Orchestrator
- **Get Credential / Get Orchestrator Credential** — retrieve a username/password pair from Orchestrator (returns `String` + `SecureString`)
- **Get Robot Asset** — retrieve an asset value scoped to the executing robot (legacy; replaced by Get Orchestrator Asset in modern folders)
- **Get Transaction Item / Set Transaction Status** — pull the next queue item; report its processing outcome
- **Set Asset / Set Credential** — update an asset or credential in Orchestrator

Local runtime:
- **Compress/Zip Files, Extract/Unzip Files** — build and read `.zip` archives (`CompressionException`)
- **Copy/Move/Rename/Delete Folder, Copy/Rename/Delete File, Create Folder** — modern StudioX file/folder operations (`FileSystemException`)
- **Download File from URL, Wait for Download / Get Latest Downloaded File** — fetch a file over HTTP or wait for a browser download

> The classic `Rename/Move File`, `Append Line`, `Kill Process`, `Invoke Code`, `Invoke Workflow File`, and `Add Queue Item` activities are covered by the **Classic Activities** package, not here.

## Common Failure Patterns

Orchestrator-resource:
- Asset or credential not found (name mismatch, wrong folder)
- Permission denied (robot account lacks View/Edit on Assets)
- Wrong activity for the asset type (Get Asset on a Credential, or vice versa)
- Folder scope mismatch (modern vs classic folders, incorrect `OrchestratorFolderPath`)
- External credential store unreachable (CyberArk, Azure Key Vault, Thycotic)
- Robot not authenticated or not licensed; network/TLS issues between robot and Orchestrator
- Queue activity input invalid, or `Service URL is empty` (no Orchestrator connection)

Local runtime:
- Corrupt/unreadable archive, output already exists, or unsupported compression format
- Filesystem path missing/null, source not found, wrong path type, or destination collision
- Download rest-call/timeout failure, or no file detected / file in use in the watched folder

## Package

NuGet: `UiPath.System.Activities`

Version-specific bugs are documented in the relevant playbooks.
