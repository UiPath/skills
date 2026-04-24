---
name: uipath-dashboards
description: "[PREVIEW] Dashboards-as-Code for UiPath — BUILD React+shadcn/ui dashboards from prompts over TS SDK data + local preview; DEPLOY as Coded Web App via uip codedapp. For bare publish→uipath-coded-apps. For Orchestrator ops→uipath-platform."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Dashboards

CLI-first, natural-language skill that turns a prompt into a production-grade React dashboard deployed on UiPath Automation Cloud as a Coded Web App. Two modes — **Build** (scaffold/edit + localhost preview) and **Deploy** (pack → publish → deploy) — dispatched by natural-language intent detection.

## When to use

- "Build me a dashboard showing X" / "create an agent-health dashboard" → **Build**
- "Add a chart of Y to the dashboard" / "change the time window" → **Build** (incremental)
- "Deploy the dashboard" / "publish to alpha" / "ship it" → **Deploy**
- "Show me which tenant this is pointing at" → ask user (status is out of v1 scope)

Do NOT use for: bare `uip codedapp` publish/deploy of non-dashboard apps (→ `uipath-coded-apps`), Orchestrator administration (→ `uipath-platform`), or policy/compliance work (→ `uipath-governance`).

## Mode detection

Classify every invocation by these signals (user prompt + presence of `<cwd>/.uipath-dashboards/state.json`):

| Prompt signal | State file exists? | Mode |
|---|---|---|
| `deploy`, `publish`, `ship`, `push to tenant`, `release`, `upgrade` | any | **Deploy** |
| `build`, `create`, `add <widget>`, `change <x>`, `open locally`, `preview`, or a new dashboard topic | no | **Build** (scaffold) |
| Same as above | yes | **Build** (incremental) |
| Ambiguous / neither | — | **Ask the user; never guess** |

Ambiguity NEVER defaults to Deploy (Deploy mutates tenant state). Build is non-destructive re: tenant state; ambiguity may default to Build only when safe, but prefer asking.

After mode detection, read **exactly one** plugin impl:
- Build → [references/plugins/build/impl.md](references/plugins/build/impl.md)
- Deploy → [references/plugins/deploy/impl.md](references/plugins/deploy/impl.md)

Never preload both.

## Critical Rules

1. **Preflight before any cloud touch.** Run `uip login status --output json`. If `Data.Status != "Logged in"`, stop and instruct `uip login --authority https://<env>.uipath.com`.
2. **Read identity from `~/.uipath/.auth`.** Never ask the user for env / orgName / tenantName — resolve them per [references/primitives/auth-context.md](references/primitives/auth-context.md).
3. **`--output json` on every `uip` call.** Parse `Data` / `Message` from the structured response.
4. **Never cache live tenant reads.** Folder lists, job counts, deployed-app lists must hit live. Caching is reserved for templates and scaffolds.
5. **Never auto-deploy.** Every Deploy surfaces the intended plan and waits for explicit user approval (`y`/`n`).
6. **State file writes are atomic.** Write `.uipath-dashboards/state.json.tmp`, rename on success.
7. **Scopes derive from generated code, never prompted.** In secret-mode these are informational only.
8. **Never overwrite hand edits silently.** Diff before write; surface diff + confirm on edits that appear user-authored. See [references/primitives/incremental-editor.md](references/primitives/incremental-editor.md) for the diff discipline.
9. **One plugin file per dispatch.** Build reads `plugins/build/impl.md` + its primitives; Deploy reads `plugins/deploy/impl.md` + its primitives. Never both.
10. **Ambiguous prompts get a clarifying question, not a guess.**
11. **Tokens are full-user-session scoped — guardrails are mandatory.** CSP, in-memory-only tokens, gitignored `.env*`, no `console.log(sdk)`. See [references/primitives/security.md](references/primitives/security.md).
12. **No `dangerouslySetInnerHTML` with tenant data. No token in URL. No localStorage for tokens.** Incremental-editor rejects edits that introduce these.
13. **You are a dashboard expert, not a phrase-book.** For every metric the user asks about, classify it on four axes (shape / time framing / aggregation / service) per [references/sdk/metric-derivation.md](references/sdk/metric-derivation.md) and derive the SDK call from first principles. [references/sdk/intent-map.md](references/sdk/intent-map.md) is illustrative; it does not constrain what you can build. Novel metrics are the default case.
14. **Every widget routes to a real detail view.** No placeholder hashes. Generator produces `<WidgetName>.tsx` + `<WidgetName>View.tsx` + aggregated hook + list hook + route registration — all in the same Generate step. See [references/aesthetic/detail-views.md](references/aesthetic/detail-views.md).
15. **Columns in detail views are derived from service semantics, not hardcoded.** Read [references/sdk/service-semantics.md](references/sdk/service-semantics.md) "Semantic columns" for the widget's service and produce a column list covering identity + time + domain-specific dimensions.

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
| Data router (intent → SDK call) | [primitives/data-router.md](references/primitives/data-router.md) |
| Chart selector (data shape → chart type) | [primitives/chart-selector.md](references/primitives/chart-selector.md) |
| Scaffold (Vite+React+shadcn+Tailwind bootstrap) | [primitives/scaffold.md](references/primitives/scaffold.md) |
| Incremental editor (diff-safe edits) | [primitives/incremental-editor.md](references/primitives/incremental-editor.md) |
| Dev server (local preview) | [primitives/dev-server.md](references/primitives/dev-server.md) |
| Deploy CLI (uip codedapp chain) | [primitives/deploy-cli.md](references/primitives/deploy-cli.md) |
| Deploy fallback (direct-API workaround) | [primitives/deploy-fallback.md](references/primitives/deploy-fallback.md) |
| Security (threat model + guardrails) | [primitives/security.md](references/primitives/security.md) |
| **Metric derivation (reasoning framework)** | [sdk/metric-derivation.md](references/sdk/metric-derivation.md) |
| **Service semantics (SDK mental model)** | [sdk/service-semantics.md](references/sdk/service-semantics.md) |
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
