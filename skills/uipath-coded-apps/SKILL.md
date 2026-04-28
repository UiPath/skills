---
name: uipath-coded-apps
description: "[PREVIEW] UiPath Coded Web Apps & Coded Action Apps (uip codedapp, app.config.json, action-schema.json, @uipath/uipath-typescript SDK). Scaffold, build, debug, deploy. For .cs/XAML→uipath-rpa, Python→uipath-agents."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Coded Apps

Build, debug, and deploy UiPath Coded Web Applications and Coded Action Apps using the `uip codedapp` CLI and `@uipath/uipath-typescript` SDK.

## When to Use This Skill

- User wants to **build, debug, or deploy** a UiPath Coded Web App or Coded Action App
- User asks about `uip codedapp` commands, `.uipath/` directory, `app.config.json`, or `action-schema.json`
- User wants to **scaffold** a new React/Vue frontend for UiPath Cloud or an Action Center form
- User wants to **push/pull source** between local and Studio Web
- User wants to use the `@uipath/uipath-typescript` SDK from a coded app
- User wants to run the **full pipeline** (build → pack → publish → deploy)

## App Types

| Type | Description | Key Difference |
|------|-------------|----------------|
| **Coded Web App** | React/Vue/other frontend hosted on UiPath CDN | User-facing app accessed via a URL |
| **Coded Action App** | React form wired to UiPath Action Center | Rendered inside human task reviews in Maestro/Agent workflows |

## Critical Rules

1. **Identify the app type before doing anything else.** Ask: *"Are you building a **Coded Web App** (custom frontend deployed to UiPath Cloud) or a **Coded Action App** (form for Action Center human task reviews)?"* The two paths diverge on scaffolding, redirect URI, and publish flag — do not guess.
2. **Always check login status first.** Run `uip login status --output json` before any cloud command. If not logged in, run `uip login`.
3. **Never skip the build step.** Run `npm run build` after scaffolding (to verify the scaffold compiles) and again before `pack` or `push` (to produce the deployable `dist/`). Verify `dist/` exists each time.
4. **Pack → Publish → Deploy order is required.** Each step depends on the previous one producing its output.
5. **Bump the version for re-publish.** If the same version already exists in Orchestrator, publish will fail.
6. **Action apps require `-t Action` on publish.** Run `uip codedapp publish -t Action` (not the default `Web` type).
7. **Never pass access tokens as CLI flags.** JWTs are too long — use the `UIPATH_ACCESS_TOKEN` environment variable instead.
8. **Base URL must use the API subdomain.** `https://api.uipath.com` not `https://cloud.uipath.com`. See the table below.
9. **`vite.config.ts` must always set `base: './'`.** The platform handles URL routing — apps must use relative asset paths. Do not use a routing name or a sub-path here.
10. **Use `getAppBase()` for client-side router basename.** Import from `@uipath/uipath-typescript`. It reads `uipath:app-base` at runtime and falls back to `'/'` locally. Never hardcode a path as the router basename.

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
| **SDK: Import paths & subpath exports** | [references/sdk/imports.md](references/sdk/imports.md) |
| **SDK: Assets, Queues, Buckets, Processes, Jobs, Attachments** | [references/sdk/orchestrator.md](references/sdk/orchestrator.md) |
| **SDK: Data Fabric (Entities, ChoiceSets)** | [references/sdk/data-fabric.md](references/sdk/data-fabric.md) |
| **SDK: Maestro (Processes, Cases)** | [references/sdk/maestro.md](references/sdk/maestro.md) |
| **SDK: Action Center (Tasks)** | [references/sdk/action-center.md](references/sdk/action-center.md) |
| **SDK: Conversational Agent** | [references/sdk/conversational-agent.md](references/sdk/conversational-agent.md) |
| **SDK: Pagination** | [references/sdk/pagination.md](references/sdk/pagination.md) |
| **UI Patterns (polling, BPMN, HITL)** | [references/patterns.md](references/patterns.md) |

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
uip login status --output json         # check if logged in
uip login                              # interactive OAuth (opens browser)
uip login --authority https://alpha.uipath.com   # non-production environments
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

1. **Auth** — `uip login status --output json`. If not logged in, ask the user for their environment and run `uip login`.
2. **Build** — `npm run build`. Verify `ls dist/`.
3. **Pack** — `uip codedapp pack dist -n <name> -v <version>`. Produces `.uipath/<name>.<version>.nupkg`. Bump version if previously published.
4. **Publish** — `uip codedapp publish` (add `-t Action` for action apps). Verify `cat .uipath/app.config.json`.
5. **Deploy** — `uip codedapp deploy`. Share the app URL with the user.

## SDK Module Imports

See [references/sdk/imports.md](references/sdk/imports.md) for the subpath ↔ class mapping, type import conventions, and anti-pattern examples. Core rules are listed under **Anti-patterns** below.

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
| `Folder key required` | Missing folder for CLI deploy | Set `UIPATH_FOLDER_KEY` or pass `--folderKey`. See note below. |
| `No packages found` | No `.nupkg` in `.uipath/` | Run `pack` first |
| Login fails / redirect error | OAuth misconfiguration | See [debug.md](references/debug.md) |
| API calls fail with 401/CORS | Wrong base URL | Use `https://api.uipath.com` not `cloud.uipath.com` |

> **Folder identifier names differ across CLI and SDK.** The CLI uses `UIPATH_FOLDER_KEY` / `--folderKey` (string) and applies only to `uip codedapp deploy`. SDK methods use different parameters: Maestro services (`MaestroProcesses`, `ProcessInstances`, `Cases`) take `folderKey` (string GUID), Orchestrator services (`Assets`, `Queues`, `Buckets`, `Processes`) take `folderId` (number). Do not pass the CLI env var into SDK calls. To bridge from a Maestro `folderKey` to an Orchestrator `folderId`, see [sdk/maestro.md](references/sdk/maestro.md) — and **never** `parseInt(folderKey)`, the GUID is not numeric.

## Completion Output

When you finish a task, report only what's applicable to the work actually done:

1. **What was done** — files created, edited, or deleted (list paths); CLI commands run
2. **Stage reached** — one of: scaffolded / built / packed / published / deployed
3. **Artifacts produced** (report only the ones that actually exist):
   - `dist/` — if `npm run build` was run
   - `.uipath/<name>.<version>.nupkg` — if `pack` was run
   - `.uipath/app.config.json` with `deploymentId` — if `publish` was run
   - Live deployment URL (`appUrl` from `app.config.json`) — if `deploy` was run
   - External Application client ID — if one was created this session
4. **Next steps**, depending on where the task stopped:
   - **Scaffolded only:** `cd <app-name> && npm run dev` to run locally
   - **Built but not packed:** ready to `uip codedapp pack` when the user wants to deploy
   - **Published but not deployed:** run `uip codedapp deploy` to go live
   - **Deployed (Web):** open/share the deployment URL; verify sign-in flow
   - **Deployed (Action):** the app will render in Action Center human tasks triggered by Maestro/Agent workflows matching the routing name
5. **Open issues** — any auth failures, scope mismatches, missing folder key, skipped steps, or errors left unresolved

If a later stage was requested but skipped (e.g., user asked to deploy but only `publish` succeeded), call it out explicitly in the next-steps section.

## Anti-patterns

These pitfalls are not already covered by the Critical Rules. For rules stated as positive requirements, see the **Critical Rules** section at the top.

- **Don't import service classes from the package root** — use the subpath (e.g., `@uipath/uipath-typescript/assets`).
- **Don't use the deprecated dot-chain `sdk.entities.getAll()`** — use constructor DI: `new Entities(sdk)`.
- **Don't delete `.uipath/` between `publish` and `deploy`** — `deploy` reads `app.config.json` written by `publish`.
