#!/usr/bin/env node
/**
 * setup-admin-folder.mjs — Idempotent AdminDashboards folder provisioning
 *
 * Creates the named folder and assigns Folder Administrator to the
 * Administrators group. Skips steps already done.
 *
 * Usage:
 *   node setup-admin-folder.mjs <FOLDER_NAME> [PROJECT_DIR]
 *
 * If PROJECT_DIR is provided, reads folderKey from .dashboard/state.json
 * first and exits immediately if already provisioned.
 */

import { execFileSync }                         from 'child_process'
import { existsSync, readFileSync, writeFileSync, renameSync } from 'fs'
import { join, resolve }                        from 'path'

const FOLDER_NAME = process.argv[2]
const PROJECT_DIR = process.argv[3] ? resolve(process.argv[3]) : null

if (!FOLDER_NAME) {
  process.stderr.write('Usage: node setup-admin-folder.mjs <FOLDER_NAME> [PROJECT_DIR]\n')
  process.exit(1)
}

// Pass argv as an array (NOT a shell string) so values like FOLDER_NAME can never
// inject shell commands — execFileSync does not spawn a shell.
function uip(args) {
  return JSON.parse(execFileSync('uip', [...args, '--output', 'json'], { encoding: 'utf8' }))
}

function log(msg) { process.stdout.write(msg + '\n') }
function fail(msg) { process.stderr.write(`ERROR: ${msg}\n`); process.exit(1) }

function updateState(projectDir, folderKey, folderName) {
  const fp    = join(projectDir, '.dashboard', 'state.json')
  if (!existsSync(fp)) return
  const state = JSON.parse(readFileSync(fp, 'utf8'))
  state.deployment       = state.deployment ?? {}
  state.deployment.folderKey  = folderKey
  state.deployment.folderName = folderName
  const tmp = fp + '.tmp'
  writeFileSync(tmp, JSON.stringify(state, null, 2))
  renameSync(tmp, fp)
}

async function main() {
  // Fast-path: already provisioned
  if (PROJECT_DIR) {
    const statePath = join(PROJECT_DIR, '.dashboard', 'state.json')
    if (existsSync(statePath)) {
      const state = JSON.parse(readFileSync(statePath, 'utf8'))
      if (state.deployment?.folderKey) {
        log(`✓ Already provisioned (folderKey: ${state.deployment.folderKey})`)
        process.exit(0)
      }
    }
  }

  log(`\n[Phase 1] Looking up role, group, and folder in parallel…`)

  const [rolesResult, usersResult, foldersResult] = await Promise.all([
    Promise.resolve(uip(['or','roles','list','--sort-by','Id asc','--limit','500'])),
    Promise.resolve(uip(['or','users','list','--username','Administrators'])),
    Promise.resolve(uip(['or','folders','list','--all','--name',FOLDER_NAME])),
  ]).catch(e => fail(e.message))

  // Extract Folder Administrator role key
  const adminRole = rolesResult.Data?.find(r => r.Name === 'Folder Administrator')
  if (!adminRole) fail('"Folder Administrator" role not found. Check: uip or roles list --output json')
  const roleKey = adminRole.Key
  log(`  ✓ Folder Administrator role: ${roleKey}`)

  // Extract Administrators group key (case-insensitive)
  const group = usersResult.Data?.find(u => {
    const name = (u.UserName ?? u.Name ?? '').toLowerCase()
    const type = (u.Type ?? u.type ?? '').toLowerCase()
    return name === 'administrators' && (type.includes('group') || type === '')
  })
  if (!group) {
    const available = (usersResult.Data ?? [])
      .filter(u => (u.Type ?? '').toLowerCase().includes('group'))
      .map(u => u.UserName ?? u.Name).join(', ')
    fail(`"Administrators" group not found. Available groups: ${available || '(none)'}`)
  }
  const groupKey = group.Key
  log(`  ✓ Administrators group: ${groupKey}`)

  // Create folder if missing
  let folderKey = foldersResult.Data?.find(f => f.Name === FOLDER_NAME)?.Key
  let folderJustCreated = false

  if (folderKey) {
    log(`  ✓ Folder "${FOLDER_NAME}" already exists: ${folderKey}`)
  } else {
    log(`\n[Phase 2] Creating folder "${FOLDER_NAME}"…`)
    const created = uip(['or','folders','create',FOLDER_NAME])
    folderKey = created.Data?.Key ?? created.Key
    if (!folderKey) fail('Could not extract folder key from create response')
    folderJustCreated = true
    log(`  ✓ Folder created: ${folderKey}`)
  }

  // Check if role already assigned (skip if folder was just created)
  if (!folderJustCreated) {
    log(`\n[Phase 3] Checking existing role assignment…`)
    const userRoles = uip(['or','roles','user-roles','list','Administrators','--type','Group'])
    const alreadyAssigned = userRoles.Data?.some(
      r => (r.FolderPath ?? '').toLowerCase() === FOLDER_NAME.toLowerCase()
        && (r.Role ?? '').toLowerCase() === 'folder administrator'
    )
    if (alreadyAssigned) {
      log(`  ✓ Folder Administrator already assigned — nothing to do.`)
      if (PROJECT_DIR) updateState(PROJECT_DIR, folderKey, FOLDER_NAME)
      log(`\n✓ ${FOLDER_NAME} ready (key: ${folderKey})`)
      return
    }
    log(`  Role not yet assigned — proceeding.`)
  }

  // Assign role — read existing roles first to avoid replacing them
  log(`\n[Phase 4] Assigning Folder Administrator to Administrators…`)
  log(`  ⚠ roles assign replaces existing roles. Reading current assignments first.`)

  let existingRoleKeys = []
  try {
    const existingAssignments = uip(['or','roles','user-roles','list','Administrators','--type','Group'])
    const folderRoles = existingAssignments.Data?.filter(
      r => (r.FolderPath ?? '').toLowerCase() === FOLDER_NAME.toLowerCase()
    )
    existingRoleKeys = folderRoles?.map(r => r.RoleId ?? r.roleId).filter(Boolean) ?? []
  } catch { /* ignore — folder is new or no existing assignments */ }

  // Include new role key in the union
  const allRoleKeys = [...new Set([...existingRoleKeys, roleKey])].join(',')
  uip(['or','roles','assign','--user-key',groupKey,'--role-keys',allRoleKeys,'--folder-key',folderKey])
  log(`  ✓ Role assigned.`)

  if (PROJECT_DIR) updateState(PROJECT_DIR, folderKey, FOLDER_NAME)

  log(`\n✓ ${FOLDER_NAME} is ready (key: ${folderKey})`)
  log(`  Administrators group has Folder Administrator access.`)
}

main().catch(e => { process.stderr.write(`ERROR: ${e.message}\n`); process.exit(1) })
