#!/usr/bin/env node
// Checks a Maestro BPMN, Maestro Flow or RPA SDD against its own tables.
// Usage: node check-sdd.mjs "<SDD_MD>" [--ready]
// Exit 0: no finding. Exit 1: one `FAIL:` line per finding. Exit 2: usage error.
// The handoff `Status` row follows the result: a finding sets it back to `draft`; `--ready` with
// no finding sets it to `ready`. A Maestro BPMN, Maestro Flow or RPA SDD gets `ready` no other way.
// It reads only the SDD: every finding is a place where two of its tables disagree.
//   rules-project   a decision table has no Business Rules Projects row, a rules project holds more
//                   than one table, or a rules project is missing from Solution / Project Breakdown
//   rule-caller     (BPMN) a decision table runs in a step that is not a Rule step, or one Rule
//                   step evaluates more than one rules project
//   error-catch     (BPMN) an Error Handling row names a node the SDD does not have, carries on
//                   after a failure nothing catches, or names a catching event that is not a boundary
//                   error event on that node or on the subprocess holding it
//   flow-condition  (BPMN) a default branch, or a flow at a per-item subprocess, carries a condition
//   unknown-node    (BPMN) a sequence flow or a gateway names a node no table declares
//   loop-nodes      (BPMN) a subprocess lists a node the inventory, gateways and events tables do not have
//   loop-boundary   (BPMN) a sequence flow joins a node inside a multi-instance subprocess to a node
//                   outside it, instead of entering and leaving through the subprocess itself, or joins
//                   the subprocess to one of its own nodes
//   extraction-scope  an extraction model's Purpose has it sort documents by kind
//   rpa-scaffold    (RPA) Project Structure draws the scaffold: an entry point, a framework file, the config file
//   rpa-runs        (RPA) a Workflow Inventory row does not say when it runs
//   one-kind        (Flow) a Nodes Inventory row names more than one step kind
import { readFileSync, writeFileSync } from 'node:fs';

const file = process.argv.slice(2).find(argument => !argument.startsWith('--'));
const flipToReady = process.argv.includes('--ready');
if (!file) {
    console.error('usage: node check-sdd.mjs "<SDD_MD>" [--ready]');
    process.exit(2);
}
let text;
try {
    text = readFileSync(file, 'utf8');
} catch (error) {
    console.error(`cannot read ${file}: ${error.message}`);
    process.exit(2);
}
const lines = text.split(/\r?\n/);

/** Lines of the section opened by a heading matching `pattern`, up to the next heading of that level or higher. */
function section(pattern) {
    const start = lines.findIndex(line => /^#{2,4} /.test(line) && pattern.test(line));
    if (start < 0) return [];
    const level = lines[start].match(/^#+/)[0].length;
    let end = start + 1;
    while (end < lines.length && !(/^#{2,4} /.test(lines[end]) && lines[end].match(/^#+/)[0].length <= level)) end++;
    return lines.slice(start + 1, end);
}

/** Rows of the first markdown table in `body`, as objects keyed by header text. */
function table(body) {
    const start = body.findIndex(line => /^\s*\|/.test(line));
    if (start < 0) return [];
    let end = start;
    while (end < body.length && /^\s*\|/.test(body[end])) end++;
    const rows = body.slice(start, end);
    if (rows.length < 2) return [];
    const cells = line => line.trim().replace(/^\||\|$/g, '').split('|').map(cell => cell.trim());
    const headers = cells(rows[0]);
    return rows.slice(2).map(line => Object.fromEntries(cells(line).map((cell, index) => [headers[index] ?? index, cell])));
}

const keys = cell => [...(cell ?? '').matchAll(/`([^`]+)`/g)].map(match => match[1]).filter(key => /[A-Za-z0-9]/.test(key));
const firstKey = cell => keys(cell)[0];
/** A name cell's value, backticked or not; undefined for an empty or placeholder cell. */
const nameOf = cell => firstKey(cell) ?? (/[A-Za-z0-9]/.test(cell ?? '') ? cell.trim() : undefined);
const findings = [];
const fail = (rule, message) => findings.push(`FAIL: [${rule}] ${message}`);

const isBpmn = lines.some(line => /^## \d+\. Activities Inventory/.test(line));
const breakdown = section(/Solution \/ Project Breakdown/).join('\n');
const rulesRows = table(section(/^### Business Rules Projects/));

// rules-project
const tablesPerProject = new Map();
for (const row of rulesRows) {
    const project = nameOf(row['Rules Project']);
    if (!project) continue;
    tablesPerProject.set(project, (tablesPerProject.get(project) ?? 0) + 1);
    if (!breakdown.includes(project)) fail('rules-project', `rules project \`${project}\` is not a row of Solution / Project Breakdown`);
}
for (const [project, count] of tablesPerProject) {
    if (count > 1) fail('rules-project', `rules project \`${project}\` holds ${count} decision tables; each table is a project of its own`);
}
for (const row of rulesRows) {
    const named = (row['Decision Table'] ?? '').match(/DT\d+/g) ?? [];
    if (named.length > 1) fail('rules-project', `one Business Rules Projects row names ${named.join(', ')}; each table is a row and a project of its own`);
}

// extraction-scope
for (const row of table(section(/^### IXP \/ Document Understanding Models/))) {
    const model = nameOf(row['Model / Project']);
    if (model && /\bclassif|\bsorts?\b|\btriage/i.test(row.Purpose ?? '')) {
        fail('extraction-scope', `extraction model \`${model}\` is said to classify documents; the model extracts fields, and sorting documents by kind is a step of its own`);
    }
}

const isRpa = lines.some(line => /^### Workflow Inventory/.test(line));
const isFlow = lines.some(line => /^## \d+\. Nodes Inventory/.test(line));

if (isRpa) {
    // rpa-scaffold / rpa-runs
    const structure = section(/^## \d+\. Project Structure/).join('\n');
    const drawn = structure.match(/\bMain\.(xaml|cs)\b|\bFramework[\\/]|\b(InitAllSettings|GetTransactionData|SetTransactionStatus)\b|\bConfig\.(xlsx|json)\b/);
    if (drawn) fail('rpa-scaffold', `Project Structure names \`${drawn[0]}\`; the scaffold, its framework files and how the entry point reaches the business workflows are uipath-rpa's, never drawn here`);
    const runs = /^\s*(once, before the items|per item|once, after the items|own entry point)\s*$/i;
    for (const row of table(section(/^### Workflow Inventory/))) {
        const workflow = nameOf(row['Workflow File']);
        if (workflow && !runs.test(row.Runs ?? '')) fail('rpa-runs', `workflow \`${workflow}\` does not say when it runs; Runs is one of \`once, before the items\`, \`per item\`, \`once, after the items\`, \`own entry point\``);
    }
} else if (isBpmn) {
    const inventory = table(section(/^## \d+\. Activities Inventory/));
    const typeOf = new Map(inventory.map(row => [firstKey(row['Node Key']), row['Step Kind'] ?? row['BPMN Element Type'] ?? '']));
    const isRule = kind => /^\s*(rule|businessRuleTask)\s*$/i.test(kind);
    const gateways = new Set(table(section(/^### Gateways/)).map(row => firstKey(row['Gateway Key'])));
    const eventRows = table(section(/^## \d+\. Events/));
    const events = new Set(eventRows.map(row => firstKey(row['Event Key'])));
    const subprocessRows = table(section(/^### Subprocesses/));

    for (const [node, type] of typeOf) {
        if (isRule(type) && !rulesRows.some(row => keys(row['Called From Node']).includes(node))) {
            fail('rules-project', `Rule step \`${node}\` has no row in Business Rules Projects; it evaluates a deployed rules project`);
        }
    }

    const projectsPerTask = new Map();
    for (const row of rulesRows) {
        for (const node of keys(row['Called From Node'])) projectsPerTask.set(node, (projectsPerTask.get(node) ?? 0) + 1);
    }
    for (const [node, count] of projectsPerTask) {
        if (count > 1) fail('rule-caller', `\`${node}\` evaluates ${count} rules projects; one Rule step evaluates one decision table`);
    }

    // error-catch
    for (const row of table(section(/^## \d+\. Error Handling/))) {
        if (!('Failing Node' in row)) break;
        const node = firstKey(row['Failing Node']);
        if (!node) continue;
        if (!typeOf.has(node)) {
            fail('error-catch', `Error Handling names \`${node}\`, which is not an Activities Inventory node; each row names one node`);
            continue;
        }
        const catcher = firstKey(row['Caught By']);
        const next = firstKey(row.Then);
        if (next && !typeOf.has(next) && !gateways.has(next) && !events.has(next)) {
            fail('error-catch', `after a failure of \`${node}\` the run continues at \`${next}\`, which is not an Activities Inventory node, a gateway or an event`);
        }
        if (!catcher) {
            if (!next && !/ends as failed/i.test(row.Then ?? '')) fail('error-catch', `nothing catches a failure of \`${node}\`, so the run ends as failed and Then says exactly \`run ends as failed\`; for the run to carry on, name the boundary error event in Caught By`);
            if (next) fail('error-catch', `a failure of \`${node}\` continues at \`${next}\` but nothing catches it; name the boundary error event on \`${node}\` in Caught By and list it in Events, or let the run end as failed`);
            continue;
        }
        if (!next) fail('error-catch', `a failure of \`${node}\` is caught by \`${catcher}\`, but Then names no node; name the node that event leads to`);
        const event = eventRows.find(candidate => firstKey(candidate['Event Key']) === catcher);
        const holderRows = subprocessRows.filter(candidate => keys(candidate['Nodes Inside']).includes(node));
        const holders = holderRows.map(candidate => firstKey(candidate['Subprocess Key']));
        const attachedTo = event && firstKey(event['Attached To (boundary)']);
        if (!event || !/boundary/i.test(event['Event Kind'] ?? '') || !/error/i.test(event.Definition ?? '') || !(attachedTo === node || holders.includes(attachedTo))) {
            fail('error-catch', `a failure of \`${node}\` is caught by \`${catcher}\`, which Events does not list as a boundary error event attached to \`${node}\` or to the subprocess holding it`);
            continue;
        }
        if (!/^\s*yes/i.test(event['Interrupting?'] ?? '')) {
            fail('error-catch', `\`${catcher}\` is not interrupting, yet the run continues at \`${next}\` after it; an event the run carries on from is interrupting`);
        }
        const loop = holderRows.find(candidate => /^\s*yes/i.test(candidate['Multi-instance?'] ?? ''));
        if (loop && next && (attachedTo !== node || !keys(loop['Nodes Inside']).includes(next))) {
            fail('error-catch', `\`${node}\` runs per item inside \`${firstKey(loop['Subprocess Key'])}\`; for the other items to carry on, \`${catcher}\` sits on \`${node}\` itself and leads to a node inside the same loop`);
        }
    }

    // rules-project / rule-caller, from the decision tables themselves
    const decisions = section(/^### Decision Tables/);
    let current = null;
    for (const line of decisions) {
        const heading = line.match(/^#### (DT\d+)/);
        if (heading) {
            current = heading[1];
            if (!rulesRows.some(row => new RegExp(`\\b${current}\\b`).test(row['Decision Table'] ?? ''))) {
                fail('rules-project', `${current} has no row in Business Rules Projects`);
            }
            continue;
        }
        const runsIn = current && line.match(/\*\*Runs in:\*\*\s*`([^`]+)`/);
        if (runsIn && typeOf.has(runsIn[1]) && !isRule(typeOf.get(runsIn[1]))) {
            fail('rule-caller', `${current} runs in \`${runsIn[1]}\`, a ${typeOf.get(runsIn[1])} step; a decision table runs in a Rule step`);
        }
    }

    // loop-nodes / loop-boundary: the gateways table's own incoming and outgoing nodes count as flows
    const gatewayRows = table(section(/^### Gateways/));
    const sequenceFlows = table(section(/^### Sequence Flows/));
    const flowKeys = new Set(sequenceFlows.map(row => firstKey(row['Flow Key'])));
    const nodesOf = cell => keys(cell).filter(key => !flowKeys.has(key));
    const flows = [
        ...sequenceFlows,
        ...gatewayRows.flatMap(row => [
            ...nodesOf(row.Incoming).map(node => ({ Source: `\`${node}\``, Target: row['Gateway Key'] })),
            ...nodesOf(row.Outgoing).map(node => ({ Source: row['Gateway Key'], Target: `\`${node}\`` })),
        ]),
    ];
    // flow-condition: a default branch and a flow at a per-item subprocess carry no condition
    const conditionOf = flow => (flow.Condition ?? flow['Condition Expression'] ?? '').trim();
    const hasCondition = flow => /[A-Za-z0-9]/.test(conditionOf(flow));
    const loopKeys = new Set(subprocessRows.filter(row => /^\s*yes/i.test(row['Multi-instance?'] ?? '')).map(row => firstKey(row['Subprocess Key'])));
    for (const flow of sequenceFlows) {
        const [source, target] = [firstKey(flow.Source), firstKey(flow.Target)];
        const name = firstKey(flow['Flow Key']) ?? `${source}→${target}`;
        if (hasCondition(flow) && (loopKeys.has(source) || (loopKeys.has(target) && !gateways.has(source)))) {
            fail('flow-condition', `flow \`${name}\` carries a condition at the per-item subprocess \`${loopKeys.has(source) ? source : target}\`; it is left when every item is done`);
        }
        const gateway = gatewayRows.find(row => firstKey(row['Gateway Key']) === source);
        const defaults = gateway ? keys(gateway['Default Flow']) : [];
        if (hasCondition(flow) && (defaults.includes(name) || defaults.includes(target))) {
            fail('flow-condition', `flow \`${name}\` is the default branch of \`${source}\` and carries a condition; the default branch carries none`);
        }
    }
    const known = new Set([...typeOf.keys(), ...gateways, ...events, ...subprocessRows.map(row => firstKey(row['Subprocess Key']))]);
    for (const flow of flows) {
        for (const end of [firstKey(flow.Source), firstKey(flow.Target)]) {
            if (end && !known.has(end)) fail('unknown-node', `a flow names \`${end}\`, which is not an Activities Inventory node, a gateway, an event or a subprocess`);
        }
    }
    for (const row of subprocessRows) {
        const subprocess = firstKey(row['Subprocess Key']);
        const inside = new Set(keys(row['Nodes Inside']));
        if (!subprocess || inside.size === 0) continue;
        for (const node of inside) {
            if (!typeOf.has(node) && !gateways.has(node) && !events.has(node)) fail('loop-nodes', `subprocess \`${subprocess}\` lists \`${node}\`, which is not an Activities Inventory node, a gateway or an event`);
        }
        if (!/^\s*yes/i.test(row['Multi-instance?'] ?? '')) continue;
        for (const flow of flows) {
            const source = firstKey(flow.Source);
            const target = firstKey(flow.Target);
            if (!source || !target) continue;
            if (source === subprocess || target === subprocess) {
                const other = source === subprocess ? target : source;
                if (inside.has(other)) fail('loop-boundary', `flow \`${firstKey(flow['Flow Key']) ?? `${source}→${target}`}\` joins the loop \`${subprocess}\` to \`${other}\`, a node inside it; flows inside the loop run between its own nodes`);
                continue;
            }
            if (inside.has(source) !== inside.has(target)) {
                const [inner, outer] = inside.has(source) ? [source, target] : [target, source];
                fail('loop-boundary', `flow \`${firstKey(flow['Flow Key']) ?? `${source}→${target}`}\` joins \`${inner}\` (inside the per-item loop \`${subprocess}\`) to \`${outer}\` (outside it); a step that runs per item is listed in Nodes Inside, and flows enter and leave through \`${subprocess}\``);
            }
        }
    }
} else if (isFlow) {
    // one-kind
    for (const row of table(section(/^## \d+\. Nodes Inventory/))) {
        const kind = row['Step Kind'];
        if (kind && /[/+&,]| and /i.test(kind)) fail('one-kind', `step \`${firstKey(row['Node Key'])}\` has Step Kind "${kind}"; one kind of work per row`);
    }
}

/** Writes the handoff Status row; returns false when the SDD has none or it already holds `status`. */
function setStatus(status) {
    const pattern = /^(\|\s*\*\*Status\*\*\s*\|\s*)(\w+)(\s*\|)/m;
    const match = text.match(pattern);
    if (!match || match[2] === status) return false;
    writeFileSync(file, text.replace(pattern, `$1${status}$3`));
    return true;
}

for (const finding of new Set(findings)) console.log(finding);
if (findings.length > 0) {
    if (setStatus('draft')) console.log('Status set back to draft: change the tables the lines above name, then run this again.');
    process.exit(1);
}
if (!isRpa && !isBpmn && !isFlow) {
    console.log('SKIP: no table rules for this template.');
    process.exit(0);
}
console.log('OK: the SDD\'s tables agree with each other.');
if (flipToReady && setStatus('ready')) console.log('Status set to ready.');
process.exit(0);
