import assert from "node:assert/strict";
import { mkdtempSync, readdirSync, readFileSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, relative, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  createCompositionPlan,
  createDefaultPlan,
  materializeComposition,
} from "../../scripts/compose-skill-flavor.mjs";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const STUDIOWEB_ROOT = join(REPO_ROOT, "skill-flavors", "studioweb");

// Studio Web works on one open solution, already scaffolded as the workspace
// root, and its host refuses `uip solution init`. Guidance that tells the agent
// to run it there sends every build down a dead end (coder_eval studio-web
// nightly 13250238: 98 tasks). The studioweb flavor must therefore never
// contain the command; every canonical mention sits in a marker block with a
// sparse studioweb replacement.
const FORBIDDEN = "uip solution init";

function markdownFiles(root) {
  const out = [];
  const walk = (dir) => {
    for (const entry of readdirSync(dir)) {
      const full = join(dir, entry);
      if (statSync(full).isDirectory()) walk(full);
      else if (entry.endsWith(".md")) out.push(full);
    }
  };
  walk(root);
  return out;
}

function filesMentioning(root, needle) {
  return markdownFiles(root)
    .filter((file) => readFileSync(file, "utf8").includes(needle))
    .map((file) => relative(root, file))
    .sort();
}

test("the built studioweb flavor never tells the agent to run `uip solution init`", (t) => {
  const output = mkdtempSync(join(tmpdir(), "studioweb-flavor-contract-"));
  t.after(() => rmSync(output, { recursive: true, force: true }));
  materializeComposition(createCompositionPlan(REPO_ROOT, STUDIOWEB_ROOT), output);

  assert.deepEqual(
    filesMentioning(output, FORBIDDEN),
    [],
    `studioweb flavor still mentions \`${FORBIDDEN}\` — wrap the passage in a marker block and add a sparse override under skill-flavors/studioweb/`,
  );
});

test("the default flavor keeps `uip solution init` (the guard is not vacuous)", (t) => {
  const output = mkdtempSync(join(tmpdir(), "default-flavor-contract-"));
  t.after(() => rmSync(output, { recursive: true, force: true }));
  materializeComposition(createDefaultPlan(REPO_ROOT), output);

  assert.ok(filesMentioning(output, FORBIDDEN).length > 0);
});
