/**
 * Pairing gate for topics maintained in both the GA and preview Flow skills.
 *
 * `skill-pairing.json` lists topics with a `ga` and a `preview` side. While
 * preview is not yet GA both sides are maintained, so a change to one side and
 * not the other is reported.
 *
 *   node scripts/check-skill-pairing.mjs <changed-file>...
 *   node scripts/check-skill-pairing.mjs --changed-from <file-with-one-path-per-line>
 *
 * Prints one line per unpaired topic and exits non-zero if there are any. Files
 * belonging to no topic are ignored. Every listed path must exist, so a rename
 * on either side fails here rather than silently unpairing a topic.
 */
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const MANIFEST = "skill-pairing.json";

export function loadManifest(repo = REPO) {
  const doc = JSON.parse(readFileSync(resolve(repo, MANIFEST), "utf8"));
  return doc.pairs;
}

/** Topics whose listed paths no longer exist — a rename or deletion. */
export function missingPaths(pairs, repo = REPO) {
  const problems = [];
  for (const pair of pairs) {
    for (const side of ["ga", "preview"]) {
      for (const path of pair[side]) {
        if (!existsSync(resolve(repo, path))) {
          problems.push(`${pair.topic}: ${side} path ${path} does not exist`);
        }
      }
    }
  }
  return problems;
}

/**
 * Topics where one side changed and the other did not.
 *
 * Returns `{ topic, changed, missing }` per finding: `changed` is the side the
 * PR touched, `missing` the paths on the other side it did not.
 */
export function unpairedChanges(pairs, changedFiles) {
  const changed = new Set(changedFiles);
  const findings = [];
  for (const pair of pairs) {
    const touched = {
      ga: pair.ga.filter((path) => changed.has(path)),
      preview: pair.preview.filter((path) => changed.has(path)),
    };
    if (touched.ga.length > 0 && touched.preview.length === 0) {
      findings.push({ topic: pair.topic, changed: "ga", missing: pair.preview });
    } else if (touched.preview.length > 0 && touched.ga.length === 0) {
      findings.push({ topic: pair.topic, changed: "preview", missing: pair.ga });
    }
  }
  return findings;
}

function main(changedFiles) {
  const pairs = loadManifest();

  const stale = missingPaths(pairs);
  if (stale.length > 0) {
    for (const problem of stale) console.error(`${MANIFEST}: ${problem}`);
    console.error(`\ncheck-skill-pairing: ${MANIFEST} is stale`);
    process.exitCode = 1;
    return;
  }

  if (changedFiles.length === 0) {
    console.log(`check-skill-pairing: ${pairs.length} paired topics, no changed files given`);
    return;
  }

  const findings = unpairedChanges(pairs, changedFiles);
  if (findings.length === 0) {
    console.log(`check-skill-pairing: OK (${pairs.length} paired topics)`);
    return;
  }
  for (const { topic, changed, missing } of findings) {
    console.error(
      `${topic}: changed on the ${changed} side only; `
        + `the other side is ${missing.join(", ")}`,
    );
  }
  console.error(
    `\ncheck-skill-pairing: ${findings.length} topic(s) changed on one side only.`
      + "\nUpdate the other side, or add the `single-tree-ok` label if the change"
      + " genuinely belongs to one tree.",
  );
  process.exitCode = 1;
}

/**
 * `--changed-from <file>` reads one path per line, so a caller does not have to
 * get shell word-splitting right for a list that can be long or empty.
 */
function changedFrom(argv) {
  const flag = argv.indexOf("--changed-from");
  if (flag < 0) return argv;
  const path = argv[flag + 1];
  if (!path) {
    console.error("check-skill-pairing: --changed-from needs a file path");
    process.exitCode = 2;
    return null;
  }
  if (!existsSync(path)) return [];
  return readFileSync(path, "utf8").split("\n").map((line) => line.trim()).filter(Boolean);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const changed = changedFrom(process.argv.slice(2));
  if (changed !== null) main(changed);
}
