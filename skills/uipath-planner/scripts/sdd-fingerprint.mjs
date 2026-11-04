#!/usr/bin/env node
// Prints the fingerprint a genome's `Designed in:` line records for its SDD (Node.js built-ins only).
//
//   node sdd-fingerprint.mjs <sdd.md>
//
// sha256 of the SDD with LF line endings and without its `Tasks file` and `Genome` handoff rows,
// which `plan` and `author` write after the SDD is agreed. uipath-build-from-genome's checker
// computes the same value to tell whether the SDD changed since the genome was written.
//
// Exit codes: 0 success · 1 usage error or unreadable file

import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

const LATE_ROWS = /^\|\s*\*\*(Tasks file|Genome)\*\*\s*\|.*\n?/gm;

const file = process.argv[2];
if (!file || process.argv.length > 3) {
    console.error('Usage: node sdd-fingerprint.mjs <sdd.md>');
    process.exit(1);
}
let text;
try {
    text = readFileSync(file, 'utf8');
} catch (e) {
    console.error(`ERROR: cannot read ${file}: ${e.message}`);
    process.exit(1);
}
const normalized = text.replace(/^﻿/, '').replace(/\r\n?/g, '\n').replace(LATE_ROWS, '');
process.stdout.write(createHash('sha256').update(normalized).digest('hex') + '\n');
