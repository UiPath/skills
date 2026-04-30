# Solutions (`uip solution`)

Create, pack, publish, deploy, and manage UiPath solution packages.

> For full option details on any command, use `--help` (e.g., `uip solution deploy run --help`).

---

## What is a Solution?

A UiPath Solution is a container that groups multiple automation projects (processes, libraries, tests) into a single deployable unit. Solutions enable:

- **Bundled deployment** -- Deploy multiple projects together as one package
- **Version management** -- Track and version the entire solution as a single entity
- **Configuration management** -- Apply environment-specific configuration at deploy time
- **Multi-environment promotion** -- Move solutions through dev, staging, and production

### Solution File Structure

```
MySolution/
├── MySolution.uipx                       <- Manifest. Source of truth: project list + IDs + StudioMinVersion.
├── <ProjectName>/
│   ├── project.uiproj OR project.json    <- Required for add/import. Type auto-detected.
│   ├── bindings.json                     <- Agent runtime bindings. NOT scanned by refresh.
│   ├── bindings_v2.json                  <- Solution refresh reads this (if it exists).
│   └── ...
├── resources/                            <- Auto-generated on add/import. NEVER hand-edit.
│   └── solution_folder/
│       ├── package/<name>.json           <- Auto-created on add. NOT cleaned by `project remove`.
│       └── process/{process,flow}/<name>.json   <- Auto-created on add. Auto-cleaned on remove.
└── userProfile/<user-uuid>/              <- Appears after first `project remove`.
```

> `.uipx` and `resources/solution_folder/` must always agree on the set of projects. Diffing them is the fastest way to detect a corrupted state — see [develop-solution.md - Field-tested gotchas](develop-solution.md#field-tested-gotchas).
>
> The `.uipx` also carries a `StudioMinVersion` field (e.g. `2025.10.0`). If users hit a version-mismatch when opening the solution, that's the constraint to check.

> **Coded apps are not registered in `.uipx`.** UiPath Coded Web Apps and Coded Action Apps have no `project.uiproj` / `project.json` — `uip solution project add` does not apply, and they are not packed by `uip solution pack`. They deploy independently via `uip codedapp publish` / `deploy`. A coded app directory can sit alongside a solution but is not part of its manifest. See [/uipath:uipath-coded-apps](/uipath:uipath-coded-apps).

---

## Solution Lifecycle

```mermaid
graph LR
    A[new] --> B[project add]
    B --> C[resource refresh]
    C --> D[pack]
    D --> E[publish]
    E --> F[deploy run]
    F --> G[activate]
```

---

## Command Tree

```
uip solution
  ├── new <name>                          Create a new solution directory with .uipx manifest
  ├── delete <solution-id>                Delete a solution from Studio Web
  ├── upload <path>                       Upload solution to Studio Web
  ├── pack <solution> <output>            Pack into a deployable .zip package
  ├── publish <package>                   Upload packed solution to UiPath
  ├── project
  │     ├── add <projectPath> [solutionFile]    Register an existing subfolder in .uipx
  │     ├── remove <projectPath> [solutionFile] Unregister a project from .uipx
  │     └── import --source <path>              Copy external project into solution and register
  ├── resource
  │     ├── list --solution-folder <path>     List local, remote, or all resources
  │     └── refresh --solution-folder <path>  Sync resource declarations from project bindings
  ├── deploy
  │     ├── run -n <name>                 Deploy a published solution package
  │     ├── status <id>                   Check deployment status
  │     ├── list                          List deployments
  │     ├── activate <name>               Activate a deployment
  │     ├── uninstall <name>              Uninstall a deployment
  │     └── config
  │           ├── get <package-name>      Fetch default deploy config
  │           ├── set <file> ...          Set a resource property in config
  │           ├── link <file> <resource>  Link to an existing Orchestrator resource
  │           └── unlink <file> <resource> Remove a resource link
  └── packages
        ├── list                          List published solution packages
        └── delete <name> <version>       Delete a specific package version
```

---

## Workflow References

Each workflow doc covers a multi-command choreography for a specific goal. Load the one that matches your task.

| Workflow | File | Covers |
|----------|------|--------|
| Develop a Solution | [develop-solution.md](develop-solution.md) | Create, add projects, manage resources, upload |
| Pack & Deploy | [pack-and-deploy.md](pack-and-deploy.md) | Pack, publish, deploy run, deploy config |
| Activate & Manage | [activate-and-manage.md](activate-and-manage.md) | Activate, uninstall, packages list/delete |

---

## Related

- **Orchestrator** (`uip or`) -- Folders, processes, jobs, machines. See [orchestrator.md](../orchestrator/orchestrator.md).
- **Resources** (`uip resource`) -- Assets, queues, buckets used by solutions. See [resources.md](../resources/resources.md).
