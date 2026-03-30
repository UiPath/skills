---
name: uipath-coded-apps
description: "End-to-end guide for UiPath Coded Web Applications and Coded Action Apps. TRIGGER when: User wants to create, scaffold, build, debug, or deploy a UiPath coded web app or coded action app; User mentions coded apps, coded action apps, action app, codedapp, web application in a UiPath context; User wants to push/pull code to/from Studio Web; User wants to scaffold a React/Vue/other frontend that connects to UiPath services; User asks about the UiPath TypeScript SDK (@uipath/uipath-typescript), OAuth scopes, or External Application setup; User asks about uip codedapp CLI commands, .uipath directory, app.config.json, or action-schema.json. DO NOT TRIGGER when: User is working with coded agents (Python — use uipath-coded-agents instead); User is working with coded workflows (.cs files — use uipath-coded-workflows instead); User is working with XAML/RPA workflows (use uipath-rpa-workflows instead); User asks about Orchestrator management without coded app context (use uipath-platform instead)."
metadata:
   allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Coded Apps

Build, debug, and deploy UiPath Coded Web Applications and Coded Action Apps using the `uip codedapp` CLI and `@uipath/uipath-typescript` SDK.

## App Types

| Type | Description | Key Difference |
|------|-------------|----------------|
| **Coded Web App** | React/Vue/other frontend hosted on UiPath CDN | User-facing app accessed via a URL |
| **Coded Action App** | React form wired to UiPath Action Center | Rendered inside human task reviews in Maestro/Agent workflows |

**Always ask this before doing anything else:**
> "Are you building a **Coded Web App** (custom frontend deployed to UiPath Cloud) or a **Coded Action App** (form for Action Center human task reviews)?"

## Task Navigation

| I want to... | Read this |
|---|---|
| **Create a new Coded Web App** | [references/create-web-app.md](references/create-web-app.md) |
| **Create a new Coded Action App** | [references/create-action-app.md](references/create-action-app.md) |
| **Debug auth or config issues** | [references/debug.md](references/debug.md) |
| **Push/pull code to Studio Web** | [references/file-sync.md](references/file-sync.md) |
| **Package and deploy** | [references/pack-publish-deploy.md](references/pack-publish-deploy.md) |
| **Full CLI command reference** | [references/commands-reference.md](references/commands-reference.md) |
| **OAuth scopes for SDK services** | [references/oauth-scopes.md](references/oauth-scopes.md) |
| **SDK: Assets, Queues, Buckets, Processes, Tasks** | [references/sdk/orchestrator.md](references/sdk/orchestrator.md) |
| **SDK: Data Fabric (Entities, ChoiceSets)** | [references/sdk/data-fabric.md](references/sdk/data-fabric.md) |
| **SDK: Maestro (Processes, Cases)** | [references/sdk/maestro.md](references/sdk/maestro.md) |
| **SDK: Action Center (Tasks)** | [references/sdk/action-center.md](references/sdk/action-center.md) |
| **SDK: Conversational Agent** | [references/sdk/conversational-agent.md](references/sdk/conversational-agent.md) |
| **SDK: Pagination** | [references/sdk/pagination.md](references/sdk/pagination.md) |
| **UI Patterns (polling, BPMN, HITL)** | [references/patterns.md](references/patterns.md) |

## Critical Rules

- **Always check login status first.** Run `uip login status --format json` before any cloud command. If not logged in, run `uip login`.
- **Never skip the build step.** Verify `dist/` exists before `pack` or `push`. Always run `npm run build` first.
- **Pack → Publish → Deploy order is required.** Each step depends on the previous one producing its output.
- **Bump the version for re-publish.** If the same version already exists in Orchestrator, publish will fail.
- **Action apps require `-t Action` on publish.** Run `uip codedapp publish -t Action` (not the default `Web` type).
- **Never pass access tokens as CLI flags.** JWTs are too long — use the `UIPATH_ACCESS_TOKEN` environment variable instead.
- **Base URL must use the API subdomain.** `https://api.uipath.com` not `https://cloud.uipath.com`. See the table below.
- **`vite.config.ts` must always set `base: './'`.** The platform handles URL routing — apps must use relative asset paths. Do not use a routing name or a sub-path here.
- **Use `getAppBase()` for client-side router basename.** Import from `@uipath/uipath-typescript`. It reads `uipath:app-base` at runtime and falls back to `'/'` locally. Never hardcode a path as the router basename.

## CLI Setup

```bash
# Install the UiPath CLI (run once)
npm install -g @uipath/cli

# Install the coded apps tool
uip tools install @uipath/codedapp-tool

# Resolve uip if not on PATH
UIP=$(command -v uip 2>/dev/null || npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip
$UIP --version
```

Authenticate before any cloud command:

```bash
uip login status --format json         # check if logged in
uip login                              # interactive OAuth (opens browser)
uip login --authority https://alpha.uipath.com   # non-production environments
```

## Deployment Lifecycle

### Web App

| Stage | CLI | Output |
|-------|-----|--------|
| **Auth** | `uip login` | Valid session |
| **Build** | `npm run build` | `dist/` directory |
| **Push** *(optional)* | `uip codedapp push` | Synced to Studio Web |
| **Pack** | `uip codedapp pack dist -n <name> -v <version>` | `.uipath/<name>.<ver>.nupkg` |
| **Publish** | `uip codedapp publish` | `.uipath/app.config.json` |
| **Deploy** | `uip codedapp deploy` | App live at URL |

### Coded Action App

Same pipeline, with one difference at publish:

```bash
uip codedapp publish -t Action    # must use -t Action
```

## Environment Variables

| Variable | Used By | Description |
|----------|---------|-------------|
| `VITE_UIPATH_CLIENT_ID` | Web App SDK | OAuth Client ID from External Application |
| `VITE_UIPATH_SCOPE` | Web App SDK | Space-separated OAuth scopes |
| `VITE_UIPATH_ORG_NAME` | Web App SDK | UiPath organization slug |
| `VITE_UIPATH_TENANT_NAME` | Web App SDK | UiPath tenant name |
| `VITE_UIPATH_BASE_URL` | Web App SDK | Must use API subdomain (see below) |
| `UIPATH_PROJECT_ID` | push / pull | Studio Web project ID |

**Base URL by environment:**

| Environment | Correct Base URL |
|---|---|
| Production (cloud) | `https://api.uipath.com` |
| Staging | `https://staging.api.uipath.com` |
| Alpha | `https://alpha.api.uipath.com` |

## Quick Deploy (Full Pipeline)

**Do NOT pause between steps to ask "should I continue?" — execute the full pipeline. Only stop if you need auth credentials or an app name.**

1. **Auth** — `uip login status --format json`. If not logged in, ask the user for their environment and run `uip login`.
2. **Build** — `npm run build`. Verify `ls dist/`.
3. **Pack** — `uip codedapp pack dist -n <name> -v <version>`. Bump version if previously published.
4. **Publish** — `uip codedapp publish` (add `-t Action` for action apps). Verify `cat .uipath/app.config.json`.
5. **Deploy** — `uip codedapp deploy`. Share the app URL with the user.

## SDK Module Imports

Always import service classes from their **subpath**, never from the root package.

| Subpath | Classes |
|---------|---------|
| `@uipath/uipath-typescript/core` | `UiPath`, `UiPathError`, `UiPathSDKConfig`, `PaginationCursor`, `PaginationOptions`, `PaginatedResponse`, `NonPaginatedResponse` |
| `@uipath/uipath-typescript/entities` | `Entities`, `ChoiceSets` |
| `@uipath/uipath-typescript/tasks` | `Tasks` |
| `@uipath/uipath-typescript/maestro-processes` | `MaestroProcesses`, `ProcessInstances`, `ProcessIncidents` |
| `@uipath/uipath-typescript/cases` | `Cases`, `CaseInstances` |
| `@uipath/uipath-typescript/assets` | `Assets` |
| `@uipath/uipath-typescript/queues` | `Queues` |
| `@uipath/uipath-typescript/buckets` | `Buckets` |
| `@uipath/uipath-typescript/processes` | `Processes` |
| `@uipath/uipath-typescript/conversational-agent` | `ConversationalAgent`, `Exchanges`, `Messages` |

Types, enums, and option interfaces are exported from the **same subpath** as their service class (e.g. `import type { AssetGetResponse } from '@uipath/uipath-typescript/assets'`).

**NEVER** import service classes from the root package (`import { Entities } from '@uipath/uipath-typescript'`) — service classes are only available via subpath imports.

**NEVER** use deprecated dot-chain access (`sdk.entities.getAll()`). Always use constructor DI: `new Entities(sdk)`.

## Key Concepts

### App Config (`.uipath/app.config.json`)

Created by `publish`, consumed by `deploy`. Contains `appName`, `systemName`, `appType`, `deploymentId`, `appUrl`. Do not delete `.uipath/` between publish and deploy.

### Action Schema (`action-schema.json`)

Action apps define a data contract between the form and the Maestro/Agent workflow. It has four sections: `inputs` (read-only data from automation), `outputs` (user-filled fields), `inOuts` (pre-populated but editable), and `outcomes` (submission buttons like Approve/Reject).

## Troubleshooting

See [references/debug.md](references/debug.md) for detailed diagnosis steps.

| Error | Cause | Fix |
|-------|-------|-----|
| `Not authenticated` | No valid session | Run `uip login` |
| `dist/ not found` | App not built | Run `npm run build` |
| `Version already exists` | Same version re-published | Bump version in `pack` |
| `Folder key required` | Missing folder | Set `UIPATH_FOLDER_KEY` or pass `--folderKey` |
| `No packages found` | No `.nupkg` in `.uipath/` | Run `pack` first |
| Login fails / redirect error | OAuth misconfiguration | See [debug.md](references/debug.md) |
| API calls fail with 401/CORS | Wrong base URL | Use `https://api.uipath.com` not `cloud.uipath.com` |
