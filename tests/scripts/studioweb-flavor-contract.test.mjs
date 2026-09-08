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
//
// `defaultMustMatch: false` marks a needle the canonical flavor legitimately
// never scripts, so its non-vacuity cannot be asserted against `default`:
// canonical names `uip tools update` only in prose, never scripts a kindless
// `solution resources list`, and never mentioned `CreateProjects` at all (that
// one only ever appeared in the pre-audit studioweb overrides, which is exactly
// the regression it guards).
const FLOW_SKILL = "uipath-maestro-flow";
const FORBIDDEN_FENCED_COMMANDS = [
  { needle: /^\s*(?:[A-Z_]+=\S+\s+)*uip login\b/, label: "uip login" },
  { needle: /^\s*uip solution resources refresh\b/, label: "uip solution resources refresh" },
  { needle: /^\s*uip solution upload\b/, label: "uip solution upload" },
  { needle: /^\s*uip solution projects add\b/, label: "uip solution projects add" },
  { needle: /^\s*uip solution pack\b/, label: "uip solution pack" },
  { needle: /^\s*uip solution deploy\b/, label: "uip solution deploy" },
  { needle: /^\s*(?:[A-Z_]+=\S+\s+)*uip maestro flow debug\b/, label: "uip maestro flow debug" },
  { needle: /^\s*uip maestro flow pack\b/, label: "uip maestro flow pack" },
  { needle: /^\s*uip tools update\b/, label: "uip tools update", defaultMustMatch: false },
  { needle: /^\s*python3?\b/, label: "python" },
  { needle: /\buuidgen\b/, label: "uuidgen" },
  { needle: /\buip [^\n]*\s--local\b/, label: "--local" },
  // A kindless `solution resources list` is not served by the host (`--source`
  // defaults to `all`, and the host serves remote/all only with `--kind`), so it
  // falls through to the browser bundle and needs a `.uipx` like `--local` does.
  {
    needle: /^\s*uip solution resources list\b(?![^\n]*(?:--kind|--source[= ]local))/,
    label: "uip solution resources list without --kind",
    defaultMustMatch: false,
  },
  // Studio Web's flow file is always `new.flow`; `<ProjectName>.flow` is the
  // Node-CLI naming and matches nothing on disk here.
  { needle: /<ProjectName>\.flow/, label: "<ProjectName>.flow" },
];
// Never legitimate anywhere in the Flow skill's studioweb text, prose included.
const FORBIDDEN_PROSE = [
  { needle: "CreateProjects", defaultMustMatch: false },
  { needle: "crypto.randomUUID" },
];

/**
 * Lines inside fenced code blocks. A fence closes only on the same character
 * repeated at least as many times as the opening run, so an inner ``` inside a
 * ````markdown example does not flip the state and silently un-scan the rest of
 * the file.
 */
function fencedLines(text) {
  const lines = [];
  let fence = null;
  for (const line of text.split(/\r?\n/)) {
    const match = /^\s*(`{3,}|~{3,})/.exec(line);
    if (match) {
      if (fence === null) fence = match[1];
      else if (match[1][0] === fence[0] && match[1].length >= fence.length) fence = null;
      continue;
    }
    if (fence !== null) lines.push(line);
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
      for (const { needle, label } of FORBIDDEN_FENCED_COMMANDS) {
        if (needle.test(line)) violations.push(`${rel}: ${label} in fenced \`${line.trim()}\``);
      }
    }
    for (const { needle } of FORBIDDEN_PROSE) {
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

test("every Flow needle still fires on the default flavor (no guard goes silently dead)", (t) => {
  const output = mkdtempSync(join(tmpdir(), "default-flow-contract-"));
  t.after(() => rmSync(output, { recursive: true, force: true }));
  materializeComposition(createDefaultPlan(REPO_ROOT), output);

  const violations = flowSkillViolations(output);
  const dead = [
    ...FORBIDDEN_FENCED_COMMANDS,
    ...FORBIDDEN_PROSE.map((entry) => ({ ...entry, label: entry.needle })),
  ]
    .filter((entry) => entry.defaultMustMatch !== false)
    .filter((entry) => !violations.some((v) => v.includes(String(entry.label))))
    .map((entry) => String(entry.label));

  assert.deepEqual(
    dead,
    [],
    "these needles no longer match anything in the default Flow skill, so they guard nothing — retire them or fix the pattern",
  );
});
