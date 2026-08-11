---
name: uipath-solution
description: "Always invoke for `.uipx` files. UiPath Solution lifecycle via `uip solution`: init, pack, publish, deploy, activate, uninstall, upload, and the projects and resources inside a multi-project solution — plus diagnosing any of those failing. Also consuming a published Solution from the tenant feed. For PDD/SDD design→uipath-planner. For non-solution Orchestrator/IS/auth/traces→uipath-platform. For .xaml/.cs→uipath-rpa. For .flow→uipath-maestro-flow. For .bpmn→uipath-maestro-bpmn. For agent.json/.py agents→uipath-agents. For standalone coded apps→uipath-coded-apps."
when_to_use: "Fires on .uipx, 'uip solution', 'pack/publish/deploy the solution', activate, deploy configs, environment promotion, Solution scope or Solution Folder, and solution resources (a queue/asset/bucket/connection declared in the solution). Also fires to diagnose solution build-time faults: pack/publish/deploy/activate errors, stale or missing bindings, unresolved resources, deploy error codes, publish name+version collisions. Build-time and CLI faults belong here; faulted Orchestrator jobs at runtime→uipath-troubleshoot. Load BEFORE editing .uipx or running uip solution commands."
---

# UiPath Solution — `uip solution` lifecycle

Create, pack, publish, deploy, and manage UiPath Solution packages (`.uipx`) via the `uip solution` CLI surface. A Solution bundles deployable automation projects (processes, tests, agents, flows, cases, apps, and API workflows) into a single unit, and is itself a versioned unit other environments consume. Code shared at build time ships as a pinned Library package instead — [Project Structure](references/develop-solution.md#project-structure--what-belongs-in-the-uipx) decides which.

> **Use the CLI. Don't roll your own REST for solution ops.** Hand-rolling HTTP calls misses the `X-UIPATH-OrganizationUnitId` folder header, OData filter shape, pagination envelope, `pipelinesInstall` deploy semantics, retry behavior, and the `Result/Code/Data` output contract. The CLI is the source of truth.

> **Platform support.** Solutions runs on Automation Cloud and on self-hosted Automation Suite **from `2.2510.0` onward**; not on Standalone Orchestrator. Available project types vary by AS version (Maestro self-hosted only from `2.2510.2`). Compat matrix + project-type-by-version table → [Solution Overview — Platform availability](references/solution-overview.md#platform-availability).

## When to Use This Skill

- User has a `.uipx` solution and wants to pack / publish / deploy / activate / upload
- User wants to create a new solution (`uip solution init`), add or remove projects, or refresh solution resources
- User asks to set up a CI/CD pipeline that builds, publishes, and deploys a UiPath solution
- User mentions deploy configs, environment promotion, or activating a deployed solution
- A skill or main agent detected a `.uipx` file and redirected the user here

**Skip this skill** when:
- The task is PDD → SDD architecture/design (sdd.md / pdd.md) — load `uipath-planner`.
- The deployable is a single non-solution package. An RPA Library uses `uip rpa pack` → `uip or libraries upload`; a standalone coded app uses its own pack/publish/deploy lifecycle. Route authoring to the relevant specialist.
- The task is authoring or publishing the shared Library itself, not the Solution that consumes it — load `uipath-rpa`.
- The task is non-solution Orchestrator work (folders, jobs, assets, queues, IS connections) — load `uipath-platform`.

## CLI Surface Probe

Before the first `uip solution …` command in a session, probe the exact surfaces needed by the task. Command groups and individual argument shapes can drift independently:

```bash
uip solution init --help --output json
uip solution project --help --output json
uip solution project import --help --output json
```

- `init` returns `Success` → post-rename lifecycle surface (default). Use `init`; an `unknown command` result means use the `new` fallback below.
- `project` returns `Success` → stable singular project group. If it is unknown, probe `uip solution projects --help --output json` and translate the group name when that succeeds.
- `project import` usage contains a required `<source>` argument → pass the source positionally (current stable surface). If help instead exposes `--source <path>`, use that option. Never guess between the two forms.
- Any later `unknown command` or `unknown option` → probe that exact command with `--help --output json`, then adapt to the returned `Usage` and `Options`.
- `command not found` / `uip: not found` / `'uip' is not recognized` → CLI not installed. Tell the user to run `npm install -g @uipath/cli`, then `uip login`, and abort the work until those succeed.

| Post-rename (default) | Pre-rename equivalent |
|---|---|
| `uip solution init <NAME>` | `uip solution new <NAME>` |
| `uip solution deploy run --parent-folder-path <PATH>` | `uip solution deploy run --folder-path <PATH>` |
| `uip solution deploy run --parent-folder-key <KEY>` | `uip solution deploy run --folder-key <KEY>` |
| `uip solution project add\|import\|list\|remove` | `uip solution projects add\|import\|list\|remove` |

For the current stable surface, `project add` takes `<project-path> [solutionFile]`, `project import` takes `<source>` plus optional `--solutionFile <path>`, and resource commands use the plural `resources`. Treat the live help output as authoritative rather than assuming the rest of the surface changed in lockstep with `init`.

## Critical Rules

1. **Probe the CLI surface before the first `uip solution` command in a session.** Probe `init`, the `project`/`projects` group, and each argument-sensitive command you will use (especially `project import`) with `--help --output json`. Re-probe the exact command on any `unknown command` or `unknown option`; do not extrapolate one rename to unrelated commands.
2. **Always use `--output json`** for `uip solution` commands whose output you parse. JSON is compact and stable; the default for non-interactive runs.
3. **Use the CLI, never roll your own REST for solution operations.** Hand-rolled HTTP calls miss the `X-UIPATH-OrganizationUnitId` header, OData filter shape, pagination envelope, and `pipelinesInstall` deploy semantics. Only fall through to REST after confirming no `uip solution` command covers the task.
4. **Never hand-edit `resources/solution_folder/`.** It's auto-generated by `uip solution project add` / `import` and auto-cleaned by `project remove`. Manual edits desync from `.uipx` and produce silent failure modes. See [scenarios/manual-edits.md](references/scenarios/manual-edits.md).
5. **`.uipx` and `resources/solution_folder/` must always agree on the project set.** Diffing them is the fastest way to detect corrupted state. If they disagree, fix via `uip solution project add/remove` — never by editing either side directly.
6. **Run `uip solution resources refresh` before `pack` or `upload`.** Bundled artefact files and `userProfile/<userId>/debug_overwrites.json` must reflect current cloud state. Skipping refresh ships stale bindings.
7. **Decide project structure before `init`, by when consumers need the code.** Run-time deployables become `.uipx` members inside the solution root; code shared at **build time** ships as a Library package pinned by exact version, with its source **outside** the solution root — scaffolders auto-register anything inside it. `project add` / `import` reject a `Library`; trust that error over any `--help` text or generated project-type table. See [Project Structure](references/develop-solution.md#project-structure--what-belongs-in-the-uipx). A published Solution is itself consumable — [Consuming a Published Solution](references/pack-and-deploy.md#consuming-a-published-solution).
8. **AppV2 coded apps register in `.uipx` when authored inside a solution.** `uip codedapp init` is the solution-side scaffolding entry point — run it from **inside a `.uipx` solution**. It writes `project.uiproj` (`ProjectType: "AppV2"`) + `webAppManifest.json`, nests source under `source/dist/`, and auto-registers as `Type: "AppV2"` — emitting `resources/solution_folder/app/{Coded,CodedAction}/`. `uip solution project add` / `uip solution project import` cover existing AppV2 folders too — both read `webAppManifest.config.isActionApp` to pick `Coded` / `CodedAction` subType (defaults `Coded` for legacy folders with no manifest). `uip solution pack` bundles them; `uip solution deploy run` provisions them. Standalone coded apps are a **different** lifecycle — scaffold them with `npx create-vite@latest` (not `uip codedapp init`), keep a flat `dist/` at the project root, and deploy via `uip codedapp pack` → `uip codedapp publish` → `uip codedapp deploy`. See [/uipath:uipath-coded-apps](/uipath:uipath-coded-apps).
9. **Verify the artifact after every CLI mutation.** Read `project.json`, `.uipx`, or `uip solution deploy status` output — exit codes lie. Verification is additional; it does not replace requested read-only list commands. If the user asks to show or list registered projects, solution resources, packages, deployments, or statuses, run the matching `uip solution ... list/status --output json` command and then inspect files only as a secondary sanity check.
10. **For multi-environment promotion, switch tenants with `uip login tenant set <tenant>` and pass a per-environment deploy config via `--config-file <path>`.** The same packed `.uipx` deploys to dev/staging/prod — the environment differs by the target tenant and the config file (generated with `deploy config get`, edited with `config set` / `config link`), not by a different package. There is no `-c <CONFIG_KEY>` flag.

## Workflow

The typical lifecycle for a UiPath Solution:

```
1. init / project add  → Create solution, register projects (.uipx + resources/solution_folder/)
2. resources refresh   → Sync bundled artefacts and debug overwrites with cloud state
3. (optional) restore  → Resolve NuGet deps in place (incl. authenticated Orchestrator feeds); login first
4. pack                → Produce deployable .zip package
5. login               → uip login (if not already authenticated)
6. publish             → Upload packed solution to UiPath
7. deploy run          → Promote to Orchestrator (auto-activates by default)
8. (optional) activate → Use --skip-activate on deploy, then activate explicitly
```

When a member consumes a Library, confirm the exact pinned version exists in the target tenant's library feed before `restore` / `pack` — a consumer cannot restore against a feed missing its pin. See [Pinned Library versions must exist in the target feed](references/develop-solution.md#pinned-library-versions-must-exist-in-the-target-feed).

> **`restore` is an optimization, not a requirement.** `pack` restores dependencies internally, so a separate `restore` step is only useful when you want deps resolved up front — most often in CI (`login → restore → pack`) to fail fast on a missing feed before the heavier pack runs. `restore` takes a `<solutionPath>` only (solution dir with a `.uipx`, or a `.uis` file), resolves deps in place, and does **not** produce a package. It needs an authenticated session to reach private Orchestrator feeds, so run `uip login` before it.

> **AppV2 coded apps in the solution flow through `uip solution`, not `uip codedapp` directly.** When a coded-app project has `Type: "AppV2"` in `.uipx`, `uip solution pack` bundles its `.nupkg` and `uip solution deploy run` provisions it in the deployment folder — no separate `uip codedapp pack` / `publish` / `deploy` step. Standalone coded apps (scaffolded outside any solution via `npx create-vite`, flat `dist/` at the project root, no `project.uiproj` / `webAppManifest.json`) use the direct `codedapp` path instead. See `uipath-coded-apps` for the standalone lifecycle and for authoring an AppV2 project inside a solution via `uip codedapp init`.

Two distinct distribution paths from the same source:
- **`pack` → `publish` → `deploy run`** — promotes a versioned package to Orchestrator.
- **`upload`** — pushes the solution to Studio Web for browser-based debugging only. Does not produce a published package and cannot be deployed via `deploy run`.

Authentication is a prerequisite. Check `uip login status --output json` before any work; if not logged in, ask the user to run `uip login` (interactive browser flow). See `uipath-platform` for full auth options (interactive OAuth, client credentials, tenant switching).

This skill is the terminal step of an SDD-driven build: after `uipath-planner` produces the SDD and derives the task list, and implementation specialists build the projects, the `.uipx` is packed and shipped here.

## Reference Navigation

| File | Purpose |
|------|---------|
| [Solution Overview](references/solution-overview.md) | What a Solution is, `.uipx` manifest, file structure, lifecycle diagram, command tree |
| [Develop a Solution](references/develop-solution.md) | `uip solution init / project add / import / remove / resources refresh / resources add / resources remove / resources edit`; field-tested gotchas |
| [Pack and Deploy](references/pack-and-deploy.md) | `restore / pack / publish / deploy run`, deploy configs, CI/CD pipeline patterns |
| [Activate and Manage](references/activate-and-manage.md) | `deploy activate / status / uninstall`, environment management |
| [Scenarios Index](references/scenarios.md) | Failure modes and edge cases — manual edits, shared resources, virtual resources, name collisions |

## Anti-patterns

1. **Hand-rolling REST calls for `pack`, `publish`, `deploy run`, or `activate`.** The `uip solution` CLI handles auth, folder headers, pipeline semantics, and pagination correctly. Reach for REST only after confirming no command covers the task.
2. **Editing `resources/solution_folder/` directly.** It is auto-generated and auto-cleaned. Manual edits desync from `.uipx`. Use `uip solution project add/remove` instead.
3. **Skipping `uip solution resources refresh` before `pack` or `upload`.** Ships stale bindings and debug-overwrite state.
4. **Running `uip codedapp pack` / `publish` / `deploy` on an AppV2 project that's already registered in `.uipx`.** Once registered as `Type: "AppV2"`, the coded app is part of the solution — `uip solution pack` / `uip solution publish` / `uip solution deploy run` handle it. Direct `uip codedapp publish` bypasses the solution's deploy config (external client ID, routing name, action schema) and creates a duplicate registration. Use `uip codedapp` directly only for standalone coded apps scaffolded with `npx create-vite` (no `.uipx` in the tree, no `project.uiproj` / `webAppManifest.json`).
5. **Creating a new `.uipx` per environment instead of using deploy configs.** One packed solution promotes to dev/staging/prod via a per-environment `--config-file` (and `uip login tenant set` to target the tenant). Different `.uipx` files per environment defeats version tracking.
6. **Using `uip solution upload` (Studio Web) as a deployment path.** Upload is for browser-based debugging only — it does not produce a published package and cannot be promoted via `deploy run`. Use `pack` → `publish` → `deploy run` for real deploys. `upload` also lands the solution in Studio Web's **Cloud workspace** tab — not the Local tab; SW's Local tab is a separate registration not addressable by `uip solution`.
7. **Trusting exit codes alone after a mutation.** Always read the artefact (`project.json`, `.uipx`, deploy status) — a non-zero exit may indicate partial state and a zero exit can mask warnings.
8. **Putting build-time-shared code in the `.uipx` instead of pinning it.** `project add` / `import` reject a `Library`, and its source inside the solution root risks scaffolder auto-registration. Pack it, upload it to the library feed, and reference the exact version from every consumer's `project.json` — [Project Structure](references/develop-solution.md#project-structure--what-belongs-in-the-uipx).
