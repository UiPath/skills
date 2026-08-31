#!/usr/bin/env node
/**
 * Deterministic template-shape audit for a planner-authored Case Management SDD.
 *
 * Usage:
 *     node audit-case-sdd.mjs <sdd.md> [--draft <sdd.draft.md>]
 *
 * Read-only. Exit 0 = shape-clean. Exit 1 = numbered findings on stderr; repair
 * the document with Write/Edit and re-run until clean. `--draft` additionally
 * verifies the finalized document preserves the draft's ordered stage/task
 * inventory and every draft `=js:` expression.
 *
 * Node is the runtime the skill can rely on: `uip` is an npm-installed Node
 * CLI, so if `uip` runs, this runs.
 */

import { readFileSync, statSync } from "node:fs";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import process from "node:process";

const DOC = `Deterministic template-shape audit for a planner-authored Case Management SDD.

Usage:
    node audit-case-sdd.mjs <sdd.md> [--draft <sdd.draft.md>]

Read-only. Exit 0 = shape-clean. Exit 1 = numbered findings on stderr; repair
the document with Write/Edit and re-run until clean. \`--draft\` additionally
verifies the finalized document preserves the draft's ordered stage/task
inventory and every draft \`=js:\` expression.`;

const REQUIRED_HEADINGS = [
  "## Document History",
  "## Planner Handoff",
  "## Table of Contents",
  "## Section 1: Case Definition",
  "### Case Metadata",
  "### Case Triggers",
  "### Case Exit Conditions",
  "### Case Variables",
  "## Section 2: Stages & Tasks",
  "## Section 3: Personas & App Views",
  "### Personas",
  "### Process App Views",
  "## Section 4: Integrations",
];

const SUMMARY_ONLY_HEADINGS = [
  "Source", "Case Objective", "Actors And Systems", "Case Trigger", "Stages",
  "Business Rules", "Task Plan", "Resource Resolution", "Acceptance Scenarios",
];

const STAGE_MARKERS = [
  "**Type:**",
  "**Design Rationale:**",
  "#### Stage Entry Conditions",
  "#### Stage Exit Conditions",
  "#### Tasks",
];

const TASK_MARKERS = [
  "**Type:**",
  "**Activation Mode:**",
  "**Design Rationale:**",
  "**Entry Condition:**",
  "**Task envelope**",
];

// task type -> (detail-block heading, alternate literal markers)
const TASK_DETAIL_MARKERS = new Map([
  ["action", ["Action Task Detail", "**HITL Implementation:**"]],
  ["wait-for-connector", ["Connector Task Detail", "**Connector:**", "**Trigger / Event:**"]],
  ["execute-connector-activity", ["Connector Task Detail", "**Connector:**", "**Resolved Resource:**"]],
  ["wait-for-timer", ["Timer Task Detail", "**Timer Configuration:**", "**Duration:**", "**Timer:**"]],
  ["case-management", ["Child Case Task Detail", "**Child Case:**"]],
  ["process", ["Process / Agent / RPA / API Workflow Task Detail", "**Resolved Resource:**"]],
  ["agent", ["Process / Agent / RPA / API Workflow Task Detail", "**Resolved Resource:**"]],
  ["rpa", ["Process / Agent / RPA / API Workflow Task Detail", "**Resolved Resource:**"]],
  ["api-workflow", ["Process / Agent / RPA / API Workflow Task Detail", "**Resolved Resource:**"]],
]);

const CASE_VARIABLES_HEADER =
  "| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |";

const STAGE_HEADING = /^###[ \t]+(Stage[ \t]+\d+|Secondary Stage):[ \t]*(.+?)[ \t]*$/gm;
const TASK_HEADING = /^#####[ \t]+Task[ \t]+(S?\d+|[A-Z]{1,4})\.(\d+):[ \t]*(.+?)[ \t]*$/gm;
const LETTERED_TASK = /^#####[ \t]+Task[ \t]+[A-RT-Z]+[A-Z]*\.\d/m;

// ─────────────────────────────────────────────────────── helpers

const reEscape = (s) => s.replace(/[.*+?^${}()|[\]\\-]/g, "\\$&");

/** Mirror of Python's `repr()` for a plain string. */
function pyRepr(s) {
  const inner = String(s)
    .replace(/\\/g, "\\\\")
    .replace(/\n/g, "\\n")
    .replace(/\t/g, "\\t");
  return inner.includes("'") && !inner.includes('"')
    ? `"${inner}"`
    : `'${inner.replace(/'/g, "\\'")}'`;
}

/** Python `sorted()` on strings — codepoint order. */
const pySorted = (it) => [...it].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));

/** Python `f"{n:,}"`. */
const withCommas = (n) => Number(n).toLocaleString("en-US");

const countNewlines = (s) => (s.match(/\n/g) || []).length;

const splitLines = (s) => s.split("\n");

/** Python str.strip(chars) — both ends. */
function stripChars(s, chars) {
  let a = 0;
  let b = s.length;
  while (a < b && chars.includes(s[a])) a += 1;
  while (b > a && chars.includes(s[b - 1])) b -= 1;
  return s.slice(a, b);
}

/** All matches for a /g regex, as arrays with .index. */
const allMatches = (re, text) => [...text.matchAll(re)];

/**
 * Body of a heading section, stopping at the first line matching `stopRe`
 * after the heading. Emulates Python's `(?=^... |\Z)` lookaheads, where `\Z`
 * is absolute end-of-string (JS `$` under /m is end-of-LINE, which would
 * truncate every section at its first newline).
 */
function sectionBody(text, headingRe, stopRe) {
  const h = text.match(headingRe);
  if (!h) return null;
  const from = h.index + h[0].length;
  const rest = text.slice(from);
  const stop = rest.match(stopRe);
  return stop ? rest.slice(0, stop.index) : rest;
}

const stripIdSuffix = (name) => name.replace(/\s*\(`[^`]*`\)\s*$/, "").trim();

/** [kind, display name, block text] for each stage heading. */
function stageBlocks(text) {
  const matches = allMatches(STAGE_HEADING, text);
  const s3 = text.match(/^## Section 3: Personas & App Views[ \t]*$/m);
  const docEnd = s3 ? s3.index : text.length;
  const out = [];
  for (let i = 0; i < matches.length; i += 1) {
    const end = i + 1 < matches.length ? matches[i + 1].index : docEnd;
    out.push([matches[i][1], stripIdSuffix(matches[i][2]), text.slice(matches[i].index, end)]);
  }
  return out;
}

/** Ordered [stage, task] name pairs, id suffixes stripped. */
function inventory(text) {
  const entries = [];
  for (const [, stageName, block] of stageBlocks(text)) {
    for (const task of allMatches(TASK_HEADING, block)) {
      entries.push([stageName, stripIdSuffix(task[3])]);
    }
  }
  return entries;
}

function jsExpressions(text) {
  return new Set(
    allMatches(/=js:[^|\n]+/g, text).map((m) => m[0].replace(/\s+/g, " ").trim()),
  );
}

// ─────────────────────────────────────────────── threshold encoding

const HIGH_WORDS = "over|above|at\\s+least|more\\s+than|greater\\s+than|in\\s+excess\\s+of|exceed(?:s|ing)?";
const LOW_WORDS = "under|below|at\\s+most|less\\s+than";
const COMPARATOR_THRESHOLD = new RegExp(
  `(>=|<=|>|<|≥|≤|\\b(?:${HIGH_WORDS}|${LOW_WORDS})\\b)\\s*` +
    "\\$\\s*(\\d[\\d,]*(?:\\.\\d+)?)\\s*([mk])?\\b",
  "gi",
);
const COMPARATOR_TOKEN = new RegExp(`(>=|<=|>|<|≥|≤|\\b(?:${HIGH_WORDS}|${LOW_WORDS})\\b)`, "gi");
const EXECUTABLE_LINE = /=js:|vars\.|\bowner\b|\brecipient\b|Role:/i;
const PROSE_MARKER = /^\*\*(Design Rationale|Description):\*\*/;

function comparatorDirection(token) {
  const t = token.toLowerCase().trim();
  if (t === ">" || t === ">=" || t === "≥") return "high";
  if (new RegExp(`^(?:${HIGH_WORDS})$`, "i").test(t)) return "high";
  return "low";
}

/**
 * Spellings of one currency threshold: '5' + 'M' -> 5M, 5 million, 5000000, 5,000,000.
 * The bare short numeral ('5') is deliberately excluded — it would match any
 * digit in an executable line and make the check vacuous.
 */
function thresholdVariants(number, suffix) {
  const bare = number.replace(/,/g, "");
  if (suffix) {
    const lower = suffix.toLowerCase();
    const factor = lower === "m" ? 1_000_000 : 1_000;
    const word = lower === "m" ? "million" : "thousand";
    const variants = [`${bare}${lower}`, `${bare} ${word}`];
    if (!bare.includes(".")) {
      const expanded = String(Number.parseInt(bare, 10) * factor);
      variants.push(expanded, withCommas(expanded));
    }
    return variants;
  }
  const variants = [bare];
  if (!bare.includes(".")) variants.push(withCommas(Number.parseInt(bare, 10)));
  return variants;
}

/** Draft comparator-currency thresholds with no executable encoding in the final. */
function unencodedThresholds(draft, final) {
  const findings = [];
  const seen = new Set();
  // Rationale/Description prose never counts as an encoding — the guard must
  // live in an executable table cell (owner/recipient/WHEN/IF/Inputs).
  const executableLines = splitLines(final).filter(
    (line) => EXECUTABLE_LINE.test(line) && !PROSE_MARKER.test(line.trim()),
  );
  for (const match of allMatches(COMPARATOR_THRESHOLD, draft)) {
    const direction = comparatorDirection(match[1]);
    const variants = thresholdVariants(match[2], match[3]);
    const key = JSON.stringify([variants[variants.length - 1], direction]);
    if (seen.has(key)) continue;
    seen.add(key);
    const needles = variants.map((v) => new RegExp(`(?<![\\w.])${reEscape(v)}(?!\\w)`, "i"));
    let covered = false;
    for (const line of executableLines) {
      if (!needles.some((n) => n.test(line))) continue;
      const ternary = line.includes("?") && line.split("?").slice(1).join("?").includes(":");
      const lineDirs = new Set(
        allMatches(COMPARATOR_TOKEN, line).map((t) => comparatorDirection(t[1])),
      );
      if (ternary || lineDirs.has(direction)) {
        covered = true;
        break;
      }
    }
    if (!covered) {
      findings.push(
        `draft threshold policy ${pyRepr(match[0].trim())} has no ${direction}-side executable encoding — ` +
          "add the guard to an owner/recipient/WHEN/IF cell (fast-path step 9), e.g. " +
          '`=js:vars.<attr> > <threshold> ? "Role:<ExceptionRole>" : "Role:<DefaultRole>"`; ' +
          "Rationale/Description prose does not count",
      );
    }
  }
  return findings;
}

// ─────────────────────────────────────────────────────── lineage

const VARIABLE_ROW =
  /^\|[ \t]*([A-Za-z]\w*)[ \t]*\|[ \t]*(In|Out|Variable)[ \t]*\|[ \t]*[^|]*\|[ \t]*([^|]*?)[ \t]*\|[ \t]*[^|]*\|[ \t]*([^|]*?)[ \t]*\|/gm;

const variableRows = (text) =>
  allMatches(VARIABLE_ROW, text).map((m) => [m[1], m[2], m[3], m[4]]);

function producedNames(text) {
  const out = new Set();
  for (const m of allMatches(/->\s*([A-Za-z]\w*)/g, text)) out.add(m[1]);
  for (const m of allMatches(/\b([A-Za-z]\w*)\s*=\s*(?!=)/g, text)) out.add(m[1]);
  return out;
}

/**
 * Mirror sdd_check's mapping + lineage closure: every consumed variable is
 * declared and produced (-> output, `X =` assignment, Default, or trigger-sourced).
 */
function lineageFindings(text) {
  const findings = [];
  const category = new Map();
  const srcTrig = new Map();
  const dflt = new Map();
  for (const [name, cat, st, d] of variableRows(text)) {
    category.set(name, cat);
    srcTrig.set(name, st.trim());
    dflt.set(name, d.trim());
  }
  if (category.size === 0) return findings; // template checks already flag a missing table
  const refs = new Set(allMatches(/=vars\.([A-Za-z]\w*)/g, text).map((m) => m[1]));
  refs.delete("X");
  const undeclared = pySorted([...refs].filter((r) => !category.has(r)));
  if (undeclared.length) {
    findings.push(
      `${undeclared.length} =vars consumed but not declared in Case Variables: ${undeclared.join(", ")}`,
    );
  }
  const produced = producedNames(text);
  const openLineage = pySorted(
    [...refs].filter(
      (r) =>
        category.has(r) &&
        category.get(r) !== "In" &&
        !dflt.get(r) &&
        !srcTrig.get(r) &&
        !produced.has(r),
    ),
  );
  for (const name of openLineage) {
    findings.push(
      `variable ${pyRepr(name)} is consumed but never produced — keep its producer output row ` +
        `(\`-> ${name}\`), assignment, Default, or trigger source`,
    );
  }
  return findings;
}

// ─────────────────────────────────────────────────── model facts

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const LAYERS_MD = resolve(join(SCRIPT_DIR, "..", "references", "case-design-layers-guide.md"));

/**
 * Parse the canonical tables in the case reference files.
 * Returns [facts, degraded]; degraded is null on a clean parse.
 */
function loadModelFacts() {
  let text;
  try {
    text = readFileSync(LAYERS_MD, "utf-8");
  } catch {
    return [{}, `${basename(LAYERS_MD)} not found beside this script`];
  }

  const section = (heading) =>
    sectionBody(text, new RegExp(`^### ${reEscape(heading)}[ \\t]*$`, "m"), /^#/m) ?? "";

  const facts = {};
  facts.task_types = new Set(
    allMatches(/^\|\s*`([a-z][a-z-]+)`\s*\|/gm, section("Task types")).map((m) => m[1]),
  );
  const yesWhen = new Set();
  const noWhen = new Set();
  const gateRules = new Map();
  for (const row of allMatches(/^\|([^|]+)\|([^|]+)\|([^|]+)\|/gm, section("Lifecycle gates"))) {
    const gate = row[1].trim();
    const marks = row[2].trim();
    const rules = new Set(allMatches(/`([a-z][a-z-]+)`/g, row[3]).map((m) => m[1]));
    if (rules.size === 0) continue;
    gateRules.set(gate, rules);
    if (marks === "Yes") for (const r of rules) yesWhen.add(r);
    else if (marks === "No") for (const r of rules) noWhen.add(r);
  }
  facts.yes_when = yesWhen;
  facts.no_when = noWhen;
  facts.gate_rules = gateRules;
  const pattern = section("Naming rules").match(/```\s*(\^[^\n`]+\$)\s*```/);
  facts.name_pattern = pattern ? new RegExp(pattern[1]) : null;

  const empty = [
    ["`### Task types` table", facts.task_types.size > 0],
    ["`### Lifecycle gates` table", yesWhen.size > 0],
    ["`### Naming rules` regex fence", facts.name_pattern !== null],
  ]
    .filter(([, ok]) => !ok)
    .map(([label]) => label);
  if (empty.length) {
    return [
      {},
      `${basename(LAYERS_MD)} parsed but ${empty.join(", ")} came back empty — the heading was ` +
        "renamed or the table reshaped; the model checks are disarmed until it is restored",
    ];
  }
  return [facts, null];
}

const ADVISORY = "[advisory] ";

const union = (...sets) => {
  const out = new Set();
  for (const s of sets) for (const v of s ?? []) out.add(v);
  return out;
};

/** Checks driven by the canonical model tables. */
function modelFindings(text, facts, carriedNames = new Set()) {
  if (!facts || Object.keys(facts).length === 0) return [];
  const findings = [];

  for (const match of allMatches(/^\*\*Type:\*\*[ \t]*`?([a-z][a-z-]+)`?[ \t]*$/gm, text)) {
    if (!facts.task_types.has(match[1])) {
      findings.push(
        `task type ${pyRepr(match[1])} outside the closed enum (case-design-layers-guide.md § Task types): ` +
          pySorted(facts.task_types).join(", "),
      );
    }
  }

  // WHEN x Marks-Complete pairing applies only inside tables whose header carries a
  // 'Marks ... Complete' column.
  const knownRules = union(facts.yes_when, facts.no_when);
  const lines = splitLines(text);
  let marksCol = null;
  for (let i = 0; i < lines.length; i += 1) {
    const stripped = lines[i].trim();
    if (!stripped.startsWith("|")) {
      marksCol = null;
      continue;
    }
    const cells = stripChars(stripped, "|").split("|").map((c) => c.trim());
    if (cells.some((c) => /^Marks (Stage|Case) Complete$/.test(c))) {
      marksCol = cells.findIndex((c) => c.startsWith("Marks "));
      continue;
    }
    const onlyRuler = [...cells[0]].every((ch) => "-: ".includes(ch));
    if (marksCol === null || cells.length <= marksCol || onlyRuler) continue;
    const when = cells[0].match(/^`?([a-z][a-z-]+)/);
    const marks = cells[marksCol] === "Yes" || cells[marksCol] === "No" ? cells[marksCol] : null;
    if (!when || marks === null || !knownRules.has(when[1])) continue;
    const legal = marks === "Yes" ? facts.yes_when : facts.no_when;
    if (!legal.has(when[1])) {
      findings.push(
        `line ${i + 1}: WHEN ${pyRepr(when[1])} with Marks Complete ${pyRepr(marks)} is an illegal ` +
          "pair (case-design-layers-guide.md § Lifecycle gates)",
      );
    }
  }

  const namePattern = facts.name_pattern;
  if (namePattern) {
    const nameFinding = (kind, rawName) => {
      const name = rawName.trim();
      if (name.includes(":")) {
        return `${kind} name ${pyRepr(name)} contains ':' — the structural ban; case-execution events are colon-delimited`;
      }
      if (carriedNames.has(name)) return null;
      const full = name.match(new RegExp(`^(?:${namePattern.source})$`));
      if (!full || full[0] !== name) {
        return (
          `${ADVISORY}${kind} name ${pyRepr(name)} uses characters outside the safe display set in\n` +
          "     case-design-layers-guide.md § Naming rules. Only ':' is known to break routing, so this does not\n" +
          "     gate: prefer the safe set when MINTING a name, and keep a name the user or the source supplied"
        );
      }
      return null;
    };

    for (const [kind, name] of stageBlocks(text)) {
      const f = nameFinding(kind.toLowerCase(), name);
      if (f) findings.push(f);
    }
    for (const match of allMatches(/^#{5} Task [S\d.]+: ([^\n]+)$/gm, text)) {
      const f = nameFinding("task", stripIdSuffix(match[1]));
      if (f) findings.push(f);
    }
  }
  return findings;
}

// ───────────────────────────────────────────────── contract checks

const EXIT_TYPES_YES = new Set(["exit-only", "return-to-origin", "wait-for-user"]);
const EXIT_TYPES_NO = new Set(["exit-only", "wait-for-user"]);
const RECIPIENT_PREFIX = /^(Role|User|UserGroup|Email|Expression):/;
const FORBIDDEN_VOCAB = [
  "groupOperator", "savedFilterTrees", "io-binding", "auto-mint", "originalVar", "inputOutputs[",
];

/** Body of a `### {heading}` section up to the next heading of any level. */
const sectionSlice = (text, heading) =>
  sectionBody(text, new RegExp(`^### ${reEscape(heading)}[ \\t]*$`, "m"), /^#{1,5} /m) ?? "";

/** [offset line index, cells] for pipe-table body rows in a chunk. */
function tableRows(chunk) {
  const lines = splitLines(chunk);
  const isRuler = (line) => {
    const stripped = line.trim();
    if (!stripped.startsWith("|")) return false;
    const cells = stripChars(stripped, "|").split("|").map((c) => c.trim());
    return cells.length > 0 && cells.every((c) => c !== "" && [...c].every((ch) => "-: ".includes(ch)));
  };
  const rows = [];
  for (let i = 0; i < lines.length; i += 1) {
    const stripped = lines[i].trim();
    if (!stripped.startsWith("|") || isRuler(lines[i])) continue;
    if (i + 1 < lines.length && isRuler(lines[i + 1])) continue; // header row
    const cells = stripChars(stripped, "|").split("|").map((c) => c.trim());
    if (cells.length) rows.push([i, cells]);
  }
  return rows;
}

function ruleName(cell) {
  const m = cell.trim().match(/^`?([a-z][a-z-]+)/);
  return m ? m[1] : null;
}

/** SLA titles per target. Casefolded keys and titles. */
function declaredSlaTitles(text) {
  const titles = new Map();
  const meta = sectionSlice(text, "Case Metadata");
  const row = meta.match(/^\|[ \t]*SLA Title[ \t]*\|[ \t]*([^|]+?)[ \t]*\|/m);
  if (row && row[1].trim() !== "—" && row[1].trim() !== "") {
    titles.set("root", new Set([row[1].trim()]));
  }
  for (const [, stageName, block] of stageBlocks(text)) {
    const found = new Set(
      allMatches(/^\*\*SLA Title:\*\*[ \t]*([^\n<]+)/gm, block).map((m) => m[1].trim()),
    );
    if (found.size) titles.set(stageName.toLowerCase(), found);
  }
  return titles;
}

const QUOTED_ARG = /["“‘']([^"”’']+)["”’']/g;
const quotedArgs = (s) => allMatches(QUOTED_ARG, s).map((m) => m[1]);

function contractFindings(text, facts) {
  const findings = [];
  const lines = splitLines(text);

  if (!text.includes("<!-- planner-handoff:v1 -->")) {
    findings.push("missing '<!-- planner-handoff:v1 -->' marker (Planner Handoff scaffold)");
  }
  if (text.includes("`<UNRESOLVED>`")) {
    findings.push("backtick-wrapped `<UNRESOLVED>` — the marker renders as plain text, exactly <UNRESOLVED>");
  }
  for (const token of FORBIDDEN_VOCAB) {
    if (text.includes(token)) {
      findings.push(
        `forbidden skill-internal term ${pyRepr(token)} in the SDD body (case-sdd-template.md § Validation footer)`,
      );
    }
  }

  const hasWfuExit = /\bwait-for-user\b/.test(text);
  const hasUssEntry = /\buser-selected-stage\b/.test(text);
  if (hasWfuExit && !hasUssEntry) {
    findings.push("wait-for-user exit with no user-selected-stage entry anywhere — validate fails with 'no possible stage options'");
  }
  if (hasUssEntry && !hasWfuExit) {
    findings.push("user-selected-stage entry with no wait-for-user exit anywhere — validate fails with 'will never be met'");
  }

  // Case Exit Conditions: >= 1 completing row
  const caseExit = sectionSlice(text, "Case Exit Conditions");
  if (caseExit && !tableRows(caseExit).some(([, cells]) => cells.includes("Yes"))) {
    findings.push("Case Exit Conditions has no 'Marks Case Complete: Yes' row — the case can never complete");
  }
  if (caseExit.includes("return-to-origin")) {
    findings.push("return-to-origin in Case Exit Conditions — it is a stage-completion exit type only");
  }

  // Case Variables: Out rows need a producer or Default
  const produced = producedNames(text);
  for (const [name, cat, , dflt] of variableRows(text)) {
    if (cat === "Out" && !dflt && !produced.has(name)) {
      findings.push(
        `Out variable ${pyRepr(name)} has no Default and no producing Outputs row (\`-> ${name}\` / \`${name} = ...\`)`,
      );
    }
  }

  // Uniqueness: stage labels and task display names, case-wide
  const seenStages = new Set();
  const seenTasks = new Map();
  for (const [, stageName, block] of stageBlocks(text)) {
    const key = stageName.trim();
    if (seenStages.has(key)) {
      findings.push(`duplicate stage label ${pyRepr(key)} — stage labels are unique across the case`);
    }
    seenStages.add(key);
    for (const task of allMatches(TASK_HEADING, block)) {
      const taskName = stripIdSuffix(task[3]).trim();
      if (seenTasks.has(taskName) && seenTasks.get(taskName) !== stageName + task[0]) {
        findings.push(
          `duplicate task display name ${pyRepr(taskName)} — task names are unique across the whole case`,
        );
      }
      if (!seenTasks.has(taskName)) seenTasks.set(taskName, stageName + task[0]);
    }
  }

  const gateRules = facts.gate_rules ?? new Map();
  const stageEntryLegal = gateRules.get("Stage entry") ?? new Set();
  const taskEntryLegal = gateRules.get("Task entry") ?? new Set();
  const slaTitles = declaredSlaTitles(text);

  for (const [kind, stageName, block] of stageBlocks(text)) {
    // Stage entry WHEN legality
    const entry = sectionBody(
      block, /^#### Stage Entry Conditions[ \t]*$/m, /^#{1,5} |\*\*Task envelope\*\*/m,
    );
    if (entry !== null && stageEntryLegal.size) {
      for (const [, cells] of tableRows(entry)) {
        const rule = ruleName(cells[0]);
        const pool = union(facts.yes_when, facts.no_when, taskEntryLegal,
          ["case-entered", "adhoc", "runs-sequentially", "current-stage-entered"]);
        if (rule && !stageEntryLegal.has(rule) && pool.has(rule)) {
          findings.push(
            `stage ${pyRepr(stageName)}: entry WHEN ${pyRepr(rule)} is not a legal stage-entry rule (case-design-layers-guide.md § Lifecycle gates)`,
          );
        }
      }
    }
    // Stage exit rows: Exit Type x Marks Stage Complete legality
    const exitSec = sectionBody(block, /^#### Stage Exit Conditions[ \t]*$/m, /^#{1,5} /m);
    if (exitSec !== null) {
      for (const [, cells] of tableRows(exitSec)) {
        const bare = cells.map((c) => stripChars(c, "`"));
        const etype = bare.find((c) => EXIT_TYPES_YES.has(c)) ?? null;
        const marks = bare.find((c) => c === "Yes" || c === "No") ?? null;
        if (etype && marks) {
          const legal = marks === "Yes" ? EXIT_TYPES_YES : EXIT_TYPES_NO;
          if (!legal.has(etype)) {
            findings.push(
              `stage ${pyRepr(stageName)}: exit type ${pyRepr(etype)} with Marks Stage Complete ${pyRepr(marks)} is illegal — ` +
                `legal for ${marks}: ${pySorted(legal).join(", ")}`,
            );
          }
        }
      }
    }
    // Task entry WHEN legality + Recipient prefix
    const tasks = allMatches(TASK_HEADING, block);
    for (let index = 0; index < tasks.length; index += 1) {
      const end = index + 1 < tasks.length ? tasks[index + 1].index : block.length;
      const taskBlock = block.slice(tasks[index].index, end);
      const taskName = stripIdSuffix(tasks[index][3]);
      const entryTblStart = taskBlock.indexOf("**Entry Condition:**");
      let entryTbl = null;
      if (entryTblStart !== -1) {
        const after = taskBlock.slice(entryTblStart + "**Entry Condition:**".length);
        const stop = after.indexOf("**Task envelope**");
        entryTbl = stop === -1 ? after : after.slice(0, stop);
      }
      if (entryTbl !== null && tableRows(entryTbl).length === 0) {
        findings.push(
          `task ${pyRepr(taskName)}: Entry Condition has no table rows — an executable gate collapsed ` +
            "into prose drops out of the planning handoff (and a task with no entry never starts)",
        );
      }
      if (entryTbl !== null && taskEntryLegal.size) {
        for (const [, cells] of tableRows(entryTbl)) {
          const rule = ruleName(cells[0]);
          const pool = union(facts.yes_when, facts.no_when, stageEntryLegal);
          if (rule && !taskEntryLegal.has(rule) && pool.has(rule)) {
            findings.push(
              `task ${pyRepr(taskName)}: entry WHEN ${pyRepr(rule)} is not a legal task-entry rule (case-design-layers-guide.md § Lifecycle gates)`,
            );
          }
        }
      }
      const recipient = taskBlock.match(/^\*\*Recipient:\*\*[ \t]*([^\n]+)/m);
      if (recipient) {
        const value = stripChars(recipient[1].trim(), "`");
        if (value !== "—" && value !== "<UNRESOLVED>" && !RECIPIENT_PREFIX.test(value) && !value.startsWith("=")) {
          findings.push(
            `task ${pyRepr(taskName)}: Recipient ${pyRepr(value)} lacks a typed prefix (Role:/User:/UserGroup:/Email:/Expression:)`,
          );
        }
      }
    }
  }

  // Buttons Maps To LHS
  const declaredVars = new Set(variableRows(text).map(([n]) => n));
  declaredVars.add("taskOutcome");
  const buttonSpans = allMatches(
    /^\|[ \t]*Button[ \t]*\|[ \t]*Maps To[ \t]*\|[^\n]*$([\s\S]*?)(?=^[^|]|$(?![\s\S]))/gm, text,
  ).map((m) => [m.index + m[0].length - m[1].length, m.index + m[0].length]);
  let outside = "";
  for (let i = 0; i < buttonSpans.length; i += 1) {
    outside += text.slice(i ? buttonSpans[i - 1][1] : 0, buttonSpans[i][0]);
  }
  outside += buttonSpans.length ? text.slice(buttonSpans[buttonSpans.length - 1][1]) : text;
  for (const [start, end] of buttonSpans) {
    for (const [, cells] of tableRows(text.slice(start, end))) {
      if (cells.length < 2) continue;
      const target = cells[1].match(/^`?([A-Za-z]\w*)/);
      if (!target) continue;
      const lhs = target[1];
      if (declaredVars.has(lhs)) continue;
      if (!new RegExp(`\\b${reEscape(lhs)}\\b`).test(outside)) {
        findings.push(
          `button ${pyRepr(cells[0])} maps to ${pyRepr(lhs)}, which is never declared, extracted, or read anywhere else — ` +
            "a typo or a dead decision route",
        );
      }
    }
  }

  // FE-parity structural rules
  const entryRowsAll = [];
  for (const [, stageName, block] of stageBlocks(text)) {
    const entry = sectionBody(block, /^#### Stage Entry Conditions[ \t]*$/m, /^#{1,5} /m);
    if (entry !== null) {
      for (const [, cells] of tableRows(entry)) {
        entryRowsAll.push([stageName, cells[0], cells]);
        for (const m of allMatches(
          /selected-stage-(?:completed|exited)\s*\(\s*["“‘']([^"”’']+)/g, cells[0],
        )) {
          if (stripIdSuffix(m[1]).trim() === stageName) {
            findings.push(`stage ${pyRepr(stageName)}: entry condition references its own stage — it can never fire`);
          }
        }
      }
    }
  }
  if (stageBlocks(text).length) {
    if (!entryRowsAll.some(([, when]) => when.includes("case-entered"))) {
      findings.push("no stage carries a `case-entered` entry row — the case has no start (first stage requires one)");
    }
  }

  // >=1 trigger row
  if (tableRows(sectionSlice(text, "Case Triggers")).length === 0) {
    findings.push("Case Triggers has no rows — a case needs at least one trigger (T02)");
  }

  // SLA bounds + case-vs-stage duration
  const UNIT_MIN = { min: 1, h: 60, d: 1440, w: 10080, m: 43200 };
  const slaMinutes = (count, unit) => {
    const u = stripChars(unit.trim(), "`");
    const n = Number.parseFloat(count);
    if (!Number.isFinite(n) || !(u in UNIT_MIN)) return null;
    return Math.trunc(n) * UNIT_MIN[u];
  };

  let caseMinutes = null;
  const meta = sectionSlice(text, "Case Metadata");
  const caseSla = meta.match(/^\|[ \t]*Case-Level SLA[ \t]*\|[ \t]*(\d+(?:\.\d+)?)[ \t]*(min|h|d|w|m)\b/m);
  if (caseSla) {
    caseMinutes = slaMinutes(caseSla[1], caseSla[2]);
    if (caseSla[2] === "min" && caseMinutes !== null && !(caseMinutes >= 15 && caseMinutes <= 1000)) {
      findings.push(`Case-Level SLA ${caseMinutes} min is out of bounds — minute counts are bounded 15–1000`);
    }
  }
  for (const [, stageName, block] of stageBlocks(text)) {
    const slaSec = sectionBody(block, /^#### Stage SLA[ \t]*$/m, /^#{1,5} /m);
    if (slaSec === null) continue;
    for (const [, cells] of tableRows(slaSec)) {
      if (cells.length < 2) continue;
      const minutes = slaMinutes(cells[0], cells[1]);
      if (minutes === null) continue;
      if (stripChars(cells[1], "`") === "min" && !(minutes >= 15 && minutes <= 1000)) {
        findings.push(`stage ${pyRepr(stageName)}: SLA ${cells[0]} min out of bounds — minute counts are bounded 15–1000`);
      }
      if (caseMinutes !== null && minutes > caseMinutes) {
        findings.push(
          `stage ${pyRepr(stageName)}: stage SLA (${cells[0]} ${stripChars(cells[1], "`")}) exceeds the case-level SLA — ` +
            "the case would breach before the stage",
        );
      }
      break;
    }
  }

  // vacuous required-*
  const requiredStage = /^\*\*Required for Case Completion:\*\*[ \t]*Yes\b/m.test(text);
  if (text.includes("required-stages-completed") && stageBlocks(text).length && !requiredStage) {
    findings.push(
      "required-stages-completed is used but no stage declares '**Required for Case Completion:** Yes' — " +
        "validate fails with 'no required stage(s) selected'",
    );
  }
  for (const [, stageName, block] of stageBlocks(text)) {
    const exitSec = sectionBody(block, /^#### Stage Exit Conditions[ \t]*$/m, /^#{1,5} /m);
    if (exitSec === null || !exitSec.includes("required-tasks-completed")) continue;
    let hasRequiredTask = false;
    for (const env of allMatches(
      /\*\*Task envelope\*\*([\s\S]*?)(?=^#{1,6} |\*\*Entry Condition:\*\*|$(?![\s\S]))/gm, block,
    )) {
      for (const [, cells] of tableRows(env[1])) {
        if (cells.length && stripChars(cells[0], "`") === "Yes") hasRequiredTask = true;
      }
    }
    TASK_HEADING.lastIndex = 0;
    if (!hasRequiredTask && TASK_HEADING.test(block)) {
      TASK_HEADING.lastIndex = 0;
      findings.push(
        `stage ${pyRepr(stageName)}: required-tasks-completed completion but no task envelope declares Required: Yes — ` +
          "validate fails with 'no task(s) marked as required'",
      );
    }
    TASK_HEADING.lastIndex = 0;
  }

  // empty stage condition tables
  for (const [, stageName, block] of stageBlocks(text)) {
    const entrySec = sectionBody(block, /^#### Stage Entry Conditions[ \t]*$/m, /^#{1,5} /m);
    if (entrySec !== null && tableRows(entrySec).length === 0) {
      findings.push(`stage ${pyRepr(stageName)}: Stage Entry Conditions has no rows — the stage can never activate`);
    }
    const exitSec = sectionBody(block, /^#### Stage Exit Conditions[ \t]*$/m, /^#{1,5} /m);
    if (exitSec !== null && tableRows(exitSec).length === 0) {
      findings.push(`stage ${pyRepr(stageName)}: Stage Exit Conditions has no rows — the stage can never complete or exit`);
    }
  }

  // entry-vs-case-exit overlap
  const normIf = (cell) => {
    const c = stripChars(cell.trim(), "`");
    return c === "—" || c === "-" || c === "" ? "" : c.replace(/\s+/g, "");
  };
  const caseExitRows = [];
  for (const [, cells] of tableRows(sectionSlice(text, "Case Exit Conditions"))) {
    const sel = cells[0].match(/selected-stage-(completed|exited)\s*\(\s*["“‘']([^"”’']+)/);
    if (sel && cells.length >= 2) {
      caseExitRows.push(JSON.stringify([sel[1], stripIdSuffix(sel[2]).trim(), normIf(cells[1])]));
    }
  }
  if (caseExitRows.length) {
    for (const [stageName, when, cells] of entryRowsAll) {
      const sel = when.match(/selected-stage-(completed|exited)\s*\(\s*["“‘']([^"”’']+)/);
      if (!sel || cells.length < 2) continue;
      const key = JSON.stringify([sel[1], stripIdSuffix(sel[2]).trim(), normIf(cells[1])]);
      if (caseExitRows.includes(key)) {
        findings.push(
          `stage ${pyRepr(stageName)}: entry condition matches a case-exit row (same rule, selector, IF) — ` +
            "case exit takes precedence, leaving the stage permanently unreachable; differentiate the IF guards",
        );
      }
    }
  }

  // exit-overrides-completion
  for (const [, stageName, block] of stageBlocks(text)) {
    const exitSec = sectionBody(block, /^#### Stage Exit Conditions[ \t]*$/m, /^#{1,5} /m);
    if (exitSec === null) continue;
    const rows = [];
    for (const [, cells] of tableRows(exitSec)) {
      const bare = cells.map((c) => stripChars(c, "`"));
      const marks = bare.find((c) => c === "Yes" || c === "No") ?? null;
      if (marks && cells.length >= 2) rows.push([ruleName(cells[0]) ?? "", normIf(cells[1]), marks]);
    }
    for (const [whenY, ifY, marksY] of rows) {
      if (marksY !== "Yes" || !ifY) continue;
      for (const [whenN, ifN, marksN] of rows) {
        if (marksN === "No" && whenN === whenY && !ifN) {
          findings.push(
            `stage ${pyRepr(stageName)}: unguarded exit row shares WHEN ${pyRepr(whenY)} with a guarded completion — ` +
              "the exit always fires first and the stage never completes; give the exit the inverse IF",
          );
        }
      }
    }
  }

  // duplicate case-exit rows
  const seenExitRows = new Set();
  for (const [, cells] of tableRows(sectionSlice(text, "Case Exit Conditions"))) {
    // JSON key stands in for Python's tuple key — collision-free for any cell content.
    const key = JSON.stringify(cells.slice(0, 4).map((c, i) => (i === 1 ? normIf(c) : stripChars(c, "`"))));
    if (seenExitRows.has(key)) {
      findings.push(`duplicate case-exit row ${pyRepr(cells[0])} — identical rules are ambiguous; differentiate or drop one`);
    }
    seenExitRows.add(key);
  }

  // Selector existence
  const stageNames = new Set(stageBlocks(text).map(([, n]) => n.trim()));
  const taskNames = new Set(allMatches(TASK_HEADING, text).map((m) => stripIdSuffix(m[3]).trim()));
  if (stageNames.size) {
    for (let i = 0; i < lines.length; i += 1) {
      for (const call of allMatches(/selected-stage-(?:completed|exited)\s*\(([^)]*)\)/g, lines[i])) {
        for (const arg of quotedArgs(call[1])) {
          if (!stageNames.has(stripIdSuffix(arg).trim())) {
            findings.push(`line ${i + 1}: stage selector references ${pyRepr(arg)} — no stage with that display name exists`);
          }
        }
      }
      for (const call of allMatches(/selected-tasks-completed\s*\(([^)]*)\)/g, lines[i])) {
        for (const arg of quotedArgs(call[1])) {
          if (taskNames.size && !taskNames.has(stripIdSuffix(arg).trim())) {
            findings.push(`line ${i + 1}: task selector references ${pyRepr(arg)} — no task with that display name exists`);
          }
        }
      }
    }
  }

  // selected-tasks-completed scope
  for (const [, stageName, block] of stageBlocks(text)) {
    const ownTasks = new Set(allMatches(TASK_HEADING, block).map((m) => stripIdSuffix(m[3]).trim()));
    const adhocTasks = new Set();
    const tasksInBlock = allMatches(TASK_HEADING, block);
    for (let index = 0; index < tasksInBlock.length; index += 1) {
      const end = index + 1 < tasksInBlock.length ? tasksInBlock[index + 1].index : block.length;
      const tb = block.slice(tasksInBlock[index].index, end);
      if (/^\*\*Activation Mode:\*\*[ \t]*`?adhoc\b/m.test(tb)) {
        adhocTasks.add(stripIdSuffix(tasksInBlock[index][3]).trim());
      }
    }
    for (const call of allMatches(/selected-tasks-completed\s*\(([^)]*)\)/g, block)) {
      for (const arg of quotedArgs(call[1])) {
        const name = stripIdSuffix(arg).trim();
        if (adhocTasks.has(name)) {
          findings.push(
            `stage ${pyRepr(stageName)}: selected-tasks-completed selects adhoc task ${pyRepr(name)} — it selects only non-adhoc tasks`,
          );
        } else if (taskNames.size && taskNames.has(name) && !ownTasks.has(name)) {
          findings.push(
            `stage ${pyRepr(stageName)}: selected-tasks-completed selects ${pyRepr(name)} from another stage — it selects only tasks in the SAME stage`,
          );
        }
      }
    }
  }

  // sla-status-change SLA-title closure
  if (slaTitles.size) {
    for (let i = 0; i < lines.length; i += 1) {
      for (const call of allMatches(/sla-status-change\s*\(([^)]*)\)/gi, lines[i])) {
        const args = quotedArgs(call[1]);
        if (args.length < 2) continue;
        const target = args[0].trim().toLowerCase();
        const declared = slaTitles.get(target);
        if (declared !== undefined) {
          const lowered = new Set([...declared].map((t) => t.toLowerCase()));
          if (!lowered.has(args[1].trim().toLowerCase())) {
            findings.push(
              `line ${i + 1}: sla-status-change references SLA title ${pyRepr(args[1])} but target ${pyRepr(args[0])} declares: ` +
                pySorted(declared).join(", "),
            );
          }
        }
      }
    }
  }
  return findings;
}

// ─────────────────────────────────────────────────────── audit

function audit(sddPath, draftPath) {
  const findings = [];
  const text = readFileSync(sddPath, "utf-8");

  const first = splitLines(text).map((l) => l.trim()).find((l) => l !== "") ?? "";
  if (!first.startsWith("# SDD — ")) {
    findings.push("first heading must be '# SDD — {Case Name}'");
  }

  for (const heading of REQUIRED_HEADINGS) {
    if (!new RegExp(`^${reEscape(heading)}[ \\t]*$`, "m").test(text)) {
      findings.push(`missing required heading ${pyRepr(heading)}`);
    }
  }
  for (const heading of SUMMARY_ONLY_HEADINGS) {
    if (new RegExp(`^## ${reEscape(heading)}[ \\t]*$`, "m").test(text)) {
      findings.push(`summary-only heading '## ${heading}' — render the full template instead`);
    }
  }

  if (!text.includes(CASE_VARIABLES_HEADER)) {
    findings.push(`Case Variables table must use the literal header ${pyRepr(CASE_VARIABLES_HEADER)}`);
  }
  if (LETTERED_TASK.test(text)) {
    findings.push("lettered task prefixes (Task R.1 / W.1 / CC.1 / ESC.1) — renumber as Task S{K}.{M}");
  }
  splitLines(text).forEach((line, i) => {
    if (/\\n\s*(?:\*\*|#|\|)/.test(line)) {
      findings.push(
        `line ${i + 1}: literal \\n escape corrupts the document structure — rewrite the block with real newlines`,
      );
    }
  });

  const stages = stageBlocks(text);
  if (stages.length === 0) {
    findings.push("no '### Stage {N}:' / '### Secondary Stage:' blocks found");
  }
  for (const [kind, stageName, block] of stages) {
    for (const marker of STAGE_MARKERS) {
      if (!block.includes(marker)) {
        findings.push(`stage ${pyRepr(stageName)} missing ${pyRepr(marker)}`);
      }
    }
    const stageType = block.match(/^\*\*Type:\*\*[ \t]*([^\n]+)/m);
    if (stageType && !["Stage", "ExceptionStage"].includes(stageType[1].trim())) {
      findings.push(
        `stage ${pyRepr(stageName)} has '**Type:** ${stageType[1].trim()}' — the stage Type literal is 'Stage'; ` +
          "secondary-ness lives in the heading, '**Stage Kind:** secondary', and '**Interrupting:**'",
      );
    }
    if (kind === "Secondary Stage" && !/^\*\*Interrupting:\*\*[ \t]*(Yes|No)\b/m.test(block)) {
      findings.push(`secondary stage ${pyRepr(stageName)} missing explicit '**Interrupting:** Yes' or 'No'`);
    }
    if (
      kind === "Secondary Stage" &&
      block.includes("return-to-origin") &&
      !/^\*\*Interrupting:\*\*[ \t]*Yes\b/m.test(block)
    ) {
      findings.push(
        `secondary stage ${pyRepr(stageName)} exits return-to-origin but does not declare '**Interrupting:** Yes'`,
      );
    }

    const tasks = allMatches(TASK_HEADING, block);
    if (tasks.length === 0) {
      findings.push(
        `stage ${pyRepr(stageName)} has no '##### Task' detail blocks — every task in its Tasks table needs one`,
      );
      continue;
    }
    for (let index = 0; index < tasks.length; index += 1) {
      const end = index + 1 < tasks.length ? tasks[index + 1].index : block.length;
      const taskBlock = block.slice(tasks[index].index, end);
      const taskName = stripIdSuffix(tasks[index][3]);
      for (const marker of TASK_MARKERS) {
        if (!taskBlock.includes(marker)) {
          findings.push(`task ${pyRepr(taskName)} missing ${pyRepr(marker)}`);
        }
      }
      const typeMatch = taskBlock.match(/^\*\*Type:\*\*[ \t]*`?([a-z-]+)/m);
      if (typeMatch) {
        const markers = TASK_DETAIL_MARKERS.get(typeMatch[1]);
        if (markers && !markers.some((marker) => taskBlock.includes(marker))) {
          findings.push(
            `task ${pyRepr(taskName)} (type ${typeMatch[1]}) missing type detail block ${pyRepr(markers[0])}`,
          );
        }
      }
    }
  }

  // sla-status-change arg shape + target resolution
  const validTargets = new Set(["root", ...stageBlocks(text).map(([, n]) => n.toLowerCase())]);
  splitLines(text).forEach((line, i) => {
    for (const call of allMatches(/sla-status-change\s*\(([^)]*)\)/gi, line)) {
      const args = quotedArgs(call[1]);
      if (args.length && args.length !== 2 && args.length !== 3) {
        findings.push(
          `line ${i + 1}: sla-status-change takes ("<SLA target>","<SLA Title>") ` +
            `or (...,"<At-Risk Escalation Display Name>"); got ${args.length} args`,
        );
      }
      if (args.length && validTargets.size && !validTargets.has(args[0].trim().toLowerCase())) {
        findings.push(
          `line ${i + 1}: sla-status-change target ${pyRepr(args[0])} is neither the literal 'root' (case-level) ` +
            "nor a stage declared in this SDD — never the case name or a synonym",
        );
      }
    }
  });

  let carried = new Set();
  const draftIsFile = draftPath !== null && (() => {
    try { return statSync(draftPath).isFile(); } catch { return false; }
  })();
  if (draftIsFile) {
    const draftText = readFileSync(draftPath, "utf-8");
    carried = new Set([
      ...stageBlocks(draftText).map(([, n]) => n.trim()),
      ...allMatches(/^#{5} Task [A-Za-z0-9.]+: ([^\n]+)$/gm, draftText).map((m) => stripIdSuffix(m[1]).trim()),
    ]);
  }
  const [facts, degraded] = loadModelFacts();
  if (degraded) findings.push(`model checks disarmed: ${degraded}`);
  findings.push(...lineageFindings(text));
  findings.push(...modelFindings(text, facts, carried));
  findings.push(
    ...contractFindings(
      text,
      Object.keys(facts).length ? facts : { gate_rules: new Map(), yes_when: new Set(), no_when: new Set() },
    ),
  );

  const draftFindings = [];
  if (draftPath !== null) {
    if (!draftIsFile) {
      draftFindings.push(
        `${draftPath} is gone — never delete or rename the draft; finalize renders a new sdd.md beside it`,
      );
    } else {
      const draft = readFileSync(draftPath, "utf-8");
      const draftInv = inventory(draft);
      const finalInv = inventory(text);
      const eq = (a, b) => a.length === b.length && a.every((p, i) => p[0] === b[i][0] && p[1] === b[i][1]);
      if (!eq(draftInv, finalInv)) {
        const has = (list, p) => list.some((q) => q[0] === p[0] && q[1] === p[1]);
        const missing = draftInv.filter((p) => !has(finalInv, p)).map(([s, t]) => `${s} / ${t}`);
        const added = finalInv.filter((p) => !has(draftInv, p)).map(([s, t]) => `${s} / ${t}`);
        const detail = [
          missing.length ? `missing: ${missing.slice(0, 8).join(", ")}` : "",
          added.length ? `added/renamed: ${added.slice(0, 8).join(", ")}` : "",
          !missing.length && !added.length ? "order changed" : "",
        ].filter(Boolean).join("; ");
        draftFindings.push(
          `stage/task inventory differs from draft (draft=${draftInv.length}, final=${finalInv.length}) — ${detail}`,
        );
      }
      const finalExpr = jsExpressions(text);
      const lost = pySorted([...jsExpressions(draft)].filter((e) => !finalExpr.has(e)));
      for (const expression of lost.slice(0, 10)) {
        draftFindings.push(`draft policy expression lost: ${expression}`);
      }
      draftFindings.push(...unencodedThresholds(draft, text));
    }
  }

  return [...draftFindings, ...findings];
}

function emitAdvisories(advisories) {
  if (!advisories.length) return;
  process.stderr.write("\nADVISORY (does not gate AUDIT OK — fix only if you agree):\n");
  advisories.slice(0, 10).forEach((a, n) => process.stderr.write(`  ${n + 1}. ${a}\n`));
  if (advisories.length > 10) {
    process.stderr.write(`  … and ${advisories.length - 10} more\n`);
  }
}

function main() {
  const args = process.argv.slice(2);
  let draft = null;
  const i = args.indexOf("--draft");
  if (i !== -1) {
    draft = args[i + 1];
    args.splice(i, 2);
  }
  if (args.length !== 1) {
    process.stderr.write(`${DOC}\n`);
    process.exit(1);
  }
  const all = audit(args[0], draft);
  const findings = all.filter((f) => !f.startsWith(ADVISORY));
  const advisories = all.filter((f) => f.startsWith(ADVISORY)).map((f) => f.slice(ADVISORY.length));
  if (findings.length) {
    const shown = findings.slice(0, 40);
    process.stderr.write("AUDIT FAIL — repair these, then re-run:\n");
    shown.forEach((f, n) => process.stderr.write(`  ${n + 1}. ${f}\n`));
    if (findings.length > shown.length) {
      process.stderr.write(`  … and ${findings.length - shown.length} more\n`);
    }
    emitAdvisories(advisories);
    process.exit(1);
  }
  process.stdout.write("AUDIT OK: sdd.md template shape is clean\n");
  emitAdvisories(advisories);
}

main();
