#!/usr/bin/env node
/**
 * Resolve every relative Markdown link in the skill trees and report the ones
 * that do not land on a file.
 *
 * A broken link is not cosmetic here: an agent reading a skill can only reach
 * a reference file by following a link or by guessing a path. When a link is
 * wrong the read fails, and the agent gets a bare "no such file" with nothing
 * to recover from — it moves on without the guidance the skill meant it to
 * have. This check is what keeps that from drifting back in.
 *
 * Scope: `skills/` (canonical) and `skill-flavors/` (sparse overrides).
 * Flavor files mirror canonical paths, so a flavor link is resolved against
 * its canonical location as well — that is where it will sit once composed.
 *
 * Ignored, because none of them address a file in the tree: absolute URLs,
 * mailto/anchor-only targets, and code-fenced text.
 */
import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const ROOTS = ["skills", "skill-flavors"];

/** `[text](target)`, skipping images (`![alt](src)`). */
const LINK_RE = /(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g;
/** Fenced code blocks — links inside them are illustrative, not navigation. */
const FENCE_RE = /^```/;

/**
 * Only repo-relative links address a file in the tree. Skipped:
 *   - URLs and `mailto:` (`scheme:`), protocol-relative `//host`
 *   - anchor-only `#section`
 *   - anything rooted at `/`. That covers the `/uipath:<skill>` invocation
 *     convention (a skill name, not a path) and the absolute-path
 *     placeholders used in examples. The repo has no absolute-link form.
 */
const isExternal = (t) =>
    /^[a-z][a-z0-9+.-]*:/i.test(t) ||
    t.startsWith("//") ||
    t.startsWith("#") ||
    t.startsWith("/");

async function walk(dir, out = []) {
    let entries;
    try {
        entries = await readdir(dir, { withFileTypes: true });
    } catch {
        return out;
    }
    for (const entry of entries) {
        // Dot-directories (`.maintenance/`) hold maintainer notes, not skill
        // content an agent reads, and they document link syntax with
        // placeholder targets like `file.md#section-name`.
        if (entry.name.startsWith(".")) continue;
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) await walk(full, out);
        else if (entry.name.endsWith(".md")) out.push(full);
    }
    return out;
}

/** Strip fenced blocks so example links do not count as navigation. */
function proseLines(text) {
    const lines = text.split("\n");
    const kept = [];
    let inFence = false;
    for (let i = 0; i < lines.length; i++) {
        if (FENCE_RE.test(lines[i])) {
            inFence = !inFence;
            continue;
        }
        if (!inFence) kept.push([i + 1, lines[i]]);
    }
    return kept;
}

/**
 * Where a link from `fromFile` should resolve. A flavor file mirrors a
 * canonical path, so it resolves as if it sat in `skills/`.
 */
function resolveBaseDir(fromFile) {
    const rel = path.relative(REPO_ROOT, fromFile);
    const parts = rel.split(path.sep);
    if (parts[0] === "skill-flavors" && parts.length > 2) {
        return path.dirname(path.join(REPO_ROOT, "skills", ...parts.slice(2)));
    }
    return path.dirname(fromFile);
}

async function exists(p) {
    try {
        await stat(p);
        return true;
    } catch {
        return false;
    }
}

const broken = [];
let checked = 0;

for (const root of ROOTS) {
    for (const file of await walk(path.join(REPO_ROOT, root))) {
        const text = await readFile(file, "utf8");
        const baseDir = resolveBaseDir(file);
        for (const [lineNo, line] of proseLines(text)) {
            for (const match of line.matchAll(LINK_RE)) {
                const raw = match[1];
                if (isExternal(raw)) continue;
                const target = decodeURI(raw.split("#")[0]);
                if (target === "") continue;
                checked++;
                // Canonicalize before use, then confirm the link stays inside
                // the repo — a target that escapes it is broken by definition.
                const resolved = path.resolve(baseDir, target);
                const inRepo =
                    resolved === REPO_ROOT ||
                    resolved.startsWith(REPO_ROOT + path.sep);
                if (!inRepo || !(await exists(resolved))) {
                    broken.push({
                        file: path.relative(REPO_ROOT, file),
                        line: lineNo,
                        target: raw,
                        why: inRepo ? "no such file" : "escapes the repo root",
                    });
                }
            }
        }
    }
}

console.log(`Checked ${checked} relative Markdown links across ${ROOTS.join(", ")}.`);
if (broken.length === 0) {
    console.log("All links resolve.");
    process.exit(0);
}
console.error(`\n${broken.length} broken link(s):\n`);
for (const b of broken) {
    console.error(`  ${b.file}:${b.line} -> ${b.target}  (${b.why})`);
}
process.exit(1);
