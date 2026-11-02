import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import { spawnSync } from 'node:child_process'
import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const SCRIPT = resolve(here, '../../skills/uipath-coded-apps/scripts/validate-action-schema.js')
const require = createRequire(import.meta.url)
const { validateActionSchema, SUPPORTED_TYPES, SUPPORTED_FORMATS } = require(SCRIPT)

const empty = () => ({ type: 'object', properties: {} })
const schema = (over = {}) => ({ inputs: empty(), outputs: empty(), inOuts: empty(), outcomes: empty(), ...over })

function run(args, input) {
  return spawnSync(process.execPath, [SCRIPT, ...args], { encoding: 'utf8', input })
}
function runFile(content) {
  const file = join(mkdtempSync(join(tmpdir(), 'action-schema-')), 'action-schema.json')
  writeFileSync(file, typeof content === 'string' ? content : JSON.stringify(content))
  return run([file])
}

// ── validateActionSchema (exported) ─────────────────────────────────────────

test('exports the supported type and format tables', () => {
  assert.ok(SUPPORTED_TYPES.includes('ContentValidationData'))
  assert.deepEqual(SUPPORTED_FORMATS, ['uuid', 'date'])
})

test('a schema with four empty sections is valid', () => {
  assert.deepEqual([...validateActionSchema(schema())], [])
})

test('a non-object root is rejected', () => {
  for (const bad of [null, [], 'x', 3]) {
    assert.deepEqual([...validateActionSchema(bad)], ['  - root: action-schema must be a JSON object'])
  }
})

test('every missing section is reported by name', () => {
  assert.deepEqual([...validateActionSchema({})], [
    '  - inputs: missing required section',
    '  - outputs: missing required section',
    '  - inOuts: missing required section',
    '  - outcomes: missing required section',
  ])
})

test('a section must be an object with type "object" and a properties object', () => {
  const errors = [...validateActionSchema(schema({
    inputs: 'nope',
    outputs: { type: 'array', properties: {} },
    inOuts: { type: 'object' },
    outcomes: { type: 'object', properties: [] },
  }))]
  assert.deepEqual(errors, [
    '  - inputs: section must be an object',
    '  - outputs.type: section "type" must be the literal "object"',
    "  - inOuts.properties: section must have a 'properties' object (use {} when empty)",
    "  - outcomes.properties: section 'properties' must be an object",
  ])
})

test('all supported types and the uuid/date formats on strings are accepted', () => {
  const properties = {}
  for (const t of SUPPORTED_TYPES) {
    properties[`f_${t}`] = t === 'array' ? { type: 'array', items: { type: 'string' } } : { type: t }
  }
  properties.id = { type: 'string', format: 'uuid', required: true, description: 'an id' }
  properties.day = { type: 'string', format: 'date' }
  properties.noFormat = { type: 'string', format: null }
  assert.deepEqual([...validateActionSchema(schema({ inputs: { type: 'object', properties } }))], [])
})

test('property-level problems are reported with their dotted path', () => {
  const errors = [...validateActionSchema(schema({
    inputs: {
      type: 'object',
      properties: {
        notObject: 'string',
        badType: { type: 'date' },
        badRequired: { type: 'string', required: 'yes' },
        badDescription: { type: 'string', description: 5 },
        unknownFormat: { type: 'string', format: 'email' },
        formatOnNumber: { type: 'number', format: 'uuid' },
      },
    },
  }))]
  assert.deepEqual(errors, [
    '  - inputs.properties.notObject: property must be an object',
    `  - inputs.properties.badType.type: type must be one of: ${SUPPORTED_TYPES.join(', ')} (got "date")`,
    '  - inputs.properties.badRequired.required: required must be a boolean',
    '  - inputs.properties.badDescription.description: description must be a string',
    `  - inputs.properties.unknownFormat.format: format must be one of: ${SUPPORTED_FORMATS.join(', ')} (got "email")`,
    "  - inputs.properties.formatOnNumber.format: 'uuid' format is only allowed on type string (type is 'number')",
  ])
})

test('arrays need items and cannot nest arrays', () => {
  const errors = [...validateActionSchema(schema({
    outputs: {
      type: 'object',
      properties: {
        noItems: { type: 'array' },
        nested: { type: 'array', items: { type: 'array', items: { type: 'string' } } },
        ok: { type: 'array', items: { type: 'object', properties: { a: { type: 'integer' } } } },
      },
    },
  }))]
  assert.deepEqual(errors, [
    "  - outputs.properties.noItems.items: array type requires an 'items' definition",
    "  - outputs.properties.nested.items.type: nested arrays are not supported (an array's items.type cannot be 'array')",
  ])
})

test('nested object properties are validated recursively', () => {
  const errors = [...validateActionSchema(schema({
    inOuts: {
      type: 'object',
      properties: {
        wrapper: { type: 'object', properties: { deep: { type: 'bogus' } } },
        badProps: { type: 'object', properties: [] },
      },
    },
  }))]
  assert.equal(errors.length, 2)
  assert.match(errors[0], /^ {2}- inOuts\.properties\.wrapper\.properties\.deep\.type: type must be one of/)
  assert.equal(errors[1], '  - inOuts.properties.badProps.properties: properties must be an object')
})

// ── CLI ─────────────────────────────────────────────────────────────────────

test('CLI: a valid file exits 0 and says so', () => {
  const r = runFile(schema())
  assert.equal(r.status, 0)
  assert.equal(r.stdout, 'action-schema.json is valid.\n')
  assert.equal(r.stderr, '')
})

test('CLI: an invalid file exits 1 with one path: message line per error on stderr', () => {
  const r = runFile(schema({ inputs: { type: 'object', properties: { x: { type: 'nope' } } } }))
  assert.equal(r.status, 1)
  assert.match(r.stderr, /^Invalid action-schema\.json:\n {2}- inputs\.properties\.x\.type: /)
  assert.equal(r.stdout, '')
})

test('CLI: "-" reads the schema from stdin', () => {
  const ok = run(['-'], JSON.stringify(schema()))
  assert.equal(ok.status, 0)
  const bad = run(['-'], JSON.stringify({}))
  assert.equal(bad.status, 1)
  assert.match(bad.stderr, /inputs: missing required section/)
})

test('CLI: malformed JSON exits 2', () => {
  const r = runFile('{ not json')
  assert.equal(r.status, 2)
  assert.match(r.stderr, /^invalid JSON: /)
})

test('CLI: an unreadable path exits 2 and names the path', () => {
  const missing = join(tmpdir(), 'definitely-missing-action-schema.json')
  const r = run([missing])
  assert.equal(r.status, 2)
  assert.ok(r.stderr.startsWith(`cannot read ${missing}: `))
})

test('CLI: no arguments or too many arguments is a usage error (exit 2)', () => {
  for (const args of [[], ['a.json', 'b.json']]) {
    const r = run(args)
    assert.equal(r.status, 2)
    assert.equal(r.stderr, 'usage: validate-action-schema.js <action-schema.json | ->\n')
  }
})

test('CLI: --show-types lists every type with its System mapping and the formats', () => {
  const r = run(['--show-types'])
  assert.equal(r.status, 0)
  assert.match(r.stdout, /^Supported field types:\n/)
  assert.match(r.stdout, /integer {2}-> System\.Int64/)
  assert.match(r.stdout, /array {4}-> \(collection of items type\)/)
  for (const t of SUPPORTED_TYPES) assert.ok(r.stdout.includes(t), `${t} listed`)
  assert.match(r.stdout, /Supported formats \(string only\): uuid, date\n$/)
})
