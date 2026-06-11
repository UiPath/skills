# Dashboard Capability

Build, edit, or deploy UiPath dashboards powered by Insights RTM and the TypeScript SDK.

---

## Step 0 — Detect intent BEFORE loading anything

Read the user's message and classify it as one of three intents. **Do not load any files yet.**

| User says | Intent | What to do next |
|-----------|--------|-----------------|
| "build me a dashboard", "show me X metrics", "create a dashboard for…" | **BUILD** | Follow the Build path below |
| "add/remove/change a widget", "update the chart", "make it 7 days" | **EDIT** | Follow the Edit path below |
| "deploy this", "publish it", "make it live", "ship it to the team", "deploy the dashboard" | **DEPLOY** | Follow the Deploy path below |

If the intent is unclear, ask one question — "What do you want to do with the dashboard?" — as a **structured choice** (SKILL.md Critical Rule 17: native question tool with selectable options when the host agent has one, else a numbered list):

| Option | Description |
|--------|-------------|
| **Build a new dashboard** | Describe metrics in plain language, get a live dashboard |
| **Edit the existing one** | Add/remove/change widgets or time ranges |
| **Deploy it** | Publish to Automation Cloud |

---

## Path A — BUILD (new dashboard)

## Turn 2 output — Show the plan (zero tool calls, zero intermediate output)

After all reads complete and pre-warm is fired, output the plan as the first and only text.

**The user should see nothing between their request and the plan.** No "Reading files…", no "Checking login…", no "Starting pre-warm…". Pure silence then the plan.

If you need to show something, show only the plan.

### Turn 2 — Everything in ONE parallel message

Fire all of these simultaneously. Use multiple tool calls in one response — do not wait for one before starting another.

> **Path note:** All file paths are relative to `SKILL_BASE_DIR` — the directory where `SKILL.md` lives. Not relative to this file's location.

**File reads (parallel) — fire all in one message:**

| File | Purpose |
|------|---------|
| `references/dashboards/plugins/build/impl.md` *(from skill root)* | Build instructions, plan format, intent.json schema |
| `references/dashboards/primitives/tier-resolution.md` *(from skill root)* | Metric classification and SDK validation rules |
| `references/dashboards/aesthetic/layout-patterns.md` *(from skill root)* | Layout rules |
| `references/dashboards/aesthetic/charting.md` *(from skill root)* | Chart-type selection, colour tokens, delta polarity |
| `assets/scripts/capability-registry.json` *(from skill root)* | Metric catalog (T1/T2 display hints) |
| `references/sdk/agents.md` *(from skill root)* | Agents + Agent Memory (Insights RTM, SDK ≥ 1.4.0) — validate agent/memory metrics |
| `references/sdk/orchestrator.md` *(from skill root)* | Jobs/Queues/Processes methods — validate job/process metrics |

**Conditional reads (add to the same parallel message if the request mentions these):**

| If user mentions | Also read |
|-----------------|-----------|
| tasks, action items | `references/sdk/action-center.md` *(from skill root)* |
| cases, process instances, Maestro | `references/sdk/maestro.md` *(from skill root)* |
| governance, policy, compliance, denials | `references/sdk/governance.md` *(from skill root)* |

**2 commands (same message):**

```bash
uip login status --output json
```

```bash
node -e "
const fs = require('fs')
fs.existsSync('.dashboard/state.json') ? process.exit(0) : process.exit(1)
" && echo INCREMENTAL || echo FRESH
```

**Pre-warm (same message — `run_in_background: true` on the Bash tool call):**

Derive the routing name from the user's request now (e.g. `"agent health dashboard"` → `"agent-health-x7k2"`). Pass **only the routing name**, not a full path. The build script creates `<cwd>/<routing-name>` — project lands in the current working directory.

```bash
node "<SKILL_BASE_DIR>/assets/scripts/build-dashboard.mjs" --prewarm "<ROUTING_NAME>"
```

⚠️ `run_in_background: true` is a tool call parameter, not a shell flag. Without it, the call blocks for 60–90s before the plan appears.

> **What the user should see:** Only the plan text. Nothing else — not file reads, not login output, not pre-warm status, not bash results, and no question popup. If there is ANY output before the plan, or any tool call in the plan response, that is a bug.

**After all reads:** output the plan as **pure text** and stop — zero tool calls in the plan response. The user replies with feedback or confirmation; setup questions (OAuth client ID, via the structured-choice tool) come only AFTER the plan is approved, and only for details the confirmation didn't already provide. See `plugins/build/impl.md` Phases 2–3.

**Routing:**
- `INCREMENTAL` → read `primitives/incremental-editor.md`, then follow it
- `FRESH` → follow `plugins/build/impl.md`

---

## Path B — EDIT (change existing dashboard)

Read `primitives/incremental-editor.md` in the same message as `uip login status --output json`. Follow it.

**Also read `primitives/customization.md` first** when the user asks for look-and-feel changes (theme, layout, styling, "make it look…") or the project shows hand edits — it defines what the build script overwrites and when to edit the project directly instead of running the script.

---

## Path C — DEPLOY

### Step 1 — Read the deploy plugin FIRST (before any CLI commands)

```
Read: references/dashboards/plugins/deploy/impl.md  *(from skill root)*
```

Read this file in parallel with:

```bash
uip login status --output json
```

**Do not run any other commands until you have read the deploy plugin and presented the plan to the user.**

### Step 2 — Present the deploy plan (pure text, zero CLI calls)

Read `.dashboard/state.json` in memory to get the app name, version, and routing name. Then output the plan:

```
Your **[Dashboard Name]** is ready to be deployed.

📦  Version:    [current] → [bumped]
🔗  URL path:   [routing-name]
📁  Folder:     AdminDashboards
🔄  Type:       Fresh deploy  OR  Updating existing deployment

📌  Do you want to pin this dashboard to the Governance UI?
   → "deploy and pin" — visible in the Governance section
   → "deploy" — deploy without pinning
```

**HALT. Do not run any CLI command until the user confirms.**

### Step 3 — Follow plugins/deploy/impl.md

After user confirms, follow every step in `plugins/deploy/impl.md` exactly as written. Do not invent steps, do not run `uip tools list`, do not run `npm run build` before the plan is confirmed.

---

## Scope

This skill only handles dashboard building, editing, and deploying. For anything else, respond:

> "This skill is for UiPath dashboard generation only. For [what they asked], please use the appropriate skill."

---

## Hard stops

- **Never** show raw tool call outputs to the user — read results in context, surface only meaningful information
- **Never** echo raw event names (WIDGET_READY, TSC_PASS, BUILD_RESULT, etc.) — translate them to clean progress lines
- **Never** show intermediate bash command outputs between the user's request and the plan — the plan is the first visible output
- **Never** call any tool — including the question/option tool — in the same response as the plan. The plan is pure text; the user replies to it; structured setup questions (OAuth, deploy pin) fire only after approval and only for details the user hasn't already given
- **Never** run ANY CLI command before presenting the plan and getting user confirmation
- **Never** improvise deploy steps — always read `plugins/deploy/impl.md` first
- **Never** run `uip tools list`, `npm run build`, or any command not in the relevant impl.md
- **Never** use `"agent-health-dashboard"` (routing slug) as the `-n` flag — always use the human-readable display name from state.json
- **Never** run `uip codedapp publish` without `-n` and `--version` flags
- **Never** fetch the live SDK docs URL — it takes 60–90s
- **Never** read `build-dashboard.mjs` — documented in impl.md
- **Never** run directory exploration via ANY shell — `ls`, `find`, `dir`, `Get-ChildItem`, `tree`, glob loops. Memory or prior-session hints are not a reason to explore; the state.json check is the only existing-work probe
- **Never** read files one at a time
- **Never** commit generated dashboard files
- **Never** auto-deploy without explicit user confirmation
