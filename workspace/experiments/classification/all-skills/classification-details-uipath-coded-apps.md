# Classification Details — uipath-coded-apps

**Classification: Partial**

---

## What the Skill Teaches

Scaffolding, building, debugging, and deploying UiPath Coded Web Apps and Coded Action Apps, including the SDK pagination pattern, OAuth scope validation, action-schema validation, dashboard generation from natural language, and UI widget integration.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | **Build → Pack → Publish → Deploy lifecycle** | **Yes — TRANSFORM-PIPELINE** | Ordered sequence: `npm run build` → `uip codedapp pack` → `uip codedapp publish` → `uip codedapp deploy`; no judgment between steps |
| 2 | **SDK pagination loop (cursor-based `while hasNextPage`)** | **Yes — EXTRACT** | Fixed cursor-loop pattern required for any list that may exceed the server's default cap |
| 3 | Action-schema validation | No | Already scripted (`scripts/validate-action-schema.js`) |
| 4 | **Folder key resolution (name → GUID)** | **Yes — EXTRACT** | Fixed lookup: `uip or folders list --all --name "<name>" --output json`, match on exact `Name`, read `Key` |
| 5 | OAuth scope validation for SDK services | Marginal | Lookup via `node_modules/.../oauth-scopes.md`; small, reference-heavy, not worth standalone script |
| 6 | Dashboard generation from natural language description | No | Judgment; translates user's NLP description to React + SDK calls, requires design decisions |
| 7 | App scaffolding (Vite setup, `vite.config.ts`, SDK config) | No | Judgment; app type, routing, component design |
| 8 | Widget integration (Validation Station, DataTable, chat, PDF viewer) | No | Judgment; widget selection, prop configuration, layout decisions |
| 9 | App type detection (Coded Web App vs Coded Action App) | Marginal | Single routing question; too thin for standalone script |

---

## Codifiable Procedures (not yet scripted)

### 1. Build → Pack → Publish → Deploy Pipeline — TRANSFORM-PIPELINE

**Source:** `skills/uipath-coded-apps/SKILL.md` §Quick Deploy (Full Pipeline)

**What it does:** Executes the full deployment sequence: check login status, run `npm run build` and verify `dist/` exists, run `uip codedapp pack dist -n <name> --version <version>`, run `uip codedapp publish` (with `-t Action` flag for action apps), resolve folder GUID, and run `uip codedapp deploy -n <name> --folder-key <GUID>`. Inputs: app name, version, folder name or key. Output: deployed app URL from `app.config.json`. Line 175: `"Do NOT pause between steps to ask 'should I continue?' — execute the full pipeline. Only stop if you need auth credentials or an app name."`

**Why it's mechanical:** Each step produces a well-defined artifact consumed by the next; branching is limited to action vs web app (one flag difference) and folder key resolution (one CLI lookup). No design or coding judgment is needed.

**Turn savings:** Without a script, the agent runs each step separately across 4–5 turns, checking output between each; a script completes the pipeline in one turn.

---

### 2. SDK Pagination Loop — EXTRACT

**Source:** `skills/uipath-coded-apps/SKILL.md` §Critical Rules (Rule 14)

**What it does:** Accumulates all pages from any SDK list call by looping `while (page.hasNextPage) { page = await getAll({ cursor: page.nextCursor }) }` and collecting `items` from each page. Applies to `getAll`, `getAllRecords`, `queryRecordsById`, `getFileMetaData`, etc. Inputs: initial SDK list call and service handle. Output: accumulated items array. Line 53: `"To list every row from a source that may exceed the cap, you MUST loop the cursor: while (page.hasNextPage) { page = await getAll({ cursor: page.nextCursor }) } and accumulate items."`

**Why it's mechanical:** The loop pattern is fixed and applies identically to every SDK service that returns paginated results — only the initial call and item property name vary.

**Turn savings:** Currently the agent writes this cursor loop inline each time it needs a full list; a shared utility function or code snippet reduces repeated manual authoring.

---

### 3. Folder Key Resolution — EXTRACT

**Source:** `skills/uipath-coded-apps/SKILL.md` §Critical Rules (Rule 11)

**What it does:** Resolves a human-readable folder name to its GUID for `uip codedapp deploy`. Runs `uip or folders list --all --name "<name>" --output json`, matches the row whose `Name` exactly equals the target (not prefix/contains), and reads its `Key`. For personal workspace folders, uses `uip or folders list --output json` filtering on `Type == "Personal"`. For a missing folder, creates it with `uip or folders create "<NAME>" --output json` and reads `Data.Key`. Line 50: `"never just take the first row — a personal workspace is not in --all — resolve it from the default uip or folders list --output json where Type == 'Personal'."`

**Why it's mechanical:** The lookup sequence is deterministic — the exact CLI commands, field names, and match conditions are specified; no judgment is needed.

**Turn savings:** Without a script, the agent runs the list command, parses JSON, and finds the matching row across 2–3 turns; a script resolves the folder key in one call.

---

## Justification for Classification

**Partial** — not Strong, not None.

**Why not Strong:** The largest portions of the skill — dashboard generation from natural language, app scaffolding and UI design, widget integration, and SDK service integration — are judgment-intensive coding tasks. The codifiable procedures (deployment pipeline, pagination, folder resolution) are mechanical helpers that support app delivery but do not constitute the dominant surface of what the skill teaches.

**Why not None:** The build→pack→publish→deploy lifecycle is an explicit ordered TRANSFORM-PIPELINE with no judgment between steps; the SDK cursor-loop is a EXTRACT pattern the skill mandates for all list calls; action-schema validation is Already scripted.

**Evidence locations:**
- Deployment pipeline: `skills/uipath-coded-apps/SKILL.md` §Quick Deploy (Full Pipeline) (lines 173–181)
- Pagination mandate: `skills/uipath-coded-apps/SKILL.md` §Critical Rules Rule 14 (lines 53–54)
- Folder resolution: `skills/uipath-coded-apps/SKILL.md` §Critical Rules Rule 11 (line 50)
- Action schema validation: `skills/uipath-coded-apps/scripts/validate-action-schema.js` (Already scripted)
