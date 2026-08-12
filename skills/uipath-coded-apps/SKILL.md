---
name: uipath-coded-apps
description: "UiPath Coded Apps — scaffold, build, run, and deploy Coded Web Apps and Coded Action Apps: React/TypeScript apps that call UiPath Cloud APIs via the `@uipath/uipath-typescript` SDK and ship to Automation Cloud (push/pull to Studio Web, pack, publish, deploy, OAuth-PKCE). Also generates live analytics & governance dashboards from a plain-language request, wired to tenant data via the Insights real-time API, with edit and deploy flows. For RPA→uipath-rpa, Python agents→uipath-agents, Maestro flows→uipath-maestro-flow, solution packaging→uipath-solution."
when_to_use: "User wants to scaffold, build, push/pull, pack, publish, or deploy a Coded Web App or Coded Action App, or use the `@uipath/uipath-typescript` SDK inside one. Also dashboard requests: 'build me a dashboard', 'show agent health / error rate / KPIs / governance violations', 'generate an analytics or observability dashboard', edit an existing one (add/remove/change a widget, change time range, deploy), or fix/diagnose a dashboard that won't build (a metric that fails to compile, a bad SDK call, a broken widget). For RPA→uipath-rpa; Python agents→uipath-agents; Maestro flows→uipath-maestro-flow."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, Task
---

# UiPath Coded Apps

Build, debug, and deploy UiPath Coded Web Applications and Coded Action Apps using the `uip codedapp` CLI and `@uipath/uipath-typescript` SDK.

## When to Use This Skill

- User wants to **build, debug, or deploy** a UiPath Coded Web App or Coded Action App
- User asks about `uip codedapp` commands, `.uipath/` directory, `app.config.json`, or `action-schema.json`
- User wants to **scaffold** a new React/Vue frontend for UiPath Cloud or an Action Center form
- User wants to embed the **Document Understanding Validation Station** widget for human review of DU extraction results
- User wants to **push/pull source** between local and Studio Web
- User wants to use the `@uipath/uipath-typescript` SDK from a coded app
- User wants to run the **full pipeline** (build → pack → publish → deploy)
- User wants to **generate an agent-monitoring / analytics dashboard** from a natural-language description — e.g. "show agent health, error rates, invocation volume, latency, active agents, KPIs, governance metrics, or consumption trends"
- User says "build/create/generate a dashboard", describes metrics to visualize, or asks for an agent observability, operations, or cost view

## App Types

| Type | Description | Key Difference |
|------|-------------|----------------|
| **Coded Web App** | React/Vue/other frontend hosted on UiPath CDN | User-facing app accessed via a URL |
| **Coded Action App** | React form wired to UiPath Action Center | Rendered inside human task reviews in Maestro/Agent workflows |

> **Two lifecycles, two scaffolding entry points.**
>
> - **Standalone coded app**: scaffold with `npx create-vite@latest` (see [create-web-app.md](references/create-web-app.md) / [create-action-app.md](references/create-action-app.md)). No `project.uiproj` / `webAppManifest.json` — those are solution-membership artefacts and standalone apps don't need them. Deploy via `uip codedapp pack` → `uip codedapp publish` (`-t Action` for action apps) → `uip codedapp deploy`. This is the classic single-app lifecycle covered by the rest of this skill.
> - **In-solution coded app**: run `uip codedapp init` from **inside a `.uipx` solution**. Init writes `project.uiproj` (`ProjectType: "AppV2"`) + `webAppManifest.json`, nests runtime + build artefacts under `source/dist/`, auto-registers the project as `Type: "AppV2"` in the `.uipx`, and emits `resources/solution_folder/app/{Coded,CodedAction}/`. From then on the app is part of the solution — `uip solution pack` bundles its `.nupkg` and `uip solution deploy run` provisions it in the deployment folder. **Do not** run `uip codedapp pack` / `publish` / `deploy` on a coded app that's already registered in `.uipx` — that bypasses the solution's deploy config (external client ID, routing name, action schema) and double-registers the package. `uip solution projects add` / `uip solution projects import` register existing AppV2 folders too, reading `webAppManifest.config.isActionApp` to pick the `Coded` / `CodedAction` subType. For the solution-side lifecycle see [/uipath:uipath-solution](/uipath:uipath-solution).
>
> **`uip codedapp init` is for solutions only.** It is not the scaffolding entry point for a standalone coded app — use `create-vite` for that.

## Critical Rules

1. **Identify the app type before doing anything else.** Ask as a structured choice (Rule 18): **Coded Web App** — custom frontend deployed to UiPath Cloud · **Coded Action App** — form for Action Center human task reviews. The two paths diverge on scaffolding, redirect URI, and publish flag — do not guess.
2. **Always check login status first.** Run `uip login status --output json` before any cloud command. Deployment must bind and verify an exact named profile, control plane, org, and tenant. If not logged in, run `uip login` for the intended environment.
3. **Build before packaging source.** Run `npm run build` after scaffolding and again before packaging a source-built candidate. An explicit synthetic Alpha/Staging test may deploy an already-built or already-published candidate as-is, but only after hashing and auditing that exact candidate and recording that the build was skipped. Never use that exception as production evidence.
4. **Use Build → Pack → Publish → Deploy for a new candidate.** A reconciled upgrade may deploy an exact already-published candidate without rebuilding, repacking, or republishing. Do not repeat an earlier stage merely because a later external write returned an ambiguous result.
5. **Choose versions before external writes.** If a version already exists, select and verify a different version before packing. Never silently auto-bump, repack, or republish in response to a conflict.
6. **Action apps require `-t Action` on publish.** Run `uip codedapp publish -t Action` (not the default `Web` type).
7. **Never handle access tokens manually.** Do not pass, print, parse, source, or set cached access tokens. Use `uip login` and supported `uip codedapp` commands; the CLI manages authentication.
8. **Base URL must use the API subdomain.** `https://api.uipath.com` not `https://cloud.uipath.com`. See the table below.
9. **`vite.config.ts` must always set `base: './'`.** The platform handles URL routing — apps must use relative asset paths. Do not use a routing name or a sub-path here.
10. **Use `getAppBase()` from `@uipath/uipath-typescript` for any absolute URL constructed at runtime** — router basename, image `src`, `fetch` paths. Deployed apps mount at a non-root prefix; `/`-rooted paths work locally but 404 after deploy. Vite's `base: './'` only fixes import-time references.
11. **`uip codedapp deploy` must run non-interactively.** Pass the folder key as `--folder-key <GUID>` (or as `UIPATH_FOLDER_KEY=<GUID>` env-var prefix — either works). The interactive folder picker fails in non-TTY contexts (CI, agent shells). If the user provides a folder **name**, resolve it to a key with `uip or folders list --output json` and match on the `Name` field (output rows are `{ Key, Name, Path, Description, Type, ParentKey }`). A **personal workspace** is the row with `Type == "Personal"` — resolve its `Key` the same way. To deploy into a **new** folder, create it first with `uip or folders create "<NAME>" --output json` and read `Data.Key`. The `uip or ...` commands require the Orchestrator tool — install once via `uip tools install @uipath/orchestrator-tool` (check first with `uip tools list`).
12. **Guard against text overflow in every UI.** See [patterns.md](references/patterns.md) "Preventing Text Overflow".
13. **Inspect the DF schema before writing analytics, filters, or seeds.** Run `uip df entities get <ENTITY_ID> --output json` to inspect fields and types. At runtime, use `entities.getById(<id>)` from the app's authenticated session. DF doesn't behave like a typical RDBMS; see [sdk/data-fabric.md](references/sdk/data-fabric.md) "Anti-shapes & gotchas".
14. **Every list call returns ONE page — even with no options. There is no "give me everything" path.** Applies to `getAll`, `getAllRecords`, `queryRecordsById`, `getFileMetaData`, etc. `getAll()` with no options does NOT return all rows; the SDK sends no `pageSize` and the **server** applies its own cap, wrapped in a misleadingly-named `NonPaginatedResponse`. To list every row from a source that may exceed the cap, you MUST loop the cursor: `while (page.hasNextPage) { page = await getAll({ cursor: page.nextCursor }) }` and accumulate `items`. Reading `result.items.length` after a single call is almost always a bug. See [sdk/pagination.md](references/sdk/pagination.md).
15. **Tables of dynamic data must paginate, not dump all rows in one scroll.** Page size 25–50 with next/prev/page-number controls and a "Showing X–Y of Z" summary. Top-N + "see all" is acceptable for explicitly summary panels (e.g., "Top 10 oldest"). Infinite-scroll-of-N-rows is unusable for operational dashboards. Applies to any table backed by any service (DF entities, Tasks, Jobs, Conversations, Process Instances, etc.). See [patterns.md](references/patterns.md) "Tabular Data".
16. **When adding any new SDK method call, verify the configured OAuth scope already includes the required scope** — both dashboards and web apps read the `scope` key from `uipath.json`. Write operations, action methods (`Jobs.stop`, `Tasks.complete`, `ProcessInstances.cancel`, etc.), or first use of a new service typically need broader scopes than read-only flows. Mismatched scopes fail silently with `401` / `403` on the first call. See [oauth-scopes.md](references/oauth-scopes.md) for scope bundles and the per-method lookup protocol (the per-method table ships inside the SDK package at `node_modules/@uipath/uipath-typescript/docs/oauth-scopes.md`).
17. **Never call `sdk.initialize()` in an action app.** That is web-app-only — it starts a PKCE OAuth redirect. Action apps run in Action Center's iframe with a host-injected session: construct `new UiPath()` (no args) and use it directly. See [create-action-app.md](references/create-action-app.md) `src/uipath.ts`.
18. **Never make the user type magic phrases.** Whenever you ask the user to pick between known options (app type, build/edit/deploy intent, OAuth setup, deploy pinning), present a **structured choice** via the host coding agent's native question tool (selectable options) when one exists. Mechanics: one option per choice with a short bold label + one-line description of what picking it does; put the recommended option **first** and suffix its label "(Recommended)"; keep to **at most 4 options** (reserve one slot for an escape option like *Make changes* / *Cancel* when applicable). If there are 5+ candidates, or the host agent has no question tool, render a plain numbered list instead and accept the number or the option label as the answer. A free-text reply must always remain valid (e.g. a plan-change request) and takes precedence over the options. **Exception — never put a question in the same response as a long output:** plan-approval gates are free-text by design (the plan ends with "confirm or tell me what to change"); structured questions fire only on later, short turns. See `references/dashboards/plugins/build/impl.md`.
19. **Never guess SDK method signatures — read the installed types.** The authoritative reference for method names, parameters, return types, and usage examples is `node_modules/@uipath/uipath-typescript/dist/<subpath>/index.d.ts` (full JSDoc; matches the installed SDK version exactly). Before calling a service you have not used in this session, Read its `.d.ts`. If `node_modules` is absent, run the install step first — the app cannot build without it. The `references/sdk/*.md` files deliberately do NOT list signatures; they cover only scopes, calling conventions, and traps the types cannot express. See [references/sdk/imports.md](references/sdk/imports.md) for the missing-capability protocol. **Boundary: read the `.d.ts`, never the compiled bundle.** `dist/*.mjs` / `*.js` is minified implementation, not API — reading it dead-ends. A grep with no output **confirms absence**; treat a genuine gap as unsupported (use the documented alternative) rather than escalating the search into the bundle.
20. **Classify the deployment lane before publishing.** The direct quick path is only for an explicitly requested, internal, synthetic-data test in Alpha or Staging. Production, customer data, or any release-trust requirement uses a governed release with reviewed source/artifact/config bindings, an approval record, an immutable receipt, and post-deploy verification. Ambiguity defaults to governed.
21. **Choose `create` or `upgrade` explicitly from remote evidence.** `.uipath/app.config.json`, `.dashboard/state.json`, and prior console output are repairable local hints, not proof of remote state. A create requires an unused route and no matching deployment; an upgrade requires the exact existing deployment, route, current version, and candidate version. Stop when remote inventory cannot prove one case.
22. **Treat external writes as indeterminate until reconciled.** After `publish` or `deploy` starts, a timeout, interruption, 5xx, HTML response, or nonzero exit may have changed remote state. Do not blindly retry, auto-bump, change or omit the route, delete/recreate the app, or fall back from upgrade to create. Re-read remote state and form a fresh operation.
23. **A route is immutable after create.** Pass the reviewed `--path-name` only for a proven create. Never invent a random suffix after a collision. For a proven upgrade, preserve the exact route and omit `--path-name`; if the CLI reports `routing name must be unique`, stop and reconcile the target rather than retrying with different flags.

## Disambiguation — Apps vs Dashboards

**Route directly to Apps workflow** (sections below) when you see:
`web app`, `action app`, `codedapp`, `app.config.json`, `action-schema.json`,
`scaffold app`, `deploy app`, `pack`, `publish`, `push`, `pull`, `debug app`

**Route directly to [references/dashboards/CAPABILITY.md](references/dashboards/CAPABILITY.md) when you see:**
`dashboard`, `analytics`, `KPI`, `metrics`, `Insights`, `observability`,
`admin console`, `report`, `chart`, `trend`, `governance report`, `agent metrics`

**When intent is ambiguous** — ask "Which fits your goal?" as a structured choice (Rule 18):

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
| **Embed the DU Validation Station widget** | [references/widgets/validation-station.md](references/widgets/validation-station.md) |
| **OAuth scopes for SDK services** | [references/oauth-scopes.md](references/oauth-scopes.md) |
| **SDK: Import paths & subpath exports** | [references/sdk/imports.md](references/sdk/imports.md) |
| **SDK: Assets, Queues, Buckets, Processes, Jobs, Attachments** | [references/sdk/orchestrator.md](references/sdk/orchestrator.md) |
| **SDK: Data Fabric (Entities, ChoiceSets)** | [references/sdk/data-fabric.md](references/sdk/data-fabric.md) |
| **SDK: Maestro (Processes, Cases)** | [references/sdk/maestro.md](references/sdk/maestro.md) |
| **SDK: Action Center (Tasks)** | [references/sdk/action-center.md](references/sdk/action-center.md) |
| **SDK: Conversational Agent** | [references/sdk/conversational-agent.md](references/sdk/conversational-agent.md) |
| **SDK: Agent Feedback** | [references/sdk/feedback.md](references/sdk/feedback.md) |
| **SDK: Pagination** | [references/sdk/pagination.md](references/sdk/pagination.md) |
| **SDK: Agents & Agent Memory (Insights RTM)** | [references/sdk/agents.md](references/sdk/agents.md) |
| **SDK: Agent Traces (Insights RTM)** | [references/sdk/traces.md](references/sdk/traces.md) |
| **SDK: Governance — policy evaluations (Insights API)** | [references/sdk/governance.md](references/sdk/governance.md) |
| **SDK: Agent Governance Decisions — runtime compliance (Insights RTM)** | [references/sdk/governance-traces.md](references/sdk/governance-traces.md) |
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

# Headless/CI — provision the credential through the runner's secure profile setup,
# never in command arguments or logs. Then verify the exact named profile.
uip login status --profile <profile-name> --output json
```

> **The CLI session scope is separate from the app's runtime OAuth scopes.** The scopes in `uipath.json` are what the *deployed app* requests at runtime (see [oauth-scopes.md](references/oauth-scopes.md)). A headless profile used for `uip codedapp publish` must include Orchestrator package scopes plus `Apps.Read Apps.Write`: publish uploads the package and then registers the coded app with a different service. Omitting Apps scopes can let upload succeed before registration fails. Configure credentials through the secure runner/profile mechanism, never through command arguments or committed files.

## SDK Config (web app)

The web app initializes the SDK with `new UiPath()` (no config). At runtime the SDK reads `clientId`, `scope`, `orgName`, `tenantName`, `baseUrl`, and `redirectUri` from `<meta name="uipath:*">` tags. During local dev `@uipath/coded-apps-dev` injects those tags from `uipath.json` (committed) — the single config source, holding `clientId`, `scope`, `orgName`, `tenantName`, `baseUrl`, and `redirectUri` (the Vite dev URL for local). In production the UiPath platform injects the same tags directly.

To change any of these values, edit `uipath.json`.

## CLI Environment Variables

| Variable | Used By | Description |
|----------|---------|-------------|
| `UIPATH_PROJECT_ID` | `uip codedapp push` / `uip codedapp pull` | Studio Web project ID |

**Base URL by environment:**

| Environment | Correct Base URL |
|---|---|
| Production (cloud) | `https://api.uipath.com` |
| Staging | `https://staging.api.uipath.com` |
| Alpha | `https://alpha.api.uipath.com` |

## Deployment Lanes

### Testing-only quick path

Use the direct CLI pipeline without a second approval only when the user explicitly requests a test deployment and all of these are true. That explicit request is the operation authorization; do not ask for a separate plan hash. Ask again only if authoritative preflight materially changes the target, intent, route, or candidate.

- Target is the exact UiPath Alpha or Staging control plane.
- App is internal/authenticated and contains synthetic data only.
- The exact org, tenant, folder, OAuth client, route, CLI/profile, candidate version, and built bytes are recorded.
- The operation is explicitly `create` or `upgrade`, supported by fresh remote evidence.
- An automatic testing receipt records the artifact/config hashes, waived gates, every external-write result, and post-deploy checks. It must say `production_eligible: false` and `release_evidence: false`.

Dirty or uncommitted source is allowed in this lane because the exact built bytes are authoritative. Record Git HEAD and worktree status for context; do not present them as provenance. If the exact candidate is already published, deploy it without rebuilding or republishing.

The stock `uip codedapp` 1.198.0 commands do not include deployment `list` or `get`. Use an approved inventory-capable deployment helper or Apps API runtime for the required remote preflight and post-verification; never extract a bearer token manually. If that capability is unavailable, stop before the write.

For a new source-built test candidate, execute the full pipeline after preflight; do not pause between steps for another approval:

1. **Auth** — verify a named profile with `uip login status --profile <name> --output json` and confirm the control plane, org, and tenant.
2. **Build and bind** — run `npm run build`, audit `dist/`, and hash the exact directory and runtime configuration.
3. **Pack** — run `uip codedapp pack dist -n <name> --version <version> -o .uipath`, then verify and hash the candidate package from the filesystem. (`pack` uses `--output` for its directory, so do not use `--output json` here.)
4. **Publish** — run `uip codedapp publish -n <name> --version <version> --profile <name> --output json` (add `-t Action` for action apps). A failed or interrupted publish is indeterminate until remote reconciliation.
5. **Deploy** — use the exact version, client, folder, tags, and profile. Add `--path-name` only for a remotely proven create; omit it for a remotely proven upgrade. Never let the command go interactive.
6. **Verify** — re-read the exact remote deployment and verify its route, assets, authentication, and an app-specific smoke test before calling it deployed.

### Governed release

Use a governed release for Production, customer data, or any request that expects durable release evidence. Bind clean reviewed source, exact dist/package/runtime hashes, CLI/profile/target identity, create-or-upgrade remote evidence, a reviewed approval, an immutable receipt, and rollback authority. Do not substitute the testing-only quick path or its receipt. See [pack-publish-deploy.md](references/pack-publish-deploy.md) for both lanes and their failure boundaries.

## SDK Module Imports

See [references/sdk/imports.md](references/sdk/imports.md) for the lookup protocol (subpaths and classes are discovered from the installed package — `ls node_modules/@uipath/uipath-typescript/dist/`), type import conventions, and anti-pattern examples. Core rules are listed under **Anti-patterns** below.

## Key Concepts

### App Config (`.uipath/app.config.json`)

Created by `publish`, consumed by `deploy`. Contains `appName`, `systemName`, `appType`, `deploymentId`, `appUrl`. Preserve it between publish and deploy, but treat it as a repairable cache: compare it with remote inventory before choosing create or upgrade.

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
| `routing name must be unique` | Create/upgrade target or route was inferred incorrectly | Stop. Reconcile remote deployment and route state; never randomize or omit the route and retry. |
| Publish/deploy timed out or returned 5xx/HTML | External write is indeterminate | Re-read remote package/deployment state before forming a fresh operation; never blind-retry. |

> **Folder identifier names differ across CLI and SDK.** The CLI uses `UIPATH_FOLDER_KEY` / `--folder-key` (string) and applies only to `uip codedapp deploy`. SDK methods use different parameters: Maestro services (`MaestroProcesses`, `ProcessInstances`, `Cases`) take `folderKey` (string GUID), Orchestrator services (`Assets`, `Queues`, `Buckets`, `Processes`) take `folderId` (number). Do not pass the CLI env var into SDK calls. To bridge from a Maestro `folderKey` to an Orchestrator `folderId`, see [sdk/maestro.md](references/sdk/maestro.md) — and **never** `parseInt(folderKey)`, the GUID is not numeric.

## Completion Output

When you finish a task, report only what's applicable to the work actually done:

1. **What was done** — files created, edited, or deleted (list paths); CLI commands run
2. **Stage reached** — one of: scaffolded / built / packed / published / deployed-for-testing / governed-deployed
3. **Artifacts produced** (report only the ones that actually exist):
   - `dist/` — if `npm run build` was run
   - `.uipath/<name>.<version>.nupkg` — if `pack` was run
   - `.uipath/app.config.json` with `deploymentId` — if `publish` was run
   - Deployment URL (`appUrl` from `app.config.json`) — if `deploy` ran and remote verification passed; label testing-only URLs as nonproduction
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
- **Don't treat `.uipath/app.config.json` as remote authority** — preserve it for `deploy`, then verify every identity and version against remote state.
