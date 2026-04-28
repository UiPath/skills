#!/usr/bin/env node
/**
 * Concurrent `uip` invocation helper. Replaces bash `&`+`wait` fan-out —
 * gives every hydration step (Check / Impact / Diagnose / Advise) the same
 * deterministic parallelism with a capped concurrency to avoid overwhelming
 * the CLI's auth refresh or the API's rate limiter.
 *
 * Input: a JSON batch file (array of jobs).
 *
 *   [
 *     {
 *       "id":    "<any string — used as result key>",
 *       "args":  ["gov","aops-policy","deployed-policy","get","NoLicense","AITrustLayer","<tenantId>"],
 *       "out":   "<optional absolute path — if set, stdout is written here instead of being returned>",
 *       "stdin": "<optional string — written to the process's stdin>"
 *     },
 *     ...
 *   ]
 *
 * Every job is invoked as: `uip <args...> --output json` (the flag is added
 * unless the caller already included it). stderr is captured and surfaced on
 * failure; stdout is either parsed as JSON into `result` or written to `out`
 * and the result contains `{ out: "<path>" }`.
 *
 * Usage:
 *   node parallel-cli.mjs \
 *     --batch       <path-to-batch.json> \
 *     --results     <path-to-results.json> \
 *     [--concurrency 8] \
 *     [--dry-run]
 *
 * Results file shape:
 *   {
 *     "<id>": { "ok": true,  "data": <parsed-json-or-null>, "out": "<path-or-null>", "code": "<CLI Code>" }
 *     "<id>": { "ok": false, "error": "<message>", "stderr": "<first 2 KB>" }
 *   }
 *
 * Exit codes:
 *   0 — batch complete (individual failures are recorded in results.json)
 *   2 — batch itself malformed
 *   3 — every job failed (nothing succeeded)
 */

import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";

const args = {};
for (let i = 2; i < process.argv.length; i++) {
    const a = process.argv[i];
    if (a === "--dry-run") { args.dryRun = true; continue; }
    if (a.startsWith("--")) args[a.slice(2)] = process.argv[++i];
}
for (const req of ["batch", "results"]) {
    if (!args[req]) {
        console.error(`error: --${req} is required`);
        process.exit(2);
    }
}
const concurrency = Math.max(1, Math.min(16, parseInt(args.concurrency ?? "8", 10)));

let batch;
try {
    batch = JSON.parse(fs.readFileSync(args.batch, "utf8"));
    if (!Array.isArray(batch)) throw new Error("batch must be a JSON array");
} catch (e) {
    console.error(`error: failed to read batch: ${e.message}`);
    process.exit(2);
}

function runOne(job) {
    return new Promise((resolve) => {
        const jobArgs = Array.isArray(job.args) ? [...job.args] : [];
        if (!jobArgs.includes("--output")) jobArgs.push("--output", "json");
        if (args.dryRun) {
            resolve({ id: job.id, ok: true, data: null, dryRun: true, cmd: ["uip", ...jobArgs].join(" ") });
            return;
        }
        const child = spawn("uip", jobArgs, { stdio: ["pipe", "pipe", "pipe"] });
        let stdout = "";
        let stderr = "";
        child.stdout.on("data", (d) => { stdout += d.toString(); });
        child.stderr.on("data", (d) => { stderr += d.toString(); });
        if (job.stdin) child.stdin.write(job.stdin);
        child.stdin.end();
        child.on("error", (e) => resolve({ id: job.id, ok: false, error: e.message, stderr: stderr.slice(0, 2048) }));
        child.on("close", (exit) => {
            if (exit !== 0) {
                resolve({
                    id: job.id,
                    ok: false,
                    error: `exit ${exit}`,
                    stderr: stderr.slice(0, 2048),
                    stdoutSnippet: stdout.slice(0, 512),
                });
                return;
            }
            if (job.out) {
                // Caller wanted stdout written to a file — don't parse, don't return.
                try {
                    fs.mkdirSync(path.dirname(path.resolve(job.out)), { recursive: true });
                    fs.writeFileSync(job.out, stdout);
                    resolve({ id: job.id, ok: true, out: path.resolve(job.out), data: null });
                } catch (e) {
                    resolve({ id: job.id, ok: false, error: `failed to write out: ${e.message}` });
                }
                return;
            }
            try {
                const parsed = stdout.trim() ? JSON.parse(stdout) : null;
                const code = parsed?.Code ?? null;
                if (parsed?.Result === "Failure") {
                    resolve({ id: job.id, ok: false, error: parsed.Message ?? "CLI reported Failure", code, data: parsed });
                    return;
                }
                resolve({ id: job.id, ok: true, data: parsed, code });
            } catch (e) {
                resolve({ id: job.id, ok: false, error: `stdout not JSON: ${e.message}`, stdoutSnippet: stdout.slice(0, 512) });
            }
        });
    });
}

// Capped-concurrency pool
async function runBatch(jobs, cap) {
    const results = new Array(jobs.length);
    let next = 0;
    const workers = Array.from({ length: Math.min(cap, jobs.length) }, async () => {
        while (true) {
            const idx = next++;
            if (idx >= jobs.length) return;
            results[idx] = await runOne(jobs[idx]);
        }
    });
    await Promise.all(workers);
    return results;
}

const t0 = Date.now();
const results = await runBatch(batch, concurrency);
const wall = ((Date.now() - t0) / 1000).toFixed(2);

const out = {};
for (const r of results) {
    const { id, ...rest } = r;
    out[id] = rest;
}

fs.mkdirSync(path.dirname(path.resolve(args.results)), { recursive: true });
fs.writeFileSync(args.results, JSON.stringify(out, null, 2));

const ok = results.filter((r) => r.ok).length;
const failed = results.length - ok;
process.stdout.write(`parallel-cli: ${ok}/${results.length} ok, ${failed} failed, ${wall}s wall (concurrency=${concurrency})\n`);
if (failed > 0) {
    const firstFail = results.find((r) => !r.ok);
    process.stdout.write(`  first failure: ${firstFail.id} → ${firstFail.error}\n`);
}

process.exit(ok === 0 && results.length > 0 ? 3 : 0);
