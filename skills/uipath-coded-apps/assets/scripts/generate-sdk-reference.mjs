#!/usr/bin/env node
/**
 * generate-sdk-reference.mjs
 *
 * Regenerates sdk-field-reference.md from the TypeScript SDK's declaration files.
 *
 * Source of truth (in priority order):
 *   1. scaffold/node_modules/@uipath/uipath-typescript/dist/  ← local .d.ts after npm ci
 *   2. https://uipath.github.io/uipath-typescript/llms-full-content.txt  ← live docs
 *
 * Run:
 *   node generate-sdk-reference.mjs             # auto-detects source
 *   node generate-sdk-reference.mjs --online    # force live docs fetch
 *   node generate-sdk-reference.mjs --check     # exit 1 if output differs from committed file
 *
 * Integrate in CI (verifies doc stays in sync with SDK version):
 *   - Run after npm ci in scaffold/
 *   - node assets/scripts/generate-sdk-reference.mjs --check
 *   - If exit 1: sdk-field-reference.md is stale — regenerate and commit
 */

import { readFileSync, writeFileSync, existsSync, readdirSync } from 'fs'
import { join, resolve, dirname } from 'path'
import { fileURLToPath } from 'url'
import { createHash } from 'crypto'

const __dirname = dirname(fileURLToPath(import.meta.url))

const SDK_DOCS_URL = 'https://uipath.github.io/uipath-typescript/llms-full-content.txt'
const SCAFFOLD_SDK = resolve(__dirname, '../templates/dashboard/scaffold/node_modules/@uipath/uipath-typescript/dist')
const OUTPUT_PATH = resolve(__dirname, '../../../references/dashboards/primitives/sdk-field-reference.md')

const FORCE_ONLINE = process.argv.includes('--online')
const CHECK_MODE = process.argv.includes('--check')

// ── Service manifest ──────────────────────────────────────────────────────────
// Lists every SDK subpath we care about for dashboard generation.
// Add new services here as the SDK grows.
const SERVICES = [
  { subpath: 'jobs',              className: 'Jobs',             importPath: '@uipath/uipath-typescript/jobs' },
  { subpath: 'queues',            className: 'Queues',           importPath: '@uipath/uipath-typescript/queues' },
  { subpath: 'assets',            className: 'Assets',           importPath: '@uipath/uipath-typescript/assets' },
  { subpath: 'tasks',             className: 'Tasks',            importPath: '@uipath/uipath-typescript/tasks' },
  { subpath: 'processes',         className: 'Processes',        importPath: '@uipath/uipath-typescript/processes' },
  { subpath: 'entities',          className: 'Entities',         importPath: '@uipath/uipath-typescript/entities' },
  { subpath: 'cases',             className: 'Cases',            importPath: '@uipath/uipath-typescript/cases' },
  { subpath: 'maestro-processes', className: 'MaestroProcesses', importPath: '@uipath/uipath-typescript/maestro-processes' },
]

// ── .d.ts parser ─────────────────────────────────────────────────────────────

/**
 * Extract all public methods from a class in a .d.ts file.
 * Returns [{name, params, returnType}]
 */
function parseMethods(dtsContent, className) {
  const methods = []
  // Match: methodName(params): ReturnType;
  const methodRe = /^\s{4}(\w+)\s*(<[^>]*>)?\s*\(([^)]*)\)\s*:\s*([^;]+);/gm
  let m
  while ((m = methodRe.exec(dtsContent)) !== null) {
    methods.push({
      name: m[1],
      params: m[3].trim(),
      returnType: m[4].trim(),
    })
  }
  return methods
}

/**
 * Extract all fields from an interface or type alias in a .d.ts file.
 * Returns [{name, type, optional}]
 */
function parseInterface(dtsContent, interfaceName) {
  // Match the interface body
  const ifaceRe = new RegExp(`(?:interface|type)\\s+${interfaceName}[^{]*\\{([^}]+)\\}`, 's')
  const match = dtsContent.match(ifaceRe)
  if (!match) return []

  const fields = []
  const fieldRe = /^\s{4}(\w+)(\?)?:\s*([^;]+);/gm
  let m
  while ((m = fieldRe.exec(match[1])) !== null) {
    fields.push({
      name: m[1],
      optional: !!m[2],
      type: m[3].trim(),
    })
  }
  return fields
}

/**
 * Find the primary response type name for a method's return type string.
 * E.g. "Promise<PaginatedResponse<JobGetResponse>>" → "JobGetResponse"
 */
function extractResponseTypeName(returnType) {
  // Unwrap Promise<...>, PaginatedResponse<...>, NonPaginatedResponse<...>
  const match = returnType.match(/(?:Paginated|NonPaginated)?Response<(\w+)>/)
  return match ? match[1] : null
}

/**
 * Parse a single service's .d.ts file.
 * Returns { className, importPath, methods[], responseTypes: { TypeName: fields[] } }
 */
function parseServiceDts(subpath, className, importPath) {
  const dtsPath = join(SCAFFOLD_SDK, subpath, 'index.d.ts')
  if (!existsSync(dtsPath)) return null

  const content = readFileSync(dtsPath, 'utf8')
  const methods = parseMethods(content, className)

  // For each method, find its primary response type and parse the interface
  const responseTypes = {}
  for (const method of methods) {
    const typeName = extractResponseTypeName(method.returnType)
    if (typeName && !responseTypes[typeName]) {
      const fields = parseInterface(content, typeName)
      if (fields.length > 0) {
        responseTypes[typeName] = fields
      }
    }
  }

  return { className, importPath, methods, responseTypes }
}

// ── Online fallback: parse llms-full-content.txt ──────────────────────────────

/**
 * Fetch and lightly parse the SDK's LLM-friendly documentation.
 * Returns a simple array of { className, importPath, methods, notes } objects.
 * Less precise than .d.ts parsing but always current without local install.
 */
async function fetchOnlineDocs() {
  console.log(`Fetching ${SDK_DOCS_URL}…`)
  const res = await fetch(SDK_DOCS_URL, { signal: AbortSignal.timeout(30_000) })
  if (!res.ok) throw new Error(`HTTP ${res.status} fetching SDK docs`)
  const text = await res.text()

  const services = []

  // The SDK docs use this pattern for service sections:
  //   ## ClassName Service  (or ## ClassName — ...)
  //   **Import:** `@uipath/uipath-typescript/subpath`
  //   ### `methodName(options?)` → `ReturnType`
  //
  // Also handles the >**methodName**(`params`): `ReturnType` style

  // Split into H2 sections
  const h2Sections = text.split(/^## /m).slice(1)

  for (const section of h2Sections) {
    const titleLine = section.split('\n')[0].trim()
    // Look for known class names in the section title
    const knownClass = SERVICES.find(s =>
      titleLine.toLowerCase().includes(s.className.toLowerCase())
    )
    if (!knownClass) continue

    const { className, importPath } = knownClass

    // Extract methods — look for ### headings with method names
    const methods = []
    const methodRe = /###\s+`?(\w+)\s*\(/g
    let mm
    while ((mm = methodRe.exec(section)) !== null) {
      // Find the return type on the same or next line
      const afterMethod = section.slice(mm.index, mm.index + 300)
      const retMatch = afterMethod.match(/[→:]\s*`([^`]+)`/)
      methods.push({
        name: mm[1],
        params: '',
        returnType: retMatch ? retMatch[1] : 'Promise<unknown>',
      })
    }

    // Also look for > **method**(...) pattern
    const altMethodRe = />\s*\*\*(\w+)\*\*\s*\([^)]*\)\s*:\s*`([^`]+)`/g
    while ((mm = altMethodRe.exec(section)) !== null) {
      if (!methods.find(m => m.name === mm[1])) {
        methods.push({ name: mm[1], params: '', returnType: mm[2] })
      }
    }

    // Extract response type tables  (| Field | Type | ... )
    const responseTypes = {}
    const tableRe = /####?\s+(\w*Response\w*|Response Fields)[^\n]*\n((?:\|[^\n]+\n)+)/g
    while ((mm = tableRe.exec(section)) !== null) {
      const typeName = mm[1].match(/\w+Response/) ? mm[1].match(/\w+Response/)[0] : className + 'Response'
      const tableRows = mm[2].trim().split('\n').slice(2) // skip header + separator
      const fields = tableRows.map(row => {
        const cells = row.split('|').map(c => c.trim()).filter(Boolean)
        if (cells.length < 2) return null
        const name = cells[0].replace(/`/g, '').replace(/\?/, '')
        const type = cells[1].replace(/`/g, '')
        return { name, type, optional: cells[0].includes('?') }
      }).filter(Boolean)
      if (fields.length > 0) responseTypes[typeName] = fields
    }

    if (methods.length > 0) {
      services.push({ className, importPath, methods, responseTypes })
    }
  }

  return services
}

// ── Markdown generator ────────────────────────────────────────────────────────

function sdkVersionFromPackageLock() {
  try {
    const lockPath = resolve(__dirname, '../templates/dashboard/scaffold/package-lock.json')
    const lock = JSON.parse(readFileSync(lockPath, 'utf8'))
    return lock.packages?.['node_modules/@uipath/uipath-typescript']?.version ?? 'latest'
  } catch {
    return 'latest'
  }
}

function renderFieldTable(fields) {
  if (fields.length === 0) return '_No fields extracted — see SDK source_\n'
  const rows = fields.map(f => `| \`${f.name}${f.optional ? '?' : ''}\` | \`${f.type}\` |`).join('\n')
  return `| Field | Type |\n|-------|------|\n${rows}\n`
}

function renderMethodTable(methods) {
  if (methods.length === 0) return '_No methods extracted_\n'
  const rows = methods.map(m => `| \`${m.name}()\` | \`${m.returnType}\` |`).join('\n')
  return `| Method | Returns |\n|--------|--------|\n${rows}\n`
}

function generateMarkdown(services, sdkVersion, source) {
  const timestamp = new Date().toISOString().slice(0, 10)
  const lines = []

  lines.push(`# SDK Field Reference`)
  lines.push(``)
  lines.push(`> **Auto-generated** ${timestamp} from SDK \`${sdkVersion}\` (source: ${source})`)
  lines.push(`> Do not edit by hand — run \`node assets/scripts/generate-sdk-reference.mjs\` to regenerate.`)
  lines.push(``)
  lines.push(`This file is loaded in the parallel blast (Turn 2) so the agent has accurate SDK`)
  lines.push(`knowledge when writing \`intent.json\`. Field names here are derived from TypeScript`)
  lines.push(`declaration files — they are exact, not approximate.`)
  lines.push(``)
  lines.push(`Fetch latest: \`${SDK_DOCS_URL}\``)
  lines.push(``)
  lines.push(`---`)
  lines.push(``)
  lines.push(`## Import subpaths`)
  lines.push(``)
  lines.push(`\`\`\`typescript`)
  for (const svc of services) {
    lines.push(`import { ${svc.className.padEnd(16)} } from '${svc.importPath}'`)
  }
  lines.push(`\`\`\``)
  lines.push(``)
  lines.push(`Always use constructor injection in T3-SDK fnBody:`)
  lines.push(`\`\`\`typescript`)
  lines.push(`const svc = new Jobs(sdk as never)         // ✓ correct`)
  lines.push(`const r   = await svc.getAll({})`)
  lines.push(`// Never: sdk.jobs.getAll()                // ✗ does not exist`)
  lines.push(`\`\`\``)
  lines.push(``)
  lines.push(`---`)
  lines.push(``)

  for (const svc of services) {
    lines.push(`## ${svc.className} — \`${svc.importPath}\``)
    lines.push(``)
    lines.push(`### Methods`)
    lines.push(``)
    lines.push(renderMethodTable(svc.methods))
    lines.push(``)
    lines.push(`Access items from paginated responses: \`result?.items ?? result?.value ?? []\``)
    lines.push(``)

    if (Object.keys(svc.responseTypes).length > 0) {
      for (const [typeName, fields] of Object.entries(svc.responseTypes)) {
        lines.push(`### \`${typeName}\` response fields`)
        lines.push(``)
        lines.push(renderFieldTable(fields))
        lines.push(``)
      }
    }

    lines.push(`---`)
    lines.push(``)
  }

  // Common patterns section — always appended
  lines.push(`## Common patterns`)
  lines.push(``)
  lines.push(`\`\`\`typescript`)
  lines.push(`// Normalise paginated / non-paginated response`)
  lines.push(`const items = result?.items ?? result?.value ?? []`)
  lines.push(``)
  lines.push(`// Compute duration from Jobs (no direct field)`)
  lines.push(`const durationMs = new Date(j.endTime).getTime() - new Date(j.startTime).getTime()`)
  lines.push(``)
  lines.push(`// SDK service classes require constructor injection`)
  lines.push(`const svc = new Jobs(sdk as never)`)
  lines.push(``)
  lines.push(`// Dynamic import inside T3-SDK fnBody`)
  lines.push(`const { Jobs } = await import('@uipath/uipath-typescript/jobs')`)
  lines.push(`\`\`\``)

  return lines.join('\n') + '\n'
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  let services = []
  let source = ''
  const sdkVersion = sdkVersionFromPackageLock()

  const hasLocalDts = existsSync(SCAFFOLD_SDK)

  if (!FORCE_ONLINE && hasLocalDts) {
    // Primary: parse local .d.ts files — exact types, works offline
    console.log(`Parsing local SDK .d.ts files from ${SCAFFOLD_SDK}`)
    source = `local .d.ts (scaffold/node_modules)`

    for (const svc of SERVICES) {
      const parsed = parseServiceDts(svc.subpath, svc.className, svc.importPath)
      if (parsed) {
        services.push(parsed)
        console.log(`  ✓ ${svc.className}: ${parsed.methods.length} methods, ${Object.keys(parsed.responseTypes).length} response types`)
      } else {
        console.log(`  ✗ ${svc.className}: .d.ts not found at dist/${svc.subpath}/index.d.ts`)
      }
    }
  } else {
    // Fallback: fetch live LLM docs
    if (FORCE_ONLINE) console.log('Forced online mode')
    else console.log('Local .d.ts not found — falling back to live SDK docs')

    source = SDK_DOCS_URL
    services = await fetchOnlineDocs()
    console.log(`  Parsed ${services.length} service classes from online docs`)
  }

  if (services.length === 0) {
    console.error('ERROR: No services parsed — cannot regenerate reference doc')
    process.exit(1)
  }

  const markdown = generateMarkdown(services, sdkVersion, source)

  if (CHECK_MODE) {
    // Verify committed file matches freshly generated output
    if (!existsSync(OUTPUT_PATH)) {
      console.error('ERROR (--check): sdk-field-reference.md does not exist')
      process.exit(1)
    }
    const committed = readFileSync(OUTPUT_PATH, 'utf8')

    // Compare content hashes (ignore the timestamp line)
    const normalize = s => s.replace(/Auto-generated \d{4}-\d{2}-\d{2}/, 'Auto-generated DATE')
    const committedHash = createHash('sha256').update(normalize(committed)).digest('hex')
    const freshHash = createHash('sha256').update(normalize(markdown)).digest('hex')

    if (committedHash !== freshHash) {
      console.error('ERROR (--check): sdk-field-reference.md is stale.')
      console.error('Run: node assets/scripts/generate-sdk-reference.mjs')
      console.error('Then commit the updated file.')
      process.exit(1)
    }
    console.log('✓ sdk-field-reference.md is up to date with SDK', sdkVersion)
    return
  }

  writeFileSync(OUTPUT_PATH, markdown, 'utf8')
  console.log(`\n✓ Generated ${OUTPUT_PATH}`)
  console.log(`  SDK version : ${sdkVersion}`)
  console.log(`  Services    : ${services.length}`)
  console.log(`  Source      : ${source}`)
}

main().catch(e => { console.error(e.message); process.exit(1) })
