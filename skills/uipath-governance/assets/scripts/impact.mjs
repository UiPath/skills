#!/usr/bin/env node
/**
 * Compliance impact: given a proposed policy change (via a simulated CLI
 * cache), compute per-pack compliance delta vs. the current tenant state.
 *
 * Runs the walker twice per pack (before/after) and across all packs in
 * parallel, then diffs per-clause results.
 *
 * Usage:
 *   node impact.mjs \
 *     --packs-root      <dir-of-extracted-packs> \
 *     --cli-cache-before <path> \
 *     --cli-cache-after  <path> \
 *     --target-product   <productIdentifier> \
 *     [--json-out        <path>]
 *
 * Pack filtering: only packs whose manifest touches `--target-product`
 * are evaluated. Packs that don't mention the product are reported as
 * "unaffected" in the summary and skipped in detail.
 *
 * Exit codes:
 *   0 — delta computed (regression is a finding, not a failure)
 *   2 — missing / malformed inputs
 *   3 — walker error
 */

import fs from "node:fs";
import path from "node:path";
import { walkPack, preloadPack, readJson } from "./walker-core.mjs";

const args = {};
for (let i = 2; i < process.argv.length; i++) {
    const a = process.argv[i];
    if (a.startsWith("--")) args[a.slice(2)] = process.argv[++i];
}
for (const req of ["packs-root", "cli-cache-before", "cli-cache-after", "target-product"]) {
    if (!args[req]) {
        console.error(`error: --${req} is required`);
        process.exit(2);
    }
}

const packsRoot = path.resolve(args["packs-root"]);
const targetProduct = args["target-product"];

let cacheBefore, cacheAfter;
try {
    cacheBefore = readJson(args["cli-cache-before"]);
    cacheAfter = readJson(args["cli-cache-after"]);
} catch (e) {
    console.error(`error: failed to read cli cache: ${e.message}`);
    process.exit(2);
}

// Discover extracted pack dirs: any immediate subdir with manifest.json
let packDirs;
try {
    packDirs = fs
        .readdirSync(packsRoot, { withFileTypes: true })
        .filter((e) => e.isDirectory())
        .map((e) => path.join(packsRoot, e.name))
        .filter((d) => fs.existsSync(path.join(d, "manifest.json")));
} catch (e) {
    console.error(`error: cannot read packs-root: ${e.message}`);
    process.exit(2);
}

if (packDirs.length === 0) {
    console.error(`error: no extracted packs found under ${packsRoot}`);
    process.exit(2);
}

function packTouchesProduct(packDir) {
    try {
        const manifest = readJson(path.join(packDir, "manifest.json"));
        return manifest.policies?.some((p) => {
            if (p.productIdentifier === targetProduct) return true;
            // fallback: load the policy file and check its productIdentifier
            try {
                const policy = readJson(path.join(packDir, p.file));
                return policy.policy?.productIdentifier === targetProduct;
            } catch {
                return false;
            }
        });
    } catch {
        return false;
    }
}

// Walk one preloaded pack against one cache
async function walkOne(preloadedPack, cache, label) {
    try {
        return walkPack({ pack: preloadedPack, cliCache: cache, strict: false });
    } catch (e) {
        console.error(`error: walk failed for ${preloadedPack.packDir} [${label}]: ${e.message}`);
        process.exit(3);
    }
}

// Preload every pack once (parse manifest + clause-map + every policy file ONE TIME),
// then reuse across before/after walks. Halves fs reads + JSON.parse vs. walking
// from disk twice. All packs preload concurrently.
const packs = await Promise.all(
    packDirs.map(async (packDir) => {
        const affected = packTouchesProduct(packDir);
        if (!affected) {
            const manifest = readJson(path.join(packDir, "manifest.json"));
            return { packDir, affected: false, manifest };
        }
        const preloaded = preloadPack(packDir);
        const [before, after] = await Promise.all([
            walkOne(preloaded, cacheBefore, "before"),
            walkOne(preloaded, cacheAfter, "after"),
        ]);
        return { packDir, affected: true, before, after };
    }),
);

// Diff each affected pack
function diffPack(before, after) {
    const afterByClause = new Map(after.clauses.map((c) => [c.clauseId, c]));
    const regressions = [];
    const improvements = [];
    const unchanged = [];
    for (const b of before.clauses) {
        const a = afterByClause.get(b.clauseId);
        if (!a) continue;
        if (b.status === a.status) {
            unchanged.push({ clauseId: b.clauseId, name: b.name, status: b.status });
            continue;
        }
        // Transitions we care about
        if (b.status === "drifted" && a.status === "compliant") {
            improvements.push({ clauseId: b.clauseId, name: b.name, from: b.status, to: a.status, obligationLevel: b.obligationLevel });
        } else if (b.status === "compliant" && a.status === "drifted") {
            regressions.push({ clauseId: b.clauseId, name: b.name, from: b.status, to: a.status, obligationLevel: b.obligationLevel });
        } else {
            // skipped ↔ anything — usually harmless; record as unchanged
            unchanged.push({ clauseId: b.clauseId, name: b.name, status: `${b.status}→${a.status}` });
        }
    }
    return { regressions, improvements, unchanged };
}

const perPack = packs.map((p) => {
    if (!p.affected) {
        return {
            packId: p.manifest.packId,
            packName: p.manifest.packName,
            version: p.manifest.version,
            affected: false,
        };
    }
    const diff = diffPack(p.before, p.after);
    return {
        packId: p.before.manifest.packId,
        packName: p.before.manifest.packName,
        version: p.before.manifest.version,
        affected: true,
        before: {
            compliant: p.before.summary.compliant,
            total: p.before.summary.totalClauses,
            drifted: p.before.summary.drifted,
        },
        after: {
            compliant: p.after.summary.compliant,
            total: p.after.summary.totalClauses,
            drifted: p.after.summary.drifted,
        },
        net: p.after.summary.compliant - p.before.summary.compliant,
        regressions: diff.regressions,
        improvements: diff.improvements,
    };
});

const totals = {
    packsEvaluated: perPack.filter((p) => p.affected).length,
    packsUnaffected: perPack.filter((p) => !p.affected).length,
    totalImprovements: perPack.reduce((n, p) => n + (p.improvements?.length ?? 0), 0),
    totalRegressions: perPack.reduce((n, p) => n + (p.regressions?.length ?? 0), 0),
    mandatoryRegressions: perPack.reduce(
        (n, p) =>
            n +
            (p.regressions?.filter(
                (r) => r.obligationLevel === "Mandatory" || r.obligationLevel === "ConditionalMandatory",
            ).length ?? 0),
        0,
    ),
};

const report = {
    reportKind: "compliance-impact",
    schemaVersion: "1.0.0",
    generatedAt: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
    targetProduct,
    totals,
    packs: perPack,
};

if (args["json-out"]) {
    fs.mkdirSync(path.dirname(path.resolve(args["json-out"])), { recursive: true });
    fs.writeFileSync(args["json-out"], JSON.stringify(report, null, 2));
}

// Terminal summary
const lines = [];
lines.push(`Compliance impact of change to ${targetProduct}:`);
for (const p of perPack) {
    if (!p.affected) {
        lines.push(`  ${p.packName.padEnd(34)} (unaffected — does not touch ${targetProduct})`);
        continue;
    }
    const sign = p.net > 0 ? `+${p.net}` : p.net < 0 ? `${p.net}` : "±0";
    const tag =
        p.regressions.length > 0
            ? ` ⚠ ${p.regressions.length} regression${p.regressions.length > 1 ? "s" : ""}`
            : p.improvements.length > 0
            ? ""
            : " unchanged";
    lines.push(
        `  ${p.packName.padEnd(34)} ${p.before.compliant}/${p.before.total} → ${p.after.compliant}/${p.after.total}  (${sign})${tag}`,
    );
    for (const r of p.regressions) {
        lines.push(`     ✗ regression: ${r.clauseId} — ${r.name} [${r.obligationLevel}]`);
    }
    for (const i of p.improvements.slice(0, 5)) {
        lines.push(`     ✓ improves:   ${i.clauseId} — ${i.name}`);
    }
    if (p.improvements.length > 5) lines.push(`     ✓ … and ${p.improvements.length - 5} more improvements`);
}
lines.push("");
if (totals.mandatoryRegressions > 0) {
    lines.push(`⚠ ${totals.mandatoryRegressions} MANDATORY-clause regression(s). Default: do not apply.`);
} else if (totals.totalRegressions > 0) {
    lines.push(`⚠ ${totals.totalRegressions} non-mandatory regression(s). Review before applying.`);
} else if (totals.totalImprovements > 0) {
    lines.push(`✓ Net improvement: +${totals.totalImprovements} clause(s) across ${totals.packsEvaluated} pack(s).`);
} else {
    lines.push(`No compliance-posture change across ${totals.packsEvaluated} pack(s).`);
}
if (args["json-out"]) lines.push(`JSON: ${path.resolve(args["json-out"])}`);
process.stdout.write(lines.join("\n") + "\n");
