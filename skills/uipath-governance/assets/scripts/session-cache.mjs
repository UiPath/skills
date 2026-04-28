#!/usr/bin/env node
/**
 * Session-scoped disk cache for AOPS template payloads and extracted
 * compliance packs. Safe to hit across Check / Diagnose / Advise / Apply
 * within one Claude session.
 *
 * What IS cached:
 *   - template-form-data   (30 min TTL)  — product template blueprint
 *   - template-locale      (30 min TTL)  — product i18n label bundle
 *   - template             (30 min TTL)  — full raw template tree
 *   - pack-extract         (1 h   TTL)   — extracted .uipolicy directory,
 *                                          keyed by the source archive's
 *                                          absolute path + size + mtime
 *
 * What is explicitly NOT cached:
 *   - deployed-policy responses. Tenant state can change under admin
 *     activity at any time; stale values would produce wrong Check drift,
 *     wrong Impact deltas, and wrong Diagnose findings. ALWAYS fetch live.
 *   - policy get / policy list / deployment tenant get. Same reason.
 *
 * Usage — fetch-or-refresh a product template's form-data blueprint:
 *
 *   node session-cache.mjs fetch template-form-data AITrustLayer --out path.json
 *
 * Usage — fetch-or-refresh the locale resource:
 *
 *   node session-cache.mjs fetch template-locale AITrustLayer --out path.json
 *
 * Usage — extract-or-reuse a .uipolicy archive:
 *
 *   node session-cache.mjs fetch pack-extract /abs/path/to/pack.uipolicy --out /dir/for/extracted/
 *
 *   (The --out dir is a POINTER — on hit, the script writes the cached
 *   extraction path to stdout as `extracted: <path>`. Callers should
 *   consume the path, not copy the contents.)
 *
 * Usage — pure read (returns null to stdout if missing or stale):
 *
 *   node session-cache.mjs read template-form-data AITrustLayer
 *
 * Cache location: $TMP_ROOT/uipath-governance/cache/, resolved via the same
 * cygpath/node-os.tmpdir logic the other scripts use.
 */

import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { spawnSync } from "node:child_process";

const TTL_SEC = {
    "template": 1800,            // 30 min — templates only change on AOPS migrations
    "template-form-data": 1800,
    "template-locale": 1800,
    "pack-extract": 3600,        // 1 h — pack archives are immutable inputs
    // NOTE: deployed-policy, policy get, tenant get are deliberately NOT cached.
    // Tenant state can change under admin activity at any time.
};

function cacheRoot() {
    const tmp = os.tmpdir().replace(/\\/g, "/");
    const dir = path.join(tmp, "uipath-governance", "cache");
    fs.mkdirSync(dir, { recursive: true });
    return dir;
}

function safeKey(k) { return k.replace(/[^a-zA-Z0-9._-]/g, "_"); }

function cachePath(kind, key) {
    return path.join(cacheRoot(), kind, safeKey(key) + ".json");
}

function isFresh(filePath, ttlSec) {
    try {
        const s = fs.statSync(filePath);
        return (Date.now() - s.mtimeMs) / 1000 < ttlSec;
    } catch {
        return false;
    }
}

// ---------- command builders ----------

function buildUipArgs(kind, key) {
    if (kind === "template-form-data") {
        // key = productIdentifier
        return {
            args: ["gov", "aops-policy", "template", "get", key, "--output-form-data", "<OUT>", "--output", "json"],
            outputIsFile: true,
        };
    }
    if (kind === "template-locale") {
        return {
            args: ["gov", "aops-policy", "template", "get", key, "--output-template-locale-resource", "<OUT>", "--output", "json"],
            outputIsFile: true,
        };
    }
    if (kind === "template") {
        return {
            args: ["gov", "aops-policy", "template", "get", key, "--output", "json"],
            outputIsFile: false,
        };
    }
    throw new Error(`unknown cache kind: ${kind}`);
}

function runUip(argsTemplate, outPath) {
    const finalArgs = argsTemplate.map((a) => (a === "<OUT>" ? outPath : a));
    const r = spawnSync("uip", finalArgs, { encoding: "utf8", maxBuffer: 50 * 1024 * 1024 });
    if (r.status !== 0) {
        throw new Error(`uip failed (exit ${r.status}): ${r.stderr?.slice(0, 2048) ?? ""}`);
    }
    return r.stdout;
}

// ---------- main ----------

const [, , subcmd, kind, key, ...rest] = process.argv;
const restArgs = {};
for (let i = 0; i < rest.length; i++) {
    const a = rest[i];
    if (a.startsWith("--")) restArgs[a.slice(2)] = rest[++i];
}

if (!subcmd || !kind || !key) {
    console.error("usage: session-cache.mjs <fetch|read> <kind> <key> [--out <path>]");
    process.exit(2);
}

const ttl = TTL_SEC[kind];
if (!ttl) {
    console.error(`error: unknown cache kind '${kind}'. Valid: ${Object.keys(TTL_SEC).join(", ")}`);
    process.exit(2);
}

// ---------- pack-extract branch (directory cache, separate layout) ----------

if (kind === "pack-extract") {
    const packAbs = path.resolve(key);
    let stat;
    try { stat = fs.statSync(packAbs); }
    catch { console.error(`error: pack not found: ${packAbs}`); process.exit(2); }

    // Key by absolute path + size + mtime so edits invalidate automatically
    const tag = `${packAbs}|${stat.size}|${stat.mtimeMs}`;
    const hash = (await import("node:crypto")).createHash("sha1").update(tag).digest("hex").slice(0, 16);
    const extractDir = path.join(cacheRoot(), "pack-extract", path.basename(packAbs, ".uipolicy") + "-" + hash);
    const sentinel = path.join(extractDir, ".uipath-governance-extracted");

    if (subcmd === "read") {
        if (fs.existsSync(sentinel) && isFresh(sentinel, TTL_SEC["pack-extract"])) {
            process.stdout.write(extractDir + "\n");
        } else {
            process.stdout.write("null\n");
        }
        process.exit(0);
    }

    if (subcmd !== "fetch") {
        console.error(`error: unknown subcmd '${subcmd}'`);
        process.exit(2);
    }

    if (fs.existsSync(sentinel) && isFresh(sentinel, TTL_SEC["pack-extract"])) {
        process.stdout.write(`cache-hit: extracted=${extractDir}\n`);
        process.exit(0);
    }

    // Miss — extract. Prefer `unzip`; fall back to PowerShell Expand-Archive on Windows.
    fs.rmSync(extractDir, { recursive: true, force: true });
    fs.mkdirSync(extractDir, { recursive: true });
    let r = spawnSync("unzip", ["-q", packAbs, "-d", extractDir], { encoding: "utf8" });
    if (r.status !== 0 && r.error && process.platform === "win32") {
        r = spawnSync("powershell", ["-NoProfile", "-Command", `Expand-Archive -Force -Path "${packAbs}" -DestinationPath "${extractDir}"`], { encoding: "utf8" });
    }
    if (r.status !== 0) {
        console.error(`error: extraction failed: ${r.stderr || r.error?.message}`);
        process.exit(3);
    }
    fs.writeFileSync(sentinel, JSON.stringify({ source: packAbs, size: stat.size, mtimeMs: stat.mtimeMs, extractedAt: new Date().toISOString() }, null, 2));
    process.stdout.write(`cache-miss (extracted): extracted=${extractDir}\n`);
    process.exit(0);
}

// ---------- template branches ----------

const cached = cachePath(kind, key);

if (subcmd === "read") {
    if (isFresh(cached, ttl)) {
        process.stdout.write(fs.readFileSync(cached, "utf8"));
    } else {
        process.stdout.write("null\n");
    }
    process.exit(0);
}

if (subcmd !== "fetch") {
    console.error(`error: unknown subcmd '${subcmd}'`);
    process.exit(2);
}

// fetch: return cached if fresh, else re-run uip
if (isFresh(cached, ttl)) {
    if (restArgs.out) {
        fs.mkdirSync(path.dirname(path.resolve(restArgs.out)), { recursive: true });
        fs.copyFileSync(cached, restArgs.out);
    }
    process.stdout.write(`cache-hit: ${cached}\n`);
    process.exit(0);
}

// cache miss → run uip
const { args: argsTemplate, outputIsFile } = buildUipArgs(kind, key);
fs.mkdirSync(path.dirname(cached), { recursive: true });

try {
    if (outputIsFile) {
        // Template variants write to a file; cache the file itself.
        const tmp = cached + ".tmp";
        runUip(argsTemplate, tmp);  // stdout discarded intentionally
        fs.renameSync(tmp, cached);
    } else {
        const stdout = runUip(argsTemplate, null);
        fs.writeFileSync(cached, stdout);
    }
} catch (e) {
    console.error(`error: ${e.message}`);
    process.exit(3);
}

if (restArgs.out) {
    fs.mkdirSync(path.dirname(path.resolve(restArgs.out)), { recursive: true });
    fs.copyFileSync(cached, restArgs.out);
}

process.stdout.write(`cache-miss (refreshed): ${cached}\n`);
