import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { citationMap } from "../../scripts/case-rule-citations.mjs";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const SNAPSHOT = join(REPO_ROOT, "tests", "fixtures", "case-rule-citations.json");

// `Rule N` citations in the case skill are indexes into its Critical Rules, and
// an insertion mid-list moves every citation at or above it onto a DIFFERENT
// EXISTING rule. Measured on this skill: inserting at Rule 4 moves 205 of 224.
// Nothing detects that -- the number still resolves, it is merely wrong now, so
// a dangling-number check stays green (this is exactly how `Never auto-run
// (Rule 12)` came to mean Build-review preference in a shipped flavor tree).
//
// So snapshot what each citation RESOLVES TO, not the number. A correct
// renumber leaves every title unchanged and this test never notices. An
// incorrect one changes titles and this test names the file and both rules.
//
// When you deliberately change which rule a document cites, regenerate:
//   node scripts/case-rule-citations.mjs > tests/fixtures/case-rule-citations.json
// and the diff is the review: every line is a claim about what a doc points at.
test("every `Rule N` in the case skill still resolves to the rule it used to", () => {
  const expected = JSON.parse(readFileSync(SNAPSHOT, "utf8"));
  const actual = citationMap();

  const drift = [];
  for (const file of new Set([...Object.keys(expected), ...Object.keys(actual)])) {
    const was = expected[file] ?? {};
    const now = actual[file] ?? {};
    for (const title of new Set([...Object.keys(was), ...Object.keys(now)])) {
      if ((was[title] ?? 0) !== (now[title] ?? 0)) {
        drift.push(`${file}: "${title}" cited ${was[title] ?? 0}x -> ${now[title] ?? 0}x`);
      }
    }
  }
  assert.deepEqual(
    drift.sort(),
    [],
    `citations now point at different rules than the snapshot records:\n  ${drift.sort().join("\n  ")}\n` +
      `If that is intended, regenerate: node scripts/case-rule-citations.mjs > tests/fixtures/case-rule-citations.json`,
  );
});

test("no citation points at a rule that does not exist", () => {
  const unresolved = [];
  for (const [file, titles] of Object.entries(citationMap())) {
    for (const title of Object.keys(titles)) {
      if (title.startsWith("<<UNRESOLVED")) unresolved.push(`${file}: ${title}`);
    }
  }
  assert.deepEqual(unresolved, [], `dangling citation(s):\n  ${unresolved.join("\n  ")}`);
});
