# UiPath Dashboard Skill — Bug Bash Scenarios

Manual test scenarios for the `uipath-coded-apps` natural-language **dashboard** capability (compiler architecture: metric modules + two-stage compile + versioning). Designed for an internal bug bash — work through each row, mark pass/fail, and log anything odd in the **Defects** column.

> The three tables below paste straight into Confluence (Confluence auto-converts a Markdown table). Steps and outcomes use line breaks within the cell.

### Prerequisites (do once before starting)

- A coding agent (Claude Code / Codex / Gemini CLI) with the **uipath-coded-apps** skill loaded from the `feat/dashboard-compiler-arch` branch.
- Logged in to a **UiPath tenant that has some agent + job data** (via the `uip` CLI).
- Able to **create an external OAuth app** (or have a non-confidential `clientId` handy) — needed for live data in the browser.
- **Node 20+** and network access (the build runs `npm ci`).
- Unless a scenario says otherwise: start each one in a **fresh agent session**. "Build" scenarios use an **empty working folder**; "edit/upgrade" scenarios **reuse a folder that already has a built dashboard**.
- Record tester name + date at the top of the Confluence page.

---

### 1. Happy Path

| Scenario | Steps | Expected Outcome | Defects |
|----------|-------|------------------|---------|
| **H1 — Build a dashboard from a prompt** | 1. New agent session in an empty folder.<br>2. Prompt: *"Build me a UiPath agent operations dashboard: active agents, faulted agent jobs, agent memory entries over the last 30 days, and agent failure rate %."*<br>3. Read the plan the agent presents.<br>4. Approve it (e.g. *"looks good, build it"*).<br>5. When asked about auth, let it create the OAuth app (or paste a client ID). | Agent shows a **plain-text plan** (widget list + time ranges, refused items called out) — **no code, no JSON, no file dumps**.<br>After approval you see only `Building …` then a **milestone block** (`✓ <widget>` lines, `✓ All code validated`) and a `http://localhost:57173` link.<br>**You do NOT see a flood of `Write(intent.json)` / `Write(metrics/*.ts)` messages.**<br>Build finishes with no errors. | |
| **H2 — View live data** | 1. After H1, open `http://localhost:57173`.<br>2. Complete the OAuth sign-in.<br>3. Inspect each widget. | Dashboard renders. KPI cards show a number + label; charts show a headline value, a delta badge, and a plotted series; tables show rows with **readable column headers and formatted values** (dates, durations, percentages).<br>No blank/empty widgets, no literal `undefined`/`NaN`, no error that blocks the page. | |
| **H3 — Drill into a chart** | 1. On the dashboard, click a **chart** widget (e.g. the memory/area chart).<br>2. Review the detail view.<br>3. Use the back link. | Navigates to a **detail page with record-grain rows** (individual records, not the chart's aggregated buckets), sortable, with sensible columns.<br>Back link returns to the dashboard. | |
| **H4 — Add a widget (incremental)** | 1. In the project folder, prompt: *"Add a widget for the top 10 memory spaces."*<br>2. Approve if asked.<br>3. Refresh `localhost:57173`. | Agent makes a **single incremental edit** (not a full rebuild).<br>The new widget appears after hot-reload; **existing widgets are unchanged**.<br>Again, no flood of file-edit messages. | |
| **H5 — Change a widget** | 1. Prompt: *"Change the agent failure-rate chart to cover the last 7 days"* (or *"make the faulted-jobs widget a bar chart"*).<br>2. Refresh. | Only that widget updates — the new time window is reflected in the subtitle **and** the data (or the new chart type renders). Other widgets untouched; app still compiles. | |
| **H6 — Upgrade an existing dashboard** *(needs a version gap — e.g. after a skill update that bumps the scaffold)* | 1. Open / edit a dashboard whose `.dashboard/state.json` `versions.scaffold` is **older** than the shipped version.<br>2. Note the agent's message.<br>3. Confirm the upgrade. | Agent tells you a **newer dashboard scaffold is available** (shows from → to) and **offers** — it never upgrades silently.<br>On confirm, the app is regenerated, **your metrics/widgets are preserved**, the app still compiles, and `state.json` `versions.scaffold` is updated to current. | |

---

### 2. Negative Scenarios

| Scenario | Steps | Expected Outcome | Defects |
|----------|-------|------------------|---------|
| **N1 — Unsupported metric mixed with valid ones** | 1. Prompt: *"Build a dashboard with agent latency over time, agent cost in dollars, and faulted jobs."*<br>2. Read the plan. | The **unsupported** metrics (agent latency timeline, dollar cost) are **refused inline** (struck through / flagged) with a **suggested alternative**, while the valid metric (faulted jobs) is still planned and built.<br>The whole dashboard is **not** abandoned because of the unsupported items. | |
| **N2 — Build with no OAuth client (auth missing)** | 1. Build a dashboard but **decline** to create/provide a client ID (*"skip auth for now"*).<br>2. Let it build.<br>3. Open `localhost:57173`. | Build still **completes** (compiles + serves), but the agent **clearly warns** auth won't work without a client ID, and the browser shows a **clear auth/config message** — not a blank white screen or a cryptic stack trace. | |
| **N3 — Ambiguous prompt** | 1. Prompt something vague: *"show me agent errors."*<br>2. Observe. | Agent asks **one focused clarifying question** (e.g. faulted agent jobs vs governance denials) rather than guessing and building the wrong thing. A free-text answer is accepted. | |
| **N4 — Edit a widget that doesn't exist** | 1. On an existing dashboard, prompt: *"Remove the revenue widget"* (one that isn't there).<br>2. Observe. | Agent reports the widget **isn't present** with a clear message, makes **no destructive change**, and the dashboard is untouched. No crash, no half-applied edit. | |

---

### 3. Monkey Testing (chaos / unexpected input)

| Scenario | Steps | Expected Outcome | Defects |
|----------|-------|------------------|---------|
| **M1 — Totally vague prompt** | 1. Prompt only: *"build me a dashboard"* (no specifics).<br>2. Observe. | Agent **asks what to track** or **proposes a sensible default set** with a plan for approval. It does **not** silently build an empty or random dashboard. | |
| **M2 — Oversized request** | 1. Prompt: *"Build a dashboard with 15 widgets covering every agent, job, memory and governance metric you can."*<br>2. Review the plan, then the build. | Agent produces a **coherent plan** (it may trim/group and say what it dropped and why). Build **completes without timing out** and without broken/empty widgets. Refused metrics are **called out**, not silently dropped or faked. | |
| **M3 — Off-topic request** | 1. In a session where the skill could load, prompt: *"Write me a poem about robots"* or *"Build me a login form."*<br>2. Observe. | The dashboard skill **does not hijack** the request or try to build a UiPath dashboard for it. Either it doesn't trigger, or it declines and clarifies it builds UiPath **data dashboards**. | |
| **M4 — Contradictory / rapid edits in one message** | 1. On an existing dashboard, prompt: *"Add a faulted-jobs widget, then remove it, then change all charts to bar charts"* — all in one message.<br>2. Observe + refresh. | Agent batches the edits sanely (ideally one run). **End state is consistent** — no leftover/orphan widget, no duplicate, no broken layout or dangling drill-down route — and the app still compiles. | |

---

### How to log a defect

In the **Defects** column, note: what you did, what you expected, what actually happened, and (if visible) any error text or screenshot link. Mark the row **PASS** / **FAIL** / **PARTIAL**. Keep `intent.json`, the `metrics/` folder, and `.dashboard/state.json` from a failing run — they're the fastest way for us to reproduce.
