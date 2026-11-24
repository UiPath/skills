// Guards SKILL.md rule 21 of uipath-api-workflow: every instruction to run
// `uip api-workflow run` (`--no-auth` included) must sit in a section that
// mentions consent. Catches regressions that reintroduce "just run it" steps.
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const ROOTS = [
  "skills/uipath-api-workflow",
  "skills/uipath-troubleshoot/references/products/api-workflows",
];

// A command line inside a fenced block, or an imperative prose sentence.
const COMMAND = /(^|&&\s*|\(\s*cd [^)]*&&\s*)uip api-workflow run\b(?![^\n]*--help)/;
const IMPERATIVE =
  /^\s*(?:[-*]|\d+\.)?\s*(?:\*\*[^*]+\*\*\s*)?(?:Then\s+)?(?:Run|Re-?run|Reproduce|Validate|Execute)\b[^\n]*uip api-workflow run\b/i;
const CONSENT = /consent|\bask\b|\byes\b|approv|rule[ -]21/i;

function markdownFiles(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return markdownFiles(path);
    return path.endsWith(".md") ? [path] : [];
  });
}

function unguardedRunInstructions(path) {
  const lines = readFileSync(path, "utf8").split("\n");
  const findings = [];
  let fenced = false;
  let sectionStart = 0;
  lines.forEach((line, index) => {
    if (/^#{1,6}\s/.test(line) && !fenced) sectionStart = index;
    if (/^\s*```/.test(line)) {
      fenced = !fenced;
      return;
    }
    const isInstruction = fenced ? COMMAND.test(line.trim()) : IMPERATIVE.test(line);
    if (!isInstruction) return;
    let sectionEnd = lines.findIndex((l, i) => i > index && /^#{1,6}\s/.test(l));
    if (sectionEnd === -1) sectionEnd = lines.length;
    if (!CONSENT.test(lines.slice(sectionStart, sectionEnd).join("\n"))) {
      findings.push(`${relative(REPO_ROOT, path)}:${index + 1}: ${line.trim()}`);
    }
  });
  return findings;
}

test("every `uip api-workflow run` instruction sits in a section that requires consent", () => {
  const findings = ROOTS.flatMap((root) => markdownFiles(join(REPO_ROOT, root))).flatMap(
    unguardedRunInstructions,
  );
  assert.deepEqual(findings, [], `Run instructions without consent wording:\n${findings.join("\n")}`);
});
