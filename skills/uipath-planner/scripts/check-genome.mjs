#!/usr/bin/env node
// Checks a genome, and its Source Map's step tables against the source export. Node >= 20, built-ins only.
//
// Usage:
//   check-genome.mjs component <genome.md> [--profile core|strict] [--expect TOKEN ...] [--source-map TOKEN ...]
//   check-genome.mjs process   <genome.md> [--profile core|strict] [--skills SKILL ...] [--expect TOKEN ...]
//   check-genome.mjs tokens    <pattern>   --expect TOKEN ... [--min FRACTION] [--files N]
//   check-genome.mjs context   <genome.md>   JSON of the facts the read plans branch on: level (from the preamble
//                                           marker, found as the component and process checks find it), sha256,
//                                           components ({path, library} per Components row of a process genome),
//                                           test_components (a test-case group in the Components table, or a
//                                           `Test case:` step), independent_packages (the process Deployment's
//                                           Packaging line: true for independent packages, false for a solution,
//                                           null when it states neither or the genome is a component), extracted
//                                           (a Source Map with a table, not a stub), source_framework (the Source
//                                           Map's `Source framework` row; a component with a `Part of:` line takes
//                                           it from its process genome's Source Map) and build_mode
//                                           (build|refactor|migration|unknown: refactor when the framework names
//                                           UiPath, migration for another framework, unknown when the genome is
//                                           extracted and no framework is found, build otherwise), transactional
//                                           (null without a level or a Transactional Shape section), designed_in
//                                           (the `Designed in:` link resolved against the genome's folder, null
//                                           without one) with designed_in_link (the link as written), and the
//                                           strict check result
//   check-genome.mjs skills                 JSON of the skill names a genome may cite: build and operate
//   check-genome.mjs -h | --help
//   component and process also take: [--shape transactional|stub [--flows N] [--unit TOKEN ...]]
//                                    [--shape-checks gate|advisory]  advisory: Transactional Shape findings
//                                    are graded by the strict profile only (a task that tests something else)
//                                    [--processes <inventory.json> --recordsets <recordsets.json>]
//
// The skill runs it with --profile strict after writing or editing a genome. For a genome extracted through the
// framework migration pack it adds the two files the pack's `data` command writes, and the build runs it so at
// migration preflight against the export it resolved. The genome tasks grade with this file.
//
// Profiles:
//   core    the genome contract a smoke test gates on: level and preamble, every section, valid skill names,
//           steps and criteria present, a Transactional Shape that is the stub or has flows that each name their
//           unit of work, Source Map tokens, expected facts; in an extracted genome (one with a Source Map), a
//           `### Steps` table with exactly one row per Workflow step.
//   strict  core plus every mechanical format rule of genome-format-guide.md, transactional-shape-guide.md and
//           extracted-genome-guide.md: behavioural wording (no code-level tokens), configuration question kind
//           and default, bold step names, numbered acceptance criteria, the As-is table, exactly the outcome
//           rows rule 4 allows, split options named by letter with only their Requires and Changes cells,
//           complete for every unit and alternative unit, retry and consecutive-failure stop; step table cells
//           holding references only; no H2 heading twice; no component genome linked twice; the `Source framework`
//           row in the Source Map of a process or standalone component genome.
//
// Export check (--processes and --recordsets, both required together):
//   --processes   a list of {"id", "name", "recordset" (name or null), "calls": [{"calleeId", "recordset"}]}
//   --recordsets  a list of {"id", "name"}; an entry with "drives": false is provenance, never a data set
//   In every step table: each source object is `Name` (id) with the id a process of that name, each data set
//   `Name` (id) with the id a data set of that name, and every row names at least one source object. A library
//   step's process that no built root reaches while a same-named copy is reachable is the wrong copy; a library
//   workflow nothing in the genome calls is a NOTE. The check reads no prose and derives nothing.
//
// <genome.md> and <pattern> may be a quoted glob ("*-genome.md"): the file name is the agent's choice, only the
// -genome.md suffix is a contract. component and process need exactly one match; tokens searches every match,
// case-sensitively, like a file_contains criterion.
//
// Options take `--flag value` or `--flag=value`. Input files are read as strict UTF-8; a missing, unreadable or
// invalid input file is a FAIL line.
//
// Exit 0 when every check passes; exit 1 with one line per failure; exit 2 on a usage error.

import { createHash } from "node:crypto";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, resolve as resolvePath } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

export const VALID_SKILLS = new Set([
  "uipath-rpa", "uipath-maestro-flow", "uipath-maestro-bpmn", "uipath-maestro-case",
  "uipath-agents", "uipath-functions", "uipath-api-workflow", "uipath-coded-apps",
  "uipath-connector-builder", "uipath-ixp", "uipath-process-mining", "uipath-mcp-servers",
  "uipath-solution", "uipath-human-in-the-loop", "uipath-rules",
]);
export const OPERATE_SKILLS = new Set([ // allowed in Platform Dependencies / Deployment, never in Build With or Components
  "uipath-platform", "uipath-tasks", "uipath-test", "uipath-admin", "uipath-insights",
  "uipath-troubleshoot", "uipath-governance", "uipath-review", "uipath-planner", "uipath-aops",
  "uipath-automationhub", "uipath-feedback",
  "uipath-activity-migrator", "uipath-knowledge-bundles", "uipath-vertical-solutions",
]);
const RETIRED_SKILLS = ["uipath-rpa-workflows", "uipath-coded-workflows", "uipath-coded-agents"];
// the skill a genome's preamble routes its build to; `uipath-genome` names it in a genome written before the split
const BUILDER = "uipath-genome-builder";
const LEGACY_BUILDER = "uipath-genome";
const routesToBuilder = (s) => /\buipath-genome(?:-builder)?(?![\w-])/.test(s);

const COMPONENT_SECTIONS = [
  "Overview", "Target Applications", "Build With", "Platform Dependencies", "Interface",
  "Configuration Questions", "Workflow", "Business Rules", "Error Handling",
  "Transactional Shape", "Acceptance Criteria", "Complexity", "Tags",
];
const PROCESS_SECTIONS = [
  "Overview", "Actors and Systems", "Components", "Process Map", "Handoffs",
  "Platform Dependencies", "Configuration Questions", "Business Rules",
  "Error Handling and Recovery", "Transactional Shape", "Acceptance Criteria", "Deployment",
  "Complexity", "Tags",
];
// Code-level tokens that must not appear in the genome body (Source Map excluded).
const BANNED_BODY_TOKENS = [
  "InvokeWorkflowFile", "RetryScope", "TryCatch", "ReadRange", "AppendRange", "WriteRange",
  "GetIMAPMailMessages", "SaveAttachments", "AddQueueItem", "ReadPDFText", "LogMessage",
  "AndAlso", "OrElse", "dt_", "in_", "out_", ".xaml", "core.action", "core.logic",
  "uipath.core.", "activityType", "JsInvoke",
];
const OUTCOME_ROWS = new Set(["Success", "Business exception", "System exception", "Postponed"]);
// format guide § Population Matrix: minimum Workflow steps and Acceptance Criteria per complexity.
// core gates only on the floor every genome meets (the simple minimum); the per-complexity minimum is strict.
const CORE_FLOOR = 3;
const MIN_STEPS_BY_COMPLEXITY = { simple: 3, medium: 5, complex: 8 };
const MIN_CRITERIA_BY_COMPLEXITY = { simple: 3, medium: 5, complex: 7 };
const SPLIT_OPTIONS = ["A", "B", "C"];
const SPLIT_COLUMNS = ["unit of work", "option", "requires", "changes against as-is"];
const STUB = "Not transactional";
// transactional shape guide rule 9: a flow with one side outside the genome names it instead of the table
const EXTERNAL_SIDE = /Split options:(?:\*\*)? none\s*[—–-]+\s*the (consumer|producer) is outside this genome/i;
// extracted genome guide § Source Map: the step table
const STEPS_COLUMNS = ["step", "source objects", "data sets", "captures", "notes"];
const REFERENCE = /^`([^`]+)`(?:\s*\(((?:[^()`]|`[^`]*`)*)\))?$/; // `Name`, `Name` (id), `Name` (id, locator)
const TEMPLATES = join(dirname(fileURLToPath(import.meta.url)), "..", "assets", "templates");
const PLACEHOLDER = /\{[a-z][^}]*\}/g;
const ONE_WORD = /^\{[a-z]+\}$/;

const DEFAULTS = {
  profile: "core", expect: [], sourceMap: [], skills: [], shape: null, shapeChecks: "gate", flows: null,
  unit: [], minSteps: 5, minCriteria: 5, min: 1.0, files: null, processes: null, recordsets: null,
};

/** Collects findings; a strict finding is dropped under the core profile. */
class Report {
  constructor(profile, shapeGates = true) {
    this.profile = profile;
    this.shapeGates = shapeGates; // --shape-checks advisory: Transactional Shape findings count as strict
    this.errors = [];
  }
  shape(message) { (this.shapeGates ? this.core : this.strict).call(this, message); }
  core(message) { this.errors.push(message); }
  strict(message) { if (this.profile === "strict") this.errors.push(message); }
}

// --- markdown helpers --------------------------------------------------------------------------

const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const lines = (s) => s.split("\n");
const repr = (list) => `[${list.map((x) => `'${x}'`).join(", ")}]`; // a list as the findings have always printed it
/** A file the checker cannot read: missing, unreadable or not UTF-8. Printed as a FAIL line, never a stack trace. */
class InputError extends Error {}
const UTF8 = new TextDecoder("utf-8", { fatal: true });
/** [bytes, text] of a file, decoded as strict UTF-8. */
function decode(path) {
  let raw;
  try { raw = readFileSync(path); } catch (e) { throw new InputError(`${posix(String(path))}: cannot be read (${e.code ?? e.message})`); }
  try { return [raw, UTF8.decode(raw)]; } catch { throw new InputError(`${posix(String(path))}: not valid UTF-8`); }
}
const read = (path) => decode(path)[1].replace(/\r\n?/g, "\n");
const posix = (p) => p.replace(/\\/g, "/");

function h2Positions(text) {
  const pos = new Map();
  for (const m of text.matchAll(/^## (.+)$/gm)) pos.set(m[1].trim(), m.index);
  return pos;
}

/** Position of the first heading that starts with name, any case ('Error Handling and Recovery'
 * counts as 'Error Handling'). The exact heading is a format rule, graded by strict. */
function sectionPos(pos, name) {
  for (const [h, p] of pos) if (h.toLowerCase().startsWith(name.toLowerCase())) return p;
  return null;
}

export function sectionBody(text, heading) {
  const m = text.match(new RegExp(`^## ${esc(heading)}\\b[^\\n]*$([\\s\\S]*?)(?=^## |(?![\\s\\S]))`, "mi"));
  return m ? m[1] : "";
}

function complexityOf(text) {
  const m = sectionBody(text, "Complexity").match(/\b(simple|medium|complex)\b/i);
  return m ? m[1].toLowerCase() : null;
}

/** {extracted, framework}: a Source Map holding a table is an extracted genome's; its `Source framework` row, in
 * any of its tables (`| Row |` in a component, `| Component |` in a process), names the framework. */
export function sourceMapFacts(text) {
  const rows = lines(sectionBody(text, "Source Map")).filter((l) => l.trim().startsWith("|")).map(cells);
  const row = rows.find((c) => c.length > 1 && c[0].replace(/\*/g, "").trim().toLowerCase() === "source framework");
  return { extracted: rows.length > 0, hasFrameworkRow: Boolean(row), framework: row ? row[1].split("—")[0].trim() || null : null };
}

/** strict: a process or standalone component genome's Source Map names its framework; a part inherits it. */
function checkSourceFramework(text, r) {
  const { extracted, hasFrameworkRow } = sourceMapFacts(text);
  if (extracted && !hasFrameworkRow) r.strict("Source Map has no 'Source framework' row");
}

const bodyWithoutSourceMap = (text) => text.split(/^## Source Map\s*$/m)[0];

const cells = (row) => row.trim().replace(/^\|+|\|+$/g, "").split("|").map((c) => c.trim());

/** Data rows of the first markdown table in block whose header row starts with headerStart. */
export function tableRows(block, headerStart) {
  const ls = lines(block);
  for (let i = 0; i < ls.length; i++) {
    if (!ls[i].trim().startsWith(headerStart)) continue;
    const rows = [];
    for (const row of ls.slice(i + 2)) {
      if (!row.trim().startsWith("|")) break;
      rows.push(cells(row));
    }
    return rows;
  }
  return [];
}

/** [name, body] per '### Flow N' block of the Transactional Shape. */
function flowBlocks(ts) {
  const parts = ts.split(/^(### Flow\b.*)$/m);
  const out = [];
  for (let i = 1; i < parts.length - 1; i += 2) out.push([parts[i].replace(/^[# ]+/, "").split(":")[0].trim(), parts[i + 1]]);
  return out;
}

/** The numbers of the Workflow's top-level steps, in order. */
export const workflowSteps = (text) => [...sectionBody(text, "Workflow").matchAll(/^(\d+)\.\s/gm)].map((m) => m[1]);

/** [header cells, rows] of the Source Map's `### Steps` table; null when the Source Map has none. */
function stepsTable(text) {
  const m = sectionBody(text, "Source Map").match(/^### Steps\s*$([\s\S]*?)(?=^#{2,3} |(?![\s\S]))/m);
  if (!m) return null;
  const header = lines(m[1]).find((l) => l.trim().startsWith("|")) ?? "";
  return [cells(header).map((c) => c.toLowerCase()), header ? tableRows(m[1], header.trim()) : []];
}

/** The parts of a step table cell, split on '; ' outside backticks and parentheses. */
function splitReferences(cell) {
  const parts = [];
  let part = "", tick = false, depth = 0;
  for (const ch of cell) {
    if (ch === "`") tick = !tick;
    else if (!tick && (ch === "(" || ch === ")")) depth = ch === "(" ? depth + 1 : Math.max(0, depth - 1);
    if (ch === ";" && !tick && depth === 0) { parts.push(part); part = ""; } else part += ch;
  }
  return [...parts, part].map((p) => p.trim()).filter(Boolean);
}

/** [[name, id or null] per reference, the parts that are no reference] of a step table cell; `none` is empty. */
function references(cell) {
  if (cell.trim().toLowerCase() === "none") return [[], []];
  const refs = [], prose = [];
  for (const part of splitReferences(cell)) {
    const m = part.match(REFERENCE);
    if (!m) { prose.push(part); continue; }
    const ident = (m[2] ?? "").split(",")[0].trim();
    refs.push([m[1], ident || null]);
  }
  return [refs, prose];
}

const skillNames = (body) => [...new Set([...body.matchAll(/`(uipath-[a-z-]+)`/g)].map((m) => m[1]))].sort();

// --- checks shared by both levels ---------------------------------------------------------------

function checkCommon(text, level, sections, r, minCriteria) {
  if (!new RegExp(`UIPATH-AUTOMATION-GENOME:\\s*${level}`, "i").test(text)) r.core(`missing preamble comment 'UIPATH-AUTOMATION-GENOME: ${level}'`);
  else if (!text.includes(`UIPATH-AUTOMATION-GENOME: ${level}`)) r.strict(`preamble comment not written exactly 'UIPATH-AUTOMATION-GENOME: ${level}'`);
  if (!/UiPath automation blueprint/i.test(text)) r.core("missing blueprint blockquote");
  else if (!text.includes("This is a UiPath automation blueprint")) r.strict("blueprint blockquote not written as the template words it");
  // format guide rule 5: the preamble routes the agent to the skill that builds the genome, not to the Build With skills
  const comment = text.match(/<!--\s*UIPATH-AUTOMATION-GENOME[\s\S]*?-->/i);
  if (comment && !routesToBuilder(comment[0])) r.strict(`preamble comment does not name ${BUILDER} as the skill that builds the genome`);
  const blockquote = text.match(/^>.*UiPath automation blueprint.*$/im);
  if (blockquote && !routesToBuilder(blockquote[0])) r.strict(`blueprint blockquote does not name ${BUILDER} as the skill that builds the genome`);
  const pos = h2Positions(text);
  const headings = [...text.matchAll(/^## (.+)$/gm)].map((m) => m[1].trim());
  for (const h of new Set(headings.filter((h, i) => headings.indexOf(h) !== i))) r.strict(`heading '## ${h}' appears more than once`);
  for (const s of sections) {
    if (sectionPos(pos, s) === null) r.core(`missing section '## ${s}'`);
    else if (!pos.has(s)) r.strict(`section '## ${s}' present under a longer or differently cased heading`);
  }
  for (const name of [...RETIRED_SKILLS].sort()) if (text.includes(name)) r.core(`retired skill name '${name}' present`);
  // skill names are read where a genome names skills; elsewhere `uipath-…` is also an Integration
  // Service connector key (`uipath-slack`, `uipath-salesforce-sfdc`), not a skill
  for (const heading of ["Build With", "Components"]) {
    for (const name of skillNames(sectionBody(text, heading))) {
      if (!VALID_SKILLS.has(name) && !OPERATE_SKILLS.has(name) && name !== BUILDER && name !== LEGACY_BUILDER) r.core(`unknown skill name '${name}' in ${heading}`);
    }
  }
  for (const heading of ["Build With", "Components"]) {
    for (const name of skillNames(sectionBody(text, heading))) {
      // skill-mapping guide rule 2; advisory: a platform row in Build With does no harm — the
      // resources still reach the target through the solution and the open-items files
      if (OPERATE_SKILLS.has(name)) r.strict(`operate-only skill '${name}' in ${heading}; it belongs under Platform Dependencies`);
    }
  }
  // a criterion is a list item in any form: '- ', '- [ ] ', '* ' or '1. '; the format guide numbers them
  const criteria = lines(sectionBody(text, "Acceptance Criteria")).filter((l) => /^(?:[-*]|\d+\.) \S/.test(l));
  if (criteria.length < CORE_FLOOR) r.core(`acceptance criteria: ${criteria.length} found, expected >= ${CORE_FLOOR}`);
  else if (criteria.length < minCriteria) r.strict(`acceptance criteria: ${criteria.length} found, expected >= ${minCriteria} for the stated complexity`);
  if (criteria.some((l) => !/^\d+\. /.test(l))) r.strict("acceptance criteria are not numbered ('1. …'), so a report cannot cite them by number");
  for (const line of criteria) if (/completes successfully|handles errors properly/i.test(line)) r.core(`generic acceptance criterion: ${line.trim()}`);

  const body = bodyWithoutSourceMap(text);
  for (const tok of BANNED_BODY_TOKENS) {
    // a prefix token counts at the start of a word only: `in_Folder`, never "login_page" or "layout_name"
    if (tok.endsWith("_") ? new RegExp(`\\b${esc(tok)}\\w`).test(body) : body.includes(tok)) r.strict(`code-level token '${tok}' in the genome body (outside Source Map)`);
  }
  for (const [, num, question] of sectionBody(text, "Configuration Questions").matchAll(/^(\d+)\. (.*)$/gm)) {
    const pointer = !question.includes("?") && /Configuration Question \d+/.test(question); // a question the process genome asks
    if (!pointer && !/\((setting|constant); default:/.test(question)) r.strict(`configuration question ${num} does not name its kind and default as '(setting; default: …)' or '(constant; default: …)'`);
  }
}

/** [flows, headed]: the '### Flow N' blocks, or — when there is no such heading but the section names a
 * unit of work — the whole section as one flow. The heading is a format rule; the unit of work is the contract. */
function effectiveFlows(ts) {
  const blocks = flowBlocks(ts);
  if (blocks.length) return [blocks, true];
  if (/unit of work/i.test(ts)) return [[["Flow 1", ts]], false];
  return [[], false];
}

let templateCache = null;

/** The `{…}` placeholders of the templates' Transactional Shape sections, a one-word one with the word before it
 * (`with {result}`, `retried {n}`). A genome's own braces — a value built from parts, such as `{item}_{date}` or
 * `INV-{n}` — are content, not a placeholder left unfilled. */
function templatePlaceholders() {
  if (templateCache) return templateCache;
  const found = new Set();
  for (const name of ["component-genome-template.md", "process-genome-template.md"]) {
    const path = join(TEMPLATES, name);
    if (!existsSync(path)) continue;
    for (const m of sectionBody(read(path), "Transactional Shape").matchAll(/(\S+ )?(\{[a-z][^}]*\})/g)) {
      found.add(ONE_WORD.test(m[2]) ? (m[1] ?? "") + m[2] : m[2]);
    }
  }
  return (templateCache = found);
}

/** Transactional Shape: the stub, or flow blocks the transactional shape guide describes. */
function checkTransactional(text, level, r, partOf = false) {
  const ts = sectionBody(text, "Transactional Shape");
  if (!ts.trim() || ts.trim().startsWith(STUB)) return;
  if (ts.includes("**Recommendation:**") || /^\|\s*(Producer|Consumer)\s*\|/m.test(ts)) r.strict("Transactional Shape carries a verdict (Recommendation line or Producer/Consumer mode table)");
  const [flows, headed] = effectiveFlows(ts);
  if (!flows.length) { r.shape("Transactional Shape is neither the stub nor flows naming their unit of work"); return; }
  if (!headed) r.strict("Transactional Shape describes its flow without '### Flow N' headings");
  // a component reached through a process genome's links is inside it, with or without its 'Part of:' line
  const inProcess = level === "component" && (partOf || text.includes("Part of:"));
  if (!inProcess && !ts.includes("**Flows:**")) r.strict("Transactional Shape has no 'Flows:' line");
  const template = templatePlaceholders(); // without the templates beside the script, every lower-case `{…}` counts
  const unfilled = template.size ? [...template].filter((p) => ts.includes(p)) : ts.match(PLACEHOLDER) ?? [];
  if (unfilled.length) {
    const first = unfilled.reduce((a, b) => (ts.indexOf(b) < ts.indexOf(a) ? b : a));
    r.strict(`Transactional Shape leaves a template placeholder unfilled: ${first}`);
  }
  for (const [name, body] of flows) {
    if (inProcess) {
      if (!body.includes("**Role:**")) r.shape(`Transactional Shape ${name}: a component inside a process has no 'Role:' line`);
      if (!body.includes("per the process genome")) r.strict(`Transactional Shape ${name}: does not point to the process genome's split options`);
      continue;
    }
    if (!/unit of work/i.test(body)) r.shape(`Transactional Shape ${name}: names no unit of work`);
    else if (!body.includes("**Unit of work:**")) r.strict(`Transactional Shape ${name}: no '**Unit of work:**' line`);
    const external = body.match(EXTERNAL_SIDE);
    const split = tableRows(body, "| Unit of work | Option |");
    if (!external && !split.length) r.strict(`Transactional Shape ${name}: no Split options table and no 'outside this genome' line`);
    if (!body.includes("| Aspect | As-is |")) r.strict(`Transactional Shape ${name}: no As-is table`);
    const consumerOutside = Boolean(external && external[1].toLowerCase() === "consumer");
    if (!consumerOutside) {
      const rows = tableRows(body, "| Outcome |").filter((row) => row.length).map((row) => row[0]);
      for (const needed of ["Success", "Business exception", "System exception"]) if (!rows.includes(needed)) r.strict(`Transactional Shape ${name}: no '${needed}' outcome row`);
      for (const extra of rows.filter((x) => !OUTCOME_ROWS.has(x))) r.strict(`Transactional Shape ${name}: outcome row '${extra}' — a source's own results map to Success or a Business exception`);
      // the consumer owes the item retry and the consecutive-failure stop (transactional shape guide rule 4)
      if (!/retr(y|ie)/i.test(body) || !/consecutive|stops? after \d/i.test(body)) r.strict(`Transactional Shape ${name}: outcomes do not state the item retry and the consecutive-failure stop`);
    }
    if (external) continue;
    const units = new Map();
    for (const row of split) {
      const m = row.length >= 2 ? row[1].match(/^([ABC])\b/) : null;
      if (m) { if (!units.has(row[0])) units.set(row[0], new Set()); units.get(row[0]).add(m[1]); }
      if (row.length >= 2 && !SPLIT_OPTIONS.includes(row[1].trim())) r.strict(`Transactional Shape ${name}: option cell '${row[1]}' of '${row[0]}' holds more than its letter — the transactional shape guide defines A, B and C`);
    }
    for (const [unit, opts] of units) {
      const missing = SPLIT_OPTIONS.filter((o) => !opts.has(o));
      if (missing.length) r.strict(`Transactional Shape ${name}: unit '${unit}' lacks option(s) ${repr(missing)}`);
    }
    const alt = lines(body).find((l) => l.startsWith("**Alternative units of work:**")) ?? "";
    if (alt && !/:\*\*\s*none\b/i.test(alt) && units.size < 2) r.strict(`Transactional Shape ${name}: alternative units of work named but split options cover only one unit`);
    const header = lines(body).find((l) => l.trim().startsWith("| Unit of work | Option |")) ?? "";
    const cols = cells(header).map((c) => c.toLowerCase());
    if (!cols.includes("requires") || !cols.includes("changes against as-is")) {
      r.strict(`Transactional Shape ${name}: Split options table has no Requires and Changes against as-is columns`);
      continue;
    }
    if (cols.join("\u0000") !== SPLIT_COLUMNS.join("\u0000")) r.strict(`Transactional Shape ${name}: Split options columns are ${repr(cols)}, expected Unit of work, Option, Requires, Changes against as-is`);
    const ir = cols.indexOf("requires"), ic = cols.indexOf("changes against as-is");
    for (const row of split) {
      if (row.length > Math.max(ir, ic) && SPLIT_OPTIONS.includes(row[1].slice(0, 1))) {
        if (!row[ir] || !row[ic]) r.strict(`Transactional Shape ${name}: option ${row[1].slice(0, 1)} of '${row[0]}' has an empty Requires or Changes cell`);
        if (/\b(recommended|best option|preferred)\b/i.test(`${row[ir]} ${row[ic]}`)) r.strict(`Transactional Shape ${name}: option ${row[1].slice(0, 1)} of '${row[0]}' ranks the options`);
      }
    }
  }
}

/** --shape: what the Transactional Shape of this genome must describe. */
function checkShapeAssertion(text, shape, flows, units, r) {
  const ts = sectionBody(text, "Transactional Shape");
  const stub = ts.trim().startsWith(STUB);
  if (shape === "stub") { if (!stub) r.core("Transactional Shape: expected the 'Not transactional' stub"); return; }
  if (stub) { r.core("Transactional Shape: expected flow blocks, found the stub"); return; }
  const [blocks] = effectiveFlows(ts);
  if (!blocks.length) { r.core("Transactional Shape: expected flows naming their unit of work, found none"); return; }
  if (flows !== null && blocks.length !== flows) r.core(`Transactional Shape: ${blocks.length} flow(s), expected ${flows}`);
  // the primary unit's line only: never the alternatives line or a table header, and whole words ('row', not 'throw')
  const unitLines = lines(ts).filter((l) => /^[*_\s>-]*unit of work\b/i.test(l)).join(" ");
  for (const tok of units) if (!new RegExp(`\\b${esc(tok)}s?\\b`, "i").test(unitLines)) r.core(`Transactional Shape: no 'Unit of work' line names '${tok}'`);
}

/** An extracted genome's step table: one row per Workflow step (core), reference-only cells (strict). */
function checkStepsTable(text, r) {
  if (!sectionBody(text, "Source Map").trim()) return;
  const table = stepsTable(text);
  if (table === null) { r.core("Source Map has no '### Steps' table pairing each Workflow step with its source objects"); return; }
  const [header, rows] = table;
  if (header.join("\u0000") !== STEPS_COLUMNS.join("\u0000")) r.strict(`step table columns are ${repr(header)}, expected Step, Source objects, Data sets, Captures, Notes`);
  const steps = workflowSteps(text);
  const keys = rows.map((row) => row[0]);
  const count = (k) => keys.filter((x) => x === k).length;
  for (const step of steps) if (count(step) !== 1) r.core(`step table: Workflow step ${step} has ${count(step)} rows, expected exactly one`);
  const orphans = [...new Set(keys)].filter((k) => !steps.includes(k)).sort((a, b) => a.length - b.length || (a < b ? -1 : a > b ? 1 : 0));
  for (const key of orphans) r.core(`step table: row '${key}' names no Workflow step — key a row by the step's number only`);
  for (let row of rows) {
    row = [...row, ...Array(Math.max(0, STEPS_COLUMNS.length - row.length)).fill("")];
    const [sources, prose] = references(row[1]);
    if (!sources.length) r.strict(`step table, step ${row[0]}: no source object`);
    const [data, dataProse] = references(row[2]);
    for (const part of [...prose, ...dataProse]) r.strict(`step table, step ${row[0]}: '${part.slice(0, 60)}' is not a reference — move it to Notes`);
    if (!data.length && row[2].trim().toLowerCase() !== "none") r.strict(`step table, step ${row[0]}: Data sets is empty — write 'none' when the step reads no data set`);
    if (!/^\d+$/.test(row[3])) r.strict(`step table, step ${row[0]}: Captures '${row[3]}' is not a count`);
  }
}

// --- levels -------------------------------------------------------------------------------------

/** [link, component genome path, is a library] per row of a process genome's Components table. */
export function componentLinks(path, text) {
  const out = [];
  for (const row of tableRows(sectionBody(text, "Components"), "| #")) {
    const m = row.join(" | ").match(/\]\(([^)]+-genome\.md)\)/);
    if (m) out.push([m[1], resolvePath(dirname(path), m[1]), row.length > 2 && /\blibrary\b/i.test(row[2])]);
  }
  return out;
}

function checkComponent(path, a, partOf, shape = true, library = false) {
  const text = read(path);
  // a library is named so in its process genome's Components table, or in its own Transactional Shape stub
  library = library || /^Not transactional:[^\n]*\blibrar(y|ies)\b/i.test(sectionBody(text, "Transactional Shape").trim());
  const r = new Report(a.profile, a.shapeChecks === "gate");
  const level = complexityOf(text);
  const minSteps = MIN_STEPS_BY_COMPLEXITY[level] ?? a.minSteps;
  checkCommon(text, "component", COMPONENT_SECTIONS, r, MIN_CRITERIA_BY_COMPLEXITY[level] ?? a.minCriteria);
  const pos = h2Positions(text);
  const bw = sectionPos(pos, "Build With"), wf = sectionPos(pos, "Workflow");
  if (bw !== null && wf !== null && bw > wf) r.core("Build With must precede Workflow");
  if (!/uipath-[a-z-]+/.test(sectionBody(text, "Build With"))) r.core("Build With names no skill");
  const workflow = sectionBody(text, "Workflow");
  const steps = (workflow.match(/^(?:\d+\.|[-*]) \S/gm) ?? []).length; // top-level numbered or bulleted steps
  // a test component's steps are its cases and a library's its public workflows (format guide § Population Matrix)
  const exempt = library || /^\d+\. \*\*Test case:/m.test(workflow);
  if (steps < CORE_FLOOR && !exempt) r.core(`workflow: ${steps} numbered steps, expected >= ${CORE_FLOOR}`);
  else if (steps < minSteps && !exempt) r.strict(`workflow: ${steps} numbered steps, expected >= ${minSteps} for complexity ${level || "not stated"}`);
  if ((workflow.match(/^\d+\. \*\*/gm) ?? []).length < Math.min(steps, minSteps)) r.strict("workflow: steps not all in the '1. **Step name**' form");
  const cq = sectionBody(text, "Configuration Questions");
  const questions = cq.match(/^\d+\. /gm) ?? [];
  if (!cq.trim()) r.core("Configuration Questions section is empty");
  else if (!questions.length && !cq.includes("no configuration needed")) r.strict("Configuration Questions: neither a numbered list of questions nor the stub line");
  if (a.sourceMap.length) {
    const sm = sectionBody(text, "Source Map");
    if (!sm.trim()) r.core("missing or empty '## Source Map' section");
    for (const tok of a.sourceMap) if (!sm.includes(tok)) r.core(`Source Map does not mention '${tok}'`);
  }
  checkStepsTable(text, r);
  if (!partOf && !text.includes("Part of:")) checkSourceFramework(text, r);
  if (partOf && !text.includes("Part of:")) r.strict("component inside a process genome lacks the 'Part of:' line");
  checkTransactional(text, "component", r, partOf);
  if (a.shape && shape) checkShapeAssertion(text, a.shape, a.flows, a.unit, r);
  for (const tok of a.expect) if (!text.toLowerCase().includes(tok.toLowerCase())) r.core(`expected token '${tok}' not found`);
  return r.errors.map((e) => `${baseName(path)}: ${e}`);
}

function checkProcess(path, a) {
  const text = read(path);
  const r = new Report(a.profile, a.shapeChecks === "gate");
  checkCommon(text, "process", PROCESS_SECTIONS, r, MIN_CRITERIA_BY_COMPLEXITY[complexityOf(text)] ?? a.minCriteria);
  const pos = h2Positions(text);
  const cp = sectionPos(pos, "Components"), pm = sectionPos(pos, "Process Map");
  if (cp !== null && pm !== null && cp > pm) r.core("Components must precede Process Map");
  const comp = sectionBody(text, "Components");
  if (lines(comp).filter((l) => l.startsWith("|") && l.includes("uipath-")).length < 2) r.core("Components table: fewer than 2 rows naming a skill");
  for (const s of a.skills) if (!new RegExp(`\\b${esc(s)}\\b`).test(comp)) r.core(`Components table lacks skill '${s}'`);
  for (const row of tableRows(comp, "| #")) {
    if (row.length > 2 && /\b(dispatcher|performer)\b/i.test(row[2])) r.strict(`Components: role word in the Type cell of '${row[1]}' — it reads the component type only`);
  }
  const links = componentLinks(path, text);
  if (!links.length) r.core("Components table links no component genome");
  const targets = links.map(([, t]) => posix(t).toLowerCase());
  const first = (i) => targets.indexOf(targets[i]) === i;
  for (const [link] of links.filter((_, i) => !first(i))) r.strict(`Components table links ${link} more than once`);
  checkSourceFramework(text, r);
  const componentErrors = [];
  for (const [link, target, isLibrary] of links.filter((_, i) => first(i))) {
    if (!existsSync(target)) r.core(`linked component genome missing on disk: ${link}`);
    else {
      // one unreadable component file is one finding; the process genome and its other components are still checked
      try { componentErrors.push(...checkComponent(target, { ...a, expect: [], sourceMap: [] }, true, false, isLibrary)); }
      catch (e) { if (!(e instanceof InputError)) throw e; r.core(e.message); }
    }
  }
  const handoffs = lines(sectionBody(text, "Handoffs")).filter((l) => l.startsWith("|"));
  if (handoffs.length < 4) r.core(`Handoffs table: ${Math.max(0, handoffs.length - 2)} rows, expected >= 2`); // header + separator + >= 2 rows
  checkTransactional(text, "process", r);
  if (a.shape) checkShapeAssertion(text, a.shape, a.flows, a.unit, r);
  for (const tok of a.expect) if (!text.toLowerCase().includes(tok.toLowerCase())) r.core(`expected token '${tok}' not found`);
  return [...r.errors.map((e) => `${baseName(path)}: ${e}`), ...componentErrors];
}

/** [failures, notes] of every step table against the export's inventory. Ids are compared as text. */
export function checkExport(genomes, processes, recordsets) {
  const byId = new Map(processes.map((p) => [String(p.id), p]));
  const byName = new Map();
  for (const p of processes) {
    const key = p.name.toLowerCase();
    if (!byName.has(key)) byName.set(key, []);
    byName.get(key).push(p);
  }
  const data = new Map(recordsets.map((d) => [String(d.id), d]));
  const errors = [], notes = [], used = [];
  for (const [path, isLibrary] of genomes) {
    const table = existsSync(path) ? stepsTable(read(path)) : null;
    for (let row of table ? table[1] : []) {
      row = [...row, ...Array(Math.max(0, STEPS_COLUMNS.length - row.length)).fill("")];
      const where = `${baseName(path)} step ${row[0]}`;
      const [sources] = references(row[1]);
      if (!sources.length) errors.push(`${where}: no source object`);
      for (const [name, ident] of sources) {
        const p = byId.get(ident ?? "");
        if (ident === null) errors.push(`${where}: \`${name}\` has no id — cite it as \`Name\` (id)`);
        else if (p === undefined) errors.push(`${where}: \`${name}\` (${ident}) is no process of the export${data.has(ident) ? " — it is a data set: move it to Data sets" : ""}`);
        else if (p.name.toLowerCase() !== name.toLowerCase()) errors.push(`${where}: id ${ident} is \`${p.name}\`, the row says \`${name}\``);
        else used.push([where, isLibrary, p]);
      }
      for (const [name, ident] of references(row[2])[0]) {
        const d = data.get(ident ?? "");
        if (ident === null) errors.push(`${where}: data set \`${name}\` has no id — cite it as \`Name\` (id)`);
        else if (d === undefined) errors.push(`${where}: data set \`${name}\` (${ident}) is no data set of the export${byId.has(ident) ? " — it is a process: move it to Source objects" : ""}`);
        else if (d.drives === false) errors.push(`${where}: \`${name}\` (${ident}) drives nothing (a file the step writes, a URL) — name it in Notes`);
        else if (d.name.toLowerCase() !== name.toLowerCase() && !d.name.toLowerCase().endsWith(`::${name.toLowerCase()}`)) errors.push(`${where}: data set id ${ident} is \`${d.name}\`, the row says \`${name}\``);
      }
    }
  }
  // the built roots: every process a non-library step was built from, and what they call
  const roots = used.filter(([, lib]) => !lib).map(([, , p]) => String(p.id));
  const scope = new Set(roots.length ? roots : byId.keys());
  const frontier = [...scope];
  while (frontier.length) {
    for (const c of byId.get(frontier.pop())?.calls ?? []) {
      const callee = String(c.calleeId);
      if (!scope.has(callee)) { scope.add(callee); frontier.push(callee); }
    }
  }
  for (const [where, lib, p] of used) {
    if (lib && !scope.has(String(p.id))) {
      const twins = (byName.get(p.name.toLowerCase()) ?? []).map((q) => String(q.id)).filter((id) => scope.has(id));
      if (twins.length) errors.push(`${where}: \`${p.name}\` (${p.id}) is not reachable from the built roots; the copy they run is ${twins.join(", ")}`);
      else notes.push(`${where}: \`${p.name}\` (${p.id}) is a library workflow no built component calls`);
    }
  }
  return [errors, notes];
}

const baseName = (p) => posix(p).split("/").pop();

/** Files matching a path or a glob relative to the working directory (`*`, `?`, `**`), sorted. */
function resolveGlob(pattern) {
  if (existsSync(pattern) || !/[*?[]/.test(pattern)) return existsSync(pattern) ? [pattern] : [];
  const toRe = (seg) => new RegExp(`^${seg.split("").map((c) => (c === "*" ? "[^/]*" : c === "?" ? "[^/]" : esc(c))).join("")}$`);
  let matches = [""];
  for (const seg of posix(pattern).split("/").filter(Boolean)) {
    const next = [];
    for (const base of matches) {
      const dir = base || ".";
      if (seg === "**") {
        const walk = (d, rel) => {
          next.push(rel);
          for (const e of safeList(d)) if (e.isDirectory()) walk(join(d, e.name), rel ? `${rel}/${e.name}` : e.name);
        };
        walk(dir, base);
      } else if (/[*?]/.test(seg)) {
        const re = toRe(seg);
        for (const e of safeList(dir)) if (re.test(e.name)) next.push(base ? `${base}/${e.name}` : e.name);
      } else next.push(base ? `${base}/${seg}` : seg);
    }
    matches = [...new Set(next)];
  }
  return matches.filter((m) => m && existsSync(m) && statSync(m).isFile()).sort();
}

function safeList(dir) {
  try { return readdirSync(dir, { withFileTypes: true }); } catch { return []; }
}

function checkTokens(paths, tokens, minimum, files) {
  const errors = [];
  if (files !== null && paths.length !== files) errors.push(`${paths.length} file(s) match, expected ${files}: ${paths.map(posix).join(", ") || "none"}`);
  const text = paths.map(read).join("\n");
  const missing = tokens.filter((t) => !text.includes(t));
  if (tokens.length && (tokens.length - missing.length) / tokens.length < minimum) {
    errors.push(`${tokens.length - missing.length}/${tokens.length} tokens found, expected >= ${Math.round(minimum * 100)}%; missing: ${missing.join(", ")}`);
  }
  return errors;
}

function loadInventory(path, what) {
  if (!existsSync(path)) throw new InputError(`${posix(path)}: the ${what} file does not exist`);
  let data;
  try { data = JSON.parse(decode(path)[1]); } catch (e) {
    if (e instanceof InputError) throw e;
    throw new InputError(`${posix(path)}: the ${what} is not valid JSON (${e.message})`);
  }
  if (!Array.isArray(data) || !data.every((x) => x && typeof x === "object" && "id" in x && "name" in x)) {
    throw new InputError(`${posix(path)}: the ${what} is a list of objects with 'id' and 'name' (regenerate it with the source guide's script)`);
  }
  return data;
}

// the preamble marker, matched anywhere in the file as checkCommon matches it; the first match decides the level
const MARKER = /UIPATH-AUTOMATION-GENOME:\s*(component|process)\b/i;
const DESIGNED_IN = /^>\s*Designed in:\s*\[[^\]]*\]\(([^)]+)\)/m;
const PART_OF = /^>\s*Part of:[^\n]*?\]\(([^)]+-genome\.md)\)/m;
const TEST_GROUP = /\btest[- ]case group\b/i;

/** The Source Map framework of the process genome a `Part of:` line links; null when the link does not resolve. */
function parentFramework(path, text) {
  const m = text.match(PART_OF);
  if (!m) return null;
  const parent = resolvePath(dirname(path), m[1]);
  if (!existsSync(parent)) return null;
  try { return sourceMapFacts(read(parent)).framework; } catch (e) { if (e instanceof InputError) return null; throw e; }
}

/** true for independent packages, false for one solution, null when the Packaging line states neither. */
function independentPackages(text) {
  const m = sectionBody(text, "Deployment").match(/^\s*[-*]\s*\*\*Packaging:?\*\*:?([^\n]*)$/im);
  if (!m) return null;
  if (/\bindependent\b/i.test(m[1])) return true;
  return /\bsolution\b/i.test(m[1]) ? false : null;
}

/** The facts every read plan branches on, read from the file once instead of re-derived by each lane. */
export function context(path) {
  const [raw, decoded] = decode(path);
  const text = decoded.replace(/\r\n?/g, "\n");
  const marker = text.match(MARKER);
  const level = marker ? marker[1].toLowerCase() : null;
  const { extracted, framework: own } = sourceMapFacts(text);
  const framework = own ?? (level === "component" ? parentFramework(path, text) : null);
  const designedIn = text.match(DESIGNED_IN);
  const links = level === "process" ? componentLinks(path, text) : [];
  const hasShape = sectionPos(h2Positions(text), "Transactional Shape") !== null;
  const a = { ...DEFAULTS, profile: "strict" };
  const errors = !level ? [] : level === "component" ? checkComponent(path, a, false) : checkProcess(path, a);
  return {
    genome: posix(path),
    sha256: createHash("sha256").update(raw).digest("hex"),
    level,
    components: links.map(([, t, library]) => ({ path: posix(t), library })),
    test_components: !level ? null : level === "process"
      ? tableRows(sectionBody(text, "Components"), "| #").some((row) => row.length > 2 && TEST_GROUP.test(row[2]))
      : /^\d+\. \*\*Test case:/m.test(sectionBody(text, "Workflow")),
    independent_packages: level === "process" ? independentPackages(text) : null,
    extracted,
    source_framework: framework,
    build_mode: !level ? null : framework ? (/\buipath\b/i.test(framework) ? "refactor" : "migration") : extracted ? "unknown" : "build",
    transactional: !level || !hasShape ? null : !sectionBody(text, "Transactional Shape").trim().startsWith(STUB),
    designed_in: designedIn ? posix(resolvePath(dirname(path), designedIn[1])) : null,
    designed_in_link: designedIn ? designedIn[1] : null,
    check: { profile: "strict", ok: Boolean(level) && !errors.length, errors: level ? errors : ["the genome carries no <!-- UIPATH-AUTOMATION-GENOME: component|process marker"] },
  };
}

// --- command line -------------------------------------------------------------------------------

const USAGE = "usage: check-genome.mjs {component,process,tokens} <genome> [options] | context <genome> | skills";
const HELP = `${USAGE}

  component|process <genome>  check a genome: [--profile core|strict] [--expect TOKEN ...] [--source-map TOKEN ...]
                              [--skills SKILL ...] [--shape transactional|stub] [--flows N] [--unit TOKEN ...]
                              [--shape-checks gate|advisory] [--min-steps N] [--min-criteria N]
                              [--processes <inventory.json> --recordsets <recordsets.json>]
  tokens <pattern>            --expect TOKEN ... [--min FRACTION] [--files N]
  context <genome>            JSON of the facts the read plans branch on
  skills                      JSON of the skill names a genome may cite

Options take '--flag value' or '--flag=value'. Exit 0 pass, 1 failures, 2 usage error.`;
const LIST = { "--expect": "expect", "--source-map": "sourceMap", "--skills": "skills", "--unit": "unit" };
const VALUE = {
  "--profile": ["profile", ["core", "strict"]], "--shape": ["shape", ["transactional", "stub"]],
  "--shape-checks": ["shapeChecks", ["gate", "advisory"]], "--flows": ["flows", "int"], "--min-steps": ["minSteps", "int"],
  "--min-criteria": ["minCriteria", "int"], "--min": ["min", "float"], "--files": ["files", "int"],
  "--processes": ["processes", "str"], "--recordsets": ["recordsets", "str"],
};

class UsageError extends Error {}

function parse(argv) {
  const a = { ...DEFAULTS, expect: [], sourceMap: [], skills: [], unit: [] };
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    let arg = argv[i], inline = null;
    const eq = arg.startsWith("--") ? arg.indexOf("=") : -1;
    if (eq > 2) [arg, inline] = [arg.slice(0, eq), arg.slice(eq + 1)];
    if (arg in LIST) {
      if (inline !== null) a[LIST[arg]].push(inline);
      else while (i + 1 < argv.length && !argv[i + 1].startsWith("-")) a[LIST[arg]].push(argv[++i]);
      if (!a[LIST[arg]].length) throw new UsageError(`argument ${arg}: expected at least one argument`);
    } else if (arg in VALUE) {
      const [key, kind] = VALUE[arg];
      if (inline === null && i + 1 >= argv.length) throw new UsageError(`argument ${arg}: expected one argument`);
      const value = inline ?? argv[++i];
      if (Array.isArray(kind) && !kind.includes(value)) throw new UsageError(`argument ${arg}: invalid choice: '${value}' (choose from ${kind.join(", ")})`);
      let number = null;
      if (kind === "int") {
        if (!/^[+-]?\d+$/.test(value.trim())) throw new UsageError(`argument ${arg}: invalid int value: '${value}'`);
        number = Number.parseInt(value, 10);
      } else if (kind === "float") {
        number = value.trim() === "" ? Number.NaN : Number(value);
        if (!Number.isFinite(number)) throw new UsageError(`argument ${arg}: invalid float value: '${value}'`);
      }
      a[key] = number ?? value;
    } else if (inline !== null) {
      throw new UsageError(`unrecognized arguments: ${argv[i]}`);
    } else if (arg.startsWith("-") && arg.length > 1) {
      throw new UsageError(`unrecognized arguments: ${arg}`);
    } else positional.push(arg);
  }
  if (positional.length !== 2) throw new UsageError("the following arguments are required: level, genome");
  if (!["component", "process", "tokens"].includes(positional[0])) throw new UsageError(`argument level: invalid choice: '${positional[0]}' (choose from component, process, tokens, context, skills)`);
  if (Boolean(a.processes) !== Boolean(a.recordsets)) throw new UsageError("--processes and --recordsets go together");
  [a.level, a.genome] = positional;
  return a;
}

export function main(argv = process.argv.slice(2), out = (s) => process.stdout.write(`${s}\n`)) {
  try {
    return run(argv, out);
  } catch (e) {
    if (!(e instanceof InputError)) throw e;
    out(`FAIL: ${e.message}`);
    return 1;
  }
}

function run(argv, out) {
  if (argv.includes("-h") || argv.includes("--help")) {
    out(HELP);
    return 0;
  }
  if (argv[0] === "skills") {
    out(JSON.stringify({ build: [...VALID_SKILLS].sort(), operate: [...OPERATE_SKILLS].sort() }, null, 2));
    return 0;
  }
  if (argv[0] === "context") {
    const paths = argv.length > 1 ? resolveGlob(argv[1]) : [];
    if (paths.length !== 1) { out(`FAIL: context takes exactly one genome, found ${paths.length}`); return 1; }
    out(JSON.stringify(context(paths[0]), null, 2));
    return 0;
  }
  let a;
  try {
    a = parse(argv);
  } catch (e) {
    if (!(e instanceof UsageError)) throw e;
    process.stderr.write(`${USAGE}\ncheck-genome.mjs: error: ${e.message}\n`);
    return 2;
  }
  const paths = resolveGlob(a.genome);
  let errors, notes = [];
  if (a.level === "tokens") {
    errors = [...(paths.length ? [] : [`no file matches ${a.genome}`]), ...checkTokens(paths, a.expect, a.min, a.files)];
  } else if (paths.length !== 1) {
    errors = [`expected exactly one file matching ${a.genome}, found ${paths.length}: ${paths.map(posix).join(", ") || "none"}`];
  } else {
    errors = a.level === "component" ? checkComponent(paths[0], a, false) : checkProcess(paths[0], a);
    if (a.processes) {
      const genomes = a.level === "process" ? componentLinks(paths[0], read(paths[0])).map(([, target, lib]) => [target, lib]) : [[paths[0], false]];
      const [exportErrors, exportNotes] = checkExport(genomes, loadInventory(a.processes, "process inventory"), loadInventory(a.recordsets, "recordset list"));
      errors.push(...exportErrors);
      notes = exportNotes;
    }
  }
  for (const e of errors) out(`FAIL: ${e}`);
  for (const n of notes) out(`NOTE: ${n}`);
  if (!errors.length) out(`OK (${a.level !== "tokens" ? a.profile : "tokens"}): ${paths.map(posix).join(", ")}`);
  return errors.length ? 1 : 0;
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) process.exitCode = main();
