#!/usr/bin/env node
// Check a rule's citations against the digitizer's output and write them into the .dmn as uipdm elements.
// Quotes are the agent's; finding them on the page is this script's.
//
// Stop-gap: this script stands in until the attribution CLI resolves citations; the Cite steps then move to it.
//
// Usage: node cite.mjs --dmn <RULES.dmn> --cites <cites.json> --dom <dom.json> [--write]
//
// cites.json:
//   { "rules":    { "<rule id>": [ { "page": 2, "quote": "verbatim words from the page" } ] | { "none": "<why>" } },
//     "inputs":   { "<input name>": { "sourceType": "document" | "system", "meaning": "<what the caller supplies>",
//                                     "values": ["<value the policy names>", ...],
//                                     "cites": [ { "page": 1, "quote": "..." } ] | { "none": "<why>" } } },
//     "outcomes": { "<outcome value>": [ { "page": 1, "quote": "..." } ] | { "none": "<why>" } },
//     "warnings": [ { "text": "<assumption or ambiguity, with its page>", "rule": "<rule id>", "field": "<input name>" } ] }
// A quote with "..." is several fragments of one clause; each fragment must be found and be at least MIN_WORDS words.
// { "none": "<why>" } is for what the document does not state: a catch-all row, a "system" input, an outcome the caller's
// profile adds (out of scope, missing information). It needs a reason.
//
// Checks: every rule, input and outcome value of the .dmn is cited; every cited id exists; every quote is found on its
// page in dom.json, once; every rule row has a unique id. Input and outcome citations are checked only: uipdm has no
// place for their boxes. --write puts into the .dmn:
//   rule/extensionElements        <uipdm:sourceRefs><uipdm:sourceRef page box/></uipdm:sourceRefs>, one per resolved quote
//   inputData/extensionElements   <uipdm:inputVariable sourceType [sourceMapping] [dataType="categorical"]> with
//                                 <uipdm:constraint>s
//   definitions/extensionElements <uipdm:qualityWarning [field]>, one per warning; a warning about one row starts
//                                 "[row <id>]" (uipdm's conditionId names a condition, not a table row)
// replacing any uipdm elements of those kinds already there, then runs check-uipdm.mjs on the result.
// Boxes are "left,top,width,height" in dom.json units. Prints one JSON report. Exit 0 when clean, 1 when anything needs
// fixing, 2 on a usage error.
import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { domPages, resolveQuote, fragments, tokens } from './quotes.mjs'

const args = process.argv.slice(2)
const flag = n => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : undefined }
const usage = m => { console.log(JSON.stringify({ status: 'error', error: m })); process.exit(2) }
const dmnPath = flag('--dmn'), citesPath = flag('--cites'), domPath = flag('--dom')
if (!dmnPath || !citesPath || !domPath) usage('usage: cite.mjs --dmn <RULES.dmn> --cites <cites.json> --dom <dom.json> [--write]. Citations need the digitizer output (dom.json); without it, do not cite.')

let dmn, cites, pages
try {
  dmn = readFileSync(dmnPath, 'utf8')
  cites = JSON.parse(readFileSync(citesPath, 'utf8'))
  pages = domPages(JSON.parse(readFileSync(domPath, 'utf8')))
} catch (e) { usage(`cannot read input: ${e.message}`) }
if (!cites || typeof cites !== 'object' || Array.isArray(cites)) usage('cites.json must be an object with "rules", "inputs", "outcomes", "warnings"')
if (!/<(?:\w+:)?definitions\b/.test(dmn)) usage('the .dmn has no <definitions> element')
const MIN_WORDS = 2

// ---- what the .dmn declares --------------------------------------------------------------------------------------
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
const unesc = s => s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, '&')
const attr = (attrs, name) => { const m = new RegExp(`\\b${name}="([^"]*)"`).exec(attrs); return m ? m[1] : undefined }
// An element written <x .../> or <x ...>body</x>; the self-closing form must not swallow the next element.
const elements = tag => [...dmn.matchAll(new RegExp(`<((?:\\w+:)?${tag})\\b([^>]*?)(?:/>|>([\\s\\S]*?)</\\1>)`, 'g'))]
const startProblems = []
const ruleIds = []
for (const m of elements('rule')) {
  const id = attr(m[2], 'id')
  if (!id) startProblems.push({ kind: 'rules', problem: 'a rule row has no id; give every <rule> a unique id' })
  else if (ruleIds.includes(id)) startProblems.push({ kind: 'rules', id, problem: 'two rule rows share this id' })
  else ruleIds.push(id)
}
const inputTypes = {}
for (const m of elements('inputData')) {
  const name = attr(m[2], 'name')
  if (name !== undefined) inputTypes[unesc(name)] = (/<(?:\w+:)?variable\b[^>]*\btypeRef="([^"]+)"/.exec(m[3] ?? '') ?? [])[1]
}
const inputNames = Object.keys(inputTypes)
const outcomeValues = new Set()
for (const m of dmn.matchAll(/<(?:\w+:)?outputEntry\b[^>]*>\s*<(?:\w+:)?text>([\s\S]*?)<\/(?:\w+:)?text>/g)) {
  // Every string literal an output entry can return: a plain "value", or the branches of an if/then/else expression.
  for (const s of unesc(m[1]).trim().matchAll(/(?:^|\bthen\b|\belse\b)\s*"((?:[^"\\]|\\.)*)"/g)) outcomeValues.add(s[1])
}
const pagesWithText = new Set(pages.filter(p => p.words.length).map(p => p.page))

// ---- resolve every citation ----------------------------------------------------------------------------------------
const report = { status: 'ok', boxUnits: 'dom', coverage: {}, problems: [...startProblems], resolved: 0, unresolved: 0, ambiguous: 0 }
const refsByRule = {}
const isNone = v => v && !Array.isArray(v) && typeof v === 'object' && 'none' in v

function resolveList(kind, id, list, noneAllowed) {
  if (isNone(list)) {
    if (!noneAllowed) report.problems.push({ kind, id, problem: '"none" is only for a "system" input' })
    else if (!String(list.none || '').trim()) report.problems.push({ kind, id, problem: '"none" needs a reason' })
    return
  }
  if (!Array.isArray(list) || list.length === 0) { report.problems.push({ kind, id, problem: 'no citation' }); return }
  for (const c of list) {
    if (!c || typeof c !== 'object') { report.problems.push({ kind, id, problem: 'each citation is { "page", "quote" }' }); continue }
    const page = Number(c.page)
    if (!Number.isInteger(page) || page < 1) { report.problems.push({ kind, id, quote: c.quote, problem: 'missing or bad page' }); continue }
    if (!pagesWithText.has(page)) { report.problems.push({ kind, id, page, problem: `dom.json has no words on page ${page}` }); continue }
    const parts = fragments(c.quote ?? '')
    if (parts.length === 0) { report.problems.push({ kind, id, page, problem: 'empty quote' }); continue }
    for (const part of parts) {
      if (tokens(part).length < MIN_WORDS) { report.problems.push({ kind, id, page, quote: part, problem: `quote at least ${MIN_WORDS} words` }); continue }
      const r = resolveQuote(pages, page, part)
      if (r.status === 'resolved' && r.page !== page) r.status = 'unresolved'
      if (r.status === 'resolved') {
        report.resolved++
        if (kind === 'rules') (refsByRule[id] ??= []).push({ page: r.page, box: r.box })
      } else {
        report[r.status === 'ambiguous' ? 'ambiguous' : 'unresolved']++
        const elsewhere = r.status === 'unresolved' ? resolveQuote(pages, 0, part) : null
        report.problems.push({ kind, id, page, quote: part, problem: r.reason,
          ...(elsewhere && elsewhere.status !== 'unresolved' ? { foundOnPage: elsewhere.page ?? elsewhere.candidates?.map(c => c.page) } : {}),
          ...(r.candidates ? { candidates: r.candidates } : {}) })
      }
    }
  }
}

const declared = { rules: ruleIds, inputs: inputNames, outcomes: [...outcomeValues] }
for (const [kind, ids] of Object.entries(declared)) {
  const given = cites[kind] ?? {}
  for (const id of Object.keys(given)) if (!ids.includes(id)) report.problems.push({ kind, id, problem: `not a ${kind.slice(0, -1)} in the .dmn` })
  let cited = 0
  for (const id of ids) {
    if (!(id in given)) { report.problems.push({ kind, id, problem: 'not cited' }); continue }
    cited++
    if (kind === 'inputs') {
      const inp = given[id]
      if (!inp || Array.isArray(inp) || typeof inp !== 'object') { report.problems.push({ kind, id, problem: 'needs { "sourceType", "cites", ... }' }); continue }
      if (!['document', 'system'].includes(inp.sourceType)) report.problems.push({ kind, id, problem: 'sourceType must be "document" or "system"' })
      if (inp.values !== undefined && !(Array.isArray(inp.values) && inp.values.every(v => typeof v === 'string' || typeof v === 'number')))
        report.problems.push({ kind, id, problem: '"values" must be a list of strings or numbers' })
      resolveList(kind, id, inp.cites, inp.sourceType === 'system')
    } else resolveList(kind, id, given[id], true)
  }
  report.coverage[kind] = `${cited}/${ids.length}`
}
const warnings = Array.isArray(cites.warnings) ? cites.warnings : []
if (cites.warnings !== undefined && !Array.isArray(cites.warnings)) report.problems.push({ kind: 'warnings', problem: '"warnings" must be a list' })
warnings.forEach((w, i) => {
  if (!String(w?.text ?? '').trim()) report.problems.push({ kind: 'warnings', id: i, problem: 'a warning needs "text"' })
  if (w?.rule && !ruleIds.includes(w.rule)) report.problems.push({ kind: 'warnings', id: i, problem: `"rule" ${w.rule} is not a rule in the .dmn` })
  if (w?.field && !inputNames.includes(w.field)) report.problems.push({ kind: 'warnings', id: i, problem: `"field" ${w.field} is not an input in the .dmn` })
})
report.warnings = warnings.length

// ---- write the uipdm elements into the .dmn -----------------------------------------------------------------------
// Each writer drops the uipdm elements of its own kind first, so running --write again replaces rather than adds.
const dropEmptyExt = body => body.replace(/\s*<((?:\w+:)?extensionElements)>\s*<\/\1>/g, '')
// <extensionElements/> becomes an open/close pair, so a block goes inside it rather than next to it.
const openExt = body => body.replace(/<((?:\w+:)?extensionElements)\s*\/>/g, '<$1></$1>')
const indentOf = (body, fallback) => (/\n([ \t]*)</.exec(body) ?? [, fallback])[1]

// Put `block` inside the element's extensionElements, creating it where DMN wants it: after <description>, else just
// before the element's first `before` child.
// Only the element's own children count: an extensionElements or description inside a child (an inputEntry) is not its.
// Text is spliced by index, never through String.replace, so "$" in a value is written as it is.
function putExt(open, body, close, block, indent, before) {
  const first = new RegExp('\\s*' + before.source).exec(body)
  const limit = first ? first.index : body.length
  const ext = /<((?:\w+:)?extensionElements)>/.exec(body)
  if (ext && ext.index < limit) {
    const at = ext.index + ext[0].length
    return open + body.slice(0, at) + `\n${block}` + body.slice(at) + close
  }
  const prefix = (/^<(\w+:)/.exec(open) ?? [])[1] ?? ''
  const extEl = `\n${indent}<${prefix}extensionElements>\n${block}\n${indent}</${prefix}extensionElements>`
  const desc = /<\/(?:\w+:)?description>/.exec(body)
  const at = desc && desc.index < limit ? desc.index + desc[0].length : limit
  return open + body.slice(0, at) + extEl + body.slice(at) + close
}

if (args.includes('--write')) {
  const NS = 'http://uipath.com/schema/1.0/dmn-ext/decision-model'
  let out = dmn
  if (!/xmlns:uipdm=/.test(out)) out = out.replace(/<((?:\w+:)?definitions)\b/, `<$1 xmlns:uipdm="${NS}"`)

  // rule rows: sourceRefs
  out = out.replace(/(<((?:\w+:)?rule)\b[^>]*?\bid="([^"]+)"[^>]*?(?<!\/)>)([\s\S]*?)(<\/\2>)/g, (whole, open, tag, id, body, close) => {
    body = dropEmptyExt(openExt(body).replace(/\s*<uipdm:sourceRefs>[\s\S]*?<\/uipdm:sourceRefs>/g, ''))
    const seen = new Set()
    const refs = (refsByRule[id] ?? []).filter(r => { const k = `${r.page}|${r.box}`; return !seen.has(k) && seen.add(k) })
    if (!refs.length) return open + body + close
    const indent = indentOf(body, '        ')
    const block = `${indent}  <uipdm:sourceRefs>\n` + refs.map(r => `${indent}    <uipdm:sourceRef page="${r.page}" box="${r.box}" />`).join('\n') + `\n${indent}  </uipdm:sourceRefs>`
    return putExt(open, body, close, block, indent, /<(?:\w+:)?inputEntry\b/)
  })

  // inputs: inputVariable
  let writtenInputs = 0
  out = out.replace(/(<((?:\w+:)?inputData)\b[^>]*?\bname="([^"]+)"[^>]*?(?<!\/)>)([\s\S]*?)(<\/\2>)/g, (whole, open, tag, name, body, close) => {
    body = dropEmptyExt(openExt(body).replace(/\s*<uipdm:inputVariable\b[^>]*\/>/g, '').replace(/\s*<uipdm:inputVariable\b[^>]*[^/]>[\s\S]*?<\/uipdm:inputVariable>/g, ''))
    const inp = (cites.inputs ?? {})[unesc(name)]
    if (!inp || typeof inp !== 'object' || Array.isArray(inp) || !['document', 'system'].includes(inp.sourceType)) return open + body + close
    const values = Array.isArray(inp.values) ? inp.values.map(String) : []
    const type = inputTypes[unesc(name)]
    // dataType only where typeRef cannot say it (uipdm.xsd): a string with named values is categorical.
    const dataType = values.length && type === 'string' ? 'categorical' : undefined
    const attrs = ` sourceType="${inp.sourceType}"` + (inp.meaning ? ` sourceMapping="${esc(inp.meaning)}"` : '') + (dataType ? ` dataType="${dataType}"` : '')
    const indent = indentOf(body, '    ')
    const block = values.length
      ? `${indent}  <uipdm:inputVariable${attrs}>\n` + values.map(v => `${indent}    <uipdm:constraint>${esc(v)}</uipdm:constraint>`).join('\n') + `\n${indent}  </uipdm:inputVariable>`
      : `${indent}  <uipdm:inputVariable${attrs} />`
    writtenInputs++
    return putExt(open, body, close, block, indent, /<(?:\w+:)?variable\b/)
  })

  // definitions: qualityWarnings, in the definitions' own extensionElements (after an optional <description>; the
  // scaffold's already holds <uipath:authoring>). Comments and the description before it are skipped, not matched.
  out = out.replace(/\s*<uipdm:qualityWarning\b[^>]*>[\s\S]*?<\/uipdm:qualityWarning>/g, '')
  const defs = /<((?:\w+:)?definitions)\b[^>]*>/.exec(out)
  const p = (/^(\w+:)/.exec(defs[1]) ?? [])[1] ?? ''
  const afterDefs = defs.index + defs[0].length
  let rest = out.slice(afterDefs)
  const lead = new RegExp(`^(?:\\s+|<!--[\\s\\S]*?-->|<${p}description\\b[^>]*>[\\s\\S]*?</${p}description>)*`).exec(rest)[0]
  const after = rest.slice(lead.length).replace(new RegExp(`^<${p}extensionElements\\s*/>`), `<${p}extensionElements></${p}extensionElements>`)
  rest = lead + after
  const own = new RegExp(`^<${p}extensionElements>([\\s\\S]*?)</${p}extensionElements>`).exec(after)
  const lines = warnings.map(w => `\n    <uipdm:qualityWarning${w.field ? ` field="${esc(w.field)}"` : ''}>${esc((w.rule ? `[row ${w.rule}] ` : '') + w.text)}</uipdm:qualityWarning>`).join('')
  const kept = own && own[1].trim() ? own[1] : ''
  const block = kept ? `<${p}extensionElements>${lines}${kept}</${p}extensionElements>`
    : lines ? `<${p}extensionElements>${lines}\n  </${p}extensionElements>` : ''
  const trimmed = lead.replace(/\s+$/, '')
  if (own) rest = (block ? lead : trimmed) + block + after.slice(own[0].length)
  else if (block) rest = trimmed + `\n  ${block}` + rest.slice(trimmed.length)
  out = out.slice(0, afterDefs) + rest

  writeFileSync(dmnPath, out)
  report.written = { rules: Object.keys(refsByRule).length, inputs: writtenInputs, warnings: warnings.length }

  // the uipdm schema check (uip rules validate does not read uipdm elements)
  const checker = join(dirname(fileURLToPath(import.meta.url)), 'check-uipdm.mjs')
  if (existsSync(checker)) {
    try {
      report.uipdmCheck = execFileSync(process.execPath, [checker, dmnPath], { encoding: 'utf8' }).trim()
    } catch (e) {
      report.uipdmCheck = String(e.stdout || e.message).trim()
      report.problems.push({ kind: 'uipdm', problem: `check-uipdm.mjs failed: ${report.uipdmCheck.slice(0, 500)}` })
    }
  } else report.problems.push({ kind: 'uipdm', problem: 'check-uipdm.mjs not found next to cite.mjs' })
}

if (report.problems.length) report.status = 'needs-fixes'
console.log(JSON.stringify(report, null, 1))
process.exit(report.problems.length ? 1 : 0)
