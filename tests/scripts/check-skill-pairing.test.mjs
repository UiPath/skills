/**
 * Tests for the skill pairing gate.
 *
 * The last test checks the committed manifest against the working tree. The
 * rest drive the two exported predicates with synthetic pairs.
 */
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  loadManifest,
  missingPaths,
  unpairedChanges,
} from "../../scripts/check-skill-pairing.mjs";

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");

const PAIRS = [
  { topic: "agent", ga: ["skills/a/agent.md", "skills/a/agent-plan.md"], preview: ["preview/a/agent.md"] },
  { topic: "hitl", ga: ["skills/a/hitl.md"], preview: ["preview/a/hitl.md"] },
];

test("a change to one side only is reported, with the other side named", () => {
  const findings = unpairedChanges(PAIRS, ["preview/a/agent.md"]);
  assert.equal(findings.length, 1);
  assert.deepEqual(findings[0], {
    topic: "agent",
    changed: "preview",
    missing: ["skills/a/agent.md", "skills/a/agent-plan.md"],
  });
});

test("the same holds in the other direction", () => {
  const findings = unpairedChanges(PAIRS, ["skills/a/agent.md"]);
  assert.deepEqual(findings.map((f) => [f.topic, f.changed]), [["agent", "ga"]]);
});

test("a change to both sides passes", () => {
  assert.deepEqual(unpairedChanges(PAIRS, ["preview/a/agent.md", "skills/a/agent.md"]), []);
});

test("touching any one file on a multi-file side satisfies that side", () => {
  assert.deepEqual(
    unpairedChanges(PAIRS, ["preview/a/agent.md", "skills/a/agent-plan.md"]),
    [],
  );
});

test("files belonging to no topic are ignored", () => {
  assert.deepEqual(unpairedChanges(PAIRS, ["README.md", "scripts/thing.mjs"]), []);
});

test("each topic is judged independently", () => {
  const findings = unpairedChanges(PAIRS, [
    "preview/a/agent.md",
    "skills/a/agent.md",
    "preview/a/hitl.md",
  ]);
  assert.deepEqual(findings.map((f) => f.topic), ["hitl"]);
});

test("an empty change set reports nothing", () => {
  assert.deepEqual(unpairedChanges(PAIRS, []), []);
});

test("a path that no longer exists is reported, so a rename cannot unpair a topic", () => {
  const dir = mkdtempSync(join(tmpdir(), "pairing-"));
  try {
    mkdirSync(join(dir, "preview", "a"), { recursive: true });
    writeFileSync(join(dir, "preview", "a", "hitl.md"), "# HITL");
    const problems = missingPaths([PAIRS[1]], dir);
    assert.equal(problems.length, 1);
    assert.match(problems[0], /hitl: ga path skills\/a\/hitl\.md does not exist/);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("the committed manifest matches the working tree", () => {
  const pairs = loadManifest(REPO);
  assert.ok(pairs.length > 0, "manifest lists no pairs");
  assert.deepEqual(missingPaths(pairs, REPO), []);
  for (const pair of pairs) {
    assert.ok(pair.topic, "a pair has no topic");
    assert.ok(pair.ga.length > 0, `${pair.topic}: no ga paths`);
    assert.ok(pair.preview.length > 0, `${pair.topic}: no preview paths`);
  }
});
