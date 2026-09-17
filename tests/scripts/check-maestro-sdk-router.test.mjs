/**
 * Tests for the Maestro router gate.
 *
 * Each negative case builds a synthetic skill with exactly one defect and
 * asserts the gate reports it. The last test runs the gate over the real
 * `preview/skills/uipath-maestro-*` guides and asserts they are clean.
 */
import assert from "node:assert/strict";
import { existsSync, readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  MAX_SECTION_BYTES,
  lintSkill,
  readSkill,
  routerRows,
} from "../../scripts/check-maestro-sdk-router.mjs";

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");

/** A minimal one-row skill. `overrides` replaces or deletes files by relative path. */
function syntheticSkill(overrides = {}) {
  const files = new Map([
    ["SKILL.md", [
      "# Flow skill",
      "",
      "## Supported node types",
      "",
      "| Surface | Node type | Builder | Section | Reference | Example |",
      "|---|---|---|---|---|---|",
      "| Script | `core.action.script` | `script(...)` | [Script](#script) "
        + "| [script.md](references/script.md) | `examples/Demo.flow.ts` |",
      "",
      "## Script",
      "Run a script.",
      "",
      "## Final evidence",
      "Run the gates.",
    ].join("\n")],
    ["references/script.md", "# Script\n\n[Router](../SKILL.md#script)"],
    ["examples/Demo.flow.ts", "script({ code: 'return 1;' })"],
  ]);
  for (const [path, body] of Object.entries(overrides)) {
    if (body === null) files.delete(path);
    else files.set(path, body);
  }
  return files;
}

test("accepts a coherent one-row skill", () => {
  assert.deepEqual(lintSkill(syntheticSkill()), []);
});

test("rejects a Section that does not target an H2 in the file", () => {
  const files = syntheticSkill();
  files.set("SKILL.md", files.get("SKILL.md").replace("[Script](#script)", "[Script](#nope)"));
  assert.match(lintSkill(files).join("\n"), /no H2 matches #nope/);
});

test("rejects a Section that points at another file instead of a governed H2", () => {
  const files = syntheticSkill();
  files.set(
    "SKILL.md",
    files.get("SKILL.md").replace("[Script](#script)", "[Script](references/script.md)"),
  );
  assert.match(lintSkill(files).join("\n"), /Section must link a governed H2/);
});

test("rejects a row with no node type", () => {
  const files = syntheticSkill();
  files.set("SKILL.md", files.get("SKILL.md").replace("`core.action.script`", ""));
  assert.match(lintSkill(files).join("\n"), /row has no node type/);
});

test("accepts a node type cell naming a family and its variants", () => {
  // Several real rows name a family plus its variants.
  const files = syntheticSkill();
  files.set(
    "SKILL.md",
    files.get("SKILL.md").replace(
      "`core.action.script`",
      "`uipath.connector.<key>.<action>` (every op: `uipath.connector.x.*`)",
    ),
  );
  assert.deepEqual(lintSkill(files), []);
});

test("rejects a Reference that does not exist", () => {
  assert.match(
    lintSkill(syntheticSkill({ "references/script.md": null })).join("\n"),
    /Reference references\/script\.md does not exist/,
  );
});

test("rejects an Example that does not exist", () => {
  assert.match(
    lintSkill(syntheticSkill({ "examples/Demo.flow.ts": null })).join("\n"),
    /Example examples\/Demo\.flow\.ts does not exist/,
  );
});

test("rejects an Example that does not demonstrate its surface", () => {
  assert.match(
    lintSkill(syntheticSkill({ "examples/Demo.flow.ts": "transform({})" })).join("\n"),
    /does not demonstrate Script/,
  );
});

test("rejects an Example outside examples/", () => {
  const files = syntheticSkill({ "Demo.flow.ts": "script({ code: 'return 1;' })" });
  files.set("SKILL.md", files.get("SKILL.md").replace("`examples/Demo.flow.ts`", "`Demo.flow.ts`"));
  assert.match(lintSkill(files).join("\n"), /must be one examples\/<file>\.flow\.ts path/);
});

test("rejects an orphaned reference", () => {
  assert.match(
    lintSkill(syntheticSkill({ "references/stray.md": "# Stray" })).join("\n"),
    /references\/stray\.md: no router row points at it/,
  );
});

test("exempts the cross-cutting guides from needing a row", () => {
  assert.deepEqual(lintSkill(syntheticSkill({ "references/CLI-LOOP.md": "# Loop" })), []);
});

test("rejects a broken relative link", () => {
  assert.match(
    lintSkill(syntheticSkill({ "references/script.md": "# Script\n\n[gone](../nope.md)" })).join("\n"),
    /link \.\.\/nope\.md does not resolve/,
  );
});

test("rejects a link to an anchor the target does not have", () => {
  assert.match(
    lintSkill(syntheticSkill({
      "references/script.md": "# Script\n\n[Router](../SKILL.md#not-a-section)",
    })).join("\n"),
    /has no matching H2/,
  );
});

test("rejects a governed section over the byte budget", () => {
  const files = syntheticSkill();
  files.set(
    "SKILL.md",
    files.get("SKILL.md").replace("Run a script.", "x".repeat(MAX_SECTION_BYTES + 1)),
  );
  const problem = lintSkill(files).find((p) => p.includes("bytes"));
  assert.match(problem, new RegExp(`is \\d+ bytes \\(~\\d+ tok\\); maximum is ${MAX_SECTION_BYTES}`));
});

test("accepts a section of many short lines that a line cap would reject", () => {
  const files = syntheticSkill();
  const body = Array.from({ length: 60 }, (_, i) => `line ${i + 1}`).join("\n");
  files.set("SKILL.md", files.get("SKILL.md").replace("Run a script.", body));
  assert.deepEqual(lintSkill(files), []);
});

test("reports a missing router table rather than throwing", () => {
  const { problems, rows } = routerRows("# Flow skill\n\nNo table here.\n");
  assert.deepEqual(rows, []);
  assert.match(problems.join("\n"), /missing `## Supported node types`/);
});

test("the real Maestro guides are coherent", () => {
  const root = join(REPO, "preview", "skills");
  const dirs = readdirSync(root)
    .filter((name) => name.startsWith("uipath-maestro-"))
    .map((name) => join(root, name))
    .filter((dir) => existsSync(join(dir, "SKILL.md")));
  assert.ok(dirs.length > 0, "no Maestro skills found");

  let routed = 0;
  for (const dir of dirs) {
    const files = readSkill(dir);
    // Case and BPMN route through prose and their own `## API index`.
    if (!files.get("SKILL.md").includes("## Supported node types")) continue;
    routed += 1;
    assert.deepEqual(lintSkill(files), [], `${dir} has router problems`);
  }
  assert.ok(routed > 0, "no skill with a router table was checked");
});
