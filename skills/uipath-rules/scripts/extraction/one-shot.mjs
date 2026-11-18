#!/usr/bin/env node
// STOP-GAP until the IXP primitives API and its CLI ship (see call-rules-api.mjs); then this wrapper keeps
// its job and swaps the API script for the CLI.
// The whole one-shot path in one command: check, run IXP rules extraction, write the returned DMN
// into an existing BusinessRules project, then `uip rules refresh` and `validate`.
// Usage: node one-shot.mjs --project-dir <PROJECT_DIR> --file <POLICY_FILE> --out <OUT_DIR> --folder-key <FOLDER_GUID> \
//   --query "<QUESTION>" --outcome "<LABEL>[:polarity[:operator]]" ... [--score-band "MIN-MAX=<LABEL>"] ... \
//   [--notes "<TEXT>"] [--schema-file <FILE>] [--profile <UIP_PROFILE>] [--poll-interval <S>] [--timeout <S>] [--check]
// Every flag except --project-dir is passed to call-rules-api.mjs unchanged.
// Prints one JSON object on stdout; exit 0 on success, 1 on a failure that names its stage, 2 on a usage error.
// `fallback: true` means the pipeline is not available here: continue with the guided flow. A DMN that was
// written but fails `validate` is NOT a fallback: the draft exists and is repaired, not regenerated.
import { spawnSync } from 'node:child_process'
import { readFileSync, writeFileSync, readdirSync, existsSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const args = process.argv.slice(2)
const OWN_VALUE_FLAGS = ['--project-dir']
const flag = name => {
  const i = args.indexOf(name)
  return i >= 0 ? args[i + 1] : undefined
}
const has = name => args.includes(name)

class Failure extends Error {
  constructor(stage, message, { fallback = false, exit = 1 } = {}) {
    super(message)
    this.stage = stage
    this.fallback = fallback
    this.exit = exit
  }
}

const passThrough = () => {
  const out = []
  for (let i = 0; i < args.length; i++) {
    if (OWN_VALUE_FLAGS.includes(args[i])) i++
    else out.push(args[i])
  }
  return out
}

// Runs a child that prints one JSON object on stdout; returns it with the exit code.
function runJson(cmd, cmdArgs, stage) {
  const res = spawnSync(cmd, cmdArgs, { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 })
  if (res.error) throw new Failure(stage, `could not run ${cmd}: ${res.error.code || res.error.message}`, { fallback: stage === 'login' })
  const text = (res.stdout || '').trim()
  const lastJson = text.slice(text.indexOf('{'))
  try {
    return { json: JSON.parse(lastJson), code: res.status }
  } catch {
    throw new Failure(stage, `${cmd} printed no JSON result (exit ${res.status})`)
  }
}

function projectDmn(projectDir) {
  if (!existsSync(join(projectDir, 'project.uiproj'))) {
    throw new Failure('project', `${projectDir} is not a BusinessRules project (no project.uiproj); create it first`, { exit: 2 })
  }
  const dmns = readdirSync(projectDir).filter(f => f.toLowerCase().endsWith('.dmn'))
  if (dmns.length !== 1) throw new Failure('project', `the project must hold exactly one .dmn; found ${dmns.length}`, { exit: 2 })
  return join(projectDir, dmns[0])
}

function lifecycle(projectDir) {
  const profile = flag('--profile')
  const prefix = profile ? ['--profile', profile] : []
  const refresh = runJson('uip', [...prefix, 'rules', 'refresh', projectDir, '--output', 'json'], 'validate')
  if (refresh.json.Result !== 'Success') throw new Failure('validate', `uip rules refresh failed: ${String(refresh.json.Message || refresh.json.Code || 'no detail').slice(0, 300)}`)
  const validate = runJson('uip', [...prefix, 'rules', 'validate', projectDir, '--output', 'json'], 'validate')
  const data = validate.json.Data || {}
  const diagnostics = Array.isArray(data.Diagnostics) ? data.Diagnostics : []
  return { valid: validate.json.Result === 'Success' && data.Status === 'Valid', diagnostics }
}

function main() {
  const projectDir = flag('--project-dir')
  if (!projectDir) throw new Failure('usage', 'usage: one-shot.mjs --project-dir <PROJECT_DIR> --file <POLICY_FILE> --out <OUT_DIR> --folder-key <FOLDER_GUID> --query <QUESTION> --outcome <LABEL> [--check]', { exit: 2 })
  // Before a billed run: a project that cannot take the result must stop the run, not waste it.
  const dmnPath = projectDmn(projectDir)

  const forwarded = passThrough()
  const api = join(HERE, 'call-rules-api.mjs')

  const check = runJson(process.execPath, [api, ...forwarded, ...(has('--check') ? [] : ['--check'])], 'login')
  if (check.json.status === 'error') return fail(check.json, check.code)
  if (has('--check')) {
    console.log(JSON.stringify({ status: 'check-passed', project_dmn: dmnPath, host: check.json.host, profile: check.json.profile }))
    return
  }

  const run = runJson(process.execPath, [api, ...forwarded], 'run')
  if (run.json.status === 'error') return fail(run.json, run.code)

  let dmn
  try {
    dmn = readFileSync(run.json.dmn_file, 'utf8')
  } catch {
    throw new Failure('write', 'the pipeline DMN could not be read back from the output directory')
  }
  writeFileSync(dmnPath, dmn)

  const result = lifecycle(projectDir)
  console.log(JSON.stringify({
    status: result.valid ? 'completed' : 'completed-with-diagnostics',
    run_id: run.json.run_id,
    project_dmn: dmnPath,
    elapsed_seconds: run.json.elapsed_seconds,
    valid: result.valid,
    diagnostics: result.diagnostics.slice(0, 20),
    next: result.valid
      ? 'validated: read the written .dmn, run the sampled runs, show its inputs and outcomes beside the profile'
      : 'repair the diagnostics in the written .dmn (3 rounds at most); do not run the pipeline again',
  }))
  if (!result.valid) process.exitCode = 1
}

// A child failure: keep its stage, error and fallback exactly as reported.
function fail(json, code) {
  console.log(JSON.stringify({ status: 'error', stage: json.stage, error: json.error, fallback: json.fallback === true, ...(json.run_id ? { run_id: json.run_id } : {}) }))
  process.exit(code && code > 0 ? code : 1)
}

try {
  main()
} catch (err) {
  const f = err instanceof Failure ? err : new Failure('internal', `unexpected error: ${err.message}`)
  console.log(JSON.stringify({ status: 'error', stage: f.stage, error: f.message, fallback: f.fallback }))
  process.exit(f.exit)
}
