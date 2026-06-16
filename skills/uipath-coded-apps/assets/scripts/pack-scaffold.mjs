#!/usr/bin/env node
// Maintainer tool: pack the dashboard scaffold into the committed starter-kit
// archive + manifest. Run it after editing templates/dashboard/scaffold/ (or the
// widget templates) and commit the refreshed zip + manifest.
//
//   node pack-scaffold.mjs [--version X.Y.Z]   pack (default: keep current version, else 1.0.0)
//   node pack-scaffold.mjs --check             verify the committed archive matches the loose scaffold
//
// Pure Node — no system zip tools — so it runs anywhere.

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { zipDir, contentHash } from './lib/zip.mjs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const SCAFFOLD_DIR = resolve(__dirname, '../templates/dashboard/scaffold')
const FIXTURES_DIR = resolve(__dirname, '../fixtures')
const ZIP_PATH = resolve(FIXTURES_DIR, 'governance-dashboard-starter-kit.zip')
const MANIFEST_PATH = resolve(FIXTURES_DIR, 'governance-dashboard-starter-kit.manifest.json')

function readManifest() {
  try { return JSON.parse(readFileSync(MANIFEST_PATH, 'utf8')) } catch { return null }
}

const args = process.argv.slice(2)
const sha = contentHash(SCAFFOLD_DIR)

if (args.includes('--check')) {
  const m = readManifest()
  if (!m) { console.error('No manifest found — run pack-scaffold.mjs to create the archive first.'); process.exit(1) }
  if (m.sha256 !== sha) {
    console.error(`STALE: scaffold content sha256 ${sha} does not match manifest ${m.sha256}.`)
    console.error('The scaffold changed but the archive was not re-packed. Run pack-scaffold.mjs and commit the refreshed zip + manifest.')
    process.exit(1)
  }
  console.log(`OK — archive matches the scaffold (sha256 ${sha.slice(0, 12)}…, version ${m.version}).`)
  process.exit(0)
}

const vIdx = args.indexOf('--version')
const version = (vIdx >= 0 ? args[vIdx + 1] : null) ?? readManifest()?.version ?? '1.0.0'

mkdirSync(FIXTURES_DIR, { recursive: true })
writeFileSync(ZIP_PATH, zipDir(SCAFFOLD_DIR))
const manifest = {
  name: 'governance-dashboard-starter-kit',
  version,
  sha256: sha,
  builtFrom: 'templates/dashboard/scaffold',
}
writeFileSync(MANIFEST_PATH, JSON.stringify(manifest, null, 2) + '\n')
console.log(`Packed ${ZIP_PATH}\n  version ${version}, sha256 ${sha.slice(0, 12)}…`)
