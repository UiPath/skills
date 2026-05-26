#!/usr/bin/env node
/**
 * build-dashboard.mjs — Single-shot dashboard builder
 *
 * Reads an approved build plan from stdin (JSON), then:
 *   1. Copies scaffold to PROJECT_DIR (Node.js fs — cross-platform, no cp -r)
 *   2. Checks pre-warm; runs npm ci if not done
 *   3. Writes .env.local
 *   4. Writes all widget + view + Dashboard.tsx + index.ts files
 *   5. Updates App.tsx route markers
 *   6. Runs tsc --noEmit
 *   7. Writes .dashboard/state.json
 *   8. Starts dev server and outputs the URL
 *
 * Plan JSON supports two modes for widget content:
 *
 *   Mode A — files map (legacy / agent-authored TypeScript):
 *     "files": { "src/dashboard/widgets/Foo.tsx": "<full tsx>", ... }
 *
 *   Mode B — widgets array (template substitution — preferred):
 *     "widgets": [ { "componentName": "Foo", "template": "kpi-card", ... } ]
 *     The script loads pre-tested template files and applies <PLACEHOLDER> substitution.
 *     TypeScript is always correct because templates are pre-validated.
 *
 * Both modes may coexist: widgets[] generates widget + view files; files{} writes
 * Dashboard.tsx, index.ts, App.tsx (anything the agent still authors directly).
 *
 * Usage:
 *   node build-dashboard.mjs <plan.json>          ← recommended (cross-platform)
 *   node build-dashboard.mjs /path/to/plan.json
 *
 * Exit 0 = success, exit 1 = failure (message on stderr).
 */

import { readFileSync, writeFileSync, copyFileSync, mkdirSync, readdirSync, existsSync, renameSync } from 'fs';
import { join, dirname, resolve } from 'path';
import { fileURLToPath } from 'url';
import { execSync, spawn } from 'child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SCAFFOLD_DIR = resolve(__dirname, '../templates/dashboard/scaffold');
const WIDGETS_DIR = resolve(__dirname, '../templates/dashboard/widgets');

// ── Helpers ──────────────────────────────────────────────────────────────────

function fail(msg) {
  process.stderr.write(`ERROR: ${msg}\n`);
  process.exit(1);
}

function log(msg) {
  process.stdout.write(msg + '\n');
}

/** Recursive directory copy — Node.js only, no cp -r, works on Windows */
function copyDir(src, dest) {
  mkdirSync(dest, { recursive: true });
  for (const entry of readdirSync(src, { withFileTypes: true })) {
    const srcPath = join(src, entry.name);
    const destPath = join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      copyFileSync(srcPath, destPath);
    }
  }
}

/** Atomic file write — write to .tmp then rename on success */
function writeAtomic(filePath, content) {
  mkdirSync(dirname(filePath), { recursive: true });
  const tmp = filePath + '.tmp';
  writeFileSync(tmp, content, 'utf8');
  renameSync(tmp, filePath);
}

// ── Template substitution ─────────────────────────────────────────────────────

const TIME_CONSTANTS = `const NOW = new Date().toISOString()
const ONE_DAY_AGO = new Date(Date.now() - 86_400_000).toISOString()
const SEVEN_DAYS_AGO = new Date(Date.now() - 604_800_000).toISOString()
const THIRTY_DAYS_AGO = new Date(Date.now() - 2_592_000_000).toISOString()
const NINETY_DAYS_AGO = new Date(Date.now() - 7_776_000_000).toISOString()
`;

/**
 * Load a widget template and apply <PLACEHOLDER> substitutions.
 * Injects time constants after the last import line.
 */
function applyTemplate(templateName, subs) {
  const templatePath = join(WIDGETS_DIR, `${templateName}.tsx`);
  if (!existsSync(templatePath)) fail(`Template not found: ${templateName}.tsx in ${WIDGETS_DIR}`);
  let content = readFileSync(templatePath, 'utf8');

  // Apply all substitutions
  for (const [key, value] of Object.entries(subs)) {
    content = content.split(`<${key}>`).join(value);
  }

  // Inject time constants after the last import line
  const lines = content.split('\n');
  let lastImportIdx = -1;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].startsWith('import ')) lastImportIdx = i;
  }
  if (lastImportIdx >= 0) {
    lines.splice(lastImportIdx + 1, 0, '', TIME_CONSTANTS.trimEnd());
    content = lines.join('\n');
  }

  return content;
}

/**
 * Generate a detail view file (always DetailViewShell + RecordsTable).
 * This is always script-generated — agents never write view files directly.
 */
function generateViewFile(widget) {
  const { componentName, title, description, dataHook, dataSelector, columns } = widget;
  const cols = columns ?? '[{key:"name",label:"Name"},{key:"value",label:"Value",align:"right" as const}]';
  return `import React from 'react'
import { DetailViewShell } from '@/dashboard/chrome/DetailViewShell'
import { RecordsTable, type ColumnDef } from '@/dashboard/chrome/RecordsTable'
import { useInsights } from '@/hooks/useInsights'
import { LoadingState, EmptyState } from '@/dashboard/chrome'

${TIME_CONSTANTS.trimEnd()}

const COLUMNS: ColumnDef<Record<string, unknown>>[] = ${cols}

export function ${componentName}View() {
  const { data, loading, error } = ${dataHook}
  const rows: Record<string, unknown>[] = ${dataSelector ?? '[]'}
  if (loading) return <DetailViewShell title="${title ?? componentName}" description="${description ?? ''}"><LoadingState height="h-96" /></DetailViewShell>
  if (error)   return <DetailViewShell title="${title ?? componentName}" description="${description ?? ''}"><EmptyState message={error.message} /></DetailViewShell>
  return (
    <DetailViewShell title="${title ?? componentName}" description="${description ?? ''}">
      <RecordsTable rows={rows} columns={COLUMNS} defaultSortKey={COLUMNS[0]?.key as string} />
    </DetailViewShell>
  )
}
`;
}

// ── Main ──────────────────────────────────────────────────────────────────────

// Accept plan as file path argument — cross-platform, no /dev/stdin issues on Windows
const planArg = process.argv[2];
if (!planArg) fail('Usage: node build-dashboard.mjs <plan.json>');

let plan;
try {
  plan = JSON.parse(readFileSync(planArg, 'utf8'));
} catch (e) {
  fail(`Could not read plan JSON from ${planArg}: ${e.message}`);
}

const {
  projectDir,
  dashboardName,
  routingName,
  orgName,
  tenantName,
  cloudUrl,
  apiUrl,
  tenantId,
  pat,
  files = {},      // { 'relative/path': 'file content' } — agent-authored files (Dashboard.tsx, index.ts, etc.)
  widgets: planWidgets = [],  // widget config array — script generates TypeScript via templates
  appTsxImports,   // string to inject between GENERATED_IMPORTS markers
  appTsxRoutes,    // string to inject between GENERATED_ROUTES markers
} = plan;

if (!projectDir) fail('plan.projectDir is required');
if (!routingName) fail('plan.routingName is required');

const P = resolve(projectDir);

// Step 1 — Copy scaffold (cross-platform Node.js, no cp -r)
log('⚙ Copying scaffold…');
if (!existsSync(SCAFFOLD_DIR)) fail(`Scaffold not found at ${SCAFFOLD_DIR}`);
copyDir(SCAFFOLD_DIR, P);

// Remove stale node_modules if present in scaffold (prevents npm ci ENOTEMPTY)
try {
  execSync(`node -e "require('fs').rmSync(${JSON.stringify(join(P, 'node_modules'))},{recursive:true,force:true})"`,
    { stdio: 'pipe' });
} catch { /* ignore */ }

// Step 2 — Write .env.local
log('⚙ Writing environment config…');
writeAtomic(join(P, '.env.local'), [
  `VITE_UIPATH_CLOUD_URL=${cloudUrl}`,
  `VITE_UIPATH_BASE_URL=${apiUrl}`,
  `VITE_UIPATH_ORG_NAME=${orgName}`,
  `VITE_UIPATH_TENANT_NAME=${tenantName}`,
  `VITE_INSIGHTS_TENANT_ID=${tenantId}`,
  `VITE_UIPATH_PAT=${pat}`,
].join('\n'));

// Step 3 — npm ci (skip if pre-warm already completed)
const lockSignal = join(P, 'node_modules', '.package-lock.json');
if (!existsSync(lockSignal)) {
  log('⚙ Installing dependencies…');
  try {
    execSync('npm ci --prefer-offline', { cwd: P, stdio: 'pipe' });
  } catch {
    execSync('npm ci', { cwd: P, stdio: 'pipe' });
  }
} else {
  log('✓ Dependencies already installed (pre-warm)');
}

// Step 4 — Write agent-authored files (files map — Dashboard.tsx, index.ts, etc.)
log('⚙ Writing dashboard files…');
for (const [relativePath, content] of Object.entries(files)) {
  writeAtomic(join(P, relativePath), content);
}

// Step 4b — Process widgets array via template substitution
const generatedWidgetNames = [];

if (planWidgets.length > 0) {
  log(`⚙ Generating ${planWidgets.length} widget(s) from templates…`);
}

for (const widget of planWidgets) {
  const { componentName, template } = widget;
  if (!componentName) fail(`Widget entry missing required field: componentName`);
  if (!template) fail(`Widget "${componentName}" missing required field: template`);

  // Build substitution map — all known placeholders with defaults
  const subs = {
    COMPONENT_NAME: componentName,
    TITLE: widget.title ?? componentName,
    DESCRIPTION: widget.description ?? '',
    DETAIL_ROUTE: widget.detailRoute ?? `/${componentName.toLowerCase()}`,
    ICON: widget.icon ?? 'Activity',
    DATA_HOOK: widget.dataHook ?? `useInsights('agents.getAgents', { startTime: THIRTY_DAYS_AGO, endTime: NOW })`,
    DATA_SELECTOR: widget.dataSelector ?? '[]',
    X_KEY: widget.xKey ?? 'date',
    Y_KEY: widget.yKey ?? 'value',
    VALUE_EXPRESSION: widget.valueExpression ?? "'—'",
    COLUMNS: widget.columns ?? '[{key:"name",label:"Name"},{key:"value",label:"Value",align:"right" as const}]',
    DATA_KEY: widget.dataKey ?? 'value',
    NAME_KEY: widget.nameKey ?? 'name',
    DELTA_DIR: widget.deltaDir ?? 'neutral',
    DELTA_TEXT: widget.deltaText ?? '',
    SERIES: widget.series ?? '[{key:"value",color:"hsl(var(--chart-1))"}]',
    PIVOT_EXPRESSION: widget.pivotExpression ?? 'rawData',
  };

  // Generate widget file from template
  const widgetContent = applyTemplate(template, subs);
  writeAtomic(join(P, 'src', 'dashboard', 'widgets', `${componentName}.tsx`), widgetContent);

  // Generate view file (always DetailViewShell + RecordsTable)
  const viewContent = generateViewFile(widget);
  writeAtomic(join(P, 'src', 'dashboard', 'views', `${componentName}View.tsx`), viewContent);

  generatedWidgetNames.push(componentName);
}

// Step 5 — Update App.tsx route markers
if (appTsxImports || appTsxRoutes) {
  const appPath = join(P, 'src', 'app', 'App.tsx');
  // Fall back to src/App.tsx if src/app/App.tsx doesn't exist
  const appFile = existsSync(appPath) ? appPath : join(P, 'src', 'App.tsx');
  let appContent = readFileSync(appFile, 'utf8');

  if (appTsxImports) {
    appContent = appContent.replace(
      /\/\/ GENERATED_IMPORTS_START[\s\S]*?\/\/ GENERATED_IMPORTS_END/,
      `// GENERATED_IMPORTS_START\n${appTsxImports}// GENERATED_IMPORTS_END`
    );
  }
  if (appTsxRoutes) {
    appContent = appContent.replace(
      /\{\/\* GENERATED_ROUTES_START \*\/\}[\s\S]*?\{\/\* GENERATED_ROUTES_END \*\/\}/,
      `{/* GENERATED_ROUTES_START */}\n${appTsxRoutes}{/* GENERATED_ROUTES_END */}`
    );
  }
  writeFileSync(appFile, appContent, 'utf8');
}

// Step 6 — tsc --noEmit
log('⚙ Validating TypeScript…');
try {
  execSync('npx tsc --noEmit', { cwd: P, stdio: 'pipe' });
  log('✓ TypeScript clean');
} catch (e) {
  const err = e.stdout?.toString() || e.stderr?.toString() || String(e);
  fail(`TypeScript errors:\n${err}`);
}

// Step 7 — Write state.json
const stateDir = join(P, '.dashboard');
mkdirSync(stateDir, { recursive: true });
const statePath = join(stateDir, 'state.json');
const existingState = existsSync(statePath)
  ? JSON.parse(readFileSync(statePath, 'utf8'))
  : {};

// Collect widget names from both modes
const filesWidgetNames = Object.keys(files)
  .filter(p => p.startsWith('src/dashboard/widgets/') && p.endsWith('.tsx'))
  .map(p => p.replace('src/dashboard/widgets/', '').replace('.tsx', ''));
const allWidgetNames = [...new Set([...filesWidgetNames, ...generatedWidgetNames])];

const newState = {
  ...existingState,
  app: { name: dashboardName, routingName, semver: existingState.app?.semver ?? '1.0.0' },
  env: cloudUrl.includes('alpha') ? 'alpha' : cloudUrl.includes('staging') ? 'staging' : 'prod',
  org: orgName,
  tenant: tenantName,
  cloudUrl,
  widgets: allWidgetNames,
  deployment: existingState.deployment ?? { systemName: null, folderKey: null, appUrl: null, lastDeployedAt: null },
};
writeAtomic(statePath, JSON.stringify(newState, null, 2));

// Step 8 — Start dev server
// Use shell:true so npm resolves correctly on Windows (npm.cmd vs npm)
log('⚙ Starting preview server…');
const isWindows = process.platform === 'win32';
const server = spawn('npm', ['run', 'dev'], {
  cwd: P,
  detached: true,
  stdio: 'pipe',
  shell: isWindows,   // required on Windows — npm is npm.cmd
});
server.on('error', () => {});  // suppress unhandled error if server fails to start
server.unref();

// Give server 5s to bind, then output result regardless
// (user runs `npm run dev` themselves if this poll times out)
let port = 5173;
const deadline = Date.now() + 5000;
while (Date.now() < deadline) {
  try {
    execSync(
      `node -e "require('http').get('http://localhost:${port}',r=>process.exit(r.statusCode<500?0:1)).on('error',()=>process.exit(1))"`,
      { stdio: 'pipe', timeout: 1000 }
    );
    break;
  } catch {
    port++;
    if (port > 5180) { port = 5173; break; }
  }
}

// Output structured result — always exit 0 after this point (server runs independently)
const result = {
  success: true,
  projectDir: P,
  port,
  previewUrl: `http://localhost:${port}`,
  widgets: allWidgetNames,
  dashboardName,
};
log('\nBUILD_RESULT:' + JSON.stringify(result));
process.exit(0);  // exit before server's detached process can throw

/**
 * PLAN JSON SCHEMA
 * ─────────────────
 * {
 *   "projectDir":    string  — absolute path where dashboard will be created
 *   "dashboardName": string  — human display name (e.g. "Agent Health Dashboard")
 *   "routingName":   string  — URL slug (e.g. "agent-health-x7k2")
 *   "orgName":       string  — from uip login (Data.Organization)
 *   "tenantName":    string  — from uip login (Data.Tenant)
 *   "cloudUrl":      string  — from uip login (Data.BaseUrl)
 *   "apiUrl":        string  — derived ("alpha" → https://alpha.api.uipath.com etc.)
 *   "tenantId":      string  — UUID from ~/.uipath/.auth UIPATH_TENANT_ID
 *   "pat":           string  — from ~/.uipath/.auth UIPATH_ACCESS_TOKEN
 *
 *   "widgets": [            — PREFERRED: agent provides config, script generates TypeScript
 *     {
 *       "componentName": string   — PascalCase; used as filename and export name
 *       "template":      string   — one of: line-chart | area-chart | bar-chart | donut-chart |
 *                                           kpi-card | kpi-with-sparkline | data-table |
 *                                           ranked-table | progress-bar-list | multi-line-chart
 *       "detailRoute":   string   — HashRouter path, e.g. "/error-rate"
 *       "icon":          string   — any lucide-react icon name
 *       "title":         string   — human label shown in CardTitle
 *       "description":   string   — one line in CardDescription
 *       "dataHook":      string   — full useInsights<ResponseType>(...) call expression
 *       "dataSelector":  string   — expression extracting array/value from response data
 *       "xKey":          string   — (line/area/bar) X-axis field name
 *       "yKey":          string   — (line/area/bar) Y-axis field name
 *       "valueExpression": string — (kpi-card/kpi-with-sparkline) expression evaluating to string
 *       "columns":       string   — (data-table/ranked-table) ColumnDef array literal
 *       "deltaDir":      string   — up-good | up-bad | down-good | down-bad | neutral
 *       "deltaText":     string   — text shown in DeltaBadge
 *       "series":        string   — (multi-line-chart) series array literal
 *       "pivotExpression": string — (multi-line-chart) expression pivoting flat array to series map
 *     }
 *   ],
 *
 *   "files": {              — agent-authored files (Dashboard.tsx, index.ts, App.tsx)
 *     "src/dashboard/Dashboard.tsx": "...",
 *     "src/dashboard/widgets/index.ts": "..."
 *   },
 *   "appTsxImports": string  — lines to inject between GENERATED_IMPORTS markers
 *   "appTsxRoutes":  string  — JSX to inject between GENERATED_ROUTES markers
 * }
 */
