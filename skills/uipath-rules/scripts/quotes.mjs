// Quote handling for cite.mjs: turn a verbatim quote into a page box from a digitizer dom.json. No dependencies.

// Compare words without case, quotes, or edge punctuation, so "2025." and "2025" match; "$1,000" and "1.5%" keep their marks.
// NFKC folds ligatures ("ﬁ" -> "fi"); every dash and minus reads as "-", so "5–10" matches "5-10".
export const normalize = text => text
  .normalize('NFKC')
  .replace(/[\u2010-\u2015\u2212]/g, '-')
  .toLowerCase()
  .replace(/[^\p{L}\p{N}%$.,-]+/gu, '')
  .replace(/^[.,-]+|[.,-]+$/g, '')

const ENTITIES = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' }
// A quote copied from extracted text can carry HTML table markup (<td>, <br>, &amp;); the words are what count. Only
// markup tags are dropped, so a threshold such as "<18 years or >65" keeps its words.
const MARKUP = /<\/?(?:table|thead|tbody|tfoot|tr|td|th|br|p|div|span|li|ul|ol|b|i|u|em|strong|sup|sub|h[1-6])\b[^<>]*>/gi
export const cleanQuote = text => String(text ?? '')
  .replace(MARKUP, ' ')
  .replace(/&(#x[0-9a-fA-F]+|#\d+|\w+);/g, (whole, name) => {
    if (name[0] === '#') return String.fromCodePoint(name[1] === 'x' ? parseInt(name.slice(2), 16) : parseInt(name.slice(1), 10))
    return name in ENTITIES ? ENTITIES[name] : whole
  })

export const tokens = text => cleanQuote(text).split(/\s+/).map(normalize).filter(Boolean)

// A quote with "..." is several fragments of one clause; each fragment resolves on its own.
export const fragments = quote => cleanQuote(quote).split(/\.\.\.|…/).map(f => f.trim()).filter(f => tokens(f).length > 0)

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

export const domPages = dom => {
  if (!dom || !Array.isArray(dom.pages)) throw new Error('dom.json needs pages[]')
  return dom.pages.map(page => ({
    page: page.pageIndex + 1,
    words: collectWords(page.sections)
      .filter(word => Array.isArray(word.box) && word.box.length === 4 && typeof word.text === 'string')
      .map(word => ({ token: normalize(word.text), box: word.box, line: word.visualLineNumber ?? 0 }))
      // A word that is only a symbol ("≥", "&", "•") normalizes to nothing; the quote's tokens drop it too.
      .filter(word => word.token),
  }))
}

// The digitizer can list a word out of reading order within its line; lines then left-to-right is the fallback order.
const readingOrder = words => [...words].sort((a, b) => a.line - b.line || a.box[1] - b.box[1])

// Word box is [top, left, width, height]; a sourceRef box is "left,top,width,height".
const round = n => Math.round(n * 100) / 100
export const union = words => {
  const left = Math.min(...words.map(w => w.box[1]))
  const top = Math.min(...words.map(w => w.box[0]))
  const right = Math.max(...words.map(w => w.box[1] + w.box[2]))
  const bottom = Math.max(...words.map(w => w.box[0] + w.box[3]))
  return `${round(left)},${round(top)},${round(right - left)},${round(bottom - top)}`
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

// One quote (or fragment) against dom pages. Returns { status: resolved|ambiguous|unresolved, page?, box?, candidates?, reason? }.
export const resolveQuote = (pages, page, quote) => {
  const wanted = tokens(String(quote ?? ''))
  if (wanted.length === 0) return { status: 'unresolved', reason: 'missing quote' }
  const cited = pages.filter(p => p.page === Number(page))
  const search = cited.length ? cited : pages
  // The digitizer lists some words twice (a paragraph and the table cell that holds it); the same box is one place.
  const seen = new Set()
  const hits = search.flatMap(p => matchesOnPage(p.words, wanted).map(words => ({ page: p.page, words, box: union(words) })))
    .filter(h => !seen.has(`${h.page}|${h.box}`) && seen.add(`${h.page}|${h.box}`))
  if (hits.length === 0) {
    return { status: 'unresolved', reason: cited.length ? `quote not found on page ${page}` : 'quote not found on any page' }
  }
  if (hits.length > 1) {
    return {
      status: 'ambiguous',
      reason: `quote matches ${hits.length} places; cite more words`,
      candidates: hits.map(h => ({ page: h.page, box: h.box })),
    }
  }
  const [hit] = hits
  return { status: 'resolved', page: hit.page, box: hit.box }
}
