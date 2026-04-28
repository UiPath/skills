#!/usr/bin/env node
/**
 * Compliance-check walker CLI: unzip-and-report wrapper around walker-core.
 * Loads an extracted .uipolicy pack, calls the shared walker against a
 * pre-fetched CLI cache, and emits a JSON report + a terminal summary.
 *
 * Pure function of its inputs — no network calls, no uip shellouts. The
 * caller is responsible for preflight, unzip, and CLI cache hydration.
 *
 * Usage:
 *   node check-walk.mjs \
 *     --pack-dir    <extracted-pack-dir> \
 *     --cli-cache   <path-to-cache.json> \
 *     --tenant-id   <tenant-guid> \
 *     --tenant-name <tenant-display-name> \
 *     --pack-source <display-string> \
 *     --out-dir     <dir>  [--json-out <path>]
 *
 * CLI cache shape — keys are "{licenseType}|{productIdentifier}", values
 * are the `Data` subtree of a successful `uip gov aops-policy
 * deployed-policy get <licenseType> <productName> <tenantId>` response
 * (caller-own mode — no S2S).
 *
 * Exit codes:
 *   0 — report written (drift is a finding, not a failure)
 *   2 — missing / malformed inputs
 *   3 — walker could not complete (cache miss, unreadable pack)
 */

import fs from "node:fs";
import path from "node:path";
import { walkPack, readJson } from "./walker-core.mjs";

const args = {};
for (let i = 2; i < process.argv.length; i++) {
    const a = process.argv[i];
    if (a.startsWith("--")) args[a.slice(2)] = process.argv[++i];
}
for (const req of ["pack-dir", "cli-cache", "tenant-id", "tenant-name"]) {
    if (!args[req]) {
        console.error(`error: --${req} is required`);
        process.exit(2);
    }
}
const outDir = args["out-dir"] ?? ".";
const packSource = args["pack-source"] ?? "";

let cliCache;
try {
    cliCache = readJson(args["cli-cache"]);
} catch (e) {
    console.error(`error: failed to read ${args["cli-cache"]}: ${e.message}`);
    process.exit(2);
}

let walked;
try {
    walked = walkPack({ packDir: args["pack-dir"], cliCache, strict: true });
} catch (e) {
    console.error(`error: ${e.message}`);
    process.exit(3);
}

const { manifest, clauses, summary, skippedPolicies } = walked;

function overallStatus() {
    if (summary.totalClauses === 0) return { label: "Compliant", klass: "badge-pass" };
    if (summary.compliant === summary.totalClauses) return { label: "Compliant", klass: "badge-pass" };
    const mandatoryDrifted = clauses.some(
        (c) =>
            (c.obligationLevel === "Mandatory" || c.obligationLevel === "ConditionalMandatory") &&
            c.status === "drifted",
    );
    if (summary.drifted === summary.totalClauses || mandatoryDrifted)
        return { label: "Non-Compliant", klass: "badge-fail" };
    return { label: "Partially Compliant", klass: "badge-partial" };
}
const overall = overallStatus();

let effectivePolicyName = null;
let effectiveDeployment = null;
for (const c of clauses) {
    for (const ctr of c.contributions) {
        if (ctr.status === "checked" && ctr.effectivePolicyName && !effectivePolicyName) {
            effectivePolicyName = ctr.effectivePolicyName;
            effectiveDeployment = ctr.effectiveDeployment;
            break;
        }
    }
    if (effectivePolicyName) break;
}

const nowIso = new Date().toISOString().replace(/\.\d+Z$/, "Z");
const tsCompact = nowIso.replace(/[-:]/g, "").replace(/Z$/, "Z");

const report = {
    reportKind: "compliance-check",
    schemaVersion: "1.0.0",
    generatedAt: nowIso,
    pack: {
        packId: manifest.packId,
        packName: manifest.packName,
        version: manifest.version,
        source: packSource,
    },
    target: {
        tenantId: args["tenant-id"],
        tenantName: args["tenant-name"],
        runScope: "caller-own",
        effectivePolicyName,
        effectiveDeployment,
    },
    overall: overall.label,
    summary: { ...summary, skippedPolicyFiles: skippedPolicies.length },
    clauses,
    skippedPolicies,
};

const jsonPath = args["json-out"] ?? path.join(outDir, `compliance-report-${manifest.packId}-${tsCompact}.json`);
fs.mkdirSync(path.dirname(path.resolve(jsonPath)), { recursive: true });
fs.writeFileSync(jsonPath, JSON.stringify(report, null, 2));

const statusRank = { drifted: 0, compliant: 1, skipped: 2 };
const oblRank = { Mandatory: 0, ConditionalMandatory: 1, Recommended: 2, Optional: 3 };
const glyph = { compliant: "✓", drifted: "✗", skipped: "·" };
const ordered = [...clauses].sort(
    (a, b) =>
        (statusRank[a.status] ?? 9) - (statusRank[b.status] ?? 9) ||
        (oblRank[a.obligationLevel] ?? 9) - (oblRank[b.obligationLevel] ?? 9) ||
        a.clauseId.localeCompare(b.clauseId),
);
const driftCount = (c) =>
    c.contributions.reduce((n, ctr) => n + ctr.properties.filter((p) => !p.match).length, 0);

const lines = [];
lines.push(`Compliance Check: ${report.pack.packName} v${report.pack.version} → tenant ${report.target.tenantName}`);
lines.push(`Overall: ${overall.label}`);
lines.push("");
for (const c of ordered) {
    const g = glyph[c.status] ?? "·";
    const ext = c.status === "drifted" ? ` (${driftCount(c)} properties)` : "";
    lines.push(`  ${g} ${c.clauseId.padEnd(10)}${c.name.padEnd(58).slice(0, 58)}  ${c.status}${ext}`);
}
lines.push("");
lines.push(
    `Result: ${summary.compliant}/${summary.totalClauses} compliant, ${summary.drifted} drifted, ${summary.skipped} skipped`,
);
if (skippedPolicies.length) {
    lines.push(`Skipped policy files: ${skippedPolicies.length}`);
}
lines.push("");
lines.push(`JSON: ${path.resolve(jsonPath)}`);
process.stdout.write(lines.join("\n") + "\n");
