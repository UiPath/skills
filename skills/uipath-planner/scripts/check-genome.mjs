#!/usr/bin/env node
// Checks a genome, and its Source Map's step tables against the source export. Node >= 20, built-ins only.
//
// Usage:
//   check-genome.mjs component <genome.md> [--profile core|strict] [--expect TOKEN ...] [--source-map TOKEN ...]
//   check-genome.mjs process   <genome.md> [--profile core|strict] [--skills SKILL ...] [--expect TOKEN ...]
//   check-genome.mjs tokens    <pattern>   --expect TOKEN ... [--min FRACTION] [--files N]
//   check-genome.mjs skills                 JSON of the skill names a genome may cite: build and operate
//   check-genome.mjs -h | --help
//   component and process also take: [--shape transactional|stub [--flows N] [--unit TOKEN ...]]
//                                    [--shape-checks gate|advisory]  advisory: Transactional Shape findings
//                                    are graded by the strict profile only (a task that tests something else)
//                                    [--processes <inventory.json> --recordsets <recordsets.json>]
//
// uipath-planner runs it with --profile strict after `author`, `extract` and `edit`, and for `check`. An
// extraction through the framework migration pack adds the two files the pack's `data` command writes. The
// genome tasks grade with this file.
//
// Profiles:
//   core    the genome contract a smoke test gates on: level and preamble, every section, valid skill names,
//           steps and criteria present, a Transactional Shape that is the stub or has flows that each name their
//           unit of work, Source Map tokens, expected facts; in an extracted genome (one with a Source Map), a
//           `### Steps` table with exactly one row per Workflow step.
//   strict  core plus every mechanical rule of the genome format, the transactional shape and the extracted
//           genome's Source Map: behavioural wording (no code-level tokens), configuration question kind
//           and default, bold step names, numbered acceptance criteria, the As-is table, exactly the outcome
//           rows the transactional shape allows, split options named by letter with only their Requires and Changes cells,
//           complete for every unit and alternative unit, a decided flow's too, a `Decided:` project chain on option B only and naming two
//           or more projects, retry and consecutive-failure stop; step table cells
//           holding references only; Open Decisions entries open, decided or withdrawn and numbered without a gap,
//           every `*[Inferred]*` mark naming an open entry or a Configuration Question that exists (`*[Inferred: D3]*`,
//           `process D3`, `CQ2`), a withdrawn configuration question kept in place, an entry withdrawn as Configuration Question <n> with a line marked
//           `*[Inferred: CQ<n>]*`; Platform Dependencies' tables
//           in the kinds' order, and a process genome's Deployment with its four bullets; a process genome beside
//           its `<slug>-genome/` component folder, never inside it; no process genome of a dispatcher and a performer alone; a case component (Build With `uipath-maestro-case`) beside a Case
//           Management SDD naming that SDD in its Interface or its `Designed in:` line; no H2 heading twice; no
//           component genome linked twice; no cross-part reference left unfilled (`{{ref:…}}`); the `Source framework`
//           row in the Source Map of a process or standalone component genome; a `Designed in:` line carrying its
//           `sdd-sha256` fingerprint, linking an SDD that can be read (a solution root with every child SDD it
//           lists) and still has that fingerprint, and a component genome carrying its SDD's Action Required items; an SDD written from the genome (`<slug>-sdd.md`, a process
//           genome's `<slug>-solution-sdd.md`) whose `Genome` row carries the genome's current genome-sha256.
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

import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, resolve as resolvePath } from "node:path";
import { pathToFileURL } from "node:url";
import { genomeFingerprint, sddFingerprint } from "./sdd-fingerprint.mjs";

export const VALID_SKILLS = new Set([
  "uipath-rpa", "uipath-maestro-flow", "uipath-maestro-bpmn", "uipath-maestro-case",
  "uipath-agents", "uipath-functions", "uipath-api-workflow", "uipath-coded-apps",
  "uipath-connector-builder", "uipath-ixp", "uipath-process-mining", "uipath-mcp-servers",
  "uipath-solution", "uipath-human-in-the-loop", "uipath-rules",
  "uipath-ontology",
]);
export const OPERATE_SKILLS = new Set([ // allowed in Platform Dependencies / Deployment, never in Build With or Components
  "uipath-platform", "uipath-tasks", "uipath-test", "uipath-admin", "uipath-insights",
  "uipath-troubleshoot", "uipath-governance", "uipath-review", "uipath-planner", "uipath-aops",
  "uipath-automationhub", "uipath-feedback",
  "uipath-activity-migrator", "uipath-bundles", "uipath-vertical-solutions",
]);
const RETIRED_SKILLS = ["uipath-rpa-workflows", "uipath-coded-workflows", "uipath-coded-agents"];
// the skill a genome's preamble routes its build to
export const BUILDER = "uipath-genome";
const routesToBuilder = (s) => /\buipath-genome(?![\w-])/.test(s);

export const COMPONENT_SECTIONS = [
  "Overview", "Target Applications", "Build With", "Platform Dependencies", "Interface",
  "Configuration Questions", "Open Decisions", "Workflow", "Business Rules", "Error Handling",
  "Transactional Shape", "Acceptance Criteria", "Complexity", "Tags",
];
export const PROCESS_SECTIONS = [
  "Overview", "Actors and Systems", "Components", "Process Map", "Handoffs",
  "Platform Dependencies", "Configuration Questions", "Open Decisions", "Business Rules",
  "Error Handling and Recovery", "Transactional Shape", "Acceptance Criteria", "Deployment",
  "Complexity", "Tags",
];
// Platform Dependencies: one `###` table per kind, in this order, then any other service's
export const DEPENDENCY_KINDS = ["Queues", "Assets", "Credentials", "Storage buckets", "Connections", "Data Fabric entities", "Triggers"];
const NO_DEPENDENCIES = "No Orchestrator or Integration Service resources required";
// a process genome's Deployment: what holds wherever it is deployed; the environments themselves are not the genome's
export const DEPLOYMENT_LABELS = ["Packaging and route", "Entry points", "Runtime", "Kept out of the logs"];
// an Open Decisions entry is open (its tier and who answers it), decided or withdrawn; it is never removed
export const DECISION_TIERS = ["business outcome", "run behaviour", "reading", "material"];
const OPEN_ENTRY = new RegExp(`\\((?:${DECISION_TIERS.join("|")}); answered by: `);
const DECIDED_ENTRY = /\(decided \d{4}-\d{2}-\d{2}: /;
const WITHDRAWN_ENTRY = /\(withdrawn: /;
const NO_DECISIONS = "No open decisions";
// `*[Inferred]*`, `*[Inferred: D3]*`, `*[Inferred: process D3]*`, `*[Inferred: CQ2]*`
const INFERRED_MARK = /\*\[Inferred(?::\s*([^\]]*))?\]\*/g;
const MARK_TARGET = /^(process\s+)?(D|CQ)(\d+)\b/;
// Code-level tokens that must not appear in the genome body (Source Map excluded).
const BANNED_BODY_TOKENS = [
  "InvokeWorkflowFile", "RetryScope", "TryCatch", "ReadRange", "AppendRange", "WriteRange",
  "GetIMAPMailMessages", "SaveAttachments", "AddQueueItem", "ReadPDFText", "LogMessage",
  "AndAlso", "OrElse", "dt_", "in_", "out_", ".xaml", "core.action", "core.logic",
  "uipath.core.", "activityType", "JsInvoke",
];
// a number another agent of an extraction in parts fixes later, which reconciliation fills in
const UNFILLED_REFERENCE = /\{\{ref:[^}\n]*\}\}/g;
export const OUTCOME_ROWS = new Set(["Success", "Business exception", "System exception", "Postponed"]);
// the genome format's minimum Workflow steps and Acceptance Criteria per complexity, a component genome's.
// core gates only on the floor every genome meets (the simple minimum); the per-complexity minimum is strict.
const CORE_FLOOR = 3;
const MIN_STEPS_BY_COMPLEXITY = { simple: 3, medium: 5, complex: 8 };
const MIN_CRITERIA_BY_COMPLEXITY = { simple: 3, medium: 5, complex: 7 };
const SPLIT_OPTIONS = ["A", "B", "C"];
export const SPLIT_COLUMNS = ["unit of work", "option", "requires", "changes against as-is"];
export const STUB = "Not transactional";
// a flow with one side outside the genome names it instead of the table
const EXTERNAL_SIDE = /Split options:(?:\*\*)? none\s*[—–-]+\s*the (consumer|producer) is outside this genome/i;
// an extracted genome's Source Map step table
export const STEPS_COLUMNS = ["step", "source objects", "data sets", "captures", "notes"];
const REFERENCE = /^`([^`]+)`(?:\s*\(((?:[^()`]|`[^`]*`)*)\))?$/; // `Name`, `Name` (id), `Name` (id, locator)
// The `{…}` placeholders of the genome templates' Transactional Shape sections, a one-word one with the word before it (`with {result}`, `retried {n}`). A genome's own
// braces — a value built from parts, such as `{item}_{date}` or `INV-{n}` — are content, not a placeholder left
// unfilled. tests/tasks/uipath-planner/_shared/test_genome_contract.py keeps this list equal to the templates.
export const TEMPLATE_PLACEHOLDERS = [
  "— {unit}",
  "{a–b}",
  "{c–d}",
  "{unit of work}",
  ": {producer}",
  "→ {consumer}",
  "{producer | consumer | producer and consumer | consumer of Flow {M}",
  "{one sentence}",
  "one {item}",
  "{identifying field(s)}",
  "{volume and cadence}",
  "{items fail, retry and are reported independently at this level; the reference exists; the retry cost is acceptable}",
  "{other item}",
  "when {condition}",
  "{steps that create items; how often; one source or several; guarded by a lock or ledger?}",
  "{steps that take items; one robot or several; how items are picked; order}",
  "{queue / table / in-memory list / folder}",
  "{status, tags, fields, output}",
  "{parent items, ledgers, locks, tag joins — what each is for; \"none\"}",
  "{one kind, or several routed inside the consumer — what differs}",
  "steps {n}",
  "{p–q}",
  "steps {r}",
  "with {result}",
  "rules: {names}",
  "handlers: {names}",
  "retried {n}",
  "after {m}",
  "{what takes the items}",
  "| {unit}",
  "{what this flow needs for one job to hold both roles — or \"excluded: {the fact that rules it out}",
  "{projects and schedules, where per-item state is visible, retry granularity, end-of-parent work}",
  "{alternative unit}",
  "{facts only — robots, schedules, sources, applications per item kind, whether items survive a run today}",
  "{only when the SDD, the request or the refactor answers already chose the split: option and unit — source; for B, `: <Project> → <Project>[ → …]` when the source names the projects (transactional shape guide rule 8)}",
  "{a, b}",
  "{c, d}",
  "{per-item record and where it lands; screenshot on system exception; run summary}",
  "{reason — the run is one unit of work; one item's work started per item by {caller}",
  "component {p}",
  "component {c}",
  "row {n}",
  "component {d}",
  "row {m}",
  "{component # and steps that create items; how often; one source or several; guarded by a lock or ledger?}",
  "{component # and steps that take items; one robot or several; how items are picked; order}",
  "run: {steps}",
  "item: {steps}",
  "end: {steps}",
  "{component #}",
  "{per-item record and where it lands; the upstream reference a chained item carries; screenshot on system exception; run summary; which component reports on them}",
  "{same block}",
];

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

/** strict: a process or standalone component genome's Source Map (one holding a table) has a `Source framework`
 * row in any of its tables (`| Row |` in a component, `| Component |` in a process); a part inherits it. */
function checkSourceFramework(text, r) {
  const rows = lines(sectionBody(text, "Source Map")).filter((l) => l.trim().startsWith("|")).map(cells);
  const hasFrameworkRow = rows.some((c) => c.length > 1 && c[0].replace(/\*/g, "").trim().toLowerCase() === "source framework");
  if (rows.length && !hasFrameworkRow) r.strict("Source Map has no 'Source framework' row");
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

function checkCommon(path, text, level, sections, r, minCriteria) {
  if (!new RegExp(`UIPATH-AUTOMATION-GENOME:\\s*${level}`, "i").test(text)) r.core(`missing preamble comment 'UIPATH-AUTOMATION-GENOME: ${level}'`);
  else if (!text.includes(`UIPATH-AUTOMATION-GENOME: ${level}`)) r.strict(`preamble comment not written exactly 'UIPATH-AUTOMATION-GENOME: ${level}'`);
  if (!/UiPath automation blueprint/i.test(text)) r.core("missing blueprint blockquote");
  else if (!text.includes("This is a UiPath automation blueprint")) r.strict("blueprint blockquote not written as the template words it");
  // the preamble routes the agent to the skill that builds the genome, not to the Build With skills
  const comment = text.match(/<!--\s*UIPATH-AUTOMATION-GENOME[\s\S]*?-->/i);
  if (comment && !routesToBuilder(comment[0])) r.strict(`preamble comment does not name ${BUILDER} as the skill that builds the genome`);
  const blockquote = text.match(/^>.*UiPath automation blueprint.*$/im);
  if (blockquote && !routesToBuilder(blockquote[0])) r.strict(`blueprint blockquote does not name ${BUILDER} as the skill that builds the genome`);
  const designedIn = text.match(/^>\s*Designed in:[^\n]*/m);
  if (designedIn && !/\bsdd-sha256\s+[0-9a-f]{64}\b/.test(designedIn[0])) r.strict("Designed in: line has no sdd-sha256 fingerprint");
  checkDesignedIn(path, text, level, r);
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
      if (!VALID_SKILLS.has(name) && !OPERATE_SKILLS.has(name) && name !== BUILDER) r.core(`unknown skill name '${name}' in ${heading}`);
    }
  }
  for (const heading of ["Build With", "Components"]) {
    for (const name of skillNames(sectionBody(text, heading))) {
      // advisory: a platform row in Build With does no harm — the
      // resources still reach the target through the solution and the open-items files
      if (OPERATE_SKILLS.has(name)) r.strict(`operate-only skill '${name}' in ${heading}; it belongs under Platform Dependencies`);
    }
  }
  // a criterion is a list item in any form: '- ', '- [ ] ', '* ' or '1. '; the genome format numbers them
  const criteria = lines(sectionBody(text, "Acceptance Criteria")).filter((l) => /^(?:[-*]|\d+\.) \S/.test(l));
  if (criteria.length < CORE_FLOOR) r.core(`acceptance criteria: ${criteria.length} found, expected >= ${CORE_FLOOR}`);
  else if (criteria.length < minCriteria) r.strict(`acceptance criteria: ${criteria.length} found, expected >= ${minCriteria} for the stated complexity`);
  if (criteria.some((l) => !/^\d+\. /.test(l))) r.strict("acceptance criteria are not numbered ('1. …'), so a report cannot cite them by number");
  for (const line of criteria) if (/completes successfully|handles errors properly/i.test(line)) r.core(`generic acceptance criterion: ${line.trim()}`);

  const body = bodyWithoutSourceMap(text);
  for (const tok of BANNED_BODY_TOKENS) {
    // a prefix token counts at a word start, in a word holding a capital, as UiPath names arguments and variables:
    // `in_Folder`, `in_strPath`, never "login_page" or a record's field `in_reply_to`, which the genome spells as the source does
    if (tok.endsWith("_") ? new RegExp(`\\b${esc(tok)}\\w*[A-Z]`).test(body) : body.includes(tok)) r.strict(`code-level token '${tok}' in the genome body (outside Source Map)`);
  }
  const unfilled = text.match(UNFILLED_REFERENCE);
  if (unfilled) r.strict(`${unfilled.length} cross-part reference(s) left unfilled, first: ${unfilled[0]}`);
  for (const [, num, question] of sectionBody(text, "Configuration Questions").matchAll(/^(\d+)\. (.*)$/gm)) {
    const pointer = !question.includes("?") && /Configuration Question \d+/.test(question); // a question the process genome asks
    const withdrawn = /^Withdrawn: /.test(question); // kept so later questions keep their numbers
    if (!pointer && !withdrawn && !/\((setting|constant); default:/.test(question)) r.strict(`configuration question ${num} does not name its kind and default as '(setting; default: …)' or '(constant; default: …)'`);
  }
}

/** Map of entry number → 'open' | 'decided' | 'withdrawn' | 'malformed' for a genome's Open Decisions. */
export function openDecisions(text) {
  const entries = new Map();
  for (const [, num, entry] of sectionBody(text, "Open Decisions").matchAll(/^(\d+)\. (.*)$/gm)) {
    const status = DECIDED_ENTRY.test(entry) ? "decided" : WITHDRAWN_ENTRY.test(entry) ? "withdrawn" : OPEN_ENTRY.test(entry) ? "open" : "malformed";
    entries.set(Number(num), status);
  }
  return entries;
}

/** strict: Open Decisions entries in one of their forms, numbered without a gap, and every `*[Inferred]*` mark
 * naming an open entry or a Configuration Question that exists. A `process D<n>` mark is checked only when the
 * process genome's entries are known (the component is checked through its process genome). */
/** The entry numbers a genome's text names outside its Open Decisions section: its own (`D3`), or with
 * processScope the process genome's (`process D3`). */
export function namedEntries(text, processScope = false) {
  const rest = text.replace(sectionBody(text, "Open Decisions"), "");
  if (processScope) return new Set([...rest.matchAll(/\bprocess\s+D(\d+)\b/g)].map((m) => Number(m[1])));
  // the forms that name an entry: a mark (`*[Inferred: D3]*`), a defect's `(ruling open: D3)`, a row's `(D3)` or `(D1, D3)`
  const named = new Set();
  for (const m of rest.matchAll(/\*\[Inferred:\s*D(\d+)\]\*|\((?:ruling open:\s*)?(D\d+(?:\s*,\s*D\d+)*)\)/g)) {
    for (const n of (m[1] ? `D${m[1]}` : m[2]).matchAll(/D(\d+)/g)) named.add(Number(n[1]));
  }
  return named;
}

function checkOpenDecisions(text, r, processEntries = null, namedElsewhere = new Set()) {
  const section = sectionBody(text, "Open Decisions");
  const entries = openDecisions(text);
  if (section.trim() && !entries.size && !section.includes(NO_DECISIONS)) r.strict("Open Decisions: neither numbered entries nor the stub line");
  const numbers = [...section.matchAll(/^(\d+)\. /gm)].map((m) => Number(m[1]));
  for (const num of new Set(numbers.filter((n, i) => numbers.indexOf(n) !== i))) r.strict(`Open Decisions: entry ${num} appears more than once`);
  [...entries.keys()].forEach((num, i) => {
    if (num !== i + 1) r.strict(`Open Decisions: entry ${num} follows entry ${i}; an entry stays when decided or withdrawn, so the numbers never skip`);
  });
  for (const [num, status] of entries) {
    if (status === "malformed") r.strict(`Open Decisions entry ${num} is none of '({tier}; answered by: …', '(decided YYYY-MM-DD: …' or '(withdrawn: …' — tiers: ${DECISION_TIERS.join(", ")}`);
  }
  const questions = new Set([...sectionBody(text, "Configuration Questions").matchAll(/^(\d+)\. /gm)].map((m) => Number(m[1])));
  const unnamed = [];
  for (const [mark, target] of text.matchAll(INFERRED_MARK)) {
    const m = (target ?? "").trim().match(MARK_TARGET);
    if (!m) { unnamed.push(mark); continue; }
    const [, processScope, kind, n] = m;
    const num = Number(n);
    if (kind === "CQ") {
      if (!processScope && !questions.has(num)) r.strict(`${mark} names Configuration Question ${num}, which this genome does not have`);
      continue;
    }
    const pool = processScope ? processEntries : entries;
    if (!pool) continue;
    const where = processScope ? "the process genome's Open Decisions" : "Open Decisions";
    if (!pool.has(num)) r.strict(`${mark} names entry ${num}, which ${where} does not have`);
    else if (pool.get(num) !== "open") r.strict(`${mark} names entry ${num} of ${where}, which is ${pool.get(num)}: a settled point keeps no marker`);
  }
  if (unnamed.length) r.strict(`${unnamed.length} *[Inferred]* mark(s) name no Open Decisions entry or Configuration Question (write *[Inferred: D<n>]*), first: ${unnamed[0]}`);
  // an entry withdrawn into a Configuration Question keeps its point marked on the line that uses the question
  for (const [, num, n] of section.matchAll(/^(\d+)\. .*\(withdrawn: asked as Configuration Question (\d+)/gm)) {
    if (!new RegExp(`\\*\\[Inferred:\\s*CQ${n}\\]\\*`).test(text)) r.strict(`Open Decisions entry ${num} is withdrawn as Configuration Question ${n}, and no line carries *[Inferred: CQ${n}]*: mark the line that uses the question, *[Inferred: CQ${n}]* (SDD [SME REVIEW]: <note>)`);
  }
  const named = namedEntries(text);
  for (const [num, status] of entries) {
    if (status === "open" && !named.has(num) && !namedElsewhere.has(num)) r.strict(`Open Decisions entry ${num} is named nowhere in the genome: mark the line that states its point (*[Inferred: D${num}]*), or name it at its defect, row or step`);
  }
}

/** strict: the SDD a `Designed in:` line links still has the fingerprint the line records. */
function checkDesignedIn(path, text, level, r) {
  const m = text.match(DESIGNED_IN);
  if (!m || !m[2]) return;
  const sdd = resolvePath(dirname(path), m[1]);
  let matches;
  // a line taken over the whole SDD, its Action Required section included, still matches an SDD that has not changed
  try { matches = sddFingerprint(sdd) === m[2] || sddFingerprint(sdd, { keepOpenQuestions: true }) === m[2]; } catch { r.strict(`Designed in: ${m[1]} or a child SDD it lists cannot be read`); return; }
  if (!matches) r.strict(`Designed in: sdd-sha256 does not match ${m[1]}; the SDD changed since the genome was written`);
  // a component genome holds every gap of its SDD: an SDD with Action Required items, a genome with none of them
  if (level !== "component") return;
  const asked = sectionBody(read(sdd), "Action Required");
  const hasItems = /\[(?:SME REVIEW|DEFAULT)\]/.test(asked) || /^\|\s*\d+\s*\|/m.test(asked) || /\*\*(?:D|CQ)\d+/.test(asked);
  if (hasItems && !/\(SDD \[(?:SME REVIEW|DEFAULT)\]/.test(text) && !openDecisions(text).size) {
    r.strict(`${m[1]} has Action Required items and the genome carries none: write each as an Open Decisions entry and its marked line, *[Inferred: D<n>]* (SDD [SME REVIEW]: <note>); an operator setting as a Configuration Question, its entry 'withdrawn: asked as Configuration Question <n>' and its line marked *[Inferred: CQ<n>]*`);
  }
}

const GENOME_ROW = /^\|\s*\*\*Genome\*\*\s*\|[^\n]*?\bgenome-sha256\s+([0-9a-f]{64})\b/m;

/** strict: the SDD written from this genome — `<slug>-sdd.md` beside it, a process genome's `<slug>-solution-sdd.md` —
 * still carries the genome's fingerprint. A genome with a `Designed in:` line has its SDD as the source instead. */
function checkWrittenSdd(path, text, level, r) {
  if (DESIGNED_IN.test(text)) return;
  const slug = baseName(path).replace(/-genome\.md$/i, "");
  const sdd = join(dirname(path), `${slug}${level === "process" ? "-solution" : ""}-sdd.md`);
  if (!existsSync(sdd)) return;
  const row = read(sdd).match(GENOME_ROW);
  if (!row) { r.strict(`${baseName(sdd)} beside the genome has no 'Genome' handoff row carrying its genome-sha256 fingerprint`); return; }
  let current;
  try { current = genomeFingerprint(path); } catch { r.strict(`${baseName(sdd)}: a component genome the genome links cannot be read for its genome-sha256`); return; }
  if (current !== row[1]) r.strict(`${baseName(sdd)}: genome-sha256 does not match the genome; the genome changed since the SDD was written from it`);
}

/** strict: Platform Dependencies holds the stub or a table per kind in the kinds' order, another service's after
 * them; a process genome's Deployment holds its bullets. */
function checkPlatformDependencies(text, level, r) {
  const body = sectionBody(text, "Platform Dependencies");
  const tables = [...body.matchAll(/^### (.+)$/gm)].map((m) => m[1].trim());
  if (!tables.length && !body.includes(NO_DEPENDENCIES)) r.strict(`Platform Dependencies: neither a table per kind nor the stub line '${NO_DEPENDENCIES}.'`);
  let last = -1, other = null;
  for (const h of tables) {
    const kind = DEPENDENCY_KINDS.indexOf(h);
    if (kind === -1) { other ??= h; continue; }
    if (other) r.strict(`Platform Dependencies: '### ${h}' after '### ${other}'; another service's table follows the kinds`);
    else if (kind < last) r.strict(`Platform Dependencies: '### ${h}' out of the kinds' order ${repr(DEPENDENCY_KINDS)}`);
    last = Math.max(last, kind);
  }
  if (level !== "process") return;
  const missing = DEPLOYMENT_LABELS.filter((l) => !new RegExp(`^- \\*\\*${esc(l)}:\\*\\*`, "m").test(sectionBody(text, "Deployment")));
  if (missing.length) r.strict(`Deployment: no bullet for ${repr(missing)}`);
}

/** [flows, headed]: the '### Flow N' blocks, or — when there is no such heading but the section names a
 * unit of work — the whole section as one flow. The heading is a format rule; the unit of work is the contract. */
function effectiveFlows(ts) {
  const blocks = flowBlocks(ts);
  if (blocks.length) return [blocks, true];
  if (/unit of work/i.test(ts)) return [[["Flow 1", ts]], false];
  return [[], false];
}

const DECIDED_CHAIN = /:\s+([^:]*→[^:]*|[A-Za-z][\w.-]*)\s*$/;
// project names after the source's last ': ' joined by any chain separator; only ' → ' names a chain
const DECIDED_LIST = /:\s+([A-Z][\w.-]*(?:\s*(?:→|->|,|\band\b)\s*[A-Z][\w.-]*)+)\s*$/;
const LIST_SEPARATOR = /\s*(?:→|->|,|\band\b)\s*/g;

/** Transactional Shape: the stub, or flow blocks of the transactional shape format. */
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
  const unfilled = TEMPLATE_PLACEHOLDERS.filter((p) => ts.includes(p));
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
      // the consumer owes the item retry and the consecutive-failure stop
      if (!/retr(y|ie)/i.test(body) || !/consecutive|stops? after \d/i.test(body)) r.strict(`Transactional Shape ${name}: outcomes do not state the item retry and the consecutive-failure stop`);
    }
    if (external) continue;
    const units = new Map();
    for (const row of split) {
      const m = row.length >= 2 ? row[1].match(/^([ABC])\b/) : null;
      if (m) { if (!units.has(row[0])) units.set(row[0], new Set()); units.get(row[0]).add(m[1]); }
      if (row.length >= 2 && !SPLIT_OPTIONS.includes(row[1].trim())) r.strict(`Transactional Shape ${name}: option cell '${row[1]}' of '${row[0]}' holds more than its letter — the transactional shape guide defines A, B and C`);
    }
    // a split the SDD, the request or the refactor answers already took (`**Decided:** B, ...`) names one row of a table kept whole
    const decidedLine = lines(body).find((l) => l.startsWith("**Decided:**")) ?? "";
    const decided = decidedLine.match(/^\*\*Decided:\*\*\s*([ABC])\b(?:,\s*([^—–]+?))?\s*(?:[—–]\s*(.*)|$)/);
    if (decidedLine && !decided) r.strict(`Transactional Shape ${name}: the 'Decided:' line does not start with the option letter`);
    if (decided) {
      // `<source>: <Project> → <Project> …` — a bare single name after the last ': ' is a one-project chain
      const chain = (decided[3] ?? "").match(DECIDED_CHAIN);
      const list = decided[1] === "B" ? (decided[3] ?? "").match(DECIDED_LIST) : null;
      if (list && list[1].match(LIST_SEPARATOR).some((sep) => sep.trim() !== "→")) {
        r.strict(`Transactional Shape ${name}: the 'Decided:' project chain '${list[1].trim()}' separates its projects with '->', ',' or ' and ' — separate them with ' → '`);
      } else if (chain) {
        const projects = chain[1].split("→").map((p) => p.trim());
        if (decided[1] !== "B") r.strict(`Transactional Shape ${name}: the 'Decided:' line of option ${decided[1]} names a project chain — only option B names its projects`);
        else if (projects.length < 2 || projects.some((p) => !p)) r.strict(`Transactional Shape ${name}: the 'Decided:' project chain '${chain[1].trim()}' does not name two or more projects separated by ' → '`);
      }
      const unit = (decided[2] ?? "").trim();
      const pool = unit && units.has(unit) ? [units.get(unit)] : unit ? [] : [...units.values()];
      if (!pool.some((opts) => opts.has(decided[1]))) r.strict(`Transactional Shape ${name}: decided option ${decided[1]}${unit ? ` of '${unit}'` : ""} has no Split options row`);
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
    if (!data.length && row[2].trim().toLowerCase() !== "none") r.strict(`step table, step ${row[0]}: Data sets is empty — write 'none' when no data set drives the step`);
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

/** strict: a case component (Build With `uipath-maestro-case`) beside a Case Management SDD — in its folder or the
 * one above, the SDD whose first section is `## Section 1: Case Definition` — names that SDD as its build input, in
 * its Interface or its own `Designed in:` line. */
function checkCaseBuildInput(path, text, r) {
  if (!/uipath-maestro-case/.test(sectionBody(text, "Build With"))) return;
  const here = dirname(resolvePath(path));
  const caseSdds = [here, dirname(here)].flatMap((dir) => {
    let names;
    try { names = readdirSync(dir); } catch { return []; }
    return names.filter((n) => /-sdd\.md$/i.test(n) && /^## Section 1: Case Definition\b/m.test(read(join(dir, n))));
  });
  if (!caseSdds.length) return;
  const named = sectionBody(text, "Interface") + (text.match(DESIGNED_IN)?.[0] ?? "");
  if (!caseSdds.some((n) => named.includes(n))) r.strict(`case component: Interface names no case SDD as its build input; name ${caseSdds[0]} (its path relative to the genome)`);
}

function checkComponent(path, a, partOf, shape = true, library = false, processEntries = null) {
  const text = read(path);
  // a library is named so in its process genome's Components table, or in its own Transactional Shape stub
  library = library || /^Not transactional:[^\n]*\blibrar(y|ies)\b/i.test(sectionBody(text, "Transactional Shape").trim());
  const r = new Report(a.profile, a.shapeChecks === "gate");
  const level = complexityOf(text);
  const minSteps = MIN_STEPS_BY_COMPLEXITY[level] ?? a.minSteps;
  checkCommon(path, text, "component", COMPONENT_SECTIONS, r, MIN_CRITERIA_BY_COMPLEXITY[level] ?? a.minCriteria);
  const pos = h2Positions(text);
  const bw = sectionPos(pos, "Build With"), wf = sectionPos(pos, "Workflow");
  if (bw !== null && wf !== null && bw > wf) r.core("Build With must precede Workflow");
  if (!/uipath-[a-z-]+/.test(sectionBody(text, "Build With"))) r.core("Build With names no skill");
  checkCaseBuildInput(path, text, r);
  const workflow = sectionBody(text, "Workflow");
  const steps = (workflow.match(/^(?:\d+\.|[-*]) \S/gm) ?? []).length; // top-level numbered or bulleted steps
  // a test component's steps are its cases and a library's its public workflows
  const exempt = library || /^\d+\. \*\*Test case:/m.test(workflow);
  if (steps < CORE_FLOOR && !exempt) r.core(`workflow: ${steps} numbered steps, expected >= ${CORE_FLOOR}`);
  else if (steps < minSteps && !exempt) r.strict(`workflow: ${steps} numbered steps, expected >= ${minSteps} for complexity ${level || "not stated"}`);
  if ((workflow.match(/^\d+\. \*\*/gm) ?? []).length < Math.min(steps, minSteps)) r.strict("workflow: steps not all in the '1. **Step name**' form");
  const cq = sectionBody(text, "Configuration Questions");
  const questions = cq.match(/^\d+\. /gm) ?? [];
  if (!cq.trim()) r.core("Configuration Questions section is empty");
  else if (!questions.length && !cq.includes("no configuration needed")) r.strict("Configuration Questions: neither a numbered list of questions nor the stub line");
  checkOpenDecisions(text, r, processEntries);
  checkPlatformDependencies(text, "component", r);
  if (a.sourceMap.length) {
    const sm = sectionBody(text, "Source Map");
    if (!sm.trim()) r.core("missing or empty '## Source Map' section");
    for (const tok of a.sourceMap) if (!sm.includes(tok)) r.core(`Source Map does not mention '${tok}'`);
  }
  checkStepsTable(text, r);
  if (!partOf && !text.includes("Part of:")) { checkSourceFramework(text, r); checkWrittenSdd(path, text, "component", r); }
  if (partOf && !text.includes("Part of:")) r.strict("component inside a process genome lacks the 'Part of:' line");
  checkTransactional(text, "component", r, partOf);
  if (a.shape && shape) checkShapeAssertion(text, a.shape, a.flows, a.unit, r);
  for (const tok of a.expect) if (!text.toLowerCase().includes(tok.toLowerCase())) r.core(`expected token '${tok}' not found`);
  return r.errors.map((e) => `${baseName(path)}: ${e}`);
}

function checkProcess(path, a) {
  const text = read(path);
  const r = new Report(a.profile, a.shapeChecks === "gate");
  // the population matrix's criteria floors are a component genome's; a process genome holds only end-to-end criteria
  checkCommon(path, text, "process", PROCESS_SECTIONS, r, CORE_FLOOR);
  const pos = h2Positions(text);
  const cp = sectionPos(pos, "Components"), pm = sectionPos(pos, "Process Map");
  if (cp !== null && pm !== null && cp > pm) r.core("Components must precede Process Map");
  const comp = sectionBody(text, "Components");
  if (lines(comp).filter((l) => l.startsWith("|") && l.includes("uipath-")).length < 2) r.core("Components table: fewer than 2 rows naming a skill");
  for (const s of a.skills) if (!new RegExp(`\\b${esc(s)}\\b`).test(comp)) r.core(`Components table lacks skill '${s}'`);
  for (const row of tableRows(comp, "| #")) {
    if (row.length > 2 && /\b(dispatcher|performer)\b/i.test(row[2])) r.strict(`Components: role word in the Type cell of '${row[1]}' — it reads the component type only`);
  }
  // a dispatcher and a performer over one queue are one `uipath-rpa` component, their split its Transactional Shape
  const rows = tableRows(comp, "| #").filter((row) => row.join("|").includes("uipath-"));
  if (rows.length === 2 && rows.every((row) => row.join("|").includes("uipath-rpa"))
    && rows.some((row) => /dispatch/i.test(row.join("|"))) && rows.some((row) => /perform/i.test(row.join("|")))) {
    r.strict("Components: a dispatcher and a performer alone are ONE uipath-rpa component, its split recorded in the Transactional Shape — write a component genome, not a process genome");
  }
  const links = componentLinks(path, text);
  if (!links.length) r.core("Components table links no component genome");
  const targets = links.map(([, t]) => posix(t).toLowerCase());
  const first = (i) => targets.indexOf(targets[i]) === i;
  for (const [link] of links.filter((_, i) => !first(i))) r.strict(`Components table links ${link} more than once`);
  // `<slug>-genome.md` sits beside its `<slug>-genome/` folder, never inside it — whatever the folder is spelled
  const slug = baseName(path).replace(/-genome\.md$/i, "");
  const home = dirname(resolvePath(path));
  const sameFolder = links.some(([, target]) => posix(dirname(target)).toLowerCase() === posix(home).toLowerCase());
  if (/-genome$/i.test(baseName(home)) && (sameFolder || baseName(home).toLowerCase() === `${slug}-genome`.toLowerCase())) {
    r.strict(`process genome sits inside its component folder ${baseName(home)}/; write it beside that folder`);
  }
  checkSourceFramework(text, r);
  checkWrittenSdd(path, text, "process", r);
  // the process genome's entries are named in its own text or in a component's (`process D3`)
  const namedByComponents = new Set();
  for (const [, target] of links) {
    if (!existsSync(target)) continue;
    try { for (const n of namedEntries(read(target), true)) namedByComponents.add(n); } catch (e) { if (!(e instanceof InputError)) throw e; }
  }
  checkOpenDecisions(text, r, null, namedByComponents);
  checkPlatformDependencies(text, "process", r);
  const processEntries = openDecisions(text);
  const componentErrors = [];
  for (const [link, target, isLibrary] of links.filter((_, i) => first(i))) {
    if (!existsSync(target)) r.core(`linked component genome missing on disk: ${link}`);
    else {
      // one unreadable component file is one finding; the process genome and its other components are still checked
      try { componentErrors.push(...checkComponent(target, { ...a, expect: [], sourceMap: [] }, true, false, isLibrary, processEntries)); }
      catch (e) { if (!(e instanceof InputError)) throw e; r.core(e.message); }
    }
  }
  const handoffs = lines(sectionBody(text, "Handoffs")).filter((l) => l.startsWith("|"));
  if (handoffs.length < 3) r.core(`Handoffs table: ${Math.max(0, handoffs.length - 2)} rows, expected >= 1`); // header + separator + >= 1 row: two components share at least one edge
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

const DESIGNED_IN = /^>\s*Designed in:\s*\[[^\]]*\]\(([^)]+)\)(?:[^\n]*?\bsdd-sha256\s+([0-9a-f]{64})\b)?/m;

// --- command line -------------------------------------------------------------------------------

const USAGE = "usage: check-genome.mjs {component,process,tokens} <genome> [options] | skills";
const HELP = `${USAGE}

  component|process <genome>  check a genome: [--profile core|strict] [--expect TOKEN ...] [--source-map TOKEN ...]
                              [--skills SKILL ...] [--shape transactional|stub] [--flows N] [--unit TOKEN ...]
                              [--shape-checks gate|advisory] [--min-steps N] [--min-criteria N]
                              [--processes <inventory.json> --recordsets <recordsets.json>]
  tokens <pattern>            --expect TOKEN ... [--min FRACTION] [--files N]
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
  if (!["component", "process", "tokens"].includes(positional[0])) throw new UsageError(`argument level: invalid choice: '${positional[0]}' (choose from component, process, tokens, skills)`);
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
