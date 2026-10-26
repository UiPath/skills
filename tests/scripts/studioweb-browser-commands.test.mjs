import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { browserSurface } from "../../scripts/build-uip-browser-catalog.mjs";
import {
  BROWSER_SNAPSHOT,
  ceilingDrift,
  commandSet,
  countUnallowed,
  extractVerbTokens,
  HOST_SERVED,
  mentionCommand,
  mentionKind,
  RATCHET,
  resolves,
  scanStudioweb,
  staleAllowEntries,
  unrunnableMentions,
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

test("a command the host serves counts as runnable, even when the bundle refuses it", () => {
  const browser = usableBrowserCommands(
    { verbs: ["case pack", "case validate"], unavailable: { "case pack": "needs the packager" } },
    { "case pack": "host", "rpa init": "host" },
  );

  assert.equal(resolves(tokens("uip case pack"), browser), true);
  assert.equal(resolves(tokens("uip rpa init MyProject"), browser), true);
  assert.equal(resolves(["rpa"], browser), true);
  assert.equal(resolves(tokens("uip rpa pack"), browser), false);
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

test("a mention is keyed on its command path, so rewording prose or an argument keeps the key", () => {
  const nodeVerbs = new Set(["login", "login status", "codedagent", "codedagent new"]);

  assert.equal(mentionCommand(tokens("uip login first"), nodeVerbs), "login");
  assert.equal(mentionCommand(tokens("uip login and have access to the audit service"), nodeVerbs), "login");
  assert.equal(mentionCommand(tokens("uip login status"), nodeVerbs), "login status");
  assert.equal(mentionCommand(tokens("uip codedagent new my-agent"), nodeVerbs), "codedagent new");
  assert.equal(mentionCommand(tokens("uip cicd run pipeline"), nodeVerbs), "cicd");
});

test("a stale path whose first token is also an English word is still reported", () => {
  const root = mkdtempSync(join(tmpdir(), "studioweb-browser-commands-test-"));
  try {
    mkdirSync(join(root, "s"));
    writeFileSync(
      join(root, "s", "a.md"),
      "Run `uip or eval list` or `uip is connectors probe`.\n",
    );
    const browser = commandSet(["or jobs list", "is connectors list"]);
    const nodeVerbs = new Set(["or", "or jobs list", "is", "is connectors", "is connectors list"]);

    assert.deepEqual(
      unrunnableMentions(root, browser, nodeVerbs).map((m) => m.command),
      ["or", "is connectors"],
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
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

test("ceiling drift reports counts over and under their ceiling, not equal ones", () => {
  assert.deepEqual(ceilingDrift({ s: { a: 3, b: 1, c: 2 } }, { s: { ceiling: { a: 2, b: 1, d: 1 } } }), [
    { skill: "s", command: "a", count: 3, ceiling: 2 },
    { skill: "s", command: "c", count: 2, ceiling: 0 },
    { skill: "s", command: "d", count: 0, ceiling: 1 },
  ]);
  assert.deepEqual(ceilingDrift({}, { t: { ceiling: { x: 1 } } }), [
    { skill: "t", command: "x", count: 0, ceiling: 1 },
  ]);
  assert.deepEqual(ceilingDrift({ u: { y: 2 } }, {}), [{ skill: "u", command: "y", count: 2, ceiling: 0 }]);
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

test("the host-served list names no command the bundle already runs", () => {
  const snapshot = JSON.parse(readFileSync(BROWSER_SNAPSHOT, "utf8"));
  const bundle = usableBrowserCommands(snapshot);
  assert.deepEqual(
    Object.keys(JSON.parse(readFileSync(HOST_SERVED, "utf8"))).filter((command) => bundle.leaves.has(command)),
    [],
    "the browser bundle now runs these itself — delete them from assets/uip-browser-host-served.json",
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

  // Below the ceiling passes: the scheduled refresh lowers it (see the script).
  const over = ceilingDrift(countUnallowed(mentions, ratchet), ratchet).filter((d) => d.count > d.ceiling);
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
});
