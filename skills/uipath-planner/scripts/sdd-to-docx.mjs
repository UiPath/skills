#!/usr/bin/env node
// SDD markdown to Word through pandoc (Node.js built-ins only, every platform).
//
//   node sdd-to-docx.mjs <sdd.md> [output.docx] [--reference-doc <template.docx>]
//   node sdd-to-docx.mjs --headings <template.docx>
//
// Convert mode writes a .docx with a table of contents; --reference-doc applies the template's
// styles. --headings prints the template's Markdown headings, one per line, to map its sections.
// Mermaid blocks stay as code: pandoc does not render them.
//
// Exit codes: 0 success · 1 usage error · 2 pandoc missing · 3 conversion failed

import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { basename, extname } from 'node:path';

const USAGE = [
    'Usage: node sdd-to-docx.mjs <sdd.md> [output.docx] [--reference-doc <template.docx>]',
    '       node sdd-to-docx.mjs --headings <template.docx>',
].join('\n');

function fail(code, message) {
    console.error(message);
    process.exit(code);
}

function requireFile(file, label) {
    if (!file) fail(1, USAGE);
    if (!existsSync(file)) fail(1, `ERROR: ${label} not found: ${file}`);
}

function pandoc(args, capture) {
    const result = spawnSync('pandoc', args, {
        encoding: 'utf-8',
        stdio: capture ? ['ignore', 'pipe', 'inherit'] : 'inherit',
        maxBuffer: 64 * 1024 * 1024,
    });
    if (result.error?.code === 'ENOENT') {
        fail(2, 'ERROR: pandoc is not installed. Install it, then re-run.');
    }
    if (result.error || result.status !== 0) {
        fail(3, `ERROR: pandoc failed: ${result.error?.message ?? `exit ${result.status}`}`);
    }
    return result.stdout;
}

function parse(argv) {
    const options = { headings: false, reference: '', positional: [] };
    for (let i = 0; i < argv.length; i++) {
        const arg = argv[i];
        if (arg === '--help' || arg === '-h') {
            console.log(USAGE);
            process.exit(0);
        } else if (arg === '--headings') {
            options.headings = true;
        } else if (arg === '--reference-doc') {
            if (i + 1 >= argv.length) fail(1, 'ERROR: --reference-doc needs a path');
            options.reference = argv[++i];
        } else {
            options.positional.push(arg);
        }
    }
    return options;
}

const { headings, reference, positional } = parse(process.argv.slice(2));

if (headings) {
    const [template] = positional;
    requireFile(template, 'template');
    const markdown = pandoc([template, '-f', 'docx', '-t', 'gfm', '--wrap=none'], true);
    for (const line of markdown.split(/\r?\n/)) {
        if (/^#{1,6}\s/.test(line)) console.log(line);
    }
    process.exit(0);
}

const [input, output = `${basename(input ?? '', extname(input ?? ''))}.docx`] = positional;
requireFile(input, 'input file');
const args = [input, '-f', 'gfm', '-t', 'docx', '--toc', '--toc-depth=2', '-o', output];
if (reference) {
    requireFile(reference, 'reference doc');
    args.push(`--reference-doc=${reference}`);
}
pandoc(args, false);
console.log(`Word document: ${output}`);
