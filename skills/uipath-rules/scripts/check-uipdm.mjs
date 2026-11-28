#!/usr/bin/env node
// Checks every uipdm element of a .dmn against uipdm.xsd. `uip rules validate` does not read them.
// Usage: node check-uipdm.mjs <DMN_FILE> [<XSD_FILE>]
// Without <XSD_FILE> it reads uipdm.xsd from the script's own folder (or ../references/).
// Exit 0: all elements valid (or none present). Exit 1: at least one invalid element.
// Exit 2: usage error, unreadable file, or a schema construct this checker does not implement.
// It needs only file access: no xmllint, no Python, no network. It reads the schema at run time, so a
// changed uipdm.xsd changes what is accepted. It implements the part of XML Schema that uipdm.xsd uses
// (named types, sequences, attributes, enumerations, patterns, simple content) and stops with exit 2
// on anything else, so an unsupported schema can never pass silently.
import { readFileSync } from 'node:fs'

const UIPDM = 'http://uipath.com/schema/1.0/dmn-ext/decision-model'
const XS = 'http://www.w3.org/2001/XMLSchema'

class Stop extends Error {}
const stop = message => {
  throw new Stop(message)
}

// ---- A small XML reader: elements, attributes, text, namespaces ---------------------------------

const ENTITIES = { lt: '<', gt: '>', amp: '&', quot: '"', apos: "'" }
const decode = text =>
  text.replace(/&(#x[0-9a-fA-F]+|#\d+|\w+);/g, (whole, name) => {
    if (name[0] === '#') return String.fromCodePoint(name[1] === 'x' ? parseInt(name.slice(2), 16) : parseInt(name.slice(1), 10))
    return name in ENTITIES ? ENTITIES[name] : whole
  })

function parseXml(text, label) {
  const root = { children: [], ns: { xml: 'http://www.w3.org/XML/1998/namespace' }, text: '' }
  const stack = [root]
  let i = 0
  const bad = what => stop(`${label} is not well-formed XML: ${what}`)
  while (i < text.length) {
    const lt = text.indexOf('<', i)
    const top = stack[stack.length - 1]
    if (lt < 0) {
      top.text += decode(text.slice(i))
      break
    }
    top.text += decode(text.slice(i, lt))
    if (text.startsWith('<!--', lt)) {
      const end = text.indexOf('-->', lt + 4)
      if (end < 0) bad('an unclosed comment')
      i = end + 3
    } else if (text.startsWith('<![CDATA[', lt)) {
      const end = text.indexOf(']]>', lt + 9)
      if (end < 0) bad('an unclosed CDATA section')
      top.text += text.slice(lt + 9, end)
      i = end + 3
    } else if (text.startsWith('<?', lt)) {
      const end = text.indexOf('?>', lt + 2)
      if (end < 0) bad('an unclosed processing instruction')
      i = end + 2
    } else if (text.startsWith('<!', lt)) {
      const end = text.indexOf('>', lt + 2)
      if (end < 0) bad('an unclosed declaration')
      i = end + 1
    } else if (text[lt + 1] === '/') {
      const end = text.indexOf('>', lt + 2)
      if (end < 0) bad('an unclosed end tag')
      const name = text.slice(lt + 2, end).trim()
      if (stack.length < 2 || top.qname !== name) bad(`</${name}> does not close <${top.qname || '?'}>`)
      stack.pop()
      i = end + 1
    } else {
      // A start tag: find its end outside quoted attribute values.
      let j = lt + 1
      let quote = ''
      while (j < text.length && (quote || text[j] !== '>')) {
        if (quote) {
          if (text[j] === quote) quote = ''
        } else if (text[j] === '"' || text[j] === "'") quote = text[j]
        j++
      }
      if (j >= text.length) bad('an unclosed start tag')
      let body = text.slice(lt + 1, j)
      const selfClosing = body.endsWith('/')
      if (selfClosing) body = body.slice(0, -1)
      const nameMatch = /^([^\s/>]+)/.exec(body)
      if (!nameMatch) bad('a tag with no name')
      const qname = nameMatch[1]
      const raw = []
      const attr = /([^\s=]+)\s*=\s*("([^"]*)"|'([^']*)')/g
      const rest = body.slice(qname.length)
      let m
      while ((m = attr.exec(rest))) raw.push([m[1], decode(m[3] !== undefined ? m[3] : m[4])])
      if (rest.replace(attr, '').trim()) bad(`a malformed attribute in <${qname}>`)
      const ns = Object.assign({}, top.ns)
      for (const [name, value] of raw) {
        if (name === 'xmlns') ns[''] = value
        else if (name.startsWith('xmlns:')) ns[name.slice(6)] = value
      }
      const split = name => (name.includes(':') ? [name.slice(0, name.indexOf(':')), name.slice(name.indexOf(':') + 1)] : ['', name])
      const [prefix, local] = split(qname)
      if (prefix && !(prefix in ns)) bad(`the prefix ${prefix} is not declared`)
      const attrs = []
      for (const [name, value] of raw) {
        if (name === 'xmlns' || name.startsWith('xmlns:')) continue
        const [p, l] = split(name)
        if (p && !(p in ns)) bad(`the prefix ${p} is not declared`)
        attrs.push({ name: l, uri: p ? ns[p] : '', value })
      }
      const node = { qname, local, uri: prefix ? ns[prefix] : ns[''] || '', attrs, children: [], ns, text: '', parent: top }
      top.children.push(node)
      if (!selfClosing) stack.push(node)
      i = j + 1
    }
  }
  if (stack.length !== 1) bad(`<${stack[stack.length - 1].qname}> is never closed`)
  if (root.children.length !== 1) bad('it needs exactly one root element')
  return root.children[0]
}

const attrOf = (node, name) => {
  const found = node.attrs.find(a => a.name === name && !a.uri)
  return found ? found.value : undefined
}
const xsChildren = (node, local) => node.children.filter(c => c.uri === XS && c.local === local)

// ---- The schema, reduced to what the checker needs ----------------------------------------------

const UNSUPPORTED = ['choice', 'all', 'any', 'anyAttribute', 'group', 'attributeGroup', 'union', 'list', 'complexContent',
  'import', 'include', 'redefine', 'key', 'keyref', 'unique']
const FACETS = ['enumeration', 'pattern']

function loadSchema(text) {
  const root = parseXml(text, 'the schema')
  if (root.uri !== XS || root.local !== 'schema') stop('the schema file is not an XML Schema document')
  const walk = node => {
    if (node.uri === XS && UNSUPPORTED.includes(node.local)) stop(`the schema uses xsd:${node.local}, which this checker does not implement`)
    node.children.forEach(walk)
  }
  walk(root)
  const typeRef = (node, value) => {
    const prefix = value.includes(':') ? value.slice(0, value.indexOf(':')) : ''
    const local = value.includes(':') ? value.slice(value.indexOf(':') + 1) : value
    return { builtin: node.ns[prefix] === XS, name: local }
  }
  const schema = { elements: {}, complex: {}, simple: {} }
  const readAttributes = owner => {
    const attrs = {}
    for (const a of xsChildren(owner, 'attribute')) {
      const name = attrOf(a, 'name')
      const type = attrOf(a, 'type')
      if (!name || !type) stop('the schema has an attribute without a name or a type')
      attrs[name] = { type: typeRef(a, type), required: attrOf(a, 'use') === 'required' }
    }
    return attrs
  }
  for (const node of root.children) {
    if (node.uri !== XS) continue
    const name = attrOf(node, 'name')
    if (node.local === 'element') {
      const type = attrOf(node, 'type')
      if (!name || !type) stop('the schema has a top-level element without a name or a type')
      schema.elements[name] = typeRef(node, type)
    } else if (node.local === 'complexType') {
      if (!name) stop('the schema has an unnamed complex type')
      const simpleContent = xsChildren(node, 'simpleContent')[0]
      if (simpleContent) {
        const extension = xsChildren(simpleContent, 'extension')[0]
        if (!extension || !attrOf(extension, 'base')) stop(`the schema type ${name} has simple content this checker does not implement`)
        schema.complex[name] = { text: typeRef(extension, attrOf(extension, 'base')), particles: [], attrs: readAttributes(extension) }
      } else {
        const sequence = xsChildren(node, 'sequence')[0]
        const particles = []
        for (const e of sequence ? xsChildren(sequence, 'element') : []) {
          const type = attrOf(e, 'type')
          if (!attrOf(e, 'name') || !type) stop(`the schema type ${name} has a child element without a name or a type`)
          const max = attrOf(e, 'maxOccurs')
          particles.push({ name: attrOf(e, 'name'), type: typeRef(e, type), min: Number(attrOf(e, 'minOccurs') ?? 1),
            max: max === 'unbounded' ? Infinity : Number(max ?? 1) })
        }
        schema.complex[name] = { text: null, particles, attrs: readAttributes(node) }
      }
    } else if (node.local === 'simpleType') {
      if (!name) stop('the schema has an unnamed simple type')
      const restriction = xsChildren(node, 'restriction')[0]
      if (!restriction || !attrOf(restriction, 'base')) stop(`the schema type ${name} is not a restriction`)
      for (const facet of restriction.children) {
        if (facet.uri === XS && !FACETS.includes(facet.local)) stop(`the schema type ${name} uses the facet ${facet.local}, which this checker does not implement`)
      }
      schema.simple[name] = {
        base: typeRef(restriction, attrOf(restriction, 'base')),
        enums: xsChildren(restriction, 'enumeration').map(e => attrOf(e, 'value')),
        patterns: xsChildren(restriction, 'pattern').map(p => new RegExp(`^(?:${attrOf(p, 'value')})$`)),
      }
    }
  }
  return schema
}

// ---- Validation ---------------------------------------------------------------------------------

const BUILTIN = {
  string: () => true,
  normalizedString: () => true,
  token: () => true,
  anyURI: () => true,
  integer: v => /^[+-]?\d+$/.test(v),
  nonNegativeInteger: v => /^\+?\d+$/.test(v) || /^-0+$/.test(v),
  positiveInteger: v => /^\+?\d+$/.test(v) && !/^\+?0+$/.test(v),
  decimal: v => /^[+-]?(\d+(\.\d*)?|\.\d+)$/.test(v),
  boolean: v => ['true', 'false', '1', '0'].includes(v),
}
const KEEPS_WHITESPACE = ['string']

// The reason `value` is not a valid `type`, or '' when it is.
function valueProblem(schema, type, value) {
  if (type.builtin) {
    const check = BUILTIN[type.name]
    if (!check) stop(`the schema uses the type xsd:${type.name}, which this checker does not implement`)
    const text = KEEPS_WHITESPACE.includes(type.name) ? value : value.trim()
    return check(text) ? '' : `'${value}' is not a valid xsd:${type.name}`
  }
  const simple = schema.simple[type.name]
  if (!simple) stop(`the schema names the type ${type.name}, which it does not define as a simple type`)
  const base = valueProblem(schema, simple.base, value)
  if (base) return base
  if (simple.enums.length && !simple.enums.includes(value)) return `'${value}' is not one of ${simple.enums.join(', ')}`
  if (simple.patterns.length && !simple.patterns.some(p => p.test(value))) return `'${value}' does not match the pattern of ${type.name}`
  return ''
}

function elementProblems(schema, node, type, problems) {
  const name = node.local
  const complex = !type.builtin && schema.complex[type.name]
  if (!complex) {
    if (node.attrs.length) problems.push(`${name}: attributes are not allowed`)
    if (node.children.length) problems.push(`${name}: child elements are not allowed`)
    const problem = valueProblem(schema, type, node.text)
    if (problem) problems.push(`${name}: ${problem}`)
    return
  }
  for (const attr of node.attrs) {
    const declared = !attr.uri && complex.attrs[attr.name]
    if (!declared) problems.push(`${name}: the attribute '${attr.name}' is not allowed`)
    else {
      const problem = valueProblem(schema, declared.type, attr.value)
      if (problem) problems.push(`${name}: attribute '${attr.name}': ${problem}`)
    }
  }
  for (const [attrName, declared] of Object.entries(complex.attrs)) {
    if (declared.required && attrOf(node, attrName) === undefined) problems.push(`${name}: the attribute '${attrName}' is required`)
  }
  if (complex.text) {
    if (node.children.length) problems.push(`${name}: child elements are not allowed`)
    const problem = valueProblem(schema, complex.text, node.text)
    if (problem) problems.push(`${name}: ${problem}`)
    return
  }
  if (node.text.trim()) problems.push(`${name}: text is not allowed here`)
  let at = 0
  for (const particle of complex.particles) {
    let count = 0
    while (at < node.children.length && node.children[at].uri === UIPDM && node.children[at].local === particle.name && count < particle.max) {
      elementProblems(schema, node.children[at], particle.type, problems)
      at++
      count++
    }
    if (count < particle.min) problems.push(`${name}: needs ${particle.min === 1 ? 'a' : `at least ${particle.min}`} '${particle.name}' child here`)
  }
  if (at < node.children.length) problems.push(`${name}: the child element '${node.children[at].local}' is not allowed here`)
}

// ---- Main ---------------------------------------------------------------------------------------

function read(path) {
  try {
    return readFileSync(path, 'utf8')
  } catch {
    return undefined
  }
}

function main(argv) {
  if (argv.length < 1 || argv.length > 2) stop('usage: node check-uipdm.mjs <DMN_FILE> [<XSD_FILE>]')
  const dmnText = read(argv[0])
  if (dmnText === undefined) stop(`cannot read ${argv[0]}`)
  const here = String(process.argv[1] || '').replace(/[^/\\]*$/, '')
  const candidates = argv[1] ? [argv[1]] : [`${here}uipdm.xsd`, `${here}../references/uipdm.xsd`]
  let xsdText
  for (const candidate of candidates) {
    xsdText = read(candidate)
    if (xsdText !== undefined) break
  }
  if (xsdText === undefined) stop(`cannot read uipdm.xsd (looked in ${candidates.join(', ')}); pass its path as the second argument`)
  const schema = loadSchema(xsdText)
  const root = parseXml(dmnText, argv[0])
  let checked = 0
  let invalid = 0
  const visit = node => {
    if (node.uri === UIPDM) {
      // A uipdm element whose parent is not uipdm is checked whole; its children are checked through it.
      checked++
      const problems = []
      const declared = schema.elements[node.local]
      if (!declared) problems.push(`${node.local}: the schema declares no such element`)
      else elementProblems(schema, node, declared, problems)
      if (problems.length) {
        invalid++
        console.log(problems.join('; '))
      }
      return
    }
    node.children.forEach(visit)
  }
  visit(root)
  console.log(`${checked} uipdm elements checked, ${invalid} invalid`)
  return invalid ? 1 : 0
}

try {
  process.exit(main(process.argv.slice(2)))
} catch (err) {
  if (!(err instanceof Stop)) throw err
  console.log(`error: ${err.message}`)
  process.exit(2)
}
