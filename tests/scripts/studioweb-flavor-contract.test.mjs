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

// The Flow skill audit (2026-09-07, verified live on alpha) found the same
// class of dead end for a handful of other commands: the Studio Web host has no
// `.uipx`, injects auth, runs debug through its own service and ships no
// python. Each of these is a command the agent copied straight out of a fenced
// block, so the guard scans fenced code in the composed Flow skill — prose may
// still name them when it says "never run".
const FLOW_SKILL = "uipath-maestro-flow";
const FORBIDDEN_FENCED_COMMANDS = [
  /^\s*(?:[A-Z_]+=\S+\s+)*uip login\b/,
  /^\s*uip solution resources refresh\b/,
  /^\s*uip solution upload\b/,
  /^\s*uip solution projects add\b/,
  /^\s*uip solution pack\b/,
  /^\s*uip solution deploy\b/,
  /^\s*(?:[A-Z_]+=\S+\s+)*uip maestro flow debug\b/,
  /^\s*uip maestro flow pack\b/,
  /^\s*uip tools update\b/,
  /^\s*python3?\b/,
  /\buuidgen\b/,
  /\buip [^\n]*\s--local\b/,
];
// Never legitimate anywhere in the Flow skill's studioweb text, prose included.
const FORBIDDEN_PROSE = ["CreateProjects", "crypto.randomUUID"];

function fencedLines(text) {
  const lines = [];
  let inFence = false;
  for (const line of text.split(/\r?\n/)) {
    if (/^\s*(```|~~~)/.test(line)) {
      inFence = !inFence;
      continue;
    }
    if (inFence) lines.push(line);
  }
  return lines;
}

function flowSkillViolations(output) {
  const root = join(output, FLOW_SKILL);
  const violations = [];
  for (const file of markdownFiles(root)) {
    const text = readFileSync(file, "utf8");
    const rel = relative(output, file);
    for (const line of fencedLines(text)) {
      for (const re of FORBIDDEN_FENCED_COMMANDS) {
        if (re.test(line)) violations.push(`${rel}: fenced \`${line.trim()}\``);
      }
    }
    for (const needle of FORBIDDEN_PROSE) {
      if (text.includes(needle)) violations.push(`${rel}: mentions ${needle}`);
    }
  }
  return violations.sort();
}

test("the built studioweb Flow skill never scripts a command the Studio Web host cannot run", (t) => {
  const output = mkdtempSync(join(tmpdir(), "studioweb-flow-contract-"));
  t.after(() => rmSync(output, { recursive: true, force: true }));
  materializeComposition(createCompositionPlan(REPO_ROOT, STUDIOWEB_ROOT), output);

  assert.deepEqual(
    flowSkillViolations(output),
    [],
    "studioweb Flow skill still scripts a Node-CLI-only command — wrap the passage in a marker block and add a sparse override under skill-flavors/studioweb/uipath-maestro-flow/",
  );
});

test("the default Flow skill keeps those commands (the Flow guard is not vacuous)", (t) => {
  const output = mkdtempSync(join(tmpdir(), "default-flow-contract-"));
  t.after(() => rmSync(output, { recursive: true, force: true }));
  materializeComposition(createDefaultPlan(REPO_ROOT), output);

  assert.ok(flowSkillViolations(output).length > 0);
});
