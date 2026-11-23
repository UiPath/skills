// Shared test support (not a test file): fake `npm`, `npx` and `uip` executables that
// are put first on PATH so the dashboard scripts never reach the network, a real
// install, or Orchestrator. Behaviour is steered through environment variables:
//
//   FAKE_LOG            file every invocation is appended to ("tool arg arg ...")
//   FAKE_NPM_FAIL       comma list of install kinds that fail: ci-offline, ci, install
//   FAKE_SDK_VERSION    version the fake npm writes for @uipath/uipath-typescript (default 1.5.1)
//   FAKE_METRICS_FAIL   set → `npx tsc -p tsconfig.metrics.json` fails with a metrics error
//   FAKE_TSC_FAIL       set → `npx tsc --noEmit` fails
//   FAKE_UIP_RESPONSES  JSON file mapping "uip args without --output json" → response JSON
//                       (a response of {"__fail": true} makes that call exit 1)

import { mkdtempSync, writeFileSync, readFileSync, existsSync, chmodSync } from 'node:fs'
import { join, delimiter } from 'node:path'
import { tmpdir } from 'node:os'

const FAKE_JS = `
const fs = require('fs'), path = require('path')
const [tool, ...args] = process.argv.slice(2)
if (process.env.FAKE_LOG) fs.appendFileSync(process.env.FAKE_LOG, [tool, ...args].join(' ') + '\\n')
if (tool === 'npm') {
  const kind = args[0] === 'install' ? 'install' : (args.includes('--prefer-offline') ? 'ci-offline' : 'ci')
  if ((process.env.FAKE_NPM_FAIL || '').split(',').includes(kind)) { process.stderr.write('npm ERR! ' + kind + ' failed\\n'); process.exit(1) }
  const nm = path.join(process.cwd(), 'node_modules')
  fs.mkdirSync(path.join(nm, '@uipath', 'uipath-typescript'), { recursive: true })
  fs.writeFileSync(path.join(nm, '.package-lock.json'), '{}')
  fs.writeFileSync(path.join(nm, '@uipath', 'uipath-typescript', 'package.json'), JSON.stringify({ version: process.env.FAKE_SDK_VERSION || '1.5.1' }))
} else if (tool === 'npx') {
  if (args[0] === 'tsc' && args[1] === '-p' && process.env.FAKE_METRICS_FAIL) {
    process.stdout.write('src/metrics/orders-table.ts(1,1): error TS2322: bad metric\\n'); process.exit(2)
  }
  if (args[0] === 'tsc' && args[1] === '--noEmit' && process.env.FAKE_TSC_FAIL) {
    process.stdout.write('src/App.tsx(1,1): error TS2304: boom\\n'); process.exit(2)
  }
} else if (tool === 'uip') {
  const rest = args.slice(0, -2)
  const responses = JSON.parse(fs.readFileSync(process.env.FAKE_UIP_RESPONSES, 'utf8'))
  const key = rest.join(' ')
  if (!(key in responses) || (responses[key] && responses[key].__fail)) { process.stderr.write('fake uip: no response for ' + key + '\\n'); process.exit(1) }
  process.stdout.write(JSON.stringify(responses[key]))
}

`

/** Create a directory holding fake npm/npx/uip launchers. Returns its path. */
export function installFakeTools() {
  const dir = mkdtempSync(join(tmpdir(), 'fk-'))
  writeFileSync(join(dir, 'fake.js'), FAKE_JS)
  for (const tool of ['npm', 'npx', 'uip']) {
    const sh = join(dir, tool)
    writeFileSync(sh, `#!/bin/sh\nexec "${process.execPath}" "${join(dir, 'fake.js')}" ${tool} "$@"\n`)
    chmodSync(sh, 0o755)
    writeFileSync(join(dir, `${tool}.cmd`), `@"${process.execPath}" "${join(dir, 'fake.js')}" ${tool} %*\r\n`)
  }
  return dir
}

const pathKey = Object.keys(process.env).find(k => k.toLowerCase() === 'path') ?? 'PATH'

/** An env for a child process that resolves npm/npx/uip to the fakes. */
export function fakeEnv(fakeDir, extra) {
  const env = { ...process.env, [pathKey]: fakeDir + delimiter + process.env[pathKey], ...extra }
  delete env.NODE_TEST_CONTEXT
  return env
}

/** Lines the fakes recorded (one per invocation). */
export function readFakeLog(logFile) {
  return existsSync(logFile) ? readFileSync(logFile, 'utf8').split('\n').filter(Boolean) : []
}

export { pathKey }
