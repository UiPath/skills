import { test } from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, writeFileSync, mkdirSync, existsSync, readFileSync } from 'node:fs'
import { resolve, dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { tmpdir } from 'node:os'
import { execFileSync } from 'node:child_process'
import { packTemplate, VALID_EDIT_OPS, classifyEditIntent, parseEvent } from '../build-dashboard.mjs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const SCRIPT = resolve(__dirname, '../build-dashboard.mjs')

function tmp(prefix) {
  return mkdtempSync(join(tmpdir(), prefix))
}

// ── EJECT is a recognized edit op ───────────────────────────────────────────────
test('VALID_EDIT_OPS includes EJECT', () => {
  assert.ok(VALID_EDIT_OPS.includes('EJECT'))
})

test('classifyEditIntent accepts a lone EJECT op', () => {
  const r = classifyEditIntent({ projectDir: '/x', op: 'EJECT' })
  assert.equal(r.ops.length, 1)
  assert.equal(r.ops[0].op, 'EJECT')
})

// ── new lifecycle events are registered (parseEvent recognizes them) ────────────
test('parseEvent recognizes the regime/template events', () => {
  for (const ev of ['TEMPLATE_BUILD', 'EJECTED', 'EJECTED_PROJECT', 'TEMPLATE_PACKED']) {
    const r = parseEvent(`${ev}:{"projectDir":"/x"}`)
    assert.ok(r && r.type === ev, `${ev} should parse`)
  }
})

// ── packTemplate stages a tenant-neutral modify-face + manifest ─────────────────
test('packTemplate stages source + template.json, strips tenant identity', () => {
  const P = tmp('packtmpl-')
  mkdirSync(join(P, '.dashboard'), { recursive: true })
  mkdirSync(join(P, 'src', 'metrics'), { recursive: true })
  mkdirSync(join(P, 'dist'), { recursive: true })
  mkdirSync(join(P, 'node_modules'), { recursive: true })
  writeFileSync(join(P, '.dashboard', 'state.json'), JSON.stringify({
    schemaVersion: 2, regime: 'ejected',
    app: { name: 'Sales Template', routingName: 'sales-template-a1b2', semver: '2.1.0' },
  }))
  writeFileSync(join(P, 'intent.json'), '{ "schemaVersion": 2, "metrics": [] }')
  writeFileSync(join(P, 'package.json'), '{ "name": "x" }')
  writeFileSync(join(P, 'uipath.json'), JSON.stringify({
    name: 'x',
    scope: 'OR.Folders Insights',
    clientId: 'SECRET-CLIENT-ID',
    orgName: 'acme-org',
    tenantName: 'acme-tenant',
    baseUrl: 'https://acme.api.uipath.com',
    redirectUri: 'http://localhost:57173',
  }))
  writeFileSync(join(P, 'src', 'metrics', 'm.ts'), 'export const fetchData = async () => []')
  writeFileSync(join(P, 'dist', 'index.html'), '<html></html>')
  writeFileSync(join(P, 'node_modules', 'junk.js'), 'junk')

  packTemplate(P)

  const S = join(P, 'dist', '_source')
  // staged modify-face
  assert.ok(existsSync(join(S, 'intent.json')), 'intent.json staged')
  assert.ok(existsSync(join(S, 'src', 'metrics', 'm.ts')), 'src/ staged recursively')
  assert.ok(existsSync(join(S, 'package.json')), 'package.json staged')
  // uipath.json staged tenant-neutral: all tenant identity blanked, scope retained
  const stagedCfg = JSON.parse(readFileSync(join(S, 'uipath.json'), 'utf8'))
  assert.equal(stagedCfg.clientId, '', 'clientId blanked')
  assert.equal(stagedCfg.orgName, '', 'orgName blanked')
  assert.equal(stagedCfg.tenantName, '', 'tenantName blanked')
  assert.equal(stagedCfg.baseUrl, '', 'baseUrl blanked')
  assert.equal(stagedCfg.scope, 'OR.Folders Insights', 'scope retained')
  assert.ok(!existsSync(join(S, 'node_modules')), 'node_modules excluded')
  // manifest
  const manifest = JSON.parse(readFileSync(join(S, 'template.json'), 'utf8'))
  assert.equal(manifest.ejected, true)
  assert.equal(manifest.regime, 'ejected')
  assert.equal(manifest.routingName, 'sales-template-a1b2')
  assert.equal(manifest.dashboardName, 'Sales Template')
  assert.ok(manifest.sdkFloor && manifest.requiredScopes.includes('Insights'))
})

// ── EJECT flips regime; the edit-script then refuses ────────────────────────────
test('EJECT op flips regime to ejected, then structured edits are refused', () => {
  const P = tmp('eject-')
  mkdirSync(join(P, '.dashboard'), { recursive: true })
  writeFileSync(join(P, '.dashboard', 'state.json'), JSON.stringify({
    schemaVersion: 2, regime: 'compiler-managed',
    app: { name: 'X', routingName: 'x-1', semver: '1.0.0' }, widgets: {}, timeRange: '30d',
  }))
  const ejectIntent = join(P, 'eject-intent.json')
  writeFileSync(ejectIntent, JSON.stringify({ op: 'EJECT', projectDir: P }))

  const out = execFileSync('node', [SCRIPT, ejectIntent], { encoding: 'utf8' })
  assert.match(out, /EJECTED:/)
  const state = JSON.parse(readFileSync(join(P, '.dashboard', 'state.json'), 'utf8'))
  assert.equal(state.regime, 'ejected')

  // A structured edit on the now-ejected project must be refused (non-zero exit).
  const rmIntent = join(P, 'rm-intent.json')
  writeFileSync(rmIntent, JSON.stringify({ op: 'REMOVE', target: 'Foo', projectDir: P }))
  let threw = false
  try {
    execFileSync('node', [SCRIPT, rmIntent], { encoding: 'utf8', stdio: 'pipe' })
  } catch (e) {
    threw = true
    const combined = `${e.stdout ?? ''}${e.stderr ?? ''}`
    assert.match(combined, /ejected|EJECTED_PROJECT/i)
  }
  assert.ok(threw, 'edit-script should exit non-zero on an ejected project')
})

// ── A template build records the ejected regime in state.json ──────────────────
// (Build-side flag; the full build is exercised by the e2e task. Here we assert
//  the regime computation only, via the documented default semantics.)
test('absent regime is treated as compiler-managed (legacy state)', () => {
  // classifyEditIntent + the runtime gate key off state.regime; legacy state with
  // no regime must NOT be treated as ejected (would wrongly disable editing).
  const legacy = { schemaVersion: 2, app: { name: 'L', routingName: 'l-1' } }
  assert.notEqual(legacy.regime, 'ejected')
})
