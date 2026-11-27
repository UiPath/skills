#!/usr/bin/env node
// Prints the fingerprint a genome's `Designed in:` line records for its SDD, or, with --genome, the one an SDD
// written from a genome records in its `Genome` handoff row (Node.js built-ins only).
//
//   node sdd-fingerprint.mjs <sdd.md>
//   node sdd-fingerprint.mjs --genome <genome.md>
//
// An SDD: sha256 of the SDD with LF line endings, without its `Genome` handoff row (written after the SDD is
// agreed), an older SDD's `Tasks file` row and its `## Action Required — SME Review Items` section (the open
// questions, written again from the genome after every write). A solution root SDD (`Project SDD role` root) is
// hashed followed by each child SDD it lists, each normalized the same way.
// A genome: sha256 of the genome with LF line endings, a process genome followed by each component genome its
// Components table links, in order, once each.
// check-genome.mjs imports both: its strict profile fails a genome whose SDD changed since the genome was written,
// and an SDD written from a genome that changed since.
//
// Exit codes: 0 success · 1 usage error, unreadable file or missing child SDD or component genome

import { createHash } from 'node:crypto';
import { readFileSync, realpathSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const LATE_ROWS = /^\|\s*\*\*(Tasks file|Genome)\*\*\s*\|.*\n?/gm;
const OPEN_QUESTIONS = /^## Action Required\b[^\n]*\n[\s\S]*?(?=^## |(?![\s\S]))/gm;
const COMPONENT_LINK = /\]\(([^)\s]+-genome\.md)\)/g;
const ROOT_ROLE = /^\|\s*\*\*Project SDD role\*\*\s*\|\s*root\s*\|/im;
// children: every `*-sdd.md` link target or backticked path in the root, and every bare one in a table row or
// list item, resolved against the root's folder, in order, once each, the root excluded
const REF = /\[[^\]]*\]\(([^)\s#]*)[^)]*\)|`([^`\s]*)`|([^\s|`()[\]<>*,;]+)/g;
const INDEX_ROW = /^\s*(?:\||[-*+]\s|\d+[.)]\s)/;
const SDD_FILE = /-sdd\.md$/;

/** The child SDD paths a root lists, as written, in order. */
function childRefs(text) {
    return text.split('\n').flatMap((line) => {
        const row = INDEX_ROW.test(line);
        return [...line.matchAll(REF)]
            .map((m) => m[1] ?? m[2] ?? (row && !m[3].includes('://') ? m[3].replace(/[.:]+$/, '') : ''))
            .filter((ref) => SDD_FILE.test(ref));
    });
}

const lf = (text) => text.replace(/^\uFEFF/, '').replace(/\r\n?/g, '\n');
const whole = (text) => lf(text).replace(LATE_ROWS, '');
const normalize = (text) => whole(text).replace(OPEN_QUESTIONS, '');

function read(path, what, clean = normalize) {
    try {
        return clean(readFileSync(path, 'utf8'));
    } catch (e) {
        throw new Error(`cannot read ${what}: ${e.message}`);
    }
}

/** The fingerprint of a genome, a process genome's covering every component genome its Components table links;
 * throws when the genome or a component cannot be read. */
export function genomeFingerprint(file) {
    const text = read(file, file, lf);
    const hash = createHash('sha256').update(text);
    const components = text.match(/^## Components\b[^\n]*\n([\s\S]*?)(?=^## |(?![\s\S]))/m);
    if (components) {
        const self = resolve(file);
        const linked = [...components[1].matchAll(COMPONENT_LINK)].map((m) => resolve(dirname(self), m[1]));
        for (const component of [...new Set(linked)].filter((p) => p !== self)) hash.update(read(component, `component genome ${component} linked by ${file}`, lf));
    }
    return hash.digest('hex');
}

/** The fingerprint of an SDD, a solution root's covering every child it lists; throws when the SDD or a child cannot be read.
 * keepOpenQuestions: hash the Action Required section too, as a `Designed in:` line taken over the whole SDD records it. */
export function sddFingerprint(file, { keepOpenQuestions = false } = {}) {
    const clean = keepOpenQuestions ? whole : normalize;
    const hash = createHash('sha256').update(read(file, file, clean));
    for (const child of childSdds(file)) hash.update(read(child, `child SDD ${child} listed by ${file}`, clean));
    return hash.digest('hex');
}

/** The child SDD paths a solution root lists, resolved, in order, once each; none for any other SDD. Throws when the
 * SDD cannot be read. */
export function childSdds(file) {
    const root = read(file, file);
    if (!ROOT_ROLE.test(root)) return [];
    const self = resolve(file);
    return [...new Set(childRefs(root).map((ref) => resolve(dirname(self), ref)))].filter((p) => p !== self);
}

const entry = (() => { try { return pathToFileURL(realpathSync(process.argv[1])).href; } catch { return ''; } })();
if (import.meta.url === entry) {
    const args = process.argv.slice(2);
    const genome = args[0] === '--genome';
    const file = genome ? args[1] : args[0];
    if (!file || args.length > (genome ? 2 : 1)) {
        console.error('Usage: node sdd-fingerprint.mjs <sdd.md> | --genome <genome.md>');
        process.exit(1);
    }
    try {
        process.stdout.write((genome ? genomeFingerprint(file) : sddFingerprint(file)) + '\n');
    } catch (e) {
        console.error(`ERROR: ${e.message}`);
        process.exit(1);
    }
}
