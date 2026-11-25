#!/usr/bin/env node
// Mechanical check of a written Case Management SDD (assets/templates/case-sdd-template.md), run before the
// Conformance Checklist walk (references/design/sdd-writing-guide.md Step 2 item 8) and after a draft finalization
// (references/design/case-review-and-conformance-guide.md § Finalizing a Case Draft).
//
// Usage: node case-sdd-check.mjs <NAME>.md          a final SDD, or one written without a draft
//        node case-sdd-check.mjs --draft <NAME>.draft.md   a draft: the title, Sections 1-2 and one block per stage only
// Exit 0 and "OK" when: the first line is `# SDD — <Case Name>`; the template's required headings exist; every
// stage block holds **Type:**, **Design Rationale:**, Entry and Exit Conditions and a Tasks table; every task block
// holds **Type:**, **Activation Mode:**, **Design Rationale:**, **Entry Condition:** and **Task envelope**; every
// **Type:** is `Stage` or one of the 17 task types, written bare; **Stage Kind:** is primary or secondary; no stage,
// task or SLA title holds a ':'; every § SLA Response Map row follows the template's cell rules and closes both ways
// with the SDD's `sla-status-change(...)` rows. Exit 1 with one FAIL line per defect.
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

if (fails.length) {
  for (const f of fails) console.log(`FAIL: ${f}`);
  process.exit(1);
}
console.log(`OK: ${stages.length} stages, template markers present, task types valid, ${rows.length} SLA Response Map rows closed both ways`);
