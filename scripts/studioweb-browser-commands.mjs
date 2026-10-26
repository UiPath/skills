#!/usr/bin/env node
/**
 * Match every `uip` command the built studioweb tree mentions against what the
 * browser bundle can actually run: assets/uip-browser-commands-snapshot.json
 * `verbs` minus its `unavailable` declarations. The snapshot lists registered
 * commands, and since cli#5399 a left-out command registers as present but
 * refusing (`case pack`), so a check against `verbs` alone would count it as
 * working.
 *
 * Studio Web also serves some commands itself, without the bundle (Autopilot's
 * subcommandInterceptors). Those are listed by hand in
 * assets/uip-browser-host-served.json, `{ command: source }`, since Autopilot
 * is private and the refresh cannot read it, and count as runnable even when
 * the bundle refuses them.
 *
 * A mention that does not resolve to a usable browser command is checked
 * against tests/scripts/studioweb-browser-commands.json, per skill:
 *   - `allow`: `{ file, command, reason }` entries — prose and deliberate
 *     Node-only notes. A regex cannot tell an instruction from a mention, so a
 *     human says which is which. An entry covers every mention of `command`
 *     in `file` (relative to the skill).
 *   - `ceiling`: the count of every other such mention, per command — today's
 *     debt, driven down per skill. Above it, the test fails. Below it, the
 *     test passes, so a flavor fix needs no edit to this root-owned file; the
 *     scheduled refresh (`--lower-ceiling`) lowers the ceiling to the count.
 *
 * Known limit: this reads what the flavor says, not what an agent executes.
 * Only `.md` files are scanned.
 *
 * Usage:
 *   node scripts/studioweb-browser-commands.mjs                  # report
 *   node scripts/studioweb-browser-commands.mjs --write-ceiling  # reset ceilings to today's counts
 *   node scripts/studioweb-browser-commands.mjs --lower-ceiling  # only lower them (the scheduled refresh)
 */
import { mkdtempSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

import { createCompositionPlan, materializeComposition } from "./compose-skill-flavor.mjs";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const BROWSER_SNAPSHOT = join(REPO_ROOT, "assets", "uip-browser-commands-snapshot.json");
export const HOST_SERVED = join(REPO_ROOT, "assets", "uip-browser-host-served.json");
export const NODE_CATALOG = join(REPO_ROOT, "assets", "uip-catalog-snapshot.json");
export const RATCHET = join(REPO_ROOT, "tests", "scripts", "studioweb-browser-commands.json");
const STUDIOWEB_ROOT = join(REPO_ROOT, "skill-flavors", "studioweb");

// Mention extraction mirrors scripts/check-skill-verbs.py so the two checkers
// read the same tokens from the same line. Keep them in step.
const UIP_LINE = /\buip(\s+[^\n`]*)?/g;
const PLACEHOLDER = /^(<.+?>(\.\w+)?|\[.+?\](\.\w+)?|\$\{?[A-Za-z_]\w*\}?|\.\.\.|\*+)$/;
const FLAG = /^-{1,2}[A-Za-z]/;
const SHELL_STOP = new Set(["|", "||", "&&", ";", ">", ">>", "<", "2>", "2>&1"]);
const TRAILING_PUNCT = /[`,.;:)\]"'\\]+$/;
const LEADING_PUNCT = /^[`(["']+/;
const PROSE_NOISE = new Set([
  "CLI", "is", "are", "was", "were", "be", "been", "being",
  "a", "the", "an", "and", "or", "to", "for", "with",
  "if", "when", "while", "from", "into", "on", "in", "at", "by", "of",
  "commands", "command", "version", "tool",
]);

/** The literal command tokens after `uip`, up to the first flag, placeholder or value. */
export function extractVerbTokens(tail) {
  const verb = [];
  for (const raw of tail.trim().split(/\s+/)) {
    const tok = raw.replace(TRAILING_PUNCT, "").replace(LEADING_PUNCT, "");
    if (!tok) break;
    if (verb.length === 0 && !/^[\p{L}\p{N}_]/u.test(tok)) break;
    if (FLAG.test(tok) || SHELL_STOP.has(tok) || tok.startsWith("#")) break;
    if (PLACEHOLDER.test(tok)) break;
    if (/[/={}"'.]/.test(tok)) break;
    if (/^\d+$/.test(tok.replace(/[-_]/g, ""))) break;
    verb.push(tok);
  }
  return verb;
}

/**
 * A command set: its runnable commands and every group above them. Tokens
 * resolve when they name a group exactly, or when a prefix of them names a
 * command (the rest are its arguments).
 */
export function commandSet(commands) {
  const leaves = new Set(commands);
  const groups = new Set();
  for (const command of leaves) {
    const words = command.split(" ");
    for (let n = 1; n < words.length; n++) groups.add(words.slice(0, n).join(" "));
  }
  return { leaves, groups };
}

export function resolves(tokens, { leaves, groups }) {
  if (groups.has(tokens.join(" "))) return true;
  for (let n = 1; n <= tokens.length; n++) {
    if (leaves.has(tokens.slice(0, n).join(" "))) return true;
  }
  return false;
}

/**
 * What Studio Web runs: the bundle's registered commands minus the unavailable
 * ones, plus the commands the host serves itself.
 */
export function usableBrowserCommands(snapshot, hostServed = {}) {
  const refusing = new Set(Object.keys(snapshot.unavailable ?? {}));
  return commandSet([...snapshot.verbs.filter((verb) => !refusing.has(verb)), ...Object.keys(hostServed)]);
}

/**
 * Label a mention the browser cannot run. The Node catalog lists groups and
 * commands alike (`login` is both), so take the longest prefix it knows: when
 * that prefix is also a browser group, the mention is a stale path inside a
 * tool the browser has (`maestro case instance list`), not a Node-only command.
 */
export function mentionKind(tokens, browser, nodeVerbs) {
  for (let n = tokens.length; n > 0; n--) {
    const prefix = tokens.slice(0, n).join(" ");
    if (nodeVerbs.has(prefix)) return browser.groups.has(prefix) ? "unknown" : "node-only";
  }
  return "unknown";
}

function markdownFiles(root) {
  const out = [];
  const walk = (dir) => {
    for (const entry of readdirSync(dir).sort()) {
      const full = join(dir, entry);
      if (statSync(full).isDirectory()) walk(full);
      else if (entry.endsWith(".md")) out.push(full);
    }
  };
  walk(root);
  return out;
}

/**
 * Every mention in `treeRoot` (one directory per skill) that the browser
 * bundle cannot run: `{ skill, file, line, command, kind, text }`, where
 * `kind` is `node-only` when the Node CLI has it and `unknown` when neither does.
 */
export function unrunnableMentions(treeRoot, browser, nodeVerbs) {
  const out = [];
  for (const path of markdownFiles(treeRoot)) {
    const [skill, ...rest] = relative(treeRoot, path).split(sep);
    const file = rest.join("/");
    readFileSync(path, "utf8")
      .split("\n")
      .forEach((text, index) => {
        for (const match of text.matchAll(UIP_LINE)) {
          const tokens = extractVerbTokens(match[1] ?? "");
          if (tokens.length === 0 || resolves(tokens, browser)) continue;
          const kind = mentionKind(tokens, browser, nodeVerbs);
          if (kind === "unknown" && PROSE_NOISE.has(tokens[0])) continue;
          out.push({ skill, file, line: index + 1, command: tokens.join(" "), kind, text: text.trim() });
        }
      });
  }
  return out;
}

/** Per skill, per command: how many mentions the allowlist does not cover. */
export function countUnallowed(mentions, ratchet) {
  const counts = {};
  for (const mention of mentions) {
    const allow = ratchet[mention.skill]?.allow ?? [];
    if (allow.some((entry) => entry.file === mention.file && entry.command === mention.command)) continue;
    const skill = (counts[mention.skill] ??= {});
    skill[mention.command] = (skill[mention.command] ?? 0) + 1;
  }
  return counts;
}

/** Allowlist entries that match no mention any more. */
export function staleAllowEntries(mentions, ratchet) {
  const stale = [];
  for (const [skill, { allow = [] }] of Object.entries(ratchet)) {
    for (const entry of allow) {
      const used = mentions.some(
        (m) => m.skill === skill && m.file === entry.file && m.command === entry.command,
      );
      if (!used) stale.push({ skill, ...entry });
    }
  }
  return stale;
}

/** Commands whose count differs from their ceiling: `{ skill, command, count, ceiling }`. */
export function ceilingDrift(counts, ratchet) {
  const drift = [];
  const skills = new Set([...Object.keys(counts), ...Object.keys(ratchet)]);
  for (const skill of [...skills].sort()) {
    const ceiling = ratchet[skill]?.ceiling ?? {};
    const count = counts[skill] ?? {};
    const commands = new Set([...Object.keys(ceiling), ...Object.keys(count)]);
    for (const command of [...commands].sort()) {
      const c = count[command] ?? 0;
      const max = ceiling[command] ?? 0;
      if (c !== max) drift.push({ skill, command, count: c, ceiling: max });
    }
  }
  return drift;
}

const readJson = (file) => JSON.parse(readFileSync(file, "utf8"));

/** Build the studioweb tree into a temp dir and scan it. */
export function scanStudioweb() {
  const output = mkdtempSync(join(tmpdir(), "studioweb-browser-commands-"));
  try {
    materializeComposition(createCompositionPlan(REPO_ROOT, STUDIOWEB_ROOT), output);
    return unrunnableMentions(
      output,
      usableBrowserCommands(readJson(BROWSER_SNAPSHOT), readJson(HOST_SERVED)),
      new Set(readJson(NODE_CATALOG).verbs),
    );
  } finally {
    rmSync(output, { recursive: true, force: true });
  }
}

/**
 * Ceilings reset to `counts`, allowlists kept, skills sorted. With
 * `lowerOnly`, a ceiling never rises: a count above it stays a failure for a
 * human to look at.
 */
export function withCeilings(ratchet, counts, { lowerOnly = false } = {}) {
  const skills = new Set([...Object.keys(ratchet), ...Object.keys(counts)]);
  const out = {};
  for (const skill of [...skills].sort()) {
    const previous = ratchet[skill]?.ceiling ?? {};
    const ceiling = {};
    for (const [command, count] of Object.entries(counts[skill] ?? {}).sort(([a], [b]) => a.localeCompare(b))) {
      const max = lowerOnly ? Math.min(count, previous[command] ?? 0) : count;
      if (max > 0) ceiling[command] = max;
    }
    out[skill] = { allow: ratchet[skill]?.allow ?? [], ceiling };
  }
  return out;
}

function main(argv) {
  const mentions = scanStudioweb();
  const ratchet = readJson(RATCHET);
  const counts = countUnallowed(mentions, ratchet);
  const write = argv.includes("--write-ceiling");
  if (write || argv.includes("--lower-ceiling")) {
    writeFileSync(RATCHET, `${JSON.stringify(withCeilings(ratchet, counts, { lowerOnly: !write }), null, 2)}\n`);
    process.stdout.write(`Wrote ${RATCHET}.\n`);
    return;
  }
  for (const m of mentions) {
    process.stdout.write(`${m.skill}/${m.file}:${m.line}: [${m.kind}] uip ${m.command}\n`);
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2));
}
