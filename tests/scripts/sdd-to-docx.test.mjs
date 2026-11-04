import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import test from "node:test";

// A fake `pandoc` on PATH records its argv. It is a POSIX shell script, which
// spawnSync cannot launch on Windows without a shell.
const SCRIPT = resolve("skills/uipath-planner/scripts/sdd-to-docx.mjs");
const skip = process.platform === "win32" && "POSIX fake pandoc";

function sandbox(t) {
  const dir = mkdtempSync(join(tmpdir(), "sdd-to-docx-"));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  writeFileSync(join(dir, "sdd.md"), "# SDD\n");
  writeFileSync(join(dir, "template.docx"), "docx");
  return dir;
}

// Builtins only: PATH holds nothing but this directory.
function fakePandoc(dir, status = 0, stdout = "") {
  const bin = join(dir, "bin");
  mkdirSync(bin, { recursive: true });
  const script = [
    "#!/bin/sh",
    `printf '%s\\n' "$@" > "${join(dir, "argv.txt")}"`,
    `printf '%s' '${stdout}'`,
    `exit ${status}`,
  ].join("\n");
  writeFileSync(join(bin, "pandoc"), script, { mode: 0o755 });
  return bin;
}

function run(dir, args, pathDir = fakePandoc(dir)) {
  return spawnSync(process.execPath, [SCRIPT, ...args], {
    cwd: dir,
    encoding: "utf-8",
    env: { ...process.env, PATH: pathDir },
  });
}

const argv = (dir) => readFileSync(join(dir, "argv.txt"), "utf-8").trim().split("\n");

test("converts with a table of contents and the customer template as reference", { skip }, (t) => {
  const dir = sandbox(t);
  const result = run(dir, ["sdd.md", "out.docx", "--reference-doc", "template.docx"]);

  assert.equal(result.status, 0);
  assert.match(result.stdout, /Word document: out\.docx/);
  assert.deepEqual(argv(dir), [
    "sdd.md", "-f", "gfm", "-t", "docx", "--toc", "--toc-depth=2", "--sandbox", "-o", "out.docx",
    "--reference-doc=template.docx",
  ]);
});

test("names the output after the input when none is given", { skip }, (t) => {
  const dir = sandbox(t);
  assert.equal(run(dir, ["sdd.md"]).status, 0);
  assert.ok(argv(dir).includes("sdd.docx"));
});

test("prints only the template headings in --headings mode", { skip }, (t) => {
  const dir = sandbox(t);
  const result = run(dir, ["--headings", "template.docx"], fakePandoc(dir, 0, "# 1. PURPOSE\n\nBody\n\n## 3.1 Architecture\n"));

  assert.equal(result.status, 0);
  assert.equal(result.stdout, "# 1. PURPOSE\n## 3.1 Architecture\n");
  assert.deepEqual(argv(dir), ["template.docx", "-f", "docx", "-t", "gfm", "--wrap=none", "--sandbox"]);
});

test("exits 1 on a usage error or a missing file", { skip }, (t) => {
  const dir = sandbox(t);
  for (const args of [[], ["missing.md"], ["sdd.md", "--reference-doc", "missing.docx"], ["sdd.md", "--reference-doc"]]) {
    assert.equal(run(dir, args).status, 1, args.join(" "));
  }
});

test("exits 2 when pandoc is not installed", { skip }, (t) => {
  const dir = sandbox(t);
  const empty = join(dir, "empty");
  mkdirSync(empty);
  const result = run(dir, ["sdd.md"], empty);

  assert.equal(result.status, 2);
  assert.match(result.stderr, /pandoc is not installed/);
});

test("exits 3 when pandoc fails", { skip }, (t) => {
  const dir = sandbox(t);
  assert.equal(run(dir, ["sdd.md"], fakePandoc(dir, 64)).status, 3);
});
