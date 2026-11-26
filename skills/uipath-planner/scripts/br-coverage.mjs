#!/usr/bin/env node
// Business-rule coverage of an SDD against its source (references/design/business-rules-guide.md § 4), run before
// the ready flip (references/design/sdd-writing-guide.md Step 4 item 8).
//
// Usage: node br-coverage.mjs --source <PDD.md> [--source <more.md>] <SDD.md> [<child-SDD.md> ...]
// A solution passes its root SDD and every child SDD: a rule may live in any of them.
// Exit 0 and "OK" when: some SDD has a Business Rules section; every rule ID the source defines (BR-001, BR-F01,
// FBR-001, BR-12) is in an SDD line that carries the rule beside its ID, outside Action Required; and every rule ID
// only the SDD has is marked [DEFAULT] or [SME REVIEW] on its line. A source with no rule IDs checks the section only.
// Exit 1 with one FAIL line per defect.
import { existsSync, readFileSync } from "node:fs";

const RULE_ID = /\b[A-Z]{0,3}BR-[A-Z]?\d+[a-z]?\b/g;
const RULES_HEADING = /^#{2,4}\s+(?:\d+\.\s+)?(?:[\w ,]+,\s*)?(?:Steps and )?Business Rules(?: and Decisions)?\s*$/m;
// words beside the IDs: a rule written as its ID alone ("BR-04") or a bare list of IDs carries no rule
const MIN_WORDS = 4;

const sources = [];
const sdds = [];
const args = process.argv.slice(2);
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--source") sources.push(args[++i]);
  else sdds.push(args[i]);
}
if (!sources.length || sources.includes(undefined) || !sdds.length) {
  console.error("usage: node br-coverage.mjs --source <PDD.md> [--source <more.md>] <SDD.md> [<child-SDD.md> ...]");
  process.exit(2);
}
const fails = [];
const read = (path) => {
  if (!existsSync(path)) { fails.push(`${path} not found`); return ""; }
  return readFileSync(path, "utf8").replace(/\r/g, "");
};

// the lines of an SDD that can carry a rule: Action Required asks about rules, it never carries one
function ruleLines(text) {
  const lines = [];
  let skipping = false;
  for (const line of text.split("\n")) {
    if (/^##\s/.test(line)) skipping = /^##\s+Action Required/.test(line);
    if (!skipping) lines.push(line);
  }
  return lines;
}
const wordsBesideIds = (line) =>
  line.replace(RULE_ID, " ").replace(/\[[^\]]*\]\([^)]*\)/g, (link) => link.replace(/\]\(.*$/, "")).match(/\p{L}{2,}/gu)?.length ?? 0;

const sourceIds = new Map();
for (const path of sources) {
  for (const line of read(path).split("\n")) {
    for (const [id] of line.matchAll(RULE_ID)) if (!sourceIds.has(id)) sourceIds.set(id, line.trim());
  }
}

const sddTexts = sdds.map(read);
if (!sddTexts.some((text) => RULES_HEADING.test(text))) {
  fails.push("no SDD has a Business Rules section: write the template's Business Rules section (business-rules-guide.md § 1)");
}

const cited = new Map(); // id -> { carried: boolean, marked: boolean }
for (const text of sddTexts) {
  for (const line of ruleLines(text)) {
    for (const [id] of line.matchAll(RULE_ID)) {
      const entry = cited.get(id) ?? { carried: false, marked: false };
      entry.carried ||= wordsBesideIds(line) >= MIN_WORDS;
      entry.marked ||= /\[(?:DEFAULT|SME REVIEW)\b/.test(line);
      cited.set(id, entry);
    }
  }
}

const shorten = (line) => (line.length > 90 ? `${line.slice(0, 87)}...` : line);
for (const [id, line] of sourceIds) {
  const entry = cited.get(id);
  if (!entry) fails.push(`${id} is in the source and in no SDD — give it a row in its home, '${id}: <the rule>' (source: ${shorten(line)})`);
  else if (!entry.carried) fails.push(`${id} is cited by its ID alone — the line that defines it carries the rule in the source's words`);
}
for (const [id, entry] of cited) {
  if (sourceIds.size && !sourceIds.has(id) && !entry.marked) {
    fails.push(`${id} is in the SDD and not in the source — keep the source's rule IDs; a rule the design adds is marked [DEFAULT] or [SME REVIEW]`);
  }
}

if (fails.length) {
  for (const fail of fails) console.log(`FAIL: ${fail}`);
  process.exit(1);
}
console.log(sourceIds.size
  ? `OK: ${sourceIds.size} of ${sourceIds.size} source rules carried, ${cited.size - sourceIds.size} added by the design`
  : "OK: the source numbers no rules; the Business Rules section is present — walk business-rules-guide.md § 4 by hand");
