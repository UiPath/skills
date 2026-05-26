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
 * Usage:
 *   node build-dashboard.mjs <plan.json>          ← recommended (cross-platform)
 *   node build-dashboard.mjs /path/to/plan.json
 *
 * The plan JSON schema is defined at the bottom of this file.
 * Exit 0 = success, exit 1 = failure (message on stderr).
 */

import { readFileSync, writeFileSync, copyFileSync, mkdirSync, readdirSync, existsSync, renameSync } from 'fs';
import { join, dirname, resolve } from 'path';
import { fileURLToPath } from 'url';
import { execSync, spawn } from 'child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SCAFFOLD_DIR = resolve(__dirname, '../templates/dashboard/scaffold');

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
  files = {},      // { 'relative/path': 'file content' }
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

// Step 4 — Write all generated files
log('⚙ Writing dashboard files…');
for (const [relativePath, content] of Object.entries(files)) {
  writeAtomic(join(P, relativePath), content);
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
const widgetNames = Object.keys(files)
  .filter(p => p.startsWith('src/dashboard/widgets/') && p.endsWith('.tsx'))
  .map(p => p.replace('src/dashboard/widgets/', '').replace('.tsx', ''));
const newState = {
  ...existingState,
  app: { name: dashboardName, routingName, semver: existingState.app?.semver ?? '1.0.0' },
  env: cloudUrl.includes('alpha') ? 'alpha' : cloudUrl.includes('staging') ? 'staging' : 'prod',
  org: orgName,
  tenant: tenantName,
  cloudUrl,
  widgets: widgetNames,
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
// Output structured result for the agent to parse
const result = {
  success: true,
  projectDir: P,
  port,
  previewUrl: `http://localhost:${port}`,
  widgets: widgetNames,
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
 *   "files": {              — map of relative path → full file content
 *     "src/dashboard/Dashboard.tsx": "...",
 *     "src/dashboard/widgets/Widget1.tsx": "...",
 *     "src/dashboard/views/Widget1View.tsx": "...",
 *     "src/dashboard/widgets/index.ts": "..."
 *   },
 *   "appTsxImports": string  — lines to inject between GENERATED_IMPORTS markers
 *   "appTsxRoutes":  string  — JSX to inject between GENERATED_ROUTES markers
 * }
 */
