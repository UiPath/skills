---
name: uipath-coded-apps
description: "UiPath Coded Web Apps, Action Apps (app.config.json, action-schema.json), and NLP-driven dashboards. Build apps via uip codedapp + TS SDK. Generate agent-health, error-rate, invocation, latency, KPI, or observability dashboards from natural-language prompts using Insights RTM API. For .cs/XAML→uipath-rpa, Python→uipath-agents, .flow→uipath-maestro-flow."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, Task
---

# UiPath Coded Apps

> **Preview** — skill is under active development; surface and behavior may change.

Build, debug, and deploy UiPath Coded Web Applications and Coded Action Apps using the `uip codedapp` CLI and `@uipath/uipath-typescript` SDK.

## When to Use This Skill

- User wants to **build, debug, or deploy** a UiPath Coded Web App or Coded Action App
- User asks about `uip codedapp` commands, `.uipath/` directory, `app.config.json`, or `action-schema.json`
- User wants to **scaffold** a new React/Vue frontend for UiPath Cloud or an Action Center form
- User wants to **push/pull source** between local and Studio Web
- User wants to use the `@uipath/uipath-typescript` SDK from a coded app
- User wants to run the **full pipeline** (build → pack → publish → deploy)
- User wants to **generate a dashboard** from a natural-language description — e.g. "build me a dashboard showing agent health, error rates, invocation volume, latency, active agents, KPIs, governance metrics, or consumption trends"
- User says "build/create/generate a dashboard", describes metrics to visualize, or asks for an agent observability, operations, or cost view

## App Types

| Type | Description | Key Difference |
|------|-------------|----------------|
| **Coded Web App** | React/Vue/other frontend hosted on UiPath CDN | User-facing app accessed via a URL |
| **Coded Action App** | React form wired to UiPath Action Center | Rendered inside human task reviews in Maestro/Agent workflows |

> **Coded apps are not registered in `.uipx` solutions.** They have no `project.uiproj` / `project.json`, so `uip solution project add` does not apply. A coded app can live alongside a solution directory but deploys independently via `uip codedapp publish` (and `uip codedapp deploy`), not via `uip solution pack` / `publish` / `deploy`.

## Critical Rules

1. **Identify the app type before doing anything else.** Ask as a structured choice (Rule 17): **Coded Web App** — custom frontend deployed to UiPath Cloud · **Coded Action App** — form for Action Center human task reviews. The two paths diverge on scaffolding, redirect URI, and publish flag — do not guess.
2. **Always check login status first.** Run `uip login status --output json` before any cloud command. If not logged in, run `uip login`.
3. **Never skip the build step.** Run `npm run build` after scaffolding (to verify the scaffold compiles) and again before `pack` or `push` (to produce the deployable `dist/`). Verify `dist/` exists each time.
4. **Pack → Publish → Deploy order is required.** Each step depends on the previous one producing its output.
5. **Bump the version for re-publish.** If the same version already exists in Orchestrator, publish will fail.
6. **Action apps require `-t Action` on publish.** Run `uip codedapp publish -t Action` (not the default `Web` type).
7. **Never pass access tokens as CLI flags.** JWTs are too long — use the `UIPATH_ACCESS_TOKEN` environment variable instead.
8. **Base URL must use the API subdomain.** `https://api.uipath.com` not `https://cloud.uipath.com`. See the table below.
9. **`vite.config.ts` must always set `base: './'`.** The platform handles URL routing — apps must use relative asset paths. Do not use a routing name or a sub-path here.
10. **Use `getAppBase()` from `@uipath/uipath-typescript` for any absolute URL constructed at runtime** — router basename, image `src`, `fetch` paths. Deployed apps mount at a non-root prefix; `/`-rooted paths work locally but 404 after deploy. Vite's `base: './'` only fixes import-time references.
11. **`uip codedapp deploy` must run non-interactively.** Pass the folder key as `--folder-key <GUID>` (or as `UIPATH_FOLDER_KEY=<GUID>` env-var prefix — either works). The interactive folder picker fails in non-TTY contexts (CI, agent shells). If the user provides a folder **name**, resolve it to a key with `uip or folders list --output json` and match on the `Name` field (output rows are `{ Key, Name, Path, Description, Type, ParentKey }`). The `uip or ...` commands require the Orchestrator tool — install once via `uip tools install @uipath/orchestrator-tool` (check first with `uip tools list`).
12. **Guard against text overflow in every UI.** See [patterns.md](references/patterns.md) "Preventing Text Overflow".
13. **Inspect the DF schema before writing analytics, filters, or seeds.** Call `entities.getById(<id>)` from inside the app's authenticated session — NOT a CLI script with `~/.uipath/.auth` (different scopes, will 401). DF doesn't behave like a typical RDBMS; see [sdk/data-fabric.md](references/sdk/data-fabric.md) "Anti-shapes & gotchas".
14. **Every list call returns ONE page — even with no options. There is no "give me everything" path.** Applies to `getAll`, `getAllRecords`, `queryRecordsById`, `getFileMetaData`, etc. `getAll()` with no options does NOT return all rows; the SDK sends no `pageSize` and the **server** applies its own cap, wrapped in a misleadingly-named `NonPaginatedResponse`. To list every row from a source that may exceed the cap, you MUST loop the cursor: `while (page.hasNextPage) { page = await getAll({ cursor: page.nextCursor }) }` and accumulate `items`. Reading `result.items.length` after a single call is almost always a bug. See [sdk/pagination.md](references/sdk/pagination.md).
15. **Tables of dynamic data must paginate, not dump all rows in one scroll.** Page size 25–50 with next/prev/page-number controls and a "Showing X–Y of Z" summary. Top-N + "see all" is acceptable for explicitly summary panels (e.g., "Top 10 oldest"). Infinite-scroll-of-N-rows is unusable for operational dashboards. Applies to any table backed by any service (DF entities, Tasks, Jobs, Conversations, Process Instances, etc.). See [patterns.md](references/patterns.md) "Tabular Data".
16. **When adding any new SDK method call, verify `VITE_UIPATH_SCOPE` already includes the required scope.** Write operations, action methods (`Jobs.stop`, `Tasks.complete`, `ProcessInstances.cancel`, etc.), or first use of a new service typically need broader scopes than read-only flows. Mismatched scopes fail silently with `401` / `403` on the first call. See [oauth-scopes.md](references/oauth-scopes.md) for the per-method scope table.
17. **Never make the user type magic phrases.** Whenever you ask the user to pick between known options (app type, build/edit/deploy intent, OAuth setup, deploy pinning), present a **structured choice** via the host coding agent's native question tool (selectable options) when one exists. Mechanics: one option per choice with a short bold label + one-line description of what picking it does; put the recommended option **first** and suffix its label "(Recommended)"; keep to **at most 4 options** (reserve one slot for an escape option like *Make changes* / *Cancel* when applicable). If there are 5+ candidates, or the host agent has no question tool, render a plain numbered list instead and accept the number or the option label as the answer. A free-text reply must always remain valid (e.g. a plan-change request) and takes precedence over the options. **Exception — never put a question in the same response as a long output:** plan-approval gates are free-text by design (the plan ends with "confirm or tell me what to change"); structured questions fire only on later, short turns. See `references/dashboards/plugins/build/impl.md`.

## Disambiguation — Apps vs Dashboards

**Route directly to Apps workflow** (sections below) when you see:
`web app`, `action app`, `codedapp`, `app.config.json`, `action-schema.json`,
`scaffold app`, `deploy app`, `pack`, `publish`, `push`, `pull`, `debug app`

**Route directly to [references/dashboards/CAPABILITY.md](references/dashboards/CAPABILITY.md) when you see:**
`dashboard`, `analytics`, `KPI`, `metrics`, `Insights`, `observability`,
`admin console`, `report`, `chart`, `trend`, `governance report`, `agent metrics`

**When intent is ambiguous** — ask "Which fits your goal?" as a structured choice (Rule 17):

| Option | Description |
|--------|-------------|
| **Build or modify a Web App / Action App** | Scaffold a UI, form, or app that deploys to Automation Cloud |
| **Generate a dashboard** | Analytics or admin view from a natural-language description |

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
| **SDK: Agent Feedback** | [references/sdk/feedback.md](references/sdk/feedback.md) |
| **SDK: Pagination** | [references/sdk/pagination.md](references/sdk/pagination.md) |
| **UI Patterns (polling, BPMN, HITL, text overflow, table pagination)** | [references/patterns.md](references/patterns.md) |
| **Generate an admin dashboard from NLP** | [references/dashboards/CAPABILITY.md](references/dashboards/CAPABILITY.md) |

## CLI Setup

```bash
# Install the UiPath CLI (run once)
npm install -g @uipath/cli

# Install the coded apps tool
uip tools install @uipath/codedapp-tool

# Install the Orchestrator tool (needed to resolve folder name → key for deploy)
uip tools install @uipath/orchestrator-tool

# Verify both are installed
uip tools list

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
3. **Pack** — `uip codedapp pack dist -n <name> --version <version>`. Produces `.uipath/<name>.<version>.nupkg`. Bump version if previously published.
4. **Publish** — `uip codedapp publish` (add `-t Action` for action apps). Verify `cat .uipath/app.config.json`.
5. **Deploy** — `uip codedapp deploy -n <name> --folder-key <GUID>`. Resolve the GUID from a user-provided folder name via `uip or folders list --output json`. Never let the command go interactive. Share the app URL with the user.

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
| `Folder key required` / deploy hangs on prompt | Missing folder for CLI deploy | Resolve folder name → key via `uip or folders list --output json` (match on `Name`, read `Key`), then run `uip codedapp deploy --folder-key <GUID> ...`. See [pack-publish-deploy.md](references/pack-publish-deploy.md#folder-key). |
| `No packages found` | No `.nupkg` in `.uipath/` | Run `pack` first |
| Login fails / redirect error | OAuth misconfiguration | See [debug.md](references/debug.md) |
| API calls fail with 401/CORS | Wrong base URL | Use `https://api.uipath.com` not `cloud.uipath.com` |

> **Folder identifier names differ across CLI and SDK.** The CLI uses `UIPATH_FOLDER_KEY` / `--folder-key` (string) and applies only to `uip codedapp deploy`. SDK methods use different parameters: Maestro services (`MaestroProcesses`, `ProcessInstances`, `Cases`) take `folderKey` (string GUID), Orchestrator services (`Assets`, `Queues`, `Buckets`, `Processes`) take `folderId` (number). Do not pass the CLI env var into SDK calls. To bridge from a Maestro `folderKey` to an Orchestrator `folderId`, see [sdk/maestro.md](references/sdk/maestro.md) — and **never** `parseInt(folderKey)`, the GUID is not numeric.

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
