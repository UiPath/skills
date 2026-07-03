#!/usr/bin/env node
// Best-effort post_run cleanup: delete the External Application(s) THIS task
// created. Precise, not a name sweep — collects the clientId(s) written into
// the sandbox's uipath.json / intent.json by the build, matches them against
// `uip admin external-apps list`, and deletes only those. Always exits 0:
// cleanup failures (no admin tool, not logged in, nothing created) never
// affect the task's pass/fail — mirroring uipath-admin/cleanup_federated_app.py.
import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { execFileSync } from 'node:child_process'

const log = (m) => console.log(`cleanup_external_apps: ${m}`)
const SKIP_DIRS = new Set(['node_modules', 'dist', '_gen', '.git', '.venv', '.npm-prefix'])
const GUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

function collectClientIds(dir, depth = 0, out = new Set()) {
  if (depth > 4) return out
  let entries = []
  try { entries = readdirSync(dir, { withFileTypes: true }) } catch { return out }
  for (const e of entries) {
    if (e.isDirectory()) {
      if (!SKIP_DIRS.has(e.name)) collectClientIds(join(dir, e.name), depth + 1, out)
    } else if (e.name === 'uipath.json' || e.name === 'intent.json') {
      try {
        const id = JSON.parse(readFileSync(join(dir, e.name), 'utf8')).clientId
        if (typeof id === 'string' && GUID.test(id)) out.add(id.toLowerCase())
      } catch { /* unparseable — ignore */ }
    }
  }
  return out
}

function uip(args) {
  // Linux/macOS: execFileSync with no shell — args can never inject. Windows:
  // Node >= 20.12 refuses to spawn .cmd shims without a shell, so shell: true
  // is required there; safe here because every dynamic arg is a regex-validated
  // GUID (see GUID gate above) and the rest are literal verbs.
  const win = process.platform === 'win32'
  const raw = execFileSync(win ? 'uip.cmd' : 'uip', [...args, '--output', 'json'],
    { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], shell: win })
  return JSON.parse(raw)
}

// Walk any JSON shape and yield objects that look like external-app entries.
function* appEntries(node) {
  if (Array.isArray(node)) { for (const n of node) yield* appEntries(n) }
  else if (node && typeof node === 'object') {
    const id = node.id ?? node.Id ?? node.clientId ?? node.ClientId
    if (typeof id === 'string' && GUID.test(id)) yield { id, name: node.name ?? node.Name ?? '' }
    for (const v of Object.values(node)) if (v && typeof v === 'object') yield* appEntries(v)
  }
}

try {
  const ids = collectClientIds(process.cwd())
  if (ids.size === 0) {
    log('no clientId found in sandbox — nothing to clean up')
    process.exit(0)
  }

  let data
  try { data = uip(['admin', 'external-apps', 'list']) }
  catch (e) { log(`could not list external apps (${String(e.message).slice(0, 120)}) — skipping`); process.exit(0) }
  if (!data || data.Result === 'Failure') { log('list returned failure — skipping'); process.exit(0) }

  const seen = new Set()
  for (const app of appEntries(data)) {
    const key = app.id.toLowerCase()
    if (seen.has(key)) continue
    if (!ids.has(key)) continue
    seen.add(key)
    try {
      const res = uip(['admin', 'external-apps', 'delete', app.id])
      log(`deleted "${app.name}" (${app.id}) → ${res?.Result ?? 'unknown'}`)
    } catch (e) {
      log(`delete failed for ${app.id}: ${String(e.message).slice(0, 120)}`)
    }
  }
  if (seen.size === 0) log(`no matching external apps on the tenant (looked for ${ids.size} clientId(s))`)
} catch (e) {
  log(`unexpected error (${String(e.message).slice(0, 120)}) — cleanup is best-effort, continuing`)
}
process.exit(0)
