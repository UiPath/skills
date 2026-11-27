#!/usr/bin/env node
// Mechanical check of a written Case Management SDD (assets/templates/case-sdd-template.md), run before the
// Conformance Checklist walk (references/design/sdd-writing-guide.md Step 4 item 8) and after a draft finalization
// (the case template's Validation footer, FINALIZING a draft).
//
// Usage: node case-sdd-check.mjs <NAME>.md          a final SDD, or one written without a draft
//        node case-sdd-check.mjs --draft <NAME>.draft.md   a draft: the title, Sections 1-2 and one block per stage only
// Exit 0 and "OK" when: the first line is `# SDD — <Case Name>`; the template's required headings exist; every
// stage block holds **Type:**, **Design Rationale:**, Entry and Exit Conditions and a Tasks table; every task block
// holds **Type:**, **Activation Mode:**, **Design Rationale:**, **Entry Condition:** and **Task envelope**; every
// **Type:** is `Stage` or one of the 17 task types, written bare; **Stage Kind:** is primary or secondary; no stage,
// task or SLA title holds a ':'; every § SLA Response Map row follows the template's cell rules and closes both ways
// with the SDD's `sla-status-change(...)` rows; § Personas has the template's six cells, Scope Case or Stages and only the
// template's permission keys; an action task's **HITL Implementation:** is `Action App: <title>`, never another task's;
// a task's Activation Mode is the same in its Tasks table row and its block. Exit 1 with one FAIL line per defect.
import { existsSync, readFileSync } from "node:fs";

const TASK_TYPES = new Set([
  "action", "agent", "rpa", "process", "api-workflow", "function", "business-rule", "execute-connector-activity",
  "wait-for-connector", "wait-for-timer", "case-management", "http-request", "flow-process", "external-agent",
  "external-workflow", "document-extraction", "script",
]);
const MEANT = { "connector-activity": "execute-connector-activity", "connector-trigger": "wait-for-connector", "wait-for-event": "wait-for-connector" };
const HEADINGS = [
  "## Table of Contents", "## Section 1: Case Definition", "### Case Metadata", "### Case Triggers",
  "### Case Exit Conditions", "### Case Variables", "## Section 2: Stages & Tasks", "## Section 3: Personas & App Views",
  "### Personas", "### Process App Views", "## Section 4: Integrations",
];
const STAGE_MARKERS = ["**Type:**", "**Design Rationale:**", "#### Stage Entry Conditions", "#### Stage Exit Conditions", "#### Tasks"];
const TASK_MARKERS = ["**Type:**", "**Activation Mode:**", "**Design Rationale:**", "**Entry Condition:**", "**Task envelope**"];
const PROC = ["Process / Agent / RPA / API Workflow Task Detail", "**Resolved Resource:**"];
const CONN = ["Connector Task Detail", "**Connector:**", "**Resolved Resource:**"];
const DETAIL = {
  action: ["Action Task Detail", "**HITL Implementation:**"],
  "wait-for-connector": ["Connector Task Detail", "**Connector:**", "**Trigger / Event:**"],
  "execute-connector-activity": CONN, "external-agent": CONN, "external-workflow": CONN,
  "wait-for-timer": ["Timer Task Detail", "**Timer Configuration:**", "**Duration:**", "**Timer:**"],
  "case-management": ["Child Case Task Detail", "**Child Case:**"],
  "http-request": ["HTTP Request Task Detail", "**Method:**", "**URL:**"],
  script: ["Script Task Detail", "```js", "```javascript"],
  "document-extraction": ["Document Extraction Task Detail", "**IXP Deployment:**", "**Model Name:**"],
  process: PROC, agent: PROC, rpa: PROC, "api-workflow": PROC, function: PROC, "business-rule": PROC, "flow-process": PROC,
};
// legal rules per gate (the case schema's rule types)
const GATE = {
  "stage-entry": ["case-entered", "selected-stage-completed", "selected-stage-exited", "wait-for-connector", "user-selected-stage", "sla-status-change", "api-event"],
  "task-entry": ["current-stage-entered", "selected-tasks-completed", "wait-for-connector", "adhoc", "runs-sequentially", "sla-status-change", "api-event"],
  "stage-complete": ["required-tasks-completed", "wait-for-connector", "api-event"],
  "stage-exit": ["selected-tasks-completed", "wait-for-connector", "api-event"],
  "case-complete": ["required-stages-completed", "wait-for-connector", "api-event"],
  "case-exit": ["selected-stage-completed", "selected-stage-exited", "wait-for-connector", "api-event"],
};
const RESPONSES = new Set(["notify-only", "start-task", "enter-stage", "exit-stage", "exit-case"]);
const STAGE = /^###\s+(Stage\s+\d+|Secondary Stage|Exception Stage):\s*(.*?)\s*$/gm;
const TASK = /^#####\s+Task\s+S?\d+\.\d+:\s*(.+?)\s*$/gm;
const strip = (name) => name.replace(/_\([^)]*\)_\s*$/, "").replace(/\s*\([^)]*\)\s*$/, "").trim();
const dash = (c) => ["", "-", "—", "–", "n/a", "na"].includes(c.trim().replace(/^[`*]+|[`*]+$/g, "").toLowerCase());
const cellsOf = (line) => line.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim().replace(/^[`*]+|[`*]+$/g, ""));

const draftMode = process.argv.includes("--draft");
const path = process.argv.slice(2).find((a) => a !== "--draft");
if (!path) { console.error("usage: node case-sdd-check.mjs [--draft] <NAME>.md"); process.exit(2); }
if (!existsSync(path)) { console.log(`FAIL: ${path} not found`); process.exit(1); }
const text = readFileSync(path, "utf8").replace(/\r/g, "");
const fails = [];
const has = (h) => new RegExp(`^${h.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*$`, "m").test(text);

if (!/^# SDD — \S/.test(text.trimStart())) fails.push("first line is not '# SDD — <Case Name>'");
if (draftMode) {
  // a draft carries less detail per block, never fewer blocks: the template's sections and one heading per stage
  for (const h of ["## Section 1: Case Definition", "### Case Variables", "## Section 2: Stages & Tasks"]) if (!has(h)) fails.push(`missing heading '${h}'`);
  const n = [...text.matchAll(STAGE)].length;
  if (!n) fails.push("no '### Stage <N>: <Name>' block — each primary stage is its own block, each lane a '### Secondary Stage: <Name>' block");
  if (/^###\s+\d+\.\s/m.test(text)) fails.push("a stage heading reads '### <N>. <Name>' — write '### Stage <N>: <Name>'");
  if (fails.length) { for (const f of fails) console.log(`FAIL: ${f}`); process.exit(1); }
  console.log(`OK (draft): ${n} stage blocks on the template's sections`);
  process.exit(0);
}
for (const h of HEADINGS) if (!has(h)) fails.push(`missing heading '${h}'`);
const FAMILIES = ["Integration Service Connectors", "API Workflows", "Agents", "Processes & RPA", "Child Cases", "External Agents"];
if (has("## Section 4: Integrations") && !FAMILIES.some((f) => has(`### ${f}`)) && !text.includes("> None.")) {
  fails.push(`Section 4 has none of its family headings (${FAMILIES.map((f) => `### ${f}`).join(", ")}) and no '> None.'`);
}

// stage and task blocks
const section3 = text.search(/^## Section 3: Personas & App Views\s*$/m);
const stages = [...text.matchAll(STAGE)];
if (!stages.length) fails.push("no '### Stage <N>:' or '### Secondary Stage:' block");
stages.forEach((s, i) => {
  const end = i + 1 < stages.length ? stages[i + 1].index : section3 > s.index ? section3 : text.length;
  const block = text.slice(s.index, end);
  const name = strip(s[2]);
  if (name.includes(":")) fails.push(`stage name '${name}' holds a ':'`);
  for (const m of STAGE_MARKERS) if (!block.includes(m)) fails.push(`stage '${name}': missing ${m}`);
  const tasks = [...block.matchAll(TASK)];
  if (!tasks.length) fails.push(`stage '${name}': no '##### Task <S>.<T>: <Name>' block`);
  tasks.forEach((t, j) => {
    const tb = block.slice(t.index, j + 1 < tasks.length ? tasks[j + 1].index : block.length);
    const tn = strip(t[1]);
    if (tn.includes(":")) fails.push(`task name '${tn}' holds a ':'`);
    for (const m of TASK_MARKERS) if (!tb.includes(m)) fails.push(`task '${tn}': missing ${m}`);
    const ty = tb.match(/^\*\*Type:\*\*\s*`?([a-z-]+)/m)?.[1];
    const detail = ty && DETAIL[ty];
    if (detail && !detail.some((m) => tb.includes(m))) fails.push(`task '${tn}': a ${ty} task needs its type detail block — '###### ${detail[0]}' (case-sdd-template.md), six hashes: a shorter heading splits the task block`);
  });
});

// an action task whose Tasks row names a persona is that persona's work: its Recipient is never `—`
const personas = new Set((text.match(/^### Personas\s*\n([\s\S]*?)(?=^#{2,3} )/m)?.[1] ?? "").split("\n")
  .filter((l) => /^\|/.test(l) && !/^\|\s*-/.test(l)).slice(1).map((l) => l.split("|")[1].trim().replace(/`/g, "")).filter(Boolean));
const personaOf = new Map();
for (const table of text.match(/^\|[^\n]*\bTask Name\b[^\n]*\bPersona\b[^\n]*\|\n(?:\|[^\n]*\|\n?)+/gm) ?? []) {
  const rows = table.trim().split("\n").map((r) => r.split("|").slice(1, -1).map((c) => c.trim()));
  const ni = rows[0].indexOf("Task Name"), pi = rows[0].indexOf("Persona");
  for (const r of rows.slice(2)) if (r[ni] && r[pi]) personaOf.set(strip(r[ni].replace(/`/g, "")), r[pi].replace(/`/g, ""));
}
for (const b of text.split(/^(?=#{3,5} )/m)) {
  const t = b.split("\n")[0].match(/^#####\s+Task\s+S?\d+\.\d+:\s*(.+?)\s*$/);
  if (!t || !/^\*\*Type:\*\*\s*action\b/m.test(b)) continue;
  const p = personaOf.get(strip(t[1]));
  const rc = b.match(/^\*\*Recipient:\*\*\s*(.*?)\s*$/m);
  if (p && personas.has(p) && rc && dash(rc[1])) fails.push(`task '${strip(t[1])}': Persona ${p}, Recipient — (write **Recipient:** Role:${p})`);
}

// § Personas: the template's six columns, Scope Case or Stages, Permissions from the template's key set
{
  const KEYS = new Set(["View", "Create", "Edit", "Close", "Reopen", "Assign", "ManageSLA", "RunAdhocTasks", "SelectStage",
    "ViewSummary", "LogsView", "TasksView", "TasksCreate", "TasksEdit", "TasksDelete", "TaskAssignmentView",
    "TaskAssignmentCreate", "TaskAssignmentEdit", "TaskAssignmentDelete", "TaskSelfAssignmentCreate",
    "TaskSelfAssignmentEdit", "TaskSelfAssignmentDelete"]);
  const STAGE_KEYS = new Set(["View", "Assign", "ManageSLA", "RunAdhocTasks"]);
  const block = text.match(/^### Personas\s*\n([\s\S]*?)(?=^#{2,3} |(?![\s\S]))/m)?.[1] ?? "";
  const lines = block.split("\n").map((l) => l.trim()).filter((l) => l.startsWith("|") && !/^\|[\s|:-]+\|$/.test(l));
  const want = "| Persona | Scope | Stages | Permissions | Description | Notes |";
  if (lines.length && lines[0].replace(/\s+/g, " ") !== want) {
    fails.push(`Personas header is '${lines[0]}' — write the template's '${want}' and re-render every row into its six cells`);
  } else {
    for (const l of lines.slice(1)) {
      const c = l.replace(/^\||\|$/g, "").split("|").map((x) => x.trim());
      const who = c[0]?.replace(/`/g, "") || "?";
      if (c.length !== 6) { fails.push(`persona '${who}': ${c.length} cells, the header 6`); continue; }
      if (c[0].startsWith("<")) continue; // the template's own placeholder row
      if (c[1] !== "Case" && c[1] !== "Stages") fails.push(`persona '${who}': Scope '${c[1]}' — write Case (every stage, Stages —) or Stages`);
      const bad = c[3].split(",").map((k) => k.trim()).filter((k) => k && !dash(k) && !KEYS.has(k));
      if (bad.length) fails.push(`persona '${who}': Permissions ${bad.join(", ")} not a template permission key — task work comes from each task's Recipient, so drop it (Reassign → Assign) and keep the prose in Notes`);
      const wide = c[1] === "Stages" ? c[3].split(",").map((k) => k.trim()).filter((k) => KEYS.has(k) && !STAGE_KEYS.has(k)) : [];
      if (wide.length) fails.push(`persona '${who}': a Stages persona holds only View, Assign, ManageSLA, RunAdhocTasks — not ${wide.join(", ")}`);
    }
  }
}

// action tasks: the HITL cell is `Action App: <title>` and the title is never another task's
{
  const blocks = text.split(/^(?=#{3,5} )/m)
    .map((b) => ({ b, h: b.split("\n")[0].match(/^#####\s+Task\s+S?\d+\.\d+:\s*(.+?)\s*$/) }))
    .filter((x) => x.h)
    .map(({ b, h }) => ({ b, name: strip(h[1]), id: h[1].match(/\(`?(t\d+)`?\)/)?.[1] }));
  const names = new Set(blocks.map((x) => x.name));
  for (const { b, name, id } of blocks) {
    const cell = b.match(/^\*\*HITL Implementation:\*\*\s*(.*?)\s*$/m)?.[1];
    if (cell == null) continue;
    if (!/^Action App:/.test(cell)) { fails.push(`task '${name}': **HITL Implementation:** ${cell} — the only form is 'Action App: <title>', the title from this task's own name`); continue; }
    const title = cell.replace(/^Action App:\s*/, "");
    const ids = [...title.matchAll(/\(`?(t\d+)`?\)/g)].map((m) => m[1]).filter((x) => x !== id);
    const other = strip(title.replace(/\s+Action App\s*$/i, "").replace(/\s*\(`?t\d+`?\)/g, ""));
    if (ids.length || (other !== name && names.has(other))) {
      fails.push(`task '${name}': **HITL Implementation:** names another task's Action App (${title}) — write 'Action App: ${name}'`);
    }
  }
}

// Activation Mode: a Tasks table cell and its task block's **Activation Mode:** line say the same literal
{
  const modeOf = new Map();
  for (const table of text.match(/^\|[^\n]*\bTask Name\b[^\n]*\bActivation Mode\b[^\n]*\|\n(?:\|[^\n]*\|\n?)+/gm) ?? []) {
    const rows = table.trim().split("\n").map((r) => r.split("|").slice(1, -1).map((c) => c.trim().replace(/`/g, "")));
    const ni = rows[0].indexOf("Task Name"), ai = rows[0].indexOf("Activation Mode");
    for (const r of rows.slice(2)) if (r[ni] && r[ai]) modeOf.set(strip(r[ni]), r[ai]);
  }
  for (const b of text.split(/^(?=#{3,5} )/m)) {
    const t = b.split("\n")[0].match(/^#####\s+Task\s+S?\d+\.\d+:\s*(.+?)\s*$/);
    const m = t && b.match(/^\*\*Activation Mode:\*\*\s*`?([^`\s]+)/m);
    if (!m) continue;
    const row = modeOf.get(strip(t[1]));
    const lit = (s) => s.toLowerCase().match(/[a-z-]+/)?.[0] ?? "";
    if (row && lit(row) !== lit(m[1])) fails.push(`task '${strip(t[1])}': Tasks table Activation Mode '${row}', task block '${m[1]}' — one literal in both (a task that starts after another is never parallel)`);
  }
}

// **Type:** values: written bare, no backticks or prose — the build reads the token as written
for (const [, t] of text.matchAll(/^\*\*Type:\*\*\s*(\S+)/gm)) {
  if (t === "Stage" || t === "ExceptionStage" || TASK_TYPES.has(t)) continue;
  const key = t.replace(/[`*]/g, "").toLowerCase().replace(/[\s_]+/g, "-");
  const meant = MEANT[key] ?? (TASK_TYPES.has(key) || key === "stage" ? key : null);
  fails.push(`**Type:** ${t} is not 'Stage' or one of the ${TASK_TYPES.size} task types${meant ? ` — write it bare: **Type:** ${meant === "stage" ? "Stage" : meant}` : " (a secondary stage is **Type:** Stage with **Stage Kind:** secondary)"}`);
}
for (const [, k] of text.matchAll(/^\*\*Stage Kind:\*\*\s*(\S+)/gm)) {
  if (k !== "primary" && k !== "secondary") fails.push(`**Stage Kind:** ${k} — write primary or secondary, bare`);
}
for (const [, title] of text.matchAll(/^\|\s*SLA Title\s*\|\s*([^|]*)\|/gim)) {
  const v = strip(title);
  if (!v || dash(v)) fails.push("an SLA Title cell is empty");
  else if (v.includes(":")) fails.push(`SLA title '${v}' holds a ':'`);
}

// § SLA Response Map
const mapAt = text.search(/^#{2,4}\s+.*SLA Response Map/m);
const calls = [];
for (const line of text.split("\n")) {
  const c = line.match(/sla-status-change\s*\(([^)]*)\)/i);
  if (!c || !line.trim().startsWith("|")) continue;
  const cells = cellsOf(line);
  const yn = [...cells].reverse().find((x) => /^(yes|no)$/i.test(x)) ?? "";
  calls.push({ args: c[1].trim(), interrupting: yn.toLowerCase() });
}
const rows = [];
if (mapAt >= 0) {
  let header = null;
  for (const line of text.slice(mapAt).split("\n").slice(1)) {
    const s = line.trim();
    if (/^#{2,4}\s+\S/.test(s)) break;
    if (!s.startsWith("|") || /^\|[\s|:-]+\|$/.test(s)) continue;
    const cells = cellsOf(s);
    if (!header) {
      header = cells.map((c) => c.toLowerCase());
      const want = ["scope", "sla", "status", "response", "target", "interrupting", "rationale"];
      if (header.join("|") !== want.join("|")) {
        fails.push(`SLA Response Map header is '| ${cells.join(" | ")} |' — write the template's '| Scope | SLA | Status | Response | Target | Interrupting | Rationale |'`);
        break;
      }
      continue;
    }
    if (cells.length !== header.length) { fails.push(`SLA Response Map row '${cells.slice(0, 3).join(" / ")}' has ${cells.length} cells, its header ${header.length}`); continue; }
    const row = Object.fromEntries(header.map((h, i) => [h, cells[i]]));
    if ((row.response ?? "").includes("<")) continue; // the template's own placeholder row
    rows.push(row);
  }
} else if (calls.length || /^#### Stage SLA\s*$/m.test(text) || /^\|\s*Case-Level SLA\s*\|\s*\d/im.test(text)) {
  fails.push("an SLA exists and the SDD has no '### SLA Response Map' table");
}
for (const r of rows) {
  const label = `${r.scope} / ${r.sla} / ${r.status}`;
  const resp = (r.response ?? "").toLowerCase();
  if ([r.sla, r.status, r.response].every((c) => dash(c ?? ""))) {
    fails.push(`SLA Response Map row '${label}': a scope with no SLA gets no row — delete it`);
    continue;
  }
  if (!RESPONSES.has(resp)) { fails.push(`SLA Response Map row '${label}': Response '${r.response}' is not one of ${[...RESPONSES].join(", ")}`); continue; }
  if (!/^(at-risk|breached)$/i.test(r.status ?? "")) fails.push(`SLA Response Map row '${label}': Status is At-Risk or Breached`);
  if (resp === "notify-only") {
    if (!dash(r.target ?? "")) fails.push(`SLA Response Map row '${label}': notify-only takes Target — (who is notified goes in the SLA block's Notify: cell)`);
    if (!dash(r.interrupting ?? "")) fails.push(`SLA Response Map row '${label}': notify-only takes Interrupting —`);
    continue;
  }
  if (dash(r.target ?? "")) fails.push(`SLA Response Map row '${label}': ${resp} names its Target`);
  if (resp === "start-task") {
    if (!dash(r.interrupting ?? "")) fails.push(`SLA Response Map row '${label}': start-task takes Interrupting — (it is the task's own task-entry row, which interrupts nothing; No would mean stage re-entry)`);
  } else if (!/^(yes|no)$/i.test(r.interrupting ?? "")) {
    fails.push(`SLA Response Map row '${label}': ${resp} takes Interrupting Yes or No`);
  }
}
const graph = rows.filter((r) => /^(start-task|enter-stage)$/i.test(r.response ?? ""));
if (graph.length && !calls.length) fails.push(`${graph.length} start-task / enter-stage SLA Response Map row(s) and no sla-status-change(...) entry row in the SDD`);
for (const { args, interrupting } of calls) {
  const [target = "", title = ""] = args.split(",").map((p) => p.trim().replace(/^["']|["']$/g, ""));
  const titled = graph.filter((r) => (r.sla ?? "").trim() === title);
  if (!titled.length) { fails.push(`sla-status-change(${args}): no start-task / enter-stage SLA Response Map row has SLA '${title}'`); continue; }
  const scoped = titled.filter((r) => {
    const sc = strip((r.scope ?? "").replace(/`/g, "")).toLowerCase();
    return target.toLowerCase() === "root" ? /^case(\s*:\s*(root|case))?$/.test(sc) : sc.replace(/^stage\s*:\s*/, "") === target.toLowerCase() && sc.startsWith("stage");
  });
  if (!scoped.length) { fails.push(`sla-status-change(${args}): the map rows for '${title}' are scoped ${titled.map((r) => r.scope).join(", ")} — scope the row to the call's target (root → case, a stage → stage: <name>)`); continue; }
  if (!interrupting) {
    if (scoped.some((r) => /^enter-stage$/i.test(r.response))) fails.push(`the Stage Entry Conditions row for sla-status-change(${args}) has no Yes/No Interrupting cell`);
    continue;
  }
  const declared = scoped.map((r) => (r.interrupting ?? "").toLowerCase());
  if (!declared.includes(interrupting)) fails.push(`sla-status-change(${args}): the entry row says Interrupting ${interrupting}, the SLA Response Map ${declared.join("/")}`);
}

// SLA durations and Variable SLA Rules rows: a conditional row carries its expression (and, on a stage, a title)
{
  let mode = null, titles = new Set();
  const duration = (n, unit, at) => {
    const c = Number(n);
    if (Number.isNaN(c)) return;
    if (c <= 0) fails.push(`${at}: an SLA count is positive`);
    if (unit.trim().toLowerCase() === "min" && (c < 15 || c > 1000)) fails.push(`${at}: an SLA in minutes lies within 15–1000`);
  };
  text.split("\n").forEach((line, i) => {
    const s = line.trim(), at = `line ${i + 1}`;
    if (s === "#### Stage SLA") { mode = "stage-sla"; return; }
    if (s === "### Variable SLA Rules") { mode = "var"; titles = new Set(); return; }
    if (s === "##### Stage Variable SLA Rules") { mode = "stage-var"; titles = new Set(); return; }
    if (s.startsWith("#")) { mode = null; return; }
    const cs = s.match(/^\|\s*Case-Level SLA\s*\|\s*([0-9]+(?:\.[0-9]+)?)\s+([A-Za-z]+)/i);
    if (cs) duration(cs[1], cs[2], at);
    if (!s.startsWith("|")) return;
    const c = s.replace(/^\||\|$/g, "").split("|").map((x) => x.trim());
    if (mode === "stage-sla" && c.length >= 2 && /^\d+(\.\d+)?$/.test(c[0])) duration(c[0], c[1], at);
    if ((mode === "var" || mode === "stage-var") && c.length >= 3 && /^\d+(\.\d+)?$/.test(c[1])) {
      duration(c[1], c[2], at);
      if (dash(c[0].replace(/^["']|["']$/g, ""))) fails.push(`${at}: a Variable SLA Rules row has no expression — a time-based SLA has no such row: delete it (the table reads '> None.')`);
      if (mode === "stage-var") {
        const title = strip((c[3] ?? "").replace(/^["']|["']$/g, ""));
        if (!title || dash(title)) fails.push(`${at}: a Stage Variable SLA Rules row has no Display Name`);
        else if (titles.has(title)) fails.push(`${at}: Display Name '${title}' repeats in its table`);
        else titles.add(title);
        if (title.includes(":")) fails.push(`${at}: Display Name '${title}' holds a ':'`);
      }
    }
  });
}

// § Case Variables: every =vars.<name> is declared, and every consumed variable is produced
const declared = new Map();
for (const m of text.matchAll(/^\|\s*`?([A-Za-z]\w*)`?\s*\|\s*(In|Out|Variable)\s*\|\s*[^|]*\|\s*([^|]*?)\s*\|\s*[^|]*\|\s*([^|]*?)\s*\|/gm)) {
  declared.set(m[1], { cat: m[2], trig: m[3].trim(), def: m[4].trim() });
}
if (!declared.size) fails.push("no § Case Variables rows '| <name> | In / Out / Variable | <type> | <source trigger> | <source field> | <default> | <description> |'");
const refs = new Set([...text.matchAll(/=vars\.([A-Za-z]\w*)/g)].map((m) => m[1]));
refs.delete("X");
const undeclared = [...refs].filter((r) => !declared.has(r)).sort();
if (declared.size && undeclared.length) fails.push(`=vars not declared in § Case Variables: ${undeclared.join(", ")} — add each row, or point the expression at the declared name`);
const produced = new Set([...text.matchAll(/->\s*([A-Za-z]\w*)/g), ...text.matchAll(/\b([A-Za-z]\w*)\s*=\s*(?!=)/g)].map((m) => m[1]));
const unproduced = [...refs].filter((r) => { const v = declared.get(r); return v && v.cat !== "In" && !v.def && !v.trig && !produced.has(r); }).sort();
if (unproduced.length) fails.push(`variable(s) consumed but never produced: ${unproduced.join(", ")} — give each a source trigger, a default, or a task output '-> <name>'`);

// gates: each WHEN is legal for its table; secondary stages interrupt; the case can complete
let gate = null, cur = null, marksIdx = -1, etIdx = -1;
const stageInfo = new Map();
for (const line of text.split("\n")) {
  const s = line.trim();
  const st = s.match(/^###\s+(Stage \d+|Exception Stage|Secondary Stage):\s*(.*)/);
  if (st) { cur = st[2].replace(/\(.*/, "").trim(); stageInfo.set(cur, { sec: !st[1].startsWith("Stage"), exits: new Set(), interrupting: null, rtc: new Set() }); gate = null; continue; }
  if (/^\*\*Stage Kind:\*\*\s*`?secondary/i.test(s) && cur) { stageInfo.get(cur).sec = true; continue; }
  if (s.startsWith("### Case Exit Conditions")) { gate = "case-exit"; continue; }
  if (s.startsWith("####") && s.includes("Entry Conditions")) { gate = "stage-entry"; continue; }
  if (s.startsWith("####") && s.includes("Exit Conditions")) { gate = "stage-exit"; continue; }
  if (s.startsWith("**Entry Condition")) { gate = "task-entry"; continue; }
  const im = s.match(/^\*\*Interrupting:\*\*\s*(Yes|No)/);
  if (im) { if (cur) stageInfo.get(cur).interrupting = im[1]; gate = null; continue; }
  if (s.startsWith("#") || s === "---" || s.startsWith("**")) { gate = null; continue; }
  if (!gate || !s.startsWith("|")) continue;
  const cells = s.replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
  if (cells[0] === "WHEN") {
    const h = cells.map((c) => c.toLowerCase());
    marksIdx = h.findIndex((x) => x.startsWith("marks"));
    etIdx = h.findIndex((x) => x.includes("exit type"));
    continue;
  }
  if (!cells[0] || /^[-: ]+$/.test(cells[0])) continue;
  const rule = cells[0].match(/^`?\s*([a-z][a-z]+(?:-[a-z]+)*)/)?.[1];
  if (!rule) continue;
  const where = cur ?? "case";
  let g = gate;
  if (gate === "stage-exit" || gate === "case-exit") {
    const marks = (marksIdx >= 0 && marksIdx < cells.length ? cells[marksIdx] : cells.at(-1)).toLowerCase().startsWith("yes");
    if (marks) g = gate === "stage-exit" ? "stage-complete" : "case-complete";
    if (gate === "stage-exit") {
      const et = etIdx >= 0 && etIdx < cells.length ? cells[etIdx] : cells.length >= 4 ? cells.at(-2) : null;
      if (et != null && cur) stageInfo.get(cur).exits.add(et);
      if (marks && rule === "required-tasks-completed" && cur) {
        const cond = (cells[1] ?? "").replace(/^[—-]$/, "");
        const seen = stageInfo.get(cur).rtc;
        if (seen.has(cond)) fails.push(`${where}: two required-tasks-completed rows with the same IF mark the stage complete — keep one and change its Exit Type (e.g. to wait-for-user) instead of adding a second`);
        seen.add(cond);
      }
      if (et && !["exit-only", "wait-for-user", "return-to-origin"].includes(et)) fails.push(`${where}: exit type '${et}' is none of exit-only, wait-for-user, return-to-origin`);
      if (et === "return-to-origin" && !(marks && ["required-tasks-completed", "wait-for-connector"].includes(rule))) fails.push(`${where}: a return-to-origin exit is required-tasks-completed or wait-for-connector with Marks Stage Complete Yes`);
    }
  }
  if (!GATE[g].includes(rule)) fails.push(`${where}: '${rule}' is not a legal ${g.replace("-", " ")} rule — legal: ${GATE[g].join(", ")}`);
}
for (const [name, info] of stageInfo) {
  if (!info.sec) continue;
  if (!info.interrupting) fails.push(`secondary stage '${name}': no '**Interrupting:** Yes' line under its heading`);
  else if (info.exits.has("return-to-origin") && info.interrupting !== "Yes") fails.push(`secondary stage '${name}' returns to its origin, so it is '**Interrupting:** Yes'`);
}
if (!text.includes("required-stages-completed")) fails.push("no required-stages-completed row in § Case Exit Conditions — the case can never complete");

if (fails.length) {
  for (const f of fails) console.log(`FAIL: ${f}`);
  process.exit(1);
}
console.log(`OK: ${stages.length} stages, template markers present, task types valid, ${rows.length} SLA Response Map rows closed both ways`);
