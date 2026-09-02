#!/usr/bin/env node
/**
 * Deterministic grammar audit for the compact no-build plan (tasks/tasks.md).
 *
 * Usage:
 *     node audit-plan.mjs <tasks/tasks.md> [--sdd <sdd.md>]
 *
 * Read-only. Exit 0 = grammar-clean. Exit 1 = numbered findings on stderr;
 * repair the plan with Write/Edit and re-run until clean. Enforces the compact
 * `tasks/tasks.md` contract (planning.md § Compact no-build T-entry shape): `## T{N}: task "{Task Name}"` headings, one
 * `field: value` per line, legal `activation-mode` / `entry-rule` pairs, lanes on
 * sequential runs, no registry-derived keys.
 * `--sdd` additionally checks every `sla-status-change(...)` reference in the
 * SDD for the 2-arg (breach) / 3-arg (at-risk) quoted shape.
 *
 * Node is the runtime the skill can rely on: `uip` is an npm-installed Node
 * CLI, so if `uip` runs, this runs. Node is the runtime the skill can rely on: `uip` is an npm-installed
 * Node CLI, so if `uip` runs, this runs. `python3` carries no such guarantee
 * (on Windows it is frequently a Store alias stub).
 */

import { readFileSync } from "node:fs";
import { basename } from "node:path";
import process from "node:process";

const DOC = `Deterministic grammar audit for the compact no-build plan (tasks/tasks.md).

Usage:
    node audit-plan.mjs <tasks/tasks.md> [--sdd <sdd.md>]

Read-only. Exit 0 = grammar-clean. Exit 1 = numbered findings on stderr;
repair the plan with Write/Edit and re-run until clean. Enforces the compact
\`tasks/tasks.md\` contract (planning.md § Compact no-build T-entry shape): \`## T{N}: task "{Task Name}"\` headings, one
\`field: value\` per line, legal \`activation-mode\` / \`entry-rule\` pairs, lanes on
sequential runs, no registry-derived keys.
\`--sdd\` additionally checks every \`sla-status-change(...)\` reference in the
SDD for the 2-arg (breach) / 3-arg (at-risk) quoted shape.`;

const TASK_FIELDS = [
  "stage", "type", "activation-mode", "entry-rule", "lane", "required",
  "run-only-once", "resource-intent", "identity", "rationale",
];
// `lane` is only mandatory for sequential runs; checked separately.
const ALWAYS_REQUIRED = TASK_FIELDS.filter((f) => f !== "lane");

// Compact form (`## T{N}: task "Name"`) or canonical full-form build title
// (`## T{N}: Add <type> task "Name" to "Stage"`) — both are addressable.
const TASK_HEADING = /^## T\d+: (?:task "[^"\n]+"|Add [a-z][a-z-]* task "[^"\n]+" to "[^"\n]+")\s*$/;
const FORBIDDEN_KEYS = ["taskTypeId", "activityTypeId", "connectionId", "registry-resolved", "recipients-resolved"];

// planning.md § Activation-mode audit — the six user-visible task modes plus
// `parallel-after-predecessor`.
const ACTIVATION_MODES = new Set([
  "sequential", "parallel", "parallel-after-predecessor",
  "event-triggered", "adhoc", "fan-in", "conditional-gate",
]);
// plugins/conditions/task-entry-conditions/planning.md § activation-mode /
// rule-type table, keyed by rule. Rules outside this map are explicitly
// authored event/condition rules and pair with any mode that permits them.
const ENTRY_RULE_MODES = new Map([
  ["runs-sequentially", new Set(["sequential", "parallel-after-predecessor"])],
  ["current-stage-entered", new Set(["parallel"])],
  ["adhoc", new Set(["adhoc"])],
  ["selected-tasks-completed", new Set(["fan-in", "conditional-gate"])],
  ["wait-for-connector", new Set(["event-triggered"])],
]);

/** Mirror of Python's `re.escape` for the subset we need. */
const reEscape = (s) => s.replace(/[.*+?^${}()|[\]\\-]/g, "\\$&");

/** Mirror of Python's `repr()` for a plain string: single quotes, escaped. */
function pyRepr(s) {
  const inner = String(s).replace(/\\/g, "\\\\").replace(/\n/g, "\\n").replace(/\t/g, "\\t");
  return inner.includes("'") && !inner.includes('"')
    ? `"${inner}"`
    : `'${inner.replace(/'/g, "\\'")}'`;
}

/** Mirror of Python's `repr()` for a tuple of strings. */
const pyTupleRepr = (arr) =>
  arr.length === 1 ? `(${pyRepr(arr[0])},)` : `(${arr.map(pyRepr).join(", ")})`;

const sortedArr = (iterable) => [...iterable].sort();

/** Strip the characters Python's `.strip('`"\\' ')` removes, both ends. */
const stripQuotes = (s) => s.replace(/^[`"' ]+/, "").replace(/[`"' ]+$/, "");

function fieldValue(section, field) {
  const re = new RegExp(`^[ \\t]*[-*]?[ \\t]*${reEscape(field)}[ \\t]*:[ \\t]*(.+)$`, "im");
  const m = section.match(re);
  return m ? m[1].trim() : null;
}

/** Leading canonical identifier, dropping any `("selector")` and trailing prose. */
function ruleToken(value) {
  const m = stripQuotes((value ?? "").trim()).toLowerCase().match(/^[a-z][a-z0-9-]*/);
  return m ? m[0] : null;
}

const countNewlines = (s) => (s.match(/\n/g) || []).length;

function audit(path) {
  const findings = [];
  const sequentialLanes = new Map();
  const text = readFileSync(path, "utf-8");

  const headings = [...text.matchAll(/^## (T\d+)[^\n]*$/gm)];
  if (headings.length === 0) {
    findings.push("no `## T{N}:` entries found — the compact plan uses T-numbered H2 entries");
    return findings;
  }

  for (const key of FORBIDDEN_KEYS) {
    if (text.includes(key)) {
      findings.push(`forbidden key ${pyRepr(key)} — the no-build plan omits registry-derived data`);
    }
  }

  for (let index = 0; index < headings.length; index += 1) {
    const heading = headings[index];
    const start = heading.index;
    const end = index + 1 < headings.length ? headings[index + 1].index : text.length;
    const section = text.slice(start, end);
    const headLine = section.split("\n")[0];
    const label = heading[1];

    const isTaskEntry = TASK_HEADING.test(headLine);
    const looksLikeTask =
      (fieldValue(section, "stage") !== null && fieldValue(section, "activation-mode") !== null) ||
      /\btask\b[^\n]*"/i.test(headLine);

    if (!isTaskEntry && looksLikeTask) {
      findings.push(
        `${label}: task heading must be \`## ${label}: task "{Task Name}"\` or the canonical ` +
          `\`## ${label}: Add <type> task "{Task Name}" to "{Stage}"\` (got: ${pyRepr(headLine)})`,
      );
    }

    if (!(isTaskEntry || looksLikeTask)) continue;

    // One `field: value` per line; semicolon-packed lines hide fields.
    for (const field of ALWAYS_REQUIRED) {
      if (fieldValue(section, field) === null) {
        let hint = "";
        if (new RegExp(`[;,][ \\t]*${reEscape(field)}[ \\t]*:`, "i").test(section)) {
          hint = " (present mid-line — each field goes on its own line)";
        }
        findings.push(`${label}: missing \`${field}:\` line${hint}`);
      }
    }

    const activation = (fieldValue(section, "activation-mode") ?? "").toLowerCase();
    const mode = ruleToken(activation);
    const rule = ruleToken(fieldValue(section, "entry-rule"));
    if (mode !== null && !ACTIVATION_MODES.has(mode)) {
      findings.push(
        `${label}: \`activation-mode: ${mode}\` is not a task mode; use one of ` +
          `${sortedArr(ACTIVATION_MODES).join(", ")}`,
      );
    } else if (mode !== null && rule !== null && ENTRY_RULE_MODES.has(rule)) {
      const allowed = ENTRY_RULE_MODES.get(rule);
      if (!allowed.has(mode)) {
        findings.push(
          `${label}: \`activation-mode: ${mode}\` cannot carry \`entry-rule: ${rule}\` — ` +
            `that rule pairs with ${sortedArr(allowed).join(" or ")} ` +
            `(list position never normalizes an authored rule into another mode)`,
        );
      }
    }
    const lane = fieldValue(section, "lane");
    if (activation.includes("sequential") && (lane === null || !/^\d+$/.test(lane))) {
      findings.push(`${label}: sequential task needs an integer \`lane:\` line`);
    } else if (activation.includes("sequential") && lane !== null) {
      const stage = stripQuotes(fieldValue(section, "stage") ?? "");
      if (!sequentialLanes.has(stage)) sequentialLanes.set(stage, []);
      sequentialLanes.get(stage).push([label, Number.parseInt(lane, 10)]);
    }
  }

  // Sequential runs use consecutive single-task lanes: no duplicates, no gaps.
  for (const [stage, lanes] of sequentialLanes) {
    const numbers = lanes.map(([, n]) => n);
    const lo = Math.min(...numbers);
    const want = Array.from({ length: numbers.length }, (_, i) => lo + i);
    const got = [...numbers].sort((a, b) => a - b);
    if (got.join(",") !== want.join(",")) {
      const labels = lanes.map(([t, n]) => `${t}=lane ${n}`).join(", ");
      findings.push(
        `stage ${pyRepr(stage)}: sequential lanes must be consecutive single-task numbers with no duplicates; got ${labels}`,
      );
    }
  }

  findings.push(...slaShapeFindings(text, basename(path)));
  return findings;
}

/**
 * sla-status-change references need 2 quoted args (breach) or 3 (at-risk).
 * Zero-quoted-arg mentions are summary/prose shorthand and are not flagged.
 */
function slaShapeFindings(text, source) {
  const findings = [];
  // Every `#### Stage SLA` block declares its title on its own line —
  // a collapsed `**SLA Type:** … **SLA Title:** …` line hides the title
  // from line-start tooling and reference resolution.
  for (const match of text.matchAll(/^####[ \t]+Stage SLA[ \t]*$/gim)) {
    const after = text.slice(match.index + match[0].length);
    const blockEnd = after.match(/^#{1,4}\s/m);
    const block = blockEnd ? after.slice(0, blockEnd.index) : after;
    if (!/^\*\*SLA Title:\*\*[ \t]*\S/im.test(block)) {
      const lineNo = countNewlines(text.slice(0, match.index)) + 1;
      findings.push(
        `${source}:${lineNo}: '#### Stage SLA' block has no line-start '**SLA Title:**' — ` +
          "render '**SLA Type:**' and '**SLA Title:**' as two separate lines",
      );
    }
  }
  const lines = text.split("\n");
  for (let i = 0; i < lines.length; i += 1) {
    for (const call of lines[i].matchAll(/sla-status-change\s*\(([^)]*)\)/gi)) {
      const args = [...call[1].matchAll(/["“‘']([^"”’']+)["”’']/g)].map((m) => m[1]);
      if (args.length && args.length !== 2 && args.length !== 3) {
        findings.push(
          `${source}:${i + 1}: sla-status-change reference needs 2 (breach) ` +
            `or 3 (at-risk) quoted args; got ${args.length}`,
        );
      }
      if (args.length && args[0].trim().toLowerCase() === "case") {
        findings.push(
          `${source}:${i + 1}: sla-status-change target 'Case' — the case-level target is the literal 'root'`,
        );
      }
    }
  }
  return findings;
}

/**
 * Every quoted-arg sla-status-change entry declared in the SDD is repeated
 * verbatim in the plan (compact-contract requirement) — target + each title.
 */
function planRepeatsSddSlaRules(plan, sdd) {
  const findings = [];
  const declared = [];
  for (const call of sdd.matchAll(/sla-status-change\s*\(([^)]*)\)/gi)) {
    const args = [...call[1].matchAll(/["“‘']([^"”’']+)["”’']/g)].map((m) => m[1]);
    if (args.length && !declared.some((d) => JSON.stringify(d) === JSON.stringify(args))) {
      declared.push(args);
    }
  }
  if (declared.length === 0) return findings;
  const lowered = plan.toLowerCase();
  if (!lowered.includes("sla-status-change")) {
    findings.push(
      "the SDD declares sla-status-change entry rules but the plan carries none — " +
        "each gets its own T-entry with rule-type: sla-status-change, repeating target and titles verbatim",
    );
    return findings;
  }
  for (const args of declared) {
    const missing = args.filter((a) => !lowered.includes(a.toLowerCase()));
    if (missing.length) {
      findings.push(
        `plan does not repeat the SDD sla-status-change entry ${pyTupleRepr(args)} verbatim — missing: ${missing.join(", ")}`,
      );
    }
  }
  return findings;
}

function main() {
  const args = process.argv.slice(2);
  let sdd = null;
  const i = args.indexOf("--sdd");
  if (i !== -1) {
    sdd = args[i + 1];
    args.splice(i, 2);
  }
  if (args.length !== 1) {
    process.stderr.write(`${DOC}\n`);
    process.exit(1);
  }
  const findings = audit(args[0]);
  if (sdd !== null) {
    const sddText = readFileSync(sdd, "utf-8");
    findings.push(...slaShapeFindings(sddText, basename(sdd)));
    findings.push(...planRepeatsSddSlaRules(readFileSync(args[0], "utf-8"), sddText));
  }
  if (findings.length) {
    const shown = findings.slice(0, 40);
    process.stderr.write("AUDIT FAIL — repair these, then re-run:\n");
    shown.forEach((f, n) => process.stderr.write(`  ${n + 1}. ${f}\n`));
    if (findings.length > shown.length) {
      process.stderr.write(`  … and ${findings.length - shown.length} more\n`);
    }
    process.exit(1);
  }
  process.stdout.write("AUDIT OK: tasks.md grammar is clean\n");
}

main();
