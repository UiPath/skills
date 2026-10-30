import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const SCRIPT = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "scripts", "audit-capability-port.mjs");

// The script's "run as CLI" guard compares import.meta.url with `file://` + argv[1],
// which only holds for POSIX paths. On Windows, present argv[1] in that shape.
const WINDOWS_ARGV = `process.argv[1] = "/" + process.argv[1].replaceAll("\\\\", "/");`;

function run(args) {
  const preload = process.platform === "win32" ? ["--import", `data:text/javascript,${encodeURIComponent(WINDOWS_ARGV)}`] : [];
  return spawnSync(process.execPath, [...preload, SCRIPT, ...args], { encoding: "utf8" });
}

function withDir(body) {
  const dir = mkdtempSync(join(tmpdir(), "acp-"));
  try {
    return body(dir);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

// The audit resolves verbs against the real CLI catalog, so pick verbs from it
// rather than hard-coding ones that may be renamed.
const { verbs } = await import("node:fs").then(({ readFileSync }) =>
  JSON.parse(readFileSync(new URL("../../assets/uip-catalog-snapshot.json", import.meta.url), "utf8")),
);
const leaf = verbs.filter((v) => v.split(" ").length === 2 && !verbs.some((o) => o.startsWith(`${v} `)));
const [verbA, verbB] = leaf;
const parent = verbs.find((v) => verbs.some((o) => o.startsWith(`${v} `)) && v.split(" ").length === 1);
const child = verbs.find((v) => v.startsWith(`${parent} `));

const { commands, rules } = await import(pathToFileURL(SCRIPT).href);

test("commands reads backticked spans and fenced lines, keeping only catalog verb paths", () => {
  const found = commands(
    [
      `Run \`uip ${verbA} --flag\` first.`,
      "",
      "```",
      `uip ${verbB} <arg>`,
      `  FOO=bar uip ${verbA}`,
      "```",
      "Prose mentioning uip nothing-real here is not a command.",
      "`uip not-a-real-verb`",
    ].join("\n"),
  );
  assert.deepEqual([...found].sort(), [verbA, verbB].sort());
});

test("commands trims example arguments back to the longest known verb path", () => {
  assert.deepEqual([...commands(`\`uip ${verbA} my-example-name\``)], [verbA]);
});

test("rules extracts bolded Never/Always/Do not imperatives, folding case and duplicates", () => {
  const found = rules(
    [
      "**Never push to main directly**",
      "**NEVER push to main directly**",
      "**Always run the tests**",
      "**Do NOT scaffold by hand**",
      "**What NOT to do**",
      "**Never x**",
      "**cannot do this thing**",
    ].join("\n"),
  );
  assert.equal(found.length, 3);
  assert.ok(found.includes("Never push to main directly"));
  assert.ok(found.includes("Always run the tests"));
  assert.ok(found.includes("Do NOT scaffold by hand"));
});

test("reports commands and rules the preview file dropped, and exits 0", () => {
  withDir((dir) => {
    const ga = join(dir, "ga.md");
    const preview = join(dir, "preview.md");
    writeFileSync(
      ga,
      [
        `Use \`uip ${verbA}\` and \`uip ${verbB}\`.`,
        "**Never delete the pipeline without a backup copy**",
        "**Always validate manifests before publishing**",
      ].join("\n"),
    );
    writeFileSync(
      preview,
      [`Use \`uip ${verbA}\`.`, "Always validate manifests before publishing."].join("\n"),
    );
    const result = run([ga, preview]);
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /^commands {3}GA 2 {2}preview 1 {2}absent 1$/m);
    assert.ok(result.stdout.includes(`  - uip ${verbB}`));
    assert.ok(!result.stdout.includes(`  - uip ${verbA}`));
    assert.match(result.stdout, /^rules {6}GA 2 {2}under-covered 1$/m);
    assert.match(result.stdout, /- \[0%\] Never delete the pipeline without a backup copy/);
    assert.ok(!result.stdout.includes("Always validate manifests"));
    assert.match(result.stdout, /^size {7}GA 3 lines {2}preview 2 lines$/m);
  });
});

test("a more specific preview command covers its GA parent, but not the reverse", () => {
  withDir((dir) => {
    const ga = join(dir, "ga.md");
    const preview = join(dir, "preview.md");
    writeFileSync(ga, `\`uip ${parent}\` and \`uip ${child}\``);
    writeFileSync(preview, `\`uip ${child}\``);
    const covered = run([ga, preview]);
    assert.equal(covered.status, 0, covered.stderr);
    assert.match(covered.stdout, /absent 0$/m);

    writeFileSync(ga, `\`uip ${child}\``);
    writeFileSync(preview, `\`uip ${parent}\``);
    const uncovered = run([ga, preview]);
    assert.match(uncovered.stdout, /absent 1$/m);
    assert.ok(uncovered.stdout.includes(`  - uip ${child}`));
  });
});

test("a directory as GA path reads only its .md files", () => {
  withDir((dir) => {
    const gaDir = join(dir, "ga");
    mkdirSync(gaDir);
    writeFileSync(join(gaDir, "a.md"), `\`uip ${verbA}\``);
    writeFileSync(join(gaDir, "b.md"), `\`uip ${verbB}\``);
    writeFileSync(join(gaDir, "c.txt"), `\`uip ${verbs.find((v) => v !== verbA && v !== verbB && v.includes(" "))}\``);
    const preview = join(dir, "preview.md");
    writeFileSync(preview, "nothing here");
    const result = run([gaDir, preview]);
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /^commands {3}GA 2 {2}preview 0 {2}absent 2$/m);
  });
});

test("missing arguments print usage and exit 2", () => {
  const result = run(["only-one"]);
  assert.equal(result.status, 2);
  assert.match(result.stderr, /usage: audit-capability-port\.mjs <ga-path> <preview-file>/);
});
