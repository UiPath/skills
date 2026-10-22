import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { browserSurface } from "../../scripts/build-uip-browser-catalog.mjs";
import {
  BROWSER_SNAPSHOT,
  ceilingDrift,
  commandSet,
  countUnallowed,
  extractVerbTokens,
  mentionKind,
  RATCHET,
  resolves,
  scanStudioweb,
  staleAllowEntries,
  usableBrowserCommands,
  withCeilings,
} from "../../scripts/studioweb-browser-commands.mjs";

// The studioweb flavor told the agent to run `uip case validate` and then
// `uip login`, and the browser bundle Studio Web embeds shipped neither. Both
// were found by hand. This check matches every `uip` mention in the built
// studioweb tree against what the bundle runs, so the next one is found by CI.
// See scripts/studioweb-browser-commands.mjs for the rules and its limits.

const tokens = (line) => extractVerbTokens(line.replace(/^uip/, ""));

test("a command the bundle registers but refuses does not count as runnable", () => {
  const browser = usableBrowserCommands({
    verbs: ["case pack", "case validate", "case debug", "maestro case pack"],
    unavailable: { "case pack": "needs the packager", "case debug": "needs the runtime" },
  });

  assert.equal(resolves(tokens("uip case validate caseplan"), browser), true);
  assert.equal(resolves(tokens("uip case"), browser), true);
  assert.equal(resolves(tokens("uip case pack"), browser), false);
  assert.equal(resolves(tokens("uip case pack ./out"), browser), false);
  assert.equal(resolves(tokens("uip login"), browser), false);
});

test("a group with only unavailable commands under it does not count as runnable", () => {
  const browser = usableBrowserCommands({
    verbs: ["case pack", "case validate"],
    unavailable: { "case pack": "needs the packager" },
  });
  assert.equal(resolves(["case"], browser), true);

  const empty = usableBrowserCommands({ verbs: ["rpa pack"], unavailable: { "rpa pack": "x" } });
  assert.equal(resolves(["rpa"], empty), false);
});

test("the refresh writes each tool's unavailable keys as full command paths", () => {
  const surface = browserSurface(
    {
      stable: {
        "@uipath/case-tool": ["case pack", "case validate"],
        "@uipath/maestro-tool": ["maestro case pack"],
      },
    },
    {
      "@uipath/case-tool": { unavailable: { pack: "needs the packager" } },
      "@uipath/maestro-tool": { unavailable: { "case pack": "needs the packager" } },
      "@uipath/orchestrator-tool": { compatible: true },
    },
  );

  assert.deepEqual(surface.verbs, ["case pack", "case validate", "maestro case pack"]);
  assert.deepEqual(surface.unavailable, {
    "case pack": "needs the packager",
    "maestro case pack": "needs the packager",
  });
});

test("the refresh fails on an unavailable command the snapshot does not register", () => {
  assert.throws(
    () =>
      browserSurface(
        { stable: { "@uipath/case-tool": ["case validate"] } },
        { "@uipath/case-tool": { unavailable: { pack: "needs the packager" } } },
      ),
    /declares 'case pack' unavailable but the snapshot does not register it/,
  );
});

test("a mention is node-only when the Node CLI has it, unknown when it is a stale path", () => {
  const browser = commandSet(["maestro case instances list", "case validate"]);
  const nodeVerbs = new Set(["login", "login status", "maestro", "maestro case", "solution", "solution pack"]);

  assert.equal(mentionKind(tokens("uip login first"), browser, nodeVerbs), "node-only");
  assert.equal(mentionKind(tokens("uip solution pack"), browser, nodeVerbs), "node-only");
  assert.equal(mentionKind(tokens("uip maestro case instance list"), browser, nodeVerbs), "unknown");
  assert.equal(mentionKind(tokens("uip cicd"), browser, nodeVerbs), "unknown");
});

test("an allowlist entry covers its command in its file only", () => {
  const mentions = [
    { skill: "s", file: "a.md", command: "login" },
    { skill: "s", file: "a.md", command: "login" },
    { skill: "s", file: "b.md", command: "login" },
    { skill: "s", file: "a.md", command: "rpa pack" },
  ];
  const ratchet = { s: { allow: [{ file: "a.md", command: "login", reason: "prose" }], ceiling: {} } };

  assert.deepEqual(countUnallowed(mentions, ratchet), { s: { login: 1, "rpa pack": 1 } });
  assert.deepEqual(staleAllowEntries(mentions, ratchet), []);
  assert.equal(staleAllowEntries([], ratchet).length, 1);
});

test("the scheduled refresh lowers a ceiling but never raises one", () => {
  const ratchet = { s: { allow: [], ceiling: { login: 3, "rpa pack": 2, "case pack": 1 } } };
  const counts = { s: { login: 1, "rpa pack": 5, "solution pack": 4 } };

  assert.deepEqual(withCeilings(ratchet, counts, { lowerOnly: true }).s.ceiling, { login: 1, "rpa pack": 2 });
  assert.deepEqual(withCeilings(ratchet, counts).s.ceiling, { login: 1, "rpa pack": 5, "solution pack": 4 });
});

test("the vendored browser snapshot registers every command it declares unavailable", () => {
  const snapshot = JSON.parse(readFileSync(BROWSER_SNAPSHOT, "utf8"));
  const verbs = new Set(snapshot.verbs);
  assert.ok(snapshot.verbs.length > 0);
  assert.deepEqual(
    Object.keys(snapshot.unavailable).filter((path) => !verbs.has(path)),
    [],
  );
});

test("the built studioweb flavor mentions no new command the browser bundle cannot run", () => {
  const mentions = scanStudioweb();
  const ratchet = JSON.parse(readFileSync(RATCHET, "utf8"));

  const stale = staleAllowEntries(mentions, ratchet);
  assert.deepEqual(
    stale,
    [],
    "allowlist entries in tests/scripts/studioweb-browser-commands.json match no mention any more — delete them",
  );

  const drift = ceilingDrift(countUnallowed(mentions, ratchet), ratchet);
  const over = drift.filter((d) => d.count > d.ceiling);
  const under = drift.filter((d) => d.count < d.ceiling);
  const where = ({ skill, command }) =>
    mentions
      .filter((m) => m.skill === skill && m.command === command)
      .map((m) => `      ${m.skill}/${m.file}:${m.line} [${m.kind}]`);

  assert.deepEqual(
    over.map(({ skill, command, count, ceiling }) => `${skill}: uip ${command} (${count} > ${ceiling})`),
    [],
    [
      "The studioweb flavor mentions a command the browser bundle does not run (Node-only, unavailable, or stale):",
      ...over.flatMap((d) => [`  ${d.skill}: uip ${d.command} — ${d.count} mentions, ceiling ${d.ceiling}`, ...where(d)]),
      "Fix the guidance for Studio Web. If the mention is prose or a deliberate Node-only note, add",
      "{ file, command, reason } to that skill's `allow` in tests/scripts/studioweb-browser-commands.json.",
    ].join("\n"),
  );

  assert.deepEqual(
    under.map(({ skill, command, count, ceiling }) => `${skill}: uip ${command} (${count} < ${ceiling})`),
    [],
    "Fewer mentions than the ceiling: lower it so the fix stays fixed — run\n" +
      "  node scripts/studioweb-browser-commands.mjs --write-ceiling",
  );
});
