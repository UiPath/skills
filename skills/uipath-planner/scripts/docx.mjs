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
//   docx.mjs <verb> -h | --help   prints that verb's usage and exits 0.
//
// Exit codes: 0 success · 1 usage error · 2 pandoc missing · 3 conversion failed
//
// pandoc is always spawned with an argument array and no shell, so no path is ever parsed as a command.
// On Windows a .cmd/.bat shim on PATH cannot be spawned without a shell; the pandoc.exe it wraps is used.

import { spawnSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { basename, delimiter, dirname, extname, isAbsolute, join, resolve } from "node:path";

const USAGE = {
  extract: [
    "Usage: docx.mjs extract <input.docx> [output.md]",
    "Converts a .docx to GitHub-flavored Markdown via pandoc.",
    "Embedded images are extracted to <output-basename>-media/.",
  ].join("\n"),
  export: [
    "Usage: docx.mjs export <sdd.md> [output.docx] [--reference-doc <template.docx>]",
    "Converts an SDD markdown file to .docx via pandoc, with table of contents.",
    "--reference-doc applies the styles of an existing Word document.",
  ].join("\n"),
};
const ALL_USAGE = [
  "Usage: docx.mjs extract <input.docx> [output.md]",
  "       docx.mjs export <sdd.md> [output.docx] [--reference-doc <template.docx>]",
].join("\n");
const err = (s) => process.stderr.write(`${s}\n`);
const out = (s) => process.stdout.write(`${s}\n`);
const stem = (p) => basename(p, extname(p));
const isFile = (p) => {
  try { return statSync(p).isFile(); } catch { return false; }
};

function missingPandoc() {
  err("ERROR: pandoc is not installed.");
  err("Install it, then re-run:");
  err("  Windows: winget install JohnMacFarlane.Pandoc");
  err("  macOS:   brew install pandoc");
  err("  Linux:   sudo apt-get install pandoc");
  return 2;
}

/** The executable to spawn: "pandoc" off Windows; on Windows the pandoc.exe found on PATH, directly or behind a shim. */
function findPandoc() {
  if (process.platform !== "win32") return "pandoc";
  const dirs = (process.env.PATH ?? process.env.Path ?? "").split(delimiter).filter(Boolean);
  for (const dir of dirs) {
    for (const ext of [".exe", ".com"]) if (isFile(join(dir, `pandoc${ext}`))) return join(dir, `pandoc${ext}`);
    for (const ext of [".cmd", ".bat"]) {
      const shim = join(dir, `pandoc${ext}`);
      if (!isFile(shim)) continue;
      // A shim names the executable it wraps; take the first existing pandoc.exe it names.
      const text = readFileSync(shim, "utf-8");
      for (const m of text.matchAll(/"?([^"\r\n]*?pandoc\.exe)"?/gi)) {
        const named = m[1].replace(/%~?dp0%?\\?/gi, () => `${dir}\\`).trim();
        const target = isAbsolute(named) ? named : resolve(dirname(shim), named);
        if (isFile(target)) return target;
      }
    }
  }
  return null;
}

/** Probes `pandoc --version`; returns the executable, or an exit code (2) after saying why. */
function probePandoc() {
  const exe = findPandoc();
  if (!exe) return missingPandoc();
  const r = spawnSync(exe, ["--version"], { stdio: "ignore", shell: false });
  if (r.error?.code === "ENOENT") return missingPandoc();
  if (r.error) { err(`ERROR: pandoc could not be run: ${r.error.message}`); return 2; }
  if (r.status !== 0) { err(`ERROR: 'pandoc --version' exited with ${r.status ?? r.signal}`); return 2; }
  return exe;
}

function pandoc(exe, args, input) {
  const r = spawnSync(exe, args, { stdio: "inherit", shell: false });
  if (r.error?.code === "ENOENT") return missingPandoc();
  if (r.error) { err(`ERROR: pandoc could not be run: ${r.error.message}`); return 3; }
  if (r.status !== 0) { err(`ERROR: pandoc conversion failed for ${input}`); return 3; }
  return 0;
}

function files(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? files(join(dir, e.name)) : [join(dir, e.name)]));
}

function extract(exe, [input, output = `${stem(input)}.md`]) {
  if (!isFile(input)) { err(`ERROR: input file not found: ${input}`); return 1; }
  const mediaDir = /\.md$/i.test(output) ? `${output.slice(0, -3)}-media` : `${output}-media`;
  // absolute, so an input named like `-x.docx` is never read by pandoc as an option
  const code = pandoc(exe, [resolve(input), "-f", "docx", "-t", "gfm", "--wrap=none", `--extract-media=${mediaDir}`, "-o", output], input);
  if (code) return code;
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

function exportSdd(exe, [input, ...rest]) {
  if (!isFile(input)) { err(`ERROR: input file not found: ${input}`); return 1; }
  let output = `${stem(input)}.docx`, reference = "";
  for (let i = 0; i < rest.length; i++) {
    if (rest[i] === "--reference-doc") {
      if (i + 1 >= rest.length) { err("ERROR: --reference-doc needs a path"); return 1; }
      reference = rest[++i];
    } else output = rest[i];
  }
  const pandocArgs = [resolve(input), "-f", "gfm", "-t", "docx", "--toc", "--toc-depth=2", "-o", output];
  if (reference) {
    if (!isFile(reference)) { err(`ERROR: reference doc not found: ${reference}`); return 1; }
    pandocArgs.push(`--reference-doc=${reference}`);
  }
  const code = pandoc(exe, pandocArgs, input);
  if (code) return code;
  out(`Word document: ${output}`);
  if (readFileSync(input, "utf-8").includes("```mermaid")) {
    err("NOTE: mermaid diagrams are kept as code blocks, not rendered images.");
    err("Render and place images separately if the deliverable needs visuals.");
  }
  return 0;
}

function main([verb, ...args]) {
  if (!verb || verb === "--help" || verb === "-h") { out(ALL_USAGE); return verb ? 0 : 1; }
  const run = { extract, export: exportSdd }[verb];
  if (!run) { err(`ERROR: unknown verb '${verb}'\n${ALL_USAGE}`); return 1; }
  if (args[0] === "--help" || args[0] === "-h") { out(USAGE[verb]); return 0; }
  if (!args.length) { out(USAGE[verb]); return 1; }
  const exe = probePandoc();
  if (typeof exe === "number") return exe;
  return run(exe, args);
}

process.exitCode = main(process.argv.slice(2));
