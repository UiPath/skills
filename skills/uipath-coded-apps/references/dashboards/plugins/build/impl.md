# Dashboard Build Plugin

Full pipeline: NLP prompt → plan approval → **single script execution** → preview.

## Architecture

The agent handles the conversational phases (plan + approval). A pre-written Node.js
script (`build-dashboard.mjs`) handles the entire build phase in one invocation.

```
Agent (conversational)          Script (execution)
──────────────────────────      ──────────────────────────────────────────
Phase 0: incremental check      build-dashboard.mjs:
Phase 1: 4 parallel reads         ∙ scaffold copy (cross-platform Node.js)
Phase 2: preflight                ∙ npm ci (or skip if pre-warm done)
Phase 3: metric derivation        ∙ write .env.local
Phase 3.5: pre-warm (bg)          ∙ write all widget + view files
Phase 4: show plan                ∙ update App.tsx routes
Phase 5: approval gate            ∙ tsc --noEmit
Phase 5.5: external client (opt)  ∙ state.json
Phase 6: write plan.json          ∙ start dev server
         run build-dashboard.mjs
Phase 7: show summary from result
```

**Total agent tool calls: ≤ 8** (down from 29 in the previous approach).
No ordering violations, no cp -r on Windows, no heredoc failures.

---

## Tool-Use Budget

| Phase | Calls | How |
|---|---|---|
| 0 Incremental check | 1 Bash | `ls .dashboard/state.json` |
| 1 Boot | 1 block | 4 reads in ONE parallel message |
| 2 Preflight | 1 Bash | `uip login status` + read .auth |
| 3a Feasibility gate | 0 | In-context (classify each metric GREEN/AMBER/RED) |
| 3b–5 Derive + Plan + Approve | 0 | In-context |
| 3.5 Pre-warm | 1 Bash | background npm ci (Node.js copy) |
| 5.5 External client (opt) | 0–1 Bash | `uip admin external-apps create` (only if user chooses "create one") |
| 6 Build | 1 Write + 1 Bash | write plan.json → run build-dashboard.mjs |
| 7 Summary | 0 | parse script output |
| **Total** | **≤ 8** | |

---

## Execution Rules — Non-negotiable

1. **Never spawn subagents.** Do not use `TaskCreate`, `Agent`, or any dispatching tool.
2. **Phase 3.5 MUST fire before Phase 4.** If you are about to render the plan and have NOT
   yet started pre-warm, STOP and fire Phase 3.5 first. The pre-warm runs while the user reads.
3. **sdk-capabilities.md MUST be in context before showing the plan.** If you reach Phase 4
   and sdk-capabilities.md is not loaded, STOP and read it first (it was in the Phase 1 block).
4. **Never read scaffold source files.** App.tsx, package.json, vite.config.ts, tsconfig.json,
   src/dashboard/chrome/*, src/components/*, useInsights.ts, insights-client.ts — all forbidden.
   Their APIs are fully documented in this file.
5. **Use build-dashboard.mjs for all file writes.** Never use Write or Edit tools for widget
   files — put configuration in plan.json `widgets` array and let the script generate TypeScript.
6. **Never write widget TypeScript.** The `widgets` array takes configuration values only
   (componentName, template, endpoint, dataSelector, icon, title, description, deltaDir).
   The script generates TypeScript from pre-tested templates — no invented imports, no wrong props.
7. **View files never contain charts.** The script generates views automatically as
   `DetailViewShell` + `RecordsTable` — agent never writes view TypeScript.
8. **Scaffold overwrites on every build.** `build-dashboard.mjs` copies the scaffold fresh into the project dir on every run. Any file the user manually edited in the project dir (e.g. `src/hooks/useAuth.ts`) will be silently overwritten. Fixes to scaffold files must be applied to `assets/templates/dashboard/scaffold/` — not to the generated project. If a user reports a fix they made locally, apply it to the scaffold source.

---

## Narration Rules — What Users See

### The Blackout Rule

From plan approval to final summary: **ZERO text output**.

| Moment | Output |
|---|---|
| After Phase 5 (user approves) | `⚙ Building your dashboard…` |
| After script exits 0 | The final summary — see Summary Format |

### Error exceptions (only if unrecoverable)
- Build script fails: `"There was a build issue — please run npm install in the project folder and try again."`
- npm ci fails: `"Dependencies are downloading — this may take a minute on first run."` then retry.

---

## Phase 0 — Incremental check (1 Bash)

```bash
ls .dashboard/state.json 2>/dev/null && echo "INCREMENTAL" || echo "FRESH"
```

**INCREMENTAL** → read `../../primitives/incremental-editor.md` and follow that flow.  
**FRESH** → continue to Phase 1.

---

## Phase 1 — Boot (**MANDATORY: all 4 reads in ONE parallel message**)

Issue **EXACTLY** these four Read calls in a **SINGLE** message. All four in one tool-call
block — do not send the message until all four paths are listed:

☐ 1. `../../primitives/auth-context.md`  
☐ 2. `../../primitives/build-plan.md`  
☐ 3. `../../sdk-capabilities.md`  
☐ 4. `../../aesthetic/layout-patterns.md`

**DO NOT send the message until all 4 paths are in the same tool-call block.**

---

## Phase 2 — Preflight (1 Bash)

```bash
# uip login status — write to temp file (avoids stdin-piping issues; os.tmpdir() works on Windows)
TMPFILE=$(node -e "process.stdout.write(require('path').join(require('os').tmpdir(),'uip-status.json'))")
uip login status --output json > "$TMPFILE"
STATUS=$(cat "$TMPFILE")

# Extract fields via process.argv — no stdin pipe needed (works on all platforms)
ORG=$(node -e "process.stdout.write(JSON.parse(process.argv[1]).Data.Organization||'')" "$STATUS")
TENANT=$(node -e "process.stdout.write(JSON.parse(process.argv[1]).Data.Tenant||'')" "$STATUS")
DATA_BASE_URL=$(node -e "process.stdout.write(JSON.parse(process.argv[1]).Data.BaseUrl||'')" "$STATUS")
rm -f "$TMPFILE"

# Read PAT and TENANT_ID from .auth file in one Node call (reliable on Windows)
AUTH_VALS=$(node -e "
  const fs=require('fs'), home=require('os').homedir();
  const f=fs.readFileSync(home+'/.uipath/.auth','utf8');
  const pat=f.match(/^UIPATH_ACCESS_TOKEN=(.+)/m)?.[1]?.trim() ||
    (() => { try { return JSON.parse(f).UIPATH_ACCESS_TOKEN||''; } catch{return '';} })();
  const tid=f.match(/^UIPATH_TENANT_ID=(.+)/m)?.[1]?.trim() ||
    (() => { try { return JSON.parse(f).UIPATH_TENANT_ID||''; } catch{return '';} })();
  process.stdout.write(pat+'\n'+tid);
")
PAT=$(echo "$AUTH_VALS" | head -1)
TENANT_ID=$(echo "$AUTH_VALS" | tail -1)

# Derive API base URL
if echo "$DATA_BASE_URL" | grep -q "alpha";    then API_BASE_URL="https://alpha.api.uipath.com"
elif echo "$DATA_BASE_URL" | grep -q "staging"; then API_BASE_URL="https://staging.api.uipath.com"
else API_BASE_URL="https://api.uipath.com"
fi
```

---

## Phase 3a — Feasibility Gate (0 tool calls, in-context)

> **MUST run before Phase 3b.** If Phase 3b derives configuration for a metric before Phase 3a
> classifies it, the feasibility gate has been bypassed. Stop and classify first.

For each metric in the user's NLP request:

**Step 1 — Check the Hard Refuse Table** (`sdk-capabilities.md` top section).
If the metric matches a row: it is RED. Note the reason and suggested alternative.

**Step 2 — Search registry aliases.**
Scan each capability entry's **Aliases** field. Match the user's phrasing against them.
- Match found + template listed → **GREEN** (template substitution via `widgets[]`)
- Match found + no template → **AMBER** (agent writes typed SDK hook in `files{}` map)
- No match → **RED** (hard refuse)

**Refuse output (inline with the plan, not a separate step):**
```
⚠ "[Requested metric]" isn't available — [reason from Hard Refuse Table or "no matching API"].
[If alternative exists: I can show [alternative] instead — want that?]
[If no alternative: I've excluded it from the plan.]
```

RED metrics are excluded from the plan. Never silently drop — always surface with reason.

AMBER metrics appear in the plan with a disclosure note:
```
• **[Widget Title]** — I'll write a custom data hook for this using the [ServiceName] SDK service.
```

---

## Phase 3b — Widget Configuration Derivation (0 tool calls, in-context)

For GREEN and AMBER metrics only (RED metrics do not reach this phase).

Use four-axis decomposition from `build-plan.md`:
- **Shape**: `line | bar | area | donut | kpi | table`
- **Time frame**: `realtime | hourly | daily | weekly | monthly`
- **Aggregation**: `count | sum | avg | p50 | p95`
- **Service**: Insights RTM or SDK (already determined in Phase 3a)

Use Widget Recipes from `sdk-capabilities.md` (already loaded in Phase 1 block).
Use response shapes from capability entries — never guess field names.

For AMBER metrics: write the custom hook in the `files{}` map using the exact method signature
and response shape from the capability entry. TypeScript must compile (`tsc --noEmit` in Phase 6).

---

## Phase 3.5 — Pre-warm (1 Bash, background, SILENT)

> **MUST fire before Phase 4.** If you haven't fired this yet and are about to show
> the plan, stop and fire this first. npm ci takes 16-25s; the user takes 30-60s to read
> the plan. This hides the install behind user think-time.

```bash
SKILL_BASE_DIR="<SKILL_BASE_DIR>"   # "Base directory for this skill" from system context

# Use Node.js to derive paths — process.cwd() returns C:\Work\... on Windows,
# not the /c/Work/... POSIX path that $(pwd) returns in Git Bash.
DASHBOARD_SLUG=$(node -e "process.stdout.write('<DASHBOARD_NAME>'.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,''))")
PROJECT_DIR=$(node -e "process.stdout.write(require('path').join(process.cwd(),'${DASHBOARD_SLUG}'))")

# Pre-warm: Node.js copy + npm ci in background
node -e "
  const fs=require('fs'),path=require('path');
  function cp(s,d){
    fs.mkdirSync(d,{recursive:true});
    for(const e of fs.readdirSync(s,{withFileTypes:true})){
      const sp=path.join(s,e.name),dp=path.join(d,e.name);
      e.isDirectory()?cp(sp,dp):fs.copyFileSync(sp,dp);
    }
  }
  cp('${SKILL_BASE_DIR}/assets/templates/dashboard/scaffold','${PROJECT_DIR}');
  try{fs.rmSync(path.join('${PROJECT_DIR}','node_modules'),{recursive:true,force:true})}catch{}
  fs.writeFileSync('/tmp/dashboard-prewarm-${DASHBOARD_SLUG}.dir','${PROJECT_DIR}');
  console.log('SCAFFOLD_COPIED');
" && (cd "${PROJECT_DIR}" && npm ci --prefer-offline 2>/dev/null || npm ci 2>/dev/null) &
echo "PREWARM_STARTED: ${PROJECT_DIR}"
```

---

## Phase 4 — Plan (0 tool calls)

Render the plan using build-plan.md format. Plain English, no API names.

**STOP if sdk-capabilities.md is not in context — read it now before showing the plan.**

**After the plan:** Append the External Client Question block from build-plan.md.

---

## Phase 5 — Approval Gate (0 tool calls)

HALT. Follow build-plan.md approval gate rules. Do not proceed until explicit approval.

---

## Phase 5.5 — External Client (only if user chooses "create one")

Skip this phase if user provided an existing Client ID — use it directly in Phase 6.

```bash
# Uses variables set in Phase 2: $DATA_BASE_URL, $ORG. $DASHBOARD_NAME = user's dashboard name from initial prompt.
TEMP_DIR=$(node -e "process.stdout.write(require('os').tmpdir())")

# Derive portal redirect URL from environment
if echo "$DATA_BASE_URL" | grep -q "alpha"; then
  PORTAL_REDIRECT="https://alpha.uipath.com/${ORG}/portal_"
elif echo "$DATA_BASE_URL" | grep -q "staging"; then
  PORTAL_REDIRECT="https://staging.uipath.com/${ORG}/portal_"
else
  PORTAL_REDIRECT="https://cloud.uipath.com/${ORG}/portal_"
fi

uip admin external-apps create "UiPath Dashboard - ${DASHBOARD_NAME}" \
  --non-confidential \
  --redirect-uri "http://localhost:5173,${PORTAL_REDIRECT}" \
  --user-scope "OR.Assets,OR.Assets.Read,OR.Jobs,OR.Jobs.Write,OR.Folders,OR.Folders.Read,OR.Buckets,OR.Buckets.Read,OR.Execution,OR.Execution.Read,OR.Tasks,OR.Tasks.Write,OR.Queues,OR.Queues.Read,OR.Users,OR.Users.Read,Insights.RealTimeData" \
  --output json > "${TEMP_DIR}/uip-extapp.json"

CLIENT_ID=$(node -e "
  const d = JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'));
  process.stdout.write(d.ClientId || d.clientId || '');
" "${TEMP_DIR}/uip-extapp.json")
rm -f "${TEMP_DIR}/uip-extapp.json"

echo "CLIENT_ID=${CLIENT_ID}"
```

If `CLIENT_ID` is empty after extraction → report error: "Could not create external app. Check that `uip admin external-apps create` is available."

---

## Phase 6 — Build (1 Write + 1 Bash)

After approval, derive widget configuration in-context (no tools), then:

### Step 1: Derive widget configuration in-context (0 tool calls)

Agent never writes widget TypeScript. Provide configuration only. The script uses templates.

Using Widget Recipes from sdk-capabilities.md, derive for each widget:
- Which template to use (`template` field)
- Endpoint + startTime/endTime for the `dataHook` expression
- `dataSelector` path from the catalog response schema
- Icon name, title, description, deltaDir, deltaText

Also generate in-context (agent still authors these directly):
- Dashboard layout (`src/dashboard/Dashboard.tsx`)
- Widget exports (`src/dashboard/widgets/index.ts`)
- App.tsx import lines and route JSX

**Allowed template values for `template` field:**
`line-chart` · `area-chart` · `bar-chart` · `donut-chart` · `kpi-card` ·
`kpi-with-sparkline` · `data-table` · `ranked-table` · `progress-bar-list` · `multi-line-chart` ·
`sdk-kpi-card` · `sdk-data-table` · `sdk-bar-chart` · `sdk-ranked-table`

### Step 2: Write plan.json (1 Write)

The plan contains widget CONFIGURATION — not TypeScript code. The script loads
pre-tested templates and applies substitutions. No TypeScript errors from agent-generated code.

```json
{
  "projectDir": "<PROJECT_DIR>",
  "dashboardName": "<DASHBOARD_NAME>",
  "routingName": "<ROUTING_NAME>",
  "orgName": "<ORG>",
  "tenantName": "<TENANT>",
  "cloudUrl": "<DATA_BASE_URL>",
  "apiUrl": "<API_BASE_URL>",
  "tenantId": "<TENANT_ID>",
  "clientId": "<CLIENT_ID>",   // from Phase 5.5 or user-provided

  "widgets": [
    {
      "componentName": "ErrorRateTrend",
      "template": "line-chart",
      "detailRoute": "/error-rate",
      "icon": "AlertTriangle",
      "title": "Error Rate Trend",
      "description": "Daily error counts — spot spikes early",
      "dataHook": "useInsights<{data:Array<{name:string;value:number;date:string}>}>('agents.getErrors', { startTime: SEVEN_DAYS_AGO, endTime: NOW })",
      "dataSelector": "(data as any)?.data ?? []",
      "xKey": "date",
      "yKey": "value",
      "deltaDir": "down-good",
      "deltaText": "errors today"
    }
  ],

  "files": {
    "src/dashboard/Dashboard.tsx": "<full Dashboard.tsx content>",
    "src/dashboard/widgets/index.ts": "export { ErrorRateTrend } from './ErrorRateTrend'\n"
  },
  "appTsxImports": "import { Dashboard } from '@/dashboard/Dashboard'\nimport { ErrorRateTrendView } from '@/dashboard/views/ErrorRateTrendView'\n",
  "appTsxRoutes": "<Route path=\"/\" element={<Dashboard />} />\n<Route path=\"/error-rate\" element={<ErrorRateTrendView />} />\n"
}
```

**Widget field reference:**

| Field | Required | Description |
|---|---|---|
| `componentName` | ✅ | PascalCase — used as filename and export name |
| `template` | ✅ | Which pre-tested template to load |
| `detailRoute` | ✅ | HashRouter path, e.g. `/error-rate` |
| `icon` | ✅ | Any lucide-react icon name |
| `title` | ✅ | Human label shown in CardTitle |
| `description` | ✅ | One line in CardDescription |
| `dataHook` | ✅ | Full `useInsights<ResponseType>(...)` call expression |
| `dataSelector` | ✅ | Expression extracting array/value from response |
| `xKey` | line/area/bar | X-axis field name |
| `yKey` | line/area/bar | Y-axis field name |
| `valueExpression` | kpi-card, kpi-with-sparkline | Expression evaluating to string value |
| `columns` | data-table, ranked-table | `ColumnDef` array literal |
| `deltaDir` | most | `up-good` / `up-bad` / `down-good` / `down-bad` / `neutral` |
| `deltaText` | most | Text shown in DeltaBadge |
| `series` | multi-line-chart | Series array literal: `[{key:"P50",color:"hsl(var(--chart-1))"}]` |
| `pivotExpression` | multi-line-chart | Expression pivoting flat `{name,value,date}` rows to series map |

The script generates widget files from templates and generates view files (DetailViewShell + RecordsTable) automatically — agent never writes these TypeScript files.

Write this to `<PROJECT_DIR>/plan.json` (it will be cleaned up by the script).

### Step 3: Run build-dashboard.mjs (1 Bash)

```bash
node "${SKILL_BASE_DIR}/assets/scripts/build-dashboard.mjs" "${PROJECT_DIR}/plan.json"
BUILD_RESULT=$?
rm -f "${PROJECT_DIR}/plan.json"   # clean up — plan.json is transient, remove after script completes
```

The script handles everything: npm ci check, file writes, App.tsx update, tsc, state.json,
dev server. It outputs `BUILD_RESULT:<json>` on success.

**If the script exits non-zero:** Report the error message from stderr. Do NOT attempt
to diagnose manually — the script's error output is sufficient.

---

## Phase 7 — Summary (0 tool calls)

Parse `BUILD_RESULT:{"previewUrl":"...","widgets":[...],...}` from the script output.

Show the final summary using the Summary Format below. Then open the browser:

```bash
# Open browser to preview URL from script result
open "<previewUrl>" 2>/dev/null || start "<previewUrl>" 2>/dev/null || xdg-open "<previewUrl>"
```

---

## Summary Format

No technical language. No file paths.

```
✨ Your **[Dashboard Name]** is ready.

**Preview:** http://localhost:[port]

**What's inside:**
• **[Widget Title]** — [Plain-English description. Business insight, not API name.]
• ...

When you're ready to publish, say **"deploy this dashboard"**.
```

---

## Incremental Mode (existing dashboard)

If `.dashboard/state.json` exists → read `../../primitives/incremental-editor.md`.

For incremental builds, Phase 6 still uses `build-dashboard.mjs` but with only the new/changed
files in the `files` map — existing files are NOT included (they stay unchanged on disk).

---

## Error Handling

| Error | Action |
|---|---|
| build-dashboard.mjs exits non-zero | Show error from stderr. Tell user to run `npm install` if dependency related. |
| Plan.json write fails | Write to a different path (e.g. `~/.uipath-dashboard-plan.json`) and update the script invocation. |
| Pre-warm copy failed | The script's own copy (Step 3.5 in the script) will catch this and re-copy. |
| tsc errors from script | Script exits 1 with the TypeScript output. Show: "There was a build configuration issue." |
