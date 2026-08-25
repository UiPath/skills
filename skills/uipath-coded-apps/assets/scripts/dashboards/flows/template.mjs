// Use-case flow: TEMPLATE packaging — stage the modify-face source + manifest into
// dist/_source so one pack artifact carries both the deploy face and the ejected,
// tenant-neutral source. Extracted from build-dashboard.mjs.

import { join, resolve, basename } from 'path'
import { existsSync, readFileSync, writeFileSync, copyFileSync, mkdirSync, rmSync, cpSync, readdirSync } from 'fs'
import { readScaffoldVersion } from '../lifecycle.mjs'
import { fail, emit, MIN_SDK_VERSION, DASHBOARD_SCOPES } from '../build-dashboard.mjs'

/**
 * Stage the full modify-face source + a template.json manifest into dist/_source/
 * so ONE `uip codedapp pack dist` artifact carries both the deploy face (dist/)
 * and the agent-modifiable source (the ejected "recipe"). Tenant-neutral: never
 * stages .env*, .dashboard/ (tenant + deployment identity), node_modules, or dist,
 * and blanks uipath.json clientId. Run AFTER `npm run build` (needs dist/), before pack.
 * @param {string} projectDir
 */
export function packTemplate(projectDir) {
  const P = resolve(projectDir)
  const distDir = join(P, 'dist')
  if (!existsSync(distDir)) fail('dist/ not found — run `npm run build` before --pack-template.')
  const statePath = join(P, '.dashboard', 'state.json')
  const state = existsSync(statePath) ? JSON.parse(readFileSync(statePath, 'utf8')) : {}

  const srcOut = join(distDir, '_source')
  try { rmSync(srcOut, { recursive: true, force: true }) } catch { /* fresh */ }
  mkdirSync(srcOut, { recursive: true })

  // The modify-face project. Tenant identity (.env*, .dashboard/) and rebuildable
  // artifacts (node_modules, dist, _gen) are deliberately excluded.
  const INCLUDE = [
    'intent.json', 'package.json', 'package-lock.json', 'index.html',
    'vite.config.ts', 'tsconfig.json', 'tsconfig.node.json', 'tsconfig.metrics.json',
    'tailwind.config.ts', 'postcss.config.js', 'src',
  ]
  const stripDirs = new Set(['node_modules', 'dist'])
  for (const rel of INCLUDE) {
    const from = join(P, rel)
    if (!existsSync(from)) continue
    cpSync(from, join(srcOut, rel), {
      recursive: true,
      filter: (s) => {
        const b = basename(s)
        return !stripDirs.has(b) && !b.startsWith('.env')
      },
    })
  }

  // uipath.json — staged tenant-neutral. dist/_source/* is web-served, so blank
  // ALL tenant identity (clientId, orgName, tenantName, baseUrl); keep only scope
  // (+ name/redirectUri). A proper template build already wrote a scope-only
  // uipath.json; this also covers packing a non-template build as a template.
  const TENANT_KEYS = ['clientId', 'orgName', 'tenantName', 'baseUrl']
  const uj = join(P, 'uipath.json')
  if (existsSync(uj)) {
    try {
      const obj = JSON.parse(readFileSync(uj, 'utf8'))
      for (const k of TENANT_KEYS) if (k in obj) obj[k] = ''
      writeFileSync(join(srcOut, 'uipath.json'), JSON.stringify(obj, null, 2))
    } catch { copyFileSync(uj, join(srcOut, 'uipath.json')) }
  }

  const manifest = {
    templateVersion: '1.0.0',
    scaffoldVersion: readScaffoldVersion(P),
    sdkFloor: MIN_SDK_VERSION,
    requiredScopes: DASHBOARD_SCOPES,
    routingName: state.app?.routingName ?? null,
    dashboardName: state.app?.name ?? null,
    regime: 'ejected',
    ejected: true,
    generatedBy: 'build-dashboard.mjs --pack-template',
  }
  writeFileSync(join(srcOut, 'template.json'), JSON.stringify(manifest, null, 2))

  emit('TEMPLATE_PACKED', {
    sourceDir: srcOut,
    files: readdirSync(srcOut),
    packCommand: `uip codedapp pack dist -n "${state.app?.name ?? '<APP_NAME>'}" --version "${state.app?.semver ?? '1.0.0'}" --output json`,
    caveat: "dist/_source/* is web-served by the platform — ship embedded source ONLY for shareable, tenant-neutral templates, never a customer's private dashboard.",
  })
}
