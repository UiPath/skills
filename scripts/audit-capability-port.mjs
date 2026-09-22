/**
 * Compare a ported capability in `preview/` against its source in the GA skill.
 *
 * Reports what the GA side states and the preview side does not: `uip` commands,
 * and bolded `Never …` / `Always …` / `Do not …` rules. Coverage is judged on the
 * distinctive words of each rule, so a reworded rule counts as covered and a
 * dropped one does not.
 *
 *   node scripts/audit-capability-port.mjs <ga-path> <preview-file>
 *   node scripts/audit-capability-port.mjs \
 *     skills/uipath-maestro-flow/references/operate \
 *     preview/skills/uipath-maestro-flow/references/operate.md
 *
 * `<ga-path>` is a file or a directory; a directory reads its `*.md`. Advisory:
 * it always exits 0. A missing item can be a deliberate omission — the point is
 * that the omission is seen and decided, not that it is forbidden.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

/** Real `uip` verb paths, so an example's arguments are not read as verbs. */
const CATALOG = new Set(
  JSON.parse(readFileSync(new URL("../assets/uip-catalog-snapshot.json", import.meta.url), "utf8")).verbs,
);

const STOPWORDS = new Set([
  "never", "always", "without", "before", "first", "instead", "because",
  "should", "would", "their", "there", "these", "those", "which", "while",
]);

function read(path) {
  if (statSync(path).isDirectory()) {
    return readdirSync(path)
      .filter((name) => name.endsWith(".md"))
      .map((name) => readFileSync(join(path, name), "utf8"))
      .join("\n");
  }
  return readFileSync(path, "utf8");
}

/**
 * `uip <verb path>`, from backticked spans and fenced lines — the two places a
 * command is actually written. Reading running prose instead would have to guess
 * where the verb path ends and the sentence resumes, and guessing wrong reports
 * a command as absent when it is three words away.
 */
export function commands(text) {
  const found = new Set();
  const spans = [
    ...[...text.matchAll(/`([^`\n]+)`/g)].map((m) => m[1]),
    ...text.split("\n").filter((line) => /^\s*(?:[A-Z_]+=\S+\s+)?uip\s/.test(line)),
  ];
  for (const span of spans) {
    const match = span.match(/\buip ((?:[a-z][a-z-]* )*[a-z][a-z-]*)/);
    if (!match) continue;
    // Trim to the longest prefix the CLI catalog actually knows. Without this,
    // an example's arguments read as verb segments and `eval add greeting-test`
    // and `eval add hello-test` count as two different commands.
    const words = [];
    for (const word of match[1].split(/\s+/)) {
      if (word.startsWith("-") || word.startsWith("<")) break;
      words.push(word);
    }
    let verb = "";
    for (let n = words.length; n > 0; n--) {
      const candidate = words.slice(0, n).join(" ");
      if (CATALOG.has(candidate)) { verb = candidate; break; }
    }
    if (verb) found.add(verb);
  }
  return found;
}

/** Bolded imperatives — the rules and anti-patterns a reader must not lose. */
export function rules(text) {
  return [...new Set(
    [...text.matchAll(/\*\*((?:Never|Always|Do not) [^*]{6,}?)\*\*/g)].map((m) => m[1]),
  )].sort();
}

/** A rule counts as covered when at least half its distinctive words appear. */
function coverage(rule, target) {
  const words = [...new Set(rule.toLowerCase().match(/[a-z-]{5,}/g) ?? [])]
    .filter((word) => !STOPWORDS.has(word));
  if (words.length === 0) return 1;
  return words.filter((word) => target.includes(word)).length / words.length;
}

function main([gaPath, previewPath]) {
  if (!gaPath || !previewPath) {
    console.error("usage: audit-capability-port.mjs <ga-path> <preview-file>");
    process.exitCode = 2;
    return;
  }
  const ga = read(gaPath);
  const preview = read(previewPath);
  const previewLower = preview.toLowerCase();

  const gaCommands = commands(ga);
  const previewCommands = commands(preview);
  // A preview command covers a GA one when it is the same or MORE specific.
  // The reverse does not hold: preview naming `maestro flow eval` says nothing
  // about whether `eval evaluator add` survived, and treating it as coverage
  // hides every subcommand behind its parent.
  const missingCommands = [...gaCommands].filter((command) =>
    ![...previewCommands].some((p) => p === command || p.startsWith(`${command} `)),
  ).sort();

  const gaRules = rules(ga);
  const scored = gaRules.map((rule) => [rule, coverage(rule, previewLower)]);
  const absent = scored.filter(([, score]) => score < 0.5);

  console.log(`commands   GA ${gaCommands.size}  preview ${previewCommands.size}  absent ${missingCommands.length}`);
  for (const command of missingCommands) console.log(`  - uip ${command}`);

  console.log(`rules      GA ${gaRules.length}  under-covered ${absent.length}`);
  for (const [rule, score] of absent) {
    console.log(`  - [${Math.round(score * 100)}%] ${rule.replace(/\s+/g, " ").slice(0, 96)}`);
  }

  const lines = (text) => text.split("\n").length;
  console.log(`size       GA ${lines(ga)} lines  preview ${lines(preview)} lines`);
}

if (import.meta.url === `file://${process.argv[1]}`) main(process.argv.slice(2));
