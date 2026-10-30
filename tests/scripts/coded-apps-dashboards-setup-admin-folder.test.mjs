import { test, before } from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, writeFileSync, mkdirSync, readFileSync } from 'node:fs'
import { resolve, dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { tmpdir } from 'node:os'
import { spawnSync } from 'node:child_process'
import { installFakeTools, fakeEnv, readFakeLog } from './support/coded-apps-dashboards-fake-tools.mjs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const SCRIPT = resolve(__dirname, '../../skills/uipath-coded-apps/assets/scripts/dashboards/setup-admin-folder.mjs')

// execFileSync('uip') cannot resolve a .cmd shim on Windows; the fake `uip` is a POSIX launcher.
const skip = process.platform === 'win32' ? 'fake uip launcher is POSIX-only' : false

let fakeDir
before(() => { fakeDir = installFakeTools() })

const ROLES = 'or roles list --sort-by Id asc --limit 500'
const USERS = 'or users list --username Administrators'
const folders = name => `or folders list --all --name ${name}`
const USER_ROLES = 'or roles user-roles list Administrators --type Group'
const ASSIGN = (group, roles, folder) => `or roles assign --user-key ${group} --role-keys ${roles} --folder-key ${folder}`

const roleList = { Data: [{ Name: 'Viewer', Key: 'role-view' }, { Name: 'Folder Administrator', Key: 'role-admin' }] }
const groupList = { Data: [{ UserName: 'Someone', Type: 'User', Key: 'u-1' }, { UserName: 'ADMINISTRATORS', Type: 'DirectoryGroup', Key: 'grp-1' }] }

/** Run the script with the given fake uip responses; returns { r, calls, state }. */
function run(args, responses, { state } = {}) {
  const work = mkdtempSync(join(tmpdir(), 'saf-'))
  const respFile = join(work, 'responses.json')
  const logFile = join(work, 'calls.log')
  writeFileSync(respFile, JSON.stringify(responses))
  let projectDir = null
  if (state !== undefined) {
    projectDir = join(work, 'proj')
    mkdirSync(join(projectDir, '.dashboard'), { recursive: true })
    writeFileSync(join(projectDir, '.dashboard', 'state.json'), JSON.stringify(state))
  }
  const argv = [SCRIPT, ...args]
  if (projectDir) argv.push(projectDir)
  const r = spawnSync(process.execPath, argv, {
    encoding: 'utf8',
    env: fakeEnv(fakeDir, { FAKE_UIP_RESPONSES: respFile, FAKE_LOG: logFile }),
  })
  const statePath = projectDir && join(projectDir, '.dashboard', 'state.json')
  return {
    r,
    calls: readFakeLog(logFile).map(l => l.replace(/^uip /, '').replace(/ --output json$/, '')),
    readState: () => JSON.parse(readFileSync(statePath, 'utf8')),
  }
}

test('without a folder name it prints usage and exits 1', () => {
  const { r, calls } = run([], {})
  assert.equal(r.status, 1)
  assert.equal(r.stderr, 'Usage: node setup-admin-folder.mjs <FOLDER_NAME> [PROJECT_DIR]\n')
  assert.deepEqual(calls, [])
})

test('an already-provisioned project exits 0 without calling uip', { skip }, () => {
  const { r, calls } = run(['AdminDashboards'], {}, { state: { deployment: { folderKey: 'fk-9' } } })
  assert.equal(r.status, 0)
  assert.match(r.stdout, /✓ Already provisioned \(folderKey: fk-9\)/)
  assert.deepEqual(calls, [])
})

test('creates a missing folder, assigns Folder Administrator to the group and records the key in state.json', { skip }, () => {
  const { r, calls, readState } = run(['AdminDashboards'], {
    [ROLES]: roleList,
    [USERS]: groupList,
    [folders('AdminDashboards')]: { Data: [] },
    'or folders create AdminDashboards': { Data: { Key: 'fk-new' } },
    [USER_ROLES]: { Data: [] },
    [ASSIGN('grp-1', 'role-admin', 'fk-new')]: {},
  }, { state: { app: { name: 'x' } } })
  assert.equal(r.status, 0, r.stderr)
  assert.match(r.stdout, /Folder Administrator role: role-admin/)
  assert.match(r.stdout, /Administrators group: grp-1/)
  assert.match(r.stdout, /Folder created: fk-new/)
  assert.match(r.stdout, /✓ AdminDashboards is ready \(key: fk-new\)/)
  assert.ok(calls.includes('or folders create AdminDashboards'))
  assert.ok(calls.includes(ASSIGN('grp-1', 'role-admin', 'fk-new')))
  assert.deepEqual(readState().deployment, { folderKey: 'fk-new', folderName: 'AdminDashboards' })
})

test('accepts a create response that carries the key at the top level', { skip }, () => {
  const { r } = run(['F1'], {
    [ROLES]: roleList, [USERS]: groupList, [folders('F1')]: {},
    'or folders create F1': { Key: 'fk-top' },
    [USER_ROLES]: { Data: [] },
    [ASSIGN('grp-1', 'role-admin', 'fk-top')]: {},
  })
  assert.equal(r.status, 0, r.stderr)
  assert.match(r.stdout, /Folder created: fk-top/)
})

test('an existing folder whose role is already assigned does nothing and still records state', { skip }, () => {
  const { r, calls, readState } = run(['AdminDashboards'], {
    [ROLES]: roleList,
    [USERS]: groupList,
    [folders('AdminDashboards')]: { Data: [{ Name: 'AdminDashboards', Key: 'fk-old' }] },
    [USER_ROLES]: { Data: [{ FolderPath: 'admindashboards', Role: 'Folder Administrator' }] },
  }, { state: { deployment: { folderKey: null } } })
  assert.equal(r.status, 0, r.stderr)
  assert.match(r.stdout, /already exists: fk-old/)
  assert.match(r.stdout, /Folder Administrator already assigned — nothing to do/)
  assert.ok(!calls.some(c => c.startsWith('or roles assign')))
  assert.equal(readState().deployment.folderKey, 'fk-old')
})

test('an existing folder with other roles keeps them: the assign call carries the union of role keys', { skip }, () => {
  const { r, calls } = run(['AdminDashboards'], {
    [ROLES]: roleList,
    [USERS]: groupList,
    [folders('AdminDashboards')]: { Data: [{ Name: 'AdminDashboards', Key: 'fk-old' }] },
    [USER_ROLES]: { Data: [
      { FolderPath: 'AdminDashboards', Role: 'Viewer', RoleId: 'role-view' },
      { FolderPath: 'Other', Role: 'Viewer', RoleId: 'role-other' },
      { FolderPath: 'AdminDashboards', Role: 'Auditor', roleId: 'role-audit' },
    ] },
    [ASSIGN('grp-1', 'role-view,role-audit,role-admin', 'fk-old')]: {},
  })
  assert.equal(r.status, 0, r.stderr)
  assert.match(r.stdout, /Role not yet assigned — proceeding/)
  assert.match(r.stdout, /roles assign replaces existing roles/)
  assert.ok(calls.includes(ASSIGN('grp-1', 'role-view,role-audit,role-admin', 'fk-old')))
  assert.match(r.stdout, /Administrators group has Folder Administrator access/)
})

test('a missing Folder Administrator role is a fatal error', { skip }, () => {
  const { r } = run(['F'], { [ROLES]: { Data: [{ Name: 'Viewer', Key: 'v' }] }, [USERS]: groupList, [folders('F')]: { Data: [] } })
  assert.equal(r.status, 1)
  assert.match(r.stderr, /^ERROR: "Folder Administrator" role not found/)
})

test('a missing Administrators group lists the groups that do exist', { skip }, () => {
  const { r } = run(['F'], {
    [ROLES]: roleList,
    [USERS]: { Data: [{ UserName: 'Ops', Type: 'DirectoryGroup', Key: 'g' }, { UserName: 'bob', Type: 'User', Key: 'u' }] },
    [folders('F')]: { Data: [] },
  })
  assert.equal(r.status, 1)
  assert.match(r.stderr, /"Administrators" group not found\. Available groups: Ops\n$/)
})

test('with no groups at all the error says (none)', { skip }, () => {
  const { r } = run(['F'], { [ROLES]: roleList, [USERS]: {}, [folders('F')]: {} })
  assert.equal(r.status, 1)
  assert.match(r.stderr, /Available groups: \(none\)/)
})

test('a create response without a key is a fatal error', { skip }, () => {
  const { r } = run(['F'], {
    [ROLES]: roleList, [USERS]: groupList, [folders('F')]: { Data: [] },
    'or folders create F': { Data: {} },
  })
  assert.equal(r.status, 1)
  assert.match(r.stderr, /Could not extract folder key from create response/)
})

test('a failing uip call surfaces as ERROR on stderr with exit 1', { skip }, () => {
  const { r } = run(['F'], { [ROLES]: { __fail: true } })
  assert.equal(r.status, 1)
  assert.match(r.stderr, /^ERROR: Command failed: uip or roles list/m)
})
