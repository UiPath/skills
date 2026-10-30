#!/usr/bin/env node
// Word documents in and out, through pandoc. Node >= 20, built-ins only; replaces the .sh/.ps1 twins.
//
// Usage:
//   docx.mjs extract <input.docx> [output.md]
//     A .docx (typically a PDD) to UTF-8 GitHub-flavored Markdown; tables kept as pipe tables, embedded
//     images (screenshots) extracted to <output-basename>-media/ so the agent can Read them.
//     output.md defaults to <input-basename>.md in the current directory.
//   docx.mjs export <sdd.md> [output.docx] [--reference-doc <template.docx>]
//     A generated SDD to a styled Word document with a table of contents; --reference-doc applies the
//     fonts, heading styles and margins of an existing .docx. output.docx defaults to <input-basename>.docx.
//     Known limitation: mermaid code blocks stay code blocks, not rendered images.
//
// Exit codes: 0 success · 1 usage error · 2 pandoc missing · 3 conversion failed

import { spawnSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { basename, extname, join } from "node:path";

const USAGE = [
  "Usage: docx.mjs extract <input.docx> [output.md]",
  "       docx.mjs export <sdd.md> [output.docx] [--reference-doc <template.docx>]",
].join("\n");
const err = (s) => process.stderr.write(`${s}\n`);
const out = (s) => process.stdout.write(`${s}\n`);
const stem = (p) => basename(p, extname(p));

function pandoc(args) {
  const r = spawnSync("pandoc", args, { stdio: "inherit" });
  if (r.error?.code === "ENOENT") {
    err("ERROR: pandoc is not installed.");
    err("Install it, then re-run:");
    err("  Windows: winget install JohnMacFarlane.Pandoc");
    err("  macOS:   brew install pandoc");
    err("  Linux:   sudo apt-get install pandoc");
    return 2;
  }
  return r.status === 0 ? 0 : 3;
}

function files(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? files(join(dir, e.name)) : [join(dir, e.name)]));
}

function extract([input, output = `${stem(input ?? "")}.md`]) {
  if (!input) { err(USAGE); return 1; }
  if (!existsSync(input) || !statSync(input).isFile()) { err(`ERROR: input file not found: ${input}`); return 1; }
  const mediaDir = output.endsWith(".md") ? `${output.slice(0, -3)}-media` : `${output}-media`;
  const code = pandoc([input, "-f", "docx", "-t", "gfm", "--wrap=none", `--extract-media=${mediaDir}`, "-o", output]);
  if (code) { if (code === 3) err(`ERROR: pandoc conversion failed for ${input}`); return code; }
  out(`Markdown: ${output}`);
  if (!existsSync(mediaDir)) { out("Media:    none embedded"); return 0; }
  const media = files(mediaDir);
  out(`Media:    ${mediaDir}/ (${media.length} file(s))`);
  const unreadable = media.filter((f) => /\.(emf|wmf)$/i.test(f));
  if (unreadable.length) {
    err(`WARNING: EMF/WMF media cannot be rendered by the Read tool: ${unreadable.join(" ")}`);
    err("Ask the user for PNG exports of those figures, or mark dependent extractions [SME REVIEW].");
  }
  return 0;
}

function exportSdd(args) {
  const [input, ...rest] = args;
  if (!input) { err(USAGE); return 1; }
  if (!existsSync(input) || !statSync(input).isFile()) { err(`ERROR: input file not found: ${input}`); return 1; }
  let output = `${stem(input)}.docx`, reference = "";
  for (let i = 0; i < rest.length; i++) {
    if (rest[i] === "--reference-doc") {
      if (i + 1 >= rest.length) { err("ERROR: --reference-doc needs a path"); return 1; }
      reference = rest[++i];
    } else output = rest[i];
  }
  const pandocArgs = [input, "-f", "gfm", "-t", "docx", "--toc", "--toc-depth=2", "-o", output];
  if (reference) {
    if (!existsSync(reference)) { err(`ERROR: reference doc not found: ${reference}`); return 1; }
    pandocArgs.push(`--reference-doc=${reference}`);
  }
  const code = pandoc(pandocArgs);
  if (code) { if (code === 3) err(`ERROR: pandoc conversion failed for ${input}`); return code; }
  out(`Word document: ${output}`);
  if (readFileSync(input, "utf-8").includes("```mermaid")) {
    err("NOTE: mermaid diagrams are kept as code blocks, not rendered images.");
    err("Render and place images separately if the deliverable needs visuals.");
  }
  return 0;
}

const [verb, ...args] = process.argv.slice(2);
if (!verb || verb === "--help" || verb === "-h") {
  out(USAGE);
  process.exitCode = verb ? 0 : 1;
} else if (verb === "extract") process.exitCode = extract(args);
else if (verb === "export") process.exitCode = exportSdd(args);
else { err(`ERROR: unknown verb '${verb}'\n${USAGE}`); process.exitCode = 1; }
