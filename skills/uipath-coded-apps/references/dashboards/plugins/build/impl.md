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
Phase 6: write plan.json          ∙ state.json
         run build-dashboard.mjs  ∙ start dev server
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
| 3–5 Derive + Plan + Approve | 0 | In-context |
| 3.5 Pre-warm | 1 Bash | background npm ci (Node.js copy) |
| 6 Build | 1 Write + 1 Bash | write plan.json → run build-dashboard.mjs |
| 7 Summary | 0 | parse script output |
| **Total** | **≤ 8** | |

---

## Execution Rules — Non-negotiable

1. **Never spawn subagents.** Do not use `TaskCreate`, `Agent`, or any dispatching tool.
2. **Phase 3.5 MUST fire before Phase 4.** If you are about to render the plan and have NOT
   yet started pre-warm, STOP and fire Phase 3.5 first. The pre-warm runs while the user reads.
3. **insights-catalog.md MUST be in context before showing the plan.** If you reach Phase 4
   and insights-catalog.md is not loaded, STOP and read it first (it was in the Phase 1 block).
4. **Never read scaffold source files.** App.tsx, package.json, vite.config.ts, tsconfig.json,
   src/dashboard/chrome/*, src/components/*, useInsights.ts, insights-client.ts — all forbidden.
   Their APIs are fully documented in this file.
5. **Use build-dashboard.mjs for all file writes.** Never use Write or Edit tools for widget
   files — put all generated content in plan.json and let the script write it.

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
☐ 3. `../../primitives/data-router.md`  
☐ 4. `../../insights-catalog.md`

**DO NOT send the message until all 4 paths are in the same tool-call block.**
**DO NOT proceed to Phase 4 unless insights-catalog.md was loaded in this block.**

---

## Phase 2 — Preflight (1 Bash)

```bash
# All auth in ONE command — no split reads
STATUS=$(uip login status --output json)
ORG=$(echo "$STATUS" | node -p "JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')).Data.Organization" 2>/dev/null || node -e "process.stdout.write(JSON.parse('$STATUS').Data.Organization)")
TENANT=$(echo "$STATUS" | node -e "const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')); process.stdout.write(d.Data.Tenant)")
DATA_BASE_URL=$(echo "$STATUS" | node -e "const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')); process.stdout.write(d.Data.BaseUrl)")

# Read both PAT and TENANT_ID in one grep — never two separate commands
eval "$(grep -E '^UIPATH_ACCESS_TOKEN=|^UIPATH_TENANT_ID=' ~/.uipath/.auth | \
  sed 's/^UIPATH_ACCESS_TOKEN=/PAT=/; s/^UIPATH_TENANT_ID=/TENANT_ID=/')"

# Derive API base URL
if echo "$DATA_BASE_URL" | grep -q "alpha";    then API_BASE_URL="https://alpha.api.uipath.com"
elif echo "$DATA_BASE_URL" | grep -q "staging"; then API_BASE_URL="https://staging.api.uipath.com"
else API_BASE_URL="https://api.uipath.com"
fi
```

---

## Phase 3 — Metric Derivation (0 tool calls, in-context)

Apply four-axis decomposition from build-plan.md. Route via data-router.md.
Use Widget Recipes from insights-catalog.md (already loaded).

---

## Phase 3.5 — Pre-warm (1 Bash, background, SILENT)

> **MUST fire before Phase 4.** If you haven't fired this yet and are about to show
> the plan, stop and fire this first. npm ci takes 16-25s; the user takes 30-60s to read
> the plan. This hides the install behind user think-time.

```bash
SKILL_BASE_DIR="<SKILL_BASE_DIR>"   # "Base directory for this skill" from system context
DASHBOARD_SLUG=$(node -e "const t='<DASHBOARD_NAME>'; \
  process.stdout.write(t.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,''))")
PROJECT_DIR="$(pwd)/${DASHBOARD_SLUG}"

# Pre-warm: Node.js copy (cross-platform) + npm ci in background
(
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
    try{fs.rmSync('${PROJECT_DIR}/node_modules',{recursive:true,force:true})}catch{}
  " && cd "${PROJECT_DIR}" && (npm ci --prefer-offline 2>/dev/null || npm ci 2>/dev/null)
) &
echo "${PROJECT_DIR}" > "/tmp/dashboard-prewarm-${DASHBOARD_SLUG}.dir"
echo "PREWARM_STARTED"
```

---

## Phase 4 — Plan (0 tool calls)

Render the plan using build-plan.md format. Plain English, no API names.

**STOP if insights-catalog.md is not in context — read it now before showing the plan.**

---

## Phase 5 — Approval Gate (0 tool calls)

HALT. Follow build-plan.md approval gate rules. Do not proceed until explicit approval.

---

## Phase 6 — Build (1 Write + 1 Bash)

After approval, generate all widget code in-context (no tools), then:

### Step 1: Generate all code in-context (0 tool calls)

Using Widget Recipes from insights-catalog.md, derive the full TypeScript source for:
- Every widget file (`src/dashboard/widgets/<Name>.tsx`)
- Every detail view (`src/dashboard/views/<Name>View.tsx`)
- Dashboard layout (`src/dashboard/Dashboard.tsx`)
- Widget exports (`src/dashboard/widgets/index.ts`)
- App.tsx import lines and route JSX

### Step 2: Write plan.json (1 Write)

Write the complete build plan as JSON. The script reads this and writes all files.

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
  "pat": "<PAT>",
  "files": {
    "src/dashboard/Dashboard.tsx": "<full Dashboard.tsx content>",
    "src/dashboard/widgets/index.ts": "<export lines>",
    "src/dashboard/widgets/<Widget1>.tsx": "<full widget TSX>",
    "src/dashboard/views/<Widget1>View.tsx": "<full view TSX>"
  },
  "appTsxImports": "import { Dashboard } from '@/dashboard/Dashboard'\nimport { <Widget1>View } from '@/dashboard/views/<Widget1>View'\n",
  "appTsxRoutes": "<Route path=\"/\" element={<Dashboard />} />\n<Route path=\"/<route1>\" element={<<Widget1>View />} />\n"
}
```

Write this to `<PROJECT_DIR>/plan.json` (it will be cleaned up by the script).

### Step 3: Run build-dashboard.mjs (1 Bash)

```bash
node "${SKILL_BASE_DIR}/assets/scripts/build-dashboard.mjs" "${PROJECT_DIR}/plan.json"
BUILD_RESULT=$?
rm -f "${PROJECT_DIR}/plan.json"   # clean up — no PAT should sit on disk longer than needed
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
