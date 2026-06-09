#!/usr/bin/env node
/**
 * provision-admin-folder.mjs
 *
 * Idempotent one-time setup for the AdminDashboards deployment folder.
 * Runs all CLI lookups in parallel, creates the folder and assigns the role
 * only when needed, and writes the folder key to state.json.
 *
 * Usage:
 *   node provision-admin-folder.mjs <project-dir>
 *
 * Exit codes:
 *   0 — provisioning complete (or already done)
 *   1 — fatal error (message on stderr)
 */

import { exec }     from 'child_process'
import { promisify } from 'util'
import { readFileSync, writeFileSync, renameSync, existsSync } from 'fs'
import { join, resolve } from 'path'

const execAsync = promisify(exec)
const projectDir = resolve(process.argv[2] ?? '.')

// ── Helpers ───────────────────────────────────────────────────────────────────

function fail(msg) {
  process.stderr.write(`ERROR: ${msg}\n`)
  process.exit(1)
}

function log(msg) {
  process.stdout.write(msg + '\n')
}

/** Run a uip CLI command and return parsed JSON. */
async function uip(...args) {
  const cmd = `uip ${args.join(' ')}`
  const { stdout, stderr } = await execAsync(cmd).catch(e => {
    throw new Error(`${cmd} failed: ${e.stderr ?? e.message}`)
  })
  try {
    return JSON.parse(stdout)
  } catch {
    throw new Error(`${cmd} returned non-JSON output: ${stdout.slice(0, 200)}`)
  }
}

/** Atomic write to state.json. */
function updateState(key, value) {
  const fp  = join(projectDir, '.dashboard', 'state.json')
  if (!existsSync(fp)) fail('state.json not found — run the dashboard build first')
  const state = JSON.parse(readFileSync(fp, 'utf8'))
  state.deployment = state.deployment ?? {}
  Object.assign(state.deployment, { [key]: value })
  const tmp = fp + '.tmp'
  writeFileSync(tmp, JSON.stringify(state, null, 2), 'utf8')
  renameSync(tmp, fp)
}

// ── Check if already provisioned ─────────────────────────────────────────────

const statePath = join(projectDir, '.dashboard', 'state.json')
if (!existsSync(statePath)) fail('state.json not found — run the dashboard build first')

const state = JSON.parse(readFileSync(statePath, 'utf8'))
if (state.deployment?.folderKey) {
  log(`AdminDashboards already provisioned (key: ${state.deployment.folderKey})`)
  process.exit(0)
}

// ── Parallel lookups ──────────────────────────────────────────────────────────

log('Looking up roles, groups, and folders in parallel…')

const [rolesData, usersData, foldersData] = await Promise.all([
  uip('or roles list --limit 500 --output json'),
  uip('or users list --username "Administrators" --output json'),
  uip('or folders list --all --output json'),
]).catch(e => fail(e.message))

// ── Extract role key ──────────────────────────────────────────────────────────

const roles = rolesData.Data ?? rolesData.data ?? (Array.isArray(rolesData) ? rolesData : [])
const adminRole = roles.find(r => r.Name === 'Folder Administrator')
if (!adminRole) fail('"Folder Administrator" role not found. Check: uip or roles list --output json')
const roleKey = adminRole.Key ?? adminRole.key
log(`✓ Folder Administrator role: ${roleKey}`)

// ── Extract group key ─────────────────────────────────────────────────────────

const users = usersData.Data ?? usersData.data ?? (Array.isArray(usersData) ? usersData : [])
const adminGroup = users.find(u => {
  const name = (u.UserName ?? u.Name ?? '').toLowerCase()
  const type = (u.Type ?? u.type ?? '').toLowerCase()
  return name === 'administrators' && (type.includes('group') || type === '')
})
if (!adminGroup) {
  const groups = users
    .filter(u => (u.Type ?? u.type ?? '').toLowerCase().includes('group'))
    .map(u => u.UserName ?? u.Name)
    .join(', ')
  fail(`"Administrators" group not found. Available groups: ${groups || '(none found)'}`)
}
const groupKey = adminGroup.Key ?? adminGroup.key
log(`✓ Administrators group: ${groupKey}`)

// ── Check / create AdminDashboards folder ─────────────────────────────────────

const folders = Array.isArray(foldersData) ? foldersData : (foldersData.Data ?? foldersData.data ?? [])
let folder = folders.find(f => f.Name === 'AdminDashboards')

if (!folder) {
  log('Creating AdminDashboards folder…')
  const created = await uip('or folders create "AdminDashboards" --output json')
    .catch(e => fail(`Could not create folder: ${e.message}`))
  folder = created.Data ?? created.data ?? created
  log(`✓ Folder created`)
} else {
  log(`✓ AdminDashboards folder already exists`)
}

const folderKey = folder.Key ?? folder.key
if (!folderKey) fail('Could not extract folder key from response')

// ── Check / assign role ───────────────────────────────────────────────────────

const rolesAssigned = await uip(`or roles user-roles list "Administrators" --type Group --output json`)
  .catch(() => ({ Data: [] }))

const assigned = (rolesAssigned.Data ?? rolesAssigned.data ?? []).find(r => {
  const fp   = (r.FolderPath ?? r.folderPath ?? '').toLowerCase()
  const role = (r.Role ?? r.role ?? '').toLowerCase()
  return fp === 'admindashboards' && role === 'folder administrator'
})

if (!assigned) {
  log('Assigning Folder Administrator role to Administrators group…')
  await uip(`or roles assign --user-key ${groupKey} --role-keys ${roleKey} --folder-key ${folderKey} --output json`)
    .catch(e => fail(`Role assignment failed: ${e.message}`))
  log(`✓ Role assigned`)
} else {
  log(`✓ Role already assigned`)
}

// ── Persist to state.json ─────────────────────────────────────────────────────

const fp    = join(projectDir, '.dashboard', 'state.json')
const s     = JSON.parse(readFileSync(fp, 'utf8'))
s.deployment = s.deployment ?? {}
s.deployment.folderKey  = folderKey
s.deployment.folderName = 'AdminDashboards'
const tmp = fp + '.tmp'
writeFileSync(tmp, JSON.stringify(s, null, 2), 'utf8')
renameSync(tmp, fp)

log(`\n✓ AdminDashboards ready (key: ${folderKey})`)
log('  Administrators group has Folder Administrator access.')
