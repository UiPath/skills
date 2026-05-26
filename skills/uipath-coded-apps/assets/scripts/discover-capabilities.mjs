#!/usr/bin/env node
// Reads sdk-capabilities.md and optionally enriches it with live
// DataFabric entity names from the active uip login session.
// Usage: node discover-capabilities.mjs [--output json]
// Output: prints the capability summary; non-zero exit if login is invalid.

import { execSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const CATALOG_PATH = join(__dirname, '../../references/dashboards/sdk-capabilities.md')

function getLoginStatus() {
  try {
    const raw = execSync('uip login status --output json', { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] })
    return JSON.parse(raw)
  } catch {
    return null
  }
}

const status = getLoginStatus()
if (!status?.isLoggedIn) {
  console.error('Not logged in — run `uip login` first')
  process.exit(1)
}

const catalog = readFileSync(CATALOG_PATH, 'utf8')
const namespaces = ['Agents', 'Traceview', 'Governance', 'Jobs']
const counts = {}
for (const ns of namespaces) {
  const matches = catalog.match(new RegExp(`\\b${ns}\\b`, 'g'))
  counts[ns] = matches ? matches.length : 0
}

const result = {
  org: status.accountName,
  tenant: status.tenantName,
  tenantId: status.tenantId ?? '(resolve from .auth file)',
  capabilityFile: CATALOG_PATH,
  namespaceCoverage: counts,
  status: 'ready',
}

if (process.argv.includes('--output') && process.argv.includes('json')) {
  console.log(JSON.stringify(result, null, 2))
} else {
  console.log(`SDK capabilities loaded for ${result.org}/${result.tenant}`)
  console.log(`Namespaces: ${Object.entries(counts).map(([k, v]) => `${k}(${v})`).join(', ')}`)
  console.log(`tenantId: ${result.tenantId}`)
}
