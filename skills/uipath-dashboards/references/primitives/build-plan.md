# build-plan

## Purpose
Show the user a **plain-language plan** for the dashboard before generating any code, capture their approval and PAT in a single round-trip, then execute silently. Non-developer users who say "build me a dashboard" should NOT see file edits, npm chatter, or framework names — they should see a list of widgets, what each shows, and a single approve-or-edit prompt.

## Inputs
- User's prompt
- SDK manifest (from `sdk-introspection`)
- `auth-context` (env / orgName / tenantName)

## Outputs
A user-facing plan + an approval-blocking gate. On approval, captures:
- Confirmation token (any "go" / "yes" / "looks good" / "lgtm" / 🚀)
- Optional manual PAT override (pasted by the user) — if absent, the Build subagent reads the access token from `~/.uipath/.auth` (env-file) or `~/.uipath/.auth.json` and uses it as the SDK secret for the local preview
- Optional refinements ("drop widget X" / "add error trend instead")

## Rules
1. **No code generation before approval.** Build mode HALTS at the plan step. The user sees a plan, not a directory of files. Phase boundaries: Plan → Approval+PAT → Generate (silent) → Validate → Preview.
2. **Plain language, no jargon.** Plan describes WHAT the dashboard will show — not HOW it's built. Forbidden words in user-facing plan output: `Vite`, `Recharts`, `shadcn`, `useEffect`, `tsx`, `npm install`, `OData`, `paginate`, `filter`, `query hook`. Permitted words: `widget`, `KPI`, `chart`, `table`, `metric`, `source` (in the sense of "data source"), `last 24 hours`, etc.
3. **One approval round-trip — no PAT copy-paste.** Approval is consent-only by default; the Build subagent reads the access token from the user's `uip login` session and uses it as the SDK secret. The plan ends with: *"Reply 'looks good' to approve. I'll use your uip login session."* Manual PAT override is supported (user pastes `rt_...` in their reply) for scope-restricted previews.
4. **Approval is text-driven.** Any reply with positive sentiment (`looks good`, `lgtm`, `yes`, `ok`, `approved`, `proceed`, 🚀) is approval. If a PAT pattern (`rt_*`) is present in the reply, it overrides the session-token default. Any reply with edits ("drop X", "add Y instead") is a refinement — re-show the plan and re-prompt.
5. **The plan IS the contract.** What the plan promises is what gets built. If the agent has to deviate during Generate (e.g., a service in the plan turns out to be unavailable), it halts and surfaces the deviation as a small follow-up plan ("I planned to include a Trace Spans widget, but your tenant doesn't have that scope. Skip it, switch to Exchange-based metrics, or pause?").

## Plan format

A plan is a markdown document with these sections — no more, no fewer. Output it directly to the user:

````markdown
## 📋 Dashboard plan: <Humanized App Name>

<One-sentence description of what this dashboard answers.>

**App name** (display): <Title Case Name>           ← what shows in the dashboard Header
**Routing name** (deploy slug): gov-dashboard-<kebab>-<4rand>   ← URL slug, auto-generated

### Widgets

<For each widget, render a card-style block:>

**<Widget title>** — <time window or scope>
<One-sentence description of what the widget shows.>
*Source:* <plain-language source — e.g., "Agent invocation history (UiPath Jobs)" — never the SDK class name>.

<Repeat per widget. Group by row: 4 KPIs at top, charts in middle, tables at bottom.>

### What's also included

- **Click-through detail views** for every widget — clicking opens the underlying records.
- **Inline error handling** — if one widget can't load, the others still render.
- **Light mode** styling with UiPath brand palette and Poppins typography. No theme toggle in v1; light mode only.
- **Manual Refresh button** in the header (when relevant). Auto-refresh is intentionally excluded — dashboards are triage pages, not ops-room displays. If you need polling later, say so during refinement.

### What I'll need from you

Just your approval. I'll use the access token from your existing `uip login` session as the SDK secret for the local preview — no PAT copy-paste needed.

(If you'd rather scope-restrict the preview to a manually-issued PAT, paste it with your reply and I'll use that instead.)

### Looks good?

Reply with:
- **"looks good"** (or `lgtm`, `yes`, `approved`, etc.) to approve. I'll use your `uip login` access token and start building.
- **"looks good, here's my PAT: rt_..."** if you want to override with a scope-restricted PAT instead.
- **"change X to Y"** to refine — I'll redraw the plan and re-ask.
- **"explain widget Z"** if you want more detail on what a specific widget will show.
````

## Inferring the plan from a prompt

The agent uses `sdk-introspection` + `metric-derivation` + `chart-selector` + `service-semantics` to derive the widget list, but presents the result through this plain-language template. The trick:

1. **Run preflight introspection** per [sdk-introspection.md](sdk-introspection.md) — installs `@uipath/uipath-typescript@latest` into `<cwd>/.uipath-dashboards/.cache/sdk/`, produces a fresh manifest. This is what makes the plan answerable: without it the agent doesn't yet know what services exist. First Build pays ~20 seconds; subsequent Builds in the same workspace reuse the cache.
2. **Derive `app.name` (display)** as **Title Case** from the prompt: "build me an agent health dashboard" → `Agent Health Dashboard`. Capitalize each word; append "Dashboard" if the prompt's noun phrase doesn't already end with it. NEVER use the lowercase kebab form — that's the slug, not the title. The dashboard Header renders `app.name` verbatim.
3. **Derive `app.routingName` (deploy slug) by calling `derive-routing-name.sh`.** Do NOT hand-construct the slug — the script enforces the 32-char server cap, applies abbreviations (`observability`→`obs`, `dashboard`→`dash`, etc.), and emits the final value. Run:
   ```bash
   bash "$SKILL_DIR/assets/scripts/derive-routing-name.sh" --app-name "$APP_NAME"
   ```
   Capture stdout as `app.routingName`. Examples: `govdash-agent-obs-dash-q4n7`, `govdash-agent-health-dash-x7k2`. The plan MUST show the script's output so the slug shown to the user equals the slug persisted at scaffold-time.
4. **Decompose the user's prompt** into widget intents (per `metric-derivation.md` four-axis classification), reasoning over the manifest from step 1 — not over `intent-map.md`.
5. **For each widget, pick a chart type** (`chart-selector`).
6. **Translate technical names to plain language**:
   - `processes.getAll({filter: "PackageType eq 'Agent'"})` → *"Agent definitions in your tenant"*
   - `jobs.getAll({filter: "ProcessType eq 'Agent' and CreationTime gt <iso>"})` → *"Agent runs in the last 24 hours"*
   - `conversational-agent.exchanges.getAll({...})` → *"Agent conversation traces"*
7. **Pin the resolved SDK version** for the scaffold step. After preflight install, read `<cache>/node_modules/@uipath/uipath-typescript/package.json`'s `version` field; the project's `package.json` will use that exact version (not `^1.2.1`).
8. **Render the markdown plan** verbatim per the format above. **Both `App name` and `Routing name` lines are mandatory** — they let the user see the convention applied before approving.

The classification work is internal — the user sees only the result.

## Refinement loop

When the user replies with edits ("drop the trace widget, add task SLA instead"):
1. Reclassify the new metric (task SLA) per metric-derivation.
2. Replace the widget in the plan.
3. Re-render the plan markdown.
4. Re-prompt for approval+PAT.

PAT once collected is preserved across re-prompts (don't re-ask).

## Approval detection

Treat the user's reply as approval if positive sentiment is present (e.g., `looks good`, `yes`, `ok`, `proceed`, `approved`, `lgtm`, `let's do it`, `🚀`). PAT presence is **no longer required** — the subagent uses the access token from `~/.uipath/.auth` (env-file) or `~/.uipath/.auth.json` if no PAT was pasted.

If a PAT-shaped string (`rt_...`, 50+ char alphanumeric) IS present in the reply, treat it as a manual override and pass it to `scaffold-project.sh --pat`. If the user posts approval AND a PAT, prefer the manual PAT.

Examples of accepted replies:
- `looks good` → use uip session token
- `lgtm` → use uip session token
- `yes, here's my PAT: rt_xyz...` → use rt_xyz manually
- `🚀` → use uip session token

If sentiment is unclear, re-prompt — never proceed silently.

## Anti-patterns

- **Showing the file list during planning.** Banned. The plan describes widgets, not files.
- **Asking for the PAT separately from approval.** One round-trip — saves the user from "ok now paste your PAT" follow-ups.
- **Surfacing internal class names in the plan.** "UiPath Jobs API" is fine. "`processes.getAll({filter: ...})`" is not.
- **Defaulting to a familiar service when introspection reveals a better fit.** The plan reflects what the introspection found — including services we hadn't documented.
- **Skipping the plan step "because the prompt is simple".** Every Build starts with a plan. Even a 1-widget dashboard.
