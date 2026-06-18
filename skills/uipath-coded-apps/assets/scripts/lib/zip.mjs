// Dependency-free ZIP reader/writer (pure Node, zlib only). Used to pack and
// extract the dashboard starter-kit archive. Cross-platform by design: it needs
// only Node — no system `unzip`/`tar`/PowerShell — so any coding agent on any OS
// gets identical behavior.

import { readdirSync, readFileSync, mkdirSync, writeFileSync } from 'node:fs'
import { join, dirname, relative, sep, resolve } from 'node:path'
import { deflateRawSync, inflateRawSync } from 'node:zlib'
import { createHash } from 'node:crypto'

const CRC_TABLE = (() => {
  const t = new Uint32Array(256)
  for (let n = 0; n < 256; n++) {
    let c = n
    for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1)
    t[n] = c >>> 0
  }
  return t
})()

export function crc32(buf) {
  let c = 0xFFFFFFFF
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xFF] ^ (c >>> 8)
  return (c ^ 0xFFFFFFFF) >>> 0
}

// Recursively list files under dir as { name: posix-relative, data: Buffer },
// sorted by name so output ordering is deterministic.
function listFiles(dir) {
  const out = []
  const walk = (d) => {
    for (const entry of readdirSync(d, { withFileTypes: true })) {
      const full = join(d, entry.name)
      if (entry.isDirectory()) walk(full)
      else if (entry.isFile()) out.push({ name: relative(dir, full).split(sep).join('/'), data: readFileSync(full) })
    }
  }
  walk(dir)
  return out.sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0))
}

/**
 * A zlib-independent hash of a directory's CONTENT (sorted name + bytes). Used as
 * the manifest checksum so the drift guard is stable across Node/zlib versions
 * (we checksum the source content, not the compressed zip bytes).
 * @param {string} srcDir
 * @returns {string} sha256 hex
 */
export function contentHash(srcDir) {
  const h = createHash('sha256')
  for (const f of listFiles(srcDir)) {
    h.update(f.name); h.update('\0')
    // Normalize CRLF→LF (drop 0x0D) so the digest is line-ending-insensitive.
    // Otherwise a Windows autocrlf checkout (CRLF) hashes differently from the
    // LF content the manifest was packed from, and the drift guard false-fails
    // on fresh checkouts / CI / non-Windows machines. Scaffold files are text.
    h.update(f.data.includes(0x0d) ? Buffer.from(f.data.filter((b) => b !== 0x0d)) : f.data)
  }
  return h.digest('hex')
}

/**
 * Pack a directory into a ZIP Buffer. Entries are sorted and stamped with a fixed
 * timestamp, so the same input yields byte-identical output within a given Node.
 * @param {string} srcDir
 * @returns {Buffer}
 */
export function zipDir(srcDir) {
  const files = listFiles(srcDir)
  const localParts = []
  const central = []
  let offset = 0
  const DOS_TIME = 0
  const DOS_DATE = 0x21 // 1980-01-01, fixed for determinism

  for (const f of files) {
    const nameBuf = Buffer.from(f.name, 'utf8')
    const crc = crc32(f.data)
    const comp = deflateRawSync(f.data)

    const local = Buffer.alloc(30)
    local.writeUInt32LE(0x04034b50, 0)   // local file header signature
    local.writeUInt16LE(20, 4)           // version needed to extract
    local.writeUInt16LE(0, 6)            // general purpose flags
    local.writeUInt16LE(8, 8)            // compression method = deflate
    local.writeUInt16LE(DOS_TIME, 10)
    local.writeUInt16LE(DOS_DATE, 12)
    local.writeUInt32LE(crc, 14)
    local.writeUInt32LE(comp.length, 18) // compressed size
    local.writeUInt32LE(f.data.length, 22) // uncompressed size
    local.writeUInt16LE(nameBuf.length, 26)
    local.writeUInt16LE(0, 28)           // extra field length
    localParts.push(local, nameBuf, comp)

    const cen = Buffer.alloc(46)
    cen.writeUInt32LE(0x02014b50, 0)     // central directory header signature
    cen.writeUInt16LE(20, 4)             // version made by
    cen.writeUInt16LE(20, 6)             // version needed
    cen.writeUInt16LE(0, 8)              // flags
    cen.writeUInt16LE(8, 10)             // method
    cen.writeUInt16LE(DOS_TIME, 12)
    cen.writeUInt16LE(DOS_DATE, 14)
    cen.writeUInt32LE(crc, 16)
    cen.writeUInt32LE(comp.length, 20)
    cen.writeUInt32LE(f.data.length, 24)
    cen.writeUInt16LE(nameBuf.length, 28)
    cen.writeUInt16LE(0, 30)             // extra len
    cen.writeUInt16LE(0, 32)             // comment len
    cen.writeUInt16LE(0, 34)             // disk number start
    cen.writeUInt16LE(0, 36)             // internal attrs
    cen.writeUInt32LE(0, 38)             // external attrs
    cen.writeUInt32LE(offset, 42)        // offset of local header
    central.push(cen, nameBuf)

    offset += local.length + nameBuf.length + comp.length
  }

  const localBuf = Buffer.concat(localParts)
  const centralBuf = Buffer.concat(central)
  const eocd = Buffer.alloc(22)
  eocd.writeUInt32LE(0x06054b50, 0)      // end of central directory signature
  eocd.writeUInt16LE(0, 4)               // disk number
  eocd.writeUInt16LE(0, 6)               // disk with central directory
  eocd.writeUInt16LE(files.length, 8)    // entries on this disk
  eocd.writeUInt16LE(files.length, 10)   // total entries
  eocd.writeUInt32LE(centralBuf.length, 12)
  eocd.writeUInt32LE(localBuf.length, 16) // central directory offset
  eocd.writeUInt16LE(0, 20)              // comment length
  return Buffer.concat([localBuf, centralBuf, eocd])
}

/**
 * Extract a ZIP Buffer into destDir. Creates parent directories; supports stored
 * (method 0) and deflate (method 8) entries.
 * @param {Buffer} buffer
 * @param {string} destDir
 */
export function unzipTo(buffer, destDir) {
  let eocd = -1
  for (let i = buffer.length - 22; i >= 0; i--) {
    if (buffer.readUInt32LE(i) === 0x06054b50) { eocd = i; break }
  }
  if (eocd < 0) throw new Error('unzipTo: end-of-central-directory not found (not a zip?)')
  const count = buffer.readUInt16LE(eocd + 10)
  let p = buffer.readUInt32LE(eocd + 16)

  for (let i = 0; i < count; i++) {
    if (buffer.readUInt32LE(p) !== 0x02014b50) throw new Error('unzipTo: bad central directory entry')
    const method = buffer.readUInt16LE(p + 10)
    const compSize = buffer.readUInt32LE(p + 20)
    const nameLen = buffer.readUInt16LE(p + 28)
    const extraLen = buffer.readUInt16LE(p + 30)
    const commentLen = buffer.readUInt16LE(p + 32)
    const localOff = buffer.readUInt32LE(p + 42)
    const name = buffer.toString('utf8', p + 46, p + 46 + nameLen)
    p += 46 + nameLen + extraLen + commentLen

    if (name.endsWith('/')) continue // directory entry
    // Zip-slip guard: never let an entry escape destDir. The shipped archive is
    // trusted, but unzipTo is a general helper — reject absolute paths, `..`
    // segments, backslashes, and anything that resolves outside the root.
    if (name.startsWith('/') || name.includes('\\') || name.split('/').includes('..')) {
      throw new Error(`unzipTo: unsafe entry path: ${name}`)
    }
    const dest = resolve(destDir, name)
    const root = resolve(destDir)
    if (dest !== root && !dest.startsWith(root + sep)) {
      throw new Error(`unzipTo: entry escapes destDir: ${name}`)
    }
    const lNameLen = buffer.readUInt16LE(localOff + 26)
    const lExtraLen = buffer.readUInt16LE(localOff + 28)
    const dataStart = localOff + 30 + lNameLen + lExtraLen
    const raw = buffer.subarray(dataStart, dataStart + compSize)
    const data = method === 8 ? inflateRawSync(raw) : Buffer.from(raw)
    mkdirSync(dirname(dest), { recursive: true })
    writeFileSync(dest, data)
  }
}
