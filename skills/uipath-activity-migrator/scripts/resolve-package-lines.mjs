#!/usr/bin/env node
// resolve-package-lines.mjs — list release lines of a UiPath activity package from the official NuGet feed.
//
// Usage: node resolve-package-lines.mjs --package <PackageId> [--min <version>] [--studio-version <x.y.z.w>] [--lines <n>] [--all-lines]
//   --package         NuGet package id, e.g. UiPath.UIAutomation.Activities (required)
//   --min             drop lines whose highest stable patch is below this version (default: none)
//   --studio-version  project.json studioVersion; a line matching its major.minor becomes the recommendation
//   --lines           how many most-recent lines to return (default 2)
//   --all-lines       include STS lines (minor != 10); default keeps LTS lines only
// Env:   UIPATH_ACTIVITY_MIGRATOR_FEED_URL  NuGet v3 flat-container base (default: UiPath Official feed)
// Output: one JSON object: { package, feed, lines:[{line, version}], recommended, reason } or { error }.
// Exit: 0 ok, 1 feed unreachable or package unknown, 2 usage. No dependencies. Node 18+.

const DEFAULT_FEED = 'https://pkgs.dev.azure.com/uipath/Public.Feeds/_packaging/UiPath-Official/nuget/v3/flat2';

const args = process.argv.slice(2);
const opt = (name, def) => {
  const i = args.indexOf(name);
  return i >= 0 && i + 1 < args.length ? args[i + 1] : def;
};
const pkg = opt('--package');
const min = opt('--min', null);
const studio = opt('--studio-version', null);
const lineCount = Number(opt('--lines', '2'));
const allLines = args.includes('--all-lines');
if (!pkg) {
  console.error('usage: node resolve-package-lines.mjs --package <PackageId> [--min <version>] [--studio-version <x.y.z.w>] [--lines <n>] [--all-lines]');
  process.exit(2);
}
const feed = (process.env.UIPATH_ACTIVITY_MIGRATOR_FEED_URL || DEFAULT_FEED).replace(/\/+$/, '');
const url = `${feed}/${pkg.toLowerCase()}/index.json`;

const parse = (v) => v.split('.').map((x) => Number(x));
const cmp = (a, b) => {
  const pa = parse(a); const pb = parse(b);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const d = (pa[i] || 0) - (pb[i] || 0);
    if (d) return d;
  }
  return 0;
};
const lineOf = (v) => { const p = parse(v); return `${p[0]}.${p[1]}`; };

let versions;
try {
  const res = await fetch(url, { signal: AbortSignal.timeout(30000) });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  versions = (await res.json()).versions || [];
} catch (e) {
  console.log(JSON.stringify({ error: `feed unreachable or package unknown: ${url} (${e.message})` }));
  process.exit(1);
}

const stable = versions.filter((v) => !v.includes('-') && /^\d+\.\d+\.\d+/.test(v));
const byLine = new Map();
for (const v of stable) {
  const l = lineOf(v);
  if (!allLines && parse(v)[1] !== 10) continue;
  if (!byLine.has(l) || cmp(v, byLine.get(l)) > 0) byLine.set(l, v);
}
let lines = [...byLine.entries()].map(([line, version]) => ({ line, version }));
if (min) lines = lines.filter((l) => cmp(l.version, min) >= 0);
lines.sort((a, b) => cmp(b.version, a.version));
lines = lines.slice(0, Math.max(1, lineCount));

let recommended = lines[0] ? lines[0].line : null;
let reason = lines[0] ? 'newest release line' : 'no candidate lines';
if (studio) {
  const sp = parse(studio);
  const sl = `${sp[0]}.${sp[1]}`;
  const hit = lines.find((l) => l.line === sl);
  if (hit) { recommended = hit.line; reason = `matches project studioVersion ${studio}`; }
}

console.log(JSON.stringify({ package: pkg, feed: url, lines, recommended, reason }));
