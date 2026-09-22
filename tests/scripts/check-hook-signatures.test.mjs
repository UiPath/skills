import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const CHECKER = fileURLToPath(new URL("../../scripts/check-hook-signatures.mjs", import.meta.url));

const BEGIN = "# SIG # Begin signature block";
const END = "# SIG # End signature block";

/** A signature block long enough to clear the checker's MIN_SIGNATURE_CHARS. */
function signatureBlock(chars = 600) {
  return [BEGIN, `# ${"Q".repeat(chars)}`, END].join("\n");
}

/** A hooks/ directory whose `.ps1` files hold the given contents. */
function packageDir(files) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "check-hook-sig-"));
  const hooksDir = path.join(root, "hooks");
  fs.mkdirSync(hooksDir);
  for (const [name, content] of Object.entries(files)) {
    fs.writeFileSync(path.join(hooksDir, name), content);
  }
  return root;
}

/** Run the checker the way publish.yml does: as a subprocess over a target. */
function check(target) {
  const result = spawnSync(process.execPath, [CHECKER, target], { encoding: "utf8" });
  return { code: result.status, out: result.stdout + result.stderr };
}

test("passes a package whose every hook carries a signature block", () => {
  const root = packageDir({
    "a.ps1": `Write-Host 'a'\n${signatureBlock()}\n`,
    "b.ps1": `Write-Host 'b'\n${signatureBlock()}\n`,
  });

  const { code, out } = check(root);

  assert.equal(code, 0);
  assert.match(out, /all 2 hook script\(s\) signed/);
});

test("fails a hook with no signature block at all", () => {
  const root = packageDir({ "a.ps1": "Write-Host 'a'\n" });

  const { code, out } = check(root);

  assert.equal(code, 1);
  assert.match(out, /UNSIGNED hooks\/a\.ps1 — no signature block/);
});

// PowerShell covers only content preceding the block, so trailing bytes are
// unsigned content in a file that still reads as signed.
test("fails a hook with content appended after the signature block", () => {
  const root = packageDir({
    "a.ps1": `Write-Host 'a'\n${signatureBlock()}\nWrite-Host 'appended'\n`,
  });

  const { code, out } = check(root);

  assert.equal(code, 1);
  assert.match(out, /content follows the signature block/);
});

test("fails a placeholder block too short to be a real signature", () => {
  const root = packageDir({ "a.ps1": `Write-Host 'a'\n${signatureBlock(16)}\n` });

  const { code, out } = check(root);

  assert.equal(code, 1);
  assert.match(out, /signature block too short/);
});

test("fails a block that is not valid base64", () => {
  const root = packageDir({
    "a.ps1": `Write-Host 'a'\n${[BEGIN, `# ${"!".repeat(600)}`, END].join("\n")}\n`,
  });

  const { code, out } = check(root);

  assert.equal(code, 1);
  assert.match(out, /not valid base64/);
});

test("fails a malformed block whose end marker precedes its begin marker", () => {
  const root = packageDir({
    "a.ps1": `Write-Host 'a'\n${[END, `# ${"Q".repeat(600)}`, BEGIN].join("\n")}\n`,
  });

  const { code, out } = check(root);

  assert.equal(code, 1);
  assert.match(out, /end precedes begin/);
});

test("fails a package with no hooks to check rather than passing vacuously", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "check-hook-sig-"));

  const { code, out } = check(root);

  assert.equal(code, 1);
  assert.match(out, /nothing was verified/);
});

test("fails a target that does not exist", () => {
  const { code, out } = check(path.join(os.tmpdir(), "definitely-absent-package"));

  assert.equal(code, 1);
  assert.match(out, /not found/);
});

test("reports usage when given no target", () => {
  const result = spawnSync(process.execPath, [CHECKER], { encoding: "utf8" });

  assert.equal(result.status, 1);
  assert.match(result.stdout + result.stderr, /usage: check-hook-signatures\.mjs/);
});

test("verifies the hooks inside a packed tarball, not just a directory", () => {
  const root = packageDir({ "a.ps1": `Write-Host 'a'\n${signatureBlock()}\n` });
  // npm tarballs nest everything under `package/`; the checker unwraps that.
  const staging = fs.mkdtempSync(path.join(os.tmpdir(), "check-hook-sig-tgz-"));
  fs.cpSync(root, path.join(staging, "package"), { recursive: true });
  const tarball = path.join(staging, "pkg.tgz");
  spawnSync("tar", ["-czf", tarball, "-C", staging, "package"], { encoding: "utf8" });

  const { code, out } = check(tarball);

  assert.equal(code, 0);
  assert.match(out, /all 1 hook script\(s\) signed/);
});
