---
name: uipath-dashboards
description: "[PREVIEW] Build UiPath dashboards from natural-language prompts — agent observability, KPIs, metrics, charts, tables over TS SDK; preview + deploy via uip codedapp. For agent build→uipath-agents. For bare publish→uipath-coded-apps."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Dashboards

CLI-first, natural-language skill that turns a prompt into a production-grade React dashboard deployed on UiPath Automation Cloud as a Coded Web App. Two modes — **Build** (scaffold/edit + localhost preview) and **Deploy** (pack → publish → deploy) — dispatched by natural-language intent detection.

## When to use

- "Build me a dashboard showing X" / "create an agent-health dashboard" → **Build**
- "Build me an agent observability dashboard with active agents, invocation volume, error rate" → **Build**
- "Create a queue throughput / job latency / case pipeline dashboard" → **Build**
- "Add a chart of Y to the dashboard" / "change the time window" → **Build** (incremental)
- "Deploy the dashboard" / "publish to alpha" / "ship it" → **Deploy**
- "Show me which tenant this is pointing at" → ask user (status is out of v1 scope)

Do NOT use for: building an actual agent (→ `uipath-agents`), bare `uip codedapp` publish/deploy of non-dashboard apps (→ `uipath-coded-apps`), Orchestrator administration (→ `uipath-platform`), or policy/compliance work (→ `uipath-governance`).

## Mode detection

Classify every invocation by the user's prompt + the workspace state at `<cwd>/.uipath-dashboards/`. Projects ALWAYS live as subdirectories under `<cwd>/.uipath-dashboards/<name>/`; per-project state is at `<project>/.dashboard/state.json`.

| Prompt signal | Workspace state | Mode |
|---|---|---|
| `deploy`, `publish`, `ship`, `push to tenant`, `release`, `upgrade` (with a project name) | project exists | **Deploy** on that project |
| `deploy` etc. without name | one project in workspace | **Deploy** that one (confirm name in plan) |
| `deploy` etc. without name | many projects in workspace | **Ask which** project to deploy |
| `build`, `create`, `add <widget>`, `change <x>`, new dashboard topic | no project of that name | **Build** (scaffold a new project under `.uipath-dashboards/<name>/`) |
| Same | a project of that name already exists | **Ask:** update existing, or create with `-1` suffix? |
| Ambiguous / neither | — | **Ask the user; never guess** |

Ambiguity NEVER defaults to Deploy (Deploy mutates tenant state). Build is non-destructive re: tenant state; ambiguity may default to Build only when safe, but prefer asking.

**Path conventions** (locked across the skill):
- Workspace container: `<cwd>/.uipath-dashboards/`
- Project root: `<cwd>/.uipath-dashboards/<kebab-name>/`
- Per-project state: `<project>/.dashboard/state.json` (NOT `.uipath-dashboards/` — that's the outer name)
- Generated dashboard files: `<project>/src/...`
- Build artifacts: `<project>/dist/` (gitignored)

After mode detection, read **exactly one** plugin impl:
- Build → [references/plugins/build/impl.md](references/plugins/build/impl.md)
- Deploy → [references/plugins/deploy/impl.md](references/plugins/deploy/impl.md)

Never preload both.

## Critical Rules

1. **Preflight before any cloud touch.** Run `uip login status --output json`. If `Data.Status != "Logged in"`, stop and instruct `uip login --authority https://<env>.uipath.com` — where `<env>` MUST come from auth-context (`~/.uipath/.auth.json` `authority` field). NEVER hardcode `cloud` as the default; users on alpha or staging would be sent to the wrong portal. If the auth file is missing entirely, ask the user which env (alpha / staging / cloud) before suggesting a login URL.
2. **Read identity from `~/.uipath/.auth`.** Never ask the user for env / orgName / tenantName — resolve them per [references/primitives/auth-context.md](references/primitives/auth-context.md). **Do not ask for folder at Build time** — widgets default to tenant-wide queries. `folderKey` is a Deploy concern (which Orchestrator folder hosts the app), collected once in Deploy Step 2 and persisted in `state.json` for subsequent upgrades. Only resolve a folder at Build if the user's prompt explicitly scopes to one.
3. **`--output json` on every `uip` call.** Parse `Data` / `Message` from the structured response.
4. **Never cache live tenant reads.** Folder lists, job counts, deployed-app lists must hit live. Caching is reserved for templates and scaffolds.
5. **Never auto-deploy.** Every Deploy surfaces the intended plan and waits for explicit user approval (`y`/`n`).
6. **State file writes are atomic.** Write `<project>/.dashboard/state.json.tmp`, rename on success. State is per-project at `.dashboard/state.json`; the outer `.uipath-dashboards/` is the workspace container, not a state path.
7. **Scopes derive from generated code, never prompted.** In secret-mode these are informational only.
8. **Never overwrite hand edits silently.** Diff before write; surface diff + confirm on edits that appear user-authored. See [references/primitives/incremental-editor.md](references/primitives/incremental-editor.md) for the diff discipline.
9. **One plugin file per dispatch.** Build reads `plugins/build/impl.md` + its primitives; Deploy reads `plugins/deploy/impl.md` + its primitives. Never both.
10. **Ambiguous prompts get a clarifying question, not a guess.**
11. **Tokens are full-user-session scoped — guardrails are mandatory.** CSP, in-memory-only tokens, gitignored `.env*`, no `console.log(sdk)`. See [references/primitives/security.md](references/primitives/security.md).
12. **No `dangerouslySetInnerHTML` with tenant data. No token in URL. No localStorage for tokens.** Incremental-editor rejects edits that introduce these.
13. **Read the SDK; don't mirror it.** At the start of every Build, run `assets/scripts/introspect-sdk.mjs` against the installed `@uipath/uipath-typescript` to produce a manifest of every service, class, method, and signature. The manifest — not our catalog files — is the source of truth for what's queryable. New SDK capabilities (trace/span APIs, new services) become available to the generator immediately, without skill changes. See [references/primitives/sdk-introspection.md](references/primitives/sdk-introspection.md). `intent-map.md` and `service-semantics.md` are opinion layered on top; they may NOT enumerate everything.
14. **Every widget routes to a real detail view.** No placeholder hashes. Generator produces `<WidgetName>.tsx` + `<WidgetName>View.tsx` + aggregated hook + list hook + route registration — all in the same Generate step. See [references/aesthetic/detail-views.md](references/aesthetic/detail-views.md).
15. **Columns in detail views are derived from service semantics, not hardcoded.** Read [references/sdk/service-semantics.md](references/sdk/service-semantics.md) "Semantic columns" for the widget's service and produce a column list covering identity + time + domain-specific dimensions.
16. **Plan first, code never first.** Build mode begins with a plain-language plan (widgets, sources, time windows) and HALTS for user approval. No code generation before the user replies with positive sentiment ("looks good", "lgtm", "yes", etc.). The local-preview SDK secret is the access token from the user's `uip login` session (`~/.uipath/.auth` env-file or `~/.uipath/.auth.json` JSON) — manual PAT paste is an override for scope-restricted previews, not a requirement. See [references/primitives/build-plan.md](references/primitives/build-plan.md). The user is non-developer by default — never lead with `npm install` chatter.
17. **Quiet execution after approval — strict subagent boundary.** From the moment the user approves the plan (and provides the PAT) to the moment the friendly summary is emitted, the main agent makes **exactly two tool calls**: one progress-line print, and one `Task` call that performs the entire Build pipeline (PAT-write, mkdir, render templates, npm install, shadcn init/add, manifest introspection, widget generation, validation, dev-server boot). **NO Read, Write, Bash, or Edit calls in the main agent during this window.** Tool calls in the main agent fire user-facing hooks (`.remember/`, telemetry, audit logs) one round per call — every visible call is one round of cosmetic noise. The cure is not making them. If the agent is tempted to "just write the PAT real quick before delegating", that's the anti-pattern — write the PAT inside the Task. See [references/primitives/quiet-execution.md § "One Task call covers everything"](references/primitives/quiet-execution.md).
18. **Validate before claiming success.** `tsc --noEmit` must pass, every SDK call in generated query hooks must exist in the introspected manifest, and the dev server must boot without resolution errors — BEFORE the user is told to open `http://localhost:5173`. See [references/primitives/validation.md](references/primitives/validation.md). On failure, surface a friendly summary with recovery offers ("skip widget / switch service / pause").
19. **User-facing voice.** Talk about widgets and metrics, never about files, frameworks, or types. Forbidden in user-visible output: `Vite`, `Recharts`, `shadcn`, `tsx`, `npm install`, `OData`, file paths, package versions, raw stderr. Permitted: widget names, metric names, time windows, the URL, the PAT prompt.

## Workflow

### Step 0 — Preflight

```bash
uip login status --output json
```
Require `Data.Status == "Logged in"`. Read `~/.uipath/.auth` per [auth-context](references/primitives/auth-context.md).

### Step 1 — Detect mode

Per the table above.

### Step 2 — Dispatch

Read exactly one:
- Build → [plugins/build/impl.md](references/plugins/build/impl.md)
- Deploy → [plugins/deploy/impl.md](references/plugins/deploy/impl.md)

Each plugin owns its end-to-end workflow and delegates to primitives.

## Reference Navigation

| Concern | File |
|---|---|
| Build workflow (scaffold + generate + preview) | [plugins/build/impl.md](references/plugins/build/impl.md) |
| Deploy workflow (pack + publish + deploy) | [plugins/deploy/impl.md](references/plugins/deploy/impl.md) |
| Auth context (read `~/.uipath/.auth`) | [primitives/auth-context.md](references/primitives/auth-context.md) |
| Intent capture (ask folder; infer rest) | [primitives/intent-capture.md](references/primitives/intent-capture.md) |
| Auth strategy (iframe postMessage + meta-tag + PAT) | [primitives/auth-strategy.md](references/primitives/auth-strategy.md) |
| State file schema + lifecycle | [primitives/state-file.md](references/primitives/state-file.md) |
| **SDK introspection (read the actual SDK package)** | [primitives/sdk-introspection.md](references/primitives/sdk-introspection.md) |
| **Build plan (plain-language, plan-first UX)** | [primitives/build-plan.md](references/primitives/build-plan.md) |
| **Quiet execution (subagent delegation, milestone-only output)** | [primitives/quiet-execution.md](references/primitives/quiet-execution.md) |
| **Validation (tsc + API + smoke gates before success)** | [primitives/validation.md](references/primitives/validation.md) |
| Data router (intent → SDK call) | [primitives/data-router.md](references/primitives/data-router.md) |
| Chart selector (data shape → chart type) | [primitives/chart-selector.md](references/primitives/chart-selector.md) |
| Scaffold (Vite+React+shadcn+Tailwind bootstrap) | [primitives/scaffold.md](references/primitives/scaffold.md) |
| Incremental editor (diff-safe edits) | [primitives/incremental-editor.md](references/primitives/incremental-editor.md) |
| Dev server (local preview) | [primitives/dev-server.md](references/primitives/dev-server.md) |
| Deploy CLI (uip codedapp chain) | [primitives/deploy-cli.md](references/primitives/deploy-cli.md) |
| Deploy fallback (direct-API workaround) | [primitives/deploy-fallback.md](references/primitives/deploy-fallback.md) |
| Security (threat model + guardrails) | [primitives/security.md](references/primitives/security.md) |
| **Metric derivation (reasoning framework)** | [sdk/metric-derivation.md](references/sdk/metric-derivation.md) |
| **Service semantics (gotchas + opinion, NOT canonical)** | [sdk/service-semantics.md](references/sdk/service-semantics.md) |
| SDK invariants (pagination, field drift, zero-fill) | [sdk/invariants.md](references/sdk/invariants.md) |
| Intent map — **illustrative** worked examples | [sdk/intent-map.md](references/sdk/intent-map.md) |
| Scope map (SDK class → OAuth scope) | [sdk/scope-map.md](references/sdk/scope-map.md) |
| Widget anatomy (canonical structure) | [aesthetic/widget-anatomy.md](references/aesthetic/widget-anatomy.md) |
| Detail views (drill-down contract) | [aesthetic/detail-views.md](references/aesthetic/detail-views.md) |
| Design-system subset | [aesthetic/design-system.md](references/aesthetic/design-system.md) |
| Charting taxonomy + rules | [aesthetic/charting.md](references/aesthetic/charting.md) |
| Layout patterns | [aesthetic/layout-patterns.md](references/aesthetic/layout-patterns.md) |

## Anti-patterns

- **Never blend modes.** One user request = one mode. If they ask about Build and Deploy in one prompt, handle Build first, then ask about Deploy.
- **Never preload both plugin impls.** Dispatch to one; the other stays on disk.
- **Never deploy without showing the plan first.** Rule 5.
- **Never overwrite user hand edits.** Rule 8.
- **Never hardcode hex colors in widget JSX.** Always Tailwind tokens (`hsl(var(--chart-N))`). See [aesthetic/charting.md](references/aesthetic/charting.md).
- **Never write tokens to state.json or localStorage.** PATs live in `.env.local` (gitignored); runtime tokens live in memory via the SDK's token manager.
