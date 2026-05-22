# Publishing a UiPath Project

How to take a built `.nupkg` from `uip rpa pack` and get it onto Orchestrator or Studio Web. Covers the standalone-project paths only — solution publish (`.uipx` solutions and `solution publish` deploy lifecycle) lives in [/uipath:uipath-solution](../../uipath-solution/SKILL.md).

## Step 0: Confirm the project is standalone

Before any `pack` / `upload`, check the `INSIDE_SOLUTION` flag from [Step 0 of the rpa skill](../SKILL.md#step-0-resolve-project_dir-and-solution-membership) — the walk-up from `{projectRoot}` looking for an ancestor `.uipx`. If a `.uipx` was found:

**Stop. Hand off to `/uipath:uipath-solution`.**

Running `uip rpa pack` + `uip or packages upload` against a solution-resident project succeeds — it produces a valid standalone `.nupkg` — but the deployed package bypasses the entire solution layer:

- `bindings_v2.json` entries are NOT bundled into the package; Orchestrator's `resourceOverwrites` never gets populated.
- Solution-scoped `UiPath.DataService.Activities` lose their `X-UiPath-FolderPath` injection (no `Entity.<name>.folderPath` binding to read), and Folder-scoped reads/writes silently collapse to tenant scope or 404 — depending on whether a tenant-level entity with the same name happens to exist.
- Folder-scoped Storage Bucket, Asset, Queue, and Connection bindings degrade the same way.

The correct path for a solution-resident project is `solution pack` → `solution publish` → `solution deploy`. See [uipath-solution/references/operate/pack-and-deploy.md](../../uipath-solution/references/operate/pack-and-deploy.md). For entity-discovery commands referenced by Data Service activities, see [activity-docs/UiPath.DataService.Activities/25.9/overview.md § Discovering values for XAML](activity-docs/UiPath.DataService.Activities/25.9/overview.md#discovering-values-for-xaml).

`INSIDE_SOLUTION=false` (no ancestor `.uipx`) → continue below.

## Pick a path

| Goal | Path | Reference | If `INSIDE_SOLUTION=true` |
|---|---|---|---|
| Run the project as an Orchestrator process / link as a Test Manager automation | **Pack → Orchestrator package upload** | This file § Pack → Upload | Test Manager link still uses tm flow (no solution wrapper exists). For runtime deploy: hand off to uipath-solution. |
| Edit / visualize in Studio Web | **Solution upload** | [uipath-solution](../../uipath-solution/SKILL.md) (solution upload) | → uipath-solution |
| Deploy a packed solution (`.uipx`) to Orchestrator with the deployment lifecycle | **Solution publish** | [uipath-solution](../../uipath-solution/references/operate/pack-and-deploy.md) | → uipath-solution |

This file documents the first row only — the legacy Orchestrator package feed flow that `uip tm testcases link-automation` requires.

## Pack → Upload (Orchestrator process flow)

The end-to-end is two CLI calls.

### Step 1 — Pack the project

```bash
uip rpa pack "<PROJECT_DIR>" "<OUTPUT_DIR>" --output json
```

| Argument | Position | Notes |
|---|---|---|
| `<PROJECT_DIR>` | Positional 1 | Path to the project (folder containing `project.json`). |
| `<OUTPUT_DIR>` | Positional 2 | Directory the `.nupkg` is written to. Must exist. |

Common optional flags (run `uip rpa pack --help` for the full set):
- `--package-version <SEMVER>` — pin the version. Defaults to the project version.
- `--skip-analyze` — skip the workflow-analyzer pass. Use only for known-clean builds.
- `--governance-file-path <PATH>` — apply a governance policy during pack.

Output (JSON) emits `OutputPath` — the full `.nupkg` path. Capture it for Step 2.

> **`uip rpa pack` does NOT accept `--project-path` or `--project-dir`.** Both arguments are positional. The `--project-dir` flag exists on most other `uip rpa` subcommands but not here.

### Step 2 — Upload to Orchestrator

```bash
uip or packages upload "<NUPKG_PATH>" --output json
```

| Argument / Flag | Required | Notes |
|---|---|---|
| `<NUPKG_PATH>` | Yes (positional) | Path to the `.nupkg` produced by `pack`. |
| `--feed-id <UUID>` | No | Target a non-default feed. Defaults to the tenant feed. |
| `-t, --tenant <NAME>` | No | Override the authenticated tenant. |

Output JSON includes the package `Id` (the package name Orchestrator stores) and `Version`. Hold on to the `Id` — it is the `--package-name` value that `uip tm testcases link-automation` and `uip or processes create` need.

> **There is no `uip or packages publish` or `uip rpa publish`.** Agents that try those names get "unknown command". Pack writes a file; upload pushes that file. Two commands, two domains (`rpa`, `or`).

## Discovery cheatsheet

Folder key (UUID — required by `processes create`, `link-automation`, etc.):

```bash
uip or folders list-current-user --output json
```

The returned `Key` is the UUID; the `FullyQualifiedName` is the human path. Either is accepted by `--folder-path` / `--folder-key` — most other CLI calls require the UUID.

After upload, list the new package version:

```bash
uip or packages list --output json
```

## End-to-end: link a coded test case to Test Manager

For the full Pack → Upload → Link → Execute pipeline targeted at Test Manager (folder-key discovery, picking the right `--test-name`, etc.), see [/uipath:uipath-test § publish-and-link-guide.md](../../uipath-test/references/publish-and-link-guide.md).

## Common pitfalls

- **`uip solution publish` expects a packed `.zip`, not a project directory.** Solutions: run `uip solution pack` first, then `uip solution publish "<ZIP_PATH>"`. Single projects: use `uip or packages upload` instead.
- **Confusing `solution upload` and `solution publish`.** `upload` pushes to Studio Web (browser editing). `publish` pushes a packed solution `.zip` to the Orchestrator solution feed for `solution deploy`. They are NOT interchangeable. See [uipath-solution](../../uipath-solution/SKILL.md) for the decision tree.
- **Re-uploading the same version.** Orchestrator rejects duplicate `<id>:<version>` uploads. Bump `--package-version` (or `project.json` `projectVersion`) before re-packing.
- **Packing a solution-resident project as a standalone `.nupkg`.** Succeeds but the runtime cannot resolve `Entity.<name>.folderPath` — the bindings are not deployed alongside a standalone package. Symptom: `X-UiPath-FolderPath` header missing at runtime; Folder-scoped Data Service activities hit tenant-level entities or return 404. Re-check Step 0 — if `INSIDE_SOLUTION=true`, use the `uip solution` path instead.
- **`pack` succeeds but `analyze` ran with errors.** A successful pack with errors in the analyzer log usually means warnings only. Re-run `uip rpa analyze --project-dir "<PROJECT_DIR>"` if you need a clean failure / pass signal.
