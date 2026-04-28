#!/usr/bin/env node
/**
 * Render a compliance-check JSON report to HTML using the template.
 *
 * Usage:
 *   node render-report.mjs \
 *     --json         <path-to-report.json> \
 *     --template     <path-to-compliance-report.html> \
 *     [--label-cache <path-to-locale-resource-map.json>] \
 *     [--out         <path-to-output.html>]
 *
 * --label-cache format: { "<productIdentifier>": { "<property-path>": "<description>" } }
 *                        (optional — falls back to the raw property path when absent)
 *
 * Exit codes:
 *   0 — HTML written
 *   2 — missing / malformed inputs
 *   3 — template contained unresolved placeholders after substitution
 */

import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";

const args = {};
for (let i = 2; i < process.argv.length; i++) {
    const a = process.argv[i];
    if (a === "--open") { args.open = true; continue; }
    if (a.startsWith("--")) args[a.slice(2)] = process.argv[++i];
}
for (const req of ["json", "template"]) {
    if (!args[req]) {
        console.error(`error: --${req} is required`);
        process.exit(2);
    }
}

function readJson(p) {
    try { return JSON.parse(fs.readFileSync(p, "utf8")); }
    catch (e) { console.error(`error: ${p}: ${e.message}`); process.exit(2); }
}

const report = readJson(args.json);
const template = fs.readFileSync(args.template, "utf8");
const labelCache = args["label-cache"] ? readJson(args["label-cache"]) : {};

// ---------- helpers ----------
function escHtml(s) {
    return String(s ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

const MAX_INLINE_LEN = 160;

function fmtVal(v) {
    if (v === null || v === undefined) return '<span style="color:#94a3b8">null</span>';
    if (typeof v === "boolean") return v ? "true" : "false";
    if (typeof v === "string") return escHtml(JSON.stringify(v));
    if (typeof v === "number") return String(v);
    if (Array.isArray(v) || typeof v === "object") {
        const compact = JSON.stringify(v);
        if (compact.length <= MAX_INLINE_LEN) {
            return `<code>${escHtml(compact)}</code>`;
        }
        const pretty = JSON.stringify(v, null, 2);
        const summary = Array.isArray(v) ? `array · ${v.length} item${v.length === 1 ? "" : "s"}` : `object · ${Object.keys(v).length} key${Object.keys(v).length === 1 ? "" : "s"}`;
        return (
            `<details><summary style="cursor:pointer;color:inherit">${escHtml(summary)}</summary>` +
            `<pre style="margin:6px 0 0;padding:8px;background:#f8fafc;border-radius:4px;font-size:11px;line-height:1.4;max-height:320px;overflow:auto;white-space:pre-wrap;word-break:break-all">${escHtml(pretty)}</pre>` +
            `</details>`
        );
    }
    return escHtml(v);
}

// Matches an unresolved i18n reference like "AITrustLayer.allowed-regions-label".
// When the locale API returns this verbatim instead of a translated string,
// treat it as missing and fall back.
const UNRESOLVED_I18N = /^[A-Z][A-Za-z0-9]+(\.[a-z0-9][A-Za-z0-9-]*)+(-(label|description|tooltip))?$/;

function lookupLabel(product, propPath) {
    const productMap = labelCache[product];
    if (!productMap) return null;
    const pick = (k) => {
        const v = productMap[k];
        if (!v || typeof v !== "string") return null;
        if (UNRESOLVED_I18N.test(v)) return null; // unresolved — fall through
        return v;
    };
    // Try exact match first
    const exact = pick(propPath);
    if (exact) return exact;
    // Try the leaf-only form ("container.pii-in-flight-agents" → "pii-in-flight-agents")
    const leaf = propPath.split(".").pop();
    const leafMatch = pick(leaf);
    if (leafMatch) return leafMatch;
    return null;
}

const STATUS_RANK = { drifted: 0, compliant: 1, skipped: 2 };
const OBL_RANK = { Mandatory: 0, ConditionalMandatory: 1, Recommended: 2, Optional: 3 };
const OBL_TAG = {
    Mandatory: "tag-mandatory",
    ConditionalMandatory: "tag-conditional",
    Recommended: "tag-recommended",
    Optional: "tag-optional",
};
const PILL = {
    compliant: ["pill-compliant", "Compliant"],
    drifted: ["pill-drifted", "Drifted"],
    skipped: ["pill-skipped", "Skipped"],
};

const clauses = report.clauses ?? [];
const summary = report.summary ?? {};
const total = summary.totalClauses ?? clauses.length;

const ordered = [...clauses].sort(
    (a, b) =>
        (STATUS_RANK[a.status] ?? 9) - (STATUS_RANK[b.status] ?? 9) ||
        (OBL_RANK[a.obligationLevel] ?? 9) - (OBL_RANK[b.obligationLevel] ?? 9) ||
        a.clauseId.localeCompare(b.clauseId),
);

const driftPropCount = (c) =>
    c.contributions.reduce((n, ctr) => n + (ctr.properties ?? []).filter((p) => !p.match).length, 0);

// ---------- CLAUSE_ROWS ----------
function contribChips(c) {
    const chips = (c.contributions ?? []).map((ctr) => {
        if (ctr.status === "skipped") {
            return `<span class="chip chip-skipped">${escHtml(ctr.product ?? "?")} — skipped (${escHtml(ctr.reason ?? "")})</span>`;
        }
        const product = escHtml(ctr.product ?? "?");
        const polName = ctr.effectivePolicyName
            ? ` · <b>${escHtml(ctr.effectivePolicyName)}</b>`
            : ` · <i>(no custom policy — global default)</i>`;
        const scope = ctr.effectiveDeployment?.type
            ? ` · ${escHtml(ctr.effectiveDeployment.type)}`
            : "";
        return `<span class="chip">${product}${polName}${scope}</span>`;
    });
    return chips.length ? `<div class="clause-contribs">${chips.join(" ")}</div>` : "";
}

const clauseRows = ordered.map((c) => {
    const [pillCls, pillLabel] = PILL[c.status] ?? ["pill-skipped", c.status];
    const dc = driftPropCount(c);
    return (
        `      <tr>` +
        `<td><span class="clause-id">${escHtml(c.clauseId)}</span></td>` +
        `<td><div class="clause-name">${escHtml(c.name)}</div>` +
        `<div class="clause-category">${escHtml(c.category ?? "")}</div>` +
        `${contribChips(c)}` +
        `</td>` +
        `<td><span class="obligation-tag ${OBL_TAG[c.obligationLevel] ?? "tag-optional"}">` +
        `${escHtml(c.obligationLevel)}</span></td>` +
        `<td><span class="status-pill ${pillCls}">${pillLabel}</span></td>` +
        `<td><span class="drift-count">${dc || ""}</span></td>` +
        `</tr>`
    );
}).join("\n");

// ---------- DRIFT_DETAILS ----------
const driftedClauses = ordered.filter((c) => c.status === "drifted");
let driftDetails;
if (!driftedClauses.length) {
    driftDetails = `<p class="empty-note">No drifted clauses.</p>`;
} else {
    driftDetails = driftedClauses
        .map((c) => {
            const contribBlocks = (c.contributions ?? [])
                .filter((ctr) => (ctr.properties ?? []).some((p) => !p.match))
                .map((ctr) => {
                    const product = ctr.product ?? "";
                    const rows = (ctr.properties ?? [])
                        .filter((p) => !p.match)
                        .map((p) => {
                            const label = lookupLabel(product, p.path);
                            const ctrl = label
                                ? `<div class="control-desc">${escHtml(label)}</div><div class="control-path"><code>${escHtml(p.path)}</code></div>`
                                : `<div class="control-desc"><code>${escHtml(p.path)}</code></div>`;
                            return (
                                `      <tr><td>${ctrl}</td>` +
                                `<td><span class="val-expected">${fmtVal(p.expected)}</span></td>` +
                                `<td><span class="val-actual">${fmtVal(p.actual)}</span></td>` +
                                `<td><span class="val-mismatch">&#x2717;</span></td></tr>`
                            );
                        })
                        .join("\n");
                    const effPolicy = ctr.effectivePolicyName
                        ? `Effective policy: <b>${escHtml(ctr.effectivePolicyName)}</b>`
                        : `Effective policy: <i>(global default — no custom policy deployed)</i>`;
                    const scope = ctr.effectiveDeployment?.type
                        ? `<span class="contrib-scope">[${escHtml(ctr.effectiveDeployment.type)}${ctr.effectiveDeployment.name ? " · " + escHtml(ctr.effectiveDeployment.name) : ""}]</span>`
                        : "";
                    const packFile = ctr.policyFile
                        ? `<span class="contrib-file">Pack source: ${escHtml(ctr.policyFile)}</span>`
                        : "";
                    return (
                        `<div class="contrib-section">` +
                        `<div class="contrib-header">` +
                        `<span class="contrib-product">${escHtml(product)}</span>` +
                        `<span class="contrib-policy">${effPolicy}</span>` +
                        `${scope}` +
                        `${packFile}` +
                        `</div>` +
                        `<table><thead><tr><th>Control</th><th>Expected</th><th>Actual</th>` +
                        `<th style="width:70px">Match</th></tr></thead>` +
                        `<tbody>\n${rows}\n</tbody></table>` +
                        `</div>`
                    );
                })
                .join("\n");
            return (
                `<div class="drift-detail">` +
                `<div class="drift-detail-header">` +
                `<span class="clause-id">${escHtml(c.clauseId)}</span>` +
                `<span class="clause-name">${escHtml(c.name)}</span>` +
                `<span class="obligation-tag ${OBL_TAG[c.obligationLevel] ?? "tag-optional"}">${escHtml(c.obligationLevel)}</span>` +
                `</div>` +
                `${contribBlocks}` +
                `</div>`
            );
        })
        .join("\n");
}

// ---------- SKIPPED_POLICIES_BLOCK ----------
const skipped = report.skippedPolicies ?? [];
let skippedBlock = "";
if (skipped.length) {
    const items = skipped
        .map((s) => `    <li><code>${escHtml(s.file)}</code> — ${escHtml(s.product)} (${escHtml(s.reason)})</li>`)
        .join("\n");
    skippedBlock =
        `<div class="skipped-policies">` +
        `<h2 style="margin-top:0">Skipped Policies</h2>` +
        `<p class="empty-note">Policy files parsed but not diffed (out of scope for V1 tenant-only checks):</p>` +
        `<ul>\n${items}\n</ul></div>`;
}

// ---------- scalars ----------
const pct = (n) => (total ? String(Math.round((n / total) * 100)) : "0");
const overallStatus = report.overall ?? "Compliant";
const overallBadgeClass =
    overallStatus === "Compliant"
        ? "badge-pass"
        : overallStatus === "Non-Compliant"
          ? "badge-fail"
          : "badge-partial";

const generatedAt = (() => {
    const d = new Date(report.generatedAt);
    if (isNaN(d.getTime())) return report.generatedAt;
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())} UTC`;
})();

const scalars = {
    PACK_NAME: escHtml(report.pack?.packName ?? ""),
    PACK_VERSION: escHtml(report.pack?.version ?? ""),
    TENANT_NAME: escHtml(report.target?.tenantName ?? ""),
    RUN_SCOPE: escHtml(report.target?.runScope ?? "tenant-only"),
    GENERATED_AT: escHtml(generatedAt),
    OVERALL_STATUS: escHtml(overallStatus),
    OVERALL_BADGE_CLASS: overallBadgeClass,
    TOTAL_CLAUSES: String(total),
    COMPLIANT_COUNT: String(summary.compliant ?? 0),
    DRIFTED_COUNT: String(summary.drifted ?? 0),
    SKIPPED_COUNT: String(summary.skipped ?? 0),
    COMPLIANT_PCT: pct(summary.compliant ?? 0),
    DRIFTED_PCT: pct(summary.drifted ?? 0),
    SKIPPED_PCT: pct(summary.skipped ?? 0),
};

let out = template;
out = out.replace("<!-- {{CLAUSE_ROWS}} -->", clauseRows);
out = out.replace("<!-- {{DRIFT_DETAILS}} -->", driftDetails);
out = out.replace("<!-- {{SKIPPED_POLICIES_BLOCK}} -->", skippedBlock);
for (const [k, v] of Object.entries(scalars)) {
    out = out.replaceAll(`{{${k}}}`, v);
}

const leftover = [...out.matchAll(/\{\{[A-Z0-9_]+\}\}/g)].map((m) => m[0]);
if (leftover.length) {
    console.error(`error: unresolved placeholders: ${[...new Set(leftover)].join(", ")}`);
    process.exit(3);
}

const outPath =
    args.out ??
    path.join(
        path.dirname(path.resolve(args.json)),
        path.basename(args.json, ".json") + ".html",
    );
fs.mkdirSync(path.dirname(path.resolve(outPath)), { recursive: true });
fs.writeFileSync(outPath, out);
const absOut = path.resolve(outPath);
process.stdout.write(`HTML: ${absOut}\n`);

if (args.open) {
    // Cross-platform open, detached so the renderer process exits cleanly
    let cmd, cmdArgs;
    if (process.platform === "win32") {
        cmd = "cmd";
        cmdArgs = ["/c", "start", "", absOut];
    } else if (process.platform === "darwin") {
        cmd = "open";
        cmdArgs = [absOut];
    } else {
        cmd = "xdg-open";
        cmdArgs = [absOut];
    }
    try {
        const child = spawn(cmd, cmdArgs, { detached: true, stdio: "ignore" });
        child.unref();
        process.stdout.write(`Opened in browser.\n`);
    } catch (e) {
        process.stderr.write(`warn: could not auto-open (${e.message}). Open manually: ${absOut}\n`);
    }
}
