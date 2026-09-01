#!/usr/bin/env node
/**
 * mine-history — read the CLI validator's vocabulary AT A TARGET VERSION, and date
 * every member from git history.
 *
 * Phase 1 of the workflow needs two things the installed tooling cannot give:
 *   - the vocabulary for a version that is NOT the one on this machine
 *   - WHEN each member arrived, which is the only cheap way to infer version-scoped
 *     semantics ("runs-sequentially arrives with 'migrate case schema to v19')
 *
 * Both come from `git show <ref>:<file>` and `git log -S` over the CLI repo. Unlike
 * probing, history is dated and works for versions you cannot run.
 *
 *   node mine-history.mjs [--repo ~/src/cli] [--ref v1.198.0] [--dates] [--json]
 *
 * --dates runs one `git log -S` per member (slower; ~1s each) to find the introducing
 * commit and any schema-version hint in its subject.
 *
 * SCOPE: this reads the CLI layer (rank 3) only. It is NOT the whole validator —
 * `case-tool` has never contained `sla-status-change`, yet `uip` accepts it, because
 * the case-schema bundled in maestro-tool also validates. Absence here is not absence
 * from the platform. Cross-check with extract-schema.mjs (rank 2) before concluding.
 */
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';

const arg = (n, d) => { const i = process.argv.indexOf(n); return i > -1 ? process.argv[i + 1] : d; };
const REPO = (arg('--repo', `${process.env.HOME}/src/cli`) || '').replace(/^~/, process.env.HOME ?? '');
const REF = arg('--ref', 'HEAD');
const DATES = process.argv.includes('--dates');
const JSON_OUT = process.argv.includes('--json');
const FILE = 'packages/case-tool/src/services/case-validate-service.ts';

if (!existsSync(`${REPO}/.git`)) {
  console.error(`mine-history: no git repo at ${REPO}`);
  console.error('Pass --repo <path to the uip CLI checkout>. Without it, phase 1 has no history to mine.');
  process.exit(2);
}
const git = (...a) => {
  try { return execFileSync('git', ['-C', REPO, ...a], { encoding: 'utf8', maxBuffer: 64 << 20 }); }
  catch { return null; }
};

const src = git('show', `${REF}:${FILE}`);
if (!src) {
  console.error(`mine-history: cannot read ${FILE} at ref "${REF}".`);
  const tags = (git('tag', '--sort=-v:refname') || '').trim().split('\n').filter(Boolean).slice(0, 10);
  console.error(`Known refs: ${tags.join(', ') || '(none)'} — or any commit sha.`);
  console.error('Refusing to fall back to HEAD: a vocabulary from the wrong version is worse than none.');
  process.exit(2);
}

/** Pull `const NAME = new Set<string>([ "a", "b" ]);` blocks. */
function sets(text) {
  const out = {};
  for (const m of text.matchAll(/const (VALID_[A-Z_]+)\s*=\s*new Set<string>\(\[([\s\S]*?)\]\)/g)) {
    out[m[1]] = [...m[2].matchAll(/"([^"]+)"/g)].map((x) => x[1]).sort();
  }
  return out;
}
const vocab = sets(src);
if (!Object.keys(vocab).length) {
  console.error(`mine-history: found no VALID_* sets at ${REF}. The file moved or changed shape —`);
  console.error('fix this script rather than reporting an empty vocabulary as "no members".');
  process.exit(2);
}

const out = { repo: REPO, ref: REF, file: FILE, vocab };

// Where the ref sits relative to the working tree, so a stale checkout is visible.
out.refCommit = (git('rev-parse', '--short', REF) || '').trim();
out.refSubject = (git('log', '-1', '--format=%s', REF) || '').trim();
out.refDate = (git('log', '-1', '--format=%ci', REF) || '').trim();

if (DATES) {
  out.introduced = {};
  for (const [set, members] of Object.entries(vocab)) {
    for (const m of members) {
      const line = (git('log', '--oneline', '--reverse', '-S', `"${m}"`, '--', FILE) || '').split('\n')[0]?.trim();
      if (!line) continue;
      // A schema-version hint in the subject is the cheapest version-scoping signal we get.
      const v = /\b[vV](\d{1,2})\b(?!\.\d)/.exec(line.replace(/#\d+/g, ''));
      out.introduced[m] = { set, commit: line, schemaVersionHint: v ? `V${v[1]}` : null };
    }
  }
}

if (JSON_OUT) { console.log(JSON.stringify(out, null, 2)); process.exit(0); }

console.log(`repo: ${REPO}`);
console.log(`ref:  ${REF} = ${out.refCommit}  (${out.refDate})`);
console.log(`      ${out.refSubject}`);
console.log(`\nCLI-layer vocabulary at this ref (rank 3 — not the whole validator):`);
for (const [k, v] of Object.entries(vocab)) console.log(`  ${k} (${v.length}): ${v.join(', ')}`);
if (out.introduced) {
  console.log('\nintroduced (first commit whose diff added the literal):');
  const rows = Object.entries(out.introduced).sort((a, b) => a[1].set.localeCompare(b[1].set) || a[0].localeCompare(b[0]));
  for (const [m, i] of rows) console.log(`  ${m.padEnd(30)} ${(i.schemaVersionHint ?? '  —').padEnd(5)} ${i.commit.slice(0, 78)}`);
}
console.log('\nRemember: absence here is not absence from the platform. maestro-tool bundles');
console.log('its own case-schema that also validates — cross-check with extract-schema.mjs.');
