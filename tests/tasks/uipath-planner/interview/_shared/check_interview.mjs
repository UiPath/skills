#!/usr/bin/env node
// Graders for the interview tasks. Run in the task's sandbox (the working directory); exit 0 pass, 1 fail,
// 2 usage or setup error, with one line per failure.
//
//   absent <regex>                        no file whose path matches, outside dot-folders: an SDD is
//                                         'sdd(\.draft)?\.md$', a genome '-genome\.md$'
//   strict                               the top-level `*-genome.md` passes check-genome.mjs --profile strict,
//                                         at the level its first line declares
//   line <regex>                          some line of a genome file (any depth) matches, case-insensitive
//   entries <genome> <state> <ids>...     each Open Decisions entry is in that state: open, decided, withdrawn;
//                                         ids as `3` or `2-11`; <genome> is a path or a glob such as `*-genome.md`
//   items <file> <answered|blank> <ids>... each item `**D<n>. …**`, `**CQ<n>. …**` or `**R<n>. …**` (a readiness
//                                         item may carry both: `**R15. D1. …**`, `**R15. D1 — …**`) of an SDD's Action Required, or
//                                         anywhere in a readiness file, is answered (its `Answer` line filled, or the
//                                         item gone) or blank (present, unfilled); ids as `D3`, `D2-11`, `CQ10`, `R3-6`.
//                                         An item is its heading and the `- ` lines under it; any other text ends it.
//   count <file> <regex> <min>            at least <min> lines of the file match, case-insensitive
//   unchanged <file> <sha256> [section]   the file, or its `## <section>`, hashes to <sha256> (line endings LF)
//   kept <file> <fixture> <section>       the file's `## <section>` holds every line of the fixture's, in order;
//                                         lines may be added (an answer that opens a new question)
//   body <sdd> <sha256>                   the SDD below `<!-- planner-sdd-body:v1 -->` hashes to <sha256>
//
// A failing check prints the current hash, so a fixture's hash is read by running the check once.
//
// check-genome.mjs is the skill's own checker: in coder-eval's container, in the plugin under test (each plugin
// mounts at /work/plugins/<i>); on a host, in the repository above this file.
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const CHECKER = join("skills", "uipath-planner", "scripts", "check-genome.mjs");
const CONTAINER_PLUGINS = "/work/plugins";
const GRADER_DIR = dirname(fileURLToPath(import.meta.url));
const SDD_BODY = "<!-- planner-sdd-body:v1 -->";
const GENOME = /-genome\.md$/;
const STATES = ["open", "decided", "withdrawn"];

function walk(dir) {
  return readdirSync(dir, { withFileTypes: true })
    .filter((e) => !e.name.startsWith(".") && e.name !== "node_modules")
    .flatMap((e) => (e.isDirectory() ? walk(join(dir, e.name)) : [join(dir, e.name)]));
}

const read = (file) => readFileSync(file, "utf8").replace(/\r\n/g, "\n");

function topGenome(pattern = "*-genome.md") {
  if (!pattern.includes("*")) return pattern;
  const found = readdirSync(".").filter((n) => GENOME.test(n));
  if (found.length !== 1) fail(`expected one top-level genome, found ${found.length}: ${found.join(", ") || "none"}`);
  return found[0];
}

function section(text, name) {
  const start = text.search(new RegExp(`^## ${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b.*$`, "m"));
  if (start < 0) return null;
  const rest = text.slice(start + 3);
  const end = rest.search(/^## /m);
  return text.slice(start, end < 0 ? undefined : start + 3 + end);
}

function checkerPath() {
  const plugins = existsSync(CONTAINER_PLUGINS) ? readdirSync(CONTAINER_PLUGINS).map((p) => join(CONTAINER_PLUGINS, p)) : [];
  const roots = [...plugins];
  for (let d = GRADER_DIR; d !== dirname(d); d = dirname(d)) roots.push(d);
  const hit = roots.map((r) => resolve(r, CHECKER)).find(existsSync);
  if (!hit) fail(`check-genome.mjs not found in ${CONTAINER_PLUGINS}/* or above ${GRADER_DIR}`, 2);
  return hit;
}

function ids(args) {
  return args.flatMap((a) => {
    const [lo, hi] = a.split("-").map(Number);
    if (!Number.isInteger(lo) || (hi !== undefined && !Number.isInteger(hi))) fail(`bad id: ${a}`, 2);
    return Array.from({ length: (hi ?? lo) - lo + 1 }, (_, i) => lo + i);
  });
}

function fail(message, code = 1) {
  console.log(message);
  process.exit(code);
}

const [command, ...args] = process.argv.slice(2);
switch (command) {
  case "absent": {
    if (args.length !== 1) fail("usage: absent <regex>", 2);
    const re = new RegExp(args[0], "i");
    const found = walk(".").filter((f) => re.test(f.replace(/\\/g, "/")));
    if (found.length) fail(`written: ${found.join(", ")}`);
    break;
  }
  case "strict": {
    const genome = topGenome();
    const level = /UIPATH-AUTOMATION-GENOME:\s*(component|process)\b/.exec(read(genome).split("\n", 1)[0])?.[1];
    if (!level) fail(`${genome}: first line declares no component or process level`);
    const run = spawnSync(process.execPath, [checkerPath(), level, genome, "--profile", "strict"], { stdio: "inherit" });
    process.exit(run.status ?? 2);
  }
  case "line": {
    if (args.length !== 1) fail("usage: line <regex>", 2);
    const re = new RegExp(args[0], "im");
    const files = walk(".").filter((f) => GENOME.test(f));
    if (!files.some((f) => re.test(read(f)))) fail(`no genome line matches /${args[0]}/i in ${files.join(", ") || "no genome"}`);
    break;
  }
  case "entries": {
    const [pattern, state, ...rest] = args;
    if (!STATES.includes(state) || !rest.length) fail("usage: entries <genome> <open|decided|withdrawn> <ids>...", 2);
    const genome = topGenome(pattern);
    const body = section(read(genome), "Open Decisions");
    if (!body) fail(`${genome}: no Open Decisions section`);
    const found = new Map(body.split("\n").map((l) => /^(\d+)\.\s(.*)/.exec(l)).filter(Boolean)
      .map(([, n, text]) => [Number(n), /\(decided \d{4}-\d{2}-\d{2}:/.test(text) ? "decided" : /\(withdrawn:/.test(text) ? "withdrawn" : "open"]));
    const wrong = ids(rest).filter((n) => found.get(n) !== state).map((n) => `D${n} is ${found.get(n) ?? "missing"}`);
    if (wrong.length) fail(`${genome}: expected ${state}: ${wrong.join("; ")}`);
    break;
  }
  case "items": {
    const [file, state, ...rest] = args;
    if (!["answered", "blank"].includes(state) || !rest.length) fail("usage: items <file> <answered|blank> <ids>...", 2);
    if (!existsSync(file)) fail(`${file} is missing`);
    const text = read(file);
    const body = section(text, "Action Required") ?? text;
    const answers = new Map();
    let current = [];
    for (const l of body.split("\n")) {
      const item = /^\*\*(?:(R\d+)\.\s+)?((?:D|CQ|R)\d+)(?:[.:]|\s+[—–-])\s/.exec(l);
      if (item) {
        current = [item[1], item[2]].filter(Boolean);
        for (const id of current) answers.set(id, "");
        continue;
      }
      if (l.trim() && !/^\s*- /.test(l)) current = [];
      const answer = /^- \*\*Answer(?: \(by [^)]+\))?:\*\*(.*)$/.exec(l);
      if (answer) for (const id of current) answers.set(id, answer[1].trim());
      if (answer) current = [];
    }
    const wanted = rest.flatMap((a) => {
      const m = /^(D|CQ|R)(\d+)(?:-(\d+))?$/.exec(a);
      if (!m) fail(`bad item id: ${a}`, 2);
      return ids([m[3] ? `${m[2]}-${m[3]}` : m[2]]).map((n) => `${m[1]}${n}`);
    });
    const wrong = wanted.filter((id) => (state === "answered" ? answers.get(id) === "" : answers.get(id) !== ""))
      .map((id) => `${id} is ${answers.has(id) ? (answers.get(id) ? `answered "${answers.get(id)}"` : "blank") : "gone"}`);
    if (wrong.length) fail(`${file}: expected ${state}: ${wrong.join("; ")}`);
    break;
  }
  case "count": {
    const [file, pattern, min] = args;
    if (!file || !pattern || !/^\d+$/.test(min ?? "")) fail("usage: count <file> <regex> <min>", 2);
    if (!existsSync(file)) fail(`${file} is missing`);
    const re = new RegExp(pattern, "i");
    const n = read(file).split("\n").filter((l) => re.test(l)).length;
    if (n < Number(min)) fail(`${file}: ${n} line(s) match /${pattern}/i, expected at least ${min}`);
    break;
  }
  case "kept": {
    const [file, fixture, name] = args;
    if (!file || !fixture || !name) fail("usage: kept <file> <fixture> <section>", 2);
    if (!existsSync(fixture)) fail(`${fixture} is missing`, 2);
    if (!existsSync(file)) fail(`${file} is missing`);
    const want = section(read(fixture), name);
    if (want === null) fail(`${fixture}: no "## ${name}" section`, 2);
    const got = section(read(file), name);
    if (got === null) fail(`${file}: no "## ${name}" section`);
    const lines = got.split("\n");
    let at = 0;
    const lost = want.split("\n").filter((l) => {
      const i = lines.indexOf(l, at);
      if (i < 0) return true;
      at = i + 1;
      return false;
    });
    if (lost.length) fail(`${file} § ${name}: ${lost.length} line(s) of the fixture's changed or gone, first: ${lost[0]}`);
    break;
  }
  case "unchanged":
  case "body": {
    const [file, sha, name] = args;
    if (!file || !/^[0-9a-f]{64}$/.test(sha ?? "")) fail(`usage: ${command} <file> <sha256>${command === "unchanged" ? " [section]" : ""}`, 2);
    if (!existsSync(file)) fail(`${file} is missing`);
    const all = read(file);
    const text = command === "body" ? (all.includes(SDD_BODY) ? all.slice(all.indexOf(SDD_BODY)) : null) : name ? section(all, name) : all;
    if (text === null) fail(`${file}: no ${command === "body" ? SDD_BODY : `"## ${name}" section`}`);
    const got = createHash("sha256").update(text).digest("hex");
    if (got !== sha) fail(`${file}${command === "body" ? " body" : name ? ` § ${name}` : ""} changed (sha256 ${got})`);
    break;
  }
  default:
    fail("usage: check_interview.mjs {absent <regex> | strict | line <regex> | entries <genome> <state> <ids>... | items <sdd> <answered|blank> <ids>... | count <file> <regex> <min> | unchanged <file> <sha256> [section] | kept <file> <fixture> <section> | body <sdd> <sha256>}", 2);
}
