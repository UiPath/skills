#!/usr/bin/env node
/**
 * Deterministic deep-merge of pack overrides onto a base formData object.
 * The base is typically the product's template defaults (fresh-create path)
 * OR the currently-deployed policy's data (subset path — preserves live
 * tenant config for fields outside the narrowed scope).
 *
 * Merge rules (shared across Apply / Advise / Diagnose CREATE and UPDATE):
 *   - Objects merge recursively, key-by-key.
 *   - Arrays REPLACE wholesale — the override's array wins. An explicit
 *     empty array [] is a deliberate clear.
 *   - Scalars (string/number/boolean) REPLACE.
 *   - Explicit null in the override means "clear this leaf".
 *   - The base fills every path the override doesn't touch.
 *
 * Usage:
 *   node merge-overrides.mjs \
 *     --base       <path-to-base-form-data.json> \
 *     --overrides  <path-to-pack-form-data.json> \
 *     --out        <path-to-merged-form-data.json> \
 *     [--summary]
 *
 * --defaults is accepted as an alias for --base for backward compatibility
 * with older callers that passed template defaults.
 *
 * Inputs MUST be the bare formData object — not wrapped in { "data": ... }.
 * The output has the same shape and is ready to pass to `uip gov aops-policy
 * create|update --input <path>`.
 *
 * Exit codes:
 *   0 — merged file written
 *   2 — missing / malformed inputs
 */

import fs from "node:fs";
import path from "node:path";

const args = {};
for (let i = 2; i < process.argv.length; i++) {
    const a = process.argv[i];
    if (a === "--summary") { args.summary = true; continue; }
    if (a.startsWith("--")) args[a.slice(2)] = process.argv[++i];
}
// --defaults is a legacy alias for --base
const basePath = args.base ?? args.defaults;
for (const [k, v] of Object.entries({ base: basePath, overrides: args.overrides, out: args.out })) {
    if (!v) {
        console.error(`error: --${k === "base" ? "base (or --defaults)" : k} is required`);
        process.exit(2);
    }
}

function readJson(p) {
    try { return JSON.parse(fs.readFileSync(p, "utf8")); }
    catch (e) { console.error(`error: ${p}: ${e.message}`); process.exit(2); }
}

const base = readJson(basePath);
const overrides = readJson(args.overrides);

if (base === null || typeof base !== "object" || Array.isArray(base)) {
    console.error(`error: --base must be an object (the bare formData, not wrapped in { data: ... })`);
    process.exit(2);
}
if (overrides === null || typeof overrides !== "object" || Array.isArray(overrides)) {
    console.error(`error: --overrides must be an object (the bare formData, not wrapped in { data: ... })`);
    process.exit(2);
}

// ---------- merge ----------
const touched = []; // paths whose value came from the override

function isPlainObject(v) {
    return v !== null && typeof v === "object" && !Array.isArray(v);
}

function merge(dst, src, trail) {
    for (const key of Object.keys(src)) {
        const overrideVal = src[key];
        const next = trail ? `${trail}.${key}` : key;
        if (overrideVal === null) {
            // explicit clear
            dst[key] = null;
            touched.push({ path: next, op: "clear" });
            continue;
        }
        if (isPlainObject(overrideVal)) {
            if (!isPlainObject(dst[key])) dst[key] = {};
            merge(dst[key], overrideVal, next);
            continue;
        }
        if (Array.isArray(overrideVal)) {
            // replace wholesale (by design — see header comment)
            dst[key] = overrideVal.slice();
            touched.push({ path: next, op: "replace-array", size: overrideVal.length });
            continue;
        }
        // scalar replace
        dst[key] = overrideVal;
        touched.push({ path: next, op: "replace-scalar" });
    }
    return dst;
}

// Clone base so we don't mutate the input file's cached parse
const merged = JSON.parse(JSON.stringify(base));
merge(merged, overrides, "");

// ---------- write ----------
fs.mkdirSync(path.dirname(path.resolve(args.out)), { recursive: true });
fs.writeFileSync(args.out, JSON.stringify(merged, null, 2));
process.stdout.write(`MERGED: ${path.resolve(args.out)}\n`);

if (args.summary) {
    process.stdout.write(`Overridden paths: ${touched.length}\n`);
    const grouped = touched.slice(0, 20);
    for (const t of grouped) {
        process.stdout.write(`  ${t.op.padEnd(16)} ${t.path}${t.size != null ? ` (array[${t.size}])` : ""}\n`);
    }
    if (touched.length > 20) process.stdout.write(`  … and ${touched.length - 20} more\n`);
}
