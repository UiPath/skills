#!/usr/bin/env node
// One-shot rules extraction through the ECS RulesExtraction RunOnce API: upload the policy as an
// Orchestrator attachment, start a run, poll it, download the DMN, delete the attachments.
//
// STOP-GAP. Why this calls the REST API directly instead of a `uip` command: the `uip` CLI has no
// command for IXP rules extraction (the ECS RulesExtraction RunOnce processor). The IXP team is
// building a new primitives API, with a CLI on top of it, that will supersede this API. Until it
// ships we deliberately do not build a CLI for the existing API; this skill is the one-off that
// calls that public API surface. When the primitives CLI is released, replace this script with it,
// keep one-shot.mjs as the wrapper, and delete this file.
// Only the login comes from the CLI: the tenant URL, organization, tenant and access token all come
// from the `uip login` session, nothing is hardcoded, and the token is read here and never printed
// or put on a command line.
// Usage: node call-rules-api.mjs --file <POLICY_FILE> --out <OUT_DIR> --folder-key <FOLDER_GUID> \
//   --query "<QUESTION>" --outcome "<LABEL>[:polarity[:operator]]" ... [--score-band "MIN-MAX=<LABEL>"] ... \
//   [--notes "<TEXT>"] [--schema-file <FILE>] [--profile <UIP_PROFILE>] [--poll-interval <SECONDS>] \
//   [--timeout <SECONDS>] [--check]
// Prints one JSON object on stdout. Exit 0 on success (or a passing --check), 1 on a failure that
// names its stage, 2 on a usage error. A failure carries `fallback`: true when the API is not
// available to this user or environment (continue with the guided flow), false when the request
// itself needs changing. Environment (base URL, organization, tenant, token) comes from the
// `uip login` session; nothing is hardcoded and the token and signed URLs are never printed.
import { execFileSync } from 'node:child_process'
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs'
import { basename, join } from 'node:path'
import net from 'node:net'

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
const ODATA_TYPE = '#UiPath.Vdbs.Domain.Api.V20Models.RulesExtractionProcessorCreateRequest'
const ODATA_TYPE_RUN_ONCE = '#UiPath.Vdbs.Domain.Api.V20Models.RulesExtractionRunOnceProcessorRequest'
const MAX_QUERY = 2000
const MAX_NOTES = 8000
const MAX_DMN_BYTES = 20 * 1024 * 1024
const REQUEST_TIMEOUT_MS = 60000
const UNAVAILABLE = new Set([401, 403, 404])
const RUNNING = new Set(['Queued', 'InProgress'])
const MAX_POLL_BLIPS = 5

// Set once RunOnce returned: from then on a billed run exists, whatever happens next.
let activeRunId

const args = process.argv.slice(2)
const flag = name => {
  const i = args.indexOf(name)
  return i >= 0 ? args[i + 1] : undefined
}
const flagAll = name => args.flatMap((a, i) => (a === name && args[i + 1] !== undefined ? [args[i + 1]] : []))
const has = name => args.includes(name)

class Failure extends Error {
  constructor(stage, message, { fallback = true, exit = 1, transient = false } = {}) {
    super(message)
    this.stage = stage
    this.fallback = fallback
    this.exit = exit
    this.transient = transient
  }
}
const usage = message => new Failure('usage', message, { fallback: false, exit: 2 })
const cap = word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()

// ---- Profile ----------------------------------------------------------------------------------

const POLARITY = new Set(['positive', 'negative', 'neutral'])
const OPERATOR = new Set(['any', 'all', 'first'])

function buildProfile() {
  const query = flag('--query')
  if (!query || !query.trim()) throw usage('--query is required')
  if (query.length > MAX_QUERY) throw usage(`--query is ${query.length} characters; the API takes at most ${MAX_QUERY}`)
  const notes = flag('--notes')
  if (notes && notes.length > MAX_NOTES) throw usage(`--notes is ${notes.length} characters; the API takes at most ${MAX_NOTES}`)

  const outcomes = flagAll('--outcome').map(spec => {
    const [value, polarity = 'positive', operator = 'any', ...extra] = spec.split(':')
    if (!value.trim() || extra.length) throw usage(`bad --outcome "${spec}": use Label[:polarity[:operator]]`)
    if (!POLARITY.has(polarity.toLowerCase())) throw usage(`bad polarity "${polarity}" in --outcome "${spec}"`)
    if (!OPERATOR.has(operator.toLowerCase())) throw usage(`bad operator "${operator}" in --outcome "${spec}"`)
    return { value: value.trim(), polarity: cap(polarity), operator: cap(operator) }
  })
  if (new Set(outcomes.map(o => o.value)).size !== outcomes.length) throw usage('--outcome labels must be unique')

  const bands = flagAll('--score-band').map(spec => {
    const m = /^(\d+)-(\d*)=(.+)$/.exec(spec)
    if (!m) throw usage(`bad --score-band "${spec}": use MIN-MAX=Outcome, MAX empty for an open top band`)
    const band = { minScore: Number(m[1]), outcome: m[3].trim() }
    if (m[2] !== '') band.maxScore = Number(m[2])
    if (band.maxScore !== undefined && band.maxScore < band.minScore) throw usage(`--score-band "${spec}": MAX is below MIN`)
    return band
  })
  for (const b of bands) {
    if (!outcomes.some(o => o.value === b.outcome)) throw usage(`--score-band outcome "${b.outcome}" is not an --outcome label`)
  }
  if (bands.length === 0 && outcomes.length === 0) throw usage('give at least one --outcome, or --score-band entries')

  const profile = { query }
  if (notes) profile.notes = notes
  // A scored profile sends its bands (outcomes are derived from them); a direct one sends its outcomes.
  if (bands.length) {
    profile.modelType = 'ScoredOutcome'
    profile.scoreBands = [...bands].sort((a, b) => a.minScore - b.minScore)
  } else {
    profile.modelType = 'DirectOutcome'
    profile.outcomes = outcomes
  }
  return profile
}

// ---- Environment from the uip login session ---------------------------------------------------

function uip(extra) {
  const profile = flag('--profile')
  const prefix = profile ? ['--profile', profile] : []
  try {
    const out = execFileSync('uip', [...prefix, ...extra, '--output', 'json'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 30000 })
    return JSON.parse(out)
  } catch (err) {
    if (err.code === 'ENOENT') throw new Failure('login', 'the uip CLI is not installed or not on PATH')
    throw new Failure('login', 'uip login status could not be read; ask the user to run `! uip login`')
  }
}

function resolveSession() {
  const status = uip(['login', 'status'])
  const d = status.Data || {}
  if (d.Status !== 'Logged in') throw new Failure('login', 'not logged in; ask the user to run `! uip login`')
  if (d.ExpirationDate && Date.parse(d.ExpirationDate) <= Date.now()) {
    throw new Failure('login', 'the uip login has expired; ask the user to run `! uip login`')
  }
  const { BaseUrl: baseUrl, OrganizationId: org, TenantId: tenant } = d
  if (!baseUrl || !org || !tenant) throw new Failure('login', 'the login has no base URL, organization or tenant')
  const which = uip(['login', 'which'])
  const authPath = which.Data && which.Data.Path
  if (!authPath || !existsSync(authPath)) throw new Failure('login', 'the login has no readable credentials file')
  const line = readFileSync(authPath, 'utf8').split(/\r?\n/).find(l => l.startsWith('UIPATH_ACCESS_TOKEN='))
  const token = line ? line.slice('UIPATH_ACCESS_TOKEN='.length).trim() : ''
  if (!token) throw new Failure('login', 'the login has no access token; ask the user to run `! uip login`')
  const expiresAt = d.ExpirationDate ? Date.parse(d.ExpirationDate) : undefined
  return { baseUrl: baseUrl.replace(/\/+$/, ''), org, tenant, token, expiresAt }
}

// ---- HTTP -------------------------------------------------------------------------------------

async function http(stage, url, init = {}) {
  let res
  try {
    res = await fetch(url, { redirect: 'manual', signal: AbortSignal.timeout(init.timeoutMs || REQUEST_TIMEOUT_MS), ...init })
  } catch (err) {
    // The error text can carry a signed URL: name only the class.
    throw new Failure(stage, `request failed: ${err.name}`, { transient: true })
  }
  return res
}

function check(stage, res, what) {
  if (res.status >= 300 && res.status < 400) throw new Failure(stage, `${what} was redirected (${res.status}); the API is not reachable with this login`)
  if (UNAVAILABLE.has(res.status)) {
    const hint = res.status === 403 ? '; the folder permission is missing or the feature is not enabled in this environment' : ''
    throw new Failure(stage, `${what} returned ${res.status}${hint}`)
  }
  if (res.status === 400) throw new Failure(stage, `${what} was rejected (400): the profile or attachment is not one the API takes`, { fallback: false })
  if (res.status >= 400) throw new Failure(stage, `${what} returned ${res.status}`, { transient: res.status >= 500 })
}

// URL parsing turns ::ffff:127.0.0.1 into ::ffff:7f00:1; unfold the IPv4 inside an IPv6 address.
const embeddedIPv4 = h => {
  const m = /^(?:0{0,4}:){2,5}(?:ffff:)?([0-9a-f]{1,4}):([0-9a-f]{1,4})$/.exec(h)
  if (!m) return null
  const hi = parseInt(m[1], 16)
  const lo = parseInt(m[2], 16)
  return `${hi >> 8}.${hi & 255}.${lo >> 8}.${lo & 255}`
}

const isInternalHost = host => {
  const h = host.replace(/^\[|\]$/g, '').replace(/\.$/, '').toLowerCase()
  if (h === 'localhost' || h.endsWith('.localhost')) return true
  if (net.isIPv4(h)) {
    const [a, b] = h.split('.').map(Number)
    return a === 10 || a === 127 || a === 0 || a >= 224 || (a === 169 && b === 254) || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168) || (a === 100 && b >= 64 && b <= 127)
  }
  if (net.isIPv6(h)) {
    const v4 = embeddedIPv4(h)
    if (v4) return isInternalHost(v4)
    return h === '::1' || h === '::' || /^f[cd]/.test(h) || /^fe[89abcdef]/.test(h) || h.startsWith('ff')
  }
  return false
}

const publicHttps = (uri, stage, what) => {
  let url
  try {
    url = new URL(uri)
  } catch {
    throw new Failure(stage, `the ${what} is not a URL`)
  }
  if (url.protocol !== 'https:' || isInternalHost(url.hostname)) throw new Failure(stage, `the ${what} is not an https URL of a public host`)
  return url
}

async function readCapped(res) {
  const chunks = []
  let size = 0
  try {
    for await (const chunk of res.body) {
      size += chunk.length
      if (size > MAX_DMN_BYTES) throw new Failure('download', `the output is larger than ${MAX_DMN_BYTES} bytes`)
      chunks.push(chunk)
    }
  } catch (err) {
    if (err instanceof Failure) throw err
    throw new Failure('download', 'the output download was interrupted', { transient: true })
  }
  return Buffer.concat(chunks)
}

// ---- The API ----------------------------------------------------------------------------------

function client(session, folderKey) {
  const headers = { Authorization: `Bearer ${session.token}`, 'X-UiPath-FolderKey': folderKey }
  const root = `${session.baseUrl}/${session.org}/${session.tenant}`
  const orchestrator = `${root}/orchestrator_/odata/Attachments`
  const ecs = `${root}/ecs_/v2`

  async function upload(name, data) {
    const create = await http('upload', orchestrator, { method: 'POST', headers: { ...headers, 'Content-Type': 'application/json' }, body: JSON.stringify({ Name: name }) })
    check('upload', create, 'Attachments create')
    const body = await create.json()
    const id = String(body.Id)
    const access = body.BlobFileAccess || {}
    const putHeaders = Object.fromEntries((access.Headers?.Keys || []).map((k, i) => [k, access.Headers.Values[i]]))
    if (access.RequiresAuth) Object.assign(putHeaders, headers)
    try {
      const putUrl = publicHttps(access.Uri, 'upload', 'attachment upload URI')
      const put = await http('upload', putUrl.href, { method: 'PUT', headers: putHeaders, body: data, timeoutMs: 300000 })
      if (put.status >= 300) {
        check('upload', put, 'Attachment blob PUT')
        throw new Failure('upload', `Attachment blob PUT returned ${put.status}`)
      }
    } catch (err) {
      // The attachment exists in the folder; a failed upload must not leave it behind.
      await remove(id).catch(() => {})
      throw err
    }
    return id
  }

  async function remove(id) {
    const res = await http('cleanup', `${orchestrator}(${id})`, { method: 'DELETE', headers })
    if (res.status === 404) return
    check('cleanup', res, 'Attachment delete')
  }

  // Run once: ECS takes no idempotency key, so a retry could start (and bill) a second run.
  async function runOnce(name, profile, attachmentId, schemaId) {
    const processor = { '@odata.type': ODATA_TYPE, name, profile }
    if (schemaId) {
      processor['@odata.type'] = ODATA_TYPE_RUN_ONCE
      processor.schemaAttachment = { attachmentId: schemaId }
    }
    const res = await http('run', `${ecs}/processors/runonce`, {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ processor, attachmentReferences: [{ attachmentId }] }),
    })
    check('run', res, 'RulesExtraction RunOnce')
    const runId = (await res.json()).runId
    if (typeof runId !== 'string' || !runId) throw new Failure('run', 'RunOnce returned no run id')
    return runId
  }

  async function getRun(runId) {
    const res = await http('poll', `${ecs}/pipelineruns/${runId}`, { headers })
    check('poll', res, 'run status')
    return res.json()
  }

  async function download(runId) {
    const res = await http('download', `${ecs}/pipelineruns/${runId}/getreaduri`, { headers })
    check('download', res, 'read URI')
    const { uri, isProxied } = await res.json()
    if (typeof uri !== 'string' || !uri) throw new Failure('download', 'the run returned no read URI')
    const url = publicHttps(uri, 'download', 'read URI')
    let sendHeaders
    if (isProxied) {
      // Credentials go only to this tenant's own ECS path.
      const base = new URL(`${root}/`)
      let decoded = ''
      try {
        decoded = decodeURIComponent(url.pathname)
      } catch {
        decoded = null
      }
      const unsafe = p => p.includes('\\') || p.split('/').some(s => s === '.' || s === '..')
      const bad = url.host !== base.host || url.username || url.password || !url.pathname.startsWith(new URL(`${root}/ecs_/`).pathname) || decoded === null || unsafe(url.pathname) || unsafe(decoded)
      if (bad) throw new Failure('download', "the proxied output URL is not on this tenant's ECS")
      sendHeaders = headers
    }
    const out = await http('download', url.href, { headers: sendHeaders })
    if (out.status !== 200) throw new Failure('download', `the output download returned ${out.status}`, { transient: out.status >= 500 || out.status === 403 })
    try {
      return new TextDecoder('utf-8', { fatal: true }).decode(await readCapped(out))
    } catch (err) {
      if (err instanceof Failure) throw err
      throw new Failure('download', 'the run output is not valid UTF-8')
    }
  }

  return { upload, remove, runOnce, getRun, download }
}

// ---- Main -------------------------------------------------------------------------------------

async function main() {
  const file = flag('--file')
  const outDir = flag('--out')
  const folderKey = flag('--folder-key')
  const schemaFile = flag('--schema-file')
  if (!file || !outDir) throw usage('usage: call-rules-api.mjs --file <POLICY_FILE> --out <OUT_DIR> --folder-key <FOLDER_GUID> --query <QUESTION> --outcome <LABEL>')
  if (!existsSync(file)) throw usage(`--file not found: ${file}`)
  if (schemaFile && !existsSync(schemaFile)) throw usage(`--schema-file not found: ${schemaFile}`)
  if (!folderKey || !UUID.test(folderKey)) throw usage('--folder-key must be an Orchestrator folder GUID; resolve it with `uip or folders list --output json` and ask the user which folder')
  const interval = Number(flag('--poll-interval') || 10)
  const timeout = Number(flag('--timeout') || 900)
  if (!(interval > 0) || !(timeout > 0)) throw usage('--poll-interval and --timeout are positive seconds')

  const profile = buildProfile()
  const session = resolveSession()
  if (has('--check')) {
    console.log(JSON.stringify({ status: 'check-passed', host: new URL(session.baseUrl).host, profile }))
    return
  }

  // A token that expires mid-run would abandon a billed run: require it to outlast the polling window.
  if (session.expiresAt && session.expiresAt - Date.now() < (timeout + 60) * 1000) {
    throw new Failure('login', 'the uip login expires before a run could finish; ask the user to run `! uip login`')
  }

  const started = Date.now()
  const api = client(session, folderKey)
  const attachments = []
  try {
    const attachmentId = await api.upload(basename(file), readFileSync(file))
    attachments.push(attachmentId)
    const schemaId = schemaFile ? await api.upload(basename(schemaFile), readFileSync(schemaFile)) : undefined
    if (schemaId) attachments.push(schemaId)

    const runId = await api.runOnce(`rules-${basename(file)}`.slice(0, 256), profile, attachmentId, schemaId)
    activeRunId = runId

    const deadline = Date.now() + timeout * 1000
    let blips = 0
    for (;;) {
      let run
      try {
        run = await api.getRun(runId)
        blips = 0
      } catch (err) {
        // A network error or a 5xx while polling does not end the run: wait and ask again.
        if (!(err instanceof Failure) || !err.transient || ++blips > MAX_POLL_BLIPS) throw err
        if (Date.now() >= deadline) throw err
        await new Promise(r => setTimeout(r, interval * 1000))
        continue
      }
      if (run.status === 'Successful') break
      if (run.status === 'Failed') throw new Failure('poll', `the run failed: ${run.failureReason || 'no reason given'}`)
      if (!RUNNING.has(run.status)) throw new Failure('poll', `the run ended with the unexpected status ${JSON.stringify(String(run.status)).slice(0, 40)}`)
      if (Date.now() >= deadline) throw new Failure('poll', `the run ${runId} did not finish in ${timeout}s; it may still be running in the tenant`)
      await new Promise(r => setTimeout(r, interval * 1000))
    }

    let dmn
    try {
      dmn = await api.download(runId)
    } catch (err) {
      // A transient failure (network, 5xx, an expired signed URL) gets one retry with a fresh read URI.
      if (!(err instanceof Failure) || err.stage !== 'download' || !err.transient) throw err
      dmn = await api.download(runId)
    }
    if (!/<(?:\w+:)?definitions[\s>]/.test(dmn)) throw new Failure('download', 'the run output is not a DMN document')
    mkdirSync(outDir, { recursive: true })
    const dmnFile = join(outDir, 'policy.dmn')
    writeFileSync(dmnFile, dmn)
    writeFileSync(join(outDir, 'profile.json'), JSON.stringify(profile, null, 2))
    console.log(JSON.stringify({ status: 'completed', run_id: runId, dmn_file: dmnFile, dmn_bytes: Buffer.byteLength(dmn), elapsed_seconds: Math.round((Date.now() - started) / 1000) }))
  } finally {
    const leftover = []
    for (const id of attachments) await api.remove(id).catch(() => leftover.push(id))
    if (leftover.length) process.stderr.write(`cleanup: ${leftover.length} attachment(s) were not deleted\n`)
  }
}

main().catch(err => {
  const f = err instanceof Failure ? err : new Failure('internal', `unexpected error: ${err.message}`)
  // After RunOnce a billed run exists: name it so the caller never starts a second one.
  console.log(JSON.stringify({ status: 'error', stage: f.stage, error: f.message, fallback: f.fallback, ...(activeRunId ? { run_id: activeRunId } : {}) }))
  process.exit(f.exit)
})
