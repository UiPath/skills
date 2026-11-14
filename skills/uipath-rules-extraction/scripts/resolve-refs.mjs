#!/usr/bin/env node
// Resolves verbatim quotes to page boxes in a digitizer dom.json.
// Usage: node resolve-refs.mjs --dom <DOM_JSON> --cites <CITES_JSON>
// <CITES_JSON>: [{ "id": "r1", "page": 1, "quote": "Employees with less than six months" }]
// Prints one JSON object on stdout. Exit 0 even when a quote is unresolved; exit 2 on a usage error.
import { readFileSync } from 'node:fs'

const args = process.argv.slice(2)
const flag = name => {
  const i = args.indexOf(name)
  return i >= 0 ? args[i + 1] : undefined
}
const fail = message => {
  console.log(JSON.stringify({ status: 'error', error: message }))
  process.exit(2)
}

const domPath = flag('--dom')
const citesPath = flag('--cites')
if (!domPath || !citesPath) fail('usage: resolve-refs.mjs --dom <DOM_JSON> --cites <CITES_JSON>')

let dom, cites
try {
  dom = JSON.parse(readFileSync(domPath, 'utf8'))
  cites = JSON.parse(readFileSync(citesPath, 'utf8'))
} catch (err) {
  fail(`cannot read input: ${err.message}`)
}
if (!Array.isArray(dom.pages) || !Array.isArray(cites)) fail('dom.json needs pages[]; cites must be an array')

// Collect every word under a page, whatever nesting the digitizer used (paragraphs, tables, cells).
const collectWords = node => {
  if (Array.isArray(node)) return node.flatMap(collectWords)
  if (!node || typeof node !== 'object') return []
  const own = Array.isArray(node.words) ? node.words : []
  const nested = Object.entries(node)
    .filter(([key]) => key !== 'words')
    .flatMap(([, value]) => collectWords(value))
  return [...own, ...nested]
}

// Compare words without case, quotes, or edge punctuation, so "2025." and "2025" match; "$1,000" and "1.5%" keep their marks.
const normalize = text => text
  .toLowerCase()
  .replace(/[^\p{L}\p{N}%$.,-]+/gu, '')
  .replace(/^[.,-]+|[.,-]+$/g, '')
const tokens = text => text.split(/\s+/).map(normalize).filter(Boolean)

const pages = dom.pages.map(page => ({
  page: page.pageIndex + 1,
  words: collectWords(page.sections)
    .filter(word => Array.isArray(word.box) && word.box.length === 4 && typeof word.text === 'string')
    .map(word => ({ token: normalize(word.text), box: word.box, line: word.visualLineNumber ?? 0 })),
}))

// The digitizer can list a word out of reading order within its line; lines then left-to-right is the fallback order.
const readingOrder = words => [...words].sort((a, b) => a.line - b.line || a.box[1] - b.box[1])

// Word box is [top, left, width, height]; a sourceRef box is "left,top,width,height".
const union = words => {
  const left = Math.min(...words.map(w => w.box[1]))
  const top = Math.min(...words.map(w => w.box[0]))
  const right = Math.max(...words.map(w => w.box[1] + w.box[2]))
  const bottom = Math.max(...words.map(w => w.box[0] + w.box[3]))
  return `${left},${top},${right - left},${bottom - top}`
}

const scan = (words, wanted) => {
  const hits = []
  for (let i = 0; i + wanted.length <= words.length; i++) {
    if (wanted.every((token, j) => words[i + j].token === token)) hits.push(words.slice(i, i + wanted.length))
  }
  return hits
}

const matchesOnPage = (words, wanted) => {
  const inDataOrder = scan(words, wanted)
  return inDataOrder.length ? inDataOrder : scan(readingOrder(words), wanted)
}

const resolveOne = cite => {
  const wanted = tokens(String(cite.quote ?? ''))
  if (!cite.id || wanted.length === 0) return { id: cite.id ?? null, status: 'unresolved', reason: 'missing id or quote' }

  const cited = pages.filter(p => p.page === Number(cite.page))
  const search = cited.length ? cited : pages
  const hits = search.flatMap(p => matchesOnPage(p.words, wanted).map(words => ({ page: p.page, words })))

  if (hits.length === 0) {
    const reason = cited.length ? `quote not found on page ${cite.page}` : 'quote not found on any page'
    return { id: cite.id, status: 'unresolved', reason }
  }
  if (hits.length > 1) {
    return {
      id: cite.id,
      status: 'ambiguous',
      reason: `quote matches ${hits.length} places; cite more words`,
      candidates: hits.map(h => ({ page: h.page, box: union(h.words) })),
    }
  }
  const [hit] = hits
  return { id: cite.id, status: 'resolved', page: hit.page, box: union(hit.words) }
}

const results = cites.map(resolveOne)
console.log(JSON.stringify({
  status: 'ok',
  resolved: results.filter(r => r.status === 'resolved').length,
  unresolved: results.filter(r => r.status === 'unresolved').length,
  ambiguous: results.filter(r => r.status === 'ambiguous').length,
  results,
}))
