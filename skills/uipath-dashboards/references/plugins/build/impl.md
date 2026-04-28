# Build — mode impl

End-to-end workflow for Build mode. Dispatched from SKILL.md when the user's intent is scaffold-or-edit a dashboard. **Read this file only when Build is the chosen mode; never preload alongside `deploy/impl.md`.**

## Preamble (every Build invocation)

### Step 0 — Preflight
Read [../../primitives/auth-context.md](../../primitives/auth-context.md). Run `uip login status --output json`. Halt if not logged in.

### Step 1 — Classify invocation
Resolve project location per [../../primitives/intent-capture.md](../../primitives/intent-capture.md): `<cwd>/.uipath-dashboards/<kebab-name>/`. Then check `<project>/.dashboard/state.json`:
- Absent → **first-run Build** (go to [First-run branch](#first-run-branch))
- Present → **incremental Build** (go to [Incremental branch](#incremental-branch))

---

## First-run branch

Pipeline: `Plan → Approve+PAT → Scaffold → Configure → Generate (silent) → Validate → Preview`

The user is non-developer by default. They see a plain-language plan, give one approval, and get a working dashboard URL. Everything between approval and "your dashboard is ready" is delegated to a subagent and surfaced as high-level milestones — NOT file edits or npm chatter. See [../../primitives/quiet-execution.md](../../primitives/quiet-execution.md).

### Plan
Delegate to [../../primitives/build-plan.md](../../primitives/build-plan.md). This:
1. Runs **preflight SDK introspection** per [../../primitives/sdk-introspection.md](../../primitives/sdk-introspection.md). Bootstraps a workspace-scoped cache at `<cwd>/.uipath-dashboards/.cache/sdk/`, runs `npm install @uipath/uipath-typescript@latest`, introspects the result. First Build in a workspace pays ~20 seconds; subsequent Builds reuse the cache. The plan reasons over the resulting manifest, NOT over `intent-map.md`.
2. Pins the resolved SDK version (read from `<cache>/node_modules/@uipath/uipath-typescript/package.json`) for the scaffold step's `package.json`.
3. Decomposes the prompt into widget intents (per `metric-derivation`) and chart types (per `chart-selector`).
4. Renders a markdown plan: humanized title + description + widget cards (title, description, plain-language source) + cross-cutting features (light/dark, click-through, error isolation) + a single approval-and-PAT prompt.
5. **HALTS until the user approves.** No code generation happens before approval. If the user requests refinements ("drop X, add Y"), reclassify and re-render the plan; re-prompt for approval.

### Approve
The user's reply must include positive sentiment. PAT is optional — the subagent reads the access token from the user's `uip login` session (`~/.uipath/.auth` env-file or `~/.uipath/.auth.json` JSON) if no manual PAT is pasted. On approval:
1. **Do NOT write any files in the main agent.** The token read, the project directory, the templates, the state.json — all of it is the subagent's job. See [../../primitives/quiet-execution.md § One Task call covers everything](../../primitives/quiet-execution.md). The main agent's role from this point until the dev server is ready is exactly: emit one progress line, issue ONE Task call, wait, emit a friendly summary.
2. Capture: the approved plan, the resolved project path (per intent-capture: `<cwd>/.uipath-dashboards/<app.name>/`), `auth-context` output, AND the manual PAT (if the user pasted one — otherwise empty so the subagent reads from the auth file). These become the Task's prompt payload.
3. Proceed to Build (delegated).

### Build (delegated to a subagent)

This step covers what previous drafts split into Scaffold + Configure + Generate + Validate. They all happen inside a single Task call so the user's chat stays clean. The main agent issues:

```
Task({
  description: "Build dashboard end-to-end",
  prompt: "<plan json + PAT + auth context + project path + skill-dir + cache-dir + reference paths>",
  subagent_type: "general-purpose"
})
```

#### Subagent throughput discipline (cuts wall-clock by ~50%)

The subagent's wall-clock is dominated by LLM round-trip latency, not subprocess work. Three rules drastically reduce that:

1. **Boot-time parallel reads.** First message in the subagent issues ALL reference-file reads in parallel (one tool-use block with multiple `Read` calls). Read these in one shot at boot:
   - `references/primitives/data-router.md`
   - `references/primitives/chart-selector.md`
   - `references/primitives/metric-derivation.md`
   - `references/primitives/validation.md`
   - `references/aesthetic/widget-anatomy.md`
   - `references/aesthetic/detail-views.md`
   - `references/aesthetic/layout-patterns.md`
   - `references/sdk/service-semantics.md`
   - `references/sdk/invariants.md`
   - The pre-introspected `<cache>/sdk-manifest.json`
   - The skill assets dir listing for `assets/templates/widgets/` and `assets/templates/views/`
   
   Eight serial reads ≈ 24 seconds; one parallel batch ≈ 3 seconds. Free 21-second win.

2. **Single-shot scaffold script.** The Scaffold sub-step (templates render + npm install + shadcn init/add + restore index.css/tailwind.config.ts + sanity checks) is a single bash invocation:
   ```bash
   bash "$SKILL_DIR/assets/scripts/scaffold-project.sh" \
     --skill-dir "$SKILL_DIR" \
     --project-path "$PROJECT_PATH" \
     --cache-dir "$CACHE_DIR" \
     --app-name "$APP_NAME" \
     --routing-name "$ROUTING_NAME" \
     --org-name "$ORG_NAME" \
     --tenant-name "$TENANT_NAME" \
     --env "$ENV" \
     --base-url "$BASE_URL" \
     --env-infix "$ENV_INFIX" \
     --semver "$SEMVER" \
     --pat "$PAT" \
     --sdk-version "$SDK_VERSION" \
     --output json
   ```
   `--app-name` MUST be the Title Case display name (e.g., `"Agent Health Dashboard"`). `--routing-name` MUST be the `gov-dashboard-<kebab>-<4rand>` slug computed during the Plan phase. If `--routing-name` is omitted, the script derives it from `--app-name` as a defensive fallback — but the Plan-phase agent should always compute and pass it so the user sees the exact slug in the plan before approval.
   Replaces ~30 `Write` calls (templates) + 5 `Bash` calls (npm install, shadcn init/add, restores) with **one** `Bash` call. Saves ~60-90 seconds. The script returns a JSON evidence object (including the `appName` and `routingName` it persisted) that the subagent passes through to the main agent.

3. **Per-widget parallel writes.** Each widget bundle is 4 files (widget tsx, view tsx, query hook, list hook). Write all 4 in a single message with parallel `Write` calls. 12 widgets × (1 round-trip with 4 parallel writes) ≈ 36 seconds; 12 widgets × (4 sequential writes) ≈ 144 seconds. Free 100-second win.

The Task subagent runs the pipeline (each sub-step still delegates to the primitive listed below, but invisibly):

#### Scaffold (one Bash call)
Delegate to `assets/scripts/scaffold-project.sh` (see [../../primitives/scaffold.md](../../primitives/scaffold.md) for the script's contract). One invocation handles:
1. Renders all `assets/templates/scaffold/*.template` files into `./<kebab-name>/` with `{{var}}` substitutions.
2. Writes `.env.local` with the PAT (gitignored, NOT a template — PAT never lands in templates).
3. Writes initial `.dashboard/state.json`.
4. Pins the resolved `@uipath/uipath-typescript` version (from preflight cache) into the project's `package.json`.
5. Runs `npm install`.
6. Reuses the preflight `<cache>/sdk-manifest.json` → `<project>/.dashboard/sdk-manifest.json` when SDK version matches (no per-project introspection needed).
7. Runs `npx shadcn@latest init` and `npx shadcn@latest add card button badge table chart separator skeleton`.
8. Restores `src/index.css` and `tailwind.config.ts` from our templates (shadcn overwrote them).
9. Pins `tailwindcss@^3.4.13` if shadcn bumped to v4.
10. Runs sanity checks (UiPath orange HSL present, Poppins link present, chart.tsx present, no oklch leftover) and emits a JSON evidence object.

The subagent calls this once; on `ready: false` from the script, surface the errors array and halt.
7. Pins `tailwindcss: ^3.4.13` in devDependencies (prevents v4 upgrade conflict with our v3-style config).
8. Runs end-to-end sanity checks (UiPath orange HSL value present, no leftover oklch, tailwindcss v3 installed, chart.tsx exists). Halts on any check failure — do NOT hand a broken CSS pipeline to the dev server.

#### Configure
Delegate to [../../primitives/intent-capture.md](../../primitives/intent-capture.md). This:
1. Derives `app.name` / `routingName` as kebab-case from the prompt.
2. Reads `auth-context` for env / orgName / tenantName.
3. **Does NOT fetch a folder list by default.** Folder is a Deploy concern (which Orchestrator folder hosts the deployed app) and is resolved by [../deploy/impl.md § Step 2](../deploy/impl.md). ONLY exception: if the user's prompt explicitly scopes to a folder ("for the Finance folder", "in X folder"), resolve it at Build time and write to `state.json.folderKey` so generated query hooks pass it through.
4. Writes initial `<project>/.dashboard/state.json` — typically with `folderKey: null`. Project itself sits at `<cwd>/.uipath-dashboards/<kebab-name>/`.

#### Generate (still inside the same subagent)

The subagent already has: approved plan, scaffolded project, state.json, the dashboard/sdk-manifest.json. **Step 0 — SDK manifest already produced** during Plan phase by sdk-introspection.

For each widget in the approved plan:
1. **Route intent** per [../../primitives/data-router.md](../../primitives/data-router.md) → SDK call spec `{service, method, filter, fieldsProjected, scope, aggregation}`.
2. **Pick chart** per [../../primitives/chart-selector.md](../../primitives/chart-selector.md) → `{chartType, widgetTemplate, chartConfig, dataMapping}`.
3. **Render widget** — copy `assets/templates/widgets/<chartType>.tsx.template` → `<project>/src/dashboard/widgets/<PascalCaseName>.tsx` with substitutions for series names, colors, data-hook name. Widget's drill-down href points at `/<kebab-slug>` — a REAL route.
4. **Render two query hooks** — (a) `<project>/src/lib/queries/<kebab>.ts` returns the widget's aggregated shape; (b) `<project>/src/lib/queries/<kebab>-list.ts` returns the same SDK call without aggregation — the full rows behind the summary. Used by the detail view.
4a. **Render detail view** — copy `assets/templates/views/detail-view.tsx.template` → `<project>/src/dashboard/views/<PascalCaseName>View.tsx`. View is thin — it calls `<RecordsTable rows={...} columns={[...]} />` from chrome; columns are derived by reasoning about the service's canonical entity type per [../../sdk/service-semantics.md](../../sdk/service-semantics.md) (Jobs → jobId/agent/state/startTime/duration; Tasks → taskId/assignee/taskSlaDetail.status/createdTime; etc.) — not hardcoded. Title/description mirror the widget's; description states the filter in English.
4b. **Register route** — append `<Route path="/<kebab-slug>" element={<WidgetNameView sdk={sdk} />} />` to `src/app/App.tsx`'s `<Routes>`. One route per widget.
5. **Compose `Dashboard.tsx`** per [../../aesthetic/layout-patterns.md](../../aesthetic/layout-patterns.md) — KPI row on top, primary chart next, secondaries in 2-up grid, tables last. **Every widget MUST be wrapped in `<WidgetBoundary label="…">`** so a throw in one widget doesn't take down the whole dashboard. Without per-widget boundaries, a single SDK shape drift or missing scope renders the entire page as "A widget crashed" and all other widgets go dark. The top-level `ErrorBoundary` in `App.tsx` is a last-resort catch for unrecoverable chrome errors only.
6. **Render auth wiring** — `<project>/src/lib/auth-strategy.ts` per [../../primitives/auth-strategy.md](../../primitives/auth-strategy.md).
7. **No theme toggle.** Dashboards default to light mode and stay there. The chrome no longer ships `ThemeToggle.tsx` or `theme.ts`; `Header` doesn't wire a toggle. Dark-mode CSS variables remain dormant in `index.css` for future use. See [../../aesthetic/design-system.md § Light mode only](../../aesthetic/design-system.md).
8. **Render SECURITY.md** — warn about full-session-token scope per [../../primitives/security.md](../../primitives/security.md).

#### Validate (still inside the same subagent)
Delegate to [../../primitives/validation.md](../../primitives/validation.md). Three passes:
1. **Type check** — `npx tsc --noEmit`. Self-heal common cases (raw `jobError` → `formatJobError`, missing `Tasks.dueDate` → `taskSlaDetail.status` via `taskSlaStatusOf`, etc.). Up to 3 self-heal iterations.
2. **API existence check** — for each generated query hook, verify every `<class>.<method>(...)` call corresponds to an entry in `sdk-manifest.json`. Surface "did you mean..." for typos; halt for genuine misses.
3. **Smoke check** — boot dev server in the background for 5s, scan output for resolution / module-not-found errors. Halt on any.

Validation must pass before Preview claims success. If it can't, surface a friendly summary per `validation.md` § "Failure surface" with explicit recovery offers (skip widget, switch service, pause).

### Preview (back in the main agent)
Once the Task subagent returns `{port, widgets, errors?, ready: true}`, the main agent emits the friendly summary per [../../primitives/quiet-execution.md § "Two messages"](../../primitives/quiet-execution.md). It does NOT make any further tool calls — the dev server is already running (the subagent left it running in the background as its last action). PAT was written by the subagent during Build; `.env.local` is populated.

For documentation completeness — the steps the SUBAGENT performed during the Build phase to bring up the server were:
1. Verifies `.env.local` has `VITE_UIPATH_PAT=<non-empty>`.
2. Runs `npm run dev` in `<project>`.
3. Captures Vite's chosen port (auto-bumps from 5173 if busy).
4. Emits the final user-facing summary per [../../primitives/quiet-execution.md § "Two messages"](../../primitives/quiet-execution.md). The summary is GENERATED from the approved plan — it describes what the dashboard tracks and how to navigate it (per-widget bullets, click-to-drill, refresh, deploy hint). It does NOT list build milestones (no `✓ Project scaffolded`, no `✓ SDK introspected`, no `✓ Type-check passed` — those are internal mechanics, not user-facing). Tone: conversational, present-tense, talks about the dashboard's data, not its assembly.
5. Leaves dev server in foreground.

---

## Incremental branch

Pipeline: `Read → Plan → Diff → Apply → Reload`

### Read
Load existing `<project>/src/dashboard/Dashboard.tsx`, every `<project>/src/dashboard/widgets/*.tsx`, every `<project>/src/lib/queries/*.ts`. Build an in-memory model of widgets + queries.

### Plan
Interpret the user's new prompt as **diffs** against the current dashboard:
- "add a chart of queue throughput" → ADD widget + query + insert into `Dashboard.tsx`.
- "change the error-rate threshold to 5%" → EDIT constant in error-rate widget.
- "remove the active-agents KPI" → DELETE widget file + remove import/JSX from `Dashboard.tsx` + remove orphaned query.

### Diff (Critical Rule 8)
For every file you plan to write:
1. Read current file content.
2. Compute diff.
3. If diff touches lines that appear user-edited (renamed variables, added comments, restructured layout, formatting changes), **stop and show the diff + ask for confirmation before writing**.

### Apply
Write approved edits. Recompute scope allowlist via [../../sdk/scope-map.md](../../sdk/scope-map.md); update `state.json.scopes` (informational in secret-mode).

### Reload
If `npm run dev` is already running, Vite HMR picks up changes. If not, instruct user to re-run.

---

## Narration

Narrate each stage back to the user as it runs. This is how "dashboards-as-code" feels alive:

```
✶ Building: "<prompt excerpt>"

→ Scaffolding Vite+React+shadcn/ui in ./<kebab>/ ... done
→ Configuring: env=<env>, org=<org>, tenant=<tenant>, folder=<folder>
→ Intent parsing:
    • <Widget 1 intent> → <chart type>
    • <Widget 2 intent> → <chart type>
    ...
→ Chart selection:
    • <Widget> → <template>
    ...
→ Generating:
    • src/dashboard/widgets/<File>.tsx
    ...
→ Paste your UiPath PAT into .env.local as VITE_UIPATH_PAT=... (generate at <env>.uipath.com/<org>/portal_/profile/personal-access-token — note: no tenant segment)
→ Starting dev server ...
→ Dashboard preview: http://localhost:<port>/ — Ctrl+C to stop.
```

## Error paths

| Condition | Action |
|---|---|
| Not logged into `uip` | Halt at Step 0; instruct `uip login`. |
| Prompt too vague ("a dashboard") | Ask specifics (what data? what time window?) before scaffolding. |
| Data-router can't map intent to an SDK call | Ask user to rephrase; link to [../../sdk/intent-map.md](../../sdk/intent-map.md). |
| Folder list empty | Report permissions issue; do NOT write a broken state.json. |
| `npm install` fails | Surface stderr; suggest common fixes (Node version, registry unreachable). |
| `shadcn init` fails | Surface stderr; halt — unfinished scaffold is worse than loud failure. |
| Port 5173 busy | Vite auto-bumps; report chosen port. |
| Hand-edited widget + rebuild change to it | Surface diff; ask confirmation before writing. |
