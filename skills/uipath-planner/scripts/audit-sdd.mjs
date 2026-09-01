#!/usr/bin/env node
/**
 * Deterministic template-shape audit for a planner-authored Case Management SDD.
 *
 * Usage:
 *     node audit-sdd.mjs <sdd.md> [--draft <sdd.draft.md>]
 *
 * Read-only. Exit 0 = shape-clean. Exit 1 = numbered findings on stderr; repair
 * the document with Write/Edit and re-run until clean. `--draft` additionally
 * verifies the finalized document preserves the draft's ordered stage/task
 * inventory and every draft `=js:` expression.
 *
 * Node stdlib only — no dependencies, no install step.
 */

import { readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const USAGE = `Deterministic template-shape audit for a planner-authored Case Management SDD.

Usage:
    node audit-sdd.mjs <sdd.md> [--draft <sdd.draft.md>]

Read-only. Exit 0 = shape-clean. Exit 1 = numbered findings on stderr; repair
the document with Write/Edit and re-run until clean. \`--draft\` additionally
verifies the finalized document preserves the draft's ordered stage/task
inventory and every draft \`=js:\` expression.
`;

// ---------------------------------------------------------------------------
// Python-parity helpers. Findings text is the agent-facing interface, so quoting
// and number formatting must render exactly as the Python original did.
// ---------------------------------------------------------------------------

/** Python `repr()` for a string: single quotes unless that forces an escape. */
function repr(value) {
  const s = String(value);
  const quote = s.includes("'") && !s.includes('"') ? '"' : "'";
  let out = quote;
  for (const ch of s) {
    if (ch === "\\") out += "\\\\";
    else if (ch === quote) out += "\\" + ch;
    else if (ch === "\n") out += "\\n";
    else if (ch === "\r") out += "\\r";
    else if (ch === "\t") out += "\\t";
    else {
      const code = ch.codePointAt(0);
      if (code < 0x20 || code === 0x7f) out += "\\x" + code.toString(16).padStart(2, "0");
      else out += ch;
    }
  }
  return out + quote;
}

/** Python `f"{n:,}"`. */
const comma = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");

/** Python `str.splitlines()` — no phantom trailing element. */
function splitLines(text) {
  const parts = text.split(/\r\n|\n|\r/);
  if (parts.length && parts[parts.length - 1] === "") parts.pop();
  return parts;
}

/** Regex-metacharacter escape for literal interpolation. */
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/** Python `str.strip("`")`. */
const stripTicks = (s) => s.replace(/^`+|`+$/g, "");

/** Fresh global copy per call — module regexes stay non-global, so no shared lastIndex. */
function* finditer(pattern, text) {
  const flags = pattern.flags.includes("g") ? pattern.flags : pattern.flags + "g";
  const re = new RegExp(pattern.source, flags);
  let match;
  while ((match = re.exec(text)) !== null) {
    yield match;
    if (match[0] === "") re.lastIndex += 1;
  }
}

/** Python `re.search` — non-global exec never mutates lastIndex. */
const search = (pattern, text) => pattern.exec(text);

/** Python `re.fullmatch`. */
function fullmatch(pattern, text) {
  const match = new RegExp(pattern.source, pattern.flags).exec(text);
  return Boolean(match) && match.index === 0 && match[0].length === text.length;
}

const union = (...sets) => new Set(sets.flatMap((s) => [...s]));
/** Python truthiness for the parsed-facts dict: an empty dict is falsy. */
const hasFacts = (facts) => Boolean(facts) && Object.keys(facts).length > 0;

// ---------------------------------------------------------------------------

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

// task type -> [detail-block heading, ...alternate literal markers]
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

const STAGE_HEADING = /^###\s+(Stage\s+\d+|Secondary Stage):\s*(.+?)\s*$/m;
const TASK_HEADING = /^#####\s+Task\s+(S?\d+|[A-Z]{1,4})\.(\d+):\s*(.+?)\s*$/m;
const LETTERED_TASK = /^#####\s+Task\s+[A-RT-Z]+[A-Z]*\.\d/m;

const stripIdSuffix = (name) => name.replace(/\s*\(`[^`]*`\)\s*$/, "").trim();

/** [kind, display name, block text] for each stage heading. */
function stageBlocks(text) {
  const matches = [...finditer(STAGE_HEADING, text)];
  const section3 = search(/^## Section 3: Personas & App Views\s*$/m, text);
  const docEnd = section3 ? section3.index : text.length;
  return matches.map((match, index) => {
    const end = index + 1 < matches.length ? matches[index + 1].index : docEnd;
    return [match[1], stripIdSuffix(match[2]), text.slice(match.index, end)];
  });
}

/** Ordered [stage, task] names, id suffixes stripped. */
function inventory(text) {
  const entries = [];
  for (const [, stageName, block] of stageBlocks(text)) {
    for (const task of finditer(TASK_HEADING, block)) {
      entries.push([stageName, stripIdSuffix(task[3])]);
    }
  }
  return entries;
}

function jsExpressions(text) {
  const found = new Set();
  for (const match of finditer(/=js:[^|\n]+/, text)) {
    found.add(match[0].replace(/\s+/g, " ").trim());
  }
  return found;
}

const HIGH_WORDS = String.raw`over|above|at\s+least|more\s+than|greater\s+than|in\s+excess\s+of|exceed(?:s|ing)?`;
const LOW_WORDS = String.raw`under|below|at\s+most|less\s+than`;
const COMPARATOR_THRESHOLD = new RegExp(
  String.raw`(>=|<=|>|<|≥|≤|\b(?:${HIGH_WORDS}|${LOW_WORDS})\b)\s*` +
    String.raw`\$\s*(\d[\d,]*(?:\.\d+)?)\s*([mk])?\b`,
  "i",
);
const COMPARATOR_TOKEN = new RegExp(String.raw`(>=|<=|>|<|≥|≤|\b(?:${HIGH_WORDS}|${LOW_WORDS})\b)`, "i");
const HIGH_WORDS_ONLY = new RegExp(HIGH_WORDS);
const EXECUTABLE_LINE = /=js:|vars\.|\bowner\b|\brecipient\b|Role:/i;
const PROSE_MARKER = /^\*\*(Design Rationale|Description):\*\*/m;

function comparatorDirection(token) {
  const value = token.toLowerCase().trim();
  if ([">", ">=", "≥"].includes(value) || fullmatch(HIGH_WORDS_ONLY, value)) return "high";
  return "low";
}

/**
 * Spellings of one currency threshold: '5' + 'M' -> 5M, 5 million, 5000000, 5,000,000.
 *
 * The bare short numeral ('5') is deliberately excluded — it would match any
 * digit in an executable line and make the check vacuous.
 */
function thresholdVariants(number, suffix) {
  const bare = number.replace(/,/g, "");
  if (suffix) {
    const lower = suffix.toLowerCase();
    const factor = lower === "m" ? 1000000 : 1000;
    const word = lower === "m" ? "million" : "thousand";
    const variants = [`${bare}${lower}`, `${bare} ${word}`];
    if (!bare.includes(".")) {
      const expanded = String(parseInt(bare, 10) * factor);
      variants.push(expanded, comma(parseInt(expanded, 10)));
    }
    return variants;
  }
  const variants = [bare];
  if (!bare.includes(".")) variants.push(comma(parseInt(bare, 10)));
  return variants;
}

/**
 * Draft comparator-currency thresholds with no executable encoding in the final.
 *
 * A threshold counts as encoded when some final line mentions one of its
 * spellings AND carries an executable signal (`=js:` / `vars.` / owner /
 * recipient / `Role:`). Prose repetition alone is not an encoding.
 */
function unencodedThresholds(draft, final) {
  const findings = [];
  const seen = new Set();
  // Rationale/Description prose never counts as an encoding — the guard must
  // live in an executable table cell (owner/recipient/WHEN/IF/Inputs).
  const executableLines = splitLines(final).filter(
    (line) => EXECUTABLE_LINE.test(line) && !search(PROSE_MARKER, line.trim()),
  );
  for (const match of finditer(COMPARATOR_THRESHOLD, draft)) {
    const direction = comparatorDirection(match[1]);
    const variants = thresholdVariants(match[2], match[3]);
    const key = `${variants[variants.length - 1]} ${direction}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const needles = variants.map((v) => new RegExp(String.raw`(?<![\w.])${esc(v)}(?!\w)`, "i"));
    let covered = false;
    for (const line of executableLines) {
      if (!needles.some((n) => n.test(line))) continue;
      const ternary = line.includes("?") && line.slice(line.indexOf("?") + 1).includes(":");
      const lineDirs = new Set(
        [...finditer(COMPARATOR_TOKEN, line)].map((token) => comparatorDirection(token[1])),
      );
      if (ternary || lineDirs.has(direction)) {
        covered = true;
        break;
      }
    }
    if (!covered) {
      findings.push(
        `draft threshold policy ${repr(match[0].trim())} has no ${direction}-side executable encoding — ` +
          "add the guard to an owner/recipient/WHEN/IF cell (fast-path step 9), e.g. " +
          '`=js:vars.<attr> > <threshold> ? "Role:<ExceptionRole>" : "Role:<DefaultRole>"`; ' +
          "Rationale/Description prose does not count",
      );
    }
  }
  return findings;
}

const VARIABLE_ROW =
  /^\|\s*([A-Za-z]\w*)\s*\|\s*(In|Out|Variable)\s*\|\s*[^|]*\|\s*([^|]*?)\s*\|\s*[^|]*\|\s*([^|]*?)\s*\|/m;

const variableRows = (text) => [...finditer(VARIABLE_ROW, text)].map((m) => [m[1], m[2], m[3], m[4]]);

/** Every identifier the document produces: an Outputs extract or an assignment. */
function producedNames(text) {
  const produced = new Set();
  for (const match of finditer(/->\s*([A-Za-z]\w*)/, text)) produced.add(match[1]);
  for (const match of finditer(/\b([A-Za-z]\w*)\s*=\s*(?!=)/, text)) produced.add(match[1]);
  return produced;
}

/**
 * Mapping + lineage closure: every consumed variable is declared and produced
 * (-> output, `X =` assignment, Default, or trigger-sourced).
 */
function lineageFindings(text) {
  const findings = [];
  const category = new Map();
  const srcTrig = new Map();
  const defaults = new Map();
  for (const [name, cat, st, d] of variableRows(text)) {
    category.set(name, cat);
    srcTrig.set(name, st.trim());
    defaults.set(name, d.trim());
  }
  if (category.size === 0) return findings; // template checks already flag a missing table
  const refs = new Set([...finditer(/=vars\.([A-Za-z]\w*)/, text)].map((m) => m[1]));
  refs.delete("X");
  const undeclared = [...refs].filter((r) => !category.has(r)).sort();
  if (undeclared.length) {
    findings.push(
      `${undeclared.length} =vars consumed but not declared in Case Variables: ${undeclared.join(", ")}`,
    );
  }
  const produced = producedNames(text);
  const openLineage = [...refs]
    .filter(
      (r) =>
        category.has(r) &&
        category.get(r) !== "In" &&
        !defaults.get(r) &&
        !srcTrig.get(r) &&
        !produced.has(r),
    )
    .sort();
  for (const name of openLineage) {
    findings.push(
      `variable ${repr(name)} is consumed but never produced — keep its producer output row ` +
        `(\`-> ${name}\`), assignment, Default, or trigger source`,
    );
  }
  return findings;
}

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const LAYERS_MD = join(SCRIPT_DIR, "..", "references", "case-design-layers-guide.md");
const LAYERS_MD_NAME = "case-design-layers-guide.md";

/**
 * Parse the canonical tables in the case reference files.
 *
 * Reads the `### Task types` table (column 1 literals), the `### Lifecycle
 * gates` table (legal WHEN rules per gate slot), and the `### Naming rules`
 * fenced regex — all from case-design-layers-guide.md.
 *
 * Returns `[facts, degraded]`. `degraded` is null on a clean parse and a reason
 * string when the model checks could not be armed — a missing guide or a parse
 * that came back empty. Never degrade silently: the caller turns the reason into
 * a finding, so a renamed heading or a reshaped table fails loudly instead of
 * no-op'ing the task-type enum, WHEN pairing, and naming checks.
 */
function loadModelFacts() {
  let text;
  try {
    text = readFileSync(LAYERS_MD, "utf-8");
  } catch {
    return [{}, `${LAYERS_MD_NAME} not found beside this script`];
  }

  const section = (heading) => {
    const match = search(
      new RegExp(String.raw`^### ${esc(heading)}\s*$(.*?)(?=^#|(?![\s\S]))`, "ms"),
      text,
    );
    return match ? match[1] : "";
  };

  const facts = {};
  facts.task_types = new Set(
    [...finditer(/^\|\s*`([a-z][a-z-]+)`\s*\|/m, section("Task types"))].map((m) => m[1]),
  );
  const yesWhen = new Set();
  const noWhen = new Set();
  const gateRules = new Map();
  for (const row of finditer(/^\|([^|]+)\|([^|]+)\|([^|]+)\|/m, section("Lifecycle gates"))) {
    const gate = row[1].trim();
    const marks = row[2].trim();
    const rules = new Set([...finditer(/`([a-z][a-z-]+)`/, row[3])].map((m) => m[1]));
    if (rules.size === 0) continue;
    gateRules.set(gate, rules);
    if (marks === "Yes") for (const rule of rules) yesWhen.add(rule);
    else if (marks === "No") for (const rule of rules) noWhen.add(rule);
  }
  facts.yes_when = yesWhen;
  facts.no_when = noWhen;
  facts.gate_rules = gateRules;
  const pattern = search(/```\s*(\^[^\n`]+\$)\s*```/, section("Naming rules"));
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
      `${LAYERS_MD_NAME} parsed but ` +
        empty.join(", ") +
        " came back empty — the heading was renamed or the table reshaped; the model checks are " +
        "disarmed until it is restored",
    ];
  }
  return [facts, null];
}

/**
 * Checks driven by the canonical model tables: task-type enum, WHEN/Marks-Complete
 * pairing legality, and display-name character rules. `carriedNames` — stage/task
 * display names present in the draft — are exempt from the minting charset (the
 * naming contract preserves them verbatim); the ':' ban stays structural. `facts`
 * comes from loadModelFacts(); an empty object means the caller already emitted
 * the degradation finding, so skip these checks rather than assert on missing tables.
 */
function modelFindings(text, facts, carriedNames = new Set()) {
  if (!hasFacts(facts)) return [];
  const findings = [];

  for (const match of finditer(/^\*\*Type:\*\*\s*`?([a-z][a-z-]+)`?\s*$/m, text)) {
    if (!facts.task_types.has(match[1])) {
      findings.push(
        `task type ${repr(match[1])} outside the closed enum (case-design-layers-guide.md § Task types): ` +
          [...facts.task_types].sort().join(", "),
      );
    }
  }

  // WHEN x Marks-Complete pairing applies only inside tables whose header carries a
  // 'Marks ... Complete' column — entry tables put Yes/No in their Interrupting column,
  // and reading that cell as Marks-Complete false-flags legal entry rows.
  const knownRules = union(facts.yes_when, facts.no_when);
  const lines = splitLines(text);
  let marksCol = null;
  for (let index = 0; index < lines.length; index += 1) {
    const lineNo = index + 1;
    const stripped = lines[index].trim();
    if (!stripped.startsWith("|")) {
      marksCol = null;
      continue;
    }
    const cells = stripped.replace(/^\|+|\|+$/g, "").split("|").map((c) => c.trim());
    if (cells.some((c) => fullmatch(/Marks (Stage|Case) Complete/, c))) {
      marksCol = cells.findIndex((c) => c.startsWith("Marks "));
      continue;
    }
    if (marksCol === null || cells.length <= marksCol || [...cells[0]].every((ch) => "-: ".includes(ch))) {
      continue;
    }
    const when = search(/^`?([a-z][a-z-]+)/, cells[0]);
    const marks = ["Yes", "No"].includes(cells[marksCol]) ? cells[marksCol] : null;
    if (!when || marks === null || !knownRules.has(when[1])) continue;
    const legal = marks === "Yes" ? facts.yes_when : facts.no_when;
    if (!legal.has(when[1])) {
      findings.push(
        `line ${lineNo}: WHEN ${repr(when[1])} with Marks Complete ${repr(marks)} is an illegal ` +
          "pair (case-design-layers-guide.md § Lifecycle gates)",
      );
    }
  }

  const namePattern = facts.name_pattern;
  if (namePattern) {
    const nameFinding = (kind, rawName) => {
      const name = rawName.trim();
      if (name.includes(":")) {
        return `${kind} name ${repr(name)} contains ':' — the structural ban; case-execution events are colon-delimited`;
      }
      if (carriedNames.has(name)) return null; // read from the draft: preserved verbatim, minting charset does not apply
      if (!fullmatch(namePattern, name)) {
        return (
          `${ADVISORY}${kind} name ${repr(name)} uses characters outside the safe display set in\n` +
          "     case-design-layers-guide.md § Naming rules. Only ':' is known to break routing, so this does not\n" +
          "     gate: prefer the safe set when MINTING a name, and keep a name the user or the source supplied"
        );
      }
      return null;
    };

    for (const [kind, name] of stageBlocks(text)) {
      const finding = nameFinding(kind.toLowerCase(), name);
      if (finding) findings.push(finding);
    }
    for (const match of finditer(/^#{5} Task [S\d.]+: ([^\n]+)$/m, text)) {
      const finding = nameFinding("task", stripIdSuffix(match[1]));
      if (finding) findings.push(finding);
    }
  }
  return findings;
}

const EXIT_TYPES_YES = new Set(["exit-only", "return-to-origin", "wait-for-user"]);
const EXIT_TYPES_NO = new Set(["exit-only", "wait-for-user"]);
const RECIPIENT_PREFIX = /^(Role|User|UserGroup|Email|Expression):/;
const FORBIDDEN_VOCAB = [
  "groupOperator", "savedFilterTrees", "io-binding", "auto-mint", "originalVar", "inputOutputs[",
];

/** Body of a `### {heading}` section up to the next heading of any level. */
function sectionSlice(text, heading) {
  const match = search(
    new RegExp(String.raw`^### ${esc(heading)}\s*$(.*?)(?=^#{1,5} |(?![\s\S]))`, "ms"),
    text,
  );
  return match ? match[1] : "";
}

/**
 * [offset line index, cells] for pipe-table body rows in a chunk.
 *
 * Header detection is structural: a ruler row (`|---|...`) is skipped, and so is
 * the row immediately preceding it — never a name list, which silently passes
 * headers it does not know (e.g. `| T# | Trigger Type | ... |`).
 */
function tableRows(chunk) {
  const lines = splitLines(chunk);

  const isRuler = (line) => {
    const stripped = line.trim();
    if (!stripped.startsWith("|")) return false;
    const cells = stripped.replace(/^\|+|\|+$/g, "").split("|").map((c) => c.trim());
    return cells.length > 0 && cells.every((c) => c !== "" && [...c].every((ch) => "-: ".includes(ch)));
  };

  const rows = [];
  for (let i = 0; i < lines.length; i += 1) {
    const stripped = lines[i].trim();
    if (!stripped.startsWith("|") || isRuler(lines[i])) continue;
    if (i + 1 < lines.length && isRuler(lines[i + 1])) continue; // header row
    const cells = stripped.replace(/^\|+|\|+$/g, "").split("|").map((c) => c.trim());
    if (cells.length) rows.push([i, cells]);
  }
  return rows;
}

function ruleName(cell) {
  const match = search(/^`?([a-z][a-z-]+)/, cell.trim());
  return match ? match[1] : null;
}

/**
 * SLA titles per target: 'root' from the §1.1 metadata row; each stage from its
 * `**SLA Title:**` lines. Casefolded keys and titles.
 */
function declaredSlaTitles(text) {
  const titles = new Map();
  const meta = sectionSlice(text, "Case Metadata");
  const row = search(/^\|\s*SLA Title\s*\|\s*([^|]+?)\s*\|/m, meta);
  if (row && !["—", ""].includes(row[1].trim())) titles.set("root", new Set([row[1].trim()]));
  for (const [, stageName, block] of stageBlocks(text)) {
    const found = new Set(
      [...finditer(/^\*\*SLA Title:\*\*\s*([^\n<]+)/m, block)].map((m) => m[1].trim()),
    );
    if (found.size) titles.set(stageName.toLowerCase(), found);
  }
  return titles;
}

const SELECTED_STAGE_CALL = /selected-stage-(completed|exited)\s*\(\s*["“‘']([^"”’']+)/;
const QUOTED_ARG = /["“‘']([^"”’']+)[”’'"]/;

/**
 * Deterministic contract checks beyond template shape: gate-slot WHEN legality,
 * exit-type pairing, SLA title closure, uniqueness, recipients, buttons, Out producers,
 * completion row, wait-for-user pairing, markers, vocabulary.
 */
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
        `forbidden skill-internal term ${repr(token)} in the SDD body (case-sdd-template.md § Validation footer)`,
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
        `Out variable ${repr(name)} has no Default and no producing Outputs row (\`-> ${name}\` / \`${name} = ...\`)`,
      );
    }
  }

  // Uniqueness: stage labels and task display names, case-wide
  const seenStages = new Set();
  const seenTasks = new Map();
  for (const [, stageName, block] of stageBlocks(text)) {
    const key = stageName.trim();
    if (seenStages.has(key)) {
      findings.push(`duplicate stage label ${repr(key)} — stage labels are unique across the case`);
    }
    seenStages.add(key);
    for (const task of finditer(TASK_HEADING, block)) {
      const taskName = stripIdSuffix(task[3]).trim();
      if (seenTasks.has(taskName) && seenTasks.get(taskName) !== stageName + task[0]) {
        findings.push(
          `duplicate task display name ${repr(taskName)} — task names are unique across the whole case`,
        );
      }
      if (!seenTasks.has(taskName)) seenTasks.set(taskName, stageName + task[0]);
    }
  }

  const gateRules = facts.gate_rules ?? new Map();
  const stageEntryLegal = gateRules.get("Stage entry") ?? new Set();
  const taskEntryLegal = gateRules.get("Task entry") ?? new Set();
  const slaTitles = declaredSlaTitles(text);
  const yesWhen = facts.yes_when ?? new Set();
  const noWhen = facts.no_when ?? new Set();

  for (const [, stageName, block] of stageBlocks(text)) {
    // Stage entry WHEN legality
    const entry = search(
      /^#### Stage Entry Conditions\s*$(.*?)(?=^#{1,5} |\*\*Task envelope\*\*|(?![\s\S]))/ms,
      block,
    );
    if (entry && stageEntryLegal.size) {
      const wideSet = union(yesWhen, noWhen, taskEntryLegal, new Set([
        "case-entered", "adhoc", "runs-sequentially", "current-stage-entered",
      ]));
      for (const [, cells] of tableRows(entry[1])) {
        const rule = ruleName(cells[0]);
        if (rule && !stageEntryLegal.has(rule) && wideSet.has(rule)) {
          findings.push(
            `stage ${repr(stageName)}: entry WHEN ${repr(rule)} is not a legal stage-entry rule (case-design-layers-guide.md § Lifecycle gates)`,
          );
        }
      }
    }
    // Stage exit rows: Exit Type x Marks Stage Complete legality
    const exitSec = search(/^#### Stage Exit Conditions\s*$(.*?)(?=^#{1,5} |(?![\s\S]))/ms, block);
    if (exitSec) {
      for (const [, cells] of tableRows(exitSec[1])) {
        const bare = cells.map((c) => stripTicks(c.trim()));
        const etype = bare.find((c) => EXIT_TYPES_YES.has(c)) ?? null;
        const marks = bare.find((c) => c === "Yes" || c === "No") ?? null;
        if (etype && marks) {
          const legal = marks === "Yes" ? EXIT_TYPES_YES : EXIT_TYPES_NO;
          if (!legal.has(etype)) {
            findings.push(
              `stage ${repr(stageName)}: exit type ${repr(etype)} with Marks Stage Complete ${repr(marks)} is illegal — ` +
                `legal for ${marks}: ${[...legal].sort().join(", ")}`,
            );
          }
        }
      }
    }
    // Task entry WHEN legality + Buttons Maps To
    const tasks = [...finditer(TASK_HEADING, block)];
    for (let index = 0; index < tasks.length; index += 1) {
      const task = tasks[index];
      const end = index + 1 < tasks.length ? tasks[index + 1].index : block.length;
      const taskBlock = block.slice(task.index, end);
      const taskName = stripIdSuffix(task[3]);
      const entryTbl = search(/\*\*Entry Condition:\*\*(.*?)(?=\*\*Task envelope\*\*|(?![\s\S]))/s, taskBlock);
      if (entryTbl && tableRows(entryTbl[1]).length === 0) {
        findings.push(
          `task ${repr(taskName)}: Entry Condition has no table rows — an executable gate collapsed ` +
            "into prose drops out of the planning handoff (and a task with no entry never starts)",
        );
      }
      if (entryTbl && taskEntryLegal.size) {
        const wideSet = union(yesWhen, noWhen, stageEntryLegal);
        for (const [, cells] of tableRows(entryTbl[1])) {
          const rule = ruleName(cells[0]);
          if (rule && !taskEntryLegal.has(rule) && wideSet.has(rule)) {
            findings.push(
              `task ${repr(taskName)}: entry WHEN ${repr(rule)} is not a legal task-entry rule (case-design-layers-guide.md § Lifecycle gates)`,
            );
          }
        }
      }
      const recipient = search(/^\*\*Recipient:\*\*\s*([^\n]+)/m, taskBlock);
      if (recipient) {
        const value = stripTicks(recipient[1].trim());
        if (
          !["—", "<UNRESOLVED>"].includes(value) &&
          !RECIPIENT_PREFIX.test(value) &&
          !value.startsWith("=")
        ) {
          findings.push(
            `task ${repr(taskName)}: Recipient ${repr(value)} lacks a typed prefix (Role:/User:/UserGroup:/Email:/Expression:)`,
          );
        }
      }
    }
  }

  // Buttons Maps To LHS: a §1.5 name, taskOutcome, or the task's own output
  // (read downstream via a direct producer reference). Flag only true orphans —
  // an identifier that never occurs outside Buttons tables is a typo or dead route.
  const declaredVars = new Set(variableRows(text).map(([name]) => name));
  declaredVars.add("taskOutcome");
  const buttonSpans = [
    ...finditer(/^\|\s*Button\s*\|\s*Maps To\s*\|[^\n]*$(.*?)(?=^[^|]|(?![\s\S]))/dms, text),
  ].map((m) => m.indices[1]);
  let outside = "";
  buttonSpans.forEach(([start], i) => {
    outside += text.slice(i ? buttonSpans[i - 1][1] : 0, start);
  });
  outside += buttonSpans.length ? text.slice(buttonSpans[buttonSpans.length - 1][1]) : text;
  for (const [start, end] of buttonSpans) {
    for (const [, cells] of tableRows(text.slice(start, end))) {
      if (cells.length < 2) continue;
      const target = search(/^`?([A-Za-z]\w*)/, cells[1]);
      if (!target) continue;
      const lhs = target[1];
      if (declaredVars.has(lhs)) continue;
      if (!new RegExp(String.raw`\b${esc(lhs)}\b`).test(outside)) {
        findings.push(
          `button ${repr(cells[0])} maps to ${repr(lhs)}, which is never declared, extracted, or read anywhere else — ` +
            "a typo or a dead decision route",
        );
      }
    }
  }

  // FE-parity structural rules (PO.Frontend validation, design-expressible subset)
  const entryRowsAll = []; // [stage, WHEN cell, cells]
  for (const [, stageName, block] of stageBlocks(text)) {
    const entry = search(/^#### Stage Entry Conditions\s*$(.*?)(?=^#{1,5} |(?![\s\S]))/ms, block);
    if (entry) {
      for (const [, cells] of tableRows(entry[1])) {
        entryRowsAll.push([stageName, cells[0], cells]);
        // self-reference: an entry selecting its own stage never fires
        for (const call of finditer(
          /selected-stage-(?:completed|exited)\s*\(\s*["“‘']([^"”’']+)/,
          cells[0],
        )) {
          if (stripIdSuffix(call[1]).trim() === stageName) {
            findings.push(`stage ${repr(stageName)}: entry condition references its own stage — it can never fire`);
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

  // >=1 trigger row (FE: NO_TRIGGER_NODE)
  if (tableRows(sectionSlice(text, "Case Triggers")).length === 0) {
    findings.push("Case Triggers has no rows — a case needs at least one trigger (T02)");
  }

  // SLA bounds + case-vs-stage duration (FE: SLA_BELOW_MIN/ABOVE_MAX_MINUTES, ROOT_SLA_LESS_THAN_NODES)
  const UNIT_MIN = { min: 1, h: 60, d: 1440, w: 10080, m: 43200 };

  const slaMinutes = (count, unit) => {
    const key = stripTicks(unit.trim());
    const value = Number.parseFloat(count);
    if (!Number.isFinite(value) || !(key in UNIT_MIN)) return null;
    return Math.trunc(value) * UNIT_MIN[key];
  };

  let caseMinutes = null;
  const meta = sectionSlice(text, "Case Metadata");
  const caseSla = search(/^\|\s*Case-Level SLA\s*\|\s*(\d+(?:\.\d+)?)\s*(min|h|d|w|m)\b/m, meta);
  if (caseSla) {
    caseMinutes = slaMinutes(caseSla[1], caseSla[2]);
    if (caseSla[2] === "min" && caseMinutes !== null && !(caseMinutes >= 15 && caseMinutes <= 1000)) {
      findings.push(`Case-Level SLA ${caseMinutes} min is out of bounds — minute counts are bounded 15–1000`);
    }
  }
  for (const [, stageName, block] of stageBlocks(text)) {
    const slaSec = search(/^#### Stage SLA\s*$(.*?)(?=^#{1,5} |(?![\s\S]))/ms, block);
    if (!slaSec) continue;
    for (const [, cells] of tableRows(slaSec[1])) {
      if (cells.length < 2) continue;
      const minutes = slaMinutes(cells[0], cells[1]);
      if (minutes === null) continue;
      if (stripTicks(cells[1]) === "min" && !(minutes >= 15 && minutes <= 1000)) {
        findings.push(`stage ${repr(stageName)}: SLA ${cells[0]} min out of bounds — minute counts are bounded 15–1000`);
      }
      if (caseMinutes !== null && minutes > caseMinutes) {
        findings.push(
          `stage ${repr(stageName)}: stage SLA (${cells[0]} ${stripTicks(cells[1])}) exceeds the case-level SLA — ` +
            "the case would breach before the stage",
        );
      }
      break;
    }
  }

  // vacuous required-* (FE + validate: 'no required stage(s)/task(s) selected')
  const requiredStage = search(/^\*\*Required for Case Completion:\*\*\s*Yes\b/m, text);
  if (text.includes("required-stages-completed") && stageBlocks(text).length && !requiredStage) {
    findings.push(
      "required-stages-completed is used but no stage declares '**Required for Case Completion:** Yes' — " +
        "validate fails with 'no required stage(s) selected'",
    );
  }
  for (const [, stageName, block] of stageBlocks(text)) {
    const exitSec = search(/^#### Stage Exit Conditions\s*$(.*?)(?=^#{1,5} |(?![\s\S]))/ms, block);
    if (!exitSec || !exitSec[1].includes("required-tasks-completed")) continue;
    let hasRequiredTask = false;
    for (const env of finditer(
      /\*\*Task envelope\*\*(.*?)(?=^#{1,6} |\*\*Entry Condition:\*\*|(?![\s\S]))/ms,
      block,
    )) {
      for (const [, cells] of tableRows(env[1])) {
        if (cells.length && stripTicks(cells[0]) === "Yes") hasRequiredTask = true;
      }
    }
    if (!hasRequiredTask && search(TASK_HEADING, block)) {
      findings.push(
        `stage ${repr(stageName)}: required-tasks-completed completion but no task envelope declares Required: Yes — ` +
          "validate fails with 'no task(s) marked as required'",
      );
    }
  }

  // empty stage condition tables (FE: ENTRY/EXIT_CONDITION_MISSING) — an entry-less stage is unreachable
  for (const [, stageName, block] of stageBlocks(text)) {
    const entrySec = search(/^#### Stage Entry Conditions\s*$(.*?)(?=^#{1,5} |(?![\s\S]))/ms, block);
    if (entrySec && tableRows(entrySec[1]).length === 0) {
      findings.push(`stage ${repr(stageName)}: Stage Entry Conditions has no rows — the stage can never activate`);
    }
    const exitSec = search(/^#### Stage Exit Conditions\s*$(.*?)(?=^#{1,5} |(?![\s\S]))/ms, block);
    if (exitSec && tableRows(exitSec[1]).length === 0) {
      findings.push(`stage ${repr(stageName)}: Stage Exit Conditions has no rows — the stage can never complete or exit`);
    }
  }

  // entry-vs-case-exit overlap: case exit/completion evaluates BEFORE stage entry, so a stage
  // entry identical to a case-exit row leaves the stage permanently unreachable
  const normIf = (cell) => {
    const value = stripTicks(cell.trim());
    return ["—", "-", ""].includes(value) ? "" : value.replace(/\s+/g, "");
  };

  const caseExitRows = new Set();
  for (const [, cells] of tableRows(sectionSlice(text, "Case Exit Conditions"))) {
    const sel = search(SELECTED_STAGE_CALL, cells[0]);
    if (sel && cells.length >= 2) {
      caseExitRows.add(JSON.stringify([sel[1], stripIdSuffix(sel[2]).trim(), normIf(cells[1])]));
    }
  }
  if (caseExitRows.size) {
    for (const [stageName, when, cells] of entryRowsAll) {
      const sel = search(SELECTED_STAGE_CALL, when);
      if (!sel || cells.length < 2) continue;
      const key = JSON.stringify([sel[1], stripIdSuffix(sel[2]).trim(), normIf(cells[1])]);
      if (caseExitRows.has(key)) {
        findings.push(
          `stage ${repr(stageName)}: entry condition matches a case-exit row (same rule, selector, IF) — ` +
            "case exit takes precedence, leaving the stage permanently unreachable; differentiate the IF guards",
        );
      }
    }
  }

  // exit-overrides-completion: within one stage, a guarded completion (Yes + IF) sharing its WHEN
  // with an unguarded exit (No, IF empty) never fires — exit evaluates first
  for (const [, stageName, block] of stageBlocks(text)) {
    const exitSec = search(/^#### Stage Exit Conditions\s*$(.*?)(?=^#{1,5} |(?![\s\S]))/ms, block);
    if (!exitSec) continue;
    const rows = [];
    for (const [, cells] of tableRows(exitSec[1])) {
      const bare = cells.map((c) => stripTicks(c.trim()));
      const marks = bare.find((c) => c === "Yes" || c === "No") ?? null;
      if (marks && cells.length >= 2) rows.push([ruleName(cells[0]) ?? "", normIf(cells[1]), marks]);
    }
    for (const [whenY, ifY, marksY] of rows) {
      if (marksY !== "Yes" || !ifY) continue;
      for (const [whenN, ifN, marksN] of rows) {
        if (marksN === "No" && whenN === whenY && !ifN) {
          findings.push(
            `stage ${repr(stageName)}: unguarded exit row shares WHEN ${repr(whenY)} with a guarded completion — ` +
              "the exit always fires first and the stage never completes; give the exit the inverse IF",
          );
        }
      }
    }
  }

  // duplicate case-exit rows (FE: condition too similar)
  const seenExitRows = new Set();
  for (const [, cells] of tableRows(sectionSlice(text, "Case Exit Conditions"))) {
    const key = JSON.stringify(cells.slice(0, 4).map((c, i) => (i === 1 ? normIf(c) : stripTicks(c))));
    if (seenExitRows.has(key)) {
      findings.push(`duplicate case-exit row ${repr(cells[0])} — identical rules are ambiguous; differentiate or drop one`);
    }
    seenExitRows.add(key);
  }

  // Selector existence: stage selectors name declared stages, task selectors declared tasks
  const stageNames = new Set(stageBlocks(text).map(([, name]) => name.trim()));
  const taskNames = new Set([...finditer(TASK_HEADING, text)].map((m) => stripIdSuffix(m[3]).trim()));
  if (stageNames.size) {
    for (let index = 0; index < lines.length; index += 1) {
      const lineNo = index + 1;
      const line = lines[index];
      for (const call of finditer(/selected-stage-(?:completed|exited)\s*\(([^)]*)\)/, line)) {
        for (const arg of finditer(QUOTED_ARG, call[1])) {
          if (!stageNames.has(stripIdSuffix(arg[1]).trim())) {
            findings.push(
              `line ${lineNo}: stage selector references ${repr(arg[1])} — no stage with that display name exists`,
            );
          }
        }
      }
      for (const call of finditer(/selected-tasks-completed\s*\(([^)]*)\)/, line)) {
        for (const arg of finditer(QUOTED_ARG, call[1])) {
          if (taskNames.size && !taskNames.has(stripIdSuffix(arg[1]).trim())) {
            findings.push(
              `line ${lineNo}: task selector references ${repr(arg[1])} — no task with that display name exists`,
            );
          }
        }
      }
    }
  }

  // selected-tasks-completed scope: only non-adhoc tasks in the SAME stage (layers § Sequencing)
  for (const [, stageName, block] of stageBlocks(text)) {
    const tasksInBlock = [...finditer(TASK_HEADING, block)];
    const ownTasks = new Set(tasksInBlock.map((m) => stripIdSuffix(m[3]).trim()));
    const adhocTasks = new Set();
    for (let index = 0; index < tasksInBlock.length; index += 1) {
      const task = tasksInBlock[index];
      const end = index + 1 < tasksInBlock.length ? tasksInBlock[index + 1].index : block.length;
      const tb = block.slice(task.index, end);
      if (search(/^\*\*Activation Mode:\*\*\s*`?adhoc\b/m, tb)) {
        adhocTasks.add(stripIdSuffix(task[3]).trim());
      }
    }
    for (const call of finditer(/selected-tasks-completed\s*\(([^)]*)\)/, block)) {
      for (const arg of finditer(QUOTED_ARG, call[1])) {
        const name = stripIdSuffix(arg[1]).trim();
        if (adhocTasks.has(name)) {
          findings.push(
            `stage ${repr(stageName)}: selected-tasks-completed selects adhoc task ${repr(name)} — it selects only non-adhoc tasks`,
          );
        } else if (taskNames.size && taskNames.has(name) && !ownTasks.has(name)) {
          findings.push(
            `stage ${repr(stageName)}: selected-tasks-completed selects ${repr(name)} from another stage — it selects only tasks in the SAME stage`,
          );
        }
      }
    }
  }

  // sla-status-change SLA-title closure (target validity is checked in audit())
  if (slaTitles.size) {
    for (let index = 0; index < lines.length; index += 1) {
      const lineNo = index + 1;
      for (const call of finditer(/sla-status-change\s*\(([^)]*)\)/i, lines[index])) {
        const args = [...finditer(QUOTED_ARG, call[1])].map((m) => m[1]);
        if (args.length < 2) continue;
        const target = args[0].trim().toLowerCase();
        const declared = slaTitles.get(target);
        if (
          declared !== undefined &&
          ![...declared].map((t) => t.toLowerCase()).includes(args[1].trim().toLowerCase())
        ) {
          findings.push(
            `line ${lineNo}: sla-status-change references SLA title ${repr(args[1])} but target ${repr(args[0])} declares: ` +
              [...declared].sort().join(", "),
          );
        }
      }
    }
  }
  return findings;
}

// Findings carrying this prefix are printed but do not gate AUDIT OK. Reserved for rules whose
// violation is a display preference rather than a platform failure: gating on those costs full repair
// rounds and — worse for a display NAME — makes the agent rewrite the user's own domain vocabulary,
// which the lane's authoring policy forbids outright. Only rules with a known runtime consequence
// block (a ':' in a name breaks colon-delimited case-execution event routing; that one still gates).
const ADVISORY = "[advisory] ";

function isFile(path) {
  try {
    return statSync(path).isFile();
  } catch {
    return false;
  }
}

function audit(sddPath, draftPath) {
  const findings = [];
  const text = readFileSync(sddPath, "utf-8");

  const first = splitLines(text).map((line) => line.trim()).find((line) => line !== "") ?? "";
  if (!first.startsWith("# SDD — ")) {
    findings.push("first heading must be '# SDD — {Case Name}'");
  }

  for (const heading of REQUIRED_HEADINGS) {
    if (!search(new RegExp(String.raw`^${esc(heading)}\s*$`, "m"), text)) {
      findings.push(`missing required heading ${repr(heading)}`);
    }
  }
  for (const heading of SUMMARY_ONLY_HEADINGS) {
    if (search(new RegExp(String.raw`^## ${esc(heading)}\s*$`, "m"), text)) {
      findings.push(`summary-only heading '## ${heading}' — render the full template instead`);
    }
  }

  if (!text.includes(CASE_VARIABLES_HEADER)) {
    findings.push(`Case Variables table must use the literal header ${repr(CASE_VARIABLES_HEADER)}`);
  }
  if (search(LETTERED_TASK, text)) {
    findings.push("lettered task prefixes (Task R.1 / W.1 / CC.1 / ESC.1) — renumber as Task S{K}.{M}");
  }
  splitLines(text).forEach((line, index) => {
    if (/\\n\s*(?:\*\*|#|\|)/.test(line)) {
      findings.push(
        `line ${index + 1}: literal \\n escape corrupts the document structure — rewrite the block with real newlines`,
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
        findings.push(`stage ${repr(stageName)} missing ${repr(marker)}`);
      }
    }
    const stageType = search(/^\*\*Type:\*\*\s*([^\n]+)/m, block);
    if (stageType && !["Stage", "ExceptionStage"].includes(stageType[1].trim())) {
      findings.push(
        `stage ${repr(stageName)} has '**Type:** ${stageType[1].trim()}' — the stage Type literal is 'Stage'; ` +
          "secondary-ness lives in the heading, '**Stage Kind:** secondary', and '**Interrupting:**'",
      );
    }
    if (kind === "Secondary Stage" && !search(/^\*\*Interrupting:\*\*\s*(Yes|No)\b/m, block)) {
      findings.push(`secondary stage ${repr(stageName)} missing explicit '**Interrupting:** Yes' or 'No'`);
    }
    if (
      kind === "Secondary Stage" &&
      block.includes("return-to-origin") &&
      !search(/^\*\*Interrupting:\*\*\s*Yes\b/m, block)
    ) {
      findings.push(
        `secondary stage ${repr(stageName)} exits return-to-origin but does not declare '**Interrupting:** Yes'`,
      );
    }

    const tasks = [...finditer(TASK_HEADING, block)];
    if (tasks.length === 0) {
      findings.push(
        `stage ${repr(stageName)} has no '##### Task' detail blocks — every task in its Tasks table needs one`,
      );
      continue;
    }
    for (let index = 0; index < tasks.length; index += 1) {
      const task = tasks[index];
      const end = index + 1 < tasks.length ? tasks[index + 1].index : block.length;
      const taskBlock = block.slice(task.index, end);
      const taskName = stripIdSuffix(task[3]);
      for (const marker of TASK_MARKERS) {
        if (!taskBlock.includes(marker)) {
          findings.push(`task ${repr(taskName)} missing ${repr(marker)}`);
        }
      }
      const typeMatch = search(/^\*\*Type:\*\*\s*`?([a-z-]+)/m, taskBlock);
      if (typeMatch) {
        const markers = TASK_DETAIL_MARKERS.get(typeMatch[1]);
        if (markers && !markers.some((marker) => taskBlock.includes(marker))) {
          findings.push(
            `task ${repr(taskName)} (type ${typeMatch[1]}) missing type detail block ${repr(markers[0])}`,
          );
        }
      }
    }
  }

  // sla-status-change arg shape: 2 quoted args (breach) or 3 (at-risk), and the
  // target must resolve: the literal 'root' or a declared stage display name.
  const validTargets = new Set(["root", ...stages.map(([, name]) => name.toLowerCase())]);
  splitLines(text).forEach((line, index) => {
    const lineNo = index + 1;
    for (const call of finditer(/sla-status-change\s*\(([^)]*)\)/i, line)) {
      const args = [...finditer(QUOTED_ARG, call[1])].map((m) => m[1]);
      if (args.length && ![2, 3].includes(args.length)) {
        findings.push(
          `line ${lineNo}: sla-status-change takes ("<SLA target>","<SLA Title>") ` +
            `or (...,"<At-Risk Escalation Display Name>"); got ${args.length} args`,
        );
      }
      if (args.length && validTargets.size && !validTargets.has(args[0].trim().toLowerCase())) {
        findings.push(
          `line ${lineNo}: sla-status-change target ${repr(args[0])} is neither the literal 'root' (case-level) ` +
            "nor a stage declared in this SDD — never the case name or a synonym",
        );
      }
    }
  });

  let carried = new Set();
  if (draftPath !== null && isFile(draftPath)) {
    const draftText = readFileSync(draftPath, "utf-8");
    // Draft headings are pre-normalization — letter prefixes (Task R.2:) included.
    carried = new Set([
      ...stageBlocks(draftText).map(([, name]) => name.trim()),
      ...[...finditer(/^#{5} Task [A-Za-z0-9.]+: ([^\n]+)$/m, draftText)].map((m) =>
        stripIdSuffix(m[1]).trim(),
      ),
    ]);
  }
  const [facts, degraded] = loadModelFacts();
  if (degraded) findings.push(`model checks disarmed: ${degraded}`);
  findings.push(...lineageFindings(text));
  findings.push(...modelFindings(text, facts, carried));
  findings.push(
    ...contractFindings(
      text,
      hasFacts(facts) ? facts : { gate_rules: new Map(), yes_when: new Set(), no_when: new Set() },
    ),
  );

  const draftFindings = [];
  if (draftPath !== null) {
    if (!isFile(draftPath)) {
      draftFindings.push(
        `${draftPath} is gone — never delete or rename the draft; finalize renders a new sdd.md beside it`,
      );
    } else {
      const draft = readFileSync(draftPath, "utf-8");
      const draftInv = inventory(draft);
      const finalInv = inventory(text);
      const same =
        draftInv.length === finalInv.length &&
        draftInv.every(([s, t], i) => finalInv[i][0] === s && finalInv[i][1] === t);
      if (!same) {
        const inList = (list, s, t) => list.some(([ls, lt]) => ls === s && lt === t);
        const missing = draftInv.filter(([s, t]) => !inList(finalInv, s, t)).map(([s, t]) => `${s} / ${t}`);
        const added = finalInv.filter(([s, t]) => !inList(draftInv, s, t)).map(([s, t]) => `${s} / ${t}`);
        const detail = [
          missing.length ? `missing: ${missing.slice(0, 8).join(", ")}` : "",
          added.length ? `added/renamed: ${added.slice(0, 8).join(", ")}` : "",
          !missing.length && !added.length ? "order changed" : "",
        ]
          .filter(Boolean)
          .join("; ");
        draftFindings.push(
          `stage/task inventory differs from draft (draft=${draftInv.length}, final=${finalInv.length}) — ${detail}`,
        );
      }
      const finalExpressions = jsExpressions(text);
      const lost = [...jsExpressions(draft)].filter((e) => !finalExpressions.has(e)).sort();
      for (const expression of lost.slice(0, 10)) {
        draftFindings.push(`draft policy expression lost: ${expression}`);
      }
      draftFindings.push(...unencodedThresholds(draft, text));
    }
  }

  return [...draftFindings, ...findings];
}

/** Suggestions, not gates — never repair-looped, never a reason to withhold the ready flip. */
function emitAdvisories(advisories) {
  if (!advisories.length) return;
  process.stderr.write("\nADVISORY (does not gate AUDIT OK — fix only if you agree):\n");
  advisories.slice(0, 10).forEach((a, i) => process.stderr.write(`  ${i + 1}. ${a}\n`));
  if (advisories.length > 10) {
    process.stderr.write(`  … and ${advisories.length - 10} more\n`);
  }
}

function main() {
  const args = process.argv.slice(2);
  let draft = null;
  const flag = args.indexOf("--draft");
  if (flag !== -1) {
    draft = args[flag + 1];
    args.splice(flag, 2);
  }
  if (args.length !== 1 || draft === undefined) {
    process.stderr.write(USAGE + "\n");
    process.exit(1);
  }

  let allFindings;
  try {
    allFindings = audit(args[0], draft);
  } catch (error) {
    process.stderr.write(`audit-sdd: ${error.message}\n`);
    process.exit(1);
  }

  const findings = allFindings.filter((f) => !f.startsWith(ADVISORY));
  const advisories = allFindings.filter((f) => f.startsWith(ADVISORY)).map((f) => f.slice(ADVISORY.length));
  if (findings.length) {
    const shown = findings.slice(0, 40);
    process.stderr.write("AUDIT FAIL — repair these, then re-run:\n");
    shown.forEach((f, i) => process.stderr.write(`  ${i + 1}. ${f}\n`));
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
