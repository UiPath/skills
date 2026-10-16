#!/usr/bin/env node
// Look up one or more names in the installed @uipath/maestro-builder-sdk API
// indexes and print each matching declaration span (doc comment included).
// Usage: node sdk-api.mjs <name|Owner.member>... [--depth N] [--all] [--sdk <dir>] [--max-lines N]
//   --depth N    also print the exported types each declaration's code references,
//                N hops deep (default 3; 0 = only the names asked for)
//   --all        include the /case and /bpmn entry points (default: Flow only)
//   --sdk <dir>  package root; default: nearest node_modules up from cwd, then `npm root -g`
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { execSync } from 'node:child_process';

const PKG = join('@uipath', 'maestro-builder-sdk');
const args = process.argv.slice(2);
const flag = (name) => {
  const i = args.indexOf(name);
  if (i < 0) return undefined;
  const v = args[i + 1];
  args.splice(i, 2);
  return v;
};
const sdkArg = flag('--sdk');
const maxLines = Number(flag('--max-lines') ?? 300);
const depth = Number(flag('--depth') ?? 3);
const BUDGET = 1500; // total printed lines before referenced types stop being expanded
const all = args.includes('--all');
const names = args.filter((a) => a !== '--all');

if (!names.length || names.includes('--help') || names.includes('-h')) {
  console.log('Usage: node sdk-api.mjs <name|Owner.member>... [--depth N] [--all] [--sdk <dir>] [--max-lines N]');
  process.exit(names.length ? 0 : 1);
}

function findSdk() {
  if (sdkArg) return existsSync(join(resolve(sdkArg), 'dist', 'api-index.md')) ? resolve(sdkArg) : null;
  for (let d = process.cwd(); ; d = dirname(d)) {
    const p = join(d, 'node_modules', PKG);
    if (existsSync(join(p, 'dist', 'api-index.md'))) return p;
    if (dirname(d) === d) break;
  }
  try {
    const g = join(execSync('npm root -g', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(), PKG);
    if (existsSync(join(g, 'dist', 'api-index.md'))) return g;
  } catch {}
  return null;
}

const root = findSdk();
if (!root) {
  console.error('SDK_NOT_FOUND: @uipath/maestro-builder-sdk is not installed in this workspace or globally.');
  console.error('Install it, then rerun: npm install -g @uipath/maestro-builder-sdk');
  process.exit(2);
}

// member rows: | `name` | kind | `Owner` | `path:a-b` |
// index rows:  | `name` | kind | `path:a-b` | area | summary |
function parse(file, isMember) {
  const rows = [];
  for (const line of readFileSync(join(root, 'dist', file), 'utf8').split('\n')) {
    if (!line.startsWith('| `')) continue;
    const cells = line.split('|').slice(1, -1).map((c) => c.trim().replace(/^`|`$/g, ''));
    const loc = (isMember ? cells[3] : cells[2]) ?? '';
    const m = loc.match(/^(.+):(\d+)-(\d+)$/);
    if (!m) continue;
    rows.push({
      name: cells[0], kind: cells[1], owner: isMember ? cells[2] : '',
      area: isMember ? '' : cells[3], path: m[1], start: +m[2], end: +m[3],
    });
  }
  return rows;
}
const rows = [...parse('api-index.md', false), ...parse('api-members.md', true)];
const inScope = (r) => all || !/^dist\/(case|bpmn)\//.test(r.path);

const fileCache = new Map();
const lines = (p) => {
  if (!fileCache.has(p)) fileCache.set(p, readFileSync(join(root, p), 'utf8').split('\n'));
  return fileCache.get(p);
};

const TYPE_KINDS = new Set(['interface', 'type', 'class', 'enum']);
// return-type plumbing every action declaration names; never the answer to a lookup
const NOT_FOLLOWED = new Set(['ActionSpec', 'FlowActionSpecs']);
const typeRows = new Map();
for (const r of rows) if (!r.owner && TYPE_KINDS.has(r.kind) && inScope(r) && !typeRows.has(r.name)) typeRows.set(r.name, r);

let missing = 0;
let budget = BUDGET;
const printed = new Set();
const queue = []; // referenced types: { row, via, hop }
const skipped = new Set();

function print(r, label) {
  const key = `${r.path}:${r.start}`;
  const head = `--- ${label ?? ''}${r.owner ? `${r.owner}.` : ''}${r.name} (${r.kind}${r.area ? `, ${r.area}` : ''}) ${r.path}:${r.start}-${r.end}`;
  if (printed.has(key)) { if (!label) console.log(`${head} [printed above]`); return null; }
  printed.add(key);
  console.log(head);
  const src = lines(r.path);
  const end = Math.min(r.end, r.start + maxLines - 1);
  const code = [];
  for (let n = r.start; n <= end; n++) {
    const text = src[n - 1] ?? '';
    console.log(`${n}\t${text}`);
    if (!/^\s*(\/\*\*|\*|\/\/)/.test(text)) code.push(text);
  }
  budget -= end - r.start + 1;
  if (end < r.end) console.log(`[truncated at ${maxLines} lines; rerun with --max-lines ${r.end - r.start + 1}]`);
  return code.join('\n');
}

function enqueue(code, via, hop) {
  if (hop > depth || !code) return;
  for (const id of new Set(code.match(/\b[A-Z][A-Za-z0-9]+\b/g) ?? [])) {
    const r = typeRows.get(id);
    if (r && id !== via && !NOT_FOLLOWED.has(id) && !printed.has(`${r.path}:${r.start}`)) queue.push({ row: r, via, hop });
  }
}

for (const query of names) {
  const [owner, member] = query.includes('.') ? query.split('.', 2) : [null, query];
  const pick = (cmp) => rows.filter((r) => cmp(r.name, member) && (!owner || cmp(r.owner, owner)));
  let hits = pick((a, b) => a === b);
  if (!hits.length) hits = pick((a, b) => a.toLowerCase() === b.toLowerCase());
  const scoped = hits.filter(inScope);
  const outOfScope = hits.length - scoped.length;
  console.log(`=== ${query}: ${scoped.length} match(es)${outOfScope ? ` (+${outOfScope} in /case or /bpmn; --all shows them)` : ''}`);
  if (!scoped.length) {
    missing++;
    const q = member.toLowerCase();
    const near = [...new Set(rows.filter(inScope).filter((r) => r.name.toLowerCase().includes(q)).map((r) => r.owner ? `${r.owner}.${r.name}` : r.name))].slice(0, 12);
    console.log(near.length ? `no exact name; similar: ${near.join(', ')}` : 'no declaration has this name — probably a RUNTIME output key; see the node reference');
    continue;
  }
  for (const r of scoped) enqueue(print(r), r.name, 1);
}

if (queue.length) console.log(`=== referenced types (${depth} hop(s) deep)`);
while (queue.length) {
  const { row, via, hop } = queue.shift();
  if (printed.has(`${row.path}:${row.start}`)) continue;
  if (budget <= 0) { skipped.add(row.name); continue; }
  enqueue(print(row, `[from ${via}] `), row.name, hop + 1);
}
if (skipped.size) console.log(`=== not expanded (line budget reached): ${[...skipped].join(' ')} — pass them as names to print them`);
process.exit(missing === names.length ? 1 : 0);
