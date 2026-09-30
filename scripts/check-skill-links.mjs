#!/usr/bin/env node
/**
 * Resolve every relative Markdown link in the skill trees and report the ones
 * that do not land on a file, then resolve their `#fragments` against the
 * target's headings.
 *
 * A broken link is not cosmetic here: an agent reading a skill can only reach
 * a reference file by following a link or by guessing a path. When a link is
 * wrong the read fails, and the agent gets a bare "no such file" with nothing
 * to recover from — it moves on without the guidance the skill meant it to
 * have. This check is what keeps that from drifting back in.
 *
 * Scope: `skills/` (canonical), `skill-flavors/` (sparse overrides) and
 * `classic/skills/` (retained trees a flavor pins). Flavor and classic files
 * mirror canonical paths, so their links are resolved from their canonical
 * location as well — that is where they will sit once composed.
 *
 * A pinned skill (`skill-flavors/<flavor>/<skill>/.canonical`) is composed
 * from `classic/skills/<skill>` in that flavor and from `skills/<skill>`
 * everywhere else. So a link into it from another skill must land in BOTH
 * trees: the default package reads one, the pinning flavor the other.
 *
 * Ignored, because none of them address a file in the tree: absolute URLs,
 * mailto/anchor-only targets, and code-fenced text.
 */
import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
    CANONICAL_PIN_FILENAME,
    CANONICAL_PIN_VALUE,
    CLASSIC_DIRNAME,
    FLAVORS_DIRNAME,
    parseMarkerBlocks,
} from "./compose-skill-flavor.mjs";

/** The repo, or the fixture tree a test names as the first argument. */
const REPO_ROOT = process.argv[2]
    ? path.resolve(process.argv[2])
    : path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const ROOTS = ["skills", FLAVORS_DIRNAME, `${CLASSIC_DIRNAME}/skills`];
const CLASSIC_SKILLS = path.join(REPO_ROOT, CLASSIC_DIRNAME, "skills");

/**
 * flavor name -> set of skills that flavor composes from `classic/skills/`.
 * A malformed pin counts as no pin here; `skills:validate` rejects it.
 */
async function readPins() {
    const pins = new Map();
    const flavorsRoot = path.join(REPO_ROOT, FLAVORS_DIRNAME);
    let flavors = [];
    try {
        flavors = await readdir(flavorsRoot, { withFileTypes: true });
    } catch {
        return pins;
    }
    for (const flavor of flavors) {
        if (!flavor.isDirectory()) continue;
        const pinned = new Set();
        let skills = [];
        try {
            skills = await readdir(path.join(flavorsRoot, flavor.name), { withFileTypes: true });
        } catch {
            continue;
        }
        for (const skill of skills) {
            if (!skill.isDirectory()) continue;
            const pin = path.join(flavorsRoot, flavor.name, skill.name, CANONICAL_PIN_FILENAME);
            try {
                if ((await readFile(pin, "utf8")).trim() === CANONICAL_PIN_VALUE) pinned.add(skill.name);
            } catch {
                // no pin
            }
        }
        pins.set(flavor.name, pinned);
    }
    return pins;
}

const PINS = await readPins();
const ALL_PINNED = new Set([...PINS.values()].flatMap((set) => [...set]));

/**
 * `[text](target)`, skipping images (`![alt](src)`).
 *
 * The text portion allows one level of nested brackets so links whose label
 * names a JSON array — `` [`bindings[]` missing](failure-modes.md) `` — still
 * match. A flat `[^\]]*` stops at the inner `]` and silently skips the link,
 * which lets a broken target through unnoticed.
 */
const LINK_RE = /(?<!!)\[(?:[^[\]]|\[[^[\]]*\])*\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g;
/** Fenced code blocks — links inside them are illustrative, not navigation. */
const FENCE_RE = /^```/;
const MALFORMED_ESCAPE = "malformed % escape";

/** A target that names a path in this repo rather than somewhere else. */
const addressesTree = (t) =>
    !/^[a-z][a-z0-9+.-]*:/i.test(t) && !t.startsWith("//") && !t.startsWith("/");

/**
 * Only repo-relative links address a file in the tree. Skipped:
 *   - URLs and `mailto:` (`scheme:`), protocol-relative `//host`
 *   - anchor-only `#section`
 *   - anything rooted at `/`. That covers the `/uipath:<skill>` invocation
 *     convention (a skill name, not a path) and the absolute-path
 *     placeholders used in examples. The repo has no absolute-link form.
 */
const isExternal = (t) => !addressesTree(t) || t.startsWith("#");

/**
 * A `#fragment` that no heading derives drops the agent at the top of the
 * file, so it reads the whole thing instead of the one section the link
 * named. That is a silent read-budget blowout, not a visible failure.
 *
 * Slugs follow GitHub: inline markup rendered to text, lowercased, every
 * character but letters, digits, `_` and `-` dropped, spaces to `-`, and a
 * repeated slug suffixed `-1`, `-2`.
 *
 * Only the trees listed here fail the run. Elsewhere a dead anchor is
 * reported and tolerated, because the ones that predate this check would
 * block every PR. Add a tree here once its anchors are clean.
 *
 * `skill-flavors/` is excluded outright. A flavor file is a sparse set of
 * replacement blocks, so its headings exist only after composition.
 */
const FRAGMENT_ENFORCED = ["skills/uipath-maestro-bpmn"];
const HEADING_RE = /^#{1,6}\s+(.*?)(?:\s+#+)?\s*$/;

function slugify(heading) {
    return heading
        .replace(/`([^`]*)`/g, "$1")
        .replace(/!?\[([^\]]*)\]\([^)]*\)/g, "$1")
        .trim()
        .toLowerCase()
        .replace(/[^\p{L}\p{N}\p{M}_ -]/gu, "")
        .replace(/ /g, "-");
}

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
 * Where a link from `fromFile` should resolve. A flavor or classic file mirrors
 * a canonical path, so it resolves as if it sat in `skills/`.
 */
function resolveBaseDir(fromFile) {
    const rel = path.relative(REPO_ROOT, fromFile);
    const parts = rel.split(path.sep);
    if (parts[0] === "skill-flavors" && parts.length > 2) {
        return path.dirname(path.join(REPO_ROOT, "skills", ...parts.slice(2)));
    }
    if (parts[0] === "classic" && parts[1] === "skills" && parts.length > 3) {
        return path.dirname(path.join(REPO_ROOT, "skills", ...parts.slice(2)));
    }
    return path.dirname(fromFile);
}

/** The skill a file belongs to once composed, or null outside a skill. */
function composedSkill(fromFile) {
    const parts = path.relative(REPO_ROOT, fromFile).split(path.sep);
    if (parts[0] === "skills") return parts[1] ?? null;
    if (parts[0] === "skill-flavors") return parts[2] ?? null;
    if (parts[0] === "classic" && parts[1] === "skills") return parts[2] ?? null;
    return null;
}

/** Names of the flavor blocks a flavor's override of `relative` replaces. */
const overrideCache = new Map();
async function overriddenBlocks(flavor, relative) {
    const key = `${flavor}\0${relative}`;
    if (overrideCache.has(key)) return overrideCache.get(key);
    let names = new Set();
    try {
        const file = path.join(REPO_ROOT, FLAVORS_DIRNAME, flavor, relative);
        names = new Set(parseMarkerBlocks(file, await readFile(file, "utf8")).map((b) => b.name));
    } catch {
        // no override file
    }
    overrideCache.set(key, names);
    return names;
}

/**
 * The on-disk files a link resolved at `logical` (a `skills/...` path) must
 * exist as, seen from `fromFile`. Each entry is `[path, label]`; the label
 * names the composition that needs it when there is more than one.
 *
 * `block` is the canonical flavor block the link sits in, if any. A pinning
 * flavor that overrides that block never composes the link, so the classic
 * tree is not asked for it — that is how a canonical passage points at the
 * current generation while the flavor's override keeps the classic pointer.
 */
async function physicalTargets(fromFile, logical, block = null) {
    const rel = path.relative(REPO_ROOT, logical);
    const parts = rel.split(path.sep);
    if (parts[0] !== "skills" || parts.length < 2 || !ALL_PINNED.has(parts[1])) {
        return [[logical, null]];
    }
    const target = parts[1];
    const classic = path.join(CLASSIC_SKILLS, ...parts.slice(1));
    const fromParts = path.relative(REPO_ROOT, fromFile).split(path.sep);
    if (fromParts[0] === "classic") return [[classic, null]];
    if (fromParts[0] === "skill-flavors") {
        return PINS.get(fromParts[1])?.has(target) ? [[classic, null]] : [[logical, null]];
    }
    // Canonical: the skill's own links stay in its own tree; a link from any
    // other skill is composed next to both generations.
    if (composedSkill(fromFile) === target) return [[logical, null]];
    const relative = path.relative(path.join(REPO_ROOT, "skills"), fromFile);
    const flavors = [];
    for (const [name, set] of PINS) {
        if (!set.has(target)) continue;
        if (block && (await overriddenBlocks(name, relative)).has(block)) continue;
        flavors.push(name);
    }
    if (flavors.length === 0) return [[logical, null]];
    return [
        [logical, "default package"],
        [classic, `classic tree the ${flavors.join(", ")} flavor(s) compose`],
    ];
}

/** Line number (1-based) -> name of the canonical flavor block around it. */
function blockLines(file, text) {
    const byLine = new Map();
    const starts = [];
    let offset = 0;
    const lineStarts = text.split("\n").map((line) => {
        const at = offset;
        offset += line.length + 1;
        return at;
    });
    for (const b of parseMarkerBlocks(file, text)) starts.push(b);
    lineStarts.forEach((at, index) => {
        const hit = starts.find((b) => at >= b.start && at < b.end);
        if (hit) byLine.set(index + 1, hit.name);
    });
    return byLine;
}

function decodeOrNull(uri) {
    try {
        return decodeURI(uri);
    } catch {
        return null;
    }
}

async function statOrNull(p) {
    try {
        return await stat(p);
    } catch {
        return null;
    }
}

const exists = async (p) => (await statOrNull(p)) !== null;
const isFile = async (p) => ((await statOrNull(p))?.isFile() ?? false);

const anchorCache = new Map();

async function anchorsOf(file) {
    if (anchorCache.has(file)) return anchorCache.get(file);
    const text = await readFile(file, "utf8");
    const counts = new Map();
    const anchors = new Set();
    for (const [, line] of proseLines(text)) {
        const heading = HEADING_RE.exec(line);
        if (!heading) continue;
        const slug = slugify(heading[1]);
        const seen = counts.get(slug) ?? 0;
        counts.set(slug, seen + 1);
        anchors.add(seen === 0 ? slug : `${slug}-${seen}`);
    }
    for (const m of text.matchAll(/<a\s+(?:name|id)=["']([^"']+)["']/g)) {
        anchors.add(m[1].toLowerCase());
    }
    anchorCache.set(file, anchors);
    return anchors;
}

const broken = [];
const deadAnchors = [];
let checked = 0;
let fragmentsChecked = 0;

for (const root of ROOTS) {
    for (const file of await walk(path.join(REPO_ROOT, root))) {
        const text = await readFile(file, "utf8");
        const baseDir = resolveBaseDir(file);
        const rel = path.relative(REPO_ROOT, file);
        const enforced = FRAGMENT_ENFORCED.some(
            (p) => rel === p || rel.startsWith(p + path.sep),
        );
        const blocks = root === "skills" ? blockLines(file, text) : new Map();
        for (const [lineNo, line] of proseLines(text)) {
            const block = blocks.get(lineNo) ?? null;
            for (const match of line.matchAll(LINK_RE)) {
                const raw = match[1];
                if (isExternal(raw)) continue;
                const target = decodeOrNull(raw.split("#")[0]);
                if (target === null) {
                    broken.push({
                        file: path.relative(REPO_ROOT, file),
                        line: lineNo,
                        target: raw,
                        why: MALFORMED_ESCAPE,
                    });
                    continue;
                }
                if (target === "") continue;
                checked++;
                // Canonicalize before use, then confirm the link stays inside
                // the repo — a target that escapes it is broken by definition.
                const resolved = path.resolve(baseDir, target);
                const inRepo =
                    resolved === REPO_ROOT ||
                    resolved.startsWith(REPO_ROOT + path.sep);
                if (!inRepo) {
                    broken.push({ file: rel, line: lineNo, target: raw, why: "escapes the repo root" });
                    continue;
                }
                for (const [physical, label] of await physicalTargets(file, resolved, block)) {
                    if (await exists(physical)) continue;
                    broken.push({
                        file: rel,
                        line: lineNo,
                        target: raw,
                        why: label ? `no such file in the ${label}` : "no such file",
                    });
                }
            }
            if (root !== "skills") continue;
            // Inline code carries format strings like `[Red](#,##0)` that the
            // link pattern matches but no reader can follow.
            for (const match of line.replace(/`[^`]*`/g, "").matchAll(LINK_RE)) {
                const raw = match[1];
                if (!addressesTree(raw)) continue;
                const hash = raw.indexOf("#");
                if (hash < 0) continue;
                const targetPart = decodeOrNull(raw.slice(0, hash));
                // A malformed target is already reported above as a broken link.
                if (targetPart === null) continue;
                const fragment = decodeOrNull(raw.slice(hash + 1));
                if (fragment === null) {
                    broken.push({ file: rel, line: lineNo, target: raw, why: MALFORMED_ESCAPE });
                    continue;
                }
                if (!fragment) continue;
                const targetFile =
                    targetPart === "" ? file : path.resolve(baseDir, targetPart);
                // Every tree the link is composed against must carry the
                // heading, not just the canonical one.
                for (const [physical, label] of await physicalTargets(file, targetFile, block)) {
                    // A missing target is already reported above as a broken link.
                    if (!(await isFile(physical))) continue;
                    fragmentsChecked++;
                    if ((await anchorsOf(physical)).has(fragment.toLowerCase())) continue;
                    deadAnchors.push({
                        file: rel,
                        line: lineNo,
                        target: label ? `${raw} (in the ${label})` : raw,
                        // A cross-generation anchor is new, so it starts clean:
                        // always enforced, whatever the source tree's status.
                        enforced: enforced || label !== null,
                    });
                }
            }
        }
    }
}

const enforcedDead = deadAnchors.filter((d) => d.enforced);
const toleratedDead = deadAnchors.filter((d) => !d.enforced);

console.log(`Checked ${checked} relative Markdown links across ${ROOTS.join(", ")}.`);
console.log(`Checked ${fragmentsChecked} link fragments in skills/.`);

if (toleratedDead.length > 0) {
    console.warn(
        `\n${toleratedDead.length} dead anchor(s) outside ${FRAGMENT_ENFORCED.join(", ")}, not enforced:\n`,
    );
    for (const d of toleratedDead) {
        console.warn(`  ${d.file}:${d.line} -> ${d.target}`);
    }
}

if (broken.length === 0 && enforcedDead.length === 0) {
    console.log("All links resolve and every enforced anchor lands.");
    process.exit(0);
}
if (broken.length > 0) {
    console.error(`\n${broken.length} broken link(s):\n`);
    for (const b of broken) {
        console.error(`  ${b.file}:${b.line} -> ${b.target}  (${b.why})`);
    }
}
if (enforcedDead.length > 0) {
    console.error(`\n${enforcedDead.length} dead anchor(s):\n`);
    for (const d of enforcedDead) {
        console.error(`  ${d.file}:${d.line} -> ${d.target}  (no such heading)`);
    }
}
process.exit(1);
