#!/usr/bin/env node
// Prints the fingerprint a genome's `Designed in:` line records for its SDD (Node.js built-ins only).
//
//   node sdd-fingerprint.mjs <sdd.md>
//
// sha256 of the SDD with LF line endings and without its `Genome` handoff row, which `author` writes
// after the SDD is agreed, or an older SDD's `Tasks file` row. A solution root SDD (`Project SDD role`
// root) is hashed followed by each child SDD it lists, each normalized the same way. check-genome.mjs imports
// sddFingerprint; its strict profile fails a genome whose SDD changed since the genome was written.
//
// Exit codes: 0 success · 1 usage error, unreadable file or missing child SDD

import { createHash } from 'node:crypto';
import { readFileSync, realpathSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const LATE_ROWS = /^\|\s*\*\*(Tasks file|Genome)\*\*\s*\|.*\n?/gm;
const ROOT_ROLE = /^\|\s*\*\*Project SDD role\*\*\s*\|\s*root\s*\|/im;
// children: every `*-sdd.md` link target or backticked path in the root, resolved against its folder, in order, once each, the root excluded
const CHILD_REF = /\]\(([^)\s#]+-sdd\.md)(?:#[^)\s]*)?\)|`([^`\s]+-sdd\.md)`/g;

const normalize = (text) => text.replace(/^﻿/, '').replace(/\r\n?/g, '\n').replace(LATE_ROWS, '');

function read(path, what) {
    try {
        return normalize(readFileSync(path, 'utf8'));
    } catch (e) {
        throw new Error(`cannot read ${what}: ${e.message}`);
    }
}

/** The fingerprint of an SDD, a solution root's covering every child it lists; throws when the SDD or a child cannot be read. */
export function sddFingerprint(file) {
    const root = read(file, file);
    const hash = createHash('sha256').update(root);
    if (ROOT_ROLE.test(root)) {
        const self = resolve(file);
        const children = [...new Set([...root.matchAll(CHILD_REF)].map((m) => resolve(dirname(self), m[1] ?? m[2])))].filter((p) => p !== self);
        for (const child of children) hash.update(read(child, `child SDD ${child} listed by ${file}`));
    }
    return hash.digest('hex');
}

const entry = (() => { try { return pathToFileURL(realpathSync(process.argv[1])).href; } catch { return ''; } })();
if (import.meta.url === entry) {
    const file = process.argv[2];
    if (!file || process.argv.length > 3) {
        console.error('Usage: node sdd-fingerprint.mjs <sdd.md>');
        process.exit(1);
    }
    try {
        process.stdout.write(sddFingerprint(file) + '\n');
    } catch (e) {
        console.error(`ERROR: ${e.message}`);
        process.exit(1);
    }
}
