#!/usr/bin/env node
/**
 * Verify that every PowerShell hook in a built package carries an Authenticode
 * signature block.
 *
 * Checks the packed artifact, not the working tree: it catches a signature that
 * was applied correctly and then destroyed on the way into the tarball.
 *
 * Structural, not cryptographic -- chain validation needs the Windows crypto
 * stack and the publish jobs run on Linux.
 *
 * Usage:
 *   node scripts/check-hook-signatures.mjs <package.tgz>
 *   node scripts/check-hook-signatures.mjs <directory>
 */

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const BEGIN_MARKER = "# SIG # Begin signature block";
const END_MARKER = "# SIG # End signature block";

/**
 * Shortest plausible signature block, in base64 characters. A SHA-256
 * Authenticode PKCS#7 with a timestamp runs to several kilobytes; this only has
 * to be high enough that a truncated or placeholder block cannot pass.
 */
const MIN_SIGNATURE_CHARS = 512;

function fail(message) {
  console.error(`check-hook-signatures: ${message}`);
  process.exitCode = 1;
}

/** Extract `tarball` into a fresh temp directory and return the package root. */
function extractTarball(tarball) {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "hook-sig-"));
  execFileSync("tar", ["-xzf", tarball, "-C", tempDir], { stdio: "pipe" });
  // npm tarballs put everything under a single `package/` directory.
  const packageRoot = path.join(tempDir, "package");
  return fs.existsSync(packageRoot) ? packageRoot : tempDir;
}

function hookScriptsIn(root) {
  const hooksDir = path.join(root, "hooks");
  if (!fs.existsSync(hooksDir)) return [];
  return fs
    .readdirSync(hooksDir)
    .filter((name) => name.endsWith(".ps1"))
    .sort()
    .map((name) => path.join(hooksDir, name));
}

/**
 * Whether `file` carries a well-formed signature block.
 *
 * The block must be the LAST thing in the file. PowerShell verifies a signature
 * over everything preceding it, so content appended afterwards is content no
 * signature covers -- a file that ends in anything else is either unsigned or
 * was modified after signing, and both are the same defect here.
 */
function inspect(file) {
  const text = fs.readFileSync(file, "utf8");
  const begin = text.lastIndexOf(BEGIN_MARKER);
  const end = text.lastIndexOf(END_MARKER);

  if (begin === -1 || end === -1) return { signed: false, reason: "no signature block" };
  if (end < begin) return { signed: false, reason: "malformed block (end precedes begin)" };
  if (text.slice(end + END_MARKER.length).trim() !== "") {
    return { signed: false, reason: "content follows the signature block, so it is not covered by the signature" };
  }

  const body = text
    .slice(begin + BEGIN_MARKER.length, end)
    .split("\n")
    .map((line) => line.replace(/^\s*#\s?/, "").trim())
    .join("");

  if (body.length < MIN_SIGNATURE_CHARS) {
    return { signed: false, reason: `signature block too short (${body.length} chars)` };
  }
  if (!/^[A-Za-z0-9+/=]+$/.test(body)) {
    return { signed: false, reason: "signature block is not valid base64" };
  }
  return { signed: true, bytes: body.length };
}

function main() {
  const target = process.argv[2];
  if (!target) {
    fail("usage: check-hook-signatures.mjs <package.tgz|directory>");
    return;
  }
  if (!fs.existsSync(target)) {
    fail(`not found: ${target}`);
    return;
  }

  const root = fs.statSync(target).isDirectory() ? target : extractTarball(target);
  const scripts = hookScriptsIn(root);

  if (scripts.length === 0) {
    // Never silently pass: a package with no hooks to check is either a
    // packaging regression or the wrong target, and reporting success would
    // make an empty result look like a verified one.
    fail(`no hooks/*.ps1 found in ${target} — nothing was verified`);
    return;
  }

  let unsigned = 0;
  for (const script of scripts) {
    const name = path.relative(root, script);
    const result = inspect(script);
    if (result.signed) {
      console.log(`  ok       ${name} (${result.bytes} base64 chars)`);
    } else {
      console.log(`  UNSIGNED ${name} — ${result.reason}`);
      unsigned += 1;
    }
  }

  if (unsigned > 0) {
    fail(`${unsigned} of ${scripts.length} hook script(s) are not signed in ${target}`);
    return;
  }
  console.log(`check-hook-signatures: all ${scripts.length} hook script(s) signed in ${target}`);
}

main();
